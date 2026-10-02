"""Run kinase-library calculations: the motif scan as a gzipped JSON handoff,
the motif enrichment as the protsea document prophosqua reads."""

import gzip
import importlib.metadata
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import cyclopts
import numpy as np
import pandas as pd

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


def _artifact_stream(path: Path, mode: str):
    """Open a stage artifact, gzipped when its name says so."""
    if path.name.endswith(".gz"):
        return gzip.open(path, mode)
    return path.open(mode)


def _read_stage(path: Path, expected: str) -> dict[str, Any]:
    with _artifact_stream(path, "rt") as handle:
        artifact = json.load(handle)
    if artifact["format"] != "prophosqua_stage" or artifact["version"] != "1.0.0":
        raise ValueError(f"Unsupported PTM stage file: {path}")
    if artifact["stage"] != expected:
        raise ValueError(f"Expected {expected}, found {artifact['stage']}")
    return artifact


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_plain(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    # The packed values carry their own missing masks; JSON has no NaN.
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_stage(source: dict[str, Any], output: Path, stage: str, result: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".gz" if output.name.endswith(".gz") else ""
    descriptor, temporary = tempfile.mkstemp(prefix=".ptm-stage-", suffix=suffix, dir=output.parent)
    os.close(descriptor)
    path = Path(temporary)
    try:
        artifact = {
            "format": "prophosqua_stage",
            "version": "1.0.0",
            "stage": stage,
            "analysis": source["analysis"],
            "statistics_sha256": source["statistics_sha256"],
            "result": _plain(mudata_values.pack(result)),
        }
        with _artifact_stream(path, "wt") as handle:
            json.dump(artifact, handle, allow_nan=False, separators=(",", ":"))
        restored = _read_stage(path, stage)
        recovered = mudata_values.unpack(restored["result"])
        for name, value in result.items():
            if isinstance(value, pd.DataFrame):
                pd.testing.assert_frame_equal(
                    recovered[name].reset_index(drop=True),
                    value.reset_index(drop=True),
                    check_dtype=False,
                )
            elif recovered[name] != value:
                raise ValueError(f"Stage file round-trip changed {name}")
        os.replace(path, output)
    finally:
        path.unlink(missing_ok=True)


@app.command
def scan(input_file: Path, output: Path) -> None:
    """Build kinase assignments from a KinaseInputs stage file."""
    from kinase_library.objects import phosphoproteomics

    source = _read_stage(input_file, "KinaseInputs")
    data = mudata_values.unpack(source["result"])["seqwindows"]
    settings = source["settings"]
    experiment = phosphoproteomics.PhosphoProteomics(
        data=data[["SequenceWindow"]].drop_duplicates().reset_index(drop=True),
        seq_col="SequenceWindow",
        pp=True,
    )
    experiment.percentile(kin_type=settings["kin_type"], return_values=False)
    percentiles = getattr(experiment, f"{settings['kin_type']}_percentiles")
    stacked = percentiles.stack()
    matches = stacked[stacked >= settings["threshold"]].reset_index()
    matches.columns = ["Sequence", "Kinase", "Value"]
    # kinase-library scores its own spelling of a window, the phosphorylated
    # residue in lower case; the assignments name the window they were given.
    submitted = experiment.data.set_index("Sequence")["SequenceWindow"]
    assignments = pd.DataFrame(
        {"term": matches["Kinase"].to_numpy(), "gene": matches["Sequence"].map(submitted).to_numpy()}
    )
    _write_stage(source, output, "KinaseAssignments", {"term2gene": assignments})


@app.command
def enrich(input_file: Path, assignments: Path, output: Path, *, threads: int = 4) -> None:
    """Write the motif enrichment of one analysis as a gzipped protsea document."""
    from kinase_library.enrichment import mea

    source = _read_stage(input_file, "KinaseInputs")
    assigned = _read_stage(assignments, "KinaseAssignments")
    if (source["analysis"], source["statistics_sha256"]) != (
        assigned["analysis"], assigned["statistics_sha256"]
    ):
        raise ValueError("Kinase preparations come from different statistics")
    ranks = mudata_values.unpack(source["result"])["ranks"]
    settings = source["settings"]
    gsea_document: dict[str, dict[str, Any]] = {"data": {}, "rank_lists": {}}
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
        serialized = fitted.to_gsea_result_data(contrast)
        gsea_document["data"].update(serialized["data"])
        gsea_document["rank_lists"].update(serialized["rank_lists"])
    _write_gsea_document(output, gsea_document)


def _write_gsea_document(output: Path, document: dict[str, Any]) -> None:
    """Write a GSEA result document gzipped, as protsea::read_gsea_json() reads it."""
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".ptm-gsea-", suffix=".json.gz", dir=output.parent)
    os.close(descriptor)
    path = Path(temporary)
    try:
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(document, handle, allow_nan=False, separators=(",", ":"))
        os.replace(path, output)
    finally:
        path.unlink(missing_ok=True)


def main() -> None:
    """Run the kinase MuData command line."""
    app()


if __name__ == "__main__":
    main()
