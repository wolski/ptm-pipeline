#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["anndata"]
# ///
"""Generate a small, committable test dataset from p40060_DanielGao.

Reads the DEAs rerun_deas.sh writes into rerun/ and produces a filtered subset at p40060_DanielGao_small/
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
    "src_dir": BASE / "p40060_DanielGao" / "rerun",
    "out_dir": BASE.parent / "tests" / "data" / "FP_LFQ_example",
    "phospho_dea": "DEA_20261002_WUcombined_STY_batch_vsn",
    "protein_dea": "DEA_20261002_WUtotal_proteome_batch_vsn",
    "phospho_annot": "combined_STY_batch_combined_sty_dataset_with_batch.tsv",
    "protein_annot": "total_proteome_batch_dataset_with_batch.tsv",
    "n_phospho": 1500,
}

if __name__ == "__main__":
    run_subset(CONFIG)
