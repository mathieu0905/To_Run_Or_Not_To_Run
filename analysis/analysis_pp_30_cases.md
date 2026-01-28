# P→P Case Detailed Analysis Report

This report analyzes 30 P→P cases (instances that succeeded in both Prohibited and Unrestricted modes),
aiming to understand why fixing these bugs **does not require code execution**.

## 1. Overall Statistics

| # | Instance | Prohibited Turns | Unrestricted Turns | Δ Turns | Lines Changed | Files |
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
| | **Average** | **13.7** | **28.0** | **+14.3** | | |

## 2. Core Findings

### 1. Prohibited Mode is Significantly More Efficient
- Average **13.7 turns** vs **28.0 turns**
- Unrestricted mode consumes **104%** more interaction turns

### 2. Code Execution is "Redundant Verification"
- All 30 cases **did not execute any tests** in Prohibited mode
- Final fix results are **identical** to Unrestricted mode

### 3. LLM Reasoning Capability is Sufficient
- Agent can understand and fix bugs solely by **reading code and problem descriptions**
- No runtime feedback needed to verify fix correctness

## 3. Bug Types and Fix Pattern Analysis

### Common Bug Types

| Bug Type | Typical Case | Characteristics | Why Execution Not Needed |
|----------|--------------|-----------------|--------------------------|
| **Regex Semantics** | django-11099 | `$` vs `\\Z` anchor issue | LLM understands Python regex semantics |
| **API Parameter Handling** | django-10914 | Incorrect default value | Clear problem description, deterministic fix |
| **String/Encoding** | astropy-6938 | encode call position | Static code analysis can locate |
| **Type Handling** | django-11133 | memoryview support | Add type check branch |
| **Serialization Logic** | django-11815 | Enum serialization | Can fix directly after understanding serialization mechanism |

### Typical Workflow in Prohibited Mode

```
1. [Understand] Read problem description → Understand expected vs actual behavior
2. [Locate] Grep/Glob → Search for relevant code locations
3. [Analyze] Read → Read code to understand implementation logic
4. [Fix] Edit → Apply fix
5. [Verify] Read → Confirm modification is correct (optional)
```

---

## 4. Analysis of All 30 Cases

### Case 1: `astropy__astropy-12907`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 7 | $0.0159 |
| Unrestricted | 7 | - |
| **Difference** | **0** | |

**Scope of Changes**: +1/-1 lines, File: `separable.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze the separability matrix bug for nested CompoundModels in astropy
2. Bash: `find /testbed -type f -name "*.py" | grep -E "separa" | head -20`
3. Bash: `find /testbed -type d -name "modeling" | head -5`
4. Let me read the separable
   - Tool: Read: separable.py
5. Read: separable.py
6. Now let me look at the test file to understand the expected behavior better
7. Read: test_separable.py
8. Let me analyze the issue by examining the `_cstack` function more closely, as th...
   - Tool: Read: separable.py

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 2: `astropy__astropy-14995`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 9 | $0.0641 |
| Unrestricted | 10 | - |
| **Difference** | **+1** (11% more) | |

**Scope of Changes**: +2/-0 lines, File: `ndarithmetic.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me start by exploring the codebase to understand the structure and find the ...
3. Glob: `**/nddata/**/*.py`
4. Grep: `NDDataRef`
5. Let me look at the relevant files
6. Read: ndarithmetic.py
7. TodoWrite
8. Now I understand the code
   - Tool: TodoWrite

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 3: `astropy__astropy-6938`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 4 | $0.0270 |
| Unrestricted | 4 | - |
| **Difference** | **0** | |

**Scope of Changes**: +1/-1 lines, File: `fitsrec.py`

**Prohibited Mode Execution Steps**:

1. Grep: `output_field.replace.*encode_a`
2. Let me read the relevant code in fitsrec
3. Read: fitsrec.py
4. I found the bug
5. Edit: fitsrec.py
6. The fix has been applied

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 4: `django__django-10914`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 9 | $0.0369 |
| Unrestricted | 36 | - |
| **Difference** | **+27** (300% more) | |

