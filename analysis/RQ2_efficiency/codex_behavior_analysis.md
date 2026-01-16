# RQ2 深入分析：为什么 Codex 在 run_free 模式下 token 消耗没有显著降低？

## 核心问题

- Codex run_free vs run_full 的 token 节省仅 0.8-13.4%
- Claude Code 的节省高达 56-62%
- 这说明 Codex 的行为模式与 Claude Code 有本质区别

---

## 1. 整体行为对比

### SWE-bench Lite

| 指标 | Codex run_free | Codex run_full | CC run_free | CC run_full |
|------|----------------|----------------|-------------|-------------|
| Avg Commands | 21.6 | 23.2 | 6.9 | 17.9 |
| Avg Input Tokens | 400,765 | 464,133 | 66,943 | 154,144 |
| Avg Reasoning | 15.4 | 16.5 | 17.1 | 33.0 |
| Avg File Changes | 2.9 | 3.1 | 2.0 | 5.4 |
| **Token 变化** | -13.7% | - | -56.6% | - |
| **命令数变化** | -6.7% | - | -61.2% | - |

### SWE-bench Verified

| 指标 | Codex run_free | Codex run_full | CC run_free | CC run_full |
|------|----------------|----------------|-------------|-------------|
| Avg Commands | 25.2 | 24.3 | 6.4 | 17.6 |
| Avg Input Tokens | 529,305 | 534,277 | 61,614 | 164,054 |
| **Token 变化** | -0.9% | - | -62.4% | - |
| **命令数变化** | +3.5% | - | -63.6% | - |

---

## 2. 命令类型分布对比

### SWE-bench Lite

| Mode | Agent | Test Exec | Python Snippet | File View | Search | Dir Browse | Other |
|------|-------|-----------|----------------|-----------|--------|------------|-------|
| run_free | Codex | 0 | 1 | 1,237 | 791 | 47 | 86 |
| run_full | Codex | 62 | 124 | 1,135 | 575 | 108 | 314 |
| run_free | CC | 16 | 57 | 358 | 107 | 40 | 115 |
| run_full | CC | 132 | 480 | 426 | 93 | 20 | 632 |

**关键发现：**
- Codex run_free 的代码探索命令（File View + Search + Dir Browse）= **2,075**
- Codex run_full 的代码探索命令 = **1,818**
- **Codex 在 run_free 模式下代码探索命令反而增加了 14%！**

- Claude Code run_free 的代码探索命令 = **505**
- Claude Code run_full 的代码探索命令 = **539**
- Claude Code 在两种模式下代码探索命令基本持平

---

## 3. 命令模式分布 (Top 命令)

### Codex

| 命令 | run_free | run_full |
|------|----------|----------|
| grep | 1,034 | 0 |
| head | 284 | 32 |
| cat | 305 | 4 |
| sed | 250 | 620 |
| find | 122 | 17 |
| rg | 1 | 777 |
| python | 1 | 465 |
| ls | 142 | 215 |

**关键发现：**
- Codex run_free 大量使用 `grep`, `head`, `cat` 来阅读代码
- Codex run_full 更多使用 `rg` (ripgrep) 和 `python` 执行

### Claude Code

| 命令 | run_free | run_full |
|------|----------|----------|
| find | 221 | 208 |
| grep | 148 | 78 |
| python | 210 | 1,401 |
| cat | 70 | 38 |
| ls | 35 | 17 |

**关键发现：**
- Claude Code run_free 的 python 命令只有 210 次
- Claude Code run_full 的 python 命令高达 1,401 次
- **Claude Code 在 run_free 模式下显著减少了 python 执行**

---

## 4. Token 消耗分布

### SWE-bench Lite

| Agent | Mode | Mean | Median | Stdev | Min | Max |
|-------|------|------|--------|-------|-----|-----|
| Codex | run_free | 400,765 | 312,916 | 313,667 | 102,553 | 1,867,927 |
| Codex | run_full | 464,133 | 364,126 | 316,817 | 75,272 | 1,739,115 |
| CC | run_free | 66,943 | 37,778 | 79,825 | 4,173 | 497,711 |
| CC | run_full | 155,701 | 115,307 | 140,524 | 6,113 | 730,495 |

**关键发现：**
- Codex 的 token 消耗方差很大（stdev ~314K）
- Claude Code 的 token 消耗更稳定（stdev ~80-140K）
- Codex 的 median 比 mean 低很多，说明有大量高消耗的异常实例

---

## 5. 工具输出大小分析

### SWE-bench Lite

| Agent | Mode | 平均输出总量 | 平均调用数 | 每次调用输出 | 估算 tokens |
|-------|------|-------------|-----------|-------------|-------------|
| Codex | run_free | 59,116 chars | 21.6 | 2,734 chars | ~14,779 |
| Codex | run_full | 281,080 chars | 23.2 | 12,126 chars | ~70,270 |
| CC | run_free | 50,536 chars | 18.1 | 2,800 chars | ~12,634 |
| CC | run_full | 72,997 chars | 35.8 | 2,041 chars | ~18,249 |

**关键发现：**
- Codex run_full 的每次调用输出（12,126 chars）远高于 run_free（2,734 chars）
- 这是因为 run_full 执行 python/pytest 会产生大量输出
- 但 Codex run_free 的总输出仍然很高（59K chars），因为它执行了更多的代码阅读命令

---

## 6. 根本原因分析

### Codex 的"补偿行为"

当 Codex 被限制不能执行测试时，它会：
1. **增加代码探索命令**：run_free 比 run_full 多 14-28% 的代码探索命令
2. **使用更多的 grep/head/cat**：试图通过阅读更多代码来"模拟"执行效果
3. **保持相似的交互轮数**：推理次数几乎不变（15-17 次）

这导致：
- 虽然没有测试执行的输出
- 但更多的代码探索命令产生了大量的文件内容输出
- 这些输出被累积到 context 中，导致 input_tokens 居高不下

### Claude Code 的"适应行为"

当 Claude Code 被限制不能执行测试时，它会：
1. **显著减少命令执行**：run_free 比 run_full 少 61-64% 的命令
2. **减少 python 执行**：从 1,401 次降到 210 次
3. **保持代码探索命令基本不变**：505 vs 539

这导致：
- 命令执行减少，输出减少
- Context 累积更少
- Token 消耗降低 56-62%

---

## 7. 结论

| 行为模式 | Codex | Claude Code |
|----------|-------|-------------|
| 对 run_free 的响应 | 增加代码探索 | 减少整体交互 |
| 命令执行策略 | 大量 head/sed/grep | 精准读取 |
| Token 效率 | 低（~400-530K/实例） | 高（~62-67K/实例） |
| 适应能力 | 弱（补偿行为） | 强（适应行为） |

**核心发现：不同 Agent 对执行限制的响应策略完全不同，这直接影响了成本节省的效果。**

- **Codex** 似乎更依赖"试错"模式，即使禁止测试执行，也会通过大量代码阅读来"模拟"执行效果
- **Claude Code** 更擅长"一次推理"，在 run_free 模式下能够减少不必要的交互

这个发现对 RQ2 的结论有重要补充：**Run-Free 模式的成本节省效果高度依赖于 Agent 的架构和行为模式。**
