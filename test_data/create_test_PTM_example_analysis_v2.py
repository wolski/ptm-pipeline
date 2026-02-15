#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl", "pyarrow"]
# ///
"""Generate a small, committable test dataset from PTM_example_analysis_v2.

Reads the full dataset and produces a filtered subset at PTM_example_FP_TMT/
with ~300 phosphosites and ~200 proteins across 2 contrasts.

Usage:
    cd test_data
    uv run create_test_PTM_example_analysis_v2.py
"""

from pathlib import Path

from subset_utils import run_subset

BASE = Path(__file__).parent

CONFIG = {
    "seed": 42,
    "src_dir": BASE / "PTM_example_analysis_v2",
    "out_dir": BASE.parent / "tests" / "data" / "FP_TMT_example",
    "phospho_dea": "DEA_20260209_WUphospho_STY_vsn",
    "protein_dea": "DEA_20260209_WUtotal_proteome_vsn",
    "phospho_res": "Results_WU_phospho_STY",
    "protein_res": "Results_WU_total_proteome",
    "phospho_inp": "Inputs_WU_phospho_STY",
    "protein_inp": "Inputs_WU_total_proteome",
    "phospho_xlsx": "DE_WUphospho_STY.xlsx",
    "protein_xlsx": "DE_WUtotal_proteome.xlsx",
    "phospho_annot": "dataset_with_contrasts.tsv",
    "protein_annot": "dataset_with_contrasts.tsv",
    "keep_contrasts": ["KO_vs_WT", "KO_vs_WT_at_Early"],
    "n_phospho": 500,
}

if __name__ == "__main__":
    run_subset(CONFIG)
