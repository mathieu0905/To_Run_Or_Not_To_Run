#!/usr/bin/env python3
import json
import os
from pathlib import Path

output_dir = Path("/home/zhihao/hdd/run_free_run_less_run_full/output/swebenchlite/claude_code")
modes = ["run_cost", "run_free", "run_full", "run_less_k1", "run_less_k2", "run_less_k3"]

for mode in modes:
    mode_dir = output_dir / mode
    checkpoint_file = mode_dir / "checkpoint.json"

    # 从头开始构建 checkpoint
    completed_set = set()
    checkpoint = {"completed": []}

    # 遍历所有实例目录
    for instance_dir in mode_dir.iterdir():
        if not instance_dir.is_dir():
            continue

        instance_id = instance_dir.name
        trace_file = instance_dir / "trace.jsonl"

        if not trace_file.exists():
            continue

        # 读取 trace.jsonl 最后一行
        with open(trace_file) as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                try:
                    last_entry = json.loads(last_line)
                    if not last_entry.get("is_error", True):
                        completed_set.add(instance_id)
                except json.JSONDecodeError:
                    pass

    # 更新 checkpoint
    checkpoint["completed"] = sorted(list(completed_set))

    with open(checkpoint_file, "w") as f:
        json.dump(checkpoint, f, indent=2)

    print(f"{mode}: {len(checkpoint['completed'])} 个已完成实例")
