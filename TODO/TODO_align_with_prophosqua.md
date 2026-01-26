# Align PTM-Pipeline with Prophosqua: Detailed Refactoring Plan

**Goal:** DRY the code between ptm-pipeline and prophosqua by:
1. Moving shared R functions to prophosqua package
2. Creating parametrizable vignettes that work standalone and in pipeline context
3. Adding tests for shared functions
4. Reducing maintenance burden by having a single source of truth

---

## Current State Analysis

### Prophosqua Package Structure (v0.2.0)

**Exported Functions (from NAMESPACE):**
```
# Core Analysis
ptmsea_data_prep(), run_ptmsea(), run_ptmsea_up_down()
download_ptmsigdb(), trim_ptmsigdb_pathways(), ptmsigdb_to_term2gene()
scan_motifs(), run_motif_gsea(), get_kinase_motifs()

# N-to-C Plotting
n_to_c_plot(), n_to_c_plot_integrated()
n_to_c_expression(), n_to_c_usage()
n_to_c_expression_multicontrast(), n_to_c_usage_multicontrast()
prepare_n_to_c_data()

# Sequence Logos
plot_diff_logo(), plot_seqlogo_with_diff()

# Data Processing
load_and_preprocess_data(), filter_contaminants(), test_diff()
explode_multisites(), get_sequence_windows()
```

**Vignettes:**
- `Analysis_PTMSEA.Rmd` - PTMsigDB GSEA analysis
- `Analysis_KinaseLibrary.Rmd` - Kinase Library GSEA analysis
- `Analysis_Motif_Enrichment.Rmd` - Motif enrichment (prophosqua scan_motifs)
- `Vis_MEA.Rmd` - MEA visualization
- `MiMBIntegratedPTM.Rmd` - Full manuscript workflow

### PTM-Pipeline Template Structure

**R Utility Files:**
- `enrichment_viz_utils.R` - Visualization functions (NOT in prophosqua)
- `feature_preparation.R` - Data prep helpers (partial overlap)
- `dea_utils.R` - DEA file finding utilities (unique to pipeline)
- `combine_ptm_results.R` - Result standardization (unique to pipeline)
- `prep_kinaselib.R` - Kinase Library CLI prep (unique to pipeline)
- `prep_ptmsigdb.R` - PTMsigDB download/merge (extends prophosqua)

**Rmd Templates:**
- `Analysis_PTMSEA.Rmd` - ~85% overlap with prophosqua vignette
- `Analysis_KinaseLibrary_GSEA.Rmd` - ~95% overlap with prophosqua vignette
- `Analysis_MEA.Rmd` - ~80% overlap with Vis_MEA.Rmd
- `Analysis_seqlogo.Rmd` - Uses prophosqua functions
- `Analysis_n_to_c.Rmd` - Uses prophosqua functions
- `Analysis_DPA_DPU.Rmd` - Workflow-specific
- `Analysis_CorrectFirst_DEA.Rmd` - Workflow-specific

---

## Gap Analysis: What's Missing in Prophosqua

### 1. Enrichment Visualization Functions
**Location:** `ptm-pipeline/template/src/enrichment_viz_utils.R`
**Functions to move:**
```r
prepare_enrichment_data(data, fdr_col, fdr_threshold)
plot_enrichment_dotplot(data, item_col, fdr_col, n_top, title, subtitle)
plot_enrichment_volcano(data, item_col, fdr_col, fdr_threshold, ...)
plot_enrichment_heatmap(data, item_col, fdr_col, fdr_filter, n_top, ...)
export_gsea_plots_pdf(results, output_file, fdr_threshold, ...)
summarize_enrichment_results(results, fdr_thresholds)
extract_gsea_results(results)
```

### 2. Feature Preparation Helpers
**Location:** `ptm-pipeline/template/src/feature_preparation.R`
**Functions to move:**
```r
filter_significant_sites(data, fdr_col, diff_col, fdr_threshold, fc_threshold)
validate_sequence_window(data, seq_col, mod_col, window_center)
get_analysis_config(analysis_type)  # DPA/DPU/CF column mapping
summarize_significant_sites(data, group_cols)
```

### 3. GSEA Rank Preparation Pattern
**Currently inline in both projects:**
```r
# This pattern is duplicated in:
# - prophosqua/vignettes/Analysis_KinaseLibrary.Rmd
# - ptm-pipeline/template/src/Analysis_KinaseLibrary_GSEA.Rmd
# - ptm-pipeline/template/src/prep_kinaselib.R

ranks <- contrasts |> set_names() |>
  map(function(ct) {
    data |> filter(contrast == ct) |>
      mutate(seq = toupper(trimws(SequenceWindow))) |>
      filter(!is.na(stat_col)) |>
      distinct(seq, .keep_all = TRUE) |>
      arrange(desc(stat_col)) |>
      (\(df) setNames(df[[stat_col]], df$seq))()
  })
```

