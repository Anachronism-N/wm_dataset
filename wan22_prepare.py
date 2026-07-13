#!/usr/bin/env python3
"""
Wan2.2 Training Data Preparation Pipeline
Process downloaded datasets into Wan2.2-compatible format.

Usage:
    python3 wan22_prepare.py --dataset mira --output /path/to/output
    python3 wan22_prepare.py --dataset charades --output /path/to/output
    python3 wan22_prepare.py --dataset all --output /path/to/output
"""

import os
import sys
import json
import tarfile
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Wan2.2 target specs
TARGET_WIDTH = 1280
TARGET_HEIGHT = 704
TARGET_FPS = 24

BASE_DIR = "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset"


def get_video_info(video_path):
    """Get video resolution, fps, duration using ffprobe."""
    cmd = [FFMPEG, '-i', str(video_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = {'width': 0, 'height': 0, 'fps': 0, 'duration': 0, 'codec': ''}
    for line in r.stderr.split('\n'):
        if 'Stream #0:0' in line and 'Video' in line:
            parts = line.split(',')
            for p in parts:
                p = p.strip()
                if 'x' in p and p[0].isdigit():
                    try:
                        w, h = p.split('x')[0], p.split('x')[1].split()[0]
                        info['width'] = int(w)
                        info['height'] = int(h)
                    except:
                        pass
                if 'fps' in p:
                    try:
                        info['fps'] = float(p.split()[0])
                    except:
                        pass
                if p.startswith('h264') or p.startswith('hevc'):
                    info['codec'] = p.split()[0]
        if 'Duration:' in line:
            dur_str = line.split('Duration:')[1].split(',')[0].strip()
            try:
                h, m, s = dur_str.split(':')
                info['duration'] = float(h)*3600 + float(m)*60 + float(s)
            except:
                pass
    return info


def convert_video(input_path, output_path, target_w=TARGET_WIDTH, target_h=TARGET_HEIGHT, target_fps=TARGET_FPS):
    """Convert video to Wan2.2 target format."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    vf_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"
    
    cmd = [
        FFMPEG, '-y',
        '-i', str(input_path),
        '-vf', vf_filter,
        '-r', str(target_fps),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-an',  # Remove audio for video-only training
        str(output_path)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, r.stderr[-200:]
    return True, None


def process_mira_dataset(output_dir):
    """Process MIRA Rocket Science dataset."""
    mira_dir = os.path.join(BASE_DIR, "general_action", "mira_rocket")
    output_dir = os.path.join(output_dir, "mira_processed")
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all tar files
    tar_files = []
    for root, dirs, files in os.walk(mira_dir):
        for f in files:
            if f.endswith('.tar') and 'train' in root:
                tar_files.append(os.path.join(root, f))
    
    print(f"Found {len(tar_files)} tar files in MIRA dataset")
    
    manifest = []
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for tar_path in tar_files:
        try:
            with tarfile.open(tar_path, 'r') as tar:
                members = [m for m in tar.getmembers() if m.name.endswith('.mp4')]
                
                for member in members:
                    # Extract video name
                    video_name = os.path.basename(member.name).replace('.mp4', '')
                    
                    # Output path
                    out_name = f"{video_name}_{TARGET_WIDTH}x{TARGET_HEIGHT}_{TARGET_FPS}fps.mp4"
                    out_path = os.path.join(output_dir, out_name)
                    
                    if os.path.exists(out_path):
                        skipped_count += 1
                        continue
                    
                    # Extract to temp and convert
                    tar.extract(member, path='/tmp/mira_temp')
                    temp_video = os.path.join('/tmp/mira_temp', member.name)
                    
                    success, error = convert_video(temp_video, out_path)
                    
                    if success:
                        info = get_video_info(out_path)
                        manifest.append({
                            "video_path": out_path,
                            "source": "mira_rocket_science",
                            "original": member.name,
                            "resolution": f"{info['width']}x{info['height']}",
                            "fps": info['fps'],
                            "duration_sec": info['duration'],
                            "num_frames": int(info['duration'] * info['fps'])
                        })
                        processed_count += 1
                    else:
                        error_count += 1
                    
                    # Clean up temp
                    os.remove(temp_video) if os.path.exists(temp_video) else None
                    
                    if processed_count % 100 == 0:
                        print(f"  Progress: {processed_count} processed, {skipped_count} skipped, {error_count} errors")
        
        except Exception as e:
            print(f"Error processing {tar_path}: {e}")
    
    # Save manifest
    manifest_path = os.path.join(output_dir, "manifest.jsonl")
    with open(manifest_path, 'w') as f:
        for item in manifest:
            f.write(json.dumps(item) + '\n')
    
    print(f"\nMIRA processing complete:")
    print(f"  Processed: {processed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Manifest: {manifest_path}")
    
    return manifest


def process_charades_dataset(output_dir):
    """Process Charades dataset."""
    charades_dir = os.path.join(BASE_DIR, "egocentric_interaction", "charades", "Charades_v1_480")
    output_dir = os.path.join(output_dir, "charades_processed")
    os.makedirs(output_dir, exist_ok=True)
    
    mp4_files = list(Path(charades_dir).glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 files in Charades dataset")
    
    manifest = []
    processed = 0
    
    for video_path in mp4_files:
        out_name = f"{video_path.stem}_{TARGET_WIDTH}x{TARGET_HEIGHT}_{TARGET_FPS}fps.mp4"
        out_path = os.path.join(output_dir, out_name)
        
        if os.path.exists(out_path):
            processed += 1
            continue
        
        success, _ = convert_video(str(video_path), out_path)
        if success:
            info = get_video_info(out_path)
            manifest.append({
                "video_path": out_path,
                "source": "charades",
                "video_id": video_path.stem,
                "resolution": f"{info['width']}x{info['height']}",
                "fps": info['fps'],
                "duration_sec": info['duration'],
                "num_frames": int(info['duration'] * info['fps'])
            })
        processed += 1
        
        if processed % 500 == 0:
            print(f"  Progress: {processed}/{len(mp4_files)}")
    
    manifest_path = os.path.join(output_dir, "manifest.jsonl")
    with open(manifest_path, 'w') as f:
        for item in manifest:
            f.write(json.dumps(item) + '\n')
    
    print(f"\nCharades processing complete: {len(manifest)} videos")
    return manifest


def generate_stats(manifest_dir):
    """Generate dataset statistics."""
    total_duration = 0
    total_videos = 0
    sources = {}
    
    for f in Path(manifest_dir).rglob("manifest.jsonl"):
        with open(f) as fh:
            for line in fh:
                item = json.loads(line)
                total_duration += item.get('duration_sec', 0)
                total_videos += 1
                src = item.get('source', 'unknown')
                sources[src] = sources.get(src, 0) + 1
    
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    print(f"Total videos: {total_videos}")
    print(f"Total duration: {total_duration/3600:.1f} hours ({total_duration/60:.0f} min)")
    print(f"Average duration: {total_duration/total_videos:.1f}s" if total_videos > 0 else "")
    print("\nPer-source breakdown:")
    for src, count in sorted(sources.items()):
        print(f"  {src}: {count} videos")
    print("="*60)
    
    return {
        "total_videos": total_videos,
        "total_hours": total_duration / 3600,
        "sources": sources
    }


def main():
    parser = argparse.ArgumentParser(description="Wan2.2 Data Preparation")
    parser.add_argument("--dataset", choices=["mira", "charades", "all"], default="all")
    parser.add_argument("--output", default=f"{BASE_DIR}/wan22_training")
    parser.add_argument("--stats-only", action="store_true", help="Only generate stats")
    args = parser.parse_args()
    
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    if args.stats_only:
        generate_stats(output_dir)
        return
    
    if args.dataset in ["mira", "all"]:
        print("\n" + "="*60)
        print("Processing MIRA Rocket Science...")
        print("="*60)
        process_mira_dataset(output_dir)
    
    if args.dataset in ["charades", "all"]:
        print("\n" + "="*60)
        print("Processing Charades...")
        print("="*60)
        process_charades_dataset(output_dir)
    
    generate_stats(output_dir)


if __name__ == "__main__":
    main()
