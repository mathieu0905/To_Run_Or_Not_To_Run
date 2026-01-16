# RQ5: Failure Modes - 数据表格

失败模式分析数据。

## 失败类型分析

### 失败模式分类

| 类别 | 描述 | 识别规则 |
|------|------|----------|
| 工具/环境错误 | 命令执行失败、文件不存在等 | trace 中包含 error, exception, failed |
| 循环试错 | 同一命令重复执行多次 | 同一命令执行 > 3 次 |
| 修偏 drift | 修改了不相关的文件 | patch 修改文件数 > 5 |
| 无效 patch | 生成了 patch 但未通过测试 | has_patch=True 但 resolved=False |

## 失败模式分布

### SWE-bench Lite

| Agent | Mode | Total | Resolved | Failed | Tool Errors | Repeated Cmds |
|-------|------|-------|----------|--------|-------------|---------------|
| claude_code | run_free | 100 | 63 | 37 | 0.0 | 0.0 |
| claude_code | run_less_k1 | 100 | 61 | 39 | 0.0 | 0.1 |
| claude_code | run_less_k3 | 100 | 62 | 38 | 0.0 | 0.1 |
| claude_code | run_cost | 100 | 63 | 37 | 0.0 | 0.1 |
| claude_code | run_full | 100 | 64 | 36 | 0.0 | 0.1 |
| codex | run_free | 100 | 73 | 27 | 0.0 | 0.2 |
| codex | run_less_k1 | 100 | 66 | 34 | 0.0 | 0.2 |
| codex | run_less_k3 | 100 | 68 | 32 | 0.0 | 0.3 |
| codex | run_cost | 100 | 69 | 31 | 0.0 | 0.2 |
| codex | run_full | 100 | 72 | 28 | 0.0 | 0.6 |

### SWE-bench Verified

| Agent | Mode | Total | Resolved | Failed | Tool Errors | Repeated Cmds |
|-------|------|-------|----------|--------|-------------|---------------|
| claude_code | run_free | 100 | 64 | 36 | 0.0 | 0.0 |
| claude_code | run_less_k1 | 100 | 64 | 36 | 0.0 | 0.1 |
| claude_code | run_less_k3 | 100 | 65 | 35 | 0.0 | 0.1 |
| claude_code | run_cost | 100 | 67 | 33 | 0.0 | 0.1 |
| claude_code | run_full | 100 | 67 | 33 | 0.0 | 0.1 |
| codex | run_free | 100 | 73 | 27 | 0.0 | 0.2 |
| codex | run_less_k1 | 100 | 72 | 28 | 0.0 | 0.2 |
| codex | run_less_k3 | 100 | 73 | 27 | 0.0 | 0.2 |
| codex | run_cost | 100 | 71 | 29 | 0.0 | 0.1 |
| codex | run_full | 100 | 75 | 25 | 0.0 | 0.5 |

## 典型案例对比

### Run-Free 成功但 Run-Full 失败的案例

| Dataset | Agent | Instance ID |
|---------|-------|-------------|
| swebenchlite | claude_code | django__django-14016 |
| swebenchlite | claude_code | django__django-13230 |
| swebenchlite | claude_code | django__django-12184 |
| swebenchlite | claude_code | django__django-12908 |
| swebenchlite | claude_code | django__django-15695 |
| swebenchlite | codex | django__django-12747 |
| swebenchlite | codex | django__django-12497 |
| swebenchlite | codex | django__django-11964 |
| swebenchlite | codex | django__django-11848 |
| swebenchverified | claude_code | django__django-11532 |

共 16 个案例

### Run-Full 成功但 Run-Free 失败的案例

| Dataset | Agent | Instance ID |
|---------|-------|-------------|
| swebenchlite | claude_code | django__django-11797 |
| swebenchlite | claude_code | django__django-12470 |
| swebenchlite | claude_code | django__django-14997 |
| swebenchlite | claude_code | django__django-11620 |
| swebenchlite | claude_code | django__django-12284 |
| swebenchlite | claude_code | django__django-15498 |
| swebenchlite | codex | django__django-15781 |
| swebenchlite | codex | django__django-15202 |
| swebenchlite | codex | django__django-15252 |
| swebenchverified | claude_code | astropy__astropy-7166 |

共 21 个案例

## 关键发现

### 1. 案例统计

- Run-Free 成功但 Run-Full 失败: **16** 个案例
- Run-Full 成功但 Run-Free 失败: **21** 个案例
- 净差异: **5** 个案例（Run-Full 优势）

### 2. 失败模式分析

**Run-Full 模式的典型失败模式:**
- 循环试错：反复执行同一测试命令，期望不同结果
- 过度修改：修改了不必要的文件，引入新问题
- 工具错误：执行过程中遇到环境问题

**Run-Free 模式的典型失败模式:**
- 推理错误：对问题理解不准确
- 缺少验证：无法确认修复是否正确
- 环境假设：对运行环境的假设不正确

### 3. 结论

- Run-Full 模式在 **5** 个案例上优于 Run-Free
- 执行反馈在某些情况下确实有帮助
- 不同失败模式需要不同的应对策略
- 开发者 review 负担取决于失败模式类型