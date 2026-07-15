#!/usr/bin/env python3
"""Process H2O, DexYCB, OpenVidHD, EPIC for Wan2.2 training format."""
import imageio_ffmpeg, subprocess, os, glob, shutil, zipfile, sys
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1280, 704, 24
BASE = "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset"
WAN22 = f"{BASE}/wan22_training"

def ffmpeg_convert(input_path, output_path, is_image_seq=False, fps=30):
    """Convert video/images to Wan2.2 format."""
    if is_image_seq:
        cmd = [FFMPEG, '-y', '-framerate', str(fps), '-i', input_path,
               '-vf', f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2',
               '-r', str(FPS), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '26', '-an', output_path]
    else:
        cmd = [FFMPEG, '-y', '-i', input_path,
               '-vf', f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2',
               '-r', str(FPS), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '26', '-an', output_path]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode == 0

# 1. H2O
print("--- H2O ---")
out = f"{WAN22}/h2o_processed"; os.makedirs(out, exist_ok=True)
sessions = glob.glob(f"{BASE}/egocentric_interaction/h2o/extracted/subject1/h1/*")
c = 0
for sess in sessions[:50]:
    for cam in glob.glob(f"{sess}/cam*"):
        imgs = sorted(glob.glob(f"{cam}/*.jpg"))
        if len(imgs) < 10: continue
        oname = f"h2o_{os.path.basename(sess)}_{os.path.basename(cam)}.mp4"
        opath = f"{out}/{oname}"
        if os.path.exists(opath): continue
        # Symlink directory for ffmpeg sequence
        td = f"/tmp/_h2o_{os.path.basename(sess)}_{os.path.basename(cam)}"
        shutil.rmtree(td, ignore_errors=True)
        os.makedirs(td, exist_ok=True)
        for j, img in enumerate(imgs): os.symlink(os.path.abspath(img), f"{td}/{j:06d}.jpg")
        if ffmpeg_convert(f"{td}/%06d.jpg", opath, is_image_seq=True): c += 1
        shutil.rmtree(td, ignore_errors=True)
        if c % 10 == 0: print(f"  H2O: {c}")
print(f"H2O: {c} videos")

# 2. DexYCB
print("--- DexYCB ---")
out = f"{WAN22}/dexycb_processed"; os.makedirs(out, exist_ok=True)
c = 0
for subj in glob.glob(f"{BASE}/egocentric_interaction/dexycb/20*subject*")[:3]:
    for sess in glob.glob(f"{subj}/*")[:10]:
        if not os.path.isdir(sess): continue
        for cam in glob.glob(f"{sess}/*")[:2]:
            if not os.path.isdir(cam): continue
            jpgs = sorted(glob.glob(f"{cam}/*.jpg"))
            if len(jpgs) < 10: continue
            oname = f"dexycb_{os.path.basename(subj)}_{os.path.basename(sess)}_{os.path.basename(cam)}.mp4"
            opath = f"{out}/{oname}"
            if os.path.exists(opath): continue
            td = f"/tmp/_dex_{os.path.basename(subj)}_{os.path.basename(sess)}_{os.path.basename(cam)}"
            shutil.rmtree(td, ignore_errors=True)
            os.makedirs(td, exist_ok=True)
            for j, jpg in enumerate(jpgs[:300]): os.symlink(os.path.abspath(jpg), f"{td}/{j:06d}.jpg")
            if ffmpeg_convert(f"{td}/%06d.jpg", opath, is_image_seq=True): c += 1
            shutil.rmtree(td, ignore_errors=True)
            if c % 10 == 0: print(f"  DexYCB: {c}")
print(f"DexYCB: {c} videos")

# 3. OpenVidHD
print("--- OpenVidHD ---")
out = f"{WAN22}/openvidhd_processed"; os.makedirs(out, exist_ok=True)
c = 0
for zp in sorted(glob.glob(f"{BASE}/general_video/openvidhd/OpenVidHD/*.zip"))[:2]:
    print(f"  {os.path.basename(zp)} ({os.path.getsize(zp)/1e9:.1f}GB)")
    with zipfile.ZipFile(zp, 'r') as zf:
        for name in [n for n in zf.namelist() if n.endswith('.mp4')][:500]:
            oname = f"{os.path.splitext(os.path.basename(name))[0]}.mp4"
            opath = f"{out}/{oname}"
            if os.path.exists(opath): continue
            try:
                zf.extract(name, '/tmp/_ov'); tmp = f'/tmp/_ov/{name}'
                if ffmpeg_convert(tmp, opath): c += 1
                if os.path.exists(tmp):
                    try: os.remove(tmp)
                    except: pass
            except: pass
            if c % 100 == 0: print(f"    {c}")
print(f"OpenVidHD: {c} videos")

# 4. EPIC-KITCHENS (already MP4, just convert)
print("--- EPIC ---")
out = f"{WAN22}/epic_processed"; os.makedirs(out, exist_ok=True)
c = 0
for mp4 in glob.glob(f"{BASE}/egocentric_interaction/epic_kitchens/videos/**/*.MP4", recursive=True)[:20]:
    oname = f"{os.path.splitext(os.path.basename(mp4))[0]}.mp4"
    opath = f"{out}/{oname}"
    if os.path.exists(opath): continue
    if ffmpeg_convert(mp4, opath): c += 1
print(f"EPIC: {c} videos")

# Stats
total = 0
for d in os.listdir(WAN22):
    mp4s = len(glob.glob(f"{WAN22}/{d}/*.mp4"))
    sz = os.popen(f"du -sh {WAN22}/{d}").read().strip().split()[0]
    print(f"  {d}: {mp4s} ({sz})")
    total += mp4s
print(f"\nWan2.2 TOTAL: {total} videos")
