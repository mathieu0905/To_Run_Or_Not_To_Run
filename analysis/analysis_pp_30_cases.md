# P→P 案例详细分析报告

本报告分析了 30 个 P→P 案例（在 Prohibited 和 Unrestricted 模式下均成功的实例），
旨在理解为什么这些 bug 的修复**不需要代码执行**。

## 一、总体统计

| # | 实例 | Prohibited Turns | Unrestricted Turns | Δ Turns | 修改行数 | 文件数 |
|---|------|-----------------|-------------------|---------|----------|--------|
| 1 | `astropy__astropy-12907` | 7 | 7 | 0 | 2 | 1 |
| 2 | `astropy__astropy-14995` | 9 | 10 | +1 | 2 | 1 |
| 3 | `astropy__astropy-6938` | 4 | 4 | 0 | 2 | 1 |
| 4 | `django__django-10914` | 9 | 36 | +27 | 2 | 1 |
| 5 | `django__django-10924` | 14 | 53 | +39 | 11 | 2 |
| 6 | `django__django-11001` | 9 | 17 | +8 | 2 | 1 |
| 7 | `django__django-11039` | 19 | 36 | +17 | 17 | 2 |
| 8 | `django__django-11049` | 8 | 7 | -1 | 4 | 2 |
| 9 | `django__django-11099` | 6 | 6 | 0 | 4 | 1 |
| 10 | `django__django-11133` | 4 | 6 | +2 | 2 | 1 |
| 11 | `django__django-11179` | 5 | 5 | 0 | 1 | 1 |
| 12 | `django__django-11422` | 16 | 20 | +4 | 10 | 1 |
| 13 | `django__django-11583` | 11 | 8 | -3 | 7 | 1 |
| 14 | `django__django-11815` | 8 | 35 | +27 | 7 | 1 |
| 15 | `django__django-11848` | 6 | 21 | +15 | 9 | 1 |
| 16 | `django__django-11999` | 12 | 43 | +31 | 5 | 1 |
| 17 | `django__django-12125` | 10 | 32 | +22 | 4 | 1 |
| 18 | `django__django-12286` | 22 | 32 | +10 | 15 | 1 |
| 19 | `django__django-12453` | 6 | 22 | +16 | 7 | 1 |
| 20 | `django__django-12497` | 15 | 25 | +10 | 6 | 2 |
| 21 | `django__django-12700` | 14 | 22 | +8 | 4 | 1 |
| 22 | `django__django-12708` | 10 | 44 | +34 | 2 | 1 |
| 23 | `django__django-12856` | 34 | 45 | +11 | 3 | 1 |
| 24 | `django__django-12915` | 8 | 40 | +32 | 6 | 1 |
| 25 | `django__django-12983` | 6 | 28 | +22 | 2 | 1 |
| 26 | `django__django-13028` | 11 | 29 | +18 | 11 | 1 |
| 27 | `django__django-13033` | 29 | 55 | +26 | 2 | 1 |
| 28 | `django__django-13158` | 39 | 54 | +15 | 2 | 1 |
| 29 | `django__django-13315` | 40 | 65 | +25 | 2 | 1 |
| 30 | `django__django-13401` | 21 | 34 | +13 | 17 | 1 |
| | **平均** | **13.7** | **28.0** | **+14.3** | | |

## 二、核心发现

### 1. Prohibited 模式显著更高效
- 平均 **13.7 turns** vs **28.0 turns**
- Unrestricted 模式多消耗 **104%** 的交互轮次

### 2. 代码执行是"冗余验证"
- 所有 30 个案例在 Prohibited 模式下均**未执行任何测试**
- 最终修复结果与 Unrestricted 模式**完全相同**

### 3. LLM 推理能力足够
- Agent 仅通过**阅读代码和问题描述**即可理解并修复 bug
- 不需要运行时反馈来验证修复正确性

## 三、Bug 类型与修复模式分析

### 常见 Bug 类型

