#!/bin/bash
# ============================================================================
# Qwen3-VL-235B-A22B vLLM 部署脚本
# 4 节点 × 8 H20 GPU = 32 GPUs
# 每副本: TP=4 (4 GPUs), 总计 8 副本
# ============================================================================

# vLLM serve 命令（在每节点运行，启动 2 副本/节点）
# 注意：需要在所有 4 个节点上分别运行此脚本

MODEL="Qwen/Qwen3-VL-235B-A22B-Instruct"
TP_SIZE=4
HOST=0.0.0.0
PORT=8000

echo "============================================"
echo "  Qwen3-VL-235B-A22B vLLM Deployment"
echo "  Model: ${MODEL}"
echo "  TP: ${TP_SIZE} GPUs per replica"
echo "  2 replicas per node (8 GPUs)"
echo "  Total: 8 replicas across 4 nodes"
echo "============================================"

# 副本 1: GPU 0-3
CUDA_VISIBLE_DEVICES=0,1,2,3 vllm serve ${MODEL} \
    --tensor-parallel-size ${TP_SIZE} \
    --host ${HOST} --port ${PORT} \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 \
    --enforce-eager \
    --trust-remote-code &
echo "Replica 1: GPU 0-3, port 8000, PID $!"

# 副本 2: GPU 4-7
CUDA_VISIBLE_DEVICES=4,5,6,7 vllm serve ${MODEL} \
    --tensor-parallel-size ${TP_SIZE} \
    --host ${HOST} --port 8001 \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 \
    --enforce-eager \
    --trust-remote-code &
echo "Replica 2: GPU 4-7, port 8001, PID $!"

echo ""
echo "Deployment started. Check:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8001/health"
echo ""
echo "On other nodes, run same script with different ports or use Ray:"
echo "  ray start --head (on node 0)"
echo "  ray start --address='node0:6379' (on nodes 1-3)"
echo "  vllm serve ... --tensor-parallel-size 4 --distributed-executor-backend ray"
