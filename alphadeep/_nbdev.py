# AUTOGENERATED BY NBDEV! DO NOT EDIT!

__all__ = ["index", "modules", "custom_doc_links", "git_url"]

index = {"match_centroid_mz": "match.ipynb",
         "PepSpecMatch": "match.ipynb",
         "MSReaderBase": "ms_reader.ipynb",
         "AlphaPept_HDF_MS1_Reader": "ms_reader.ipynb",
         "AlphaPept_HDF_MS2_Reader": "ms_reader.ipynb",
         "read_until": "ms_reader.ipynb",
         "find_line": "ms_reader.ipynb",
         "parse_pfind_scan_from_TITLE": "ms_reader.ipynb",
         "is_pfind_mgf": "ms_reader.ipynb",
         "index_ragged_list": "ms_reader.ipynb",
         "MGFReader": "ms_reader.ipynb",
         "MSReaderProvider": "ms_reader.ipynb",
         "ms2_reader_provider": "ms_reader.ipynb",
         "ms1_reader_provider": "ms_reader.ipynb",
         "ModelImplBase": "base.ipynb",
         "mod_feature_size": "rt.ipynb",
         "max_instrument_num": "ms2.ipynb",
         "frag_types": "ms2.ipynb",
         "max_frag_charge": "ms2.ipynb",
         "num_ion_types": "ms2.ipynb",
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
         "charge_factor": "ms2.ipynb",
         "EncDecModelCCS": "ccs.ipynb",
         "get_reduced_mass": "ccs.ipynb",
         "ccs_to_mobility_bruker": "ccs.ipynb",
         "mobility_to_ccs_bruker": "ccs.ipynb",
         "ccs_to_mobility_pred_df": "ccs.ipynb",
         "mobility_to_ccs_df": "ccs.ipynb",
         "AlphaCCSModel": "ccs.ipynb",
         "mod_elements": "featurize.ipynb",
         "mod_elem_to_idx": "featurize.ipynb",
         "MOD_TO_FEATURE": "featurize.ipynb",
         "parse_mod_feature": "featurize.ipynb",
         "get_batch_mod_feature": "featurize.ipynb",
         "parse_aa_indices": "featurize.ipynb",
         "instrument_dict": "featurize.ipynb",
         "unknown_inst_index": "featurize.ipynb",
         "parse_instrument_indices": "featurize.ipynb",
         "ModelMSMSpDeep": "ms2.ipynb",
         "IntenAwareLoss": "ms2.ipynb",
         "pDeepModel": "ms2.ipynb",
         "nce_factor": "ms2.ipynb",
         "pDeepParamSearch": "ms2.ipynb",
         "product_dict": "ms2.ipynb",
         "get_param_iter": "ms2.ipynb",
         "normalize_training_intensities": "ms2.ipynb",
         "pearson": "ms2.ipynb",
         "spectral_angle": "ms2.ipynb",
         "spearman": "ms2.ipynb",
         "add_cutoff_metric": "ms2.ipynb",
         "calc_ms2_similarity": "ms2.ipynb",
         "uniform_sampling": "rt.ipynb",
         "EncDecModelRT": "rt.ipynb",
         "AlphaRTModel": "rt.ipynb",
         "evaluate_linear_regression": "rt.ipynb",
         "evaluate_linear_regression_plot": "rt.ipynb",
         "convert_predicted_rt_to_irt": "rt.ipynb",
         "irt_pep": "rt.ipynb",
         "download_models": "pretrained_models.ipynb",
         "sandbox_dir": "pretrained_models.ipynb",
         "model_zip": "pretrained_models.ipynb",
         "load_phos_models": "pretrained_models.ipynb",
         "load_models": "pretrained_models.ipynb",
         "AlphaDeepModels": "pretrained_models.ipynb",
         "protease_dict": "fasta.ipynb",
         "read_fasta_file": "fasta.ipynb",
         "load_all_proteins": "fasta.ipynb",
         "read_fasta_file_entries": "fasta.ipynb",
         "concat_proteins": "fasta.ipynb",
         "cleave_sequence_with_cut_pos": "fasta.ipynb",
         "Digest": "fasta.ipynb",
         "get_fix_mods": "fasta.ipynb",
         "get_candidate_sites": "fasta.ipynb",
         "get_var_mod_sites": "fasta.ipynb",
         "get_var_mods_per_sites_multi_mods_on_aa": "fasta.ipynb",
         "get_var_mods_per_sites_single_mod_on_aa": "fasta.ipynb",
         "get_var_mods": "fasta.ipynb",
         "get_var_mods_per_sites": "fasta.ipynb",
         "get_mods": "fasta.ipynb",
         "FastaSpecLib": "fasta.ipynb",
         "parse_ap": "alphapept_reader.ipynb",
         "get_x_tandem_score": "alphapept_reader.ipynb",
         "AlphaPeptReader": "alphapept_reader.ipynb",
         "SpectronautReader": "dia_search_reader.ipynb",
         "OpenSwathReader": "dia_search_reader.ipynb",
         "DiannReader": "dia_search_reader.ipynb",
         "parse_modseq": "maxquant_reader.ipynb",
         "MaxQuantReader": "maxquant_reader.ipynb",
         "MaxQuantMSMSReader": "maxquant_reader.ipynb",
         "get_MSFragger_mods": "msfragger_reader.ipynb",
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
         "ScoreFeatureExtractor": "feature_extractor.ipynb",
         "fdr_to_q_values": "percolator.ipynb",
         "calc_fdr": "percolator.ipynb",
         "score_to_q_value": "percolator.ipynb",
         "DeepLearningScore": "percolator.ipynb",
         "Percolator": "percolator.ipynb",
         "PredictLib": "predict_lib.ipynb",
         "create_modified_sequence": "translate.ipynb",
         "merge_precursor_fragment_df": "translate.ipynb",
         "speclib_to_single_df": "translate.ipynb",
         "alpha_to_other_mod_dict": "translate.ipynb"}

modules = ["mass_spec/match.py",
           "mass_spec/ms_reader.py",
           "model/base.py",
           "model/building_block.py",
           "model/ccs.py",
           "model/featurize.py",
           "model/ms2.py",
           "model/rt.py",
           "pretrained_models.py",
           "protein/fasta.py",
           "psm_reader/alphapept_reader.py",
           "psm_reader/dia_search_reader.py",
           "psm_reader/maxquant_reader.py",
           "psm_reader/msfragger_reader.py",
           "psm_reader/pfind_reader.py",
           "psm_reader/psm_reader.py",
           "rescore/feature_extractor.py",
           "rescore/percolator.py",
           "spec_lib/predict_lib.py",
           "spec_lib/translate.py"]

doc_url = "https://MannLabs.github.io/alphadeep/"

git_url = "https://github.com/MannLabs/alphadeep/tree/main/"

def custom_doc_links(name): return None
