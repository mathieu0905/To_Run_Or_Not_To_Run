#!/usr/bin/env python3
"""
下载并保存 SWE-bench 数据集到本地
"""
from datasets import load_dataset
from pathlib import Path
import json

# 数据集保存目录
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("开始下载数据集...")

# 下载 SWE-bench Lite
print("\n1. 下载 SWE-bench Lite...")
lite_dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
print(f"   ✓ 已加载 {len(lite_dataset)} 个实例")

# 保存为 JSON
lite_path = DATA_DIR / "swe_bench_lite.json"
with open(lite_path, 'w', encoding='utf-8') as f:
    json.dump([dict(item) for item in lite_dataset], f, indent=2, ensure_ascii=False)
print(f"   ✓ 已保存到: {lite_path}")

# 下载 SWE-bench Verified
print("\n2. 下载 SWE-bench Verified...")
verified_dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
print(f"   ✓ 已加载 {len(verified_dataset)} 个实例")

# 保存为 JSON
verified_path = DATA_DIR / "swe_bench_verified.json"
with open(verified_path, 'w', encoding='utf-8') as f:
    json.dump([dict(item) for item in verified_dataset], f, indent=2, ensure_ascii=False)
print(f"   ✓ 已保存到: {verified_path}")

print("\n✅ 所有数据集已保存到本地！")
print(f"\n数据集位置: {DATA_DIR}")
print(f"  - SWE-bench Lite: {lite_path.name} ({len(lite_dataset)} 个实例)")
print(f"  - SWE-bench Verified: {verified_path.name} ({len(verified_dataset)} 个实例)")
