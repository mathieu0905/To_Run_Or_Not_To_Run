# 交叉分析 v2：Prohibited vs Unrestricted 定位准确度对比

*Generated: 2026-01-29 12:07:33*

## 研究问题

对于**同一个 instance**，比较：
1. **Prohibited 模式**（禁止执行）的定位准确度
2. **Unrestricted 模式**（允许执行）的定位准确度，按 reproduction 类型分组

这样可以控制问题难度，回答：**「执行是否真的帮助了定位？」**

---

## P→P 案例分析

| Agent | Mode | Repro Category | Count | Hit Rate | Avg Recall |
|-------|------|----------------|-------|----------|------------|
| Claude Code | **Prohibited** | N/A (无执行) | 116 | 97.4% | 96.6% |
| Claude Code | Unrestricted | Actionable | 46 | 93.5% | 92.4% |
| Claude Code | Unrestricted | Non-actionable | 18 | 94.4% | 94.4% |
| Claude Code | Unrestricted | No Reproduction | 52 | 100.0% | 99.0% |
|  |  |  |  |  |  |
| Codex | **Prohibited** | N/A (无执行) | 142 | 94.4% | 92.2% |
| Codex | Unrestricted | Actionable | 7 | 85.7% | 85.7% |
| Codex | Unrestricted | Non-actionable | 1 | 100.0% | 100.0% |
| Codex | Unrestricted | No Reproduction | 134 | 97.8% | 95.4% |

### P→P 配对对比：同一 Instance 在两种模式下的定位变化

| Agent | Repro Category | Count | Prohibited→Unrestricted Hit变化 | Recall变化 |
|-------|----------------|-------|--------------------------------|------------|
| Claude Code | Actionable | 46 | +0/-1/=45 | -2.2pp |
| Claude Code | Non-actionable | 18 | +0/-0/=18 | +0.0pp |
| Claude Code | No Reproduction | 52 | +0/-0/=52 | +0.0pp |
| Codex | Actionable | 7 | +0/-0/=7 | +0.0pp |
| Codex | Non-actionable | 1 | +0/-0/=1 | +0.0pp |
| Codex | No Reproduction | 134 | +4/-0/=130 | +2.9pp |

## F→F 案例分析

| Agent | Mode | Repro Category | Count | Hit Rate | Avg Recall |
|-------|------|----------------|-------|----------|------------|
| Claude Code | **Prohibited** | N/A (无执行) | 84 | 84.5% | 78.7% |
| Claude Code | Unrestricted | Actionable | 37 | 83.8% | 74.8% |
| Claude Code | Unrestricted | Non-actionable | 16 | 75.0% | 66.9% |
| Claude Code | Unrestricted | No Reproduction | 31 | 93.5% | 90.3% |
|  |  |  |  |  |  |
| Codex | **Prohibited** | N/A (无执行) | 55 | 89.1% | 82.1% |
| Codex | Unrestricted | Actionable | 4 | 100.0% | 70.8% |
| Codex | Unrestricted | No Reproduction | 51 | 90.2% | 85.0% |

### F→F 配对对比：同一 Instance 在两种模式下的定位变化

| Agent | Repro Category | Count | Prohibited→Unrestricted Hit变化 | Recall变化 |
|-------|----------------|-------|--------------------------------|------------|
| Claude Code | Actionable | 37 | +1/-0/=36 | +2.0pp |
| Claude Code | Non-actionable | 16 | +1/-1/=14 | -3.1pp |
| Claude Code | No Reproduction | 31 | +1/-1/=29 | +0.0pp |
| Codex | Actionable | 4 | +0/-0/=4 | +0.0pp |
| Codex | No Reproduction | 51 | +2/-1/=48 | +2.0pp |

---

## 关键发现

### Claude Code

**Actionable Reproduction 组** (46 个 instance)：
- Hit 变化: +0 提升 / -1 下降 / =45 不变
- Recall 平均变化: -2.2pp

**No Reproduction 组** (52 个 instance)：
- Hit 变化: +0 提升 / -0 下降 / =52 不变
- Recall 平均变化: +0.0pp

### Codex

**Actionable Reproduction 组** (7 个 instance)：
- Hit 变化: +0 提升 / -0 下降 / =7 不变
- Recall 平均变化: +0.0pp

**No Reproduction 组** (134 个 instance)：
- Hit 变化: +4 提升 / -0 下降 / =130 不变
- Recall 平均变化: +2.9pp

## 解读

- **+Hit 提升**: Prohibited 模式定位失败，Unrestricted 模式定位成功 → 执行帮助了定位
- **-Hit 下降**: Prohibited 模式定位成功，Unrestricted 模式定位失败 → 执行可能干扰了定位
- **=Hit 不变**: 两种模式定位结果一致 → 执行对定位无影响

如果 Actionable 组的「提升」数量远大于「下降」，说明执行确实帮助了定位。
如果两者接近或「下降」更多，说明执行对定位帮助有限甚至有负面影响。
