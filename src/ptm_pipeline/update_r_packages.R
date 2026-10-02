# Install the pushed commits of the R packages the pipeline runs. pak and
# remotes skip a package whose installed commit is already the pushed one.
if (!requireNamespace("pak", quietly = TRUE)) {
  stop("ptm-pipeline update needs the R package pak.", call. = FALSE)
}
pak::pkg_install(c("github::fgcz/prolfqua", "github::prolfqua/prolfquapp", "github::prolfqua/protsea"), ask = FALSE)

# prophosqua's reports are its vignettes, installed into doc/. pak does not
# build vignettes, so remotes installs prophosqua; a prophosqua installed
# without them is reinstalled even at the pushed commit.
if (!requireNamespace("remotes", quietly = TRUE)) {
  pak::pkg_install("remotes", ask = FALSE)
}
remotes::install_github(
  "prolfqua/prophosqua",
  build_vignettes = TRUE,
  dependencies = TRUE,
  upgrade = "never",
  force = !nzchar(system.file("doc", "ptm_statistics.qmd", package = "prophosqua"))
)
