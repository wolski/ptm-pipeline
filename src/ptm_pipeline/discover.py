"""Auto-discovery of DEA folders, AnnData artifacts and stored contrasts."""

from pathlib import Path
import h5py
import numpy as np


def find_all_dea_folders(project_dir: Path) -> dict[str, list[Path]]:
    """Find all DEA folders, grouped by type.

    Returns dict with 'phospho', 'protein' and 'protein_peptide' keys, each
    containing list of paths.
    """
    # Phospho patterns - multiple naming conventions
    phospho_dirs = set()
    for pattern in ["DEA_*_WUphospho_*", "DEA_*_WUcombined_*", "DEA_*_*STY*"]:
        phospho_dirs.update(d for d in project_dir.glob(pattern) if d.is_dir())
    phospho_dirs = sorted(phospho_dirs, key=lambda x: x.name, reverse=True)

    # Protein patterns
    protein_dirs = sorted(
        [d for d in
         list(project_dir.glob("DEA_*_WUprot_*")) +
         list(project_dir.glob("DEA_*_WUtotal_*"))
         if d.is_dir()],
        key=lambda x: x.name,
        reverse=True
    )

    # A peptide-level total DEA names its workunit *peptide*; its AnnData looks
    # like any other, so the name is what tells it apart.
    def peptide_level(d: Path) -> bool:
        return "peptide" in d.name.lower()

    return {
        "phospho": phospho_dirs,
        "protein": [d for d in protein_dirs if not peptide_level(d)],
        "protein_peptide": [d for d in protein_dirs if peptide_level(d)],
    }


def find_dea_anndata(dea_dir: Path) -> Path | None:
    """Find the producer's DEA AnnData artifact in a selected DEA directory."""
    matches = sorted(dea_dir.glob("Results_WU_*/AnnData.h5ad"))
    return matches[0] if matches else None


# The PTM import reads what prolfquapp 2.10.5 writes: schema 2.1.0, with the
# imputedData layer and the feature keys in every result frame.
SUPPORTED_DEA_SCHEMAS = {"2.1.0"}


def read_dea_contrasts(path: Path) -> list[str]:
    """Read the stored contrast names without guessing from an annotation file."""
    with h5py.File(path) as handle:
        metadata = handle["uns/prolfquapp"]
        if metadata["schema_version"].asstr()[()] not in SUPPORTED_DEA_SCHEMAS:
            raise ValueError(f"Unsupported prolfquapp schema in {path}")
        names = metadata["contrasts/contrast_name"].asstr()[()]
        return np.atleast_1d(names).tolist()


def get_experiment_name(phospho_dea_dir: Path) -> str:
    """Extract experiment name from DEA folder name.

    E.g., DEA_20260109_WUphospho_SHP2_vsn → SHP2
         DEA_20260113_WUcombined_STY_batch_vsn → STY_batch
    """
    name = phospho_dea_dir.name
    parts = name.split("_")
    if len(parts) >= 4:
        # Find the WU-prefixed part (WUphospho, WUcombined, etc.)
        for keyword in ("phospho", "combined"):
            idx = next((i for i, p in enumerate(parts) if keyword in p.lower()), -1)
            if idx >= 0 and idx + 1 < len(parts):
                suffix = "_".join(parts[idx + 1:])
                # Strip trailing _vsn suffix
                if suffix.endswith("_vsn"):
                    suffix = suffix[:-4]
                return suffix
    return "experiment"
