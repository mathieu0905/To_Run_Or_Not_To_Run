# Hard-Limit Execution Experiment — Design

Status: draft, pending user approval before implementation.
Target: ISSTA 2026 revision (Reviewer C, Metareview item #1).

## Goal

Reviewer C and the metareview require a **tool-level** hard-limit run of the
\textsc{Prohibited} mode so the main result is no longer tied to prompt-level
compliance. Concretely:

> "At least one hard-limit execution experiment with tool-level blocking for
> the prohibited setting, and ideally also one strict quota setting."

This document describes (a) the implementation, (b) the experimental scope,
(c) the cost and runtime budget, (d) the analysis plan that plugs the new
runs back into Table `tab:compliant-subset` and Table `tab:pass-rate-full`.

## Implementation: remove the shell tool from the agent's toolset

Instead of intercepting shell invocations at the filesystem layer (a shim
on `PATH`), we remove the shell/Bash tool from the agent's capability set
at the CLI level. The agent never sees the tool, so it cannot attempt to
execute code — no refused-command logs, no context pollution, and no grey
area. File-reading, file-editing, globbing, and grepping tools remain
available, so the agent can still localise the bug and write a patch.

### Claude Code

```bash
claude -p \
  --disallowedTools "Bash" \
  --output-format stream-json \
  --dangerously-skip-permissions \
  "<prompt>"
```

- `--disallowedTools "Bash"` removes the `Bash` tool from the model's
  available-tools list. Subagents inherit the restriction. `Read`,
  `Write`, `Edit`, `Glob`, `Grep`, `WebSearch` remain.
- Verified on Claude Code v2.1.112: with `--disallowedTools Bash` the
  agent reports "Bash tool is not available in the current context"
  when asked to run shell commands, while `Write` and `Edit` on
  arbitrary files continue to work. **Do not add** `--permission-mode
  plan`: that mode restricts `Write`/`Edit` to plan files only, which
  would prevent the agent from modifying source code and invalidate
  the repair experiment.

### Codex

```bash
codex exec \
  --skip-git-repo-check \
  --dangerously-bypass-approvals-and-sandbox \
  -c features.shell_tool=false \
  -c features.unified_exec=false \
  --json "<prompt>"
```

- Codex exposes two exec paths: `shell_tool` (classic) and
  `unified_exec` (PTY-backed, on-by-default on non-Windows). **Both must
  be set to `false`**; disabling only one leaves a bypass.
- File-editing via `apply_patch` is built into the core protocol and is
  unaffected. The agent can still read, edit, and write files.

### OpenCode

Set in the per-run `opencode.json` (already written by
`agent_caller.py::_build_opencode_command`):

```json
{
  "permission": {
    "bash": "deny",
    "edit": "allow",
    "write": "allow",
    "read": "allow"
  },
  "provider": { ... },
  "agent":    { ... }
}
```

OpenCode's permission plumbing is documented to short-circuit `bash`
calls at the harness level when `deny` is set. **However**, the docs do
not explicitly confirm this under the headless `opencode run
--dangerously-skip-permissions --format json` path we use — a smoke test
on 1–2 instances is required before the full sweep (see Phase 0 below).

### Hard-Quota-K mode

Tool-deny yields Quota = 0 exactly. Strict Quota-K (K=1 or K=3) still
needs a counter. Two options:

- **Per-invocation allowlist flip**: not feasible; the toolset is fixed
  for the duration of a run.
- **PATH-shim with counter for Bash-enabled runs**: keep the Bash tool
  enabled, but shim `pytest`/`tox`/`python -m pytest`/etc. to increment
  `/tmp/hard_limit_counter` and refuse after K attempts. This is the
  same shim-based approach as the earlier draft, but applied only to
  Quota-K modes where the tool itself cannot be fully removed.

We recommend deferring hard-Quota-K to Phase 2 and doing hard-Prohibited
(tool-deny) as Phase 1.

### Wiring in `agent_caller.py`

New mode strings registered in `runner.py` and `prompt_builder.py`:

- `run_hard_free` — Bash/shell tool hard-disabled; prompt still includes
  the Prohibited-mode narrative so the agent is told to reason rather
  than attempting execution (redundant with the tool removal but keeps
  the prompt diff small). Outputs to
  `output/{dataset}/{agent}/run_hard_free/{instance_id}/`.

New method `_hard_limit_args(agent_type: str) -> list[str]` in
`AgentCaller` returns the extra CLI flags, and
`_build_{claude,codex,opencode}_command` calls it when mode starts with
`run_hard_`. For OpenCode, `_build_opencode_command` additionally merges
`{"permission": {"bash": "deny", ...}}` into the `opencode.json` it
writes.

### Phase 0: smoke test (pre-implementation)

Before running 600 paid instances, run 3 smoke tests per agent on cheap
instances (e.g. `django__django-11099`):

1. Run hard-Prohibited and inspect `trace.jsonl` for any `Bash` /
   `shell_tool` / `unified_exec` / `bash` tool_call events. The count
   should be exactly zero.
2. Check `patch.diff` is non-empty and diffs only `.py` files.
3. Compare turn count and tokens against the soft-Prohibited run of the
   same instance — they should be of the same order (~10–30 turns).

If the OpenCode permission deny does not short-circuit the tool in
headless mode, fall back to the PATH-shim approach for OpenCode only.

## Experimental scope

Reviewer C's request is literally "**at least one** hard-limit execution
experiment". We run exactly one cell, chosen to maximise information
gain given the soft-Prohibited compliance data already in
`tab:compliance`:

**Target cell: Claude Code × SWE-bench Verified, `run_hard_free`, 100 instances.**

Rationale:

- Claude Code is the agent with the highest soft-Prohibited attempt rate
  (0.76 / task on Verified), so prompt-level compliance confounds the
  soft result here more than anywhere else. Hard-enforcement at this
  cell produces the largest possible signal.
- On `prohibit-strict` (`tab:compliant-subset`), Claude Code Verified is
  the single cell with the largest Prohibited–Unrestricted gap
  (−4.8 pp, $N=84$) — exactly the datapoint reviewers are most likely
  to scrutinise.
- Codex and OpenCode are already near zero-execution in soft-Prohibited
  (0.00–0.01 / task for Codex, 0.00 / task for OpenCode Verified); a
  hard run on them would only confirm what the soft run already shows.

| Agent       | Benchmark | Runs | Est. time/run | Wall-clock @ 4 parallel | API cost |
|-------------|-----------|-----:|--------------:|------------------------:|---------:|
| Claude Code | Verified  |  100 | ~ 700 s       | ~ 5 h                   | ~ $75    |

Cost assumes Sonnet 4.5 at current pricing.

### Parallelisation

Reuse the existing `batch_runner.py` at 4-way concurrency. No new
infrastructure.

### Out of scope

- Strict Quota-K enforcement. The metareview phrases this as "*ideally*
  also one strict quota setting", not a hard requirement. The current
  soft Quota-1 compliance table already shows Codex adheres (1.10–1.19
  / task) while Claude Code does not — the informative contrast is
  already available. If reviewers push on it in the next round, we will
  add hard Quota-1 in a follow-up.
- Codex and OpenCode hard runs. Their soft-Prohibited attempts are
  already $\leq 1$ / task, so hard-enforcement cannot change the result
  by more than ~1 pp and would not address the reviewer's concern about
  *non-compliant* cells.

## Analysis plan

1. Re-run `compute_compliance.py` to pick up the new `run_hard_*` modes.
   Expectation (hard-Prohibited): attempted = env-err = completed =
   actionable = 0 across all six (agent, benchmark) cells. This is the
   "zero-execution by construction" row the reviewer asked for.
2. Re-run `recompute_on_compliant.py` so the hard-enforced cell flows
   into `tab:compliant-subset` as a new row alongside the existing six.
   The headline comparisons on the Claude Code Verified cell are:

   | Comparison                                    | What it shows           |
   |----------------------------------------------|-------------------------|
   | soft-Prohibited vs hard-Prohibited            | prompt vs tool fidelity |
   | hard-Prohibited vs Unrestricted               | revised main result     |
   | hard-Prohibited vs soft-Prohibited on `prohibit-strict` subset | null-change sanity check |

3. Extend `sec:env-clean-subset` with a paragraph reporting the three
   comparisons above and the pairwise McNemar / TOST statistics. Frame
   the cell choice explicitly: "we target the configuration with the
   highest soft-Prohibited attempt rate, which is where prompt-level
   compliance most plausibly confounds the comparison."
4. Do **not** replace the main `tab:pass-rate-full` numbers. The hard
   result is reported as a robustness check in `sec:env-clean-subset`,
   preserving the existing five-mode × three-agent × two-benchmark
   structure.

## Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| OpenCode permission deny does not short-circuit `bash` in headless mode | Phase 0 smoke test verifies; fallback is PATH-shim on OpenCode only. |
| Removing Bash also removes some non-test capability the agent depends on (e.g. `git log`, `ls`) | Claude Code's `Glob`/`Grep`/`Read` tools cover file-system inspection; `git` is already disabled in all modes by our prompts. Spot-check 5 agents traces for "I wish I could run X" complaints. |
| Hard-Prohibited resolve rate comes in materially lower than soft (> 5pp on multiple cells) | Publishable as a main-claim refinement: "\textsc{Prohibited} $\approx$ \textsc{Unrestricted} under intention-to-treat; hard-enforcement imposes a cost of \textit{X} pp on \textit{Y} cells but still saves \textit{Z}\% of tokens." |
| Hard-Prohibited causes agents to retry the same tool-use in a loop | `--disallowedTools` removes the tool from the context so the model cannot name it; no retry loop is expected. Monitor anyway. |
| vLLM OOM under sustained 8-way load for 14 h | Already battle-tested from the main Qwen run; drop to 4-way if needed. |

## Timeline

Assuming approval on day 0:

- Day 1 AM: Phase 0 smoke test (Claude Code, 1 instance) verifies
  `trace.jsonl` has zero `Bash` tool_use events under
  `--disallowedTools "Bash" --permission-mode plan`.
- Day 1 PM: if smoke passes, wire `run_hard_free` into
  `agent_caller.py` and kick off the full 100-instance sweep.
- Day 2: sweep completes (~5 h at 4-way); re-run `compute_compliance.py`
  and `recompute_on_compliant.py`.
- Day 3: integrate the new cell into paper (one added row in
  `tab:compliance`, one added row in `tab:compliant-subset`, one added
  paragraph in `sec:env-clean-subset`).

Total elapsed: 3 days, ~$75.