**Should be:** `prepare_gsea_ranks(data, stat_col, seq_col, contrast_col)`

---

## Refactoring Plan

### Phase 1: Move Visualization Functions to Prophosqua (HIGH PRIORITY)

**Target:** Create `prophosqua/R/enrichment_visualization.R`

**Steps:**
1. Copy functions from `ptm-pipeline/template/src/enrichment_viz_utils.R`
2. Add roxygen2 documentation
3. Export functions in NAMESPACE
4. Add to Imports in DESCRIPTION: `enrichplot` (move from Suggests)
5. Create tests in `prophosqua/tests/testthat/test-enrichment_visualization.R`

**Functions to add:**
```r
#' @export
prepare_enrichment_data <- function(data, fdr_col = "FDR", fdr_threshold = 0.1)

#' @export
plot_enrichment_dotplot <- function(data, item_col = "kinase", fdr_col = "FDR",
                                     n_top = 30, title = NULL, subtitle = NULL)

#' @export
plot_enrichment_volcano <- function(data, item_col = "kinase", fdr_col = "FDR",
                                     fdr_threshold = 0.1, label_fdr_threshold = 0.05,
                                     n_labels = 5, title = NULL, subtitle = NULL)

#' @export
plot_enrichment_heatmap <- function(data, item_col = "ID", fdr_col = "p.adjust",
                                     fdr_filter = 0.15, n_top = 25,
                                     item_label_col = NULL, title = NULL)

#' @export
export_gsea_plots_pdf <- function(results, output_file, fdr_threshold = 0.25,
                                   width = 10, height = 6, prefix_pattern = NULL)

#' @export
summarize_enrichment_results <- function(results, fdr_thresholds = c(0.1, 0.05))

#' @export
extract_gsea_results <- function(results)
```

**Tests to add:**
```r
test_that("prepare_enrichment_data adds computed columns", {
  df <- data.frame(NES = c(1, -1, 0.5), FDR = c(0.01, 0.2, 0.05))
  result <- prepare_enrichment_data(df)
  expect_true("neg_log_fdr" %in% names(result))
  expect_true("direction" %in% names(result))
  expect_true("significant" %in% names(result))
})

test_that("extract_gsea_results handles clusterProfiler objects", {
  # Create mock gseaResult object for testing
  ...
})
```

### Phase 2: Add GSEA Rank Preparation Function (HIGH PRIORITY)

**Target:** Add to `prophosqua/R/ptmsea.R` or new `prophosqua/R/gsea_utils.R`

**Function:**
```r
#' Prepare ranked lists for GSEA analysis
#'
#' Creates named numeric vectors suitable for clusterProfiler::GSEA from
#' phosphoproteomics data with multiple contrasts.
#'
#' @param data Data frame with phosphosite data
#' @param stat_col Column name for ranking statistic (e.g., "statistic.site")
#' @param seq_col Column name for sequence windows (default: "SequenceWindow")
#' @param contrast_col Column name for contrasts (default: "contrast")
#' @param to_uppercase Convert sequences to uppercase (default: TRUE)
#' @param add_suffix Suffix to add to sequences (default: NULL, use "-p" for PTMsigDB)
#' @return Named list of named numeric vectors, one per contrast
#' @export
prepare_gsea_ranks <- function(data, stat_col, seq_col = "SequenceWindow",
                                contrast_col = "contrast", to_uppercase = TRUE,
                                add_suffix = NULL) {
  contrasts <- unique(data[[contrast_col]])

  purrr::set_names(contrasts) |>
    purrr::map(function(ct) {
      ct_data <- data[data[[contrast_col]] == ct, ]

      seqs <- ct_data[[seq_col]]
      if (to_uppercase) seqs <- toupper(trimws(seqs))
      if (!is.null(add_suffix)) seqs <- paste0(seqs, add_suffix)

      stats <- ct_data[[stat_col]]
      names(stats) <- seqs

      # Remove NA and duplicates
      stats <- stats[!is.na(stats) & !is.na(names(stats))]
      stats <- stats[!duplicated(names(stats))]

      sort(stats, decreasing = TRUE)
    })
}
```

**This replaces duplicated patterns in:**
- `prophosqua/vignettes/Analysis_KinaseLibrary.Rmd:129-141`
- `ptm-pipeline/template/src/Analysis_KinaseLibrary_GSEA.Rmd`
- `ptm-pipeline/template/src/prep_kinaselib.R`

### Phase 3: Add Feature Preparation Functions (MEDIUM PRIORITY)

**Target:** Create `prophosqua/R/feature_preparation.R`

