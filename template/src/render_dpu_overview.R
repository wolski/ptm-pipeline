#!/usr/bin/env Rscript
#' Render DPU Overview Report
#'
#' This script renders the prophosqua integration overview document
#' for DPU (Differential PTM Usage) results.
#'
#' Usage:
#'   Rscript render_dpu_overview.R <combined_test_diff.rds> <output_dir> [project_id] [work_unit_id]
#'
#' Arguments:
#'   combined_test_diff.rds - RDS file containing combined test diff data
#'   output_dir            - Directory for output HTML
#'   project_id            - Optional project identifier (default: "PTM_analysis")
#'   work_unit_id          - Optional work unit ID (default: "DPU_Integration")

suppressPackageStartupMessages({
  library(prolfquapp)
  library(prophosqua)
})

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop("Usage: Rscript render_dpu_overview.R <combined_test_diff.rds> <output_dir> [project_id] [work_unit_id]")
}

input_rds <- args[1]
output_dir <- args[2]
project_id <- if (length(args) >= 3) args[3] else "PTM_analysis"
work_unit_id <- if (length(args) >= 4) args[4] else "DPU_Integration"

# Validate input
if (!file.exists(input_rds)) {
  stop("Input RDS file not found: ", input_rds)
}

# Create output directory
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Load combined test diff data
message("Loading data from: ", input_rds)
combined_test_diff <- readRDS(input_rds)

# Create DEA config
drumm <- prolfquapp::make_DEA_config_R6(
  PROJECTID = project_id,
  ORDERID = "fgcz_project",
  WORKUNITID = work_unit_id
)

# Copy template from prophosqua
prophosqua::copy_phospho_integration()

# Render the overview document
message("Rendering DPU overview report...")
rmarkdown::render(
  "_Overview_PhosphoAndIntegration_site.Rmd",
  params = list(
    data = combined_test_diff,
    grp = drumm
  ),
  output_format = bookdown::html_document2(
    toc = TRUE,
    toc_float = TRUE
  ),
  envir = new.env(parent = globalenv())
)

# Move output to target location
output_file <- file.path(output_dir, "Result_DPU.html")
file.copy(
  from = "_Overview_PhosphoAndIntegration_site.html",
  to = output_file,
  overwrite = TRUE
)

# Clean up temporary files
unlink("_Overview_PhosphoAndIntegration_site.Rmd")
unlink("_Overview_PhosphoAndIntegration_site.html")

message("DPU overview report saved to: ", output_file)
