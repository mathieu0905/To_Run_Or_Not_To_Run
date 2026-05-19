# Reproduction Execution 对文件定位的影响分析

*分析目标：Actionable 的执行反馈是否提升了文件定位准确度？*

## 方法论

### 配对对比设计

对于**同一个 instance**，比较：
- **Prohibited 模式**（禁止执行）的定位准确度
- **Unrestricted 模式**（允许执行）的定位准确度

按 Unrestricted 模式中 reproduction 的类型分组，计算 **Δ = Unrestricted - Prohibited**

### 分类定义

| 类别 | 定义 |
|:-----|:-----|
| **Actionable** | 至少一次 reproduction 包含有效定位信息（文件路径、Traceback、行号） |
| **Non-actionable** | 有 reproduction 但全部是环境错误或无有效信息 |
| **No Reproduction** | 没有在编辑前执行测试 |

---

## P→P 案例（两种模式都成功修复）

| Agent | Repro Category | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |
|:------|:---------------|------:|---------------:|------------------:|-----------------:|--------------------:|------:|---------:|
| Claude Code | Actionable | 46 | 95.7% | 94.6% | 93.5% | 92.4% | **-2.2pp** | -2.2pp |
| Claude Code | Non-actionable | 18 | 94.4% | 94.4% | 94.4% | 94.4% | +0.0pp | +0.0pp |
| Claude Code | No Reproduction | 52 | 100.0% | 99.0% | 100.0% | 99.0% | +0.0pp | +0.0pp |
| Codex | Actionable | 7 | 85.7% | 85.7% | 85.7% | 85.7% | +0.0pp | +0.0pp |
| Codex | Non-actionable | 1 | 100.0% | 100.0% | 100.0% | 100.0% | +0.0pp | +0.0pp |
| Codex | No Reproduction | 134 | 94.8% | 92.5% | 97.8% | 95.4% | **+3.0pp** | +2.9pp |

## F→F 案例（两种模式都失败）

| Agent | Repro Category | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |
|:------|:---------------|------:|---------------:|------------------:|-----------------:|--------------------:|------:|---------:|
| Claude Code | Actionable | 37 | 81.1% | 72.7% | 83.8% | 74.8% | **+2.7pp** | +2.0pp |
| Claude Code | Non-actionable | 16 | 75.0% | 70.0% | 75.0% | 66.9% | +0.0pp | -3.1pp |
| Claude Code | No Reproduction | 31 | 93.5% | 90.3% | 93.5% | 90.3% | +0.0pp | +0.0pp |
| Codex | Actionable | 4 | 100.0% | 70.8% | 100.0% | 70.8% | +0.0pp | +0.0pp |
| Codex | No Reproduction | 51 | 88.2% | 83.0% | 90.2% | 85.0% | +2.0pp | +2.0pp |

---

## 关键发现

### P→P（成功案例）：Actionable 执行没有帮助定位

| Agent | Actionable 组变化 | 结论 |
|:------|:------------------|:-----|
| Claude Code | Hit: 95.7% → 93.5% (**-2.2pp**) | 执行后定位反而略差 |
| Codex | Hit: 85.7% → 85.7% (+0.0pp) | 无变化 |

### F→F（失败案例）：Actionable 执行略有帮助

| Agent | Actionable 组变化 | 结论 |
|:------|:------------------|:-----|
| Claude Code | Hit: 81.1% → 83.8% (**+2.7pp**) | 执行略有帮助 |
| Codex | Hit: 100.0% → 100.0% (+0.0pp) | 无变化 |

---

## 结论

1. **对于成功修复的 bug (P→P)**：
   - Actionable reproduction 对定位没有帮助，Claude Code 甚至略有下降 (-2.2pp)
   - 说明这些问题的描述本身就足够清晰，不需要执行

2. **对于失败的 bug (F→F)**：
   - Actionable reproduction 有微弱帮助 (+2.7pp)，但幅度很小
   - 即使执行提供了 actionable 信息，也无法挽救这些失败案例

3. **总体结论**：
   - 即使 execution 提供了 actionable 信息（文件路径、stacktrace、行号），对文件定位的提升也微乎其微
   - 这强烈支持论文的论点：**"Problem descriptions are sufficiently clear"**
