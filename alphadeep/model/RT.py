# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/model/RT.ipynb (unless otherwise specified).

__all__ = ['mod_feature_size', 'EncDecModelRT', 'AlphaRTModel', 'evaluate_linear_regression',
           'evaluate_linear_regression_plot']

# Cell
import torch
import pandas as pd
import numpy as np

from tqdm import tqdm

from alphadeep.model.featurize import \
    parse_aa_indices, \
    get_batch_mod_feature

from alphadeep._settings import model_const

import alphadeep.model.base as model_base


mod_feature_size = len(model_const['mod_elements'])


# Cell
class EncDecModelRT(torch.nn.Module):
    def __init__(self,
        dropout=0.2
    ):
        super().__init__()
        self.aa_embedding_size = 27

        self.dropout = torch.nn.Dropout(dropout)

        hidden = 256
        self.rt_encoder = model_base.Input_AA_CNN_LSTM_Encoder(
            hidden
        )

        self.rt_decoder = model_base.LinearDecoder(
            hidden,
            1
        )

    def forward(self,
        aa_indices,
        mod_x,
    ):
        x = self.rt_encoder(aa_indices, mod_x)
        x = self.dropout(x)

        return self.rt_decoder(x).squeeze(1)

# Cell
class AlphaRTModel(model_base.ModelImplBase):
    def __init__(self, dropout=0.2, lr=0.001):
        super().__init__()
        self.build(
            EncDecModelRT, lr=lr,
            dropout=dropout,
        )
        self.loss_func = torch.nn.L1Loss()

    def _prepare_predict_data_df(self,
        precursor_df:pd.DataFrame,
    ):
        precursor_df['predict_RT'] = 0
        self.predict_df = precursor_df

    def _get_features_from_batch_df(self,
        batch_df: pd.DataFrame,
        nAA
    ):
        aa_indices = torch.LongTensor(
            parse_aa_indices(
                batch_df['sequence'].values.astype('U')
            )
        )

        mod_x_batch = get_batch_mod_feature(batch_df, nAA)
        mod_x = torch.Tensor(mod_x_batch)

        return aa_indices, mod_x

    def _get_targets_from_batch_df(self,
        batch_df: pd.DataFrame,
        nAA
    ) -> torch.Tensor:
        return torch.Tensor(batch_df['RT'].values)

    def _set_batch_predict_data(self,
        batch_df: pd.DataFrame,
        predicts,
    ):
        self.predict_df.loc[batch_df.index,'predict_RT'] = predicts

# Cell
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate_linear_regression(df, x='predict_RT', y='RT', ci=0.95):
    gls = sm.GLS(df[y], sm.add_constant(df[x]))
    res = gls.fit()
    summary = res.summary(alpha=1-ci)
    return summary

def evaluate_linear_regression_plot(df, x='predict_RT', y='RT', ci=95):
    sns.regplot(data=df, x=x, y=y, color='r', ci=ci, scatter_kws={'s':0.05, 'alpha':0.05, 'color':'b'})
    plt.show()