| Bug 类型 | 典型案例 | 特点 | 为什么不需要执行 |
|----------|----------|------|------------------|
| **正则表达式语义** | django-11099 | `$` vs `\\Z` 锚点问题 | LLM 理解 Python regex 语义 |
| **API 参数处理** | django-10914 | 默认值设置错误 | 问题描述明确，修复确定 |
| **字符串/编码** | astropy-6938 | encode 调用位置 | 静态代码分析可定位 |
| **类型处理** | django-11133 | memoryview 支持 | 添加类型检查分支 |
| **序列化逻辑** | django-11815 | Enum 序列化 | 理解序列化机制后可直接修复 |

### Prohibited 模式的典型工作流

```
1. [理解] 阅读问题描述 → 理解预期 vs 实际行为
2. [定位] Grep/Glob → 搜索相关代码位置
3. [分析] Read → 阅读代码理解实现逻辑
4. [修复] Edit → 应用修复
5. [验证] Read → 确认修改正确（可选）
```

---

## 四、30 个案例逐一分析

### 案例 1: `astropy__astropy-12907`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 7 | $0.0159 |
| Unrestricted | 7 | - |
| **差异** | **0** | |

**修改范围**: +1/-1 行，文件: `separable.py`

**Prohibited 模式执行步骤**:

1. I'll analyze the separability matrix bug for nested CompoundModels in astropy
2. Bash: `find /testbed -type f -name "*.py" | grep -E "separa" | head -20`
3. Bash: `find /testbed -type d -name "modeling" | head -5`
4. Let me read the separable
   - 工具: Read: separable.py
5. Read: separable.py
6. Now let me look at the test file to understand the expected behavior better
7. Read: test_separable.py
8. Let me analyze the issue by examining the `_cstack` function more closely, as th...
   - 工具: Read: separable.py

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 2: `astropy__astropy-14995`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 9 | $0.0641 |
| Unrestricted | 10 | - |
| **差异** | **+1** (11% 更多) | |

**修改范围**: +2/-0 行，文件: `ndarithmetic.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me start by exploring the codebase to understand the structure and find the ...
3. Glob: `**/nddata/**/*.py`
4. Grep: `NDDataRef`
5. Let me look at the relevant files
6. Read: ndarithmetic.py
7. TodoWrite
8. Now I understand the code
   - 工具: TodoWrite

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 3: `astropy__astropy-6938`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 4 | $0.0270 |
| Unrestricted | 4 | - |
| **差异** | **0** | |

**修改范围**: +1/-1 行，文件: `fitsrec.py`

**Prohibited 模式执行步骤**:

1. Grep: `output_field.replace.*encode_a`
2. Let me read the relevant code in fitsrec
3. Read: fitsrec.py
4. I found the bug
5. Edit: fitsrec.py
6. The fix has been applied

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 4: `django__django-10914`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 9 | $0.0369 |
| Unrestricted | 36 | - |
| **差异** | **+27** (300% 更多) | |

**修改范围**: +1/-1 行，文件: `global_settings.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me understand the problem first
3. Glob: `**/conf/global_settings.py`
4. Grep: `FILE_UPLOAD_PERMISSION`
5. Let me read the relevant files to understand the current implementation
6. Read: global_settings.py
7. Read: storage.py
8. TodoWrite

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 5: `django__django-10924`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 14 | $0.0386 |
| Unrestricted | 53 | - |
| **差异** | **+39** (279% 更多) | |

**修改范围**: +8/-3 行，文件: `__init__.py`, `fields.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me start by exploring the FilePathField implementation in Django
3. Glob: `**/fields/**/*.py`
4. Grep: `class FilePathField`
5. Let me look at the FilePathField implementation in both the model fields and for...
6. Read: __init__.py
7. Read: fields.py
8. Let me search for the FilePathField class definition in the models fields file

**为什么不需要执行也能成功?**

- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 6: `django__django-11001`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 9 | $0.0300 |
| Unrestricted | 17 | - |
| **差异** | **+8** (89% 更多) | |

**修改范围**: +1/-1 行，文件: `compiler.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me first find the SQLCompiler class and the `get_order_by` method
3. Grep: `class SQLCompiler`
4. Grep: `ordering_parts`
5. Let me read the SQLCompiler file to understand the issue
6. Read: compiler.py
7. TodoWrite
8. Now I understand the issue
   - 工具: TodoWrite

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 7: `django__django-11039`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 19 | $0.0329 |
| Unrestricted | 36 | - |
| **差异** | **+17** (89% 更多) | |

