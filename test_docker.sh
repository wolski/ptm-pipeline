#!/bin/bash
# Build the Docker image locally and run the integration tests.
# Usage:
#   ./test_docker.sh              # build + test
#   ./test_docker.sh --build      # build only
#   ./test_docker.sh --test       # test only (image must exist)
set -euo pipefail

IMAGE_REPO="ptm-pipeline-ci"
IMAGE_VERSION="local"
IMAGE="${IMAGE_REPO}:${IMAGE_VERSION}"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$REPO_DIR/tests/data"

do_build=true
do_test=true

if [ "${1:-}" = "--build" ]; then do_test=false; fi
if [ "${1:-}" = "--test" ];  then do_build=false; fi

# --- Build ---
if $do_build; then
    echo "=== Building Docker image: $IMAGE ==="
    docker build --platform linux/amd64 -t "$IMAGE" "$REPO_DIR"
    echo ""
    echo "=== Build succeeded ==="
    echo ""
fi

# --- Test ---
if $do_test; then
    echo "=== Running integration tests ==="

    # Unzip test datasets
    echo "--- Unzipping test data ---"
    for z in "$DATA_DIR"/*.zip; do
        echo "  Unzipping $(basename "$z")"
        unzip -qo "$z" -d "$DATA_DIR"
    done

    # Init: loop over unzipped data dirs and call ptm-pipeline.sh
    # Paths must be relative to REPO_DIR since the container mounts $(pwd) as /work
    echo ""
    echo "--- Initializing test projects ---"
    for z in "$DATA_DIR"/*.zip; do
        d="${z%.zip}"
        out="$DATA_DIR/PTM_$(basename "$d")"
        rel_d="${d#$REPO_DIR/}"
        rel_out="${out#$REPO_DIR/}"
        echo "  $rel_d -> $rel_out"
        "$REPO_DIR/ptm-pipeline.sh" \
            --image-repo "$IMAGE_REPO" \
            --image-version "$IMAGE_VERSION" \
            init-default "$rel_d" "$rel_out"
    done

    # Run: loop over PTM_ dirs
    echo ""
    echo "--- Running pipelines ---"
    for dir in "$DATA_DIR"/PTM_*/; do
        rel_dir="${dir#$REPO_DIR/}"
        echo "  Running in $rel_dir"
        "$REPO_DIR/ptm-pipeline.sh" \
            --image-repo "$IMAGE_REPO" \
            --image-version "$IMAGE_VERSION" \
            run "$rel_dir"
    done

    # Verify: check dir_out exists in each PTM_ dir
    echo ""
    echo "--- Verifying outputs ---"
    fail=0
    for dir in "$DATA_DIR"/PTM_*/; do
        out=$(grep "^dir_out:" "$dir/ptm_config.yaml" | awk '{print $2}')
        if [ -d "$dir/$out" ]; then
            echo "  OK: $dir$out"
        else
            echo "  FAIL: $dir$out missing"
            fail=1
        fi
    done

    if [ "$fail" -ne 0 ]; then
        echo ""
        echo "=== Some tests FAILED ==="
        exit 1
    fi

    echo ""
    echo "=== All tests passed ==="
fi
