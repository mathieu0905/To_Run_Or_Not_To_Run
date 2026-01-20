#!/usr/bin/env python3
"""
Download and save SWE-bench datasets locally
"""
from datasets import load_dataset
from pathlib import Path
import json

# Dataset save directory
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Starting dataset download...")

# Download SWE-bench Lite
print("\n1. Downloading SWE-bench Lite...")
lite_dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
print(f"   ✓ Loaded {len(lite_dataset)} instances")

# Save as JSON
lite_path = DATA_DIR / "swe_bench_lite.json"
with open(lite_path, 'w', encoding='utf-8') as f:
    json.dump([dict(item) for item in lite_dataset], f, indent=2, ensure_ascii=False)
print(f"   ✓ Saved to: {lite_path}")

# Download SWE-bench Verified
print("\n2. Downloading SWE-bench Verified...")
verified_dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
print(f"   ✓ Loaded {len(verified_dataset)} instances")

# Save as JSON
verified_path = DATA_DIR / "swe_bench_verified.json"
with open(verified_path, 'w', encoding='utf-8') as f:
    json.dump([dict(item) for item in verified_dataset], f, indent=2, ensure_ascii=False)
print(f"   ✓ Saved to: {verified_path}")

print("\n✅ All datasets saved locally!")
print(f"\nDataset location: {DATA_DIR}")
print(f"  - SWE-bench Lite: {lite_path.name} ({len(lite_dataset)} instances)")
print(f"  - SWE-bench Verified: {verified_path.name} ({len(verified_dataset)} instances)")