**Scope of Changes**: +1/-1 lines, File: `global_settings.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me understand the problem first
3. Glob: `**/conf/global_settings.py`
4. Grep: `FILE_UPLOAD_PERMISSION`
5. Let me read the relevant files to understand the current implementation
6. Read: global_settings.py
7. Read: storage.py
8. TodoWrite

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 5: `django__django-10924`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 14 | $0.0386 |
| Unrestricted | 53 | - |
| **Difference** | **+39** (279% more) | |

**Scope of Changes**: +8/-3 lines, Files: `__init__.py`, `fields.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me start by exploring the FilePathField implementation in Django
3. Glob: `**/fields/**/*.py`
4. Grep: `class FilePathField`
5. Let me look at the FilePathField implementation in both the model fields and for...
6. Read: __init__.py
7. Read: fields.py
8. Let me search for the FilePathField class definition in the models fields file

**Why Can It Succeed Without Execution?**

- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 6: `django__django-11001`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 9 | $0.0300 |
| Unrestricted | 17 | - |
| **Difference** | **+8** (89% more) | |

**Scope of Changes**: +1/-1 lines, File: `compiler.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me first find the SQLCompiler class and the `get_order_by` method
3. Grep: `class SQLCompiler`
4. Grep: `ordering_parts`
5. Let me read the SQLCompiler file to understand the issue
6. Read: compiler.py
7. TodoWrite
8. Now I understand the issue
   - Tool: TodoWrite

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 7: `django__django-11039`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 19 | $0.0329 |
| Unrestricted | 36 | - |
| **Difference** | **+17** (89% more) | |

**Scope of Changes**: +16/-1 lines, Files: `sqlmigrate.py`, `test_commands.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this issue step by step to understand the problem and implement a f...
2. Bash: `find /testbed -type f -name "*.py" -path "*/management/commands/*" | grep -i mig`
3. Bash: `find /testbed -type f -name "*.py" -path "*/migrations/*" | grep -E "(executor|t`
4. I'll analyze the code to understand the issue and implement the fix
   - Tool: Read: executor.py, Read: sqlmigrate.py
5. Read: executor.py, Read: sqlmigrate.py
6. Read: executor.py, Read: sqlmigrate.py
7. Now I can see the issue clearly
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/db/backends/*" | xargs grep -l "can_`, Bash: `grep -n "can_rollback_ddl" /testbed/django/db/migrations/executor.py`
8. Bash: `find /testbed -type f -name "*.py" -path "*/db/backends/*" | xargs grep -l "can_`, Bash: `grep -n "can_rollback_ddl" /testbed/django/db/migrations/executor.py`

**Why Can It Succeed Without Execution?**

- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 8: `django__django-11049`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 8 | $0.0469 |
| Unrestricted | 7 | - |
| **Difference** | **-1** | |

**Scope of Changes**: +2/-2 lines, Files: `__init__.py`, `test_durationfield.py`

**Prohibited Mode Execution Steps**:

1. Grep: `\[DD\].*\[HH:`
2. Let me look at the main source file and understand the actual parsing behavior f...
3. Read: __init__.py
4. Grep: `parse_duration`
5. Now let me look at the actual parsing logic in `dateparse
6. Read: dateparse.py
7. Now I understand the issue
8. Edit: __init__.py

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 9: `django__django-11099`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 6 | $0.0031 |
| Unrestricted | 6 | - |
| **Difference** | **0** | |

**Scope of Changes**: +2/-2 lines, File: `validators.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze and fix the UsernameValidator issue where trailing newlines are inc...
2. Bash: `find /testbed -type f -name "validators.py" | grep -E "contrib/auth"`
3. I'll examine the validators file to understand the current implementation and fi...
   - Tool: Read: validators.py
4. Read: validators.py
5. Perfect! I can see the issue clearly
   - Tool: Edit: validators.py
6. Edit: validators.py
7. Now let me fix the second validator:
   - Tool: Edit: validators.py
8. Edit: validators.py

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 10: `django__django-11133`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 4 | $0.0004 |
| Unrestricted | 6 | - |
| **Difference** | **+2** (50% more) | |

**Scope of Changes**: +2/-0 lines, File: `response.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze the Django codebase to understand and fix the issue where HttpRespo...
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/http/*" | grep -E "(response|__init_`
2. Bash: `find /testbed -type f -name "*.py" -path "*/http/*" | grep -E "(response|__init_`
3. I'll analyze the Django HttpResponse code to understand and fix the memoryview h...
   - Tool: Read: response.py
4. Read: response.py
5. I'll analyze the code to understand how HttpResponse handles content and identif...
   - Tool: Edit: response.py
6. Edit: response.py
7. Perfect! I've successfully fixed the issue

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 11: `django__django-11179`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 5 | $0.0133 |
| Unrestricted | 5 | - |
| **Difference** | **0** | |

**Scope of Changes**: +1/-0 lines, File: `deletion.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze the Django deletion code to understand and fix the issue where `del...
2. Read: deletion.py
3. I can see the issue
   - Tool: Read: deletion.py
4. Read: deletion.py
5. Perfect! Now I can see the issue clearly
6. Edit: deletion.py
7. Perfect! I've successfully fixed the bug
   - Tool: Read: deletion.py
8. Read: deletion.py

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 12: `django__django-11422`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 16 | $0.0978 |
| Unrestricted | 20 | - |
| **Difference** | **+4** (25% more) | |

**Scope of Changes**: +8/-2 lines, File: `autoreload.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me start by exploring the Django autoreload mechanism to understand how it w...
   - Tool: Glob
3. Glob: `**/autoreload*.py`, Glob
4. Read: autoreload.py
5. Now I understand the autoreload mechanism
   - Tool: Grep: `sys\.argv\[0\]`, Grep: `__main__`
6. Grep: `sys\.argv\[0\]`, Grep: `__main__`
7. Grep: `sys\.argv\[0\]`, Grep: `__main__`
8. TodoWrite

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 13: `django__django-11583`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 11 | $0.0285 |
| Unrestricted | 8 | - |
| **Difference** | **-3** | |

**Scope of Changes**: +4/-3 lines, File: `autoreload.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this bug about the intermittent "ValueError: embedded null byte" in...
   - Tool: Bash: `find /testbed -type f -name "autoreload.py" | head -20`
