#!/usr/bin/env python3
"""Master processing pipeline for Wan2.2 training data.
Processes MIRA, OpenVidHD, H2O, DexYCB in background with checkpointing."""

import imageio_ffmpeg, subprocess, os, tarfile, json, glob, zipfile, time
from pathlib import Path

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
TARGET_W, TARGET_H, TARGET_FPS = 1280, 704, 24
BASE = "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset"
WAN22_DIR = f"{BASE}/dataset/wan22_training"

def process_mira():
    """Process MIRA Rocket Science tars -> Wan2.2 MP4."""
    out_dir = f"{WAN22_DIR}/mira_processed"
    os.makedirs(out_dir, exist_ok=True)
    
    tar_files = sorted(glob.glob(f'{BASE}/dataset/general_action/mira_rocket/train/*/*.tar'))
    manifest_path = f"{out_dir}/manifest.jsonl"
    
    # Checkpoint: count already done
    done = len(glob.glob(f"{out_dir}/*.mp4"))
    print(f"MIRA: {done} already converted, {len(tar_files)} tars total")
    
    total = converted = 0
    for tar_path in tar_files:
        try:
            with tarfile.open(tar_path, 'r') as tar:
                mp4s = [m for m in tar.getmembers() if m.name.endswith('.mp4')]
                if not mp4s: continue
                
                for m in mp4s:
                    oname = f"{m.name.replace('/','_').replace('.mp4','')}_720p.mp4"
                    opath = os.path.join(out_dir, oname)
                    if os.path.exists(opath):
                        converted += 1; total += 1; continue
                    
                    tar.extract(m, path='/tmp/wan22_proc')
                    tmp = f'/tmp/wan22_proc/{m.name}'
                    cmd = [FFMPEG, '-y', '-i', tmp, '-vf', 
                           f'scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2',
                           '-r', str(TARGET_FPS), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '26', '-an', opath]
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if r.returncode == 0: converted += 1
                    total += 1
                    if os.path.exists(tmp):
                        try: os.remove(tmp)
                        except: pass
        except KeyboardInterrupt: break
        except Exception as e: continue
        
        if total % 2000 == 0:
            print(f"  MIRA: {total} processed, {converted} converted ({converted/max(total,1)*100:.1f}%)")
            # Save checkpoint
            with open(manifest_path, 'w') as f:
                for mp4 in glob.glob(f"{out_dir}/*.mp4"):
                    f.write(json.dumps({"video_path": mp4, "source": "mira"}) + '\n')
    
    print(f"MIRA complete: {converted} converted out of {total}")
    return converted

def process_openvidhd():
    """Process OpenVidHD zips -> Wan2.2 MP4."""
    out_dir = f"{WAN22_DIR}/openvidhd_processed"
    os.makedirs(out_dir, exist_ok=True)
    
    zips = sorted(glob.glob(f'{BASE}/dataset/general_video/openvidhd/OpenVidHD/*.zip'))
    done = len(glob.glob(f"{out_dir}/*.mp4"))
    print(f"OpenVidHD: {done} already, {len(zips)} zips total")
    
    converted = 0
    for zpath in zips:
        try:
            with zipfile.ZipFile(zpath, 'r') as zf:
                mp4s = [n for n in zf.namelist() if n.endswith('.mp4')]
                for name in mp4s[:100]:  # First 100 per zip for now
                    oname = f"{Path(name).stem}_720p.mp4"
                    opath = os.path.join(out_dir, oname)
                    if os.path.exists(opath): continue
                    
                    zf.extract(name, '/tmp/wan22_proc')
                    tmp = f'/tmp/wan22_proc/{name}'
                    cmd = [FFMPEG, '-y', '-i', tmp, '-vf',
                           f'scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2',
                           '-r', str(TARGET_FPS), '-t', '10', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '26', '-an', opath]
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                    if r.returncode == 0: converted += 1
                    if os.path.exists(tmp):
                        try: os.remove(tmp)
                        except: pass
        except Exception: continue
        if converted % 100 == 0:
            print(f"  OpenVidHD: {converted} converted")
    
    print(f"OpenVidHD: {converted} total converted")
    return converted

def stats():
    """Print final stats."""
    print("\n" + "="*60)
    print("FINAL DATASET STATISTICS")
    print("="*60)
    for d in os.listdir(WAN22_DIR):
        if os.path.isdir(f"{WAN22_DIR}/{d}"):
            mp4s = len(glob.glob(f"{WAN22_DIR}/{d}/*.mp4"))
            size = os.popen(f"du -sh {WAN22_DIR}/{d}").read().strip().split()[0]
            print(f"  {d:25s}: {mp4s:>8,} videos ({size})")
    
    total = sum(len(glob.glob(f"{WAN22_DIR}/{d}/*.mp4")) for d in os.listdir(WAN22_DIR) if os.path.isdir(f"{WAN22_DIR}/{d}"))
    total_size = os.popen(f"du -sh {WAN22_DIR}").read().strip().split()[0]
    print(f"  {'TOTAL':25s}: {total:>8,} videos ({total_size})")
    print("="*60)

def main():
    print("=== Wan2.2 Data Processing Pipeline ===")
    print(f"Target: {WAN22_DIR}")
    print()
    process_mira()
    process_openvidhd()
    stats()

if __name__ == "__main__":
    main()
