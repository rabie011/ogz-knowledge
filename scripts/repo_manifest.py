#!/usr/bin/env python3
"""Print a manifest of the repo: file counts per folder, total sizes, etc."""
import os
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).parent.parent

print(f"Repo manifest: {REPO_ROOT}\n")
print(f"{'Folder':<35} {'Files':>8} {'Size (KB)':>12}")
print("-" * 60)

total_files = 0
total_size = 0
counts = []

for entry in sorted(REPO_ROOT.iterdir()):
    if entry.name.startswith('.') or entry.name == 'scripts':
        continue
    if entry.is_dir():
        n_files = sum(1 for _ in entry.rglob("*") if _.is_file())
        size_kb = sum(_.stat().st_size for _ in entry.rglob("*") if _.is_file()) / 1024
        counts.append((entry.name, n_files, size_kb))
        total_files += n_files
        total_size += size_kb
    elif entry.is_file():
        size_kb = entry.stat().st_size / 1024
        counts.append((entry.name, 1, size_kb))
        total_files += 1
        total_size += size_kb

for name, n, sz in counts:
    print(f"{name:<35} {n:>8} {sz:>12.1f}")

print("-" * 60)
print(f"{'TOTAL':<35} {total_files:>8} {total_size:>12.1f}")

# File-type breakdown
extensions = Counter()
for f in REPO_ROOT.rglob("*"):
    if f.is_file() and not str(f).startswith(str(REPO_ROOT / '.git')):
        extensions[f.suffix or '<no-ext>'] += 1

print(f"\nFile type breakdown:")
for ext, count in extensions.most_common():
    print(f"  {ext:<15} {count:>5}")
