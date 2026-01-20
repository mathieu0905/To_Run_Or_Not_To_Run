# RQ4: Agent Sensitivity - Sensitivity Differences Across Different Agents

## Research Question

**RQ4**: Is the impact of execution permissions consistent across different agents (Claude Code vs Codex)? Why can some agents (e.g., Claude Code) significantly reduce costs in run-free mode, while other agents (e.g., Codex) show minimal cost changes?

## Methodology

- Use run_free as the baseline and calculate ΔCost and ΔPass for each mode
- Compare differences between Claude Code and Codex
- Analyze token consumption distribution (Input vs Output)

## Key Findings

### 1. Cost Sensitivity Comparison

| Agent | Dataset | ΔTokens% (Free→Full) | ΔPass% | Sensitivity Ratio |
|-------|---------|----------------------|--------|----------|
| Claude Code | Lite | +129.4% | +1.0% | 129.4 |
| Claude Code | Verified | +162.6% | +3.0% | 54.2 |
| Codex | Lite | +15.5% | -1.0% | 15.2 |
| Codex | Verified | +0.8% | +2.0% | 0.4 |

**Key Findings**:
- Claude Code's sensitivity ratio is significantly higher than Codex (54-129 vs 0.4-15)
- Claude Code shows token growth of **129-163%** from Run-Free to Run-Full
- Codex shows token growth of only **0.8-15.5%** from Run-Free to Run-Full

### 2. Agent Characteristics Comparison

| Metric | Claude Code | Codex |
|------|-------------|-------|
| Run-Free Token Consumption | ~65K | ~470K |
| Run-Full Token Consumption | ~160K | ~510K |
| Token Growth Rate | +146% | +8% |
| Pass Rate Change | +2.0% | +0.5% |
| Time Growth Rate | +105% | +4% |

### 3. Token Consumption Breakdown

**Claude Code:**
- Run-Free: 97% Input, 3% Output
- Run-Full: 98% Input, 2% Output
- Execution feedback primarily increases Input tokens (context accumulation)

**Codex:**
- Run-Free: 98% Input, 2% Output
- Run-Full: 98% Input, 2% Output
- Token distribution remains nearly unchanged

### 4. Analysis of Differences

**Reasons for Claude Code's Cost Sensitivity:**

1. **Low Base Cost**: Run-Free mode consumes only ~65K tokens, with concise and efficient reasoning
2. **Execution Feedback Accumulation**: Each execution result is added to the context, causing rapid Input token growth
3. **Increased Interaction Rounds**: Run-Full mode averages 70 interactions, while Run-Free has only 35
4. **High Time Cost**: Execution wait time significantly increases total time consumption (+93-115%)

**Reasons for Codex's Cost Stability:**

1. **High Base Cost**: Run-Free mode already consumes ~470K tokens, with inherently verbose reasoning
2. **Small Marginal Impact**: Execution feedback has minimal marginal impact relative to existing context
3. **Stable Interaction Rounds**: Interaction rounds vary little across modes (41-46 rounds)
4. **Stable Time Cost**: Execution time has minimal impact on total time consumption (+4-8%)

### 5. Practical Impact

**For Claude Code:**
- Run-Free mode can save **56-62%** of token costs
- Time savings of **48-54%**
- Pass rate loss of only **1-3%**
- **Strongly recommend using Run-Free mode**

**For Codex:**
- Run-Free mode saves only **0.8-13%** of token costs
- Time change is negligible
- Pass rate changes are inconsistent (-1% to +2%)
- **Execution mode choice has minimal impact on costs**

## Conclusions

1. **Impact of Execution Permissions Varies Significantly Across Different Agents**
   - Claude Code: Cost-sensitive type (execution permissions significantly increase costs)
   - Codex: Cost-stable type (execution permissions have minimal impact on costs)

2. **Cost Sensitivity Should Be Considered When Selecting Agents**
   - For cost-effectiveness, Claude Code + Run-Free is the best choice
   - For maximum performance, Codex + Run-Full is slightly better

3. **Base Cost Determines Sensitivity**
   - Agents with low base costs are more sensitive to execution feedback
   - Agents with high base costs are less sensitive to execution feedback

4. **Implications for Research**
   - Different agents require different execution strategies
   - A "one size fits all" execution strategy is not applicable
