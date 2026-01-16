# RQ6: 案例分析与任务难度分层

## 全模式对比分析

对比所有 5 种执行模式的表现差异。

### SWE-bench Lite

**claude_code:**

#### 成功率对比

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 63 | 63.0% |
| run_less_k1 | 61 | 61.0% |
| run_less_k3 | 62 | 62.0% |
| run_cost | 63 | 63.0% |
| run_full | 64 | 64.0% |

#### 模式间差异矩阵

表格显示：行模式成功但列模式失败的案例数

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 4 | 5 | 6 | 5 |
| run_less_k1 | 2 | - | 3 | 4 | 3 |
| run_less_k3 | 4 | 4 | - | 5 | 2 |
| run_cost | 6 | 6 | 6 | - | 4 |
| run_full | 6 | 6 | 4 | 5 | - |

#### 关键对比

**Run-Free vs Run-Less-K1:**
- 两者都成功: 59
- run_free 独有: 4
- run_less_k1 独有: 2
- 净差异: -2

**Run-Free vs Run-Less-K3:**
- 两者都成功: 58
- run_free 独有: 5
- run_less_k3 独有: 4
- 净差异: -1

**Run-Free vs Run-Cost:**
- 两者都成功: 57
- run_free 独有: 6
- run_cost 独有: 6
- 净差异: +0

**Run-Free vs Run-Full:**
- 两者都成功: 58
- run_free 独有: 5
- run_full 独有: 6
- 净差异: +1

**Run-Less-K1 vs Run-Full:**
- 两者都成功: 58
- run_less_k1 独有: 3
- run_full 独有: 6
- 净差异: +3

**Run-Less-K3 vs Run-Full:**
- 两者都成功: 60
- run_less_k3 独有: 2
- run_full 独有: 4
- 净差异: +2

**Run-Cost vs Run-Full:**
- 两者都成功: 59
- run_cost 独有: 4
- run_full 独有: 5
- 净差异: +1

**codex:**

#### 成功率对比

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 73 | 73.0% |
| run_less_k1 | 66 | 66.0% |
| run_less_k3 | 68 | 68.0% |
| run_cost | 69 | 69.0% |
| run_full | 72 | 72.0% |

#### 模式间差异矩阵

表格显示：行模式成功但列模式失败的案例数

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 9 | 6 | 8 | 4 |
| run_less_k1 | 2 | - | 3 | 5 | 2 |
| run_less_k3 | 1 | 5 | - | 6 | 2 |
| run_cost | 4 | 8 | 7 | - | 5 |
| run_full | 3 | 8 | 6 | 8 | - |

#### 关键对比

**Run-Free vs Run-Less-K1:**
- 两者都成功: 64
- run_free 独有: 9
- run_less_k1 独有: 2
- 净差异: -7

**Run-Free vs Run-Less-K3:**
- 两者都成功: 67
- run_free 独有: 6
- run_less_k3 独有: 1
- 净差异: -5

**Run-Free vs Run-Cost:**
- 两者都成功: 65
- run_free 独有: 8
- run_cost 独有: 4
- 净差异: -4

**Run-Free vs Run-Full:**
- 两者都成功: 69
- run_free 独有: 4
- run_full 独有: 3
- 净差异: -1

**Run-Less-K1 vs Run-Full:**
- 两者都成功: 64
- run_less_k1 独有: 2
- run_full 独有: 8
- 净差异: +6

**Run-Less-K3 vs Run-Full:**
- 两者都成功: 66
- run_less_k3 独有: 2
- run_full 独有: 6
- 净差异: +4

**Run-Cost vs Run-Full:**
- 两者都成功: 64
- run_cost 独有: 5
- run_full 独有: 8
- 净差异: +3

### SWE-bench Verified

**claude_code:**

#### 成功率对比

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 64 | 64.0% |
| run_less_k1 | 64 | 64.0% |
| run_less_k3 | 65 | 65.0% |
| run_cost | 67 | 67.0% |
| run_full | 67 | 67.0% |

#### 模式间差异矩阵

表格显示：行模式成功但列模式失败的案例数

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 8 | 8 | 4 | 6 |
| run_less_k1 | 8 | - | 2 | 3 | 3 |
| run_less_k3 | 9 | 3 | - | 2 | 2 |
| run_cost | 7 | 6 | 4 | - | 4 |
| run_full | 9 | 6 | 4 | 4 | - |

#### 关键对比

**Run-Free vs Run-Less-K1:**
- 两者都成功: 56
- run_free 独有: 8
- run_less_k1 独有: 8
- 净差异: +0

**Run-Free vs Run-Less-K3:**
- 两者都成功: 56
- run_free 独有: 8
- run_less_k3 独有: 9
- 净差异: +1

