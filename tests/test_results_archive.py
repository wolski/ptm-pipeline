import importlib.util
from pathlib import Path
from zipfile import ZipFile


def test_results_archive_contains_only_declared_final_outputs(tmp_path):
    template = Path(__file__).resolve().parents[1] / "template" / "helpers.py"
    spec = importlib.util.spec_from_file_location("pipeline_helpers", template)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    folder = tmp_path / "PTM_output"
    for relative in (
        "PTM_results.h5mu",
        "PTM_inputs.h5mu",
        "PTM_statistics.h5mu",
        "PTM_DPA/result_ptm_sea.cbor",
        "PTM_DPA/Analysis_DPA_DPU.html",
        "ptm_statistics.html",
        "PTM_DPA/ptm_enrichment.html",
        "PTM_DPU/ptm_enrichment.html",
        "PTM_CF_DPU/ptm_enrichment.html",
        "PTM_results.xlsx",
    ):
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative)
    reports = [str(folder / "ptm_statistics.html")] + [
        str(folder / analysis / "ptm_enrichment.html")
        for analysis in ("PTM_DPA", "PTM_DPU", "PTM_CF_DPU")
    ]
    index = folder / "index.html"
    module.create_report_index(str(index), reports)
    archive_path = tmp_path / "results.zip"
    module.create_results_archive(
        str(folder), str(archive_path),
        [str(folder / "PTM_results.h5mu"), str(folder / "PTM_results.xlsx"), str(index)] + reports,
    )

    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {
            "PTM_output/PTM_results.h5mu",
            "PTM_output/PTM_results.xlsx",
            "PTM_output/index.html",
            "PTM_output/ptm_statistics.html",
            "PTM_output/PTM_DPA/ptm_enrichment.html",
            "PTM_output/PTM_DPU/ptm_enrichment.html",
            "PTM_output/PTM_CF_DPU/ptm_enrichment.html",
        }
        assert b"ptm_statistics.html" in archive.read("PTM_output/index.html")
        for analysis in (b"PTM_DPA", b"PTM_DPU", b"PTM_CF_DPU"):
            assert analysis + b"/ptm_enrichment.html" in archive.read("PTM_output/index.html")
