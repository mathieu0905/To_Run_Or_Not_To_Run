# 交叉分析 v5：修复 Actionable 分类逻辑（合并 Success）

*Generated: 2026-01-29 12:35:42*

## 改进的分类逻辑

**Actionable** (有效信息，可帮助定位):
- 测试成功 (pytest passed, unittest OK)
- 测试失败但有具体信息 (FAILED, AssertionError)
- 业务代码运行时错误 (TypeError, ValueError 等，指向 /testbed/)

**Non-actionable** (无效信息):
- 环境错误 (ModuleNotFoundError, OperationalError, SyntaxError)
- 配置错误 (Django settings, pytest config)
- 无实质性输出

---

## Reproduction 分类统计

### Claude Code

| Category | Count | Percentage |
|----------|------:|------------|
| **Actionable** | 113 | 33.9% |
| **Non-actionable** | 220 | 66.1% |
| **Total** | 333 | 100% |

### Codex

| Category | Count | Percentage |
|----------|------:|------------|
| **Actionable** | 9 | 37.5% |
| **Non-actionable** | 15 | 62.5% |
| **Total** | 24 | 100% |

---

## P→P 案例分析

| Agent | Repro Category | Count | Prohibited Hit | Unrestricted Hit | Δ Hit |
|-------|----------------|------:|---------------:|-----------------:|------:|
| Claude Code | Actionable | 32 | 93.8% | 90.6% | **-3.1pp** |
| Claude Code | Non-actionable | 32 | 96.9% | 96.9% | **+0.0pp** |
| Claude Code | No Reproduction | 52 | 100.0% | 100.0% | **+0.0pp** |
| Codex | Actionable | 5 | 80.0% | 80.0% | **+0.0pp** |
| Codex | Non-actionable | 3 | 100.0% | 100.0% | **+0.0pp** |
| Codex | No Reproduction | 134 | 94.8% | 97.8% | **+3.0pp** |

## F→F 案例分析

| Agent | Repro Category | Count | Prohibited Hit | Unrestricted Hit | Δ Hit |
|-------|----------------|------:|---------------:|-----------------:|------:|
| Claude Code | Actionable | 31 | 83.9% | 83.9% | **+0.0pp** |
| Claude Code | Non-actionable | 22 | 72.7% | 77.3% | **+4.5pp** |
| Claude Code | No Reproduction | 31 | 93.5% | 93.5% | **+0.0pp** |
| Codex | Actionable | 4 | 100.0% | 100.0% | **+0.0pp** |
| Codex | No Reproduction | 51 | 88.2% | 90.2% | **+2.0pp** |

---

## 关键发现

### Claude Code

**Actionable 组** (32 instances):
- Δ Hit: **-3.1pp**

**Non-actionable 组** (32 instances):
- Δ Hit: **+0.0pp**

**No Reproduction 组** (52 instances):
- Δ Hit: **+0.0pp**

### Codex

**Actionable 组** (5 instances):
- Δ Hit: **+0.0pp**

**Non-actionable 组** (3 instances):
- Δ Hit: **+0.0pp**

**No Reproduction 组** (134 instances):
- Δ Hit: **+3.0pp**
