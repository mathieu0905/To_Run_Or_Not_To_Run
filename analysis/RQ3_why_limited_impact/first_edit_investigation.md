# 首次编辑命中率差异分析

*Generated: 2026-01-28 16:21:18*

## 问题

为什么 P→P 案例中 Unrestricted 模式的首次编辑命中率（55.2%）远低于 Prohibited 模式（95.7%）？

## 假设

**Unrestricted 模式下 Agent 会先编辑测试文件/调试脚本，而不是直接编辑源代码文件。**

## 验证结果

| Agent | Mode | Total | 首次编辑是测试文件 | 首次编辑是源代码 | 首次编辑命中 GT |
|-------|------|-------|-------------------|-----------------|-----------------|
| claude_code | Unrestricted | 116 | 52 (44.8%) | 64 (55.2%) | 64 (55.2%) |
| claude_code | Prohibited | 116 | 3 (2.6%) | 113 (97.4%) | 111 (95.7%) |
| codex | Unrestricted | 142 | 3 (2.1%) | 139 (97.9%) | 137 (96.5%) |
| codex | Prohibited | 142 | 2 (1.4%) | 140 (98.6%) | 136 (95.8%) |

## 分析

### Claude Code

- **Unrestricted** 模式：44.8% 的首次编辑是测试/调试文件
- **Prohibited** 模式：2.6% 的首次编辑是测试/调试文件

**结论**：假设验证！Unrestricted 模式下 Agent 倾向于先编辑测试文件进行问题复现，
这导致首次编辑命中率显著低于 Prohibited 模式。

## 未命中示例

### claude_code - Unrestricted

**django__django-10914**
- 首次编辑: `test_permissions.py` (测试文件: True)
- GT 文件: `django/conf/global_settings.py`

**django__django-10924**
- 首次编辑: `test_callable_path.py` (测试文件: True)
- GT 文件: `django/db/models/fields/__init__.py`

**django__django-11815**
- 首次编辑: `test_enum_issue.py` (测试文件: True)
- GT 文件: `django/db/migrations/serializer.py`

### claude_code - Prohibited

**django__django-13401**
- 首次编辑: `test_field_equality.py` (测试文件: True)
- GT 文件: `django/db/models/fields/__init__.py`

**django__django-14017**
- 首次编辑: `django/db/models/expressions.py` (测试文件: False)
- GT 文件: `django/db/models/query_utils.py`

**django__django-15213**
- 首次编辑: `django/db/models/expressions.py` (测试文件: False)
- GT 文件: `django/db/models/fields/__init__.py`

### codex - Unrestricted

**django__django-13033**
- 首次编辑: `tests/queries/models.py` (测试文件: False)
- GT 文件: `django/db/models/sql/compiler.py`

**django__django-13158**
- 首次编辑: `tests/queries/test_qs_combinators.py` (测试文件: True)
- GT 文件: `django/db/models/sql/query.py`

**django__django-11211**
- 首次编辑: `django/contrib/contenttypes/fields.py` (测试文件: False)
- GT 文件: `django/db/models/fields/__init__.py`

### codex - Prohibited

**django__django-10924**
- 首次编辑: `django/forms/fields.py` (测试文件: False)
- GT 文件: `django/db/models/fields/__init__.py`

**django__django-15061**
- 首次编辑: `django/forms/boundfield.py` (测试文件: False)
- GT 文件: `django/forms/widgets.py`

**django__django-11211**
- 首次编辑: `django/contrib/contenttypes/fields.py` (测试文件: False)
- GT 文件: `django/db/models/fields/__init__.py`

## 结论

首次编辑命中率的差异主要是由于**分析方法的问题**，而非 Agent 能力的差异：

1. **Unrestricted 模式**：Agent 先创建测试脚本复现问题，然后再修复源代码
2. **Prohibited 模式**：Agent 无法执行，直接编辑源代码

**因此，"首次编辑命中率"不应作为定位能力的指标**。应该使用：
- **最终编辑命中率**：所有编辑文件中是否包含 GT 文件
- **文件召回率**：GT 文件中有多少被 Agent 编辑到