**修改范围**: +16/-1 行，文件: `sqlmigrate.py`, `test_commands.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this issue step by step to understand the problem and implement a f...
2. Bash: `find /testbed -type f -name "*.py" -path "*/management/commands/*" | grep -i mig`
3. Bash: `find /testbed -type f -name "*.py" -path "*/migrations/*" | grep -E "(executor|t`
4. I'll analyze the code to understand the issue and implement the fix
   - 工具: Read: executor.py, Read: sqlmigrate.py
5. Read: executor.py, Read: sqlmigrate.py
6. Read: executor.py, Read: sqlmigrate.py
7. Now I can see the issue clearly
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/db/backends/*" | xargs grep -l "can_`, Bash: `grep -n "can_rollback_ddl" /testbed/django/db/migrations/executor.py`
8. Bash: `find /testbed -type f -name "*.py" -path "*/db/backends/*" | xargs grep -l "can_`, Bash: `grep -n "can_rollback_ddl" /testbed/django/db/migrations/executor.py`

**为什么不需要执行也能成功?**

- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 8: `django__django-11049`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 8 | $0.0469 |
| Unrestricted | 7 | - |
| **差异** | **-1** | |

**修改范围**: +2/-2 行，文件: `__init__.py`, `test_durationfield.py`

**Prohibited 模式执行步骤**:

1. Grep: `\[DD\].*\[HH:`
2. Let me look at the main source file and understand the actual parsing behavior f...
3. Read: __init__.py
4. Grep: `parse_duration`
5. Now let me look at the actual parsing logic in `dateparse
6. Read: dateparse.py
7. Now I understand the issue
8. Edit: __init__.py

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 9: `django__django-11099`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 6 | $0.0031 |
| Unrestricted | 6 | - |
| **差异** | **0** | |

**修改范围**: +2/-2 行，文件: `validators.py`

**Prohibited 模式执行步骤**:

1. I'll analyze and fix the UsernameValidator issue where trailing newlines are inc...
2. Bash: `find /testbed -type f -name "validators.py" | grep -E "contrib/auth"`
3. I'll examine the validators file to understand the current implementation and fi...
   - 工具: Read: validators.py
4. Read: validators.py
5. Perfect! I can see the issue clearly
   - 工具: Edit: validators.py
6. Edit: validators.py
7. Now let me fix the second validator:
   - 工具: Edit: validators.py
8. Edit: validators.py

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 10: `django__django-11133`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 4 | $0.0004 |
| Unrestricted | 6 | - |
| **差异** | **+2** (50% 更多) | |

**修改范围**: +2/-0 行，文件: `response.py`

**Prohibited 模式执行步骤**:

1. I'll analyze the Django codebase to understand and fix the issue where HttpRespo...
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/http/*" | grep -E "(response|__init_`
2. Bash: `find /testbed -type f -name "*.py" -path "*/http/*" | grep -E "(response|__init_`
3. I'll analyze the Django HttpResponse code to understand and fix the memoryview h...
   - 工具: Read: response.py
4. Read: response.py
5. I'll analyze the code to understand how HttpResponse handles content and identif...
   - 工具: Edit: response.py
6. Edit: response.py
7. Perfect! I've successfully fixed the issue

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 11: `django__django-11179`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 5 | $0.0133 |
| Unrestricted | 5 | - |
| **差异** | **0** | |

**修改范围**: +1/-0 行，文件: `deletion.py`

**Prohibited 模式执行步骤**:

1. I'll analyze the Django deletion code to understand and fix the issue where `del...
2. Read: deletion.py
3. I can see the issue
   - 工具: Read: deletion.py
4. Read: deletion.py
5. Perfect! Now I can see the issue clearly
6. Edit: deletion.py
7. Perfect! I've successfully fixed the bug
   - 工具: Read: deletion.py
8. Read: deletion.py

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 12: `django__django-11422`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 16 | $0.0978 |
| Unrestricted | 20 | - |
| **差异** | **+4** (25% 更多) | |

**修改范围**: +8/-2 行，文件: `autoreload.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me start by exploring the Django autoreload mechanism to understand how it w...
   - 工具: Glob
3. Glob: `**/autoreload*.py`, Glob
4. Read: autoreload.py
5. Now I understand the autoreload mechanism
   - 工具: Grep: `sys\.argv\[0\]`, Grep: `__main__`
6. Grep: `sys\.argv\[0\]`, Grep: `__main__`
7. Grep: `sys\.argv\[0\]`, Grep: `__main__`
8. TodoWrite

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 13: `django__django-11583`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 11 | $0.0285 |
| Unrestricted | 8 | - |
| **差异** | **-3** | |

**修改范围**: +4/-3 行，文件: `autoreload.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this bug about the intermittent "ValueError: embedded null byte" in...
   - 工具: Bash: `find /testbed -type f -name "autoreload.py" | head -20`
