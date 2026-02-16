# Dockerfile for PTM Pipeline
# Based on prolfquapp which provides R, prolfqua, prolfquapp, and all their deps
#
# Build:
#   docker build -t ptm-pipeline .
#
# Run:
#   docker run --rm -v $(pwd):/work -w /work ptm-pipeline \
#     bash -c "cd test_data/PTM_example_FP_TMT && snakemake -s Snakefile --configfile ptm_config.yaml -j1 all"

FROM docker.io/prolfqua/prolfquapp:2.0.10

# System dev libs needed to compile R packages from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libharfbuzz-dev libfribidi-dev libpng-dev libtiff5-dev libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# R packages (delta — only what prolfquapp doesn't have)
# Install clusterProfiler and other deps first (prophosqua vignettes need them)
RUN R -e "pak::pkg_install(c( \
    'bioc::clusterProfiler', 'bioc::fgsea', 'bioc::enrichplot', \
    'any::ggseqlogo', 'any::patchwork', 'any::DT', 'any::here', 'any::rmarkdown' \
))"

# prophosqua: build_vignettes so Rmd files are available via system.file('doc', ...)
RUN R -e "install.packages('remotes')" \
 && R -e "remotes::install_github('prolfqua/prophosqua', build_vignettes=TRUE, upgrade='never')"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
ENV UV_TOOL_DIR=/opt/uv-tools
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Python: install snakemake, kinase-library, and ptm-pipeline via uv
RUN uv tool install snakemake
RUN uv tool install "kinase-library @ git+https://github.com/wolski/kinase-library"
RUN uv tool install "ptm-pipeline @ git+https://github.com/wolski/ptm-pipeline"

# Verify critical packages are loadable
RUN R -e "library(prolfqua); library(prolfquapp); library(prophosqua); library(clusterProfiler); message('All R packages OK')"

# Clear inherited ENTRYPOINT ["/bin/bash"] so commands run directly
ENTRYPOINT []

WORKDIR /work
