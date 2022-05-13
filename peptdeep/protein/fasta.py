# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/protein/fasta.ipynb (unless otherwise specified).

__all__ = ['protease_dict', 'read_fasta_file', 'load_all_proteins', 'concat_proteins', 'cleave_sequence_with_cut_pos',
           'Digest', 'get_fix_mods', 'get_candidate_sites', 'get_var_mod_sites',
           'get_var_mods_per_sites_multi_mods_on_aa', 'get_var_mods_per_sites_single_mod_on_aa', 'get_var_mods',
           'get_var_mods_per_sites', 'parse_term_mod', 'add_single_peptide_labeling', 'parse_labels',
           'create_labeling_peptide_df', 'protein_idxes_to_names', 'PredictFastaSpecLib',
           'append_regular_modifications']

# Cell
import regex as re
import numpy as np
import pandas as pd
import numba
import os
import itertools
from Bio import SeqIO
from typing import Union

from alphabase.yaml_utils import load_yaml
from alphabase.io.hdf import HDF_File
from peptdeep.spec_lib.predict_lib import PredictSpecLib
from peptdeep.pretrained_models import ModelManager
from peptdeep.utils import explode_multiple_columns

protease_dict = load_yaml(
    os.path.join(
        os.path.dirname(
            __file__
        ),
        'protease.yaml'
    )
)

# Cell

def read_fasta_file(fasta_filename:str=""):
    """
    Read a FASTA file line by line
    Args:
        fasta_filename (str): fasta.
    Yields:
        dict {id:str, name:str, description:str, sequence:str}: protein information.
    """
    with open(fasta_filename, "rt") as handle:
        iterator = SeqIO.parse(handle, "fasta")
        while iterator:
            try:
                record = next(iterator)
                parts = record.id.split("|")  # pipe char
                if len(parts) > 1:
                    id = parts[1]
                else:
                    id = record.name
                sequence = str(record.seq)
                entry = {
                    "id": id,
                    "full_name": record.name,
                    "description": record.description,
                    "sequence": sequence,
                }

                yield entry
            except StopIteration:
                break

def load_all_proteins(fasta_file_list:list):
    protein_dict = {}
    for fasta in fasta_file_list:
        for protein in read_fasta_file(fasta):
            protein_dict[protein['id']] = protein
    return protein_dict

def concat_proteins(protein_dict:dict)->str:
    """Concatenate all protein sequences into a single sequence

    Args:
        protein_dict (dict): protein_dict by read_fasta_file()

    Returns:
        str: concatenated sequence
    """
    seq_list = ['']
    seq_count = 1
    for key in protein_dict:
        protein_dict[key]['offset'] = seq_count
        seq_list.append(protein_dict[key]['sequence'])
        seq_count += protein_dict[key]['sequence']+1
    seq_list.append('')
    return '$'.join(seq_list)

# Cell
@numba.njit
def cleave_sequence_with_cut_pos(
    sequence:str,
    cut_pos:np.ndarray,
    n_missed_cleavages:int=2,
    pep_length_min:int=6,
    pep_length_max:int=45,
)->np.ndarray:
    """
    Cleave a sequence with cut postions (cut_pos).
    Filters to have a minimum and maximum length.
    Args:
        sequence (str): protein sequence
        cut_pos (np.array): cut postions determined by a given protease.
        n_missed_cleavages (int): the number of max missed cleavages.
        pep_length_min (int): min peptide length.
        pep_length_max (int): max peptide length.
    Returns:
        list (str): cleaved peptide sequences with missed cleavages.
        list (int): number of miss cleavage of each peptide.
        list (bool): if N-term peptide
        list (bool): if C-term pepetide
    """
    seq_list = []
    miss_list = []
    nterm_list = []
    cterm_list = []
    for i,start_pos in enumerate(cut_pos):
        for n_miss,end_pos in enumerate(
            cut_pos[i+1:i+2+n_missed_cleavages]
        ):
            if end_pos > start_pos + pep_length_max:
                break
            elif end_pos < start_pos + pep_length_min:
                continue
            else:
                seq_list.append(sequence[start_pos:end_pos])
                miss_list.append(n_miss)
                if start_pos == 0:
                    nterm_list.append(True)
                else:
                    nterm_list.append(False)
                if end_pos == len(sequence):
                    cterm_list.append(True)
                else:
                    cterm_list.append(False)
    return seq_list, miss_list, nterm_list, cterm_list