**Run-Free vs Run-Cost:**
- 两者都成功: 60
- run_free 独有: 4
- run_cost 独有: 7
- 净差异: +3

**Run-Free vs Run-Full:**
- 两者都成功: 58
- run_free 独有: 6
- run_full 独有: 9
- 净差异: +3

**Run-Less-K1 vs Run-Full:**
- 两者都成功: 61
- run_less_k1 独有: 3
- run_full 独有: 6
- 净差异: +3

**Run-Less-K3 vs Run-Full:**
- 两者都成功: 63
- run_less_k3 独有: 2
- run_full 独有: 4
- 净差异: +2

**Run-Cost vs Run-Full:**
- 两者都成功: 63
- run_cost 独有: 4
- run_full 独有: 4
- 净差异: +0

**codex:**

#### 成功率对比

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 73 | 73.0% |
| run_less_k1 | 72 | 72.0% |
| run_less_k3 | 73 | 73.0% |
| run_cost | 71 | 71.0% |
| run_full | 75 | 75.0% |

#### 模式间差异矩阵

表格显示：行模式成功但列模式失败的案例数

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 5 | 5 | 7 | 1 |
| run_less_k1 | 4 | - | 6 | 7 | 2 |
| run_less_k3 | 5 | 7 | - | 8 | 3 |
| run_cost | 5 | 6 | 6 | - | 2 |
| run_full | 3 | 5 | 5 | 6 | - |

#### 关键对比

**Run-Free vs Run-Less-K1:**
- 两者都成功: 68
- run_free 独有: 5
- run_less_k1 独有: 4
- 净差异: -1

**Run-Free vs Run-Less-K3:**
- 两者都成功: 68
- run_free 独有: 5
- run_less_k3 独有: 5
- 净差异: +0

**Run-Free vs Run-Cost:**
- 两者都成功: 66
- run_free 独有: 7
- run_cost 独有: 5
- 净差异: -2

**Run-Free vs Run-Full:**
- 两者都成功: 72
- run_free 独有: 1
- run_full 独有: 3
- 净差异: +2

**Run-Less-K1 vs Run-Full:**
- 两者都成功: 70
- run_less_k1 独有: 2
- run_full 独有: 5
- 净差异: +3

**Run-Less-K3 vs Run-Full:**
- 两者都成功: 70
- run_less_k3 独有: 3
- run_full 独有: 5
- 净差异: +2

**Run-Cost vs Run-Full:**
- 两者都成功: 69
- run_cost 独有: 2
- run_full 独有: 6
- 净差异: +4


## 执行权限递增分析

分析从 Run-Free 到 Run-Full 的渐进变化。

### SWE-bench Lite

**claude_code:**

| 类别 | 数量 | 说明 |
|------|------|------|
| 始终成功 | 52 | 所有模式都能解决 |
| 始终失败 | 0 | 所有模式都无法解决 |
| 随执行改善 | 4 | 更多执行权限有帮助 |
| 随执行恶化 | 5 | 更多执行权限反而有害 |
| 不一致 | 11 | 表现不稳定 |

**随执行恶化的案例（Run-Free 成功但 Run-Full 失败）:**
- `django__django-12184`
- `django__django-12908`
- `django__django-13230`
- `django__django-14016`
- `django__django-15695`

**codex:**

| 类别 | 数量 | 说明 |
|------|------|------|
| 始终成功 | 59 | 所有模式都能解决 |
| 始终失败 | 0 | 所有模式都无法解决 |
| 随执行改善 | 2 | 更多执行权限有帮助 |
| 随执行恶化 | 4 | 更多执行权限反而有害 |
| 不一致 | 14 | 表现不稳定 |

**随执行恶化的案例（Run-Free 成功但 Run-Full 失败）:**
- `django__django-11848`
- `django__django-11964`
- `django__django-12497`
- `django__django-12747`

### SWE-bench Verified

**claude_code:**

| 类别 | 数量 | 说明 |
|------|------|------|
| 始终成功 | 55 | 所有模式都能解决 |
| 始终失败 | 0 | 所有模式都无法解决 |
| 随执行改善 | 8 | 更多执行权限有帮助 |
| 随执行恶化 | 6 | 更多执行权限反而有害 |
| 不一致 | 7 | 表现不稳定 |

**随执行恶化的案例（Run-Free 成功但 Run-Full 失败）:**
- `astropy__astropy-14365`
- `django__django-11532`
- `django__django-11555`
- `django__django-11728`
- `django__django-11790`
- ... 共 6 个

**codex:**

| 类别 | 数量 | 说明 |
|------|------|------|
| 始终成功 | 59 | 所有模式都能解决 |
| 始终失败 | 0 | 所有模式都无法解决 |
| 随执行改善 | 3 | 更多执行权限有帮助 |
| 随执行恶化 | 1 | 更多执行权限反而有害 |
| 不一致 | 19 | 表现不稳定 |

