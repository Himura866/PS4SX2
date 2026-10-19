#!/usr/bin/env python3
"""Backup PS4SX2 memory cards and save states to a mounted USB/HD directory.
Run only when the emulator is closed; does not change the source saves.
Example: python3 tools/backup_saves.py /data/PS4SX2 /mnt/usb0
"""
import argparse
import datetime
import pathlib
import shutil
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_root", type=pathlib.Path, help="PS4SX2 data folder")
    parser.add_argument("destination", type=pathlib.Path, help="mounted USB or HDD directory")
    args = parser.parse_args()
    root = args.data_root.resolve(strict=True)
    dest = args.destination.resolve(strict=True)
    if not root.is_dir() or not dest.is_dir():
        parser.error("Source and destination must be existing directories")
    if dest == root or root in dest.parents or dest in root.parents:
        parser.error("Destination must be a separate drive/directory")
    folders = ["memcards", "savestates"]
    available = [p for p in root.iterdir() if p.is_dir() and p.name.lower() in folders]
    if not available:
        parser.error("No memcards or savestates folder found; check your emulator configuration")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output = dest / "PS4SX2-backups" / stamp
    if output.exists():
        parser.error("Backup destination already exists")
    output.mkdir(parents=True)
    total = 0
    try:
        for folder in available:
            target = output / folder.name
            shutil.copytree(folder, target, symlinks=False)
            for file in folder.rglob("*"):
                if file.is_file() and not file.is_symlink():
                    copied = target / file.relative_to(folder)
                    if copied.stat().st_size != file.stat().st_size:
                        raise IOError("Size mismatch for " + str(file))
                    total += 1
        if total == 0:
            raise IOError("No save files found")
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise
    print(f"Backup complete: {total} files in {output}")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print("Backup failed:", exc, file=sys.stderr)
        sys.exit(1)
