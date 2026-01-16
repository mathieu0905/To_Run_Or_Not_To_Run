# Run-Less 模式的优势场景分析

虽然整体数据显示 Run-Less 不如 Run-Free，但在某些特定场景下，适度执行确实有帮助。

## 1. Run-Less 独有成功的案例

这些案例中，Run-Free 和 Run-Full 都失败，但 Run-Less 成功了。

### SWE-bench Lite

**claude_code:**

- Run-Less-K1 独有成功: 1 个
- Run-Less-K3 独有成功: 0 个
- 任一 Run-Less 独有成功: 1 个

**案例列表:**
- `django__django-11964` (K1)

**codex:**

- Run-Less-K1 独有成功: 1 个
- Run-Less-K3 独有成功: 1 个
- 任一 Run-Less 独有成功: 1 个

**案例列表:**
- `django__django-15213` (K1, K3)

### SWE-bench Verified

**claude_code:**

- Run-Less-K1 独有成功: 2 个
- Run-Less-K3 独有成功: 2 个
- 任一 Run-Less 独有成功: 3 个

**案例列表:**
- `astropy__astropy-14369` (K3)
- `django__django-11433` (K1, K3)
- `django__django-12193` (K1)

**codex:**

- Run-Less-K1 独有成功: 2 个
- Run-Less-K3 独有成功: 3 个
- 任一 Run-Less 独有成功: 5 个

**案例列表:**
- `astropy__astropy-14369` (K1)
- `django__django-11149` (K3)
- `django__django-11433` (K3)
- `django__django-12273` (K3)
- `django__django-12308` (K1)

## 2. Run-Less 独有成功案例的详细分析

