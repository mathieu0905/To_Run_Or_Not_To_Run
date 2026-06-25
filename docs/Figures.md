# Figures

This file defines the figures to be plotted and their reproducible specifications (data sources, metrics, layout, and output).

## Global Conventions (applicable to all figures)

- Modes (parallel configurations, all included in comparison): `run_free`, `run_less_k1`, `run_less_k3`, `run_cost`, `run_full`
- Agents: `claude_code`, `codex`
- Datasets: SWE-bench Lite, SWE-bench Verified
- Pass Rate metric (strictly consistent with `sb-cli-reports`):
  - `pass_rate = resolved_instances / completed_instances`
  - The denominator for each setting is fixed using `completed_instances` from the report (100 for this project)
- Figure language: English (axis / legend / title / annotation)
- Output: Unified output to `figures/` (default export `.png` for easy preview; can additionally export `.pdf` if needed)

---

## 1. Main Results Figure: Pass Rate Comparison (with Confidence Intervals)

- Figure type: Bar chart + 95% CI error bars
- X-axis: Mode (ordered as `run_free → run_less_k1 → run_less_k3 → run_cost → run_full`)
- Y-axis: Pass Rate (from `sb-cli-reports/*.json`)
- Confidence interval: 95% Wilson score interval
- Faceted display: `2 agents × 2 datasets = 4` subplots (suggested: rows=Dataset, columns=Agent; shared y-axis range)
- Core value: Immediately see that confidence intervals highly overlap, supporting the conclusion of "no significant difference / limited marginal benefit"

---

## 2. Cost-Effectiveness Trade-off Figure (Pareto Front)

- Do not use log scale; if points are crowded, prioritize splitting subplots / adjusting layout to ensure intuitiveness
- Faceted display (suggested): `2 agents × 2 datasets = 4` subplots (rows=Dataset, columns=Agent)
- Each point: One Mode (`run_free/run_less_k1/run_less_k3/run_cost/run_full`)
- X-axis: Avg Total Tokens (mean calculated from `output/` traces)
- Y-axis: Pass Rate (from `sb-cli-reports`)
- Point size: Avg High-Cost Exec (calculated from `output/` traces; high-cost execution = test framework commands)
- Encoding suggestions:
  - color=Mode
  - Directly label each point with mode text (avoid relying solely on legend for understanding)
- Optional: Highlight Pareto-optimal points (for discussing "cost-effectiveness frontier")
- Core value: Intuitively see the cost increase brought by execution (tokens + high-cost exec), and the limited marginal benefit in pass rate

---

## 3. Equivalence Test Forest Plot

- Each row is a comparison (all using `run_full` as baseline):
  - `run_free` vs `run_full`
  - `run_less_k1` vs `run_full`
  - `run_less_k3` vs `run_full`
  - `run_cost` vs `run_full`
- Effect size: `ΔPass(pp) = PassRate(mode) - PassRate(run_full)`
- Plot: 90% CI + equivalence interval `±5pp` (with 0 as center line)
- CI method: Based on `completed_ids/resolved_ids` from `sb-cli-reports`, perform paired bootstrap to calculate 90% CI
  - Default recommendation: `n_boot=10000`, `seed=0` (fixed to ensure reproducibility)
- Faceted display: `2 agents × 2 datasets = 4` subplots
- Core value: Clearly show the upper bound of benefit and whether it falls within the equivalence interval, supporting the argument of "limited execution benefit / equivalence"

---

## 4. Paired Analysis Figure (Optional)

- Goal: Support "differences come more from randomness rather than systematic advantage"
- Data source: `completed_ids/resolved_ids` from `sb-cli-reports` (instance-by-instance pairing)
- Figure type (selected): b/c scatter plot
  - X=b (only mode succeeds, run_full fails)
  - Y=c (only run_full succeeds, mode fails)
  - Each point = one mode's paired comparison with run_full (modes include: `run_free/run_less_k1/run_less_k3/run_cost`)
  - Suggest adding diagonal line `y=x` as reference
- Faceted display: `2 agents × 2 datasets = 4` subplots
- Core value: Intuitively see the symmetry/bias of b and c, consistent with McNemar's formulation

---

## Priority Recommendations

- Must plot: Figure 1 (main results) + Figure 2 (cost trade-off)
- Strongly recommended: Figure 3 (Forest Plot)
- Optional: Figure 4 (paired analysis)