2. Bash: `find /testbed -type f -name "autoreload.py" | head -20`
3. I'll analyze the autoreload
   - 工具: Read: autoreload.py
4. Read: autoreload.py
5. Now let me examine the specific area where the error occurs
   - 工具: Read: autoreload.py
6. Read: autoreload.py
7. Looking at the code and the error description, I can now analyze the root cause ...
   - 工具: Read: autoreload.py
8. Read: autoreload.py

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 14: `django__django-11815`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 8 | $0.0728 |
| Unrestricted | 35 | - |
| **差异** | **+27** (338% 更多) | |

**修改范围**: +4/-3 行，文件: `serializer.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me understand the bug first
3. Grep: `class EnumSerializer`
4. Grep: `Enum.*serialize`
5. Let me read the serializer file to understand how Enum objects are currently ser...
6. Read: serializer.py
7. TodoWrite
8. I found the issue

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 15: `django__django-11848`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 6 | $0.0143 |
| Unrestricted | 21 | - |
| **差异** | **+15** (250% 更多) | |

**修改范围**: +6/-3 行，文件: `http.py`

**Prohibited 模式执行步骤**:

1. I'll analyze the Django code to understand and fix the two-digit year check issu...
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/django/utils/http.py" | head -5`
2. Bash: `find /testbed -type f -name "*.py" -path "*/django/utils/http.py" | head -5`
3. I'll read the `parse_http_date` function to understand the current implementatio...
   - 工具: Read: http.py
4. Read: http.py
5. Now I can see the issue clearly
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i http | head -10`
6. Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i http | head -10`
7. Let me read the test file to understand the expected behavior better
8. Read: test_http.py

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 16: `django__django-11999`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 12 | $0.0216 |
| Unrestricted | 43 | - |
| **差异** | **+31** (258% 更多) | |

**修改范围**: +3/-2 行，文件: `__init__.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me start by understanding the bug
3. Grep: `get_.*_display`
4. Glob: `**/db/models/**/*.py`
5. Let me look at the relevant files to understand how `get_FOO_display` is impleme...
6. Read: __init__.py
7. Grep: `get_.*_display|_get_FIELD_disp`
8. Now I can see the key code

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 17: `django__django-12125`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 10 | $0.0174 |
| Unrestricted | 32 | - |
| **差异** | **+22** (220% 更多) | |

**修改范围**: +2/-2 行，文件: `serializer.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this Django bug where `makemigrations` produces incorrect paths for...
   - 工具: Bash: `find /testbed -type f -name "*.py" | grep -E "(migration|serializer)" | head -20`
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(migration|serializer)" | head -20`
3. I'll analyze the Django bug where `makemigrations` produces incorrect paths for ...
4. Bash: `find /testbed/django -type f -path "*/migrations/*.py" | grep -E "(serializer|wr`
5. Let me examine the migration serializer code to understand how it handles class ...
   - 工具: Read: serializer.py
