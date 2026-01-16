# RQ5: Failure Modes - 失败模式分析

## 研究问题

**RQ5**: 不同执行 regime 会诱发哪些典型失败模式（工具/环境错误、循环试错、修偏 drift、无效 patch）？这些失败模式是否会增加或降低开发者后续调试与 review 负担？

## 方法

自动识别失败模式：

| 类别 | 描述 | 识别规则 |
|------|------|----------|
| 工具/环境错误 | 命令执行失败、文件不存在等 | trace 中包含 error, exception, failed |
| 循环试错 | 同一命令重复执行多次 | 同一命令执行 > 3 次 |
| 修偏 drift | 修改了不相关的文件 | patch 修改文件数 > 5 |
| 无效 patch | 生成了 patch 但未通过测试 | has_patch=True 但 resolved=False |

## 主要发现

### 1. 案例统计

| 类型 | 数量 |
|------|------|
| Run-Free 成功但 Run-Full 失败 | 16 |
| Run-Full 成功但 Run-Free 失败 | 21 |
| 净差异（Run-Full 优势） | 5 |

**关键发现**: Run-Full 仅在 5 个净案例上优于 Run-Free，优势非常有限。

### 2. 失败模式分布

**SWE-bench Lite:**

| Agent | Mode | Failed | Repeated Cmds |
|-------|------|--------|---------------|
| Claude Code | run_free | 37 | 0.0 |
| Claude Code | run_full | 36 | 0.1 |
| Codex | run_free | 27 | 0.2 |
| Codex | run_full | 28 | 0.6 |

**观察**:
- 失败数量在各模式间差异很小
- Run-Full 模式下循环试错略多（Codex: 0.2 → 0.6）

### 3. 典型案例分析

**Run-Free 成功但 Run-Full 失败的案例（16 个）**:
- django__django-14016
- django__django-13230
- django__django-12184
- ...

**可能原因**:
- 执行反馈误导了 Agent 的判断
- 过度依赖测试结果，忽略了问题本质
- 试错循环导致偏离正确方向

**Run-Full 成功但 Run-Free 失败的案例（21 个）**:
- django__django-11797
- django__django-12470
- django__django-14997
- ...

**可能原因**:
- 需要执行反馈来确认环境配置
- 问题需要动态调试才能定位
- 推理能力不足以完全理解问题

### 4. 失败模式对开发者负担的影响

**Run-Full 模式的失败特点**:
- 更多的执行历史需要 review
- 可能存在多次修改尝试
- trace 文件更长，调试信息更多

**Run-Free 模式的失败特点**:
- 失败原因更直接（推理错误）
- 没有执行历史干扰
- 更容易定位问题根源

### 5. 开发者 Review 负担对比

| 指标 | Run-Free | Run-Full |
|------|----------|----------|
| 平均 trace 长度 | 短 | 长 |
| 执行历史 | 无 | 有 |
| 失败原因定位 | 容易 | 复杂 |
| 修复建议清晰度 | 高 | 中 |

## 结论

1. **失败模式差异不大**
   - Run-Free 和 Run-Full 的失败数量接近
   - 执行权限并未显著改变失败率

2. **执行反馈是双刃剑**
   - 16 个案例中，执行反馈反而导致失败
   - 21 个案例中，执行反馈帮助成功
   - 净收益仅 5 个案例

3. **开发者负担**
   - Run-Free 失败更容易调试（trace 短，原因直接）
   - Run-Full 失败需要更多 review 时间

4. **建议**
   - 对于简单问题，优先使用 Run-Free
   - 对于需要环境验证的问题，使用 Run-Full
   - 失败后的调试策略应根据模式调整
