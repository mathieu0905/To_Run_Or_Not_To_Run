#!/usr/bin/env python3
"""
为 sb-cli 生成 SWE-bench predictions JSON。

设计目标（论文式对比，按“同模型同样例”公平比较不同配置）：
- 对每个 dataset × model：
  - 先统计每个配置在 output/ 中“实际评测过”的样例集合（判定标准：trace.jsonl 存在）
  - 若某个配置评测样例数 < min_config_instances（默认 10），则该配置不纳入比较范围
  - 对纳入范围的配置取样例交集，得到 intersection_instances
  - 若交集样例数 < min_intersection_instances（默认 10），则该 dataset × model 不输出任何 predictions
- 对交集样例分别生成每个配置的 predictions JSON（patch.diff 缺失或空则 model_patch 置为空字符串）
- 每次运行默认清空 dest_root 下对应数据集/split 的旧产物，避免旧结果干扰

输出格式遵循 sb-cli 文档（Dictionary Format）：
{
  "<instance_id>": {"model_patch": "...", "model_name_or_path": "..."},
  ...
}
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Set


DATASET_SPECS = {
    "lite": {
        "subset": "swe-bench_lite",
        "output_dirname": "swebenchlite",
        "data_file": "data/swe_bench_lite.json",
        "default_split": "test",
    },
    "verified": {
        "subset": "swe-bench_verified",
        "output_dirname": "swebenchverified",
        "data_file": "data/swe_bench_verified.json",
        "default_split": "test",
    },
}


DEFAULT_AGENTS = ["claude_code", "codex"]
DEFAULT_MODE_DIRS = [
    "run_cost",
    "run_free",
    "run_full",
    "run_less_k1",
    "run_less_k2",
    "run_less_k3",
]


@dataclass(frozen=True)
class Config:
    agent: str
    mode_dir: str

    @property
    def config_id(self) -> str:
        return f"{self.agent}__{self.mode_dir}"


@dataclass
class ConfigStatsInIntersection:
    dataset_subset: str
    agent: str
    mode_dir: str
    intersection_instances: int
    patch_present: int
    patch_missing: int
    patch_empty: int
    missing_patch_instances: List[str]
    empty_patch_instances: List[str]


@dataclass
class AgentGroupSummary:
    dataset_subset: str
    split: str
    agent: str
    mode_dirs_considered: List[str]
    mode_dirs_included: List[str]
    mode_dirs_excluded: Dict[str, str]  # mode_dir -> reason
    counts_by_mode_dir: Dict[str, int]  # evaluated instance count per config
    intersection_size: int
    intersection_instances: List[str]
    files: List[str]
    stats_in_intersection: List[ConfigStatsInIntersection]


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_expected_configs(
    agents: Iterable[str],
    mode_dirs: Iterable[str],
) -> List[Config]:
    configs: List[Config] = []
    for agent in agents:
        for mode_dir in mode_dirs:
            configs.append(Config(agent=agent, mode_dir=mode_dir))
    return configs


def read_patch_text(patch_path: Path) -> Tuple[str, str]:
    """
    Returns:
      (status, patch_text)
      status in {"missing", "empty", "present"}
    """
    if not patch_path.exists():
        return "missing", ""
    text = patch_path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return "empty", ""
    return "present", text


def is_instance_evaluated(instance_dir: Path) -> bool:
    # 你确认的判定标准：trace.jsonl 存在即视为“已评测过”
    return (instance_dir / "trace.jsonl").is_file()


def collect_evaluated_instances(config_dir: Path) -> Set[str]:
    if not config_dir.is_dir():
        return set()
    instances: Set[str] = set()
    for child in config_dir.iterdir():
        if not child.is_dir():
            continue
        if is_instance_evaluated(child):
            instances.add(child.name)
    return instances


def build_predictions_for_config_on_instances(
    *,
    output_root: Path,
    dataset_output_dirname: str,
    dataset_subset: str,
    split: str,
    config: Config,
    instance_ids: List[str],
    strict: bool,
) -> Tuple[Dict[str, Dict[str, str]], ConfigStatsInIntersection]:
    preds: Dict[str, Dict[str, str]] = {}

    missing_instances: List[str] = []
    empty_instances: List[str] = []
    present = 0

    for instance_id in instance_ids:
        patch_path = (
            output_root
            / dataset_output_dirname
            / config.agent
            / config.mode_dir
            / instance_id
            / "patch.diff"
        )

        status, patch_text = read_patch_text(patch_path)
        if status == "missing":
            missing_instances.append(instance_id)
            if strict:
                raise FileNotFoundError(f"缺少 patch.diff：{patch_path}")
        elif status == "empty":
            empty_instances.append(instance_id)
        else:
            present += 1

        # model_name_or_path 按你的要求带上数据集信息，便于区分 lite/verified
        model_name_or_path = f"{dataset_subset}__{split}__{config.agent}__{config.mode_dir}"
        preds[instance_id] = {
            "model_patch": patch_text,
            "model_name_or_path": model_name_or_path,
        }

    stats = ConfigStatsInIntersection(
        dataset_subset=dataset_subset,
        agent=config.agent,
        mode_dir=config.mode_dir,
        intersection_instances=len(instance_ids),
        patch_present=present,
        patch_missing=len(missing_instances),
        patch_empty=len(empty_instances),
        missing_patch_instances=missing_instances,
        empty_patch_instances=empty_instances,
    )
    return preds, stats


def write_json(path: Path, obj: object, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"文件已存在（可用 --overwrite 覆盖）：{path}")
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 output/ 汇总补丁，生成 sb-cli 可提交的 predictions JSON。"
    )
    parser.add_argument(
        "--dataset",
        choices=sorted(list(DATASET_SPECS.keys()) + ["both"]),
        default="both",
        help="数据集：lite / verified / both（默认 both）。",
    )
    parser.add_argument(
        "--split",
        default=None,
        help="sb-cli 的 split（dev/test）。默认取 run 脚本一致的 test。",
    )
    parser.add_argument(
        "--agents",
        default=",".join(DEFAULT_AGENTS),
        help=f"需要整理的 agent 列表（逗号分隔，默认 {','.join(DEFAULT_AGENTS)}）。",
    )
    parser.add_argument(
        "--mode_dirs",
        default=",".join(DEFAULT_MODE_DIRS),
        help="需要考虑的配置目录名（逗号分隔，默认包含 run_cost/run_free/run_full/run_less_k1..k3）。",
    )
    parser.add_argument(
        "--output_root",
        default="output",
        help="实验输出根目录（默认 output）。",
    )
    parser.add_argument(
        "--dest_root",
        default="sbcli_preds",
        help="predictions 输出根目录（默认 sbcli_preds）。",
    )
    parser.add_argument(
        "--min_config_instances",
        type=int,
        default=10,
        help="配置纳入比较的最小样例数阈值（默认 10）。",
    )
    parser.add_argument(
        "--min_intersection_instances",
        type=int,
        default=10,
        help="交集样例数不足则不输出该 dataset×model（默认 10）。",
    )
    parser.add_argument(
        "--no_clean",
        action="store_true",
        help="不清空 dest_root 下对应数据集/split 的旧产物（默认会清空）。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的 predictions 文件（当 --no_clean 启用时有用）。",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：任意 instance 缺 patch.diff 直接报错退出（默认关闭）。",
    )
    return parser.parse_args()


def _parse_csv(value: str) -> List[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


def prepare_for_one_dataset(*, dataset_key: str, args: argparse.Namespace) -> None:
    spec = DATASET_SPECS[dataset_key]
    subset = spec["subset"]
    dataset_output_dirname = spec["output_dirname"]
    split = args.split or spec["default_split"]
    if split != "test":
        raise ValueError(f"当前脚本按你确认固定使用 split=test（收到：{split}）")

    output_root = Path(args.output_root)
    dest_root = Path(args.dest_root)
    dataset_dest_root = dest_root / subset / split

    if not args.no_clean and dataset_dest_root.exists():
        shutil.rmtree(dataset_dest_root)

    agents = _parse_csv(args.agents)
    mode_dirs = _parse_csv(args.mode_dirs)
    configs = iter_expected_configs(agents=agents, mode_dirs=mode_dirs)

    dataset_output_root = output_root / dataset_output_dirname
    groups: List[AgentGroupSummary] = []

    for agent in agents:
        agent_output_root = dataset_output_root / agent
        if not agent_output_root.is_dir():
            # 你选择的策略：跳过缺失的模型（互不影响）
            continue

        evaluated_by_mode: Dict[str, Set[str]] = {}
        counts_by_mode_dir: Dict[str, int] = {}
        excluded: Dict[str, str] = {}
        included_mode_dirs: List[str] = []

        for mode_dir in mode_dirs:
            config_dir = agent_output_root / mode_dir
            evaluated = collect_evaluated_instances(config_dir)
            evaluated_by_mode[mode_dir] = evaluated
            counts_by_mode_dir[mode_dir] = len(evaluated)

        for mode_dir in mode_dirs:
            n = counts_by_mode_dir[mode_dir]
            if n < args.min_config_instances:
                excluded[mode_dir] = f"样例数<{args.min_config_instances}（{n}）"
            else:
                included_mode_dirs.append(mode_dir)

        # 没有任何配置满足阈值，直接跳过
        if not included_mode_dirs:
            continue

        # 取交集（只在该 agent 内部）
        intersection: Set[str] | None = None
        for mode_dir in included_mode_dirs:
            if intersection is None:
                intersection = set(evaluated_by_mode[mode_dir])
            else:
                intersection &= evaluated_by_mode[mode_dir]
        assert intersection is not None

        if len(intersection) < args.min_intersection_instances:
            # 你选择的策略：交集不足则该 dataset×model 不产出任何 json
            continue

        intersection_ids = sorted(intersection)
        created_files: List[str] = []
        stats_in_intersection: List[ConfigStatsInIntersection] = []

        # 写每个 included 配置的 predictions
        for mode_dir in included_mode_dirs:
            config = Config(agent=agent, mode_dir=mode_dir)
            preds, stats = build_predictions_for_config_on_instances(
                output_root=output_root,
                dataset_output_dirname=dataset_output_dirname,
                dataset_subset=subset,
                split=split,
                config=config,
                instance_ids=intersection_ids,
                strict=args.strict,
            )
            out_path = dataset_dest_root / agent / f"{mode_dir}.json"
            write_json(out_path, preds, overwrite=args.overwrite)
            created_files.append(str(out_path))
            stats_in_intersection.append(stats)

        # 写交集样例列表（方便你用 --instance_ids 或复核）
        instance_list_path = dataset_dest_root / agent / "instance_ids.txt"
        instance_list_path.parent.mkdir(parents=True, exist_ok=True)
        instance_list_path.write_text("\n".join(intersection_ids) + "\n", encoding="utf-8")
        created_files.append(str(instance_list_path))

        groups.append(
            AgentGroupSummary(
                dataset_subset=subset,
                split=split,
                agent=agent,
                mode_dirs_considered=mode_dirs,
                mode_dirs_included=included_mode_dirs,
                mode_dirs_excluded=excluded,
                counts_by_mode_dir={k: counts_by_mode_dir[k] for k in mode_dirs},
                intersection_size=len(intersection_ids),
                intersection_instances=intersection_ids,
                files=created_files,
                stats_in_intersection=stats_in_intersection,
            )
        )

    # 输出 summary（按 dataset 一份）
    if groups:
        summary = {
            "dataset_key": dataset_key,
            "subset": subset,
            "split": split,
            "output_root": str(output_root),
            "dataset_output_dirname": dataset_output_dirname,
            "min_config_instances": args.min_config_instances,
            "min_intersection_instances": args.min_intersection_instances,
            "groups": [asdict(g) for g in groups],
        }
        summary_path = dataset_dest_root / "summary.json"
        write_json(summary_path, summary, overwrite=args.overwrite)

        print(f"✅ 已生成 sb-cli predictions：{subset} {split}")
        for g in groups:
            print(
                f"  - {g.agent}: included={len(g.mode_dirs_included)} "
                f"intersection={g.intersection_size} -> {dataset_dest_root / g.agent}"
            )
    else:
        print(f"⚠️ 未生成任何 predictions：{subset} {split}（可能模型目录缺失或交集不足）")


def main() -> None:
    args = parse_args()

    if args.dataset == "both":
        datasets = ["lite", "verified"]
    else:
        datasets = [args.dataset]

    for dataset_key in datasets:
        prepare_for_one_dataset(dataset_key=dataset_key, args=args)


if __name__ == "__main__":
    main()
