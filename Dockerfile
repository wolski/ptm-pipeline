# Dockerfile for PTM Pipeline CI
# Based on Bioconductor with R 4.5 + all required R/Python packages
#
# Build:
#   docker build -t ptm-pipeline-ci .
#
# Run tests:
#   docker run --rm -v $(pwd):/work -w /work ptm-pipeline-ci \
#     bash -c "cd test_data/PTM_example_FP_TMT && snakemake -s Snakefile --configfile ptm_config.yaml -j1 all"

FROM bioconductor/bioconductor_docker:RELEASE_3_21

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    curl \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# R packages from CRAN
RUN R -e "install.packages(c( \
    'tidyverse', 'readxl', 'writexl', 'arrow', \
    'ggseqlogo', 'seqinr', 'patchwork', 'remotes', \
    'bookdown', 'rmarkdown', 'DT', 'optparse', 'here' \
), repos='https://cloud.r-project.org/')"

# R packages from Bioconductor (needed by prolfquapp + pipeline scripts)
RUN R -e "BiocManager::install(c( \
    'SummarizedExperiment', 'vsn', \
    'clusterProfiler', 'fgsea', 'enrichplot' \
), ask=FALSE, update=FALSE)"

# R packages from GitHub (dependencies=TRUE to pull remaining CRAN deps)
RUN R -e "remotes::install_github('fgcz/prolfqua', dependencies=TRUE, upgrade='never')"
RUN R -e "remotes::install_github('prolfqua/prolfquapp', dependencies=TRUE, upgrade='never')"
RUN R -e "remotes::install_github('prolfqua/prophosqua', dependencies=TRUE, upgrade='never')"

# Verify critical packages are loadable
RUN R -e "library(prolfqua); library(prolfquapp); library(prophosqua); message('All R packages OK')"

# Python: install snakemake, kinase-library, and ptm-pipeline via uv
RUN uv tool install snakemake
RUN uv tool install "kinase-library @ git+https://github.com/wolski/kinase-library"
RUN uv tool install "ptm-pipeline @ git+https://github.com/wolski/ptm-pipeline"
# NOTE: CI overrides ptm-pipeline with the current checkout via uv tool install --force .

# Set work directory
WORKDIR /work
