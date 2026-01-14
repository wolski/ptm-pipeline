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


#' Get Parquet File from DEA Directory
#'
#' Finds the normalized parquet file within a DEA directory's Results_WU_* subfolder.
#'
#' @param dea_dir Path to DEA output directory
#' @return Full path to the parquet file
get_dea_parquet <- function(dea_dir) {
  pattern <- file.path(dea_dir, "Results_WU_*", "lfqdata_normalized.parquet")
  matches <- Sys.glob(pattern)
  if (length(matches) == 0) {
    stop("No parquet file found in: ", dea_dir)
  }
  return(matches[1])
}


#' Get YAML Config from DEA Directory
#'
#' Finds the lfqdata.yaml file within a DEA directory's Results_WU_* subfolder.
#'
#' @param dea_dir Path to DEA output directory
#' @return Full path to the yaml file
get_dea_yaml <- function(dea_dir) {
  pattern <- file.path(dea_dir, "Results_WU_*", "lfqdata.yaml")
  matches <- Sys.glob(pattern)
  if (length(matches) == 0) {
    stop("No yaml file found in: ", dea_dir)
  }
  return(matches[1])
}
