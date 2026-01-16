# Run-Cost 模式深度分析

Run-Cost 是有成本约束的执行模式，在执行次数和成本之间寻求平衡。

## 1. 整体表现对比

### SWE-bench Lite

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 63 | 61 | 62 | 63 | 64 |
| codex | 73 | 66 | 68 | 69 | 72 |

### SWE-bench Verified

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 64 | 64 | 65 | 67 | 67 |
| codex | 73 | 72 | 73 | 71 | 75 |

## 2. Run-Cost 与其他模式的对比

### SWE-bench Lite

**claude_code:**

| 对比 | Run-Cost 胜 | 对方胜 | 净差异 |
|------|-------------|--------|--------|
| vs Run-Free | 6 | 6 | +0 |
| vs Run-Less-K1 | 6 | 4 | +2 |
| vs Run-Less-K3 | 6 | 5 | +1 |
| vs Run-Full | 4 | 5 | -1 |

**Run-Cost 独有成功 (2 个):**
- `django__django-12113`
- `django__django-12589`

**codex:**

| 对比 | Run-Cost 胜 | 对方胜 | 净差异 |
|------|-------------|--------|--------|
| vs Run-Free | 4 | 8 | -4 |
| vs Run-Less-K1 | 8 | 5 | +3 |
| vs Run-Less-K3 | 7 | 6 | +1 |
| vs Run-Full | 5 | 8 | -3 |

**Run-Cost 独有成功 (2 个):**
- `django__django-12589`
- `django__django-14997`

### SWE-bench Verified

**claude_code:**

| 对比 | Run-Cost 胜 | 对方胜 | 净差异 |
|------|-------------|--------|--------|
| vs Run-Free | 7 | 4 | +3 |
| vs Run-Less-K1 | 6 | 3 | +3 |
| vs Run-Less-K3 | 4 | 2 | +2 |
| vs Run-Full | 4 | 4 | +0 |

**codex:**

| 对比 | Run-Cost 胜 | 对方胜 | 净差异 |
|------|-------------|--------|--------|
| vs Run-Free | 5 | 7 | -2 |
| vs Run-Less-K1 | 6 | 7 | -1 |
| vs Run-Less-K3 | 6 | 8 | -2 |
| vs Run-Full | 2 | 6 | -4 |

**Run-Cost 独有成功 (1 个):**
- `astropy__astropy-13236`

## 3. 汇总统计

| 指标 | 数量 |
|------|------|
| Run-Cost 独有成功 | 5 |
| Run-Cost 比 Run-Free 好 | 22 |
| Run-Cost 比 Run-Full 好 | 15 |
| Run-Free 比 Run-Cost 好 | 25 |
| Run-Full 比 Run-Cost 好 | 23 |

## 4. Run-Cost 独有成功案例详细分析

### `astropy__astropy-13236` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 1,115,511 | 72 | 2 | 失败 |
| run_less_k1 | 263,515 | 37 | 2 | 失败 |
| run_less_k3 | 678,205 | 60 | 8 | 失败 |
| run_cost | 594,006 | 61 | 2 | **成功** |
| run_full | 564,008 | 55 | 10 | 失败 |

### `django__django-12113` (claude_code, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 91,157 | 34 | 0 | 失败 |
| run_less_k1 | 104,128 | 34 | 1 | 失败 |
| run_less_k3 | 330,868 | 83 | 7 | 失败 |
| run_cost | 443,799 | 112 | 0 | **成功** |
| run_full | 103,905 | 34 | 0 | 失败 |

### `django__django-12589` (claude_code, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 506,993 | 107 | 9 | 失败 |
| run_less_k1 | 115,450 | 45 | 2 | 失败 |
| run_less_k3 | 154,816 | 59 | 3 | 失败 |
| run_cost | 570,922 | 157 | 11 | **成功** |
| run_full | 294,978 | 108 | 8 | 失败 |

### `django__django-14997` (codex, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 905,040 | 58 | 0 | 失败 |
| run_less_k1 | 926,072 | 56 | 2 | 失败 |
| run_less_k3 | 609,736 | 49 | 2 | 失败 |
| run_cost | 1,362,485 | 78 | 6 | **成功** |
| run_full | 564,813 | 53 | 2 | 失败 |

### `django__django-12589` (codex, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 1,056,172 | 67 | 0 | 失败 |
| run_less_k1 | 1,304,099 | 78 | 2 | 失败 |
| run_less_k3 | 1,195,104 | 77 | 4 | 失败 |
| run_cost | 1,547,467 | 81 | 2 | **成功** |
| run_full | 554,197 | 57 | 2 | 失败 |

## 5. 成本效率分析

Run-Cost 的成本相对于其他模式的位置。

### SWE-bench Lite

**claude_code:**

| Mode | Avg Tokens | Pass Rate | 效率比 (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 69,047 | 63 | 0.91 |
| run_less_k1 | 105,400 | 61 | 0.58 |
| run_less_k3 | 139,240 | 62 | 0.45 |
| run_cost | 143,596 | 63 | 0.44 |
| run_full | 158,417 | 64 | 0.40 |

**codex:**

| Mode | Avg Tokens | Pass Rate | 效率比 (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 409,355 | 73 | 0.18 |
| run_less_k1 | 375,408 | 66 | 0.18 |
| run_less_k3 | 524,471 | 68 | 0.13 |
| run_cost | 499,337 | 69 | 0.14 |
| run_full | 472,777 | 72 | 0.15 |

### SWE-bench Verified

**claude_code:**

| Mode | Avg Tokens | Pass Rate | 效率比 (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 63,490 | 64 | 1.01 |
| run_less_k1 | 125,338 | 64 | 0.51 |
| run_less_k3 | 125,777 | 65 | 0.52 |
| run_cost | 134,374 | 67 | 0.50 |
| run_full | 166,746 | 67 | 0.40 |

**codex:**

| Mode | Avg Tokens | Pass Rate | 效率比 (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 539,302 | 73 | 0.14 |
| run_less_k1 | 409,696 | 72 | 0.18 |
| run_less_k3 | 578,573 | 73 | 0.13 |
| run_cost | 491,096 | 71 | 0.14 |
| run_full | 543,763 | 75 | 0.14 |

## 6. Run-Cost 模式的价值

### 优势

1. **成本可控** - 有明确的成本上限，避免无限制消耗
2. **表现稳定** - 在多数情况下接近 Run-Full 的效果
3. **独有成功案例** - 有些问题只有 Run-Cost 能解决
4. **比 Run-Less 更灵活** - 不是简单限制次数，而是限制总成本

### 适用场景

1. **预算有限但需要执行反馈** - 比 Run-Free 多一些验证能力
2. **避免过度执行** - 比 Run-Full 更节制
3. **生产环境** - 成本可预测，适合大规模部署

### 实践建议

1. **Run-Free** - 默认首选，成本最低
2. **Run-Cost** - 需要执行但要控制成本时的最佳选择
3. **Run-Full** - 仅在调试复杂问题时使用
4. **Run-Less** - 不推荐，表现不稳定
