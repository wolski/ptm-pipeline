"""Compare MuData kinase inputs and outputs with an existing pipeline delivery.

Run with: python compare_kinase_mudata.py BASELINE NEW_STAGE_DIRECTORY
The migrated stage directory uses KinaseInputs_DPA.h5mu, etc.
"""

import sys
from pathlib import Path

import h5py
import pandas as pd
from anndata.io import read_elem

from ptm_pipeline.mudata_values import unpack


def read_result(root: Path, stage: str, analysis: str):
    modality = "enriched" if analysis == "DPA" else "cf"
    with h5py.File(root / f"{stage}_{analysis}.h5mu") as handle:
        return unpack(
            read_elem(
                handle[
                    f"mod/{modality}/uns/prophosqua/completed_stages/{stage}__{analysis}"
                ]
            )
        )


def compare(expected, actual):
    pd.testing.assert_frame_equal(
        expected.reset_index(drop=True),
        actual.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-8,
        atol=1e-12,
    )


def main():
    baseline, stages = map(Path, sys.argv[1:])
    for analysis, directory in (
        ("DPA", "PTM_DPA"),
        ("DPU", "PTM_DPU"),
        ("CF", "PTM_CF_DPU"),
    ):
        source = baseline / directory / "KinaseLib"
        inputs = read_result(stages, "KinaseInputs", analysis)
        compare(
            pd.read_csv(source / f"{analysis}_seqwindows.tsv", sep="\t"),
            inputs["seqwindows"],
        )
        for contrast, ranks in inputs["ranks"].items():
            compare(
                pd.read_csv(source / f"{analysis}_MEA_{contrast}.rnk", sep="\t"), ranks
            )
        assignments = read_result(stages, "KinaseAssignments", analysis)["term2gene"]
        compare(pd.read_csv(source / "term2gene.csv"), assignments)
        results = read_result(stages, "MotifEnrichment", analysis)["mea_results"]
        for contrast, frame in results.groupby("contrast", sort=False):
            compare(
                pd.read_csv(source / f"mea_{contrast}.csv"),
                frame.drop(columns="contrast"),
            )
        print(
            f"{analysis}: exact row/column order, ranks, assignments and MEA values verified"
        )


if __name__ == "__main__":
    main()
