"""Discovery uses producer metadata and preserves unresolved input paths."""

import tempfile
import unittest
from pathlib import Path

import h5py

from ptm_pipeline.config import generate_config
from ptm_pipeline.discover import find_dea_anndata, read_dea_contrasts


class DiscoverAnnDataTest(unittest.TestCase):
    def test_stored_contrasts_and_deterministic_artifact_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(find_dea_anndata(root))
            for name in ("Results_WU_b", "Results_WU_a"):
                output = root / name / "AnnData.h5ad"
                output.parent.mkdir()
                with h5py.File(output, "w") as handle:
                    group = handle.create_group("uns/prolfquapp")
                    group["schema_version"] = "2.0.0"
                    group["contrasts/contrast_name"] = [
                        "treatment_vs_control",
                        "second_vs_control",
                    ]
            selected = find_dea_anndata(root)
            self.assertEqual(selected.parent.name, "Results_WU_a")
            self.assertEqual(
                read_dea_contrasts(selected),
                ["treatment_vs_control", "second_vs_control"],
            )
            with h5py.File(selected, "r+") as handle:
                handle["uns/prolfquapp/schema_version"][()] = "1.0.0"
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                read_dea_contrasts(selected)

    def test_config_keeps_missing_inputs_editable(self):
        root = Path("/project")
        config = generate_config(
            root / "phospho", root / "protein", None, None, [], project_dir=root
        )
        self.assertEqual(config["enriched_h5ad"], "")
        self.assertEqual(config["total_h5ad"], "")
        self.assertNotIn("annot_file", config)
        self.assertEqual(config["gsea"]["max_size"], 500)
        self.assertEqual(config["kinaselib"]["gsea_max_size"], 5000)


if __name__ == "__main__":
    unittest.main()
