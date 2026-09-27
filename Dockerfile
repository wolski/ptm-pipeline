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
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# The R packages come through prophosqua: its Imports and Suggests (the
# reports need the suggested ones) and the Remotes of prophosqua and its
# dependencies, which pin prolfqua, prolfquapp, protsea, fgczQuartoTemplate and
# wolski/anndataR to GitHub.
# pak cannot replace itself during an install, and prophosqua's suggested
# devtools needs a newer pak than the base image has, so pak is updated first.
RUN R -e "install.packages('pak'); stopifnot(packageVersion('pak') >= '0.11')"
RUN R -e "pak::pkg_install('github::prolfqua/prophosqua', dependencies = TRUE)"

# prophosqua again with its vignettes built: the reports are installed from
# vignettes/ into doc/.
RUN R -e "install.packages('remotes')" \
 && R -e "remotes::install_github('prolfqua/prophosqua', dependencies=FALSE, build_vignettes=TRUE, upgrade='never')"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
ENV UV_TOOL_DIR=/opt/uv-tools
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV UV_PYTHON=3.12

# Python: install snakemake, kinase-library, and ptm-pipeline via uv
RUN uv tool install snakemake
RUN uv tool install "kinase-library @ git+https://github.com/wolski/kinase-library"
# Cache-bust ARG: pass --build-arg PTM_VERSION=<commit> to force re-install
ARG PTM_VERSION=latest
RUN uv tool install "ptm-pipeline @ git+https://github.com/wolski/ptm-pipeline"

# Verify critical packages are loadable
RUN R -e "library(prolfqua); library(prolfquapp); library(prophosqua); library(clusterProfiler); message('All R packages OK')"

# Clear inherited ENTRYPOINT ["/bin/bash"] so commands run directly
ENTRYPOINT []

WORKDIR /work
