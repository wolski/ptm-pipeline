"""Auto-discovery of DEA folders and annotation files."""

from pathlib import Path
import csv


def find_all_dea_folders(project_dir: Path) -> dict[str, list[Path]]:
    """Find all DEA folders, grouped by type.

    Returns dict with 'phospho' and 'protein' keys, each containing list of paths.
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

    return {"phospho": phospho_dirs, "protein": protein_dirs}


def find_annotation_file(phospho_dea_dir: Path) -> Path | None:
    """Find annotation file inside phospho DEA folder.

    Looks in Inputs_*/ subdirectory for:
    - *_annot_*.tsv (standard prolfqua format)
    - *_dataset*.tsv (alternative format with Group/Control columns)
    """
    inputs_dirs = list(phospho_dea_dir.glob("Inputs_*"))
    if not inputs_dirs:
        return None

    for inputs_dir in inputs_dirs:
        # Try standard annotation file first
        annot_files = list(inputs_dir.glob("*_annot_*.tsv"))
        if annot_files:
            return annot_files[0]

        # Try dataset file (alternative format)
        dataset_files = list(inputs_dir.glob("*_dataset*.tsv"))
        if dataset_files:
            return dataset_files[0]

    return None


def parse_contrasts(annot_file: Path) -> list[str]:
    """Parse contrast names from annotation TSV file.

    Supports two formats:
    1. Standard: has ContrastName column with explicit contrast names
    2. Dataset: has Group and Control columns (T=treatment, C=control)

    Returns unique non-NA contrast names.
    """
    contrasts = set()

    with open(annot_file, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)

        if not rows:
            return []

        # Check which format we have
        first_row = rows[0]

        if "ContrastName" in first_row:
            # Standard format with explicit contrast names
            for row in rows:
                contrast_name = row.get("ContrastName", "").strip()
                if contrast_name and contrast_name.upper() != "NA":
                    contrasts.add(contrast_name)

        elif "Group" in first_row and "Control" in first_row:
            # Dataset format: derive contrast from Group/Control
            # Control='C' means control group, Control='T' means treatment
            control_groups = set()
            treatment_groups = set()

            for row in rows:
                group = row.get("Group", "").strip()
                control_flag = row.get("Control", "").strip().upper()

                if control_flag == "C":
                    control_groups.add(group)
                elif control_flag == "T":
                    treatment_groups.add(group)

            # Generate contrast names: treatment_vs_control
            for treatment in sorted(treatment_groups):
                for control in sorted(control_groups):
                    contrasts.add(f"{treatment}_vs_{control}")

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
