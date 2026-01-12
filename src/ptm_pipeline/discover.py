"""Auto-discovery of DEA folders and annotation files."""

from pathlib import Path
import csv
from typing import NamedTuple


class DEAFolders(NamedTuple):
    """Container for discovered DEA folder paths."""
    phospho: Path | None
    protein: Path | None


def find_dea_folders(project_dir: Path) -> DEAFolders:
    """Find phospho and protein DEA folders in project directory.

    Looks for patterns:
    - DEA_*_WUphospho_* → phospho DEA
    - DEA_*_WUprot_* or DEA_*_WUtotal_* → protein DEA

    Returns the most recent (by name, assuming date prefix) if multiple found.
    """
    phospho_dirs = sorted(project_dir.glob("DEA_*_WUphospho_*"), reverse=True)
    protein_dirs = sorted(
        list(project_dir.glob("DEA_*_WUprot_*")) +
        list(project_dir.glob("DEA_*_WUtotal_*")),
        reverse=True
    )

    # Filter to only directories
    phospho_dirs = [d for d in phospho_dirs if d.is_dir()]
    protein_dirs = [d for d in protein_dirs if d.is_dir()]

    return DEAFolders(
        phospho=phospho_dirs[0] if phospho_dirs else None,
        protein=protein_dirs[0] if protein_dirs else None,
    )


def find_all_dea_folders(project_dir: Path) -> dict[str, list[Path]]:
    """Find all DEA folders, grouped by type.

    Returns dict with 'phospho' and 'protein' keys, each containing list of paths.
    """
    phospho_dirs = sorted(
        [d for d in project_dir.glob("DEA_*_WUphospho_*") if d.is_dir()],
        reverse=True
    )
    protein_dirs = sorted(
        [d for d in
         list(project_dir.glob("DEA_*_WUprot_*")) +
         list(project_dir.glob("DEA_*_WUtotal_*"))
         if d.is_dir()],
        reverse=True
    )

    return {"phospho": phospho_dirs, "protein": protein_dirs}


def find_annotation_file(phospho_dea_dir: Path) -> Path | None:
    """Find annotation file inside phospho DEA folder.

    Looks in Inputs_*/ subdirectory for phospho_annot_*.tsv
    """
    inputs_dirs = list(phospho_dea_dir.glob("Inputs_*"))
    if not inputs_dirs:
        return None

    for inputs_dir in inputs_dirs:
        annot_files = list(inputs_dir.glob("*_annot_*.tsv"))
        if annot_files:
            return annot_files[0]

    return None


def parse_contrasts(annot_file: Path) -> list[str]:
    """Parse contrast names from annotation TSV file.

    Expects columns: FileName, Group, Name, ContrastName, Contrast
    Returns unique non-NA contrast names.
    """
    contrasts = set()

    with open(annot_file, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            contrast_name = row.get("ContrastName", "").strip()
            if contrast_name and contrast_name.upper() != "NA":
                contrasts.add(contrast_name)

    return sorted(contrasts)


def get_experiment_name(phospho_dea_dir: Path) -> str:
    """Extract experiment name from DEA folder name.

    E.g., DEA_20260109_WUphospho_SHP2_vsn → SHP2
    """
    name = phospho_dea_dir.name
    # Remove prefix: DEA_YYYYMMDD_WUphospho_
    parts = name.split("_")
    if len(parts) >= 4:
        # Join everything after WUphospho
        idx = next((i for i, p in enumerate(parts) if "phospho" in p.lower()), -1)
        if idx >= 0 and idx + 1 < len(parts):
            return "_".join(parts[idx + 1:])
    return "experiment"
