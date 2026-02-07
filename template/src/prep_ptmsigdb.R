#!/usr/bin/env Rscript
# Preprocess PTMsigDB: download, merge human+mouse, filter by sub-source
#
# Usage: Rscript prep_ptmsigdb.R --output_dir data/ptmsigdb --keep_sources KINASE-PSP,PATH-NP
#
# Sub-sources in PTMsigDB v2.0.0:
#   KINASE-PSP   : PhosphoSitePlus kinase-substrate (experimental)
#   KINASE-iKiP  : iKiP kinase-substrate (computational)
#   PATH-NP      : NetPath pathways
#   PATH-WP      : WikiPathways
#   PATH-BI      : Broad Institute pathways
#   PERT-PSP     : Perturbation (PSP)
#   PERT-P100-*  : Perturbation (P100 variants)
#   DISEASE-PSP  : Disease associations

library(prophosqua)
library(fgsea)
library(optparse)
library(stringr)

# Parse arguments
option_list <- list(
  make_option("--output_dir", type = "character", default = "data/ptmsigdb",
              help = "Output directory for filtered GMT files"),
  make_option("--keep_sources", type = "character", default = "KINASE-PSP",
              help = "Comma-separated sub-sources to keep (e.g. KINASE-PSP,PATH-NP)"),
  make_option("--trim_to", type = "integer", default = 15,
              help = "Trim flanking sequences to N residues (default: 15)")
)
args <- parse_args(OptionParser(option_list = option_list))

# Create output directory
dir.create(args$output_dir, recursive = TRUE, showWarnings = FALSE)

# Download raw PTMsigDB
message("Downloading PTMsigDB for human and mouse...")
cache_dir <- file.path(args$output_dir, "raw_cache")
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)

gmt_human <- download_ptmsigdb(species = "human", output_dir = cache_dir)
gmt_mouse <- download_ptmsigdb(species = "mouse", output_dir = cache_dir)

pathways_human <- fgsea::gmtPathways(gmt_human)
pathways_mouse <- fgsea::gmtPathways(gmt_mouse)

message(sprintf("Human pathways: %d", length(pathways_human)))
message(sprintf("Mouse pathways: %d", length(pathways_mouse)))

# Merge human + mouse
message("Merging human and mouse pathways...")
all_names <- union(names(pathways_human), names(pathways_mouse))
pathways_merged <- lapply(all_names, function(name) {
  human_sites <- pathways_human[[name]]
  mouse_sites <- pathways_mouse[[name]]
  unique(c(human_sites, mouse_sites))
})
names(pathways_merged) <- all_names

message(sprintf("Total pathways before filtering: %d", length(pathways_merged)))

# Filter by sub-source (e.g. KINASE-PSP, PATH-NP)
keep_sources <- str_split(args$keep_sources, ",")[[1]]
keep_pattern <- paste0("^(", paste(keep_sources, collapse = "|"), ")_")

pathways_filtered <- pathways_merged[str_detect(names(pathways_merged), keep_pattern)]

message(sprintf("Pathways after filtering (keeping %s): %d",
                args$keep_sources, length(pathways_filtered)))

# Report sub-source counts
all_sources <- c("KINASE-PSP", "KINASE-iKiP", "PATH-NP", "PATH-WP", "PATH-BI",
                 "PERT-PSP", "PERT-P100-DIA2", "PERT-P100-PRM", "PERT-P100-DIA",
                 "DISEASE-PSP")
message("Sub-source breakdown:")
for (src in all_sources) {
  n <- sum(str_detect(names(pathways_merged), paste0("^", src, "_")))
  kept <- sum(str_detect(names(pathways_filtered), paste0("^", src, "_")))
  if (n > 0) {
    marker <- if (kept > 0) " *" else ""
    message(sprintf("  %s: %d total, %d kept%s", src, n, kept, marker))
  }
}

# Trim flanking sequences
message(sprintf("Trimming flanking sequences to %d-mer...", args$trim_to))
pathways_trimmed <- trim_ptmsigdb_pathways(pathways_filtered, trim_to = as.character(args$trim_to))

# Write filtered GMT
output_file <- file.path(args$output_dir,
                         sprintf("ptmsigdb_filtered_%s_%dmer.gmt",
                                 gsub(",", "_", args$keep_sources),
                                 args$trim_to))

# Convert to GMT format and write
write_gmt <- function(pathways, file) {
  lines <- sapply(names(pathways), function(name) {
    sites <- pathways[[name]]
    paste(c(name, "NA", sites), collapse = "\t")
  })
  writeLines(lines, file)
}
write_gmt(pathways_trimmed, output_file)

message(sprintf("Wrote filtered GMT to: %s", output_file))

# Also save as RDS for faster loading
rds_file <- sub("\\.gmt$", ".rds", output_file)
saveRDS(pathways_trimmed, rds_file)
message(sprintf("Wrote RDS cache to: %s", rds_file))

message("Done!")
