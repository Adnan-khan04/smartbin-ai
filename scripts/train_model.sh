#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT_DIR/backend/venv/bin/python"
SCRIPT="$ROOT_DIR/ai-model/waste_classifier.py"

DATA_DIR=${1:-"$ROOT_DIR/ai-model/data"}
EPOCHS=${2:-5}
SAVE_PATH=${3:-"$ROOT_DIR/backend/models/waste_classifier.pth"}

echo "Training: data_dir=$DATA_DIR epochs=$EPOCHS save_path=$SAVE_PATH"
"$PYTHON" "$SCRIPT" train --data-dir "$DATA_DIR" --epochs $EPOCHS --model-save-path "$SAVE_PATH"