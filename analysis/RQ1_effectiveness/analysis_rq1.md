# RQ1: Effectiveness - Impact of Execution Regimes on Repair Success Rate

## Research Question

**RQ1**: On SWE-bench Lite / Verified, what impact do three execution regimes (Run-Free, Run-Less, Run-Full) have on agent repair success rate (Pass Rate)? Is there a monotonic "more execution = better" relationship?

## Method

- Compare 5 execution modes: run_free, run_less_k1, run_less_k3, run_cost, run_full
- Use 2 Agents: Claude Code and Codex
- Test on 2 datasets: SWE-bench Lite and SWE-bench Verified
- Use run_full as baseline, calculate Pass Rate differences (ΔPass) for each mode

## Main Findings

### 1. Execution Regimes Have Minimal Impact on Success Rate

| Agent | Dataset | Run-Free | Run-Full | ΔPass |
|-------|---------|----------|----------|-------|
| Claude Code | Lite | 63.0% | 64.0% | +1.0% |
| Claude Code | Verified | 64.0% | 67.0% | +3.0% |
| Codex | Lite | 74.5% | 73.5% | -1.0% |
| Codex | Verified | 73.0% | 75.0% | +2.0% |

**Average Difference**: Run-Full improves over Run-Free by only **1.2%**

### 2. No Monotonic "More Execution = Better" Relationship

Among 4 experimental groups, only 1 (Claude Code on Verified) shows monotonic increase:

- **Claude Code (Lite)**: 63.0% → 61.0% → 62.0% → 63.0% → 64.0% ✗
- **Codex (Lite)**: 74.5% → 67.3% → 69.4% → 70.4% → 73.5% ✗
- **Claude Code (Verified)**: 64.0% → 64.0% → 65.0% → 67.0% → 67.0% ✓
- **Codex (Verified)**: 73.0% → 72.0% → 73.0% → 71.0% → 75.0% ✗

### 3. Run-Less Mode Underperforms Expectations

Limiting execution count (K=1, K=3) did not achieve "precise execution" effect, and generally performs worse than Run-Free:

| Agent | Dataset | run_free | run_less_k1 | run_less_k3 |
|-------|---------|----------|-------------|-------------|
| Claude Code | Lite | 63.0% | 61.0% | 62.0% |
| Codex | Lite | 74.5% | 67.3% | 69.4% |

### 4. Codex's Run-Free Performance is Exceptionally Strong

Codex's performance in Run-Free mode is even slightly better than Run-Full (Lite: 74.5% vs 73.5%), indicating that strong reasoning capabilities can largely compensate for the lack of execution feedback.

## Conclusion

1. **Execution environment is not a necessary condition**: Run-Free mode already achieves near-optimal performance (gap < 5%)
2. **"One smart run" hypothesis not validated**: Run-Less mode fails to outperform Run-Full, and even underperforms Run-Free
3. **Limited value of execution feedback**: For current LLM Agents, the marginal benefit from execution feedback is minimal
4. **Agent capability is key**: Codex outperforms Claude Code across all modes, indicating model capability is more important than execution regimes

## Impact on Research Hypothesis

The original hypothesis "One smart run is worth ten blind runs" is **not supported** by current experiments. Data shows:

- Limiting execution count does not force Agents to perform more "intelligent" executions
- Strong performance of Run-Free indicates LLM reasoning capabilities are already sufficiently powerful
- Execution environment is more of an "engineering shortcut" than a "necessary capability"
