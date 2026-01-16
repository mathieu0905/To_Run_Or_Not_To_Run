# RQ1: Effectiveness - 执行权限对修复成功率的影响

## 研究问题

**RQ1**: 在 SWE-bench Lite / Verified 上，Run-Free、Run-Less、Run-Full 三种执行权限对 agent 修复成功率（Pass Rate）有什么影响？是否存在"执行越多越强"的单调关系？

## 方法

- 对比 5 种执行模式：run_free, run_less_k1, run_less_k3, run_cost, run_full
- 使用 2 个 Agent：Claude Code 和 Codex
- 在 2 个数据集上测试：SWE-bench Lite 和 SWE-bench Verified
- 以 run_full 为基准，计算各模式的 Pass Rate 差异（ΔPass）

## 主要发现

### 1. 执行权限对成功率影响很小

| Agent | Dataset | Run-Free | Run-Full | ΔPass |
|-------|---------|----------|----------|-------|
| Claude Code | Lite | 63.0% | 64.0% | +1.0% |
| Claude Code | Verified | 64.0% | 67.0% | +3.0% |
| Codex | Lite | 74.5% | 73.5% | -1.0% |
| Codex | Verified | 73.0% | 75.0% | +2.0% |

**平均差异**: Run-Full 相比 Run-Free 仅提升 **1.2%**

### 2. 不存在"执行越多越强"的单调关系

在 4 组实验中，只有 1 组（Claude Code on Verified）呈现单调递增：

- **Claude Code (Lite)**: 63.0% → 61.0% → 62.0% → 63.0% → 64.0% ✗
- **Codex (Lite)**: 74.5% → 67.3% → 69.4% → 70.4% → 73.5% ✗
- **Claude Code (Verified)**: 64.0% → 64.0% → 65.0% → 67.0% → 67.0% ✓
- **Codex (Verified)**: 73.0% → 72.0% → 73.0% → 71.0% → 75.0% ✗

### 3. Run-Less 模式表现不如预期

限制执行次数（K=1, K=3）并未带来"精准执行"的效果，反而普遍低于 Run-Free：

| Agent | Dataset | run_free | run_less_k1 | run_less_k3 |
|-------|---------|----------|-------------|-------------|
| Claude Code | Lite | 63.0% | 61.0% | 62.0% |
| Codex | Lite | 74.5% | 67.3% | 69.4% |

### 4. Codex 的 Run-Free 表现异常优秀

Codex 在 Run-Free 模式下的表现甚至略优于 Run-Full（Lite: 74.5% vs 73.5%），说明强大的推理能力可以在很大程度上弥补执行反馈的缺失。

## 结论

1. **执行环境并非必要条件**：Run-Free 模式已能达到接近最佳的性能（差距 < 5%）
2. **"One smart run" 假设未得到验证**：Run-Less 模式未能优于 Run-Full，甚至不如 Run-Free
3. **执行反馈的价值有限**：对于当前的 LLM Agent，执行反馈带来的边际收益很小
4. **Agent 能力是关键**：Codex 在所有模式下都优于 Claude Code，说明模型能力比执行权限更重要

## 对研究假设的影响

原假设"One smart run is worth ten blind runs"在当前实验中**未得到支持**。数据显示：

- 限制执行次数并不能迫使 Agent 进行更"智能"的执行
- Run-Free 的强劲表现说明 LLM 的推理能力已经足够强大
- 执行环境更像是"工程捷径"而非"必要能力"
