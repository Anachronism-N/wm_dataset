#!/usr/bin/env python3
"""VFHQ batch downloader using bypy's internal API with pagination."""

import os
import sys
import time
from bypy import ByPy

bp = ByPy()

VFHQ_REMOTE = "VFHQ"
LOCAL_BASE = "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset/digital_human/vfhq"

def list_paginated(remote_path, page_size=100):
    """List directory with pagination to avoid timeout."""
    items = []
    start = 0
    while True:
        try:
            # Use bypy's internal list with offset
            r = bp.pcs.list_files(remotepath=f"/apps/bypy/{remote_path}", 
                                   start=start, limit=page_size)
            if not r or 'list' not in r:
                break
            batch = r['list']
            items.extend(batch)
            print(f"  Listed {len(items)} items so far...", end='\r')
            if len(batch) < page_size:
                break
            start += page_size
        except Exception as e:
            print(f"\n  List error at offset {start}: {e}")
            time.sleep(5)
            continue
    print(f"\n  Total: {len(items)} items")
    return items

def download_file(remote_path, local_path):
    """Download single file."""
    try:
        bp.pcs.download(
            remotepath=f"/apps/bypy/{remote_path}",
            localpath=local_path
        )
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False

def main():
    os.makedirs(LOCAL_BASE, exist_ok=True)
    
    # List top-level folders
    print("Scanning VFHQ top-level directories...")
    items = list_paginated(VFHQ_REMOTE, page_size=200)
    
    dirs = [i for i in items if i.get('isdir') == 1]
    print(f"Found {len(dirs)} directories to download")
    
    if not dirs:
        print("No directories found. Checking if items are files...")
        files = [i for i in items if i.get('isdir') != 1]
        print(f"Found {len(files)} files at top level")
        if files:
            print("VFHQ structure: files at top level")
            # Download files
            for f in files:
                fname = f['server_filename']
                remote = f"{VFHQ_REMOTE}/{fname}"
                local = os.path.join(LOCAL_BASE, fname)
                if not os.path.exists(local):
                    print(f"  Downloading: {fname}")
                    bp.download(remote, LOCAL_BASE)
        return
    
    # Download each directory
    downloaded = 0
    for d in dirs:
        dname = d['server_filename']
        local_dir = os.path.join(LOCAL_BASE, dname)
        
        if os.path.exists(local_dir) and os.listdir(local_dir):
            downloaded += 1
            continue
        
        os.makedirs(local_dir, exist_ok=True)
        print(f"[{downloaded+1}/{len(dirs)}] Downloading {dname}...")
        
        try:
            bp.syncdown(f"{VFHQ_REMOTE}/{dname}", local_dir)
            downloaded += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            time.sleep(2)
        
        if downloaded % 100 == 0:
            print(f"  Progress: {downloaded}/{len(dirs)}, size: {os.popen(f'du -sh {LOCAL_BASE}').read().strip()}")

    print(f"\nDone! Downloaded {downloaded}/{len(dirs)} directories")
    os.system(f"du -sh {LOCAL_BASE}")

if __name__ == "__main__":
    main()
