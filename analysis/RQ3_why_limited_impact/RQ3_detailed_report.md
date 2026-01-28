# RQ3 详细分析报告: 为什么执行反馈影响有限?

## 1. 总体发现

- Hurt 案例 (执行反馈导致失败): 16 个
- Helped 案例 (执行反馈帮助成功): 21 个
- 净收益: 5 个实例

## 2. Hurt vs Helped 对比

| 指标 | Hurt 案例 | Helped 案例 |
|------|-----------|-------------|
| 案例数量 | 16 | 21 |
| 平均测试执行 | 8.1 | 8.6 |
| 平均错误命令 | 5.7 | 6.8 |
| 平均重复命令 | 1.6 | 2.4 |

## 3. Hurt 案例列表

| Instance | Agent | 命令数 | 测试数 | 重复数 | 错误数 |
|----------|-------|--------|--------|--------|--------|
| django__django-12184 | claude_code | 26 | 14 | 5 | 5 |
| django__django-12908 | claude_code | 17 | 14 | 1 | 5 |
| django__django-14016 | claude_code | 23 | 14 | 0 | 3 |
| django__django-15695 | claude_code | 22 | 12 | 3 | 6 |
| django__django-13230 | claude_code | 17 | 8 | 2 | 4 |
| django__django-12497 | codex | 16 | 3 | 0 | 10 |
| django__django-11964 | codex | 27 | 2 | 3 | 12 |
| django__django-11848 | codex | 12 | 3 | 0 | 6 |
| django__django-12747 | codex | 19 | 3 | 0 | 3 |
| django__django-11532 | claude_code | 15 | 10 | 3 | 5 |
| astropy__astropy-14365 | claude_code | 6 | 3 | 1 | 3 |
| django__django-11555 | claude_code | 24 | 15 | 4 | 9 |
| django__django-13121 | claude_code | 18 | 7 | 0 | 5 |
| django__django-11728 | claude_code | 16 | 10 | 1 | 5 |
| django__django-11790 | claude_code | 17 | 6 | 1 | 5 |
| django__django-10973 | codex | 17 | 6 | 1 | 5 |

## 4. Helped 案例列表

| Instance | Agent | 命令数 | 测试数 | 重复数 | 错误数 |
|----------|-------|--------|--------|--------|--------|
| django__django-14997 | claude_code | 19 | 5 | 0 | 7 |
| django__django-15498 | claude_code | 18 | 7 | 0 | 5 |
| django__django-12470 | claude_code | 38 | 12 | 4 | 9 |
| django__django-11620 | claude_code | 16 | 12 | 3 | 5 |
| django__django-11797 | claude_code | 41 | 8 | 4 | 5 |
| django__django-12284 | claude_code | 26 | 18 | 4 | 8 |
| django__django-15202 | codex | 34 | 4 | 5 | 15 |
| django__django-15781 | codex | 18 | 2 | 0 | 9 |
| django__django-15252 | codex | 33 | 5 | 0 | 7 |
| django__django-11206 | claude_code | 25 | 21 | 8 | 10 |
| django__django-11490 | claude_code | 15 | 11 | 3 | 7 |
| astropy__astropy-14096 | claude_code | 17 | 12 | 1 | 8 |
| django__django-12304 | claude_code | 24 | 5 | 3 | 5 |
| django__django-10973 | claude_code | 9 | 2 | 0 | 2 |
| django__django-12965 | claude_code | 20 | 7 | 1 | 1 |
| django__django-12663 | claude_code | 17 | 12 | 4 | 7 |
| django__django-11265 | claude_code | 25 | 22 | 5 | 12 |
| astropy__astropy-7166 | claude_code | 21 | 2 | 1 | 2 |
| django__django-11490 | codex | 18 | 2 | 0 | 3 |
| django__django-12304 | codex | 15 | 3 | 2 | 4 |
| django__django-11265 | codex | 34 | 8 | 3 | 11 |

## 5. 结论

执行反馈的影响有限，原因包括：

1. **双刃剑效应**: 执行反馈既可能帮助 (21例) 也可能误导 (16例)
2. **试错循环陷阱**: 执行反馈容易导致 agent 陷入无效的重试循环
3. **确定性结果**: 90%+ 的案例无论是否有执行反馈结果相同
4. **净收益微小**: 400 个实例中仅 5 个净收益
