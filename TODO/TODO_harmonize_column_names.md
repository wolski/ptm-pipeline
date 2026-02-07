# TODO: Harmonize DPA / DPU / CF-DPU Output Columns

## Problem

DPA, DPU, and CF-DPU produce results with different column names for the same concepts.
This forces mapping/rename code in multiple places downstream.

### Current Column Names

| Concept        | DPA               | DPU              | CF              |
|----------------|-------------------|------------------|-----------------|
| Effect size    | `diff.site`       | `diff_diff`      | `diff_diff`     |
| FDR            | `FDR.site`        | `FDR_I`          | `FDR_I`         |
| Statistic      | `statistic.site`  | `tstatistic_I`   | `statistic`     |
| Gene name      | `gene_name.site`  | `gene_name.site` | `gene_name`     |
| Protein length | present           | present          | **missing** (joined later from DPA) |

### Excel Sheet / File Names

| | DPA | DPU | CF |
|---|---|---|---|
| **File** | `Result_DPA.xlsx` | `Result_DPU.xlsx` | `CorrectFirst_PTM_usage_results.xlsx` |
| **Sheet** | `combinedSiteProteinData` | `combinedStats` | `results` |

### DPA vs DPU: NOT a Superset Relationship

DPA and DPU have fundamentally different column structures — one is NOT an extension of the other:

- **DPA** (`combined_site_prot`): Left join of phospho + protein, keeps both sides as parallel columns (`diff.site`, `diff.protein`, `FDR.site`, `FDR.protein`, etc.)
- **DPU** (`combined_test_diff` from `prophosqua::test_diff()`): Computes a new combined statistic — `diff_diff = diff.site - diff.protein`, with combined SE and new t-test. Original per-side columns are NOT preserved.
- **Row sets differ**: DPU includes `measured_In = "both" | "site" | "prot"` categories; DPA is phosphosite-centric (left join).

They could share one Excel file as separate sheets (they're already produced by the same Rmd), but cannot be collapsed into a single sheet.

### Where Mapping Code Currently Lives

| File | Lines | What it does |
|------|-------|-------------|
| `combine_ptm_results.R` | 29-49 | Per-type rename configs to standardize columns |
| `combine_ptm_results.R` | 57-62 | CF-only: join `gene_name` + `protein_length` from DPA |
| `feature_preparation.R` | 68-100 | `get_analysis_config()` with per-type sheet/column configs |
| `Analysis_CorrectFirst_DEA.Rmd` | 290-307 | CF renames `diff`->`diff_diff`, `FDR`->`FDR_I` at export |

## Implementation Steps

### Step 1: Add `gene_name` + `protein_length` to CF output (PRIORITY)

**Why:** The user-facing CF Excel currently lacks these columns. They are joined later from DPA data in `combine_ptm_results.R`, but the standalone CF file is incomplete.

**Where:** `template/src/Analysis_CorrectFirst_DEA.Rmd`, lines 263-280 (the `site_info` join)

**What:** The `site_info` select already reads from the phospho DEA xlsx `normalized_abundances` sheet, which has `gene_name` and `protein_length`. Just add them to both the new-format and old-format branches:

```r
# New format branch (line 264-271): add gene_name, protein_length to select()
site_info <- full_results |>
  dplyr::select(
    protein_Id_site,
    posInProtein = PTM_SiteLocation,
    modAA = PTM_SiteAA,
    SequenceWindow = !!sym(seq_col),
    gene_name, protein_length          # <-- ADD
  ) |>
  dplyr::distinct()

# Old format branch (line 275-277): add gene_name, protein_length to select()
site_info <- full_results |>
  dplyr::select(site, posInProtein, modAA, SequenceWindow = !!sym(seq_col),
                gene_name, protein_length) |>    # <-- ADD
  dplyr::distinct()
```

**Downstream cleanup after Step 1:**
- `combine_ptm_results.R`: remove `needs_join = TRUE` from CF config (line 47), remove the join block (lines 57-62), remove `reference_data` parameter from `standardize_results()` signature
- `combine_ptm_results.R`: update `standardize_cf()` wrapper (line 80) — no longer needs `dpa_data` argument
- `combine_ptm_results.R`: update `combine_ptm_results()` call at line 109 — `cf` no longer needs `dpa_raw`

### Step 2: Rename DPU columns to match DPA convention (in prophosqua)

**Why:** DPU uses `diff_diff`, `FDR_I`, `tstatistic_I` while DPA uses `diff.site`, `FDR.site`, `statistic.site`. Standardizing at the source eliminates downstream mapping.

**Where:** `prophosqua::test_diff()` in `prophosqua/R/test_diff_diff.R`

**What:** After computing diff-of-diffs, rename output columns:
- `diff_diff` -> `diff.site`
- `FDR_I` -> `FDR.site`
- `tstatistic_I` -> `statistic.site`

**Risk:** `test_diff()` may be used by other code outside ptm-pipeline. Check consumers before changing.

### Step 3: Rename CF columns to match DPA convention (in ptm-pipeline)

**Why:** CF uses `diff_diff`, `FDR_I`, `statistic` — yet another variation.

**Where:** `template/src/Analysis_CorrectFirst_DEA.Rmd`, line 292

**What:** Change the rename at export:
```r
# Current:
dplyr::rename(diff_diff = diff, FDR_I = FDR)
# Change to:
dplyr::rename(diff.site = diff, FDR.site = FDR, statistic.site = statistic)
```

### Step 4: Simplify downstream mapping

Once Steps 1-3 are done, all three types use identical column names. Then:
- `combine_ptm_results.R`: replace 3 per-type configs with one shared config, remove all rename logic
- `feature_preparation.R`: collapse `get_analysis_config()` — `stat_col`, `diff_col`, `fdr_col` are the same for all types
- `ptm_config.yaml`: `stat_column` becomes a single shared value, not per-analysis

## Target State

All three analysis types export with identical column names:

| Concept        | Standardized Name  |
|----------------|--------------------|
| Effect size    | `diff.site`        |
| FDR            | `FDR.site`         |
| Statistic      | `statistic.site`   |
| Gene name      | `gene_name`        |
| Protein length | `protein_length`   |

## Notes

- DPA vs DPU/CF represent fundamentally different biological questions (raw vs protein-corrected) — only the **column naming** should be harmonized, not the analyses themselves
- Step 1 is self-contained within ptm-pipeline and should be done first
- Step 2 touches prophosqua and may affect other consumers of `test_diff()` — check for downstream dependencies before changing
- File/sheet naming is a secondary concern; column names are the priority
