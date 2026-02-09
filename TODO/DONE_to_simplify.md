# Your test constrain


After your refactoring this must still run.

```
uv tool install /Users/wolski/projects/ptm-pipeline --force
ptm-pipeline init
cd /Users/wolski/projects/ptm-pipeline/test_data/p40060_DanielGao
make all
```

And results must be the same in:

./PTM_42C_vs_37C

So you must generate a different result folder.


# Code Simplification Opportunities

Analysis of `/Users/wolski/projects/ptm-pipeline/template/src/` for simplification opportunities.

## Summary

The codebase shows good overall structure with shared utility files (`dea_utils.R`, `enrichment_viz_utils.R`, `feature_preparation.R`) that reduce duplication across Rmd files. However, there are several opportunities for simplification:

1. **Duplicated column configuration logic** appears in multiple files (prep_kinaselib.R, feature_preparation.R, Analysis_KinaseLibrary_GSEA.Rmd)
2. **Repeated data loading and validation patterns** across Rmd files
3. **Redundant code in enrichment analysis files** (Analysis_MEA.Rmd, Analysis_KinaseLibrary_GSEA.Rmd, Analysis_PTMSEA.Rmd)
4. **Overly verbose result extraction** that could use shared utilities
5. **Inconsistent parameter handling** across files

---

## Per-File Analysis

### dea_utils.R

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 9-38 | `get_dea_xlsx` has redundant pattern: `results_dir <- results_dir[1]` at line 19 could be integrated into initial assignment |
| Low | 47-54, 63-70 | `get_dea_parquet` and `get_dea_yaml` are near-identical functions that differ only in filename pattern - could be consolidated into a single generic function with a filename parameter |

**Specific findings:**

- Lines 47-54 (`get_dea_parquet`) and lines 63-70 (`get_dea_yaml`) follow identical patterns:
  ```r
  pattern <- file.path(dea_dir, "Results_WU_*", "FILENAME")
  matches <- Sys.glob(pattern)
  if (length(matches) == 0) { stop(...) }
  return(matches[1])
  ```
  These could be a single `get_dea_file(dea_dir, filename)` function.

---

### enrichment_viz_utils.R

| Priority | Lines | Issue |
|----------|-------|-------|
| Medium | 22-29, 63-72 | Similar `mutate` blocks for calculating `neg_log_fdr` and `significant` appear in both `plot_enrichment_dotplot` and `plot_enrichment_volcano` |
| Low | 186-214 | `export_gsea_plots_pdf` iterates through results inefficiently - could extract geneset metadata in one step instead of filtering twice (line 188 and 195) |
| Low | 250-263 | `extract_gsea_results` uses verbose explicit column extraction - could use `select()` instead of manual `tibble()` construction |

**Specific findings:**

- Lines 24-25 and lines 64-66: Repeated pattern for calculating derived columns:
  ```r
  neg_log_fdr = -log10(pmax(.data[[fdr_col]], 1e-10)),
  significant = .data[[fdr_col]] < threshold
  ```
  Could be a shared helper function.

- Lines 195: Inside the loop, the code filters `res@result` twice:
  ```r
  row <- res@result |> as_tibble() |> filter(ID == geneset)
  ```
  This is already filtering data that was filtered at line 188-192. The row data could be extracted in the initial filter step.

---

### feature_preparation.R

| Priority | Lines | Issue |
|----------|-------|-------|
| Medium | 53-76 | `prepare_ntoc_data` has redundant `modelName.site` assignment logic - the DPA branch conditionally adds it, but it could be simplified |
| Low | 106-134 | `get_analysis_config` duplicates configuration that also exists in `prep_kinaselib.R` (lines 40-56) |

**Specific findings:**

- Lines 58-60: Conditional mutate is verbose:
  ```r
  dplyr::mutate(
    modelName.site = if ("modelName.site" %in% names(data)) modelName.site else "observed"
  )
  ```
  Could use `dplyr::coalesce()` or check once before the function.

- Lines 106-134: `get_analysis_config()` defines sheet names, column mappings for DPA/DPU/CF. This same configuration exists in:
  - `prep_kinaselib.R` lines 40-56
  - `Analysis_KinaseLibrary_GSEA.Rmd` lines 66-70
  These should be consolidated into a single source.

---

### prep_kinaselib.R

| Priority | Medium | Issue |
|----------|--------|-------|
| Medium | 40-56 | Column configuration duplicates `feature_preparation.R` `get_analysis_config()` |
| Low | 89-98 | Sequence cleaning logic (`filter`, `mutate(toupper)`) is duplicated with similar patterns in other files |

