# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/protein/lcp_digest.ipynb (unless otherwise specified).

__all__ = ['get_lcp_array', 'get_next_stop_char', 'get_all_substring_indices_from_lcp', 'get_substring_indices']

# Cell

import numba
import numpy as np
from pydivsufsort import divsufsort, kasai

def get_lcp_array(cat_prot):
    suffix_array = divsufsort(cat_prot)
    lcp_array = kasai(cat_prot, suffix_array)
    return lcp_array[np.argsort(suffix_array)]

@numba.njit
def get_next_stop_char(seq, stop_char='$'):
    next_stop_indices = np.zeros(len(seq), dtype=np.uint32)
    curr_next_stop = len(seq)-1
    for i in range(len(seq)-1, -1, -1):
        if seq[i]==stop_char:
            curr_next_stop = i
        else:
            next_stop_indices[i] = curr_next_stop
    return next_stop_indices

@numba.njit
def get_all_substring_indices_from_lcp(cat_prot, lcp_array, min_len, max_len, stop_char='$'):
    pos_starts = []
    pos_ends = []
    next_stops = get_next_stop_char(cat_prot, stop_char)
    for i in range(len(cat_prot)):
        if cat_prot[i] == stop_char: continue
        for seq_len in range(
            max(lcp_array[i]+1,min_len),
            min(len(cat_prot)-i,max_len+1)
        ):
            end_pos = i+seq_len
            if end_pos>next_stops[i]: break
            pos_starts.append(i)
            pos_ends.append(end_pos)
    return np.array(pos_starts,dtype=np.uint32), np.array(pos_ends,dtype=np.uint32)

def get_substring_indices(cat_prot, min_len=7, max_len=25, stop_char='$'):
    lcp_array = get_lcp_array(cat_prot)
    return get_all_substring_indices_from_lcp(cat_prot, lcp_array, min_len, max_len, stop_char=stop_char)

#compile
_ = "$ABCABCD$ABCDE$ABCE$BCDEF$"
get_substring_indices(_, 2, 100)