2. Bash: `find /testbed -type f -name "autoreload.py" | head -20`
3. I'll analyze the autoreload
   - Tool: Read: autoreload.py
4. Read: autoreload.py
5. Now let me examine the specific area where the error occurs
   - Tool: Read: autoreload.py
6. Read: autoreload.py
7. Looking at the code and the error description, I can now analyze the root cause ...
   - Tool: Read: autoreload.py
8. Read: autoreload.py

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 14: `django__django-11815`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 8 | $0.0728 |
| Unrestricted | 35 | - |
| **Difference** | **+27** (338% more) | |

**Scope of Changes**: +4/-3 lines, File: `serializer.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me understand the bug first
3. Grep: `class EnumSerializer`
4. Grep: `Enum.*serialize`
5. Let me read the serializer file to understand how Enum objects are currently ser...
6. Read: serializer.py
7. TodoWrite
8. I found the issue

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 15: `django__django-11848`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 6 | $0.0143 |
| Unrestricted | 21 | - |
| **Difference** | **+15** (250% more) | |

**Scope of Changes**: +6/-3 lines, File: `http.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze the Django code to understand and fix the two-digit year check issu...
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/django/utils/http.py" | head -5`
2. Bash: `find /testbed -type f -name "*.py" -path "*/django/utils/http.py" | head -5`
3. I'll read the `parse_http_date` function to understand the current implementatio...
   - Tool: Read: http.py
4. Read: http.py
5. Now I can see the issue clearly
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i http | head -10`
6. Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i http | head -10`
7. Let me read the test file to understand the expected behavior better
8. Read: test_http.py

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 16: `django__django-11999`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 12 | $0.0216 |
| Unrestricted | 43 | - |
| **Difference** | **+31** (258% more) | |

**Scope of Changes**: +3/-2 lines, File: `__init__.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me start by understanding the bug
3. Grep: `get_.*_display`
4. Glob: `**/db/models/**/*.py`
5. Let me look at the relevant files to understand how `get_FOO_display` is impleme...
6. Read: __init__.py
7. Grep: `get_.*_display|_get_FIELD_disp`
8. Now I can see the key code

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 17: `django__django-12125`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 10 | $0.0174 |
| Unrestricted | 32 | - |
| **Difference** | **+22** (220% more) | |

**Scope of Changes**: +2/-2 lines, File: `serializer.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this Django bug where `makemigrations` produces incorrect paths for...
   - Tool: Bash: `find /testbed -type f -name "*.py" | grep -E "(migration|serializer)" | head -20`
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(migration|serializer)" | head -20`
3. I'll analyze the Django bug where `makemigrations` produces incorrect paths for ...
4. Bash: `find /testbed/django -type f -path "*/migrations/*.py" | grep -E "(serializer|wr`
5. Let me examine the migration serializer code to understand how it handles class ...
   - Tool: Read: serializer.py
