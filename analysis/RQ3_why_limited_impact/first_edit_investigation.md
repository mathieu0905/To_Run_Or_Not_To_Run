# First Edit Hit Rate Difference Analysis

*Generated: 2026-01-28 16:21:18*

## Problem

Why is the first edit hit rate in P→P cases much lower in Unrestricted mode (55.2%) than in Prohibited mode (95.7%)?

## Hypothesis

**In Unrestricted mode, Agent tends to edit test files/debug scripts first, rather than directly editing source code files.**

## Verification Results

| Agent | Mode | Total | First Edit is Test File | First Edit is Source Code | First Edit Hits GT |
|-------|------|-------|-------------------|-----------------|-----------------|
| claude_code | Unrestricted | 116 | 52 (44.8%) | 64 (55.2%) | 64 (55.2%) |
| claude_code | Prohibited | 116 | 3 (2.6%) | 113 (97.4%) | 111 (95.7%) |
| codex | Unrestricted | 142 | 3 (2.1%) | 139 (97.9%) | 137 (96.5%) |
| codex | Prohibited | 142 | 2 (1.4%) | 140 (98.6%) | 136 (95.8%) |

## Analysis

### Claude Code

- **Unrestricted** mode: 44.8% of first edits are test/debug files
- **Prohibited** mode: 2.6% of first edits are test/debug files

**Conclusion**: Hypothesis verified! In Unrestricted mode, Agent tends to edit test files first to reproduce the problem,
which leads to significantly lower first edit hit rate compared to Prohibited mode.

## Miss Examples

### claude_code - Unrestricted

**django__django-10914**
- First edit: `test_permissions.py` (Test file: True)
- GT file: `django/conf/global_settings.py`

**django__django-10924**
- First edit: `test_callable_path.py` (Test file: True)
- GT file: `django/db/models/fields/__init__.py`

**django__django-11815**
- First edit: `test_enum_issue.py` (Test file: True)
- GT file: `django/db/migrations/serializer.py`

### claude_code - Prohibited

**django__django-13401**
- First edit: `test_field_equality.py` (Test file: True)
- GT file: `django/db/models/fields/__init__.py`

**django__django-14017**
- First edit: `django/db/models/expressions.py` (Test file: False)
- GT file: `django/db/models/query_utils.py`

**django__django-15213**
- First edit: `django/db/models/expressions.py` (Test file: False)
- GT file: `django/db/models/fields/__init__.py`

### codex - Unrestricted

**django__django-13033**
- First edit: `tests/queries/models.py` (Test file: False)
- GT file: `django/db/models/sql/compiler.py`

**django__django-13158**
- First edit: `tests/queries/test_qs_combinators.py` (Test file: True)
- GT file: `django/db/models/sql/query.py`

**django__django-11211**
- First edit: `django/contrib/contenttypes/fields.py` (Test file: False)
- GT file: `django/db/models/fields/__init__.py`

### codex - Prohibited

**django__django-10924**
- First edit: `django/forms/fields.py` (Test file: False)
- GT file: `django/db/models/fields/__init__.py`

**django__django-15061**
- First edit: `django/forms/boundfield.py` (Test file: False)
- GT file: `django/forms/widgets.py`

**django__django-11211**
- First edit: `django/contrib/contenttypes/fields.py` (Test file: False)
- GT file: `django/db/models/fields/__init__.py`

## Conclusion

The difference in first edit hit rate is mainly due to **analysis methodology issues**, not differences in Agent capability:

1. **Unrestricted mode**: Agent creates test scripts first to reproduce the problem, then fixes source code
2. **Prohibited mode**: Agent cannot execute, so directly edits source code

**Therefore, "first edit hit rate" should not be used as an indicator of localization capability**. Should use:
- **Final edit hit rate**: Whether all edited files include GT files
- **File recall rate**: How many GT files were edited by Agent