**Specific findings:**

- Lines 40-56: This configuration block is nearly identical to `feature_preparation.R` lines 106-125:
  ```r
  col_config <- list(
    DPA = list(sheet = ..., diff_col = ..., flanking_col = ...),
    DPU = list(...),
    CF = list(...)
  )
  ```

---

### prep_ptmsigdb.R

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 85-91 | `write_gmt` is a local function that could be shared or use an existing package function |
| Low | 48-53 | Pathway merging uses explicit loop with `lapply` - could use purrr or vectorized operations |

**Specific findings:**

- Lines 85-91: Local `write_gmt` function. Consider using `fgsea::writeGmtPathways()` if available, or move to a shared utility.

---

### combine_ptm_results.R

| Priority | Lines | Issue |
|----------|-------|-------|
| Medium | 20-57 | Three `standardize_*` functions share significant structure - could be consolidated with a configuration-driven approach |
| Low | 105-124 | Data loading for abundances has repetitive pivot_wider patterns |

**Specific findings:**

- Lines 20-28, 32-39, 44-57: The three standardize functions (`standardize_dpa`, `standardize_dpu`, `standardize_cf`) all do similar select/rename operations. They could be a single function:
  ```r
  standardize_results <- function(data, analysis_type, join_data = NULL) {
    config <- get_analysis_config(analysis_type)
    # Apply column mapping based on config
  }
  ```

- Lines 113-124: Repeated pattern of loading parquet, selecting columns, pivoting. Could be a helper function.

---

### render_dpu_overview.R

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 47-52 | `make_DEA_config_R6` creates a config but some parameters are hardcoded - could be more flexible |

**Specific findings:**

- Lines 47-52: Hardcoded values like `ORDERID = "fgcz_project"` reduce flexibility. Consider parameterizing.

---

### Analysis_MEA.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Medium | 58-72 | Column renaming logic with multiple `if` statements for different MEA output formats - could be more elegant |
| Medium | 78-89 | `mea_clean` mutate block duplicates enrichment preprocessing from `enrichment_viz_utils.R` |
| Low | 106-139 | Per-contrast loop with inline cat/print could be cleaner with helper functions |

**Specific findings:**

- Lines 58-72: Multiple conditional renames:
  ```r
  if ("Kinase" %in% names(mea_results)) { mea_results <- mea_results |> rename(kinase = Kinase) }
  if ("p.value" %in% names(mea_results)) { ... }
  ```
  Could use a column mapping approach or `rename_with()`.

- Lines 78-89: Creates `neg_log_fdr`, `direction`, `significant` columns - same pattern as in enrichment_viz_utils.R volcano/dotplot functions. Consider a shared `prepare_enrichment_data()` helper.

---

### Analysis_KinaseLibrary_GSEA.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Medium | 66-70 | Column configuration duplicates `prep_kinaselib.R` and `feature_preparation.R` |
| Medium | 369-377 | Result extraction duplicates pattern from lines 393-399 in export section |
| Low | 265-277 | Individual dotplot generation loop could be simplified |

**Specific findings:**

- Lines 66-70: Same column config pattern seen in 3 other files.

- Lines 369-377 and 393-399: Both extract results from gsea_results in the same way:
  ```r
  names(gsea_results) |>
    map_dfr(function(ct) {
      gsea_results[[ct]]@result |> as_tibble() |> ...
    })
  ```
  Should use `extract_gsea_results()` from enrichment_viz_utils.R instead.

---

### Analysis_PTMSEA.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 63-65 | Development devtools::load_all pattern repeated in multiple Rmds - could be a shared setup chunk |
| Low | 119-137 | Overlap statistics calculation is verbose - could be a utility function |
| Medium | 354-381 | GSEA plot loop nearly identical to Analysis_KinaseLibrary_GSEA.Rmd lines 336-362 |

**Specific findings:**

- Lines 63-65: This pattern appears in multiple Rmds:
  ```r
  if (file.exists("~/projects/prophosqua")) {
    devtools::load_all("~/projects/prophosqua", quiet = TRUE)
  }
  ```

- Lines 354-381: The GSEA example plots loop is nearly identical between Analysis_PTMSEA.Rmd and Analysis_KinaseLibrary_GSEA.Rmd. Could be a shared function.

---

### Analysis_DPA_DPU.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 36-38 | Development prophosqua loading pattern - same as other Rmds |
| Low | 98-103 | `join_column` definition is verbose - could use named vector directly |

**Specific findings:**

