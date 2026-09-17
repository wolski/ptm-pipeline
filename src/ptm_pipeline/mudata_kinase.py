"""Run the existing kinase-library calculations using only MuData handoffs."""

import importlib.metadata
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import cyclopts
import h5py
import mudata
import pandas as pd
from anndata.io import write_elem

from ptm_pipeline import mudata_values

app = cyclopts.App(help=__doc__)


@app.command
def dependencies() -> None:
    """Print installed source paths used as Snakemake dependencies."""
    print(Path(__file__).resolve())
    print(Path(mudata_values.__file__).resolve())
    distribution = importlib.metadata.distribution("kinase-library")
    for file in distribution.files:
        if str(file).endswith((".py", "METADATA")):
            print(distribution.locate_file(file).resolve())


def _read_stage(path: Path, expected: str) -> tuple[Any, str, dict[str, Any]]:
    container = mudata.read_h5mu(path)
    metadata = container.uns["prophosqua"]
    if metadata["stage"] != expected:
        raise ValueError(f"Expected {expected}, found {metadata['stage']}")
    return container, metadata["analysis"], mudata_values.unpack(metadata["parameters"])


def _result(container: Any, stage: str, analysis: str) -> dict[str, Any]:
    modality = {"DPA": "enriched", "DPU": "cf", "CF": "cf"}[analysis]
    encoded = container.mod[modality].uns["prophosqua"]["completed_stages"][
        f"{stage}__{analysis}"
    ]
    return mudata_values.unpack(encoded)


def _write_stage(
    source: Path, output: Path, stage: str, analysis: str, result: dict[str, Any]
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".h5mu-", suffix=".h5mu", dir=output.parent
    )
    os.close(descriptor)
    path = Path(temporary)
    try:
        # Preserve every source dataset and annotation byte-for-byte. The only
        # changed fields are stage identity and the newly completed result.
        shutil.copyfile(source, path)
        modality = {"DPA": "enriched", "DPU": "cf", "CF": "cf"}[analysis]
        with h5py.File(path, "r+") as handle:
            write_elem(handle["uns/prophosqua"], "stage", stage)
            group = handle[f"mod/{modality}/uns/prophosqua/completed_stages"]
            write_elem(group, f"{stage}__{analysis}", mudata_values.pack(result))
        restored = mudata.read_h5mu(path)
        if restored.uns["prophosqua"]["stage"] != stage:
            raise ValueError("MuData stage round-trip changed the completed type")
        recovered = _result(restored, stage, analysis)
        for name, frame in result.items():
            pd.testing.assert_frame_equal(
                recovered[name].reset_index(drop=True),
                frame.reset_index(drop=True),
                check_dtype=False,
            )
        os.replace(path, output)
    finally:
        path.unlink(missing_ok=True)


@app.command
def scan(input_file: Path, output: Path) -> None:
    """Build complete kinase assignments from a KinaseInputs MuData stage."""
    from kinase_library.objects import phosphoproteomics

    container, analysis, parameters = _read_stage(input_file, "KinaseInputs")
    data = _result(container, "KinaseInputs", analysis)["seqwindows"]
    settings = parameters["kinaselib"]
    experiment = phosphoproteomics.PhosphoProteomics(
        data=data[["SequenceWindow"]].drop_duplicates().reset_index(drop=True),
        seq_col="SequenceWindow",
        pp=True,
    )
    experiment.percentile(kin_type=settings["kin_type"], return_values=False)
    percentiles = getattr(experiment, f"{settings['kin_type']}_percentiles")
    stacked = percentiles.stack()
    matches = stacked[stacked >= settings["threshold"]].reset_index()
    matches.columns = ["SequenceWindow", "Kinase", "Value"]
    assignments = matches[["Kinase", "SequenceWindow"]].copy()
    assignments.columns = ["term", "gene"]
    _write_stage(
        input_file, output, "KinaseAssignments", analysis, {"term2gene": assignments}
    )


@app.command
def enrich(input_file: Path, output: Path, *, threads: int = 4) -> None:
    """Build complete motif enrichment from a KinaseAssignments MuData stage."""
    from kinase_library.enrichment import mea

    container, analysis, parameters = _read_stage(input_file, "KinaseAssignments")
    ranks = _result(container, "KinaseInputs", analysis)["ranks"]
    settings = parameters["kinaselib"]
    results = []
    for contrast, data in ranks.items():
        ranked = mea.RankedPhosData(
            dp_data=data, rank_col="statistic.site", seq_col="SequenceWindow", pp=True
        )
        fitted = ranked.mea(
            kin_type=settings["kin_type"],
            kl_method="percentile",
            kl_thresh=settings["threshold"],
            permutation_num=int(settings["permutations"]),
            threads=threads,
        )
        result = fitted.enrichment_results.reset_index()
        result.insert(0, "contrast", contrast)
        results.append(result)
    _write_stage(
        input_file,
        output,
        "MotifEnrichment",
        analysis,
        {"mea_results": pd.concat(results, ignore_index=True)},
    )


def main() -> None:
    """Run the kinase MuData command line."""
    app()


if __name__ == "__main__":
    main()
