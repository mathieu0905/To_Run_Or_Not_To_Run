#!/usr/bin/env python3
"""
Mega Batch Runner: Execute mixed (instance, mode, dataset) tasks in a single
ThreadPoolExecutor queue so workers never idle waiting for the slowest task
in a batch.

Usage:
    python mega_batch_runner.py <queue.tsv> [workers] [agent_type] [timeout]

queue.tsv format (tab-separated):
    instance_id<TAB>mode<TAB>dataset_short
    e.g.
    django__django-10914    run_free    lite
    astropy__astropy-12907  run_full    verified

dataset_short: "lite" -> princeton-nlp/SWE-bench_Lite
               "verified" -> princeton-nlp/SWE-bench_Verified
"""
import sys
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from runner import run_experiment, save_result


PROJ_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJ_ROOT / "output"

DATASETS = {
    "lite": "princeton-nlp/SWE-bench_Lite",
    "verified": "princeton-nlp/SWE-bench_Verified",
}
DATASET_DIRS = {
    "lite": "swebenchlite",
    "verified": "swebenchverified",
}


def has_valid_patch(instance_id: str, mode: str, dataset_short: str,
                    agent_type: str) -> bool:
    p = (OUTPUT_DIR / DATASET_DIRS[dataset_short] / agent_type / mode /
         instance_id / "patch.diff")
    return p.exists() and p.stat().st_size > 0


VALID_MODES = {"run_free", "run_less", "run_less_k1", "run_less_k2",
               "run_less_k3", "run_cost", "run_full"}


def load_queue(queue_file: Path):
    tasks = []
    for line in queue_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) != 3:
            print(f"WARN: skip malformed line: {line!r}")
            continue
        inst, mode, ds = parts
        if mode not in VALID_MODES:
            print(f"WARN: skip bad mode: {line!r}")
            continue
        if ds not in DATASETS:
            print(f"WARN: skip bad dataset: {line!r}")
            continue
        tasks.append((inst, mode, ds))
    return tasks


def run_one(inst: str, mode: str, dataset_short: str, agent_type: str,
            timeout: int):
    # run_less_k{N} is shorthand for mode=run_less with that k value.
    k = 2
    real_mode = mode
    if mode.startswith("run_less_k"):
        try:
            k = int(mode[len("run_less_k"):])
        except ValueError:
            k = 2
        real_mode = "run_less"
    return run_experiment(
        instance_id=inst,
        mode=real_mode,
        k=k,
        agent_type=agent_type,
        timeout=timeout,
        dataset_name=DATASETS[dataset_short],
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    queue_file = Path(sys.argv[1])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    agent_type = sys.argv[3] if len(sys.argv) > 3 else "opencode"
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 3600

    if not queue_file.exists():
        print(f"ERROR: queue file not found: {queue_file}")
        sys.exit(1)

    all_tasks = load_queue(queue_file)
    print(f"Loaded {len(all_tasks)} tasks from {queue_file}")

    # Skip already-completed (with valid patch)
    todo = [(i, m, d) for (i, m, d) in all_tasks
            if not has_valid_patch(i, m, d, agent_type)]
    skipped = len(all_tasks) - len(todo)
    print(f"Skipping {skipped} (already have valid patch); running {len(todo)}")
    print(f"Workers: {workers}, agent: {agent_type}, timeout: {timeout}s")
    print("=" * 70)

    # Sort: run heavier tasks (run_full + verified) first so they don't tail
    def task_weight(t):
        inst, mode, ds = t
        return (0 if mode == "run_full" else 1,
                0 if ds == "verified" else 1)
    todo.sort(key=task_weight)

    t0 = time.time()
    results = {}
    completed = 0
    failed = 0
    empty_patches = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_one, inst, mode, ds, agent_type, timeout):
                (inst, mode, ds)
            for (inst, mode, ds) in todo
        }
        total = len(futures)
        for fut in as_completed(futures):
            inst, mode, ds = futures[fut]
            try:
                r = fut.result()
                # Persist result.json + flat result file (runner.save_result
                # is normally only called from runner.py __main__).
                try:
                    save_result(r, DATASETS[ds])
                except Exception as e:
                    print(f"WARN: save_result failed for {inst}: {e}",
                          flush=True)
                ok = r.success and r.patch and len(r.patch) > 0
                if ok:
                    completed += 1
                    status = "OK"
                else:
                    if r.success and (not r.patch or len(r.patch) == 0):
                        empty_patches += 1
                        status = "EMPTY"
                    else:
                        failed += 1
                        status = "FAIL"
                results[(inst, mode, ds)] = r
                done = completed + failed + empty_patches
                elapsed = time.time() - t0
                eta = elapsed / done * (total - done) if done else 0
                print(f"[{done}/{total}] {status} {ds}/{mode} {inst} "
                      f"({r.duration_sec:.0f}s, {r.tokens_used} tok) "
                      f"| elapsed={elapsed/60:.1f}min eta={eta/60:.1f}min "
                      f"| ok={completed} empty={empty_patches} fail={failed}",
                      flush=True)
            except Exception as e:
                failed += 1
                done = completed + failed + empty_patches
                print(f"[{done}/{total}] EXC {ds}/{mode} {inst} - {e}",
                      flush=True)

    print("=" * 70)
    print(f"Total runtime: {(time.time()-t0)/60:.1f} min")
    print(f"OK={completed}  EMPTY={empty_patches}  FAIL={failed}")


if __name__ == "__main__":
    main()
