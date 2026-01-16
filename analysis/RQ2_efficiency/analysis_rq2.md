# RQ2: Efficiency - 成本与效率的 Pareto 前沿

## 研究问题

**RQ2**: 不同执行权限对成本（Avg Total tokens）、交互轮数（Avg Turns）、运行时间（Avg Time）的影响有多大？Run-Less 能否以显著更低成本获得接近 Run-Full 的成功率（即形成 Pareto-optimal tradeoff）？

## 方法

- 统计各模式的平均 Token 消耗、交互轮数、运行时间
- 以 run_full 为基准，计算相对变化百分比（ΔCost%、ΔTurns%、ΔTime%）
- 绘制 Pass Rate vs Avg Total Tokens 的 Pareto 前沿

## 主要发现

### 1. Claude Code 的成本节省显著

| Dataset | Mode | Avg Tokens | vs run_full |
|---------|------|------------|-------------|
| Lite | run_free | 69,046 | -56.4% |
| Lite | run_full | 158,417 | - |
| Verified | run_free | 63,490 | -61.9% |
| Verified | run_full | 166,745 | - |

Claude Code 在 Run-Free 模式下可节省约 **56-62%** 的 Token 消耗。

### 2. Codex 的成本节省较小

| Dataset | Mode | Avg Tokens | vs run_full |
|---------|------|------------|-------------|
| Lite | run_free | 409,354 | -13.4% |
| Lite | run_full | 472,776 | - |
| Verified | run_free | 539,301 | -0.8% |
| Verified | run_full | 543,762 | - |

Codex 在 Run-Free 模式下仅节省约 **0.8-13.4%** 的 Token 消耗，远低于 Claude Code。

### 3. 时间消耗对比

| Agent | Dataset | Run-Free | Run-Full | 节省 |
|-------|---------|----------|----------|------|
| Claude Code | Lite | 531s | 1028s | 48.4% |
| Claude Code | Verified | 573s | 1234s | 53.6% |
| Codex | Lite | 570s | 618s | 7.8% |
| Codex | Verified | 724s | 723s | -0.1% |

Claude Code 的时间节省与 Token 节省成正比，而 Codex 几乎没有时间差异。

### 4. Pareto 前沿分析

**SWE-bench Lite 的 Pareto 最优点**:
- Claude Code run_free (63.0%, 69K tokens) ✓
- Claude Code run_full (64.0%, 158K tokens) ✓
- Codex run_free (74.5%, 409K tokens) ✓
- Codex run_less_k1 (67.3%, 375K tokens) ✓

**关键发现**:
- Claude Code run_free 是最具成本效益的选择（最低成本，接近最高性能）
- Codex run_free 在高性能区域是 Pareto 最优的

### 5. 效率比分析

效率比 = Token 节省 / Pass Rate 差异

| Agent | Dataset | Token 节省 | Pass 差异 | 效率比 |
|-------|---------|------------|-----------|--------|
| Claude Code | Lite | 56.4% | +1.0% | 56.4 |
| Claude Code | Verified | 61.9% | +3.0% | 20.6 |
| Codex | Lite | 13.4% | -1.0% | 13.1 |
| Codex | Verified | 0.8% | +2.0% | 0.4 |

Claude Code 的效率比远高于 Codex，说明 Claude Code 更适合在 Run-Free 模式下使用。

## 结论

1. **Run-Free 是最具成本效益的选择**
   - 平均节省 33% Token，仅损失 1.2% Pass Rate
   - 对于 Claude Code，节省更为显著（56-62%）

2. **不存在明显的 Pareto 前沿**
   - Run-Less 模式未能形成有效的 Pareto 前沿
   - 大多数情况下，Run-Free 或 Run-Full 是最优选择

3. **Agent 差异显著**
   - Claude Code 在 Run-Free 模式下成本节省显著
   - Codex 的成本几乎不受执行模式影响

4. **Green AI 视角**
   - Run-Free 模式可大幅降低计算成本和碳排放
   - 对于成本敏感的应用场景，Run-Free 是首选
