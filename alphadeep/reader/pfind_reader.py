# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/reader/pfind_reader.ipynb (unless otherwise specified).

__all__ = ['convert_one_pFind_mod', 'translate_pFind_mod', 'get_pFind_mods', 'remove_pFind_decoy_protein',
           'pFindReader', 'PSMLabelReader', 'load_psmlabel_list']

# Cell
import pandas as pd
import numpy as np
import typing
from tqdm import tqdm

import alphabase.constants.modification as ap_mod
from alphabase.peptide.fragment import \
    concat_precursor_fragment_dataframes,\
    init_fragment_by_precursor_dataframe


from alphadeep.reader.psm_reader import \
    PSMReaderBase, psm_reader_provider, \
    PSMReader_w_FragBase, psm_w_frag_reader_provider


def convert_one_pFind_mod(mod):
    if mod[-1] == ')':
        mod = mod[:(mod.find('(')-1)]
        idx = mod.rfind('[')
        name = mod[:idx]
        site = mod[(idx+1):]
    else:
        idx = mod.rfind('[')
        name = mod[:idx]
        site = mod[(idx+1):-1]
    if len(site) == 1:
        return name + '@' + site
    elif site == 'AnyN-term':
        return name + '@' + 'Any N-term'
    elif site == 'ProteinN-term':
        return name + '@' + 'Protein N-term'
    elif site.startswith('AnyN-term'):
        return name + '@' + site[-1] + '^Any N-term'
    elif site.startswith('ProteinN-term'):
        return name + '@' + site[-1] + '^Protein N-term'
    elif site == 'AnyC-term':
        return name + '@' + 'Any C-term'
    elif site == 'ProteinC-term':
        return name + '@' + 'Protein C-term'
    elif site.startswith('AnyC-term'):
        return name + '@' + site[-1] + '^Any C-term'
    elif site.startswith('ProteinC-term'):
        return name + '@' + site[-1] + '^Protein C-term'
    else:
        return None

def translate_pFind_mod(mod_str):
    if not mod_str: return ""
    ret_mods = []
    for mod in mod_str.split(';'):
        mod = convert_one_pFind_mod(mod)
        if not mod: return pd.NA
        elif mod not in ap_mod.MOD_INFO_DICT: return pd.NA
        else: ret_mods.append(mod)
    return ';'.join(ret_mods)

def get_pFind_mods(pfind_mod_str):
    pfind_mod_str = pfind_mod_str.strip(';')
    if not pfind_mod_str: return "", ""

    items = [item.split(',',3) for item in pfind_mod_str.split(';')]
    items = list(zip(*items))
    return ';'.join(items[1]), ';'.join(items[0])

def remove_pFind_decoy_protein(protein):
    proteins = protein[:-1].split('/')
    return ';'.join([protein for protein in proteins if not protein.startswith('REV_')])


# Cell
class pFindReader(PSMReaderBase):
    def __init__(self,
        frag_types=['b','y','b_modloss','y_modloss'],
        max_frag_charge=2,
        frag_tol=20, frag_ppm=True,
    ):
        super().__init__(
            frag_types=frag_types,
            max_frag_charge=max_frag_charge,
            frag_tol=frag_tol, frag_ppm=frag_ppm
        )

        self.column_mapping = {
            'sequence': 'Sequence',
            'charge': 'Charge',
            'RT': 'RT',
            'CCS': 'CCS',
            'raw_name': 'raw_name',
            'msms_id': 'File_Name',
            'scan_no': 'Scan_No',
            'score': 'score',
            'proteins': 'Proteins',
            'uniprot_ids': 'uniprot_ids',
            'genes': 'genes',
            'q_value': 'Q-value',
            'decoy': 'decoy'
        }

    def _translate_modifications(self):
        pass

    def _post_process(self, filename: str, origin_df: pd.DataFrame):
        pass

    def _load_file(self, filename):
        pfind_df = pd.read_csv(filename, index_col=False, sep='\t')
        pfind_df.fillna('', inplace=True)
        columns = pfind_df.columns.values.copy()
        pfind_df = pfind_df.iloc[:,:len(columns)]
        pfind_df['raw_name'] = pfind_df['File_Name'].str.split('.').apply(lambda x: x[0])
        pfind_df['score'] = -np.log(pfind_df['Final_Score'].values)
        pfind_df['Proteins'] = pfind_df['Proteins'].apply(remove_pFind_decoy_protein)
        pfind_df['decoy'] = (pfind_df['Target/Decoy']=='decoy').astype(int)
        pfind_df['uniprot_ids'] = ''
        pfind_df['genes'] = ''
        return pfind_df

    def _translate_columns(self, pfind_df):
        super()._translate_columns(pfind_df)
        self._psm_df['mods'], self._psm_df['mod_sites'] = zip(*pfind_df['Modification'].apply(get_pFind_mods))

        self._psm_df['mods'] = self._psm_df['mods'].apply(translate_pFind_mod)
        self._psm_df = self._psm_df[~self._psm_df['mods'].isna()]

psm_reader_provider.register_reader('pfind', pFindReader)
psm_w_frag_reader_provider.register_reader('pfind', pFindReader)

# Cell

