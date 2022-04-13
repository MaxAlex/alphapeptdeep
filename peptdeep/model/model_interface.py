# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/model/model_interface.ipynb (unless otherwise specified).

__all__ = ['get_cosine_schedule_with_warmup', 'PeptideModelInterfaceBase']

# Cell
import os
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

from zipfile import ZipFile
from typing import IO, Tuple, List, Union
from alphabase.yaml_utils import save_yaml
from alphabase.peptide.precursor import is_precursor_sorted

from peptdeep.settings import model_const
from peptdeep.utils import logging

from peptdeep.model.building_block import *

# Cell
from torch.optim.lr_scheduler import LambdaLR

# copied from huggingface
def get_cosine_schedule_with_warmup(
    optimizer, num_warmup_steps,
    num_training_steps, num_cycles=0.5,
    last_epoch=-1
):
    """ Create a schedule with a learning rate that decreases following the
    values of the cosine function between 0 and `pi * cycles` after a warmup
    period during which it increases linearly between 0 and 1.
    """

    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / max(1, num_warmup_steps)
        progress = float(
            current_step - num_warmup_steps
        ) / max(1, num_training_steps - num_warmup_steps)
        return max(0.0, 0.5 * (
            1.0 + np.cos(np.pi * num_cycles * 2.0 * progress)
        ))

    return LambdaLR(optimizer, lr_lambda, last_epoch)

