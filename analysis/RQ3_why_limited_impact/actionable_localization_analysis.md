# 交叉分析：Actionable Reproduction 是否提升文件定位准确度？

*Generated: 2026-01-29 11:57:24*

## 研究问题

当 Agent 在编辑代码前执行测试（reproduction），且执行结果包含**可操作信息**
（如文件路径、stacktrace、行号）时，文件定位的准确度是否更高？

## 分类定义

- **Actionable**: 至少一次 reproduction 包含有效定位信息（文件路径、Traceback、行号）
- **Non-actionable**: 有 reproduction 但全部是环境错误或无有效信息
- **None**: 没有在编辑前执行测试

---

## P→P 案例分析 (Unrestricted 模式)

| Agent | Repro Category | Count | Hit Rate | Avg Recall |
|-------|----------------|-------|----------|------------|
| Claude Code | Actionable | 46 | 93.5% | 92.4% |
| Claude Code | Non-actionable | 18 | 94.4% | 94.4% |
| Claude Code | No Reproduction | 52 | 100.0% | 99.0% |
| Codex | Actionable | 7 | 85.7% | 85.7% |
| Codex | Non-actionable | 1 | 100.0% | 100.0% |
| Codex | No Reproduction | 134 | 97.8% | 95.4% |

## F→F 案例分析 (Unrestricted 模式)

| Agent | Repro Category | Count | Hit Rate | Avg Recall |
|-------|----------------|-------|----------|------------|
| Claude Code | Actionable | 37 | 83.8% | 74.8% |
| Claude Code | Non-actionable | 16 | 75.0% | 66.9% |
| Claude Code | No Reproduction | 31 | 93.5% | 90.3% |
| Codex | Actionable | 4 | 100.0% | 70.8% |
| Codex | Non-actionable | 0 | 0.0% | 0.0% |
| Codex | No Reproduction | 51 | 90.2% | 85.0% |

---

## 关键发现

### Claude Code

- Actionable reproduction **没有提升** Hit Rate: 93.5% vs 100.0% (-6.5pp)
- Actionable reproduction **没有提升** Recall: 92.4% vs 99.0% (-6.6pp)
- Non-actionable reproduction 案例: 18 (Hit: 94.4%, Recall: 94.4%)

### Codex

- Actionable reproduction **没有提升** Hit Rate: 85.7% vs 97.8% (-12.0pp)
- Actionable reproduction **没有提升** Recall: 85.7% vs 95.4% (-9.7pp)
- Non-actionable reproduction 案例: 1 (Hit: 100.0%, Recall: 100.0%)

## 结论

如果 Actionable reproduction 的 Hit/Recall 与 No reproduction 相近或更低，
说明即使执行提供了可操作信息，Agent 的定位能力也没有显著提升。
这进一步支持「问题描述足够清晰」的论点。
