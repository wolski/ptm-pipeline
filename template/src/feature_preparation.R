#' Feature Preparation Utilities
#'
#' Pipeline-specific functions for preparing data across analysis templates.
#' Note: filter_significant_sites() and summarize_significant_sites() are now
#' provided by prophosqua package - use prophosqua::filter_significant_sites()

library(dplyr)

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
      stat_col = "statistic.site",
      diff_col = "diff.site",
      fdr_col = "FDR.site",
      flanking_col = "SequenceWindow"
    ),
    cf = list(
      sheet = "results",
      stat_col = "statistic",
      diff_col = "diff_diff",
      fdr_col = "FDR_I",
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