6. Read: serializer.py
7. Now I can see the issue
   - Tool: Bash: `grep -n "__qualname__" /testbed/django/db/migrations/serializer.py`
8. Bash: `grep -n "__qualname__" /testbed/django/db/migrations/serializer.py`

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 18: `django__django-12286`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 22 | $0.0638 |
| Unrestricted | 32 | - |
| **Difference** | **+10** (45% more) | |

**Scope of Changes**: +14/-1 lines, File: `translation.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this Django translation issue where `translation
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(translation|check)" | head -20`
3. Bash: `grep -r "translation.E004" /testbed --include="*.py"`
4. I'll analyze the Django translation check issue and fix it
   - Tool: Read: translation.py, Read: test_translation.py
5. Read: translation.py, Read: test_translation.py
6. Read: translation.py, Read: test_translation.py
7. Now I can see the issue
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/translation/*" | grep -v __pycache__`
8. Bash: `find /testbed -type f -name "*.py" -path "*/translation/*" | grep -v __pycache__`

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 19: `django__django-12453`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 6 | $0.0144 |
| Unrestricted | 22 | - |
| **Difference** | **+16** (267% more) | |

**Scope of Changes**: +4/-3 lines, File: `creation.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this issue and implement the fix
2. Bash: `find /testbed -type f -name "creation.py" | grep -E "db/backends/base"`
3. I'll analyze the issue and implement the fix
4. Read: creation.py
5. Now I can see the issue clearly
   - Tool: Edit: creation.py
6. Edit: creation.py
7. Now let me update the `deserialize_db_from_string` method to wrap the deserializ...
   - Tool: Edit: creation.py
8. Edit: creation.py

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 20: `django__django-12497`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 15 | $0.0339 |
| Unrestricted | 25 | - |
| **Difference** | **+10** (67% more) | |

**Scope of Changes**: +3/-3 lines, Files: `related.py`, `test_relative_fields.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this Django bug about the incorrect hint message for recursive rela...
2. Grep: `If you want to create a recurs`
3. Let me search for the error message in the source code to understand the issue b...
4. Read: related.py
5. Let me search for the specific error message in the file
   - Tool: Grep: `If you want to create a recurs`
6. Grep: `If you want to create a recurs`
7. Now let me look at the broader context around these error messages to understand...
8. Read: related.py

**Why Can It Succeed Without Execution?**

- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 21: `django__django-12700`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 14 | $0.0586 |
| Unrestricted | 22 | - |
| **Difference** | **+8** (57% more) | |

**Scope of Changes**: +4/-0 lines, File: `debug.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this security issue where Django's `SafeExceptionReporterFilter
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/views/debug.py" | head -5`
2. Bash: `find /testbed -type f -name "*.py" -path "*/views/debug.py" | head -5`
3. I'll analyze the Django security issue where `SafeExceptionReporterFilter
   - Tool: Read: debug.py
4. Read: debug.py
5. Now I can see the issue clearly
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i debug | head -10`
6. Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | grep -i debug | head -10`
7. Let me check the test file to understand the expected behavior better
   - Tool: Read: test_debug.py
8. Read: test_debug.py

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 22: `django__django-12708`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 10 | $0.0911 |
| Unrestricted | 44 | - |
| **Difference** | **+34** (340% more) | |

**Scope of Changes**: +1/-1 lines, File: `schema.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me start by reading the relevant file mentioned in the problem description
   - Tool: Read: schema.py
3. Read: schema.py
4. Now I can see the `_delete_composed_index` method at line 402
5. Grep: `def _constraint_names`
6. Read: schema.py
7. Now I understand the issue
8. TodoWrite

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 23: `django__django-12856`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 34 | $0.0975 |
| Unrestricted | 45 | - |
| **Difference** | **+11** (32% more) | |

**Scope of Changes**: +3/-0 lines, File: `base.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this issue step by step
   - Tool: Bash: `find /testbed -type f -path "*/models/constraints.py" | head -5`, Bash: `find /testbed -type f -name "*.py" | grep -E "(check|constraint)" | head -20`
