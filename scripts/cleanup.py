#!/usr/bin/env python3
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_files(days_old=30):
    cutoff_date = datetime.now() - timedelta(days=days_old)
    removed_count = 0
    freed_space = 0
    
    cleanup_dirs = ['tailored_resumes', 'cover_letters', 'applications', 'logs']
    
    print(f"🧹 Cleaning files older than {days_old} days...")
    
    for dir_path in cleanup_dirs:
        if not os.path.exists(dir_path):
            continue
            
        for file_path in Path(dir_path).rglob('*'):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_time < cutoff_date:
                    file_size = file_path.stat().st_size
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        freed_space += file_size
                        print(f"🗑️  Removed: {file_path}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
    
    freed_mb = freed_space / (1024 * 1024)
    print(f"\n✅ Removed {removed_count} files")
    print(f"💾 Freed {freed_mb:.2f} MB")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()
    cleanup_old_files(args.days)
