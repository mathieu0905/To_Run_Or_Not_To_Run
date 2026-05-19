# 交叉分析 v4：修复 Actionable 分类逻辑后的结果

*Generated: 2026-01-29 12:27:15*

## 改进的分类逻辑

**Actionable** (真正有助于定位):
- 测试成功 (pytest passed, unittest OK)
- AssertionError + Traceback
- 业务代码的运行时错误 (TypeError, ValueError 等，且指向 /testbed/)

**Non-actionable** (环境错误或无用信息):
- 模块导入错误 (ModuleNotFoundError, ImportError)
- 文件系统错误 (FileNotFoundError, PermissionError)
- 数据库错误 (OperationalError, table already exists)
- 语法错误 (SyntaxError)
- 配置错误 (pytest: error, DJANGO_SETTINGS_MODULE)
- 其他无法提供定位信息的输出

---

## P→P 案例分析

| Agent | Repro Category | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |
|-------|----------------|-------|----------------|-------------------|------------------|---------------------|-------|----------|
| Claude Code | Actionable | 25 | 92.0% | 92.0% | 92.0% | 92.0% | +0.0pp | +0.0pp |
| Claude Code | Non-actionable | 39 | 97.4% | 96.2% | 94.9% | 93.6% | -2.6pp | -2.6pp |
| Claude Code | No Reproduction | 52 | 100.0% | 99.0% | 100.0% | 99.0% | +0.0pp | +0.0pp |
| Codex | Actionable | 3 | 66.7% | 66.7% | 66.7% | 66.7% | +0.0pp | +0.0pp |
| Codex | Non-actionable | 5 | 100.0% | 100.0% | 100.0% | 100.0% | +0.0pp | +0.0pp |
| Codex | No Reproduction | 134 | 94.8% | 92.5% | 97.8% | 95.4% | +3.0pp | +2.9pp |

## F→F 案例分析

| Agent | Repro Category | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |
|-------|----------------|-------|----------------|-------------------|------------------|---------------------|-------|----------|
| Claude Code | Actionable | 15 | 80.0% | 70.2% | 80.0% | 70.2% | +0.0pp | +0.0pp |
| Claude Code | Non-actionable | 38 | 78.9% | 72.6% | 81.6% | 73.2% | +2.6pp | +0.7pp |
| Claude Code | No Reproduction | 31 | 93.5% | 90.3% | 93.5% | 90.3% | +0.0pp | +0.0pp |
| Codex | Actionable | 2 | 100.0% | 66.7% | 100.0% | 66.7% | +0.0pp | +0.0pp |
| Codex | Non-actionable | 2 | 100.0% | 75.0% | 100.0% | 75.0% | +0.0pp | +0.0pp |
| Codex | No Reproduction | 51 | 88.2% | 83.0% | 90.2% | 85.0% | +2.0pp | +2.0pp |

---

## 关键发现

### Claude Code

**Actionable 组** (25 个 instance)：
- Prohibited Hit: 92.0% → Unrestricted Hit: 92.0% (**Δ +0.0pp**)
- Prohibited Recall: 92.0% → Unrestricted Recall: 92.0% (**Δ +0.0pp**)

**Non-actionable 组** (39 个 instance)：
- Prohibited Hit: 97.4% → Unrestricted Hit: 94.9% (**Δ -2.6pp**)

**No Reproduction 组** (52 个 instance)：
- Prohibited Hit: 100.0% → Unrestricted Hit: 100.0% (**Δ +0.0pp**)

### Codex

**Actionable 组** (3 个 instance)：
- Prohibited Hit: 66.7% → Unrestricted Hit: 66.7% (**Δ +0.0pp**)
- Prohibited Recall: 66.7% → Unrestricted Recall: 66.7% (**Δ +0.0pp**)

**Non-actionable 组** (5 个 instance)：
- Prohibited Hit: 100.0% → Unrestricted Hit: 100.0% (**Δ +0.0pp**)

**No Reproduction 组** (134 个 instance)：
- Prohibited Hit: 94.8% → Unrestricted Hit: 97.8% (**Δ +3.0pp**)

## 解读

- **Δ > 0**: Unrestricted 模式定位更准 → 执行帮助了定位
- **Δ ≈ 0**: 两种模式定位相当 → 执行对定位无显著影响
- **Δ < 0**: Unrestricted 模式定位更差 → 执行可能干扰了定位