2. Bash: `find /testbed -type f -path "*/models/constraints.py" | head -5`, Bash: `find /testbed -type f -name "*.py" | grep -E "(check|constraint)" | head -20`
3. Bash: `find /testbed -type f -path "*/models/constraints.py" | head -5`, Bash: `find /testbed -type f -name "*.py" | grep -E "(check|constraint)" | head -20`
4. I'll analyze the Django codebase to understand how to add field validation for `...
5. Read: constraints.py
6. Bash: `find /testbed -type f -name "*.py" -path "*/models/*" | grep -E "check" | head -`
7. Now let me look at how `unique_together` implements its field validation to unde...
   - Tool: Bash: `find /testbed -type f -name "*.py" -path "*/models/*" | grep -E "base|options" |`
8. Bash: `find /testbed -type f -name "*.py" -path "*/models/*" | grep -E "base|options" |`

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 24: `django__django-12915`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 8 | $0.0228 |
| Unrestricted | 40 | - |
| **Difference** | **+32** (400% more) | |

**Scope of Changes**: +6/-0 lines, File: `handlers.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this issue step by step to understand the problem and implement a f...
   - Tool: Read: handlers.py, Read: asgi.py
2. Read: handlers.py, Read: asgi.py
3. Read: handlers.py, Read: asgi.py
4. Now let me check the base handler to understand how `get_response_async` is impl...
5. Read: base.py
6. Now I understand the issue
7. Grep: `from asgiref`
8. Now I'll implement the fix

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 25: `django__django-12983`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 6 | $0.0295 |
| Unrestricted | 28 | - |
| **Difference** | **+22** (367% more) | |

**Scope of Changes**: +1/-1 lines, File: `text.py`

**Prohibited Mode Execution Steps**:

1. Grep: `def slugify`
2. Let me search for the slugify function in the Django codebase
3. Glob: `**/text.py`
4. Read: text.py
5. I found the `slugify` function at line 394-406 in `/testbed/django/utils/text
   - Tool: Edit: text.py
6. Edit: text.py
7. The fix has been applied
8. Read: text.py

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Fast resolution (<7 turns): Agent quickly understood the problem essence
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 26: `django__django-13028`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 11 | $0.1431 |
| Unrestricted | 29 | - |
| **Difference** | **+18** (164% more) | |

**Scope of Changes**: +6/-5 lines, File: `query.py`

**Prohibited Mode Execution Steps**:

1. TodoWrite
2. Let me understand the bug first
3. Grep: `def check_filterable`
4. Glob: `**/django/db/models/sql/query.py`
5. Read: query.py
6. Now I can see the issue
7. TodoWrite
8. Let me look at how the `filterable` attribute is used in Django expressions to u...

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 27: `django__django-13033`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 29 | $0.2267 |
| Unrestricted | 55 | - |
| **Difference** | **+26** (90% more) | |

**Scope of Changes**: +1/-1 lines, File: `compiler.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this Django ORM issue where self-referencing foreign keys cause inc...
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(query|order)" | head -20`
3. Bash: `ls -la /testbed`
4. I'll analyze this Django ORM bug where self-referencing foreign keys cause incor...
   - Tool: Bash: `find /testbed/django/db/models -type f -name "*.py" | grep -E "(sql|query)" | he`, Bash: `ls -la /testbed/django/db/models`
5. Bash: `find /testbed/django/db/models -type f -name "*.py" | grep -E "(sql|query)" | he`, Bash: `ls -la /testbed/django/db/models`
6. Bash: `find /testbed/django/db/models -type f -name "*.py" | grep -E "(sql|query)" | he`, Bash: `ls -la /testbed/django/db/models`
7. Let me explore the Django ORM code to understand how ordering works with self-re...
   - Tool: Bash: `ls -la /testbed/django/db/models/sql`, Grep: `order_by`
8. Bash: `ls -la /testbed/django/db/models/sql`, Grep: `order_by`

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 28: `django__django-13158`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 39 | $0.2682 |
| Unrestricted | 54 | - |
| **Difference** | **+15** (38% more) | |

