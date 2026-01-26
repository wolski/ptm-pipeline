#' Feature Preparation Utilities
#'
#' Shared functions for filtering significant features and preparing data
#' across Analysis_n_to_c.Rmd, Analysis_seqlogo.Rmd, and other analyses.

library(dplyr)

#' Filter significant PTM sites by FDR and fold change
#'
#' @param data Data frame with PTM results
#' @param fdr_col Name of FDR column (default: "FDR.site")
#' @param diff_col Name of fold change column (default: "diff.site")
#' @param fdr_threshold FDR threshold (default: 0.05)
#' @param fc_threshold Absolute log2 fold change threshold (default: 0.6)
#' @param require_sequence If TRUE, filter out rows with invalid SequenceWindow (default: FALSE)
#' @return Filtered data frame with added 'regulation' column
filter_significant_sites <- function(data, fdr_col = "FDR.site", diff_col = "diff.site",
                                      fdr_threshold = 0.05, fc_threshold = 0.6,
                                      require_sequence = FALSE) {
  result <- data |>
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

  if (require_sequence) {
    result <- result |>
      dplyr::filter(
        !is.na(SequenceWindow),
        !grepl("^_", SequenceWindow),
        !grepl("_$", SequenceWindow)
      )
  }

  return(result)
}


#' Prepare data for N-to-C plotting based on analysis type
#'
#' Renames columns to match what prophosqua plotting functions expect.
#'
#' @param data Data frame with standardized column names (diff.site, FDR.site, etc.)
#' @param analysis_type One of "dpa", "dpu", or "cf"
#' @return Data frame with columns renamed for prophosqua functions
prepare_ntoc_data <- function(data, analysis_type) {
  if (analysis_type == "dpa") {
    # DPA: n_to_c_expression_multicontrast expects diff.site, FDR.site, diff.protein
    # Our standardized format already has these column names
    plot_data <- data |>
      dplyr::mutate(
        modelName.site = if ("modelName.site" %in% names(data)) modelName.site else "observed"
      )
  } else {
    # DPU/CF: n_to_c_usage_multicontrast expects diff_diff, FDR_I
    plot_data <- data |>
      dplyr::rename(
        diff_diff = diff.site,
        FDR_I = FDR.site,
        tstatistic_I = statistic.site
      ) |>
      dplyr::mutate(
        modelName.site = "observed",
        modelName.protein = "observed"
      )
  }

  return(plot_data)
}


#' Validate sequence window by checking central residue
#'
#' Ensures the central amino acid (position 8 in 15-mer) matches the modAA column.
#'
#' @param data Data frame with SequenceWindow and modAA columns
#' @param seq_col Name of sequence window column (default: "SequenceWindow")
#' @param mod_col Name of modified amino acid column (default: "modAA")
#' @param window_center Position of central residue (default: 8 for 15-mer)
#' @return Filtered data frame with only validated sequences
validate_sequence_window <- function(data, seq_col = "SequenceWindow",
                                      mod_col = "modAA", window_center = 8) {
  data |>
    dplyr::mutate(
      .central_aa = toupper(substr(.data[[seq_col]], window_center, window_center))
    ) |>
    dplyr::filter(.central_aa == .data[[mod_col]]) |>
    dplyr::select(-.central_aa)
}


#' Get column configuration for analysis type
#'
#' Returns the expected column names for different analysis types.
#'
#' @param analysis_type One of "dpa", "dpu", or "cf"
#' @return Named list with sheet, stat_col, diff_col, fdr_col
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
    stop("Unknown analysis type: ", analysis_type,
         ". Expected one of: ", paste(names(configs), collapse = ", "))
  }

  return(configs[[analysis_type]])
}


#' Generate summary statistics for significant sites
#'
#' @param data Data frame with regulation column (from filter_significant_sites)
#' @param group_cols Columns to group by (default: c("contrast"))
#' @return Summary tibble with counts by group and regulation direction
summarize_significant_sites <- function(data, group_cols = c("contrast")) {
  data |>
    dplyr::group_by(dplyr::across(dplyr::all_of(c(group_cols, "regulation")))) |>
    dplyr::summarize(n = dplyr::n(), .groups = "drop") |>
    tidyr::pivot_wider(
      names_from = regulation,
      values_from = n,
      values_fill = 0
    )
}