# Cell
class PeptideModelInterfaceBase(object):
    def __init__(self,
        **kwargs
    ):
        self.model:torch.nn.Module = None
        if 'GPU' in kwargs:
            self.use_GPU(kwargs['GPU'])
        else:
            self.use_GPU(True)
        self.optimizer = None

    def use_GPU(self, GPU=True):
        if not torch.cuda.is_available():
            GPU=False
        self.device = torch.device('cuda' if GPU else 'cpu')
        if self.model is not None:
            self.model.to(self.device)

    def build(self,
        model_class: torch.nn.Module,
        **kwargs
    ):
        self.model = model_class(**kwargs)
        self.model_params = kwargs
        self.model.to(self.device)
        self._init_for_train()

    def train_with_warmup(self,
        precursor_df: pd.DataFrame,
        *,
        batch_size=1024,
        epoch=10,
        warmup_epoch=5,
        lr=1e-4,
        verbose=False,
        verbose_each_epoch=False,
        **kwargs
    ):
        self._pre_training(precursor_df, lr, **kwargs)

        lr_scheduler = get_cosine_schedule_with_warmup(
            self.optimizer, warmup_epoch, epoch
        )

        for epoch in range(epoch):
            batch_cost = self._train_one_epoch(
                precursor_df, epoch,
                batch_size, verbose_each_epoch,
                **kwargs
            )
            lr_scheduler.step()
            if verbose: print(
                f'[Training] Epoch={epoch+1}, lr={lr_scheduler.get_last_lr()[0]}, loss={np.mean(batch_cost)}'
            )

        torch.cuda.empty_cache()

    def train(self,
        precursor_df: pd.DataFrame,
        *,
        batch_size=1024,
        epoch=10,
        lr=1e-4,
        verbose=False,
        verbose_each_epoch=False,
        **kwargs
    ):
        self._pre_training(precursor_df, lr, **kwargs)

        for epoch in range(epoch):
            batch_cost = self._train_one_epoch(
                precursor_df, epoch,
                batch_size, verbose_each_epoch,
                **kwargs
            )
            if verbose: print(f'[Training] Epoch={epoch+1}, Mean Loss={np.mean(batch_cost)}')

        torch.cuda.empty_cache()

    def predict(self,
        precursor_df:pd.DataFrame,
        *,
        batch_size=1024,
        verbose=False,
        **kwargs
    )->pd.DataFrame:
        if 'nAA' not in precursor_df.columns:
            precursor_df['nAA'] = precursor_df.sequence.str.len()
            precursor_df.sort_values('nAA', inplace=True)
            precursor_df.reset_index(drop=True,inplace=True)
        self._check_predict_in_order(precursor_df)
        self._prepare_predict_data_df(precursor_df,**kwargs)
        self.model.eval()

        _grouped = precursor_df.groupby('nAA')
        if verbose:
            batch_tqdm = tqdm(_grouped)
        else:
            batch_tqdm = _grouped
        with torch.no_grad():
            for nAA, df_group in batch_tqdm:
                for i in range(0, len(df_group), batch_size):
                    batch_end = i+batch_size

                    batch_df = df_group.iloc[i:batch_end,:]

                    features = self._get_features_from_batch_df(
                        batch_df, nAA, **kwargs
                    )

                    predicts = self._predict_one_batch(*features)

                    self._set_batch_predict_data(
                        batch_df, predicts,
                        **kwargs
                    )

        torch.cuda.empty_cache()
        return self.predict_df

    def save(self, save_as):
        dir = os.path.dirname(save_as)
        if not dir: dir = './'
        if not os.path.exists(dir): os.makedirs(dir)
        torch.save(self.model.state_dict(), save_as)
        with open(save_as+'.txt','w') as f: f.write(str(self.model))
        save_yaml(save_as+'.model_const.yaml', model_const)
        self._save_codes(save_as+'.model.py')
        save_yaml(save_as+'.param.yaml', self.model_params)

    def load(
        self,
        model_file: Tuple[str, IO],
        model_path_in_zip: str = None,
        **kwargs
    ):
        if isinstance(model_file, str):
            # We may release all models (msms, rt, ccs, ...) in a single zip file
            if model_file.lower().endswith('.zip'):
                with ZipFile(model_file) as model_zip:
                    with model_zip.open(model_path_in_zip,'r') as pt_file:
                        self._load_model_file(pt_file)
            else:
                with open(model_file,'rb') as pt_file:
                    self._load_model_file(pt_file)
        else:
            self._load_model_file(model_file)

    def get_parameter_num(self):
        return np.sum([p.numel() for p in self.model.parameters()])

    def build_from_py_codes(self,
        model_code_file:str,
        code_file_in_zip:str=None,
        **kwargs
    ):
        if model_code_file.lower().endswith('.zip'):
            with ZipFile(model_code_file, 'r') as model_zip:
                with model_zip.open(code_file_in_zip) as f:
                    codes = f.read()
        else:
            with open(model_code_file, 'r') as f:
                codes = f.read()
        codes = compile(
            codes,
            filename='model_file_py',
            mode='exec'
        )
        exec(codes) #codes must contains torch model codes 'class Model(...'
        self.model = Model(**kwargs)
        self.model_params = kwargs
        self.model.to(self.device)
        self._init_for_train()

    def _init_for_train(self):
        self.loss_func = torch.nn.L1Loss()

    def _load_model_file(self, stream):
        (
            missing_keys, unexpect_keys
        ) = self.model.load_state_dict(torch.load(
            stream, map_location=self.device),
            strict=False
        )
        if len(missing_keys) > 0:
            logging.warn(f"nn parameters {missing_keys} are MISSING while loading models in {self.__class__}")
        if len(unexpect_keys) > 0:
            logging.warn(f"nn parameters {unexpect_keys} are UNEXPECTED while loading models in {self.__class__}")

    def _save_codes(self, save_as):
        import inspect
        code = '''import torch\nimport peptdeep.model.base as model_base\n'''
        class_code = inspect.getsource(self.model.__class__)
        code += 'class Model' + class_code[class_code.find('('):]
        with open(save_as, 'w') as f:
            f.write(code)

    def _train_one_epoch(self,
        precursor_df, epoch, batch_size, verbose_each_epoch,
        **kwargs
    ):
        """Training for an epoch"""
        batch_cost = []
        _grouped = list(precursor_df.sample(frac=1).groupby('nAA'))
        rnd_nAA = np.random.permutation(len(_grouped))
        if verbose_each_epoch:
            batch_tqdm = tqdm(rnd_nAA)
        else:
            batch_tqdm = rnd_nAA
        for i_group in batch_tqdm:
            nAA, df_group = _grouped[i_group]
            # df_group = df_group.reset_index(drop=True)
            for i in range(0, len(df_group), batch_size):
                batch_end = i+batch_size

                batch_df = df_group.iloc[i:batch_end,:]
                targets = self._get_targets_from_batch_df(
                    batch_df,nAA=nAA,**kwargs
                )
                features = self._get_features_from_batch_df(
                    batch_df,nAA=nAA,**kwargs
                )

                batch_cost.append(
                    self._train_one_batch(targets, *features)
                )

            if verbose_each_epoch:
                batch_tqdm.set_description(
                    f'Epoch={epoch+1}, nAA={nAA}, batch={len(batch_cost)}, loss={batch_cost[-1]:.4f}'
                )
        return batch_cost

    def _train_one_batch(
        self,
        targets:torch.Tensor,
        *features,
    ):
        """Training for a mini batch"""
        self.optimizer.zero_grad()
        predicts = self.model(*[fea.to(self.device) for fea in features])
        cost = self.loss_func(predicts, targets.to(self.device))
        cost.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()
        return cost.item()

    def _predict_one_batch(self,
        *features
    ):
        """Predicting for a mini batch"""
        return self.model(
            *[fea.to(self.device) for fea in features]
        ).cpu().detach().numpy()

    def _get_targets_from_batch_df(self,
        batch_df:pd.DataFrame,
        nAA:int=None, **kwargs,
    )->torch.Tensor:
        """Tell the `train()` method how to get target values from the `batch_df`.
           All sub-classes must re-implement this method.

        Args:
            batch_df (pd.DataFrame): Dataframe of each mini batch.
            nAA (int, optional): Peptide length. Defaults to None.

        Raises:
            NotImplementedError: 'Must implement _get_targets_from_batch_df() method'

        Returns:
            torch.Tensor: Target value tensor
        """
        raise NotImplementedError(
            'Must implement _get_targets_from_batch_df() method'
        )

    def _get_features_from_batch_df(self,
        batch_df:pd.DataFrame,
        nAA:int, **kwargs,
    )->Tuple[torch.Tensor]:
        """Tell `train()` and `predict()` methods how to get feature tensors from the `batch_df`.
           All sub-classes must re-implement this method.

        Args:
            batch_df (pd.DataFrame): Dataframe of each mini batch.
            nAA (int, optional): Peptide length. Defaults to None.

        Raises:
            NotImplementedError: 'Must implement _get_features_from_batch_df() method'

        Returns:
            Tuple[torch.Tensor]: A feature tensor or multiple feature tensors.
        """
        raise NotImplementedError(
            'Must implement _get_features_from_batch_df() method'
        )

    def _prepare_predict_data_df(self,
        precursor_df:pd.DataFrame,
        **kwargs
    ):
        '''
        This method must define `self._predict_column_in_df` and create a `self.predict_df` dataframe.
        All sub-classes must re-implement this method.
        For example for RT prediction:
        >>> self._predict_column_in_df = 'rt_pred'
        >>> precursor_df[self._predict_column_in_df] = 0
        >>> self.predict_df = precursor_df
        ...
        '''
        raise NotImplementedError(
            'Must implement _prepare_predict_data_df() method'
        )

    def _prepare_train_data_df(self,
        precursor_df:pd.DataFrame,
        **kwargs
    ):
        pass

    def _set_batch_predict_data(self,
        batch_df:pd.DataFrame,
        predict_values:np.array,
        **kwargs
    ):
        """Set predicted values into `self.predict_df`.

        Args:
            batch_df (pd.DataFrame): Dataframe of mini batch when predicting
            predict_values (np.array): Predicted values
        """
        predict_values[predict_values<0] = 0.0
        if self._predict_in_order:
            self.predict_df.loc[:,self._predict_column_in_df].values[
                batch_df.index.values[0]:batch_df.index.values[-1]+1
            ] = predict_values
        else:
            self.predict_df.loc[
                batch_df.index,self._predict_column_in_df
            ] = predict_values

    def _init_optimizer(self, lr):
        """Set optimizer"""
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=lr
        )

    def set_lr(self, lr:float):
        """Set learning rate"""
        if self.optimizer is None:
            self._init_optimizer(lr)
        else:
            for g in self.optimizer.param_groups:
                g['lr'] = lr

    def _pre_training(self, precursor_df, lr, **kwargs):
        if 'nAA' not in precursor_df.columns:
            precursor_df['nAA'] = precursor_df.sequence.str.len()
        self._prepare_train_data_df(precursor_df, **kwargs)
        self.model.train()

        self.set_lr(lr)

    def _check_predict_in_order(self, precursor_df:pd.DataFrame):
        if is_precursor_sorted(precursor_df):
            self._predict_in_order = True
        else:
            self._predict_in_order = False