**Scope of Changes**: +2/-0 lines, File: `query.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this Django bug where `QuerySet
   - Tool: Bash: `ls -la /testbed`, Bash: `find /testbed -type f -name "*.py" | grep -E "(queryset|query)" | head -20`
2. Bash: `ls -la /testbed`, Bash: `find /testbed -type f -name "*.py" | grep -E "(queryset|query)" | head -20`
3. Bash: `ls -la /testbed`, Bash: `find /testbed -type f -name "*.py" | grep -E "(queryset|query)" | head -20`
4. I'll analyze this Django bug where `QuerySet
   - Tool: Read: query.py
5. Read: query.py
6. Let me search for the `none()` method and understand how it works with combined ...
7. Bash: `grep -n "def none" /testbed/django/db/models/query.py`
8. Let me read the `none()` method and understand how it works with combined querie...

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 29: `django__django-13315`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 40 | $0.1113 |
| Unrestricted | 65 | - |
| **Difference** | **+25** (62% more) | |

**Scope of Changes**: +1/-1 lines, File: `models.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this Django issue about duplicate options in ForeignKey formfields ...
2. Bash: `find /testbed -type f -name "*.py" | grep -E "(test|regression)" | grep -i "limi`
3. Bash: `find /testbed -type f -name "*.py" -path "*/tests/*" | head -30`
4. I'll analyze this Django issue about duplicate options in ForeignKey formfields ...
5. Bash: `find /testbed -type f -name "*.py" -path "*" | grep -E "limit_choices" | head -2`
6. Bash: `find /testbed -type f -name "*.patch" -o -name "*.diff" | head -10`
7. Let me search for files related to ForeignKey and limit_choices_to to understand...
8. Bash: `find /testbed -type f -name "*.py" -path "*/django/db/models/*" | grep -E "(fiel`

**Why Can It Succeed Without Execution?**

- ✅ Small scope changes (≤5 lines): Simple fix logic, easy to verify through reasoning
- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

### Case 30: `django__django-13401`

| Mode | Turns | Cost |
|------|-------|------|
| Prohibited | 21 | $0.1253 |
| Unrestricted | 34 | - |
| **Difference** | **+13** (62% more) | |

**Scope of Changes**: +14/-3 lines, File: `__init__.py`

**Prohibited Mode Execution Steps**:

1. I'll analyze this issue step by step to understand the problem and implement a f...
2. Bash: `find /testbed -type f -name "*.py" -path "*/django/db/models/*" | grep -E "(fiel`
3. I'll analyze the Django field comparison issue and implement a fix
4. Read: __init__.py
5. Let me search for the `__eq__`, `__hash__`, and `__lt__` methods in the Field cl...
6. Grep: `def __eq__|def __hash__|def __`
7. Let me read the comparison methods in the Field class
8. Read: __init__.py

**Why Can It Succeed Without Execution?**

- ✅ Single file modification: Clear problem boundary, no cross-module dependencies
- ✅ Bug type suitable for reasoning: Does not involve boundary conditions, performance, concurrency, or other issues requiring runtime verification

---

## 5. Conclusions and Insights

### Core Conclusions

1. **LLM's Intrinsic Reasoning Capability is Sufficient**: For these 30 P→P cases, the Agent can correctly fix bugs solely through code reading and understanding

2. **Execution is Redundant Verification**: Test execution in Unrestricted mode did not bring additional value, but consumed more resources instead

3. **Prohibited is More Efficient**: Saves an average of 51% interaction turns with lower cost

### Bug Characteristics Suitable for Prohibited Mode

| Characteristic | Description |
|----------------|-------------|
| Clear problem description | Issue clearly states expected vs actual behavior |
| Deterministic fix | Can directly provide correct answer after understanding the problem |
| Semantic/logic errors | Such as regex, API calls, type handling |
| Small scope changes | Usually ≤10 lines of code |
| No runtime dependencies | Does not involve boundary conditions, concurrency, performance |

### Support for RQ3

> These 30 cases demonstrate: For most successfully fixed bugs (P→P), LLM's reasoning capability is sufficient.
> Code execution in these scenarios is **redundant verification**, not a necessary condition for fixing.
> This explains why Prohibited mode can achieve a resolve rate comparable to Unrestricted mode.