### `django__django-11964` (claude_code, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 264,394 | 107 | 7 | 失败 |
| run_less_k1 | 279,901 | 91 | 6 | **成功** |
| run_less_k3 | 286,153 | 92 | 5 | 失败 |
| run_cost | 371,806 | 110 | 6 | 失败 |
| run_full | 454,826 | 148 | 11 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-15213` (codex, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 773,892 | 52 | 0 | 失败 |
| run_less_k1 | 497,171 | 42 | 0 | **成功** |
| run_less_k3 | 648,812 | 55 | 6 | **成功** |
| run_cost | 1,194,744 | 86 | 10 | **成功** |
| run_full | 664,227 | 54 | 4 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `astropy__astropy-14369` (claude_code, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 23,182 | 36 | 0 | 失败 |
| run_less_k1 | 662,637 | 94 | 3 | 失败 |
| run_less_k3 | 202,229 | 55 | 5 | **成功** |
| run_cost | 172,953 | 64 | 4 | **成功** |
| run_full | 159,775 | 62 | 3 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-11433` (claude_code, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 17,216 | 17 | 0 | 失败 |
| run_less_k1 | 143,606 | 71 | 6 | **成功** |
| run_less_k3 | 152,186 | 70 | 2 | **成功** |
| run_cost | 243,147 | 83 | 6 | 失败 |
| run_full | 197,423 | 89 | 2 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-12193` (claude_code, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 10,860 | 11 | 0 | 失败 |
| run_less_k1 | 83,166 | 44 | 2 | **成功** |
| run_less_k3 | 89,103 | 50 | 4 | 失败 |
| run_cost | 92,623 | 56 | 4 | 失败 |
| run_full | 60,372 | 43 | 1 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `astropy__astropy-14369` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 476,795 | 44 | 0 | 失败 |
| run_less_k1 | 465,523 | 46 | 0 | **成功** |
| run_less_k3 | 863,774 | 67 | 2 | 失败 |
| run_cost | 799,612 | 66 | 2 | 失败 |
| run_full | 1,023,689 | 67 | 2 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-11149` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 887,761 | 77 | 0 | 失败 |
| run_less_k1 | 1,666,811 | 87 | 4 | 失败 |
| run_less_k3 | 1,745,265 | 76 | 6 | **成功** |
| run_cost | 1,617,609 | 74 | 4 | 失败 |
| run_full | 1,249,548 | 78 | 2 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-11433` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 290,823 | 33 | 0 | 失败 |
| run_less_k1 | 457,464 | 43 | 4 | 失败 |
| run_less_k3 | 326,728 | 39 | 6 | **成功** |
| run_cost | 565,026 | 62 | 6 | **成功** |
| run_full | 655,146 | 55 | 8 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-12273` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 460,123 | 52 | 0 | 失败 |
| run_less_k1 | 288,012 | 36 | 2 | 失败 |
| run_less_k3 | 779,584 | 66 | 4 | **成功** |
| run_cost | 306,596 | 41 | 0 | 失败 |
| run_full | 342,668 | 27 | 4 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

### `django__django-12308` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 264,021 | 32 | 0 | 失败 |
| run_less_k1 | 348,176 | 40 | 2 | **成功** |
| run_less_k3 | 235,008 | 33 | 6 | 失败 |
| run_cost | 295,168 | 42 | 4 | 失败 |
| run_full | 209,938 | 29 | 6 | 失败 |

**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。

## 3. Run-Less 比 Run-Free 更好的案例

这些案例中，Run-Free 失败但 Run-Less 成功。

### SWE-bench Lite

**claude_code:**

- Run-Less-K1 成功但 Run-Free 失败: 2 个
- Run-Less-K3 成功但 Run-Free 失败: 4 个

**案例:**
- `django__django-11964` (K1 成功)
- `django__django-15498` (K1 成功)
- `django__django-11620` (K3 成功)
- `django__django-11797` (K3 成功)
- `django__django-12284` (K3 成功)

**codex:**

- Run-Less-K1 成功但 Run-Free 失败: 2 个
- Run-Less-K3 成功但 Run-Free 失败: 1 个

**案例:**
- `django__django-15202` (K1 成功)
- `django__django-15213` (K1 成功)

### SWE-bench Verified

**claude_code:**

- Run-Less-K1 成功但 Run-Free 失败: 8 个
- Run-Less-K3 成功但 Run-Free 失败: 9 个

**案例:**
- `astropy__astropy-14096` (K1 成功)
- `astropy__astropy-7166` (K1 成功)
- `django__django-11206` (K1 成功)
- `django__django-11433` (K1 成功)
- `django__django-11490` (K1 成功)
- `astropy__astropy-14369` (K3 成功)
- `django__django-12663` (K3 成功)

**codex:**

- Run-Less-K1 成功但 Run-Free 失败: 4 个
- Run-Less-K3 成功但 Run-Free 失败: 5 个

**案例:**
- `astropy__astropy-14369` (K1 成功)
- `django__django-11490` (K1 成功)
- `django__django-12304` (K1 成功)
- `django__django-12308` (K1 成功)
- `django__django-11149` (K3 成功)
- `django__django-11433` (K3 成功)
- `django__django-12273` (K3 成功)

## 4. 适度执行的价值分析

| 模式 | 独有成功 | 比 Run-Free 好 | 比 Run-Full 好 |
|------|----------|----------------|----------------|
| run_less_k1 | 4 | 16 | 10 |
| run_less_k3 | 2 | 19 | 9 |
| run_cost | 5 | 22 | 15 |

## 5. 核心发现：适度执行的价值

### 适度执行有帮助的场景

1. **需要验证但不需要迭代的问题**
   - 1-3 次执行足以验证修复是否正确
   - 更多执行反而引入噪声和干扰

2. **Run-Free 推理不足的问题**
   - 纯推理无法确定正确答案
   - 但少量执行反馈就能指明方向

3. **Run-Full 过度执行有害的问题**
   - 过多执行导致试错循环
   - 适度执行避免了这个问题

### 实践建议

1. **Run-Free 仍是默认首选** - 成本最低，效果接近最佳
2. **Run-Less-K1 可作为备选** - 当 Run-Free 失败时，尝试 1 次执行
3. **避免 Run-Full** - 除非确实需要大量迭代调试
4. **适度执行的价值在于验证** - 不是探索，而是确认
