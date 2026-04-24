#!/usr/bin/env bash
# Download HoloMotion v1.2 pretrained ONNX checkpoints from HuggingFace.
#
# Usage:
#   bash scripts/download/download_holomotion_ckpt.sh [MODEL]
#
# Arguments:
#   MODEL  (optional)  one of:
#                        motion      - motion tracking model only
#                        velocity    - velocity tracking model only
#                        all         - both (default)
#
# Environment:
#   HOLOMOTION_CACHE_DIR  target directory, default: $HOME/.cache/genesis/holomotion
#
# Result layout:
#   $HOLOMOTION_CACHE_DIR/
#     holomotion_v1.2_motion_tracking_model/
#       config.yaml
#       exported/*.onnx
#     holomotion_v1.2_velocity_tracking_model/
#       config.yaml
#       exported/*.onnx

set -euo pipefail

DEST_DIR="${HOLOMOTION_CACHE_DIR:-$HOME/.cache/genesis/holomotion}"
MODEL="${1:-all}"

REPO="HorizonRobotics/HoloMotion_v1.2"
MOTION_SUBDIR="holomotion_v1.2_motion_tracking_model"
VELOCITY_SUBDIR="holomotion_v1.2_velocity_tracking_model"

if ! command -v hf >/dev/null 2>&1 && ! command -v huggingface-cli >/dev/null 2>&1; then
    echo "[ERR] huggingface CLI not found. Install: pip install -U huggingface_hub" >&2
    exit 1
fi

HF_BIN=$(command -v hf || command -v huggingface-cli)

mkdir -p "$DEST_DIR"
echo "[INFO] Downloading HoloMotion checkpoints to: $DEST_DIR"
echo "[INFO] Model selection: $MODEL"

download_subdir() {
    local subdir="$1"
    local target="$DEST_DIR/$subdir"
    echo "[INFO] Downloading $REPO : $subdir -> $target"
    # hf v0.35+ uses `hf download`; fallback to legacy syntax otherwise.
    if [[ "$HF_BIN" == *"/hf" ]]; then
        "$HF_BIN" download "$REPO" \
            --include "$subdir/*" \
            --local-dir "$DEST_DIR" \
            --local-dir-use-symlinks False 2>/dev/null || \
        "$HF_BIN" download "$REPO" \
            --include "$subdir/*" \
            --local-dir "$DEST_DIR"
    else
        "$HF_BIN" download "$REPO" \
            --include "$subdir/*" \
            --local-dir "$DEST_DIR"
    fi
}

case "$MODEL" in
    motion)
        download_subdir "$MOTION_SUBDIR"
        ;;
    velocity)
        download_subdir "$VELOCITY_SUBDIR"
        ;;
    all)
        download_subdir "$MOTION_SUBDIR"
        download_subdir "$VELOCITY_SUBDIR"
        ;;
    *)
        echo "[ERR] Unknown MODEL: $MODEL (expected: motion | velocity | all)" >&2
        exit 1
        ;;
esac

echo ""
echo "[DONE] Checkpoints downloaded to: $DEST_DIR"
echo ""
echo "Verify:"
find "$DEST_DIR" -maxdepth 3 -type f \( -name '*.onnx' -o -name 'config.yaml' \) | sort
