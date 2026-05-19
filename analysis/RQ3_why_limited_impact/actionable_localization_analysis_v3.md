# 交叉分析 v3：同一批 Instance 的配对对比

*Generated: 2026-01-29 12:12:20*

## 核心问题

对于 Unrestricted 模式中有 **Actionable reproduction** 的那批 instance，
**同一批 instance** 在 Prohibited 模式（无执行）下的 Hit Rate 是多少？

这样才能回答：**执行提供 actionable 信息后，定位是否真的更准？**

---

## P→P 案例分析

| Agent | Repro Category (Unrestricted) | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |
|-------|------------------------------|-------|----------------|-------------------|------------------|---------------------|-------|----------|
| Claude Code | Actionable | 46 | 95.7% | 94.6% | 93.5% | 92.4% | -2.2pp | -2.2pp |
| Claude Code | Non-actionable | 18 | 94.4% | 94.4% | 94.4% | 94.4% | +0.0pp | +0.0pp |
| Claude Code | No Reproduction | 52 | 100.0% | 99.0% | 100.0% | 99.0% | +0.0pp | +0.0pp |
| Codex | Actionable | 7 | 85.7% | 85.7% | 85.7% | 85.7% | +0.0pp | +0.0pp |
| Codex | Non-actionable | 1 | 100.0% | 100.0% | 100.0% | 100.0% | +0.0pp | +0.0pp |
| Codex | No Reproduction | 134 | 94.8% | 92.5% | 97.8% | 95.4% | +3.0pp | +2.9pp |

## F→F 案例分析

| Agent | Repro Category (Unrestricted) | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |
|-------|------------------------------|-------|----------------|-------------------|------------------|---------------------|-------|----------|
| Claude Code | Actionable | 37 | 81.1% | 72.7% | 83.8% | 74.8% | +2.7pp | +2.0pp |
| Claude Code | Non-actionable | 16 | 75.0% | 70.0% | 75.0% | 66.9% | +0.0pp | -3.1pp |
| Claude Code | No Reproduction | 31 | 93.5% | 90.3% | 93.5% | 90.3% | +0.0pp | +0.0pp |
| Codex | Actionable | 4 | 100.0% | 70.8% | 100.0% | 70.8% | +0.0pp | +0.0pp |
| Codex | No Reproduction | 51 | 88.2% | 83.0% | 90.2% | 85.0% | +2.0pp | +2.0pp |

---

## 关键发现

### Claude Code

**Actionable 组** (46 个 instance)：
- Prohibited Hit: 95.7% → Unrestricted Hit: 93.5% (**Δ -2.2pp**)
- Prohibited Recall: 94.6% → Unrestricted Recall: 92.4% (**Δ -2.2pp**)

**No Reproduction 组** (52 个 instance)：
- Prohibited Hit: 100.0% → Unrestricted Hit: 100.0% (**Δ +0.0pp**)
- Prohibited Recall: 99.0% → Unrestricted Recall: 99.0% (**Δ +0.0pp**)

### Codex

**Actionable 组** (7 个 instance)：
- Prohibited Hit: 85.7% → Unrestricted Hit: 85.7% (**Δ +0.0pp**)
- Prohibited Recall: 85.7% → Unrestricted Recall: 85.7% (**Δ +0.0pp**)

**No Reproduction 组** (134 个 instance)：
- Prohibited Hit: 94.8% → Unrestricted Hit: 97.8% (**Δ +3.0pp**)
- Prohibited Recall: 92.5% → Unrestricted Recall: 95.4% (**Δ +2.9pp**)

## 解读

- **Δ > 0**: Unrestricted 模式定位更准 → 执行帮助了定位
- **Δ ≈ 0**: 两种模式定位相当 → 执行对定位无显著影响
- **Δ < 0**: Unrestricted 模式定位更差 → 执行可能干扰了定位

如果 Actionable 组的 Δ 显著为正，说明 actionable 的执行反馈确实帮助了文件定位。
如果 Δ ≈ 0 或为负，说明即使执行提供了 actionable 信息，对定位帮助也有限。