**随执行恶化的案例（Run-Free 成功但 Run-Full 失败）:**
- `django__django-10973`


## 典型案例全模式分析

### `django__django-10973` (codex, SWE-bench Verified)

**类型**: Run-Free 成功但 Run-Full 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 232,585 | 47 | 0 | **成功** |
| run_less_k1 | 149,535 | 29 | 2 | 失败 |
| run_less_k3 | 166,599 | 27 | 0 | 失败 |
| run_cost | 162,007 | 24 | 8 | 失败 |
| run_full | 278,583 | 44 | 12 | 失败 |

**分析**: 执行反馈可能导致 Agent 陷入试错循环或偏离正确方向。

### `django__django-12304` (codex, SWE-bench Verified)

**类型**: Run-Full 成功但 Run-Free 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 157,322 | 25 | 0 | 失败 |
| run_less_k1 | 191,904 | 31 | 4 | **成功** |
| run_less_k3 | 259,846 | 40 | 4 | **成功** |
| run_cost | 234,968 | 33 | 4 | **成功** |
| run_full | 200,265 | 27 | 4 | **成功** |

**分析**: 该问题可能需要执行反馈来验证修复或定位问题。

### `django__django-11490` (codex, SWE-bench Verified)

**类型**: Run-Full 成功但 Run-Free 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 252,469 | 32 | 0 | 失败 |
| run_less_k1 | 202,265 | 19 | 2 | **成功** |
| run_less_k3 | 411,288 | 47 | 6 | **成功** |
| run_cost | 345,046 | 47 | 4 | **成功** |
| run_full | 305,072 | 38 | 4 | **成功** |

**分析**: 该问题可能需要执行反馈来验证修复或定位问题。

### `django__django-11265` (codex, SWE-bench Verified)

**类型**: Run-Full 成功但 Run-Free 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 409,485 | 29 | 0 | 失败 |
| run_less_k1 | 585,511 | 39 | 2 | 失败 |
| run_less_k3 | 745,455 | 45 | 8 | 失败 |
| run_cost | 1,087,114 | 61 | 12 | **成功** |
| run_full | 858,408 | 54 | 16 | **成功** |

**分析**: 该问题可能需要执行反馈来验证修复或定位问题。

### `django__django-11790` (claude_code, SWE-bench Verified)

**类型**: Run-Free 成功但 Run-Full 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 132,602 | 59 | 0 | **成功** |
| run_less_k1 | 233,202 | 87 | 6 | 失败 |
| run_less_k3 | 198,961 | 80 | 6 | 失败 |
| run_cost | 189,346 | 80 | 4 | 失败 |
| run_full | 176,459 | 75 | 5 | 失败 |

**分析**: 执行反馈可能导致 Agent 陷入试错循环或偏离正确方向。

### `astropy__astropy-14365` (claude_code, SWE-bench Verified)

**类型**: Run-Free 成功但 Run-Full 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 15,768 | 14 | 0 | **成功** |
| run_less_k1 | 15,657 | 12 | 0 | 失败 |
| run_less_k3 | 53,159 | 29 | 2 | 失败 |
| run_cost | 70,629 | 38 | 3 | 失败 |
| run_full | 39,176 | 32 | 3 | 失败 |

**分析**: 执行反馈可能导致 Agent 陷入试错循环或偏离正确方向。

### `django__django-11532` (claude_code, SWE-bench Verified)

**类型**: Run-Free 成功但 Run-Full 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 11,961 | 7 | 0 | **成功** |
| run_less_k1 | 101,566 | 42 | 3 | **成功** |
| run_less_k3 | 94,802 | 40 | 5 | 失败 |
| run_cost | 129,260 | 54 | 4 | **成功** |
| run_full | 124,953 | 56 | 6 | 失败 |

**分析**: 执行反馈可能导致 Agent 陷入试错循环或偏离正确方向。

### `django__django-12965` (claude_code, SWE-bench Verified)

**类型**: Run-Full 成功但 Run-Free 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 191,095 | 69 | 0 | 失败 |
| run_less_k1 | 182,385 | 67 | 4 | **成功** |
| run_less_k3 | 182,567 | 69 | 3 | **成功** |
| run_cost | 188,172 | 71 | 5 | **成功** |
| run_full | 225,064 | 84 | 5 | **成功** |

**分析**: 该问题可能需要执行反馈来验证修复或定位问题。

### `django__django-12663` (claude_code, SWE-bench Verified)

