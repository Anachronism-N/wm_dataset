# Qwen3-VL-235B-A22B 部署与视频 Caption

> 目标：用最强 VLM 为训练数据打高质量 caption
> 硬件：4 节点 × 8 H20 (96GB) = 32 GPUs
> 创建日期：2026-07-16

---

## 一、模型选择

| 候选 | 参数 | 优势 | 劣势 |
|------|------|------|------|
| **Qwen3-VL-235B-A22B** | 235B MoE (22B active) | Qwen 系列最强 VLM | 需 4GPU/副本 |
| Qwen2.5-VL-72B | 72B dense | 成熟稳定 | 上代架构 |
| Qwen3-VL-32B | 32B dense | 1GPU/副本, 高吞吐 | 质量略低 |

**选择 Qwen3-VL-235B-A22B**：256K context, hours-long video, Interleaved-MRoPE 时序建模。

---

## 二、部署架构

```
4 节点 × 8 H20 GPUs (96GB)
├── 每节点 2 副本 (TP=4, 4 GPU/副本)
├── 端口: 8000, 8001
└── 总计 8 副本并行

推理流程:
  视频 → ffmpeg 采 8 帧 → JPEG → base64 → vLLM API → caption
```

| 参数 | 值 | 说明 |
|------|-----|------|
| TP | 4 | Tensor Parallel |
| max-model-len | 65536 | 上下文长度 |
| gpu-memory | 0.92 | GPU 显存利用率 |
| max-num-seqs | 64 | 最大并发序列 |

---

## 三、部署代码

### deploy_qwen3vl.sh

```bash
#!/bin/bash
# 每节点运行此脚本，启动 2 个 vLLM 副本

MODEL="Qwen/Qwen3-VL-235B-A22B-Instruct"
TP=4

# 副本 1: GPU 0-3
CUDA_VISIBLE_DEVICES=0,1,2,3 vllm serve ${MODEL} \
    --tensor-parallel-size ${TP} --port 8000 \
    --max-model-len 65536 --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 --enforce-eager --trust-remote-code &

# 副本 2: GPU 4-7
CUDA_VISIBLE_DEVICES=4,5,6,7 vllm serve ${MODEL} \
    --tensor-parallel-size ${TP} --port 8001 \
    --max-model-len 65536 --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 --enforce-eager --trust-remote-code &
```

### 多节点配置

在其余 3 个节点上运行相同脚本，使用不同端口或相同端口（节点间不冲突）。

---

## 四、Caption 生成代码

### caption_videos.py

```python
"""
批量视频 Caption - Qwen3-VL-235B-A22B
通过 vLLM OpenAI-compatible API 调用
"""

import os, json, glob, time, base64, subprocess, tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm

# ===== 配置 =====
API_URLS = [
    "http://localhost:8000/v1/chat/completions",
    "http://localhost:8001/v1/chat/completions",
]
VIDEO_DIRS = [
    "dataset/wan22_training/charades_processed",
    "dataset/wan22_training/openvidhd_processed",
]
OUTPUT_FILE = "captions/qwen3vl_captions.jsonl"
MAX_FRAMES = 8
CONCURRENT = 64
# ==================

PROMPT = """You are a video captioning expert. Describe the video in natural English in 2-4 sentences. Focus on:
1. What is happening (actions, interactions)
2. Who/what is in the scene (people, objects)
3. The setting/environment
4. Any notable details

Keep it concise and factual."""

def encode_video_base64(video_path, num_frames=8):
    """采样帧并编码为 base64."""
    r = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', video_path], capture_output=True, text=True)
    dur = 5.0
    try: dur = float(json.loads(r.stdout)['format'].get('duration', 5))
    except: pass

    intervals = [i * dur / (num_frames + 1) for i in range(1, num_frames + 1)]
    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(intervals):
            out = f"{tmp}/frame_{i:03d}.jpg"
            subprocess.run(['ffmpeg', '-y', '-ss', str(t), '-i', video_path,
                           '-vframes', '1', '-q:v', '2', out],
                          capture_output=True, timeout=10)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                with open(out, 'rb') as f:
                    frames.append(base64.b64encode(f.read()).decode())
    return frames

def call_vlm(frames, video_name, api_urls):
    """调用 VLM API."""
    content = []
    for fb64 in frames:
        content.append({"type": "image_url",
                       "image_url": {"url": f"data:image/jpeg;base64,{fb64}"}})
    content.append({"type": "text", "text": PROMPT})

    payload = {
        "model": "Qwen3-VL-235B-A22B-Instruct",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 256, "temperature": 0.3,
    }
    for url in api_urls:
        try:
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except: continue
    return None

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # 断点续传
    done = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            for line in f:
                try: done.add(json.loads(line)["video_path"])
                except: pass

    all_videos = []
    for d in VIDEO_DIRS:
        all_videos.extend(sorted(glob.glob(f"{d}/**/*.mp4", recursive=True)))

    todo = [v for v in all_videos if v not in done]
    print(f"Total: {len(all_videos)}, Done: {len(done)}, Todo: {len(todo)}")

    def process_one(v):
        try:
            frames = encode_video_base64(v)
            if not frames: return None
            cap = call_vlm(frames, Path(v).stem, API_URLS)
            if cap: return {"video_path": v, "caption": cap}
        except: pass
        return None

    with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
        futures = {pool.submit(process_one, v): v for v in todo}
        with open(OUTPUT_FILE, 'a') as f:
            for future in tqdm(as_completed(futures), total=len(todo)):
                result = future.result()
                if result:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()

    print(f"Done! Captions saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
```

---

## 五、Caption Prompt 设计

| 数据集 | Prompt 策略 | 示例 |
|--------|-----------|------|
| OpenVidHD | 通用描述 | "Describe what is happening in this video..." |
| Charades | 居家活动 | "Describe the daily activity happening..." |
| MIRA | 游戏交互 | "Describe the game action from this player's view..." |
| EasyCom | 对话场景 | 已有对话文本，无需打标 |
| HOIGen-1M | 已有 CSV caption | 直接使用，无需打标 |

---

## 六、预期性能

| 指标 | 值 |
|------|-----|
| 每副本吞吐 | ~10-15 videos/min |
| 8 副本总吞吐 | ~80-120 videos/min |
| 每天处理 | ~115K-170K videos |
| 1.9M MIRA 预计 | ~11-17 天 |

---

## 七、数据集 Caption 状态

| 数据集 | 视频数 | Caption 方式 | 状态 |
|--------|--------|-------------|------|
| HOIGen-1M | 1M+ | CSV 自带 | 已就绪 |
| EasyCom | 323 | 对话文本 | 已就绪 |
| MIRA | 1.9M | JSONL→LLM 模板 | 待打标 |
| OpenVidHD | 300K+ | Qwen3-VL | 待打标 |
| Charades | 9,848 | Qwen3-VL | 待打标 |
| DexYCB | 348K img | 先转视频→Qwen3-VL | 待处理 |
| H2O | 183K img | 先转视频→Qwen3-VL | 待处理 |

---

## 八、环境要求

| 组件 | 版本 |
|------|------|
| CUDA | 12.9 |
| PyTorch | 2.6.0 |
| vLLM | 0.8.5 |
| Python | 3.11 |
| GPU | H20 96GB × 32 |
