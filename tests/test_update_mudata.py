"""Updating an existing order supplies MuData paths without resetting settings."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import yaml

from ptm_pipeline.cli import update


class UpdateMuDataTests(unittest.TestCase):
    def test_update_migrates_existing_order_and_preserves_settings(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"dir_out": "chosen_output", "fdr": 0.07,
                      "phospho_dea_dir": "site", "protein_dea_dir": "protein",
                      "proptm3d": {"max_proteins": None}}
            for name in ("site", "protein"):
                artifact = root / name / "Results_WU_example" / "AnnData.h5ad"
                artifact.parent.mkdir(parents=True)
                artifact.touch()
            path = root / "ptm_config.yaml"
            original = yaml.safe_dump(config)
            path.write_text(original)
            with patch("ptm_pipeline.init.copy_template_files", return_value=[]):
                update(root, dry_run=True)
                self.assertEqual(path.read_text(), original)
                update(root)
                migrated = yaml.safe_load(path.read_text())
                self.assertEqual({key: migrated[key] for key in config}, config)
                self.assertEqual(migrated["enriched_h5ad"], "site/Results_WU_example/AnnData.h5ad")
                self.assertEqual(migrated["total_h5ad"], "protein/Results_WU_example/AnnData.h5ad")
                # A current configuration is not rewritten on the next update.
                current = path.read_text()
                update(root)
                self.assertEqual(path.read_text(), current)

    def test_update_renames_xlsx_input_to_xlsx_output(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"dir_out": "chosen_output",
                      "phospho_dea_dir": "site", "protein_dea_dir": "protein",
                      "enriched_h5ad": "site/Results_WU_example/AnnData.h5ad",
                      "total_h5ad": "protein/Results_WU_example/AnnData.h5ad",
                      "analyses": {
                          "dpa": {"sheet": "DPA", "subdir": "PTM_DPA",
                                  "xlsx_input": "Result_DPA.xlsx",
                                  "stat_column": "statistic.site"},
                          "cf": {"sheet": "CF", "subdir": "PTM_CF_DPU",
                                 "xlsx_input": "CorrectFirst_PTM_usage_results.xlsx",
                                 "stat_column": "statistic.site"}}}
            path = root / "ptm_config.yaml"
            original = yaml.safe_dump(config)
            path.write_text(original)
            with patch("ptm_pipeline.init.copy_template_files", return_value=[]):
                update(root, dry_run=True)
                self.assertEqual(path.read_text(), original)
                update(root)
                migrated = yaml.safe_load(path.read_text())["analyses"]
                self.assertEqual(migrated["dpa"]["xlsx_output"], "Result_DPA.xlsx")
                self.assertEqual(migrated["cf"]["xlsx_output"],
                                 "CorrectFirst_PTM_usage_results.xlsx")
                for analysis in migrated.values():
                    self.assertNotIn("xlsx_input", analysis)
                    self.assertEqual(analysis["stat_column"], "statistic.site")
                # An already-renamed configuration is left untouched.
                current = path.read_text()
                update(root)
                self.assertEqual(path.read_text(), current)

    def test_update_renames_ptm3d_to_proptm3d(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"dir_out": "chosen_output",
                      "phospho_dea_dir": "site", "protein_dea_dir": "protein",
                      "enriched_h5ad": "site/Results_WU_example/AnnData.h5ad",
                      "total_h5ad": "protein/Results_WU_example/AnnData.h5ad",
                      "ptm3d": {"run": True, "repo": "git+https://github.com/prolfqua/ptm3d",
                                "max_proteins": 20}}
            path = root / "ptm_config.yaml"
            original = yaml.safe_dump(config)
            path.write_text(original)
            with patch("ptm_pipeline.init.copy_template_files", return_value=[]):
                update(root, dry_run=True)
                self.assertEqual(path.read_text(), original)
                update(root)
                migrated = yaml.safe_load(path.read_text())
                self.assertNotIn("ptm3d", migrated)
                self.assertEqual(migrated["proptm3d"],
                                 {"run": True, "repo": "git+https://github.com/prolfqua/proptm3d",
                                  "max_proteins": 20})
                current = path.read_text()
                update(root)
                self.assertEqual(path.read_text(), current)

    def test_update_keeps_a_local_proptm3d_checkout_path(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = {"dir_out": "chosen_output",
                      "phospho_dea_dir": "site", "protein_dea_dir": "protein",
                      "enriched_h5ad": "site/Results_WU_example/AnnData.h5ad",
                      "total_h5ad": "protein/Results_WU_example/AnnData.h5ad",
                      "ptm3d": {"run": True, "repo": "/home/user/checkouts/ptm3d"}}
            path = root / "ptm_config.yaml"
            path.write_text(yaml.safe_dump(config))
            with patch("ptm_pipeline.init.copy_template_files", return_value=[]):
                update(root)
                migrated = yaml.safe_load(path.read_text())
                self.assertEqual(migrated["proptm3d"]["repo"], "/home/user/checkouts/proptm3d")
