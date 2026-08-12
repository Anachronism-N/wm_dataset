#!/bin/bash
# ============================================================================
# Qwen3-VL-235B-A22B-Instruct-FP8 vLLM Deployment (single node, 8 GPUs)
#
# Model:  Qwen3-VL-235B-A22B-Instruct-FP8 (~282GB, MoE 235B total / 22B active)
# GPU:    8× H20-96GB (TP=8, single replica)
# Source: https://recipes.vllm.ai/Qwen/Qwen3-VL-235B-A22B-Instruct
#
# Usage:
#   bash deploy_qwen3vl.sh           # foreground
#   nohup bash deploy_qwen3vl.sh > /tmp/vllm_qwen3vl.log 2>&1 &  # background
#
# Health check:
#   curl http://localhost:8000/health
# ============================================================================

set -euo pipefail

MODEL="/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/models/Qwen3-VL-235B-A22B-Instruct-FP8"
TP_SIZE=8
HOST=0.0.0.0
PORT=8000

# --- GPU 占卡管理 ---
# 启动 vLLM 前先停止本机占卡，释放 GPU；vLLM 退出后恢复占卡。
OCCUPIER="/apdcephfs_gy4/share_302533218/cedricnie/gpu_occupier.py"
GUARD_PATTERN="gpu_guard_25min.sh|gpu_occupier|occupy_all_gpu"
DISABLE_MARKER="/apdcephfs_gy4/share_302533218/cedricnie/.gpu_occupy_disabled"

stop_occupy() {
    echo "[deploy] 停止本机 GPU 占卡..."
    pkill -f "${GUARD_PATTERN}" 2>/dev/null || true
    sleep 3
    # 清理 GPU 上残留的占卡子进程
    for dev in /dev/nvidia*; do
        for pid in $(fuser "$dev" 2>/dev/null); do
            kill -9 "$pid" 2>/dev/null || true
        done
    done 2>/dev/null
    sleep 2
    echo "[deploy] 占卡已停止"
}

start_occupy() {
    echo "[deploy] 恢复 GPU 占卡..."
    rm -f "${DISABLE_MARKER}"
    nohup /root/.venv/bin/python "${OCCUPIER}" > /tmp/gpu_occupy_local.log 2>&1 &
    disown
    nohup bash /apdcephfs_gy4/share_302533218/cedricnie/gpu_guard_25min.sh > /tmp/gpu_guard_local.log 2>&1 &
    disown
    echo "[deploy] 占卡已恢复"
}

# 退出时恢复占卡
trap start_occupy EXIT

# 启动前停止占卡
stop_occupy

# Sanity: model dir must exist
if [ ! -d "${MODEL}" ]; then
    echo "ERROR: model not found at ${MODEL}"
    echo "Download it first:"
    echo "  python3 -c \"from modelscope.hub.snapshot_download import snapshot_download as s; s('Qwen/Qwen3-VL-235B-A22B-Instruct-FP8', local_dir='${MODEL}')\""
    exit 1
fi

# Sanity: all 8 GPUs visible
NGPU=$(nvidia-smi --query-gpu=index --format=csv,noheader | wc -l)
if [ "${NGPU}" -lt 8 ]; then
    echo "ERROR: need 8 GPUs, found ${NGPU}"
    exit 1
fi

echo "============================================"
echo "  Qwen3-VL-235B-A22B-Instruct-FP8 vLLM"
echo "  Model:  ${MODEL}"
echo "  TP:     ${TP_SIZE} (single replica, all 8 GPUs)"
echo "  Port:   ${PORT}"
echo "============================================"

# Single replica, TP=8 across all GPUs.
# Flags per official vLLM recipe for H100/H200 (also valid for H20-96GB):
#   --mm-encoder-tp-mode data   : vision encoder data-parallel (better perf)
#   --enable-expert-parallel    : MoE expert parallelism
#   --async-scheduling          : overlap scheduling with decoding
# Note: --enforce-eager is INCOMPATIBLE with --async-scheduling (needs CUDA graphs)
# VLLM_HOST_IP=127.0.0.1 forces workers to connect to engine core via localhost
# (required when get_ip() returns an external IP not bound to a local interface,
#  which causes shm_broadcast "cancelled" errors on some nodes)
VLLM_HOST_IP=127.0.0.1 \
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 exec vllm serve "${MODEL}" \
    --tensor-parallel-size ${TP_SIZE} \
    --host ${HOST} --port ${PORT} \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 \
    --mm-encoder-tp-mode data \
    --enable-expert-parallel \
    --async-scheduling \
    --trust-remote-code
