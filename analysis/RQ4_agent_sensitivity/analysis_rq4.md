# RQ4: Agent Sensitivity - 不同 Agent 的敏感性差异

## 研究问题

**RQ4**: 执行权限对不同 agent（Claude Code vs Codex）的影响是否一致？为什么某些 agent（如 Claude Code）run-free 能大幅降成本，而某些 agent（如 Codex）成本变化较小？

## 方法

- 以 run_free 为基准，计算各 mode 的 ΔCost 和 ΔPass
- 对比 Claude Code 和 Codex 的差异
- 分析 Token 消耗分布（Input vs Output）

## 主要发现

### 1. 成本敏感性对比

| Agent | Dataset | ΔTokens% (Free→Full) | ΔPass% | 敏感性比 |
|-------|---------|----------------------|--------|----------|
| Claude Code | Lite | +129.4% | +1.0% | 129.4 |
| Claude Code | Verified | +162.6% | +3.0% | 54.2 |
| Codex | Lite | +15.5% | -1.0% | 15.2 |
| Codex | Verified | +0.8% | +2.0% | 0.4 |

**关键发现**:
- Claude Code 的敏感性比远高于 Codex（54-129 vs 0.4-15）
- Claude Code 从 Run-Free 到 Run-Full，Token 增长 **129-163%**
- Codex 从 Run-Free 到 Run-Full，Token 仅增长 **0.8-15.5%**

### 2. Agent 特性对比

| 指标 | Claude Code | Codex |
|------|-------------|-------|
| Run-Free Token 消耗 | ~65K | ~470K |
| Run-Full Token 消耗 | ~160K | ~510K |
| Token 增长率 | +146% | +8% |
| Pass Rate 变化 | +2.0% | +0.5% |
| 时间增长率 | +105% | +4% |

### 3. Token 消耗分解

**Claude Code:**
- Run-Free: 97% Input, 3% Output
- Run-Full: 98% Input, 2% Output
- 执行反馈主要增加 Input Token（上下文积累）

**Codex:**
- Run-Free: 98% Input, 2% Output
- Run-Full: 98% Input, 2% Output
- Token 分布几乎不变

### 4. 差异原因分析

**Claude Code 成本敏感的原因:**

1. **基础成本低**: Run-Free 模式下仅消耗 ~65K Token，推理过程简洁高效
2. **执行反馈累积**: 每次执行结果都被添加到上下文，导致 Input Token 快速增长
3. **交互轮数增加**: Run-Full 模式下平均 70 轮交互，Run-Free 仅 35 轮
4. **时间成本高**: 执行等待时间显著增加总耗时（+93-115%）

**Codex 成本稳定的原因:**

1. **基础成本高**: Run-Free 模式下已消耗 ~470K Token，推理过程本身冗长
2. **边际影响小**: 执行反馈相对于已有上下文的边际影响很小
3. **交互轮数稳定**: 各模式下交互轮数变化不大（41-46 轮）
4. **时间成本稳定**: 执行时间对总耗时影响很小（+4-8%）

### 5. 实际影响

**对于 Claude Code:**
- Run-Free 模式可节省 **56-62%** 的 Token 成本
- 时间节省 **48-54%**
- Pass Rate 仅损失 **1-3%**
- **强烈推荐使用 Run-Free 模式**

**对于 Codex:**
- Run-Free 模式仅节省 **0.8-13%** 的 Token 成本
- 时间几乎无变化
- Pass Rate 变化不一致（-1% 到 +2%）
- **执行模式选择对成本影响不大**

## 结论

1. **执行权限对不同 Agent 的影响差异显著**
   - Claude Code: 成本敏感型（执行权限显著增加成本）
   - Codex: 成本稳定型（执行权限对成本影响小）

2. **选择 Agent 时应考虑成本敏感性**
   - 如果追求成本效益，Claude Code + Run-Free 是最佳选择
   - 如果追求最高性能，Codex + Run-Full 略优

3. **基础成本决定敏感性**
   - 基础成本低的 Agent 对执行反馈更敏感
   - 基础成本高的 Agent 对执行反馈不敏感

4. **对研究的启示**
   - 不同 Agent 需要不同的执行策略
   - "One size fits all" 的执行策略不适用