- Lines 98-103: Could be simplified:
  ```r
  # Current
  join_column <- c("protein_Id" = "protein_Id", "contrast", "description", "protein_length")
  # Simpler
  join_column <- c("protein_Id", "contrast", "description", "protein_length")
  ```
  The `"protein_Id" = "protein_Id"` syntax is only needed when names differ.

---

### Analysis_n_to_c.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 47-49 | Development prophosqua loading - same pattern |
| Low | 139-143 | Output directory determination uses verbose if/else - could use `%||%` operator |

**Specific findings:**

- Lines 139-143:
  ```r
  pdf_dir <- if (!is.null(params$output_dir)) {
    params$output_dir
  } else {
    dirname(params$xlsx_file)
  }
  ```
  Could be: `pdf_dir <- params$output_dir %||% dirname(params$xlsx_file)`

---

### Analysis_seqlogo.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 43-46 | `is_docx` check is verbose and has redundant condition |
| Low | 101-112 | Conditional table output (flextable vs kable) is verbose |

**Specific findings:**

- Lines 43-46:
  ```r
  is_docx <- knitr::pandoc_to() == "docx"
  if (length(is_docx) == 0) {
    is_docx <- TRUE
  }
  ```
  Could be: `is_docx <- identical(knitr::pandoc_to(), "docx")`

---

### Analysis_CorrectFirst_DEA.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Medium | 31-51 | Parameter defaulting logic is overly complex - could use standard Rmd params with defaults |
| Medium | 191-217 | Contrast generation logic with nested loops is complex - could be simplified |
| Low | 262-280 | Column format detection (new vs old) has verbose branching |

**Specific findings:**

- Lines 31-51: The manual default_params handling with loop to fill missing params is non-standard. R Markdown params YAML already supports defaults. This entire section could likely be removed if params are properly defined in YAML header.

- Lines 191-217: Nested loops for generating contrasts:
  ```r
  for (trt in sort(treatment_groups)) {
    for (ctrl in sort(control_groups)) { ... }
  }
  ```
  Could use `expand.grid()` or `tidyr::crossing()` for cleaner cross-product.

- Lines 262-280: New vs old format column handling has two nearly identical code paths. Could use a mapping approach.

---

### create_top_index.Rmd

| Priority | Lines | Issue |
|----------|-------|-------|
| Low | 29-35 | `link_if_exists` returns empty string on failure - could return NA for cleaner table handling |
| Medium | 68-109, 115-162, 169-212 | Three nearly identical section generators (DPA, DPU, CF) - high duplication |

**Specific findings:**

- Lines 68-109, 115-162, 169-212: The three analysis sections (DPA, DPU, CF) follow the same pattern but with different directory paths. This could be refactored to:
  ```r
  generate_analysis_section <- function(analysis_type, base_dir) {
    # Generate the markdown table for one analysis type
  }
  ```
  Then call it three times with different parameters.

---

## Recommendations (Prioritized)

### High Priority

1. **Consolidate column configuration** - Create a single `analysis_config.R` file with `get_analysis_config()` and remove duplicates from `prep_kinaselib.R`, `feature_preparation.R`, and `Analysis_KinaseLibrary_GSEA.Rmd`

2. **Create shared enrichment data preparation** - Add `prepare_enrichment_data()` to `enrichment_viz_utils.R` to handle the common pattern of adding `neg_log_fdr`, `direction`, and `significant` columns

3. **Refactor create_top_index.Rmd** - Extract the repeated section generation into a function to eliminate ~100 lines of duplication

### Medium Priority

4. **Consolidate standardize functions** in `combine_ptm_results.R` - Use configuration-driven approach

5. **Simplify Analysis_CorrectFirst_DEA.Rmd param handling** - Use proper Rmd param defaults

6. **Extract GSEA example plot generation** - Create shared function for Analysis_PTMSEA.Rmd and Analysis_KinaseLibrary_GSEA.Rmd

### Low Priority

7. **Merge get_dea_parquet/get_dea_yaml** in dea_utils.R into single generic function

8. **Use null-coalescing operator** (`%||%`) for optional parameter fallbacks

9. **Standardize development prophosqua loading** - Create shared setup chunk

10. **Simplify is_docx detection** in Analysis_seqlogo.Rmd

---

## Estimated Impact

| Category | Files Affected | Lines Reducible |
|----------|----------------|-----------------|
| Column config consolidation | 4 | ~60 |
| Enrichment data prep | 3 | ~30 |
| Index section generation | 1 | ~100 |
| Standardize functions | 1 | ~25 |
| GSEA plot generation | 2 | ~40 |
| **Total** | **11** | **~255** |

---

*Generated: 2026-01-26*
