"""Run kinase-library calculations with compact CBOR handoffs."""

import gzip
import importlib.metadata
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import cbor2
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
    """Open a stage artifact, gzipped when its name says so.

    prophosqua writes and reads these compressed: the payloads are text-like and
    reach hundreds of megabytes per analysis.
    """
    if path.name.endswith(".gz"):
        return gzip.open(path, mode)
    return path.open(mode)


def _read_stage(path: Path, expected: str) -> dict[str, Any]:
    with _artifact_stream(path, "rb") as handle:
        artifact = cbor2.load(handle)
    if artifact["format"] != "prophosqua_stage" or artifact["version"] != "1.0.0":
        raise ValueError(f"Unsupported PTM CBOR artifact: {path}")
    if artifact["stage"] != expected:
        raise ValueError(f"Expected {expected}, found {artifact['stage']}")
    return artifact


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_plain(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write_stage(source: dict[str, Any], output: Path, stage: str, result: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".gz" if output.name.endswith(".gz") else ""
    descriptor, temporary = tempfile.mkstemp(prefix=".ptm-cbor-", suffix=suffix, dir=output.parent)
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
        with _artifact_stream(path, "wb") as handle:
            cbor2.dump(artifact, handle)
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
                raise ValueError(f"CBOR stage round-trip changed {name}")
        os.replace(path, output)
    finally:
        path.unlink(missing_ok=True)


@app.command
def scan(input_file: Path, output: Path) -> None:
    """Build kinase assignments from a KinaseInputs CBOR artifact."""
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
    matches.columns = ["SequenceWindow", "Kinase", "Value"]
    assignments = matches[["Kinase", "SequenceWindow"]].copy()
    assignments.columns = ["term", "gene"]
    _write_stage(source, output, "KinaseAssignments", {"term2gene": assignments})


@app.command
def enrich(input_file: Path, assignments: Path, output: Path, *, threads: int = 4) -> None:
    """Build motif enrichment from kinase preparation CBOR artifacts."""
    from kinase_library.enrichment import mea

    source = _read_stage(input_file, "KinaseInputs")
    assigned = _read_stage(assignments, "KinaseAssignments")
    if (source["analysis"], source["statistics_sha256"]) != (
        assigned["analysis"], assigned["statistics_sha256"]
    ):
        raise ValueError("Kinase CBOR preparations come from different statistics")
    ranks = mudata_values.unpack(source["result"])["ranks"]
    settings = source["settings"]
    results = []
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
        result = fitted.enrichment_results.reset_index()
        result.insert(0, "contrast", contrast)
        results.append(result)
        serialized = fitted.to_gsea_result_data(contrast)
        gsea_document["data"].update(serialized["data"])
        gsea_document["rank_lists"].update(serialized["rank_lists"])
    _write_stage(
        source,
        output,
        "MotifEnrichment",
        {
            "mea_results": pd.concat(results, ignore_index=True),
            "gsea_json": json.dumps(
                gsea_document,
                allow_nan=False,
                separators=(",", ":"),
            ),
        },
    )


def main() -> None:
    """Run the kinase MuData command line."""
    app()


if __name__ == "__main__":
    main()
