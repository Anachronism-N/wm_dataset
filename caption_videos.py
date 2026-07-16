#!/usr/bin/env python3
"""
批量视频 Caption 生成脚本 - Qwen3-VL-235B-A22B
通过 vLLM OpenAI-compatible API 调用
支持断点续传、并发请求
"""

import os, json, glob, time, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm

# ===== 配置 =====
API_URLS = [
    "http://localhost:8000/v1/chat/completions",
    "http://localhost:8001/v1/chat/completions",
    # 添加其他节点的 URL...
]
VIDEO_DIRS = [
    "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset/wan22_training/charades_processed",
    "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset/wan22_training/openvidhd_processed",
]
OUTPUT_FILE = "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/captions/qwen3vl_captions.jsonl"
MAX_FRAMES = 8  # 采样帧数
CONCURRENT = 64  # 并发请求数
# ==================

PROMPT = """You are a video captioning expert. Describe the video in natural English in 2-4 sentences. Focus on:
1. What is happening (actions, interactions)
2. Who/what is in the scene (people, objects)
3. The setting/environment
4. Any notable details (camera movement, lighting, mood)

Keep it concise and factual. Do NOT start with "The video shows" - just describe directly."""

def encode_video_base64(video_path, num_frames=MAX_FRAMES):
    """Extract frames and encode as base64 for vLLM."""
    import subprocess, tempfile
    
    # Get video duration
    r = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
        video_path
    ], capture_output=True, text=True)
    dur = 5.0  # default
    try:
        dur = float(json.loads(r.stdout)['format'].get('duration', 5))
    except: pass
    
    # Sample frames evenly
    intervals = [i * dur / (num_frames + 1) for i in range(1, num_frames + 1)]
    frames = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, t in enumerate(intervals):
            out = f"{tmpdir}/frame_{i:03d}.jpg"
            cmd = ['ffmpeg', '-y', '-ss', str(t), '-i', video_path,
                   '-vframes', '1', '-q:v', '2', out]
            subprocess.run(cmd, capture_output=True, timeout=10)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                with open(out, 'rb') as f:
                    frames.append(base64.b64encode(f.read()).decode())
    
    return frames

def call_vlm(frames_base64, video_name, api_urls):
    """Call VLM API for caption."""
    content = []
    for fb64 in frames_base64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{fb64}"}
        })
    content.append({"type": "text", "text": PROMPT})
    
    payload = {
        "model": "Qwen3-VL-235B-A22B-Instruct",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 256,
        "temperature": 0.3,
    }
    
    for url in api_urls:
        try:
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except: continue
    return None

def load_done(output_file):
    """Load already processed video IDs."""
    done = set()
    if os.path.exists(output_file):
        with open(output_file) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["video_path"])
                except: pass
    return done

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    done = load_done(OUTPUT_FILE)
    
    # Collect all videos
    all_videos = []
    for d in VIDEO_DIRS:
        all_videos.extend(sorted(glob.glob(f"{d}/**/*.mp4", recursive=True)))
    
    # Filter done
    todo = [v for v in all_videos if v not in done]
    print(f"Total: {len(all_videos)}, Done: {len(done)}, Todo: {len(todo)}")
    
    if not todo:
        print("All done!")
        return
    
    # Process in parallel
    def process_one(video_path):
        try:
            frames = encode_video_base64(video_path)
            if not frames: return None
            cap = call_vlm(frames, Path(video_path).stem, API_URLS)
            if cap:
                return {"video_path": video_path, "caption": cap}
        except Exception as e:
            print(f"Error {video_path}: {e}")
        return None
    
    with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
        futures = {pool.submit(process_one, v): v for v in todo}
        
        with open(OUTPUT_FILE, 'a') as f:
            for future in tqdm(as_completed(futures), total=len(todo)):
                result = future.result()
                if result:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()
    
    print(f"\nDone! Captions saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
