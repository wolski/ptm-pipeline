#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["anndata"]
# ///
"""Generate a small, committable test dataset from o40094_Fabienne.

Reads the DEAs rerun_deas.sh writes into rerun/ and produces a filtered subset at o40094_Fabienne_small/
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
    "src_dir": BASE / "o40094_Fabienne" / "rerun",
    "out_dir": BASE.parent / "tests" / "data" / "BGS_Spectronaut_DIA_example",
    "phospho_dea": "DEA_20261002_WUphospho_ERK_vsn",
    "protein_dea": "DEA_20261002_WUprot_ERK_vsn",
    "phospho_annot": "phospho_ERK_phospho_annot_ERK_RUX.tsv",
    "protein_annot": "prot_ERK_prot_annot_ERK_RUX.tsv",
    "n_phospho": 1500,
}

if __name__ == "__main__":
    run_subset(CONFIG)
