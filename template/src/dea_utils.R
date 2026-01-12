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


#' Find Latest DEA Output Directory
#'
#' Searches for DEA output directories matching a workunit_id pattern
#' and returns the path to the most recent one (by date in folder name).
#' Matches pattern: DEA_YYYYMMDD_WU{workunit_id}_vsn
#'
#' @param project_dir Base directory to search in (default: ".")
#' @param workunit_id The workunit identifier (e.g., "total_proteome", "phoshpho")
#' @param pattern Prefix pattern for DEA folders (default: "DEA")
#' @return Full path to the latest matching directory
#' @examples
#' find_latest_dea(".", "total_proteome")
#' find_latest_dea(".", "phoshpho")
find_latest_dea <- function(project_dir = ".", workunit_id, pattern = "DEA") {
  # Find all directories in project_dir
  dirs <- list.dirs(project_dir, recursive = FALSE, full.names = TRUE)

  # Build regex: DEA_YYYYMMDD_WU{workunit_id}_vsn
  regex <- paste0("^", pattern, "_\\d{8}_WU", workunit_id, "_vsn$")
  matches <- dirs[grepl(regex, basename(dirs))]

  if (length(matches) == 0) {
    stop("No DEA output found for workunit_id: ", workunit_id,
         "\nSearched in: ", normalizePath(project_dir),
         "\nPattern: ", regex)
  }

  # Extract dates from folder names
  dates <- gsub(paste0("^", pattern, "_(\\d{8})_.*"), "\\1", basename(matches))

  # Return the one with the newest date
  latest <- matches[which.max(dates)]
  message("Found DEA output: ", basename(latest))
  return(latest)
}


#' Get Path to DEA Excel Results File
#'
#' Finds the latest DEA directory for a workunit and returns the path
#' to the Excel results file within it (in Results_WU_{workunit_id} subfolder).
#'
#' @param project_dir Base directory to search in (default: ".")
#' @param workunit_id The workunit identifier (e.g., "total_proteome", "phoshpho")
#' @param pattern Prefix pattern for DEA folders (default: "DEA")
#' @return Full path to the Excel file
find_latest_dea_xlsx <- function(project_dir = ".", workunit_id, pattern = "DEA") {
  dea_dir <- find_latest_dea(project_dir, workunit_id, pattern)

  # Results are in Results_WU_{workunit_id} subdirectory
  results_dir <- file.path(dea_dir, paste0("Results_WU_", workunit_id))

  if (!dir.exists(results_dir)) {
    # Fallback: search in main directory
    results_dir <- dea_dir
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


#' Find Latest CorrectFirst Output Directory
#'
#' Searches for CorrectFirst output directories matching a workunit_id pattern
#' and returns the path to the most recent one (by date in folder name).
#' Matches pattern: CorrectFirst_YYYYMMDD_{workunit_id}
#'
#' @param project_dir Base directory to search in (default: ".")
#' @param workunit_id The workunit identifier (e.g., "PTM_usage")
#' @return Full path to the latest matching directory
find_latest_correctfirst <- function(project_dir = ".", workunit_id = "PTM_usage") {
  dirs <- list.dirs(project_dir, recursive = FALSE, full.names = TRUE)

  # Build regex: CorrectFirst_YYYYMMDD_{workunit_id}
  regex <- paste0("^CorrectFirst_\\d{8}_", workunit_id, "$")
  matches <- dirs[grepl(regex, basename(dirs))]

  if (length(matches) == 0) {
    stop("No CorrectFirst output found for workunit_id: ", workunit_id,
         "\nSearched in: ", normalizePath(project_dir),
         "\nPattern: ", regex)
  }

  # Extract dates from folder names
  dates <- gsub("^CorrectFirst_(\\d{8})_.*", "\\1", basename(matches))

  # Return the one with the newest date
  latest <- matches[which.max(dates)]
  message("Found CorrectFirst output: ", basename(latest))
  return(latest)
}


#' Get Path to CorrectFirst Excel Results File
#'
#' Finds the latest CorrectFirst directory for a workunit and returns the path
#' to the Excel results file within it.
#'
#' @param project_dir Base directory to search in (default: ".")
#' @param workunit_id The workunit identifier (default: "PTM_usage")
#' @return Full path to the Excel file
find_latest_correctfirst_xlsx <- function(project_dir = ".", workunit_id = "PTM_usage") {
  cf_dir <- find_latest_correctfirst(project_dir, workunit_id)

  # Find xlsx file in directory
  xlsx_files <- list.files(cf_dir, pattern = "\\.xlsx$", full.names = TRUE)

  if (length(xlsx_files) == 0) {
    stop("No Excel file found in: ", cf_dir)
  }

  # Prefer the one with "CorrectFirst_" prefix
  cf_files <- xlsx_files[grepl("^CorrectFirst_", basename(xlsx_files))]
  if (length(cf_files) > 0) {
    message("Using: ", basename(cf_files[1]))
    return(cf_files[1])
  }

  message("Using: ", basename(xlsx_files[1]))
  return(xlsx_files[1])
}


