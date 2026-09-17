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
                      "ptm3d": {"max_proteins": None}}
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