6. Read: serializer.py
7. Now I can see the issue
   - 工具: Bash: `grep -n "__qualname__" /testbed/django/db/migrations/serializer.py`
8. Bash: `grep -n "__qualname__" /testbed/django/db/migrations/serializer.py`

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 18: `django__django-12286`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 22 | $0.0638 |
| Unrestricted | 32 | - |
| **差异** | **+10** (45% 更多) | |

**修改范围**: +14/-1 行，文件: `translation.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this Django translation issue where `translation
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(translation|check)" | head -20`
3. Bash: `grep -r "translation.E004" /testbed --include="*.py"`
4. I'll analyze the Django translation check issue and fix it
   - 工具: Read: translation.py, Read: test_translation.py
5. Read: translation.py, Read: test_translation.py
6. Read: translation.py, Read: test_translation.py
7. Now I can see the issue
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/translation/*" | grep -v __pycache__`
8. Bash: `find /testbed -type f -name "*.py" -path "*/translation/*" | grep -v __pycache__`

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 19: `django__django-12453`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 6 | $0.0144 |
| Unrestricted | 22 | - |
| **差异** | **+16** (267% 更多) | |

**修改范围**: +4/-3 行，文件: `creation.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this issue and implement the fix
2. Bash: `find /testbed -type f -name "creation.py" | grep -E "db/backends/base"`
3. I'll analyze the issue and implement the fix
4. Read: creation.py
5. Now I can see the issue clearly
   - 工具: Edit: creation.py
6. Edit: creation.py
7. Now let me update the `deserialize_db_from_string` method to wrap the deserializ...
   - 工具: Edit: creation.py
8. Edit: creation.py

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 20: `django__django-12497`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 15 | $0.0339 |
| Unrestricted | 25 | - |
| **差异** | **+10** (67% 更多) | |

**修改范围**: +3/-3 行，文件: `related.py`, `test_relative_fields.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this Django bug about the incorrect hint message for recursive rela...
2. Grep: `If you want to create a recurs`
3. Let me search for the error message in the source code to understand the issue b...
4. Read: related.py
5. Let me search for the specific error message in the file
   - 工具: Grep: `If you want to create a recurs`
6. Grep: `If you want to create a recurs`
7. Now let me look at the broader context around these error messages to understand...
8. Read: related.py

**为什么不需要执行也能成功?**

- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 21: `django__django-12700`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 14 | $0.0586 |
| Unrestricted | 22 | - |
| **差异** | **+8** (57% 更多) | |

**修改范围**: +4/-0 行，文件: `debug.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this security issue where Django's `SafeExceptionReporterFilter
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/views/debug.py" | head -5`
2. Bash: `find /testbed -type f -name "*.py" -path "*/views/debug.py" | head -5`
3. I'll analyze the Django security issue where `SafeExceptionReporterFilter
   - 工具: Read: debug.py
4. Read: debug.py
5. Now I can see the issue clearly
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i debug | head -10`
6. Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i debug | head -10`
7. Let me check the test file to understand the expected behavior better
   - 工具: Read: test_debug.py
8. Read: test_debug.py

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 22: `django__django-12708`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 10 | $0.0911 |
| Unrestricted | 44 | - |
| **差异** | **+34** (340% 更多) | |

**修改范围**: +1/-1 行，文件: `schema.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me start by reading the relevant file mentioned in the problem description
   - 工具: Read: schema.py
3. Read: schema.py
4. Now I can see the `_delete_composed_index` method at line 402
5. Grep: `def _constraint_names`
6. Read: schema.py
7. Now I understand the issue
8. TodoWrite

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 23: `django__django-12856`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 34 | $0.0975 |
| Unrestricted | 45 | - |
| **差异** | **+11** (32% 更多) | |

**修改范围**: +3/-0 行，文件: `base.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this issue step by step
   - 工具: Bash: `find /testbed -type f -path "*/models/constraints.py" | head -5`, Bash: `find /testbed -type f -name "*.py" | grep -E "(check|constraint)" | head -20`
