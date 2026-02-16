#!/bin/bash
# Run ptm-pipeline commands inside the Docker image.
# - Pulls the image from GHCR if not available locally.
# - Mounts the current directory to /work.
# - All arguments are passed to ptm-pipeline inside the container.
#
# Usage:
#   ./ptm-pipeline.sh init-default DEA_data/ output/
#   ./ptm-pipeline.sh run output/
#   ./ptm-pipeline.sh --help
#
# Options:
#   --image-version VERSION  Image tag (default: latest)
#   --image-repo REPO        Image repository (default: ghcr.io/wolski/ptm-pipeline-ci)

set -euo pipefail

IMAGE_VERSION="0.3.0"
IMAGE_REPO="ghcr.io/wolski/ptm-pipeline-ci"

usage() {
    echo "Usage: $0 [--image-version VERSION] [--image-repo REPO] [ptm-pipeline args...]"
    echo ""
    echo "Runs ptm-pipeline inside the Docker image with the current directory mounted."
    echo ""
    echo "Options:"
    echo "  --image-version   Image tag to use (default: $IMAGE_VERSION)"
    echo "  --image-repo      Image repository (default: $IMAGE_REPO)"
    echo ""
    echo "Examples:"
    echo "  $0 init-default DEA_data/ output/"
    echo "  $0 run output/"
    echo "  $0 run output/ --dry-run"
    echo "  $0 validate output/"
    exit 1
}

if [ "$#" -eq 0 ]; then
    usage
fi

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --image-version)
            IMAGE_VERSION="$2"
            shift 2
            ;;
        --image-repo)
            IMAGE_REPO="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done

CONTAINER_ARGS=("$@")

if command -v podman > /dev/null 2>&1; then
    DOCKER="podman"
else
    DOCKER="docker"
fi

IMAGE="${IMAGE_REPO}:${IMAGE_VERSION}"

if $DOCKER image inspect "$IMAGE" > /dev/null 2>&1; then
    echo "Using local image $IMAGE"
else
    echo "Image $IMAGE not found locally. Pulling..."
    $DOCKER pull "$IMAGE"
fi

if [ -t 0 ]; then
    DOCKER_ARGS="-it"
else
    DOCKER_ARGS="-i"
fi

$DOCKER run --rm $DOCKER_ARGS \
    --user "$(id -u):$(id -g)" \
    --mount "type=bind,source=$(pwd),target=/work" \
    -w /work \
    "$IMAGE" \
    ptm-pipeline "${CONTAINER_ARGS[@]}"
