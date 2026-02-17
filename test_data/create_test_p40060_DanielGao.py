#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl", "pyarrow"]
# ///
"""Generate a small, committable test dataset from p40060_DanielGao.

Reads the full dataset and produces a filtered subset at p40060_DanielGao_small/
with ~300 phosphosites and ~200 proteins (single contrast 42C_vs_37C).

Usage:
    cd test_data
    uv run create_test_p40060_DanielGao.py
"""

from pathlib import Path

from subset_utils import run_subset

BASE = Path(__file__).parent

CONFIG = {
    "seed": 42,
    "src_dir": BASE / "p40060_DanielGao",
    "out_dir": BASE.parent / "tests" / "data" / "FP_LFQ_example",
    "phospho_dea": "DEA_20260113_WUcombined_STY_batch_vsn",
    "protein_dea": "DEA_20260113_WUtotal_proteome_batch_vsn",
    "phospho_res": "Results_WU_combined_STY_batch",
    "protein_res": "Results_WU_total_proteome_batch",
    "phospho_inp": "Inputs_WU_combined_STY_batch",
    "protein_inp": "Inputs_WU_total_proteome_batch",
    "phospho_xlsx": "DE_WUcombined_STY_batch.xlsx",
    "protein_xlsx": "DE_WUtotal_proteome_batch.xlsx",
    "phospho_annot": "combined_sty_dataset_with_batch.tsv",
    "protein_annot": "dataset_with_batch.tsv",
    "keep_contrasts": ["42C_vs_37C"],
    "n_phospho": 1500,
}

if __name__ == "__main__":
    run_subset(CONFIG)
