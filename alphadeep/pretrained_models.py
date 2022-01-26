# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/pretrained_models.ipynb (unless otherwise specified).

__all__ = ['is_model_zip', 'download_models', 'install_models', 'sandbox_dir', 'model_name', 'model_zip', 'model_url',
           'count_mods', 'psm_sampling_with_important_mods', 'load_phos_models', 'load_HLA_models', 'load_models',
           'load_models_by_model_type_in_zip', 'mgr_settings', 'ModelManager']

# Cell
import os
import io
import pandas as pd
from zipfile import ZipFile
from tarfile import TarFile
from typing import Tuple
import torch
import urllib
import socket
import logging
import shutil

sandbox_dir = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "installed_models"
)

if not os.path.exists(sandbox_dir):
    os.makedirs(sandbox_dir)

model_name = "alphadeep_models.zip"
model_zip = os.path.join(
    sandbox_dir, model_name
)

def is_model_zip(downloaded_zip):
    with ZipFile(downloaded_zip) as zip:
        return any(x=='regular/ms2.pth' for x in zip.namelist())

model_url = 'https://datashare.biochem.mpg.de/s/ABnQuD2KkXfIGF3/download'

def download_models(
    url:str=model_url, overwrite=True
):
    """[summary]

    Args:
        url (str, optional): remote or local path.
          Defaults to alphadeep.pretrained_models.model_url.
        overwrite (bool, optional): overwirte old model files.
          Defaults to True.

    Raises:
        FileNotFoundError: If remote url is not accessible.
    """
    if not os.path.isfile(url):
        downloaded_zip = os.path.join(
            sandbox_dir,'released_models.zip'
        )
        if os.path.exists(model_zip):
            if overwrite:
                os.remove(model_zip)
            else:
                return

        logging.info(f'Downloading {model_name} ...')
        try:
            requests = urllib.request.urlopen(url, timeout=10)
            with open(downloaded_zip, 'wb') as f:
                f.write(requests.read())
        except (
            socket.timeout,
            urllib.error.URLError,
            urllib.error.HTTPError
        ) as e:
            raise FileNotFoundError(
                'Downloading model failed! Please download the '
                f'zip or tar file by yourself from "{url}",'
                ' and use \n'
                '"alphadeep --install /path/to/released_models.tar (or .zip)"\n'
                ' to install the models'
            )
    else:
        downloaded_zip = url
    install_models(downloaded_zip, overwrite=overwrite)
    os.remove(downloaded_zip)

def install_models(downloaded_zip:str, overwrite=True):
    """ Install the model zip file. Note that if the `downloaded_zip`
    is downloaded using download_models(), it is a zip file; if it is
    downloaded using a browser, it will be a tar file.

    Args:
        downloaded_zip (str): path to the downloaded file
        overwrite (bool, optional): Overwrite the existing model.
          Defaults to True.
    """
    if os.path.exists(model_zip):
        if overwrite:
            os.remove(model_zip)
        else:
            return
    if is_model_zip(downloaded_zip):
        shutil.copy(
            downloaded_zip, model_zip
        )
        return
    _zip = ZipFile(downloaded_zip)
    try:
        _zip.extract(
            f'released_models/{model_name}',
            sandbox_dir
        )
        shutil.move(
            os.path.join(sandbox_dir, f'released_models/{model_name}'),
            os.path.join(sandbox_dir, model_name)
        )
        os.rmdir(os.path.join(sandbox_dir, 'released_models'))
    except KeyError:
        tar = TarFile(downloaded_zip)
        with open(os.path.join(sandbox_dir, model_name), 'wb') as f:
            f.write(tar.extractfile(
                f'released_models/{model_name}'
            ).read())
        tar.close()
    _zip.close()
    logging.info(f'Installed {model_name}')

# Cell
if not os.path.exists(model_zip):
    download_models()

# Cell
from alphadeep.model.ms2 import (
    pDeepModel, normalize_training_intensities
)
from alphadeep.model.rt import AlphaRTModel, uniform_sampling
from alphadeep.model.ccs import AlphaCCSModel

from alphadeep.settings import global_settings
mgr_settings = global_settings['model_mgr']

