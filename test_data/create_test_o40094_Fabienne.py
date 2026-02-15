#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl", "pyarrow"]
# ///
"""Generate a small, committable test dataset from o40094_Fabienne.

Reads the full dataset and produces a filtered subset at o40094_Fabienne_small/
with ~300 phosphosites and ~200 proteins across 2 contrasts.

Usage:
    cd test_data
    uv run create_test_o40094_Fabienne.py
"""

from pathlib import Path

from subset_utils import run_subset

BASE = Path(__file__).parent

CONFIG = {
    "seed": 42,
    "src_dir": BASE / "o40094_Fabienne",
    "out_dir": BASE.parent / "tests" / "data" / "BGS_Spectronaut_DIA_example",
    "phospho_dea": "DEA_20260109_WUphospho_ERK_vsn",
    "protein_dea": "DEA_20260109_WUprot_ERK_vsn",
    "phospho_res": "Results_WU_phospho_ERK",
    "protein_res": "Results_WU_prot_ERK",
    "phospho_inp": "Inputs_WU_phospho_ERK",
    "protein_inp": "Inputs_WU_prot_ERK",
    "phospho_xlsx": "DE_WUphospho_ERK.xlsx",
    "protein_xlsx": "DE_WUprot_ERK.xlsx",
    "phospho_annot": "phospho_annot_ERK_RUX.tsv",
    "protein_annot": "prot_annot_ERK_RUX.tsv",
    "keep_contrasts": ["no_ERK_vs_ERK", "no_ERK_vs_ERK_at_NoRux"],
    "n_phospho": 500,
}

if __name__ == "__main__":
    run_subset(CONFIG)
