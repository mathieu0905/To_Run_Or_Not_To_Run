# RQ3 补充分析：Verification/Reproduction 完整统计

*Generated: 2026-01-28 21:13:09*

## 1. Reproduction Execution 统计

**定义**：发生在第一次 file edit 之前的测试执行，用于理解/定位 bug。

- **Actionable**: 执行结果包含有效信息（文件路径、stacktrace、行号），可用于定位
- **Non-actionable**: 环境错误或无有效信息

### P→P 案例 (Unrestricted 模式)

| Agent | Has Repro. | Total Execs | Actionable | Non-actionable |
|-------|-----------|-------------|------------|----------------|
| Claude Code | 64 (55.2%) | 164 | 80 (48.8%) | 84 |
| Codex | 9 (6.3%) | 17 | 11 (64.7%) | 6 |

## 2. Verification Execution 统计

**定义**：发生在第一次 file edit 之后的测试执行，用于验证补丁。

### P→P 案例 (Unrestricted 模式)

| Agent | Has Verif. | Total Execs | Success | Test Fail | Env Error |
|-------|-----------|-------------|---------|-----------|-----------|
| Claude Code | 100 (86.2%) | 851 | 414 (48.6%) | 154 (18.1%) | 127 (14.9%) |
| Codex | 138 (97.2%) | 445 | 230 (51.7%) | 60 (13.5%) | 152 (34.2%) |

### F→F 案例 (Unrestricted 模式)

| Agent | Has Verif. | Total Execs | Success | Test Fail | Env Error |
|-------|-----------|-------------|---------|-----------|-----------|
| Claude Code | 80 (95.2%) | 668 | 272 (40.7%) | 102 (15.3%) | 121 (18.1%) |
| Codex | 52 (94.5%) | 153 | 85 (55.6%) | 17 (11.1%) | 49 (32.0%) |

## 3. 每实例平均执行次数

| Agent | Outcome | Avg. Repro/Instance | Avg. Verif/Instance |
|-------|---------|---------------------|---------------------|
| Claude Code | P→P | 1.41 | 7.34 |
| Claude Code | F→F | 2.02 | 7.95 |
| Codex | P→P | 0.12 | 3.13 |
| Codex | F→F | 0.18 | 2.78 |

## 4. 关键发现

### Claude Code

- **Reproduction**: 164 次执行中 80 次 (48.8%) 提供了可用于定位的信息
- **Verification**: 851 次执行中 414 次 (48.6%) 成功，127 次 (14.9%) 是环境错误

### Codex

- **Reproduction**: 17 次执行中 11 次 (64.7%) 提供了可用于定位的信息
- **Verification**: 445 次执行中 230 次 (51.7%) 成功，152 次 (34.2%) 是环境错误
