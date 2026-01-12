#!/usr/bin/env Rscript
# Preprocess PTMsigDB: download, merge human+mouse, filter categories
#
# Usage: Rscript prep_ptmsigdb.R --output_dir data/ptmsigdb --keep_categories KINASE,PATH
#
# Categories in PTMsigDB:
#   KINASE-PSP_  : Kinase-substrate relationships (keep by default)
#   PATH-PSP_    : Pathway signatures (keep by default)
#   PERT-PSP_    : Perturbation signatures (remove by default)
#   DISEASE-PSP_ : Disease-associated patterns (remove by default)

library(prophosqua)
library(fgsea)
library(optparse)
library(stringr)

# Parse arguments
option_list <- list(
  make_option("--output_dir", type = "character", default = "data/ptmsigdb",
              help = "Output directory for filtered GMT files"),
  make_option("--keep_categories", type = "character", default = "KINASE,PATH",
              help = "Comma-separated categories to keep (default: KINASE,PATH)"),
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

# Filter by category
keep_cats <- str_split(args$keep_categories, ",")[[1]]
keep_pattern <- paste0("^(", paste(keep_cats, collapse = "|"), ")-")

pathways_filtered <- pathways_merged[str_detect(names(pathways_merged), keep_pattern)]

message(sprintf("Pathways after filtering (keeping %s): %d",
                args$keep_categories, length(pathways_filtered)))

# Report category counts
message("Category breakdown:")
for (cat in c("KINASE", "PATH", "PERT", "DISEASE")) {
  n <- sum(str_detect(names(pathways_merged), paste0("^", cat, "-")))
  kept <- sum(str_detect(names(pathways_filtered), paste0("^", cat, "-")))
  message(sprintf("  %s: %d total, %d kept", cat, n, kept))
}

# Trim flanking sequences
message(sprintf("Trimming flanking sequences to %d-mer...", args$trim_to))
pathways_trimmed <- trim_ptmsigdb_pathways(pathways_filtered, trim_to = as.character(args$trim_to))

# Write filtered GMT
output_file <- file.path(args$output_dir,
                         sprintf("ptmsigdb_filtered_%s_%dmer.gmt",
                                 gsub(",", "_", args$keep_categories),
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
