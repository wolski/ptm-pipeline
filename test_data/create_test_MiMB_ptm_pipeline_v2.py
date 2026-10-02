#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["anndata"]
# ///
"""Generate a small, committable test dataset from MiMB_ptm_pipeline_v2.

The Maculins TMT phosphoproteome (Zenodo 15879865), as MiMB_ptm_pipeline_v2's
run_dea.fish analyses it: phospho sites, total proteins and total peptides, in
two plexes. Its DEAs are used as they are; test_data/MiMB_ptm_pipeline_v2 links
to that project. Produces a subset at tests/data/FP_TMT_example/.

Usage:
    cd test_data
    uv run create_test_MiMB_ptm_pipeline_v2.py
"""

from pathlib import Path

from subset_utils import run_subset

BASE = Path(__file__).parent

CONFIG = {
    "seed": 42,
    "src_dir": BASE / "MiMB_ptm_pipeline_v2",
    "out_dir": BASE.parent / "tests" / "data" / "FP_TMT_example",
    "phospho_dea": "DEA_20260929_WUphospho_STY_vsn",
    "protein_dea": "DEA_20260929_WUtotal_proteome_vsn",
    "peptide_dea": "DEA_20260929_WUtotal_peptide_vsn",
    "phospho_annot": "dataset_with_contrasts.tsv",
    "protein_annot": "dataset_with_contrasts.tsv",
    "peptide_annot": "dataset_with_contrasts.tsv",
    "peptides_per_protein": 2,
    "n_phospho": 1500,
}

if __name__ == "__main__":
    run_subset(CONFIG)
