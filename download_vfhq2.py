#!/usr/bin/env python3
"""VFHQ downloader using bypy API directly - survives long runs."""

import sys, os, time
sys.path.insert(0, '/usr/local/lib/python3.11/site-packages')
from bypy import ByPy

LOCAL_BASE = "/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset/digital_human/vfhq"

def main():
    os.makedirs(LOCAL_BASE, exist_ok=True)
    bp = ByPy()
    
    print("=== VFHQ Download Started ===")
    print(f"Target: {LOCAL_BASE}")
    print("Phase 1: Scanning directory (this may take 5-30 min for 15K+ folders)...")
    print()
    
    # Use bypy's syncdown which handles recursive sync
    try:
        bp.syncdown(remotedir='VFHQ', localdir=LOCAL_BASE, deletelocal=False)
    except KeyboardInterrupt:
        print("\nInterrupted, progress saved.")
    except Exception as e:
        print(f"Error: {e}")
        print("Will retry...")
        time.sleep(10)
    
    size = os.popen(f'du -sh {LOCAL_BASE}').read().strip()
    file_count = os.popen(f'find {LOCAL_BASE} -type f | wc -l').read().strip()
    print(f"\nDone! Size: {size}, Files: {file_count}")

if __name__ == "__main__":
    main()