def count_mods(psm_df)->pd.DataFrame:
    mods = psm_df[
        psm_df.mods.str.len()>0
    ].mods.apply(lambda x: x.split(';'))
    mod_dict = {}
    mod_dict['mutation'] = {}
    mod_dict['mutation']['spec_count'] = 0
    for one_mods in mods.values:
        for mod in set(one_mods):
            items = mod.split('->')
            if (
                len(items)==2
                and len(items[0])==3
                and len(items[1])==5
            ):
                mod_dict['mutation']['spec_count'] += 1
            elif mod not in mod_dict:
                mod_dict[mod] = {}
                mod_dict[mod]['spec_count'] = 1
            else:
                mod_dict[mod]['spec_count'] += 1
    return pd.DataFrame().from_dict(
            mod_dict, orient='index'
        ).reset_index(drop=False).rename(
            columns={'index':'mod'}
        ).sort_values(
            'spec_count',ascending=False
        ).reset_index(drop=True)

def psm_sampling_with_important_mods(
    psm_df, n_sample,
    top_n_mods = 10,
    n_sample_each_mod = 0,
    uniform_sampling_column = None,
    random_state=1337,
):
    psm_df_list = []
    if uniform_sampling_column is None:
        def _sample(psm_df, n):
            if n < len(psm_df):
                return psm_df.sample(
                    n, replace=False,
                    random_state=random_state
                ).copy()
            else:
                return psm_df.copy()
    else:
        def _sample(psm_df, n):
            return uniform_sampling(
                psm_df, target=uniform_sampling_column,
                n_train = n, random_state=random_state
            )

    psm_df_list.append(_sample(psm_df, n_sample))
    if n_sample_each_mod > 0:
        mod_df = count_mods(psm_df)
        mod_df = mod_df[mod_df['mod']!='mutation']

        if len(mod_df) > top_n_mods:
            mod_df = mod_df.iloc[:top_n_mods,:]
        for mod in mod_df['mod'].values:
            psm_df_list.append(
                _sample(
                    psm_df[psm_df.mods.str.contains(mod, regex=False)],
                    n_sample_each_mod,
                )
            )
    if len(psm_df_list) > 0:
        return pd.concat(psm_df_list).reset_index(drop=True)
    else:
        return pd.DataFrame()

def load_phos_models(mask_phos_modloss=False):
    ms2_model = pDeepModel(mask_modloss=mask_phos_modloss)
    ms2_model.load(model_zip, model_path_in_zip='phospho/ms2.pth')
    rt_model = AlphaRTModel()
    rt_model.load(model_zip, model_path_in_zip='phospho/rt.pth')
    ccs_model = AlphaCCSModel()
    ccs_model.load(model_zip, model_path_in_zip='regular/ccs.pth')
    return ms2_model, rt_model, ccs_model

def load_HLA_models():
    ms2_model = pDeepModel(mask_modloss=True)
    ms2_model.load(model_zip, model_path_in_zip='HLA/ms2.pth')
    rt_model = AlphaRTModel()
    rt_model.load(model_zip, model_path_in_zip='HLA/rt.pth')
    ccs_model = AlphaCCSModel()
    ccs_model.load(model_zip, model_path_in_zip='regular/ccs.pth')
    return ms2_model, rt_model, ccs_model

def load_models():
    ms2_model = pDeepModel()
    ms2_model.load(model_zip, model_path_in_zip='regular/ms2.pth')
    rt_model = AlphaRTModel()
    rt_model.load(model_zip, model_path_in_zip='regular/rt.pth')
    ccs_model = AlphaCCSModel()
    ccs_model.load(model_zip, model_path_in_zip='regular/ccs.pth')
    return ms2_model, rt_model, ccs_model

def load_models_by_model_type_in_zip(model_type_in_zip:str):
    ms2_model = pDeepModel()
    ms2_model.load(model_zip, model_path_in_zip=f'{model_type_in_zip}/ms2.pth')
    rt_model = AlphaRTModel()
    rt_model.load(model_zip, model_path_in_zip=f'{model_type_in_zip}/rt.pth')
    ccs_model = AlphaCCSModel()
    ccs_model.load(model_zip, model_path_in_zip=f'{model_type_in_zip}/ccs.pth')
    return ms2_model, rt_model, ccs_model


# Cell
from alphabase.peptide.fragment import (
    create_fragment_mz_dataframe,
    get_charged_frag_types,
    concat_precursor_fragment_dataframes
)
from alphabase.peptide.precursor import (
    refine_precursor_df,
    update_precursor_mz
)
from alphadeep.settings import global_settings

import torch.multiprocessing as mp
from typing import Dict
from alphadeep.utils import logging, process_bar

