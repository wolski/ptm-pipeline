import importlib.util
from pathlib import Path
from zipfile import ZipFile


def test_results_archive_contains_only_final_h5mu(tmp_path):
    template = Path(__file__).resolve().parents[1] / "template" / "helpers.py"
    spec = importlib.util.spec_from_file_location("pipeline_helpers", template)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    folder = tmp_path / "PTM_output"
    (folder / "PTM_DPA" / "logs").mkdir(parents=True)
    (folder / "PTM_DPA" / "report.html.render").mkdir()
    for relative in (
        "PTM_results.h5mu",
        "PTM_inputs.h5mu",
        "PTM_statistics.h5mu",
        "PTM_DPA/PTMSEA.h5mu",
        "PTM_DPA/PTMSEA.cbor",
        "PTM_DPA/report.html",
        "PTM_DPA/logs/report.log",
        "PTM_DPA/report.html.render/plot.png",
    ):
        path = folder / relative
        path.write_text(relative)
    archive_path = tmp_path / "results.zip"

    module.create_results_archive(str(folder), str(archive_path))

    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {
            "PTM_output/PTM_results.h5mu",
            "PTM_output/PTM_DPA/report.html",
        }