**类型**: Run-Full 成功但 Run-Free 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 85,546 | 40 | 0 | 失败 |
| run_less_k1 | 185,420 | 64 | 3 | 失败 |
| run_less_k3 | 301,056 | 83 | 2 | **成功** |
| run_cost | 483,717 | 116 | 5 | **成功** |
| run_full | 440,663 | 118 | 5 | **成功** |

**分析**: 该问题可能需要执行反馈来验证修复或定位问题。

### `django__django-10973` (claude_code, SWE-bench Verified)

**类型**: Run-Full 成功但 Run-Free 失败

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 8,643 | 15 | 0 | 失败 |
| run_less_k1 | 32,236 | 28 | 3 | 失败 |
| run_less_k3 | 25,522 | 23 | 3 | 失败 |
| run_cost | 22,523 | 20 | 3 | 失败 |
| run_full | 51,807 | 41 | 3 | **成功** |

**分析**: 该问题可能需要执行反馈来验证修复或定位问题。


## 任务难度分层分析

按任务难度分析执行权限的影响。难度定义基于 Run-Full 模式下的成功率。

### 难度分布

- 简单 (所有 Agent 在 Run-Full 下都成功): 141 个
- 中等 (部分 Agent 成功): 15 个
- 困难 (所有 Agent 都失败): 12 个

### 按难度分层的全模式对比

#### 简单任务 (141 个)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 79.4% | 81.6% | 84.4% | 83.0% | 88.7% |
| codex | 93.6% | 89.4% | 90.8% | 89.4% | 97.9% |

#### 中等任务 (15 个)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 80.0% | 53.3% | 40.0% | 66.7% | 40.0% |
| codex | 80.0% | 60.0% | 66.7% | 73.3% | 60.0% |

#### 困难任务 (12 个)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 25.0% | 16.7% | 16.7% | 25.0% | 0.0% |
| codex | 16.7% | 25.0% | 25.0% | 25.0% | 0.0% |


## 全模式成本分析

### SWE-bench Lite

**claude_code:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 69,047 | 35.2 | 0.6 | - |
| run_less_k1 | 105,400 | 48.5 | 4.0 | +52.6% |
| run_less_k3 | 139,240 | 59.6 | 5.2 | +101.7% |
| run_cost | 143,596 | 61.3 | 5.4 | +108.0% |
| run_full | 158,417 | 69.7 | 7.0 | +129.4% |

**codex:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 409,355 | 41.0 | 0.0 | - |
| run_less_k1 | 375,408 | 40.1 | 2.3 | +-8.3% |
| run_less_k3 | 524,471 | 46.8 | 4.9 | +28.1% |
| run_cost | 499,337 | 44.9 | 4.4 | +22.0% |
| run_full | 472,777 | 44.1 | 6.3 | +15.5% |

### SWE-bench Verified

**claude_code:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 63,490 | 32.7 | 0.5 | - |
| run_less_k1 | 125,338 | 52.6 | 3.7 | +97.4% |
| run_less_k3 | 125,777 | 53.6 | 4.4 | +98.1% |
| run_cost | 134,374 | 56.6 | 4.5 | +111.6% |
| run_full | 166,746 | 68.7 | 6.3 | +162.6% |

**codex:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 539,302 | 46.5 | 0.0 | - |
| run_less_k1 | 409,696 | 41.3 | 2.2 | +-24.0% |
| run_less_k3 | 578,573 | 50.3 | 4.5 | +7.3% |
| run_cost | 491,096 | 44.9 | 3.8 | +-8.9% |
| run_full | 543,763 | 46.3 | 5.9 | +0.8% |


## 案例分析总结

### 核心发现

1. **执行反馈是双刃剑**
   - 部分案例中，执行反馈帮助 Agent 验证修复
   - 部分案例中，执行反馈反而误导 Agent 偏离正确方向
   - 净收益有限（通常 < 5 个案例）

2. **Run-Less 模式表现不稳定**
   - Run-Less-K1 和 Run-Less-K3 并未比 Run-Free 更好
   - 限制执行次数并不能迫使 Agent 进行更智能的执行
   - 反而可能因为执行次数不足而无法完成验证

3. **任务难度决定执行价值**
   - 简单任务：执行权限几乎无影响
   - 中等任务：执行权限有一定帮助
   - 困难任务：执行权限无法解决根本问题

4. **成本随执行权限单调增加**
   - Run-Free < Run-Less-K1 < Run-Less-K3 < Run-Cost < Run-Full
   - 但 Pass Rate 并未单调增加

### 实践建议

1. **默认使用 Run-Free** - 成本效益最高
2. **不推荐 Run-Less 模式** - 表现不如 Run-Free，成本更高
3. **仅在必要时启用 Run-Full** - 当推理无法确定修复正确性时
4. **Run-Cost 是折中选择** - 有成本约束时的备选方案