class Digest(object):
    def __init__(self,
        protease:str='trypsin',
        max_missed_cleavages:int=2,
        peptide_length_min:int=6,
        peptide_length_max:int=45,
    ):
        self.n_miss_cleave = max_missed_cleavages
        self.peptide_length_min = peptide_length_min
        self.peptide_length_max = peptide_length_max
        if protease in protease_dict:
            self.regex_pattern = re.compile(
                protease_dict[protease]
            )
        else:
            self.regex_pattern = re.compile(
                protease
            )

    def cleave_sequence(self,
        sequence:str,
    )->list:
        """
        Cleave a sequence.
        Args:
            sequence (str): the given (protein) sequence.
        Returns:
            list (of str): cleaved peptide sequences with missed cleavages.
        """

        cut_pos = [0]
        cut_pos.extend([
            m.start()+1 for m in
            self.regex_pattern.finditer(sequence)
        ])
        cut_pos.append(len(sequence))
        cut_pos = np.array(cut_pos, dtype=np.int64)

        (
            seq_list, miss_list, nterm_list, cterm_list
        ) = cleave_sequence_with_cut_pos(
            sequence, cut_pos,
            self.n_miss_cleave,
            self.peptide_length_min,
            self.peptide_length_max,
        )
        # Consider M loss at protein N-term
        if sequence.startswith('M'):
            for seq,miss,cterm in zip(
                seq_list,miss_list,cterm_list
            ):
                if (
                    sequence.startswith(seq)
                    and len(seq)>self.peptide_length_min
                ):
                    seq_list.append(seq[1:])
                    miss_list.append(miss)
                    nterm_list.append(True)
                    cterm_list.append(cterm)
        return seq_list, miss_list, nterm_list, cterm_list

# Cell
def get_fix_mods(
    sequence:str,
    fix_mod_aas:str,
    fix_mod_dict:dict
)->tuple:
    mods = []
    mod_sites = []
    for i,aa in enumerate(sequence):
        if aa in fix_mod_aas:
            mod_sites.append(i+1)
            mods.append(fix_mod_dict[aa])
    return ';'.join(mods), ';'.join(str(i) for i in mod_sites)

# Cell
def get_candidate_sites(
    sequence:str, target_mod_aas:str
)->list:
    """get candidate modification sites

    Args:
        sequence (str): peptide sequence
        target_mod_aas (str): AAs that may have modifications

    Returns:
        list: candiadte mod sites in alphabase format (0: N-term, -1: C-term, 1-n:others)
    """
    candidate_sites = []
    for i,aa in enumerate(sequence):
        if aa in target_mod_aas:
            candidate_sites.append(i+1) #alphabase mod sites
    return candidate_sites

def get_var_mod_sites(
    sequence:str,
    target_mod_aas:str,
    max_var_mod: int,
    max_combs: int,
)->list:
    """get all combinations of variable modification sites

    Args:
        sequence (str): peptide sequence
        target_mod_aas (str): AAs that may have modifications
        max_var_mod (int): max number of mods in a sequence
        max_combs (int): max number of combinations for a sequence

    Returns:
        list: list of combinations of (tuple) modification sites
    """
    candidate_sites = get_candidate_sites(
        sequence, target_mod_aas
    )
    mod_sites = [(s,) for s in candidate_sites]
    for n_var_mod in range(2, max_var_mod+1):
        if len(mod_sites)>=max_combs: break
        mod_sites.extend(
            itertools.islice(
                itertools.combinations(
                    candidate_sites, n_var_mod
                ),
                max_combs-len(mod_sites)
            )
        )
    return mod_sites