class ModelManager(object):
    def __init__(self):
        self.ms2_model:pDeepModel = None
        self.rt_model:AlphaRTModel = None
        self.ccs_model:AlphaCCSModel = None

        self.grid_nce_search = mgr_settings[
            'fine_tune'
        ]['grid_nce_search']

        self.psm_num_to_tune_ms2 = 5000
        self.psm_num_per_mod_to_tune_ms2 = 100
        self.epoch_to_tune_ms2 = mgr_settings[
            'fine_tune'
        ]['epoch_ms2']
        self.psm_num_to_tune_rt_ccs = 3000
        self.psm_num_per_mod_to_tune_rt_ccs = 100
        self.epoch_to_tune_rt_ccs = mgr_settings[
            'fine_tune'
        ]['epoch_rt_ccs']

        self.top_n_mods_to_tune = 10

        self.nce = mgr_settings[
            'predict'
        ]['default_nce']
        self.instrument = mgr_settings[
            'predict'
        ]['default_instrument']
        self.verbose = mgr_settings[
            'predict'
        ]['verbose']

    def set_default_nce(self, df):
        df['nce'] = self.nce
        df['instrument'] = self.instrument

    def load_installed_models(self, model_type='regular', mask_modloss=True):
        """ Load built-in MS2/CCS/RT models.
        Args:
            model_type (str, optional): To load the installed MS2/RT/CCS models
                or phos MS2/RT/CCS models. It could be 'phospho', 'HLA', 'regular', or
                model_type (model sub-folder) in alphadeep_models.zip.
                Defaults to 'regular'.
            mask_modloss (bool, optional): If modloss ions are masked to zeros
                in the ms2 model. `modloss` ions are mostly useful for phospho
                MS2 prediciton model. Defaults to True.
        """
        if model_type.lower() in ['phospho','phos']:
            (
                self.ms2_model, self.rt_model, self.ccs_model
            ) = load_phos_models(mask_modloss)
        elif model_type.lower() in ['regular','common']:
            (
                self.ms2_model, self.rt_model, self.ccs_model
            ) = load_models()
        elif model_type.lower() in [
            'hla','unspecific','non-specific', 'nonspecific'
        ]:
            (
                self.ms2_model, self.rt_model, self.ccs_model
            ) = load_HLA_models()
        else:
            (
                self.ms2_model, self.rt_model, self.ccs_model
            ) = load_models_by_model_type_in_zip(model_type)

    def load_external_models(self,
        *,
        ms2_model_file: Tuple[str, io.BytesIO]=None,
        rt_model_file: Tuple[str, io.BytesIO]=None,
        ccs_model_file: Tuple[str, io.BytesIO]=None,
        mask_modloss=True
    ):
        """Load external MS2/RT/CCS models

        Args:
            ms2_model_file (Tuple[str, io.BytesIO], optional): ms2 model file or stream.
                It will load the installed model if the value is None. Defaults to None.
            rt_model_file (Tuple[str, io.BytesIO], optional): rt model file or stream.
                It will load the installed model if the value is None. Defaults to None.
            ccs_model_file (Tuple[str, io.BytesIO], optional): ccs model or stream.
                It will load the installed model if the value is None. Defaults to None.
            mask_modloss (bool, optional): If modloss ions are masked to zeros
                in the ms2 model. Defaults to True.
        """
        self.ms2_model = pDeepModel(mask_modloss=mask_modloss)
        self.rt_model = AlphaRTModel()
        self.ccs_model = AlphaCCSModel()

        if ms2_model_file is not None:
            self.ms2_model.load(ms2_model_file)
        else:
            self.ms2_model.load(model_zip, model_path_in_zip='regular/ms2.pth')
        if rt_model_file is not None:
            self.rt_model.load(rt_model_file)
        else:
            self.rt_model.load(model_zip, model_path_in_zip='regular/rt.pth')
        if ccs_model_file is not None:
            self.ccs_model.load(ccs_model_file)
        else:
            self.ccs_model.load(model_zip, model_path_in_zip='regular/ccs.pth')

    def fine_tune_rt_model(self,
        psm_df:pd.DataFrame,
    ):
        """ Fine-tune the RT model. The fine-tuning will be skipped
            if `n_rt_ccs_tune` is zero.

        Args:
            psm_df (pd.DataFrame): training psm_df which contains 'rt_norm' column.
        """
        if self.psm_num_to_tune_rt_ccs > 0:
            tr_df = psm_sampling_with_important_mods(
                psm_df, self.psm_num_to_tune_rt_ccs,
                self.top_n_mods_to_tune,
                self.psm_num_per_mod_to_tune_rt_ccs,
                uniform_sampling_column='rt_norm'
            )
            if len(tr_df) > 0:
                self.rt_model.train(tr_df,
                    epoch=self.epoch_to_tune_rt_ccs
                )

    def fine_tune_ccs_model(self,
        psm_df:pd.DataFrame,
    ):
        """ Fine-tune the CCS model. The fine-tuning will be skipped
            if `n_rt_ccs_tune` is zero.

        Args:
            psm_df (pd.DataFrame): training psm_df which contains 'ccs' column.
        """

        if self.psm_num_to_tune_rt_ccs > 0:
            tr_df = psm_sampling_with_important_mods(
                psm_df, self.psm_num_to_tune_rt_ccs,
                self.top_n_mods_to_tune,
                self.psm_num_per_mod_to_tune_rt_ccs,
                uniform_sampling_column='ccs'
            )
            if len(tr_df) > 0:
                self.ccs_model.train(tr_df,
                    epoch=self.epoch_to_tune_rt_ccs
                )

    def fine_tune_ms2_model(self,
        psm_df: pd.DataFrame,
        matched_intensity_df: pd.DataFrame,
    ):
        if self.psm_num_to_tune_ms2 > 0:
            tr_df = psm_sampling_with_important_mods(
                psm_df, self.psm_num_to_tune_ms2,
                self.top_n_mods_to_tune,
                self.psm_num_per_mod_to_tune_ms2
            )
            if len(tr_df) > 0:
                tr_df, frag_df = normalize_training_intensities(
                    tr_df, matched_intensity_df
                )
                tr_inten_df = pd.DataFrame()
                for frag_type in self.ms2_model.charged_frag_types:
                    if frag_type in frag_df.columns:
                        tr_inten_df[frag_type] = frag_df[frag_type]
                    else:
                        tr_inten_df[frag_type] = 0

                if self.grid_nce_search:
                    self.nce, self.instrument = self.ms2_model.grid_nce_search(
                        tr_df, tr_inten_df,
                        nce_first=mgr_settings['fine_tune'][
                            'grid_nce_first'
                        ],
                        nce_last=mgr_settings['fine_tune'][
                            'grid_nce_last'
                        ],
                        nce_step=mgr_settings['fine_tune'][
                            'grid_nce_step'
                        ],
                        search_instruments=mgr_settings['fine_tune'][
                            'grid_instrument'
                        ],
                    )
                    tr_df['nce'] = self.nce
                    tr_df['instrument'] = self.instrument
                elif 'nce' not in tr_df.columns:
                    self.set_default_nce(tr_df)

                self.ms2_model.train(tr_df,
                    fragment_intensity_df=tr_inten_df,
                    epoch=self.epoch_to_tune_ms2
                )

    def predict_ms2(self, precursor_df:pd.DataFrame,
        *,
        batch_size=mgr_settings[
            'predict'
        ]['batch_size_ms2'],
        reference_frag_df = None,
    ):
        if 'nce' not in precursor_df.columns:
            self.set_default_nce(precursor_df)
        if self.verbose:
            logging.info('Predicting MS2 ...')
        return self.ms2_model.predict(precursor_df,
            batch_size=batch_size,
            reference_frag_df=reference_frag_df,
            verbose=self.verbose
        )

    def predict_rt(self, precursor_df:pd.DataFrame,
        *, batch_size=mgr_settings[
             'predict'
           ]['batch_size_rt_ccs']
    ):
        if self.verbose:
            logging.info("Predicting RT ...")
        df = self.rt_model.predict(precursor_df,
            batch_size=batch_size, verbose=self.verbose
        )
        df['rt_norm_pred'] = df.rt_pred
        return df

    def predict_mobility(self, precursor_df:pd.DataFrame,
        *, batch_size=mgr_settings[
             'predict'
           ]['batch_size_rt_ccs']
    ):
        if self.verbose:
            logging.info("Predicting mobility ...")
        precursor_df = self.ccs_model.predict(precursor_df,
            batch_size=batch_size, verbose=self.verbose
        )
        return self.ccs_model.ccs_to_mobility_pred(
            precursor_df
        )

    def _predict_all_for_mp(self, arg_dict):
        return self.predict_all(
            multiprocessing=False, **arg_dict
        )

    def predict_all(self, precursor_df:pd.DataFrame,
        *,
        predict_items:list = [
            'rt' #,'mobility' ,'ms2'
        ],
        frag_types:list = get_charged_frag_types(
            ['b','y'],2
        ),
        multiprocessing:bool = True,
        thread_num:int = global_settings['thread_num']
    )->Dict[str, pd.DataFrame]:
        """ predict all items defined by `predict_items`,
        which may include rt, mobility, fragment_mz
        and fragment_intensity.

        Args:
            precursor_df (pd.DataFrame): precursor dataframe contains
              `sequence`, `mods`, `mod_sites`, `charge` ... columns.
            predict_items (list, optional): items ('rt', 'mobility',
              'ms2') to predict.
              Defaults to [ 'rt' ].
            frag_types (list, optional): fragment types to predict.
              Defaults to ['b_z1','b_z2','y_z1','y_z2'].
            multiprocessing (bool, optional): if use multiprocessing.
              Defaults to True.
            thread_num (int, optional): Defaults to global_settings['thread_num']
        Returns:
            Dict[str, pd.DataFrame]: {'precursor_df': precursor_df}
              if 'ms2' in predict_items, it also contains:
              {
                  'fragment_mz_df': fragment_mz_df,
                  'fragment_intensity_df': fragment_intensity_df
              }

        """
        def refine_df(df):
            if 'ms2' in predict_items:
                refine_precursor_df(df)
            else:
                refine_precursor_df(df, drop_frag_idx=False)

        if 'precursor_mz' not in precursor_df.columns:
            update_precursor_mz(precursor_df)

        if torch.cuda.is_available() or not multiprocessing:
            refine_df(precursor_df)
            if 'rt' in predict_items:
                self.predict_rt(precursor_df)
            if 'mobility' in predict_items:
                self.predict_mobility(precursor_df)
            if 'ms2' in predict_items:
                fragment_intensity_df = self.predict_ms2(
                    precursor_df
                )

                fragment_intensity_df.drop(
                    columns=[
                        col for col in fragment_intensity_df.columns
                        if col not in frag_types
                    ], inplace=True
                )

                precursor_df.drop(
                    columns=['frag_start_idx'], inplace=True
                )
                fragment_mz_df = create_fragment_mz_dataframe(
                    precursor_df, frag_types
                )
                fragment_mz_df.drop(
                    columns=[
                        col for col in fragment_mz_df.columns
                        if col not in frag_types
                    ], inplace=True
                )

                # clear error modloss intensities
                for col in fragment_mz_df.columns.values:
                    if 'modloss' in col:
                        fragment_intensity_df.loc[
                            fragment_mz_df[col]==0,col
                        ] = 0

                return {
                    'precursor_df': precursor_df,
                    'fragment_mz_df': fragment_mz_df,
                    'fragment_intensity_df': fragment_intensity_df,
                }
            else:
                return {'precursor_df': precursor_df}
        else:
            self.ms2_model.model.share_memory()
            self.rt_model.model.share_memory()
            self.ccs_model.model.share_memory()

            df_groupby = precursor_df.groupby('nAA')

            def param_generator(df_groupby):
                for nAA, df in df_groupby:
                    yield {
                        'precursor_df': df,
                        'predict_items': predict_items,
                        'frag_types': frag_types,
                    }

            precursor_df_list = []
            if 'ms2' in predict_items:
                fragment_mz_df_list = []
                fragment_intensity_df_list = []
            else:
                fragment_mz_df_list = None

            if self.verbose:
                logging.info(
                    f'Predicting {",".join(predict_items)} ...'
                )
            verbose_bak = self.verbose
            self.verbose = False

            with mp.Pool(thread_num) as p:
                for ret_dict in process_bar(
                    p.imap_unordered(
                        self._predict_all_for_mp,
                        param_generator(df_groupby)
                    ), df_groupby.ngroups
                ):
                    precursor_df_list.append(ret_dict['precursor_df'])
                    if fragment_mz_df_list is not None:
                        fragment_mz_df_list.append(
                            ret_dict['fragment_mz_df']
                        )
                        fragment_intensity_df_list.append(
                            ret_dict['fragment_intensity_df']
                        )
            self.verbose = verbose_bak

            if fragment_mz_df_list is not None:
                (
                    precursor_df, fragment_mz_df, fragment_intensity_df
                ) = concat_precursor_fragment_dataframes(
                    precursor_df_list,
                    fragment_mz_df_list,
                    fragment_intensity_df_list,
                )

                return {
                    'precursor_df': precursor_df,
                    'fragment_mz_df': fragment_mz_df,
                    'fragment_intensity_df': fragment_intensity_df,
                }
            else:
                precursor_df = pd.concat(precursor_df_list)
                precursor_df.reset_index(drop=True, inplace=True)

                return {'precursor_df': precursor_df}