2. Bash: `find /testbed -type f -path "*/models/constraints.py" | head -5`, Bash: `find /testbed -type f -name "*.py" | grep -E "(check|constraint)" | head -20`
3. Bash: `find /testbed -type f -path "*/models/constraints.py" | head -5`, Bash: `find /testbed -type f -name "*.py" | grep -E "(check|constraint)" | head -20`
4. I'll analyze the Django codebase to understand how to add field validation for `...
5. Read: constraints.py
6. Bash: `find /testbed -type f -name "*.py" -path "*/models/*" | grep -E "check" | head -`
7. Now let me look at how `unique_together` implements its field validation to unde...
   - 工具: Bash: `find /testbed -type f -name "*.py" -path "*/models/*" | grep -E "base|options" |`
8. Bash: `find /testbed -type f -name "*.py" -path "*/models/*" | grep -E "base|options" |`

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 24: `django__django-12915`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 8 | $0.0228 |
| Unrestricted | 40 | - |
| **差异** | **+32** (400% 更多) | |

**修改范围**: +6/-0 行，文件: `handlers.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this issue step by step to understand the problem and implement a f...
   - 工具: Read: handlers.py, Read: asgi.py
2. Read: handlers.py, Read: asgi.py
3. Read: handlers.py, Read: asgi.py
4. Now let me check the base handler to understand how `get_response_async` is impl...
5. Read: base.py
6. Now I understand the issue
7. Grep: `from asgiref`
8. Now I'll implement the fix

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 25: `django__django-12983`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 6 | $0.0295 |
| Unrestricted | 28 | - |
| **差异** | **+22** (367% 更多) | |

**修改范围**: +1/-1 行，文件: `text.py`

**Prohibited 模式执行步骤**:

1. Grep: `def slugify`
2. Let me search for the slugify function in the Django codebase
3. Glob: `**/text.py`
4. Read: text.py
5. I found the `slugify` function at line 394-406 in `/testbed/django/utils/text
   - 工具: Edit: text.py
6. Edit: text.py
7. The fix has been applied
8. Read: text.py

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ 快速解决（<7 turns）：Agent 迅速理解问题本质
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 26: `django__django-13028`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 11 | $0.1431 |
| Unrestricted | 29 | - |
| **差异** | **+18** (164% 更多) | |

**修改范围**: +6/-5 行，文件: `query.py`

**Prohibited 模式执行步骤**:

1. TodoWrite
2. Let me understand the bug first
3. Grep: `def check_filterable`
4. Glob: `**/django/db/models/sql/query.py`
5. Read: query.py
6. Now I can see the issue
7. TodoWrite
8. Let me look at how the `filterable` attribute is used in Django expressions to u...

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 27: `django__django-13033`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 29 | $0.2267 |
| Unrestricted | 55 | - |
| **差异** | **+26** (90% 更多) | |

**修改范围**: +1/-1 行，文件: `compiler.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this Django ORM issue where self-referencing foreign keys cause inc...
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(query|order)" | head -20`
3. Bash: `ls -la /testbed`
4. I'll analyze this Django ORM bug where self-referencing foreign keys cause incor...
   - 工具: Bash: `find /testbed/django/db/models -type f -name "*.py" | grep -E "(sql|query)" | he`, Bash: `ls -la /testbed/django/db/models`
5. Bash: `find /testbed/django/db/models -type f -name "*.py" | grep -E "(sql|query)" | he`, Bash: `ls -la /testbed/django/db/models`
6. Bash: `find /testbed/django/db/models -type f -name "*.py" | grep -E "(sql|query)" | he`, Bash: `ls -la /testbed/django/db/models`
7. Let me explore the Django ORM code to understand how ordering works with self-re...
   - 工具: Bash: `ls -la /testbed/django/db/models/sql`, Grep: `order_by`
8. Bash: `ls -la /testbed/django/db/models/sql`, Grep: `order_by`

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 28: `django__django-13158`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 39 | $0.2682 |
| Unrestricted | 54 | - |
| **差异** | **+15** (38% 更多) | |