# Cell
import copy
def get_var_mods_per_sites_multi_mods_on_aa(
    sequence:str,
    mod_sites:tuple,
    var_mod_dict:dict
)->list:
    mods_str_list = ['']
    for i,site in enumerate(mod_sites):
        if len(var_mod_dict[sequence[site-1]]) == 1:
            for i in range(len(mods_str_list)):
                mods_str_list[i] += var_mod_dict[sequence[site-1]][0]+';'
        else:
            _new_list = []
            for mod in var_mod_dict[sequence[site-1]]:
                _lst = copy.deepcopy(mods_str_list)
                for i in range(len(_lst)):
                    _lst[i] += mod+';'
                _new_list.extend(_lst)
            mods_str_list = _new_list
    return [mod[:-1] for mod in mods_str_list]

def get_var_mods_per_sites_single_mod_on_aa(
    sequence:str,
    mod_sites:tuple,
    var_mod_dict:dict
)->list:
    mod_str = ''
    for site in mod_sites:
            mod_str += var_mod_dict[sequence[site-1]]+';'
    return [mod_str[:-1]]

get_var_mods_per_sites = get_var_mods_per_sites_single_mod_on_aa

def get_var_mods(
    sequence:str,
    var_mod_aas:str,
    mod_dict:dict,
    max_var_mod:int,
    max_combs:int,
    keep_unmodified:bool=False,
)->tuple:
    mod_sites_list = get_var_mod_sites(
        sequence, var_mod_aas,
        max_var_mod, max_combs
    )
    ret_mods = []
    ret_sites_list = []
    for mod_sites in mod_sites_list:
        _mods = get_var_mods_per_sites(
            sequence,mod_sites,mod_dict
        )
        mod_sites_str = ';'.join([str(i) for i in mod_sites])
        ret_mods.extend(_mods)
        ret_sites_list.extend([mod_sites_str]*len(_mods))
    if keep_unmodified:
        ret_mods.append('')
        ret_sites_list.append('')
    return ret_mods, ret_sites_list

# Cell
def parse_term_mod(term_mod_name:str):
    _mod, term = term_mod_name.split('@')
    if '^' in term:
        return tuple(term.split('^'))
    else:
        return '', term

# Cell
def add_single_peptide_labeling(
    seq:str,
    mods:str,
    mod_sites:str,
    label_aas:str,
    label_mod_dict:dict,
    nterm_label_mod:str,
    cterm_label_mod:str
):
    add_nterm_label = True if nterm_label_mod else False
    add_cterm_label = True if cterm_label_mod else False
    if mod_sites:
        _sites = mod_sites.split(';')
        if '0' in _sites: add_nterm_label = False
        if '-1' in _sites: add_cterm_label = False
        mod_list = [mods]
        mod_site_list = [mod_sites]
    else:
        mod_list = []
        mod_site_list = []
    if add_nterm_label:
        mod_list.append(nterm_label_mod)
        mod_site_list.append('0')
    if add_cterm_label:
        mod_list.append(cterm_label_mod)
        mod_site_list.append('-1')
    aa_labels, aa_label_sites = get_fix_mods(seq, label_aas, label_mod_dict)
    if aa_labels:
        mod_list.append(aa_labels)
        mod_site_list.append(aa_label_sites)
    return ';'.join(mod_list), ';'.join(mod_site_list)

def parse_labels(labels:list):
    label_aas = ''
    label_mod_dict = {}
    nterm_label_mod = ''
    cterm_label_mod = ''
    for label in labels:
        _, aa = label.split('@')
        if len(aa) == 1:
            label_aas += aa
            label_mod_dict[aa] = label
        elif aa == 'Any N-term':
            nterm_label_mod = label
        elif aa == 'Any C-term':
            cterm_label_mod = label
    return label_aas, label_mod_dict, nterm_label_mod, cterm_label_mod