class PSMLabelReader(pFindReader, PSMReader_w_FragBase):
    def __init__(self,
        frag_types=['b','y','b_modloss','y_modloss'],
        max_frag_charge=2,
        frag_tol=20, frag_ppm=True,
    ):
        super().__init__(
            frag_types=frag_types,
            max_frag_charge=max_frag_charge,
            frag_tol=frag_tol, frag_ppm=frag_ppm
        )

        self.column_mapping = {
            'sequence': 'peptide',
            'charge': 'charge',
            'RT': 'RT',
            'CCS': 'CCS',
            'raw_name': 'raw_name',
            'msms_id': 'File_Name',
            'scan_no': 'scan_no',
        }

        psmlabel_columns = 'b,b-NH3,b-H20,b-ModLoss,y,y-HN3,y-H20,y-ModLoss'.split(',')
        self.psmlabel_frag_columns = []
        self.frag_df_columns = {}
        for _type in psmlabel_columns:
            frag_idxes = [
                i for i,_t in enumerate(
                    self.charged_frag_types
                ) if _t.startswith(_type.replace('-','_').lower()+'_')
            ]
            if frag_idxes:
                self.psmlabel_frag_columns.append(_type)
                self.frag_df_columns[_type] = np.array(
                    frag_idxes, dtype=int
                )

    def _load_file(self, filename):
        psmlabel_df = pd.read_csv(filename, sep="\t")
        psmlabel_df.fillna('', inplace=True)

        psmlabel_df['raw_name'], psmlabel_df['scan_no'], psmlabel_df['charge'] = zip(
            *psmlabel_df['spec'].str.split('.').apply(lambda x: (x[0], x[-4], x[-3]))
        )
        psmlabel_df['scan_no'] = psmlabel_df['scan_no'].astype(int)
        psmlabel_df['charge'] = psmlabel_df['charge'].astype(int)
        return psmlabel_df

    def _translate_columns(self, psmlabel_df):
        PSMReader_w_FragBase._translate_columns(self, psmlabel_df)
        (
            self._psm_df['mods'], self._psm_df['mod_sites']
        ) = zip(*psmlabel_df['modinfo'].apply(get_pFind_mods))
        self._psm_df['mods'] = self._psm_df['mods'].apply(translate_pFind_mod)

    def _post_process(self, filename: str, psmlabel_df: pd.DataFrame):
        psmlabel_df = psmlabel_df[
            ~self._psm_df['mods'].isna()
        ].reset_index(drop=True)

        self._psm_df = self._psm_df[
            ~self._psm_df['mods'].isna()
        ].reset_index(drop=True)

        self._fragment_inten_df = init_fragment_by_precursor_dataframe(
            psmlabel_df, self.charged_frag_types
        )

        for ith_psm, (nAA, start,end) in enumerate(
            psmlabel_df[['nAA','frag_start_idx','frag_end_idx']].values
        ):
            intens = np.zeros((nAA-1, len(self.charged_frag_types)))
            for ion_type in self.psmlabel_frag_columns:
                if ion_type not in psmlabel_df.columns: continue

                pos_end = ion_type.find('-')-len(ion_type)-2 if '-' in ion_type else -2
                typed_frags = psmlabel_df.loc[ith_psm,ion_type]
                if not typed_frags: continue
                typed_frags = typed_frags.strip(';').split(';')
                frag_pos = []
                frag_charge = []
                frag_inten = []

                for frag in typed_frags:
                    frag, inten = frag.split(',')
                    frag_pos.append(int(frag[1:pos_end]))
                    frag_charge.append(int(frag[-1]))
                    frag_inten.append(float(inten))
                if not frag_inten: continue

                frag_pos = np.array(frag_pos, dtype=int)
                frag_col = np.array(frag_charge, dtype=int)-1

                if ion_type[0] in 'xyz':
                    frag_pos = nAA - frag_pos -1
                else:
                    frag_pos -= 1
                intens[frag_pos,self.frag_df_columns[ion_type][frag_col]] = frag_inten
            if np.any(intens>0):
                intens /= np.max(intens)
            self._fragment_inten_df.iloc[
                start:end,:
            ] = intens

        self._psm_df[
            ['frag_start_idx','frag_end_idx']
        ] = psmlabel_df[['frag_start_idx','frag_end_idx']]

psm_reader_provider.register_reader('psmlabel', PSMLabelReader)
psm_w_frag_reader_provider.register_reader(
    'psmlabel', PSMLabelReader
)

# Cell
def load_psmlabel_list(
    psmlabel_list,
    nce_list,
    instrument_list,
    frag_types=['b','y','b_modloss','y_modloss'],
    frag_charge=2,
    include_mod_list=[
        'Oxidation@M','Phospho@S','Phospho@T','Phospho@Y','Acetyl@Protein N-term'
    ]
):
    psm_df_list = []
    fragment_inten_df_list = []
    for i,psmlabel in tqdm(enumerate(psmlabel_list)):
        psm_reader = PSMLabelReader(
            frag_types=frag_types,
            max_frag_charge = frag_charge
        )
        psm_reader.load(psmlabel)
        psm_reader.filter_psm_by_modifications(include_mod_list)
        psm_reader.psm_df['NCE'] = nce_list[i]
        psm_reader.psm_df['instrument'] = instrument_list[i]
        psm_df_list.append(psm_reader.psm_df)
        fragment_inten_df_list.append(psm_reader.fragment_inten_df)
    return concat_precursor_fragment_dataframes(psm_df_list, fragment_inten_df_list)
