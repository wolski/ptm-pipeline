"""Shared utilities for creating small, committable test datasets from full DEA output.

Used by create_test_*.py scripts to cut the phospho and protein DEA AnnData files,
the only DEA output the pipeline reads, down to a few hundred sites and their
proteins. The DEAs are rerun by rerun_deas.sh with only the contrasts a test keeps.
"""

import random
import shutil
from collections import Counter
from pathlib import Path

import anndata as ad
import pandas as pd


def accession(protein_id: str) -> str:
    """UniProt accession of a bare or FASTA-style (sp|P12345|NAME) protein ID."""
    parts = protein_id.split("|")
    return parts[1] if len(parts) >= 3 else protein_id


def anndata_file(dea_dir: Path) -> Path:
    """The single Results_WU_*/AnnData.h5ad of a DEA folder."""
    files = sorted(dea_dir.glob("Results_WU_*/AnnData.h5ad"))
    if len(files) != 1:
        raise FileNotFoundError(f"Expected one Results_WU_*/AnnData.h5ad in {dea_dir}, found {len(files)}")
    return files[0]


def contrast_fdr(adata: ad.AnnData) -> pd.DataFrame:
    """FDR of every feature (rows) in every contrast (columns), from the contrast varm frames."""
    fdr_col = adata.uns["prolfquapp"]["contrast_configuration"]["fdr_col"]
    frames = {
        frame["contrast"].dropna().iloc[0]: frame[fdr_col]
        for frame in adata.varm.values()
        if isinstance(frame, pd.DataFrame) and "contrast" in frame and fdr_col in frame
    }
    return pd.DataFrame(frames, index=adata.var_names)


def _flag(var: pd.DataFrame, column: str) -> pd.Series:
    if column not in var:
        return pd.Series(False, index=var.index)
    return var[column].astype(str).str.upper().isin(["TRUE", "1"])


def select_phosphosites(phospho: ad.AnnData, n_phospho: int) -> list[str]:
    """Select n_phospho sites with a result in every contrast, plus ~20% with only some.

    Sites flagged REV or CON, or without a sequence window, are left out.
    """
    var = phospho.var
    window = var["SequenceWindow"].astype(str)
    valid = ~_flag(var, "REV") & ~_flag(var, "CON") & (window.str.len() >= 7) & (window != "None")
    fdr = contrast_fdr(phospho)[valid.to_numpy()]
    present = fdr.notna()
    complete = list(fdr.index[present.all(axis=1)])
    partial = {c: list(fdr.index[present[c] & ~present.all(axis=1)]) for c in fdr.columns}
    print(f"Valid sites: {len(complete)} complete (all {fdr.shape[1]} contrasts), "
          f"partial: { {c: len(v) for c, v in partial.items()} }")

    selected = set(random.sample(complete, min(n_phospho, len(complete))))
    n_per_contrast = max(1, n_phospho // 5 // max(1, fdr.shape[1]))
    for sites in partial.values():
        available = [s for s in sites if s not in selected]
        selected.update(random.sample(available, min(n_per_contrast, len(available))))

    sites = [s for s in phospho.var_names if s in selected]
    print(f"Selected {len(sites)} phosphosites from {var.loc[sites, 'protein_Id'].nunique()} proteins")
    print(f"  modAA distribution: {dict(Counter(var.loc[sites, 'modAA']))}")
    return sites


def select_proteins(protein: ad.AnnData, phospho_proteins: set[str]) -> list[str]:
    """Select the protein (or peptide) features whose protein a selected site belongs to."""
    accessions = {accession(p) for p in phospho_proteins}
    keep = protein.var["protein_Id"].map(accession).isin(accessions)
    print(f"Features of the {len(accessions)} phospho proteins: {keep.sum()}")
    return list(protein.var_names[keep.to_numpy()])


def first_per_protein(adata: ad.AnnData, features: list[str], n: int) -> list[str]:
    """The first n features of each protein, which keeps a peptide-level subset small."""
    var = adata.var.loc[features]
    kept = var.groupby("protein_Id", sort=False, observed=True).head(n)
    print(f"  {len(kept)} of {len(features)} features, at most {n} per protein")
    return list(kept.index)


def write_subset(adata: ad.AnnData, features: list[str], path: Path) -> None:
    """Write the features' AnnData; strings stay strings, which R reads as character."""
    path.parent.mkdir(parents=True, exist_ok=True)
    adata[:, features].copy().write_h5ad(path, compression="gzip", convert_strings_to_categoricals=False)
    print(f"  {path}: {len(features)} features")


def run_subset(cfg: dict):
    """Subset the phospho and protein DEA AnnData and copy their annotations.

    cfg keys: seed, src_dir, out_dir, phospho_dea, protein_dea, phospho_annot,
    protein_annot (annotation file names in the DEA's Inputs_WU_*), n_phospho;
    optionally peptide_dea, peptide_annot and peptides_per_protein, a
    peptide-level total DEA cut to that many peptides of each selected protein.
    """
    random.seed(cfg["seed"])
    src_dir = Path(cfg["src_dir"])
    out_dir = Path(cfg["out_dir"])
    print(f"Source: {src_dir}\nOutput: {out_dir}\n")

    phospho_file = anndata_file(src_dir / cfg["phospho_dea"])
    protein_file = anndata_file(src_dir / cfg["protein_dea"])
    phospho = ad.read_h5ad(phospho_file)
    protein = ad.read_h5ad(protein_file)

    print("--- Selecting phosphosites ---")
    sites = select_phosphosites(phospho, cfg["n_phospho"])
    print("\n--- Selecting proteins ---")
    proteins = select_proteins(protein, set(phospho.var.loc[sites, "protein_Id"]))
    peptide_file = anndata_file(src_dir / cfg["peptide_dea"]) if cfg.get("peptide_dea") else None
    peptide = ad.read_h5ad(peptide_file) if peptide_file else None
    peptides = (
        first_per_protein(peptide, select_proteins(peptide, set(phospho.var.loc[sites, "protein_Id"])),
                          cfg["peptides_per_protein"])
        if peptide is not None else []
    )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    print("\n--- Writing subsets ---")
    subsets = [
        (cfg["phospho_dea"], phospho_file, phospho, sites, cfg["phospho_annot"]),
        (cfg["protein_dea"], protein_file, protein, proteins, cfg["protein_annot"]),
    ]
    if peptide is not None:
        subsets.append((cfg["peptide_dea"], peptide_file, peptide, peptides, cfg["peptide_annot"]))
    for dea, source, adata, features, annotation in subsets:
        write_subset(adata, features, out_dir / dea / source.parent.name / "AnnData.h5ad")
        inputs = next((src_dir / dea).glob("Inputs_WU_*"))
        (out_dir / dea / inputs.name).mkdir(parents=True)
        shutil.copy2(inputs / annotation, out_dir / dea / inputs.name / annotation)

    total = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    print(f"\n  TOTAL: {total / 1024 / 1024:.1f} MB\nDone!")