def create_labeling_peptide_df(peptide_df:pd.DataFrame, labels:list):
    df = peptide_df.copy()
    (
        label_aas, label_mod_dict,
        nterm_label_mod, cterm_label_mod
    ) = parse_labels(labels)

    (
        df['mods'],
        df['mod_sites']
    ) = zip(*df[
        ['sequence','mods','mod_sites']
    ].apply(lambda x:
        add_single_peptide_labeling(
            *x, label_aas, label_mod_dict,
            nterm_label_mod, cterm_label_mod
        ), axis=1,
    ))

    return df

# Cell
def protein_idxes_to_names(protein_idxes:str, protein_names:list):
    if len(protein_idxes) == 0: return ''
    return ';'.join(protein_names[int(i)] for i in protein_idxes.split(';'))

# Cell

class PredictFastaSpecLib(PredictSpecLib):
    def __init__(self,
        model_manager:ModelManager = None,
        charged_frag_types:list = ['b_z1','b_z2','y_z1','y_z2'],
        protease:str = 'trypsin',
        max_missed_cleavages:int = 2,
        peptide_length_min:int = 7,
        peptide_length_max:int = 35,
        precursor_charge_min:int = 2,
        precursor_charge_max:int = 4,
        precursor_mz_min:float = 200.0,
        precursor_mz_max:float = 2000.0,
        var_mods:list = ['Acetyl@Protein N-term','Oxidation@M'],
        max_var_mod_num:int = 2,
        fix_mods:list = ['Carbamidomethyl@C'],
        decoy: str = None, # or pseudo_reverse or diann
        I_to_L=False,
    ):
        super().__init__(
            model_manager,
            charged_frag_types=charged_frag_types,
            precursor_mz_min=precursor_mz_min,
            precursor_mz_max=precursor_mz_max,
            decoy=decoy
        )
        self.protein_df:pd.DataFrame() = pd.DataFrame()
        self.I_to_L = I_to_L
        self.max_mod_combinations = 100
        self._digest = Digest(
            protease, max_missed_cleavages,
            peptide_length_min, peptide_length_max
        )
        self.precursor_charge_min = precursor_charge_min
        self.precursor_charge_max = precursor_charge_max

        self.var_mods = var_mods
        self.fix_mods = fix_mods
        self.max_var_mod_num = max_var_mod_num

        self.decoy = decoy

        self.fix_mod_aas = ''
        self.fix_mod_prot_nterm_dict = {}
        self.fix_mod_prot_cterm_dict = {}
        self.fix_mod_pep_nterm_dict = {}
        self.fix_mod_pep_cterm_dict = {}
        self.fix_mod_dict = {}

        def _set_term_mod(term_mod,
            prot_nterm, prot_cterm, pep_nterm, pep_cterm,
            allow_conflicts
        ):
            def _set_dict(term_dict,site,mod,
                allow_conflicts
            ):
                if allow_conflicts:
                    if site in term_dict:
                        term_dict[site].append(term_mod)
                    else:
                        term_dict[site] = [term_mod]
                else:
                    term_dict[site] = term_mod
            site, term = parse_term_mod(term_mod)
            if term == "Any N-term":
                _set_dict(pep_nterm, site, term_mod,
                    allow_conflicts
                )
            elif term == 'Protein N-term':
                _set_dict(prot_nterm, site, term_mod,
                    allow_conflicts
                )
            elif term == 'Any C-term':
                _set_dict(pep_cterm, site, term_mod,
                    allow_conflicts
                )
            elif term == 'Protein C-term':
                _set_dict(prot_cterm, site, term_mod,
                    allow_conflicts
                )

        for mod in fix_mods:
            if mod.find('@')+2 == len(mod):
                self.fix_mod_aas += mod[-1]
                self.fix_mod_dict[mod[-1]] = mod
            else:
                _set_term_mod(
                    mod,
                    self.fix_mod_prot_nterm_dict,
                    self.fix_mod_prot_cterm_dict,
                    self.fix_mod_pep_nterm_dict,
                    self.fix_mod_pep_cterm_dict,
                    allow_conflicts=False
                )

        self.var_mod_aas = ''
        self.var_mod_prot_nterm_dict = {}
        self.var_mod_prot_cterm_dict = {}
        self.var_mod_pep_nterm_dict = {}
        self.var_mod_pep_cterm_dict = {}
        self.var_mod_dict = {}

        global get_var_mods_per_sites
        if self._check_if_multi_mods_on_aa(var_mods):
            for mod in var_mods:
                if mod.find('@')+2 == len(mod):
                    if mod[-1] in self.fix_mod_dict: continue
                    self.var_mod_aas += mod[-1]
                    if mod[-1] in self.var_mod_dict:
                        self.var_mod_dict[mod[-1]].append(mod)
                    else:
                        self.var_mod_dict[mod[-1]] = [mod]
            get_var_mods_per_sites = get_var_mods_per_sites_multi_mods_on_aa
        else:
            for mod in var_mods:
                if mod.find('@')+2 == len(mod):
                    if mod[-1] in self.fix_mod_dict: continue
                    self.var_mod_aas += mod[-1]
                    self.var_mod_dict[mod[-1]] = mod
            get_var_mods_per_sites = get_var_mods_per_sites_single_mod_on_aa

        for mod in var_mods:
            if mod.find('@')+2 < len(mod):
                _set_term_mod(
                    mod,
                    self.var_mod_prot_nterm_dict,
                    self.var_mod_prot_cterm_dict,
                    self.var_mod_pep_nterm_dict,
                    self.var_mod_pep_cterm_dict,
                    allow_conflicts=True
                )

    def _check_if_multi_mods_on_aa(self, var_mods):
        mod_set = set()
        for mod in var_mods:
            if mod.find('@')+2 == len(mod):
                if mod[-1] in mod_set: return True
                mod_set.add(mod[-1])
        return False

    def import_fasta(self, fasta_files:Union[str,list]):
        self.from_fasta(fasta_files)
        self._preprocessing_after_load_pep_seqs()

    def import_protein_dict(self, protein_dict:dict):
        self.from_protein_dict(protein_dict)
        self._preprocessing_after_load_pep_seqs()

    def import_peptide_sequences(self,
        pep_seq_list:list, protein_list
    ):
        self.from_peptide_sequence_list(pep_seq_list, protein_list)
        self._preprocessing_after_load_pep_seqs()

    def _preprocessing_after_load_pep_seqs(self):
        self.append_decoy_sequence()
        self.add_modifications()
        self.add_charge()

    def from_fasta(self, fasta_file:Union[str,list]):
        """Load peptide sequence from fasta file.

        Args:
            fasta_path (Union[str,list]): could be a fasta path or a list of fasta paths
              or a list of fasta paths
        """
        if isinstance(fasta_file, str):
            self.from_fasta_list([fasta_file])
        else:
            self.from_fasta_list(fasta_file)

    def from_fasta_list(self, fasta_files:list):
        """Load peptide sequences from fasta file list

        Args:
            fasta_files (list): fasta file list
        """
        protein_dict = load_all_proteins(fasta_files)
        self.from_protein_dict(protein_dict)

    def from_protein_dict(self, protein_dict:dict):
        pep_dict = {}

        self.protein_df = pd.DataFrame.from_dict(
            protein_dict, orient='index'
        ).reset_index(drop=True)

        if self.I_to_L:
            self.protein_df[
                'sequence_I2L'
            ] = self.protein_df.sequence.str.replace('I','L')
            digest_seq = 'sequence_I2L'
        else:
            digest_seq = 'sequence'

        for i,prot_seq in enumerate(
            self.protein_df[digest_seq].values
        ):
            (
                seq_list, miss_list, nterm_list, cterm_list
            ) = self._digest.cleave_sequence(prot_seq)
            for seq,miss,nterm,cterm in zip(
                seq_list,miss_list,nterm_list, cterm_list
            ):
                if seq in pep_dict:
                    pep_dict[seq][0] += ';'+str(i)
                    if nterm:
                        pep_dict[seq][2] = nterm
                    if cterm:
                        pep_dict[seq][3] = cterm
                else:
                    pep_dict[seq] = [str(i),miss,nterm,cterm]
        self._precursor_df = pd.DataFrame().from_dict(
            pep_dict, orient='index', columns = [
                'protein_idxes','miss_cleavage',
                'is_prot_nterm','is_prot_cterm'
            ]
        )
        self._precursor_df.reset_index(drop=False, inplace=True)
        self._precursor_df.rename(
            columns={'index':'sequence'}, inplace=True
        )
        self._precursor_df['mods'] = ''
        self._precursor_df['mod_sites'] = ''
        self.refine_df()

    def append_protein_name(self):
        if (
            'id' not in self.protein_df or
            'protein_idxes' not in self._precursor_df
        ):
            return

        self._precursor_df['proteins'] = self._precursor_df['protein_idxes'].apply(
            protein_idxes_to_names,
            protein_names=self.protein_df['id'].values
        )


    def from_peptide_sequence_list(self,
        pep_seq_list:list,
        protein_list:list = None
    ):
        self._precursor_df = pd.DataFrame()
        self._precursor_df['sequence'] = pep_seq_list
        if protein_list is not None:
            self._precursor_df['protein_name'] = protein_list
        self._precursor_df['is_prot_nterm'] = False
        self._precursor_df['is_prot_cterm'] = False
        self.refine_df()

    def add_mods_for_one_seq(self, sequence:str,
        is_prot_nterm, is_prot_cterm
    ):
        fix_mods, fix_mod_sites = get_fix_mods(
            sequence, self.fix_mod_aas, self.fix_mod_dict
        )
        #TODO add prot and pep C-term fix mods
        #TODO add prot and pep N-term fix mods

        if len(fix_mods) == 0:
            fix_mods = ['']
            fix_mod_sites = ['']
        else:
            fix_mods = [fix_mods]
            fix_mod_sites = [fix_mod_sites]

        var_mods_list, var_mod_sites_list = get_var_mods(
            sequence, self.var_mod_aas, self.var_mod_dict,
            self.max_var_mod_num, self.max_mod_combinations-1, # 1 for unmodified
            keep_unmodified=True
        )

        nterm_var_mods = ['']
        nterm_var_mod_sites = ['']
        if is_prot_nterm and len(self.var_mod_prot_nterm_dict)>0:
            if '' in self.var_mod_prot_nterm_dict:
                nterm_var_mods.extend(self.var_mod_prot_nterm_dict[''])
            if sequence[0] in self.var_mod_prot_nterm_dict:
                nterm_var_mods.extend(self.var_mod_prot_nterm_dict[sequence[0]])
        if len(self.var_mod_pep_nterm_dict)>0:
            if '' in self.var_mod_pep_nterm_dict:
                nterm_var_mods.extend(self.var_mod_pep_nterm_dict[''])
            if sequence[0] in self.var_mod_pep_nterm_dict:
                nterm_var_mods.extend(self.var_mod_pep_nterm_dict[sequence[0]])
        nterm_var_mod_sites.extend(['0']*(len(nterm_var_mods)-1))

        #TODO add prot and pep C-term var mods

        return (
            list(
                ';'.join([i for i in items if i]) for items in itertools.product(
                    fix_mods, nterm_var_mods, var_mods_list
                )
            ),
            list(
                ';'.join([i for i in items if i]) for items in itertools.product(
                    fix_mod_sites, nterm_var_mod_sites, var_mod_sites_list
                )
            ),
        )

    def add_modifications(self):
        if 'is_prot_nterm' not in self._precursor_df.columns:
            self._precursor_df['is_prot_nterm'] = False
        if 'is_prot_cterm' not in self._precursor_df.columns:
            self._precursor_df['is_prot_cterm'] = False

        (
            self._precursor_df['mods'],
            self._precursor_df['mod_sites']
        ) = zip(*self._precursor_df[
            ['sequence','is_prot_nterm','is_prot_cterm']
        ].apply(lambda x:
            self.add_mods_for_one_seq(*x), axis=1
        ))
        self._precursor_df = explode_multiple_columns(
            self._precursor_df,
            ['mods','mod_sites']
        )
        self._precursor_df.reset_index(drop=True, inplace=True)

    def add_peptide_labeling(self, labeling_channel_dict:dict):
        """
        Add labeling onto peptides inplace of self._precursor_df

        Args:
            labeling_channel_dict (dict of list): for example:
              {
                  'reference': [], # not labelled for reference
                  'light': ['Dimethyl@Any N-term','Dimethyl@K'],
                  'median': ['Dimethyl:2H(4)@Any N-term','Dimethyl:2H(4)@K'],
                  'heavy': ['Dimethyl:2H(6)13C(2)@Any N-term','Dimethyl:2H(6)13C(2)@K'],
              }.
              The key name could be arbitrary distinguished strings, and value must be a list of string.

        """
        df_list = []
        for channel, labels in labeling_channel_dict.items():
            df = create_labeling_peptide_df(self._precursor_df, labels)
            df['label_channel'] = channel
            df_list.append(df)
        self._precursor_df = pd.concat(df_list)
        self._precursor_df.reset_index(drop=True, inplace=True)

    def add_charge(self):
        self._precursor_df['charge'] = [
            np.arange(
                self.precursor_charge_min,
                self.precursor_charge_max+1
            )
        ]*len(self._precursor_df)
        self._precursor_df = self._precursor_df.explode('charge')
        self._precursor_df['charge'] = self._precursor_df.charge.astype(np.int8)
        self._precursor_df.reset_index(drop=True, inplace=True)

    def save_hdf(self, hdf_file):
        super().save_hdf(hdf_file)
        _hdf = HDF_File(
            hdf_file,
            read_only=False,
            truncate=True,
            delete_existing=False
        )
        _hdf.library.protein_df = self.protein_df

