library(dplyr)

#' Get Excel File from DEA Directory
#'
#' Finds the Excel results file within a DEA directory's Results_WU_* subfolder.
#'
#' @param dea_dir Path to DEA output directory
#' @return Full path to the Excel file
get_dea_xlsx <- function(dea_dir) {
  # Find Results_WU_* subdirectory
  results_dirs <- list.dirs(dea_dir, recursive = FALSE, full.names = TRUE)
  results_dir <- results_dirs[grepl("^Results_WU_", basename(results_dirs))]


  if (length(results_dir) == 0) {
    # Fallback: search in main directory
    results_dir <- dea_dir
  } else {
    results_dir <- results_dir[1]
  }

  # Find xlsx file in directory
  xlsx_files <- list.files(results_dir, pattern = "\\.xlsx$", full.names = TRUE)

  if (length(xlsx_files) == 0) {
    stop("No Excel file found in: ", results_dir)
  }

  # Prefer the one with "DE_" prefix (standard prolfquapp output)
  de_files <- xlsx_files[grepl("^DE_", basename(xlsx_files))]
  if (length(de_files) > 0) {
    message("Using: ", basename(de_files[1]))
    return(de_files[1])
  }

  message("Using: ", basename(xlsx_files[1]))
  return(xlsx_files[1])
}


#' Get File from DEA Directory
#'
#' Generic helper to find files within a DEA directory's Results_WU_* subfolder.
#'
#' @param dea_dir Path to DEA output directory
#' @param filename Filename to find (e.g., "lfqdata_normalized.parquet")
#' @param description Description for error message (e.g., "parquet file")
#' @return Full path to the file
get_dea_file <- function(dea_dir, filename, description = "file") {
  pattern <- file.path(dea_dir, "Results_WU_*", filename)
  matches <- Sys.glob(pattern)
  if (length(matches) == 0) {
    stop("No ", description, " found in: ", dea_dir)
  }
  return(matches[1])
}

#' Get Parquet File from DEA Directory
#' @param dea_dir Path to DEA output directory
#' @return Full path to the parquet file
get_dea_parquet <- function(dea_dir) {
  get_dea_file(dea_dir, "lfqdata_normalized.parquet", "parquet file")
}

#' Get YAML Config from DEA Directory
#' @param dea_dir Path to DEA output directory
#' @return Full path to the yaml file
get_dea_yaml <- function(dea_dir) {
  get_dea_file(dea_dir, "lfqdata.yaml", "yaml file")
}