**Functions to add:**
```r
#' Filter significant PTM sites
#'
#' @param data Data frame with PTM results
#' @param fdr_col FDR column name
#' @param diff_col Fold change column name
#' @param fdr_threshold FDR cutoff (default: 0.05)
#' @param fc_threshold Absolute log2FC cutoff (default: 0.6)
#' @return Filtered data with 'regulation' column added
#' @export
filter_significant_sites <- function(data, fdr_col = "FDR.site",
                                      diff_col = "diff.site",
                                      fdr_threshold = 0.05,
                                      fc_threshold = 0.6) {
  data |>
    dplyr::filter(
      .data[[fdr_col]] < fdr_threshold,
      abs(.data[[diff_col]]) > fc_threshold
    ) |>
    dplyr::mutate(
      regulation = dplyr::case_when(
        .data[[diff_col]] > 0 ~ "upregulated",
        .data[[diff_col]] < 0 ~ "downregulated",
        TRUE ~ "no_change"
      )
    )
}

#' Get analysis type configuration
#'
#' Returns column mappings for DPA, DPU, or CF analysis types.
#'
#' @param analysis_type One of "dpa", "dpu", or "cf"
#' @return Named list with sheet, stat_col, diff_col, fdr_col, flanking_col
#' @export
get_analysis_config <- function(analysis_type) {
  configs <- list(
    dpa = list(
      sheet = "combinedSiteProteinData",
      stat_col = "statistic.site",
      diff_col = "diff.site",
      fdr_col = "FDR.site",
      flanking_col = "SequenceWindow"
    ),
    dpu = list(
      sheet = "combinedStats",
      stat_col = "tstatistic_I",
      diff_col = "diff_diff",
      fdr_col = "FDR_I",
      flanking_col = "SequenceWindow"
    ),
    cf = list(
      sheet = "results",
      stat_col = "statistic",
      diff_col = "diff_diff",
      fdr_col = "FDR",
      flanking_col = "SequenceWindow"
    )
  )

  analysis_type <- tolower(analysis_type)
  if (!analysis_type %in% names(configs)) {
    stop("Unknown analysis type: ", analysis_type)
  }
  configs[[analysis_type]]
}
```

### Phase 4: Create Parametrizable Vignette Templates (MEDIUM PRIORITY)

**Goal:** Single source vignettes that work in both contexts:
1. **Vignette mode:** Run with package example data, defaults
2. **Pipeline mode:** Run with external parameters (paths, thresholds)

**Strategy:** Use params in YAML header with sensible defaults

**Example: Analysis_KinaseLibrary.Rmd transformation:**

```yaml
---
title: "Kinase Library GSEA Analysis"
params:
  # Data source: "example" uses package data, otherwise path to RDS/xlsx
  data_source: "example"
  data_path: NULL
  data_sheet: "combinedSiteProteinData"

  # Analysis configuration
  analysis_type: "dpa"  # dpa, dpu, or cf

  # Kinase Library source: "package" or path to term2gene.csv
  term2gene_source: "package"
  term2gene_path: NULL

  # GSEA parameters
  min_gs_size: 15
  max_gs_size: 5000
  pvalue_cutoff: 0.25

  # Output
  output_dir: "."
  export_pdf: true

output:
  html_document:
    toc: true
    toc_float: true
    code_folding: hide
---
```

```{r load_data}
library(prophosqua)

# Load data based on source
if (params$data_source == "example") {
  data("combined_test_diff_example", package = "prophosqua")
  analysis_data <- combined_test_diff_example
} else {
  # Load from external file
  if (grepl("\\.xlsx$", params$data_path)) {
    analysis_data <- readxl::read_xlsx(params$data_path, sheet = params$data_sheet)
  } else {
    analysis_data <- readRDS(params$data_path)
  }
}

# Get column configuration
config <- get_analysis_config(params$analysis_type)
```

**Vignettes to refactor:**
| Vignette | Package Data | Pipeline Params |
|----------|--------------|-----------------|
| Analysis_PTMSEA.Rmd | combined_test_diff_example | ptm_config.yaml paths |
| Analysis_KinaseLibrary.Rmd | combined_test_diff_example + bundled term2gene | external term2gene.csv |
| Vis_MEA.Rmd | Bundled MEA results | KinaseLib/mea_*.csv |

### Phase 5: Update PTM-Pipeline Templates (MEDIUM PRIORITY)

After prophosqua is updated, simplify ptm-pipeline templates:

**Before (Analysis_KinaseLibrary_GSEA.Rmd):**
```r
source("src/enrichment_viz_utils.R")
source("src/feature_preparation.R")

# Inline rank preparation code...
# Inline visualization code...
```

