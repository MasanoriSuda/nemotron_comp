#!/bin/bash
# run_eval.sh — GUI一時停止してeval実行、終わったら自動復帰
# Usage: ssh localhost './run_eval.sh --adapter_dir adapters/v65 --max_samples 3'
set -e

cd /home/msuda/workspace/kaggle/nemotron_comp

echo "Stopping GUI to free VRAM..."
sudo systemctl isolate multi-user.target
sleep 3

echo "Running eval..."
PATH=/usr/local/cuda-12.8/bin:$PATH \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
.venv312/bin/python local_eval.py "$@"
EXIT_CODE=$?

echo "Restoring GUI..."
sudo systemctl isolate graphical.target

exit $EXIT_CODE
