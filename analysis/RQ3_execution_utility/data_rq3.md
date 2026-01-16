# RQ3: Execution Utility - 数据表格

执行行为的目的分析数据。

## 执行目的分类分布

### SWE-bench Lite

| Agent | Mode | Total | Verification | Localization | Environment | Exploration | Other |
|-------|------|-------|--------------|--------------|-------------|-------------|-------|
| claude_code | run_free | 693 | 59 (8.5%) | 16 (2.3%) | 44 (6.3%) | 493 (71.1%) | 81 (11.7%) |
| claude_code | run_less_k1 | 1064 | 395 (37.1%) | 235 (22.1%) | 92 (8.6%) | 257 (24.2%) | 85 (8.0%) |
| claude_code | run_less_k3 | 1372 | 516 (37.6%) | 310 (22.6%) | 122 (8.9%) | 299 (21.8%) | 125 (9.1%) |
| claude_code | run_cost | 1450 | 541 (37.3%) | 254 (17.5%) | 175 (12.1%) | 355 (24.5%) | 125 (8.6%) |
| claude_code | run_full | 1804 | 703 (39.0%) | 239 (13.2%) | 342 (19.0%) | 375 (20.8%) | 145 (8.0%) |
| codex | run_free | 4324 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2372 (54.9%) | 1952 (45.1%) |
| codex | run_less_k1 | 4040 | 226 (5.6%) | 22 (0.5%) | 26 (0.6%) | 1064 (26.3%) | 2702 (66.9%) |
| codex | run_less_k3 | 4760 | 488 (10.3%) | 37 (0.8%) | 168 (3.5%) | 1246 (26.2%) | 2821 (59.3%) |
| codex | run_cost | 4562 | 442 (9.7%) | 42 (0.9%) | 82 (1.8%) | 1072 (23.5%) | 2924 (64.1%) |
| codex | run_full | 4636 | 634 (13.7%) | 44 (0.9%) | 80 (1.7%) | 1090 (23.5%) | 2788 (60.1%) |

### SWE-bench Verified

| Agent | Mode | Total | Verification | Localization | Environment | Exploration | Other |
|-------|------|-------|--------------|--------------|-------------|-------------|-------|
| claude_code | run_free | 640 | 46 (7.2%) | 21 (3.3%) | 3 (0.5%) | 462 (72.2%) | 108 (16.9%) |
| claude_code | run_less_k1 | 1086 | 374 (34.4%) | 227 (20.9%) | 125 (11.5%) | 259 (23.8%) | 101 (9.3%) |
| claude_code | run_less_k3 | 1226 | 444 (36.2%) | 287 (23.4%) | 102 (8.3%) | 304 (24.8%) | 89 (7.3%) |
| claude_code | run_cost | 1322 | 451 (34.1%) | 224 (16.9%) | 209 (15.8%) | 329 (24.9%) | 109 (8.2%) |
| claude_code | run_full | 1758 | 633 (36.0%) | 220 (12.5%) | 385 (21.9%) | 353 (20.1%) | 167 (9.5%) |
| codex | run_free | 5034 | 2 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2612 (51.9%) | 2420 (48.1%) |
| codex | run_less_k1 | 4130 | 220 (5.3%) | 18 (0.4%) | 62 (1.5%) | 928 (22.5%) | 2902 (70.3%) |
| codex | run_less_k3 | 5008 | 448 (8.9%) | 30 (0.6%) | 164 (3.3%) | 1200 (24.0%) | 3166 (63.2%) |
| codex | run_cost | 4544 | 378 (8.3%) | 38 (0.8%) | 112 (2.5%) | 1080 (23.8%) | 2936 (64.6%) |
| codex | run_full | 4864 | 594 (12.2%) | 40 (0.8%) | 94 (1.9%) | 1114 (22.9%) | 3022 (62.1%) |

## 各模式执行目的对比

对比不同执行模式下的执行行为差异。

### SWE-bench Lite

**claude_code:**

- Run-Free 总执行次数: 693
- Run-Full 总执行次数: 1804
- Run-Free 验证执行: 59
- Run-Full 验证执行: 703
- 执行次数差异: +1111 (160.3% 增加)

**codex:**

- Run-Free 总执行次数: 4324
- Run-Full 总执行次数: 4636
- Run-Free 验证执行: 0
- Run-Full 验证执行: 634
- 执行次数差异: +312 (7.2% 增加)

### SWE-bench Verified

**claude_code:**

- Run-Free 总执行次数: 640
- Run-Full 总执行次数: 1758
- Run-Free 验证执行: 46
- Run-Full 验证执行: 633
- 执行次数差异: +1118 (174.7% 增加)

**codex:**

- Run-Free 总执行次数: 5034
- Run-Full 总执行次数: 4864
- Run-Free 验证执行: 2
- Run-Full 验证执行: 594
- 执行次数差异: +-170 (-3.4% 增加)

## 试错循环分析

统计同一命令重复执行的情况，反映试错行为。

### SWE-bench Lite

| Agent | Mode | 重复命令数 | 试错实例数 |
|-------|------|------------|------------|
| claude_code | run_free | 8 | 8 |
| claude_code | run_less_k1 | 86 | 86 |
| claude_code | run_less_k3 | 119 | 119 |
| claude_code | run_cost | 120 | 120 |
| claude_code | run_full | 124 | 124 |
| codex | run_free | 2041 | 2041 |
| codex | run_less_k1 | 1896 | 1896 |
| codex | run_less_k3 | 2220 | 2220 |
| codex | run_cost | 2151 | 2151 |
| codex | run_full | 2122 | 2122 |

### SWE-bench Verified

| Agent | Mode | 重复命令数 | 试错实例数 |
|-------|------|------------|------------|
| claude_code | run_free | 9 | 9 |
| claude_code | run_less_k1 | 94 | 94 |
| claude_code | run_less_k3 | 113 | 113 |
| claude_code | run_cost | 94 | 94 |
| claude_code | run_full | 115 | 115 |
| codex | run_free | 2394 | 2394 |
| codex | run_less_k1 | 1946 | 1946 |
| codex | run_less_k3 | 2334 | 2334 |
| codex | run_cost | 2169 | 2169 |
| codex | run_full | 2241 | 2241 |

## 关键发现

### 1. 执行目的分类

| 类别 | 描述 | 典型命令 |
|------|------|----------|
| 验证 (Verification) | 运行测试框架验证修复 | pytest, python -m pytest, python -m unittest |
| 定位 (Localization) | 运行脚本定位问题 | python script.py |
| 环境确认 (Environment) | 确认环境配置 | python --version, pip list, pip show |
| 探索 (Exploration) | 探索文件系统和代码 | ls, find, cat |

### 2. 主要发现

**各模式平均执行次数:**

- run_free: 平均 2673 次执行，其中 27 次验证
- run_less_k1: 平均 2580 次执行，其中 304 次验证
- run_less_k3: 平均 3092 次执行，其中 474 次验证
- run_cost: 平均 2970 次执行，其中 453 次验证
- run_full: 平均 3266 次执行，其中 641 次验证

### 3. 结论

- **Run-Free 模式几乎不执行命令**：验证执行次数接近 0
- **Run-Full 模式执行最多**：大量用于验证和探索
- **验证是主要执行目的**：在有执行权限的模式下，验证占比最高
- **试错循环普遍存在**：Run-Full 模式下重复执行同一命令的情况较多