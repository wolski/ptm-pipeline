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


ANNOTATION_NAME_PATTERNS = ("*annot*", "*dataset*")
ANNOTATION_SUFFIXES = (".tsv", ".csv")


def find_annotation_file(phospho_dea_dir: Path) -> Path | None:
    """Find annotation file inside phospho DEA folder.

    Looks in Inputs_*/ subdirectory for a name containing "annot" (standard
    prolfqua format) or "dataset" (alternative format with Group/Control
    columns), as .tsv or .csv. prolfquapp copies whatever the DEA was given
    under its original name, so the match is on the substring rather than on
    a fixed "_annot_" spelling.
    """
    inputs_dirs = list(phospho_dea_dir.glob("Inputs_*"))
    if not inputs_dirs:
        return None

    for inputs_dir in inputs_dirs:
        for name_pattern in ANNOTATION_NAME_PATTERNS:
            for suffix in ANNOTATION_SUFFIXES:
                matches = sorted(inputs_dir.glob(name_pattern + suffix))
                if matches:
                    return matches[0]

    return None


def parse_contrasts(annot_file: Path) -> list[str]:
    """Parse contrast names from annotation TSV file.

    Supports two formats:
    1. Standard: has ContrastName column with explicit contrast names
    2. Dataset: has Group and Control columns (T=treatment, C=control)

    Returns unique non-NA contrast names.
    """
    contrasts = set()

    delimiter = "," if annot_file.suffix.lower() == ".csv" else "\t"

    with open(annot_file, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return []

        # Column names are matched case-insensitively: prolfquapp writes CONTROL
        # (run_contrasts_single) while hand-written annotations use Control.
        first_row = rows[0]
        by_lower = {name.lower(): name for name in first_row if name}
        contrast_col = by_lower.get("contrastname")
        group_col = by_lower.get("group")
        control_col = by_lower.get("control")

        if contrast_col:
            # Standard format with explicit contrast names
            for row in rows:
                contrast_name = (row.get(contrast_col) or "").strip()
                if contrast_name and contrast_name.upper() != "NA":
                    contrasts.add(contrast_name)

        elif group_col and control_col:
            # Dataset format: derive contrast from Group/Control
            # Control='C' means control group, Control='T' means treatment
            control_groups = set()
            treatment_groups = set()

            for row in rows:
                group = (row.get(group_col) or "").strip()
                control_flag = (row.get(control_col) or "").strip().upper()

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
