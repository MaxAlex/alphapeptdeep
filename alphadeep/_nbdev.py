# AUTOGENERATED BY NBDEV! DO NOT EDIT!

__all__ = ["index", "modules", "custom_doc_links", "git_url"]

index = {"centroid_mass_match": "match.ipynb",
         "Match": "match.ipynb",
         "MSReaderBase": "ms_reader.ipynb",
         "AlphaPept_HDF_MS1_Reader": "ms_reader.ipynb",
         "AlphaPept_HDF_MS2_Reader": "ms_reader.ipynb",
         "read_until": "ms_reader.ipynb",
         "find_line": "ms_reader.ipynb",
         "parse_pfind_scan_from_TITLE": "ms_reader.ipynb",
         "is_pfind_mgf": "ms_reader.ipynb",
         "MGFReader": "ms_reader.ipynb",
         "MSReaderProvider": "ms_reader.ipynb",
         "ms2_reader_provider": "ms_reader.ipynb",
         "ms1_reader_provider": "ms_reader.ipynb",
         "charge_factor": "msms.ipynb",
         "EncDecModelCCS": "CCS.ipynb",
         "AlphaCCSModel": "CCS.ipynb",
         "mod_feature_size": "msms.ipynb",
         "EncDecModelRT": "RT.ipynb",
         "AlphaRTModel": "RT.ipynb",
         "evaluate_linear_regression": "RT.ipynb",
         "evaluate_linear_regression_plot": "RT.ipynb",
         "ModelImplBase": "base.ipynb",
         "max_instrument_num": "msms.ipynb",
         "frag_types": "msms.ipynb",
         "max_frag_charge": "msms.ipynb",
         "num_ion_types": "msms.ipynb",
         "aa_embedding_size": "building_block.ipynb",
         "SeqCNN": "building_block.ipynb",
         "aa_embedding": "building_block.ipynb",
         "aa_one_hot": "building_block.ipynb",
         "zero_param": "building_block.ipynb",
         "xavier_param": "building_block.ipynb",
         "SeqLSTM": "building_block.ipynb",
         "init_state": "building_block.ipynb",
         "SeqGRU": "building_block.ipynb",
         "SeqTransformer": "building_block.ipynb",
         "SeqAttentionSum": "building_block.ipynb",
         "InputMetaNet": "building_block.ipynb",
         "InputModNet": "building_block.ipynb",
         "InputModNetFixFirstK": "building_block.ipynb",
         "InputAALSTM": "building_block.ipynb",
         "InputAALSTM_cat_Meta": "building_block.ipynb",
         "InputAALSTM_cat_Charge": "building_block.ipynb",
         "InputAAEmbedding": "building_block.ipynb",
         "Input_AA_CNN_LSTM_Encoder": "building_block.ipynb",
         "Input_AA_CNN_Encoder": "building_block.ipynb",
         "Input_AA_CNN_LSTM_cat_Charge_Encoder": "building_block.ipynb",
         "Input_AA_LSTM_Encoder": "building_block.ipynb",
         "SeqLSTMDecoder": "building_block.ipynb",
         "SeqGRUDecoder": "building_block.ipynb",
         "OutputLSTM_cat_Meta": "building_block.ipynb",
         "OutputLinear_cat_Meta": "building_block.ipynb",
         "LinearDecoder": "building_block.ipynb",
         "HiddenTransformer": "building_block.ipynb",
         "mod_elements": "featurize.ipynb",
         "mod_elem_to_idx": "featurize.ipynb",
         "MOD_TO_FEATURE": "featurize.ipynb",
         "parse_mod_feature": "featurize.ipynb",
         "get_batch_mod_feature": "featurize.ipynb",
         "parse_aa_indices": "featurize.ipynb",
         "instrument_dict": "featurize.ipynb",
         "unknown_inst_index": "featurize.ipynb",
         "parse_instrument_indices": "featurize.ipynb",
         "ModelMSMSpDeepTestResNet": "msms.ipynb",
         "ModelMSMSpDeep": "msms.ipynb",
         "IntenAwareLoss": "msms.ipynb",
         "pDeepModel": "msms.ipynb",
         "nce_factor": "msms.ipynb",
         "pDeepParamSearch": "msms.ipynb",
         "product_dict": "msms.ipynb",
         "get_param_iter": "msms.ipynb",
         "pearson": "msms.ipynb",
         "spectral_angle": "msms.ipynb",
         "spearman": "msms.ipynb",
         "evaluate_msms": "msms.ipynb",
         "add_cutoff_metric": "msms.ipynb",
         "parse_ap": "alphapept_reader.ipynb",
         "AlphaPeptReader": "alphapept_reader.ipynb",
         "parse_mq": "maxquant_reader.ipynb",
         "MaxQuantReader": "maxquant_reader.ipynb",
         "MaxQuantMSMSReader": "maxquant_reader.ipynb",
         "convert_one_pFind_mod": "pfind_reader.ipynb",
         "translate_pFind_mod": "pfind_reader.ipynb",
         "get_pFind_mods": "pfind_reader.ipynb",
         "remove_pFind_decoy_protein": "pfind_reader.ipynb",
         "pFindReader": "pfind_reader.ipynb",
         "PSMLabelReader": "pfind_reader.ipynb",
         "load_psmlabel_list": "pfind_reader.ipynb",
         "translate_other_modification": "psm_reader.ipynb",
         "keep_modifications": "psm_reader.ipynb",
         "PSMReaderBase": "psm_reader.ipynb",
         "PSMReader_w_FragBase": "psm_reader.ipynb",
         "PSMReaderProvider": "psm_reader.ipynb",
         "psm_reader_provider": "psm_reader.ipynb",
         "PSMwFragReaderProvider": "psm_reader.ipynb",
         "psm_w_frag_reader_provider": "psm_reader.ipynb",
         "SpectronautReader": "spectronaut_reader.ipynb",
         "PredictLib": "predict_lib.ipynb",
         "merge_precursor_fragment_df": "translate.ipynb",
         "speclib_to_single_df": "translate.ipynb",
         "alpha_to_other_mod_dict": "translate.ipynb"}

modules = ["mass_spec/match.py",
           "mass_spec/ms_reader.py",
           "model/CCS.py",
           "model/RT.py",
           "model/base.py",
           "model/building_block.py",
           "model/featurize.py",
           "model/msms.py",
           "reader/alphapept_reader.py",
           "reader/maxquant_reader.py",
           "reader/pfind_reader.py",
           "reader/psm_reader.py",
           "reader/spectronaut_reader.py",
           "speclib/predict_lib.py",
           "speclib/translate.py"]

doc_url = "https://MannLabs.github.io/alphadeep/"

git_url = "https://github.com/MannLabs/alphadeep/tree/main/"

def custom_doc_links(name): return None
