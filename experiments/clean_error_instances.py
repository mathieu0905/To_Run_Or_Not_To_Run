#!/usr/bin/env python3
"""
清理 trace.jsonl 最后一行包含 "is_error":true 的实例，以及没有生成 patch.diff 的实例
"""
import json
import shutil
from pathlib import Path


def check_trace_has_error(trace_file: Path) -> bool:
    """检查 trace.jsonl 文件最后一行是否包含 is_error:true"""
    try:
        with open(trace_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return False

            last_line = lines[-1].strip()
            if not last_line:
                return False

            # 解析最后一行的 JSON
            try:
                data = json.loads(last_line)
                return data.get('is_error', False) is True
            except json.JSONDecodeError:
                return False
    except Exception as e:
        print(f"  警告: 无法读取 {trace_file}: {e}")
        return False


def clean_error_instances(base_dir: str):
    """清理所有包含错误的实例"""
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"目录不存在: {base_dir}")
        return

    total_deleted = 0

    # 遍历所有模式目录 (run_free, run_less_k1, etc.)
    for mode_dir in base_path.iterdir():
        if not mode_dir.is_dir():
            continue

        print(f"\n处理模式: {mode_dir.name}")

        checkpoint_file = mode_dir / "checkpoint.json"
        checkpoint_data = {}

        # 读取 checkpoint.json
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
            except Exception as e:
                print(f"  警告: 无法读取 checkpoint.json: {e}")

        deleted_instances = []

        # 遍历所有实例目录
        for instance_dir in mode_dir.iterdir():
            if not instance_dir.is_dir():
                continue

            instance_id = instance_dir.name
            trace_file = instance_dir / "trace.jsonl"
            patch_file = instance_dir / "patch.diff"

            if not trace_file.exists():
                continue

            # 检查是否有错误或缺少 patch 或 patch 为空
            has_error = check_trace_has_error(trace_file)
            missing_patch = not patch_file.exists()
            empty_patch = patch_file.exists() and patch_file.stat().st_size == 0

            if has_error or missing_patch or empty_patch:
                reason = []
                if has_error:
                    reason.append("trace 错误")
                if missing_patch:
                    reason.append("缺少 patch")
                if empty_patch:
                    reason.append("patch 为空")
                print(f"  删除实例: {instance_id} ({', '.join(reason)})")

                # 删除实例目录
                try:
                    shutil.rmtree(instance_dir)
                    deleted_instances.append(instance_id)
                    total_deleted += 1
                except Exception as e:
                    print(f"    错误: 无法删除目录 {instance_dir}: {e}")

        # 更新 checkpoint.json
        if deleted_instances and checkpoint_data:
            # checkpoint.json 结构: {"completed": ["instance1", "instance2", ...]}
            if "completed" in checkpoint_data:
                original_count = len(checkpoint_data["completed"])
                checkpoint_data["completed"] = [
                    inst for inst in checkpoint_data["completed"]
                    if inst not in deleted_instances
                ]
                removed_count = original_count - len(checkpoint_data["completed"])

                # 写回 checkpoint.json
                try:
                    with open(checkpoint_file, 'w') as f:
                        json.dump(checkpoint_data, f, indent=2)
                    print(f"  已更新 checkpoint.json，从 completed 数组中删除了 {removed_count} 个实例")
                except Exception as e:
                    print(f"  警告: 无法更新 checkpoint.json: {e}")
            else:
                print(f"  警告: checkpoint.json 格式不正确，缺少 'completed' 字段")

    print(f"\n总计删除了 {total_deleted} 个包含错误的实例")


if __name__ == "__main__":
    # 可选的目录列表
    available_dirs = [
        "output/swebenchlite/claude_code",
        "output/swebenchlite/claude_code_glm",
        "output/swebenchlite/codex",
        "output/swebenchverified/claude_code",
        "output/swebenchverified/claude_code_glm",
        "output/swebenchverified/codex",
    ]

    print("=" * 60)
    print("清理 output 目录中的错误实例")
    print("=" * 60)
    print("\n可选的目录：")

    # 显示可选目录
    for i, dir_path in enumerate(available_dirs, 1):
        exists = Path(dir_path).exists()
        status = "✓" if exists else "✗"
        print(f"  {i}. [{status}] {dir_path}")

    # 获取用户输入
    print("\n请输入要清理的目录编号（多个编号用逗号或空格分隔，输入 'all' 清理所有）：")
    user_input = input("> ").strip()

    # 解析用户输入
    selected_dirs = []
    if user_input.lower() == 'all':
        selected_dirs = [d for d in available_dirs if Path(d).exists()]
    else:
        # 支持逗号或空格分隔
        numbers = user_input.replace(',', ' ').split()
        for num_str in numbers:
            try:
                num = int(num_str)
                if 1 <= num <= len(available_dirs):
                    dir_path = available_dirs[num - 1]
                    if Path(dir_path).exists():
                        selected_dirs.append(dir_path)
                    else:
                        print(f"警告: 目录 {dir_path} 不存在，跳过")
                else:
                    print(f"警告: 编号 {num} 超出范围，跳过")
            except ValueError:
                print(f"警告: 无效的输入 '{num_str}'，跳过")

    # 确认清理
    if not selected_dirs:
        print("\n没有选择任何目录，退出")
    else:
        print(f"\n将清理以下 {len(selected_dirs)} 个目录：")
        for dir_path in selected_dirs:
            print(f"  - {dir_path}")

        confirm = input("\n确认清理？(y/N): ").strip().lower()
        if confirm == 'y':
            for dir_path in selected_dirs:
                clean_error_instances(dir_path)
        else:
            print("已取消清理")