**After:**
```r
library(prophosqua)

# Use package functions
ranks <- prepare_gsea_ranks(data, config$stat_col)
results <- run_motif_gsea(ranks, term2gene_df)
results_df <- extract_gsea_results(results)

# Use package visualization
plot_enrichment_dotplot(results_df, item_col = "ID")
plot_enrichment_volcano(results_df, item_col = "ID")
export_gsea_plots_pdf(results, output_file)
```

**Files to update:**
- [ ] `Analysis_PTMSEA.Rmd` - Use prophosqua visualization functions
- [ ] `Analysis_KinaseLibrary_GSEA.Rmd` - Use prophosqua functions
- [ ] `Analysis_MEA.Rmd` - Use prophosqua visualization functions
- [ ] Remove or minimize `enrichment_viz_utils.R` (after prophosqua update)
- [ ] Remove or minimize `feature_preparation.R` (after prophosqua update)

### Phase 6: Add Tests to Prophosqua (LOW PRIORITY)

**Test files to create:**

`tests/testthat/test-enrichment_visualization.R`:
```r
test_that("prepare_enrichment_data works", {...})
test_that("plot_enrichment_dotplot creates ggplot", {...})
test_that("plot_enrichment_volcano creates ggplot", {...})
test_that("extract_gsea_results handles empty results", {...})
```

`tests/testthat/test-feature_preparation.R`:
```r
test_that("filter_significant_sites filters correctly", {...})
test_that("get_analysis_config returns valid configs", {...})
```

`tests/testthat/test-gsea_utils.R`:
```r
test_that("prepare_gsea_ranks creates sorted named vectors", {...})
test_that("prepare_gsea_ranks handles duplicates", {...})
test_that("prepare_gsea_ranks adds suffix correctly", {...})
```

---

## Implementation Order

| Phase | Priority | Effort | Dependencies | Description |
|-------|----------|--------|--------------|-------------|
| 1 | HIGH | 2-3h | None | Move visualization functions to prophosqua |
| 2 | HIGH | 1h | None | Add prepare_gsea_ranks() function |
| 3 | MEDIUM | 1-2h | None | Add feature preparation functions |
| 4 | MEDIUM | 3-4h | Phases 1-3 | Parametrize prophosqua vignettes |
| 5 | MEDIUM | 2-3h | Phases 1-4 | Update ptm-pipeline templates |
| 6 | LOW | 2h | Phases 1-3 | Add comprehensive tests |

**Total estimated effort:** 11-15 hours

---

## Verification Plan

After each phase, verify:

1. **Prophosqua package builds and passes checks:**
```bash
cd ~/projects/prophosqua
R CMD build .
R CMD check prophosqua_*.tar.gz
```

2. **Vignettes render correctly:**
```r
devtools::build_vignettes()
```

3. **PTM-pipeline still works (after Phase 5):**
```bash
cd ~/projects/ptm-pipeline/test_data/p40060_DanielGao
snakemake -s Snakefile --configfile ptm_config.yaml -j1 all
# Compare outputs with reference
```

---

## Files Summary

### Files to ADD to prophosqua:
- [ ] `R/enrichment_visualization.R` (new)
- [ ] `R/gsea_utils.R` (new, or add to ptmsea.R)
- [ ] `R/feature_preparation.R` (new)
- [ ] `tests/testthat/test-enrichment_visualization.R`
- [ ] `tests/testthat/test-gsea_utils.R`
- [ ] `tests/testthat/test-feature_preparation.R`

### Files to MODIFY in prophosqua:
- [ ] `DESCRIPTION` - Add enrichplot to Imports
- [ ] `NAMESPACE` - Add exports (via roxygen)
- [ ] `vignettes/Analysis_PTMSEA.Rmd` - Add params header
- [ ] `vignettes/Analysis_KinaseLibrary.Rmd` - Add params header
- [ ] `vignettes/Vis_MEA.Rmd` - Add params header

### Files to MODIFY in ptm-pipeline (after prophosqua update):
- [ ] `template/src/enrichment_viz_utils.R` - Remove or thin wrapper
- [ ] `template/src/feature_preparation.R` - Remove or thin wrapper
- [ ] `template/src/Analysis_PTMSEA.Rmd` - Use prophosqua functions
- [ ] `template/src/Analysis_KinaseLibrary_GSEA.Rmd` - Use prophosqua functions
- [ ] `template/src/Analysis_MEA.Rmd` - Use prophosqua functions

---

## Benefits

1. **Single source of truth** - Functions maintained in one place
2. **Better testing** - Package functions can have unit tests
3. **Documentation** - roxygen2 provides consistent documentation
4. **Reusability** - Users can use visualization functions directly
5. **Reduced maintenance** - Bug fixes apply to both projects
6. **Cleaner pipeline** - Templates become thin wrappers around package functions

---

*Created: 2026-01-26*
*Author: Claude Code analysis*