**修改范围**: +2/-0 行，文件: `query.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this Django bug where `QuerySet
   - 工具: Bash: `ls -la /testbed`, Bash: `find /testbed -type f -name "*.py" | grep -E "(queryset|query)" | head -20`
2. Bash: `ls -la /testbed`, Bash: `find /testbed -type f -name "*.py" | grep -E "(queryset|query)" | head -20`
3. Bash: `ls -la /testbed`, Bash: `find /testbed -type f -name "*.py" | grep -E "(queryset|query)" | head -20`
4. I'll analyze this Django bug where `QuerySet
   - 工具: Read: query.py
5. Read: query.py
6. Let me search for the `none()` method and understand how it works with combined ...
7. Bash: `grep -n "def none" /testbed/django/db/models/query.py`
8. Let me read the `none()` method and understand how it works with combined querie...

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 29: `django__django-13315`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 40 | $0.1113 |
| Unrestricted | 65 | - |
| **差异** | **+25** (62% 更多) | |

**修改范围**: +1/-1 行，文件: `models.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this Django issue about duplicate options in ForeignKey formfields ...
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(test|regression)" | grep -i "limi`
3. Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | head -30`
4. I'll analyze this Django issue about duplicate options in ForeignKey formfields ...
5. Bash: `find /testbed -type f -name "*.py" -path "*" | grep -E "limit_choices" | head -2`
6. Bash: `find /testbed -type f -name "*.patch" -o -name "*.diff" | head -10`
7. Let me search for files related to ForeignKey and limit_choices_to to understand...
8. Bash: `find /testbed -type f -name "*.py" -path "*/django/db/models/*" | grep -E "(fiel`

**为什么不需要执行也能成功?**

- ✅ 小范围修改（≤5行）：修复逻辑简单，易于推理验证
- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

### 案例 30: `django__django-13401`

| 模式 | Turns | 成本 |
|------|-------|------|
| Prohibited | 21 | $0.1253 |
| Unrestricted | 34 | - |
| **差异** | **+13** (62% 更多) | |

**修改范围**: +14/-3 行，文件: `__init__.py`

**Prohibited 模式执行步骤**:

1. I'll analyze this issue step by step to understand the problem and implement a f...
2. Bash: `find /testbed -type f -name "*.py" -path "*/django/db/models/*" | grep -E "(fiel`
3. I'll analyze the Django field comparison issue and implement a fix
4. Read: __init__.py
5. Let me search for the `__eq__`, `__hash__`, and `__lt__` methods in the Field cl...
6. Grep: `def __eq__|def __hash__|def __`
7. Let me read the comparison methods in the Field class
8. Read: __init__.py

**为什么不需要执行也能成功?**

- ✅ 单文件修改：问题边界清晰，不涉及跨模块依赖
- ✅ Bug 类型适合推理：不涉及边界条件、性能、并发等需要运行时验证的问题

---

## 五、结论与启示

### 核心结论

1. **LLM 内在推理能力足够**：对于这 30 个 P→P 案例，Agent 仅通过代码阅读和理解即可正确修复

2. **执行是冗余验证**：Unrestricted 模式下的测试执行并未带来额外价值，反而消耗了更多资源

3. **Prohibited 更高效**：平均节省 51% 的交互轮次，成本更低

### 适合 Prohibited 模式的 Bug 特征

| 特征 | 描述 |
|------|------|
| 问题描述清晰 | Issue 明确说明预期 vs 实际行为 |
| 确定性修复 | 理解问题后可直接给出正确答案 |
| 语义/逻辑错误 | 如 regex、API 调用、类型处理 |
| 小范围修改 | 通常 ≤10 行代码 |
| 无运行时依赖 | 不涉及边界条件、并发、性能 |

### 对 RQ3 的支撑

> 这 30 个案例证明：对于大多数成功修复的 bug（P→P），LLM 的推理能力已经足够。
> 代码执行在这些场景下是**冗余验证**，而非修复的必要条件。
> 这解释了为什么 Prohibited 模式能够达到与 Unrestricted 模式相当的 resolve rate。