# Cell
def append_regular_modifications(df:pd.DataFrame,
    var_mods = ['Phospho@S','Phospho@T','Phospho@Y'],
    max_mod_num=1, max_combs=100,
    keep_unmodified=True,
):
    mod_dict = dict([(mod[-1],mod) for mod in var_mods])
    var_mod_aas = ''.join(mod_dict.keys())

    (
        df['mods_app'],
        df['mod_sites_app']
    ) = zip(*df.sequence.apply(get_var_mods,
            var_mod_aas=var_mod_aas, mod_dict=mod_dict,
            max_var_mod=max_mod_num, max_combs=max_combs,
            keep_unmodified=keep_unmodified
        )
    )

    if keep_unmodified:
        df = df.explode(['mods_app','mod_sites_app'])
        df.fillna('', inplace=True)
    else:
        df.drop(df[df.mods_app.apply(lambda x: len(x)==0)].index, inplace=True)
        df = df.explode(['mods_app','mod_sites_app'])
    df['mods'] = df[['mods','mods_app']].apply(
        lambda x: ';'.join(i for i in x if i), axis=1
    )
    df['mod_sites'] = df[['mod_sites','mod_sites_app']].apply(
        lambda x: ';'.join(i for i in x if i), axis=1
    )
    df.drop(columns=['mods_app', 'mod_sites_app'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df