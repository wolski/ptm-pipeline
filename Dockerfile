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
    'bookdown', 'rmarkdown' \
), repos='https://cloud.r-project.org/')"

# R packages from Bioconductor
RUN R -e "BiocManager::install(c('clusterProfiler', 'fgsea', 'enrichplot'), ask=FALSE, update=FALSE)"

# R packages from GitHub
RUN R -e "remotes::install_github('fgcz/prolfqua', upgrade='never')"
RUN R -e "remotes::install_github('prolfqua/prolfquapp', upgrade='never')"
RUN R -e "remotes::install_github('prolfqua/prophosqua', upgrade='never')"

# Python: install snakemake and kinase-library globally via uv
RUN uv tool install snakemake
RUN uv tool install "kinase-library @ git+https://github.com/wolski/kinase-library"

# Set work directory
WORKDIR /work
