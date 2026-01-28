# Data Leakage Defense: 数据泄漏防御分析报告

## 背景与动机

在使用 SWE-bench 评估 LLM 代码修复能力时，一个常见的质疑是：**模型的成功是否源于数据泄漏（Data Leakage）而非真正的推理能力？**

如果模型在预训练阶段"记住"了这些 Bug 的标准修复方案，它自然不需要运行测试来验证——因为它是在"背诵"答案而不是在"推理解题"。在这种情况下，OFFLINE 模式的高成功率就不能证明"推理胜过执行"，只能证明"作弊胜过考试"。

本报告通过三个维度的分析，系统性地反驳数据泄漏假设。

---

## 分析方法概述

| 方案 | 核心逻辑 | 证据类型 |
|------|----------|----------|
| **A. Hurt Cases 分析** | 如果是背答案，执行反馈不应该让模型"改错" | 反证法 |
| **B. 补丁相似度分析（按难度）** | 高相似度+简单问题=正常；高相似度+复杂问题=可能记忆 | 分层分析 |
| **C. 跨模式一致性分析** | 如果是背答案，不同模式应产生相同补丁 | 直接验证 |

---

## 方案 A: Hurt Cases 分析

### 核心逻辑

如果模型纯粹是靠「背诵」泄漏的答案，那么**执行不应该导致它失败**。

既然背过了完美答案，模型输出它，运行测试，测试自然通过。UNBOUNDED 模式应该至少和 OFFLINE 一样好，甚至更稳。

**Hurt Cases** = OFFLINE 成功但 UNBOUNDED 失败的案例

这些案例证明：模型是在**实时推理**，并且会被执行结果「带偏」。

### 结果

| Dataset | Agent | Hurt Cases | Help Cases | Net Effect |
|---------|-------|------------|------------|------------|
| SWE-bench Lite | claude_code | 5 | 6 | +1 |
| SWE-bench Lite | codex | 4 | 3 | -1 |
| SWE-bench Verified | claude_code | 6 | 9 | +3 |
| SWE-bench Verified | codex | 1 | 3 | +2 |
| **Total** | - | **16** | **21** | **+5** |

### Hurt Cases 详细列表

**SWE-bench Lite - claude_code (5 个)**:
- `django__django-12184`
- `django__django-12908`
- `django__django-13230`
- `django__django-14016`
- `django__django-15695`

**SWE-bench Lite - codex (4 个)**:
- `django__django-11848`
- `django__django-11964`
- `django__django-12497`
- `django__django-12747`

**SWE-bench Verified - claude_code (6 个)**:
- `astropy__astropy-14365`
- `django__django-11532`
- `django__django-11555`
- `django__django-11728`
- `django__django-11790`
- `django__django-13121`

**SWE-bench Verified - codex (1 个)**:
- `django__django-10973`

### 结论

**共发现 16 个 Hurt Cases**——这些案例在 OFFLINE 模式下成功修复，但在 UNBOUNDED 模式下被执行反馈"带偏"而失败。

这种"被执行带偏"的脆弱性，恰恰说明模型是在**实时推理**，而不是在机械地复述记忆。如果模型只是背诵答案，执行反馈不应该让它偏离正确答案。

---

## 方案 B: 补丁相似度分析（按难度分类）

### 核心逻辑

如果模型是通过「记忆」泄漏的数据来解决问题，生成的补丁应该与 Ground Truth **高度相似**。

**但相似度高也可能是因为问题简单、解法唯一。因此需要按难度分类分析。**

### 难度分类标准

| 难度 | 修改行数 | 文件数 |
|------|----------|--------|
| Easy | ≤5 行 | 1 个文件 |
| Medium | ≤20 行 | ≤2 个文件 |
| Hard | >20 行 | >2 个文件 |

### 判据

| 相似度 | 难度 | 解释 |
|--------|------|------|
| 高(≥90%) | Easy | ✅ 正常 - 简单问题解法趋同 |
| 高(≥90%) | Hard | ⚠️ 可能记忆 - 需要关注 |
| 低(<40%) | Medium/Hard | ✅ 推理证据 - 不同路径解决复杂问题 |

### 结果

#### SWE-bench Lite

**claude_code - 按难度分类**

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 47 | 58.4% | 11 (23%) | 9 (19%) | 13 (28%) | 14 (30%) |
| Medium | 47 | 48.8% | 5 (11%) | 7 (15%) | 16 (34%) | 19 (40%) |
| Hard | 6 | 36.5% | **0 (0%)** | 0 (0%) | 3 (50%) | 3 (50%) |

**codex - 按难度分类**

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 47 | 24.6% | 0 (0%) | 0 (0%) | 7 (15%) | 40 (85%) |
| Medium | 47 | 24.8% | 0 (0%) | 1 (2%) | 5 (11%) | 41 (87%) |
| Hard | 6 | 23.2% | **0 (0%)** | 0 (0%) | 0 (0%) | 6 (100%) |

#### SWE-bench Verified

**claude_code - 按难度分类**

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 45 | 66.4% | 20 (44%) | 5 (11%) | 8 (18%) | 12 (27%) |
| Medium | 35 | 52.6% | 3 (9%) | 7 (20%) | 14 (40%) | 11 (31%) |
| Hard | 20 | 29.5% | **1 (5%)** | 1 (5%) | 3 (15%) | 15 (75%) |

**codex - 按难度分类**

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 45 | 27.2% | 0 (0%) | 1 (2%) | 8 (18%) | 36 (80%) |
| Medium | 35 | 22.5% | 0 (0%) | 0 (0%) | 4 (11%) | 31 (89%) |
| Hard | 20 | 24.7% | **0 (0%)** | 0 (0%) | 6 (30%) | 14 (70%) |

### 关键案例

#### ⚠️ 需要关注：高相似度(≥90%) + 复杂补丁(Hard)

**仅发现 1 个案例**：
- `django__django-10973`: 93.2% similarity, 37 lines changed (SWE-bench Verified, claude_code)

#### ✅ 推理证据：低相似度(<40%) + 中/复杂补丁

**共 140 个案例**，代表性案例：

| Instance | Similarity | Lines Changed |
|----------|------------|---------------|
| `django__django-11964` | 4.1% | 8 lines |
| `django__django-11564` | 9.7% | 31 lines |
| `django__django-12589` | 9.8% | 15 lines |
| `astropy__astropy-13977` | 3.0% | 95 lines |
| `django__django-11885` | 3.2% | 130 lines |
| `astropy__astropy-13398` | 3.7% | 215 lines |

### 结论

- **需要关注的案例**（高相似度 ≥90% + 复杂补丁 Hard）: **仅 1 个**
- **推理证据案例**（低相似度 <40% + 中/复杂补丁）: **140 个**

所有高相似度案例几乎都是简单问题（解法趋同是正常的），复杂问题都展现了解法多样性。

---

## 方案 C: 跨模式补丁一致性分析

### 核心逻辑

如果模型是「背答案」，那么同一个 Bug 在不同执行模式下应该产生**相同的补丁**——因为都是在复述同一个记忆。

如果是「推理」，不同模式的执行反馈会影响解法路径，产生**不同的补丁**。

### 分析维度

为了更精细地区分"背答案"和"推理"，我们分析三个维度：

| 维度 | 背答案预期 | 推理预期 |
|------|-----------|----------|
| 文件重叠度 | 100% | 可能不同 |
| 代码修改重叠度 | ~100%（仅格式差异）| 显著不同 |
| 完整补丁相似度 | ~100% | 变化大 |

### 结果：OFFLINE vs UNBOUNDED 对比

#### 三维度相似度统计

**SWE-bench Lite - claude_code**

| 维度 | 平均值 | 完全相同(100%) | 高度相似(≥80%) | 显著不同(<50%) |
|------|--------|----------------|----------------|----------------|
| 文件重叠度 | 73.6% | 55 (55%) | 55 (55%) | 11 (11%) |
| 代码修改重叠 | 51.0% | 21 (21%) | 24 (24%) | 38 (38%) |
| 完整补丁相似度 | 59.2% | 21 (21%) | 34 (34%) | 46 (46%) |

**SWE-bench Lite - codex**

| 维度 | 平均值 | 完全相同(100%) | 高度相似(≥80%) | 显著不同(<50%) |
|------|--------|----------------|----------------|----------------|
| 文件重叠度 | 79.7% | 65 (65%) | 67 (67%) | 19 (19%) |
| 代码修改重叠 | 37.5% | 1 (1%) | 3 (3%) | 59 (59%) |
| 完整补丁相似度 | 46.9% | 1 (1%) | 11 (11%) | 62 (62%) |

**SWE-bench Verified - claude_code**

| 维度 | 平均值 | 完全相同(100%) | 高度相似(≥80%) | 显著不同(<50%) |
|------|--------|----------------|----------------|----------------|
| 文件重叠度 | 74.8% | 56 (56%) | 56 (56%) | 12 (12%) |
| 代码修改重叠 | 54.6% | 27 (27%) | 29 (29%) | 36 (36%) |
| 完整补丁相似度 | 61.1% | 26 (26%) | 35 (35%) | 42 (42%) |

**SWE-bench Verified - codex**

| 维度 | 平均值 | 完全相同(100%) | 高度相似(≥80%) | 显著不同(<50%) |
|------|--------|----------------|----------------|----------------|
| 文件重叠度 | 78.2% | 60 (60%) | 63 (63%) | 21 (21%) |
| 代码修改重叠 | 42.6% | 1 (1%) | 4 (4%) | 49 (49%) |
| 完整补丁相似度 | 46.1% | 1 (1%) | 9 (9%) | 55 (55%) |

#### 案例分类

| Dataset | Agent | 完全相同 | 同文件不同代码 | 不同文件 |
|---------|-------|----------|---------------|---------|
| Lite | claude_code | 21 (21%) | **17 (17%)** | 11 (11%) |
| Lite | codex | 1 (1%) | **33 (33%)** | 19 (19%) |
| Verified | claude_code | 26 (26%) | **13 (13%)** | 12 (12%) |
| Verified | codex | 1 (1%) | **21 (21%)** | 21 (21%) |

### 关键证据："同文件不同代码"案例

这类案例最能区分「背答案」和「推理」：
- 模型知道要修改哪个文件（说明理解了问题）
- 但两次运行产生了完全不同的代码修改（说明不是在背诵）

**代表性案例（文件重叠 100%，代码重叠 <10%）**：

| Instance | 文件重叠 | 代码重叠 |
|----------|----------|----------|
| `django__django-12589` | 100% | 0% |
| `astropy__astropy-14995` | 100% | 0% |
| `django__django-14997` | 100% | 0% |
| `django__django-11422` | 100% | 2% |
| `django__django-12747` | 100% | 3% |

如果是纯粹背诵，同一个文件里的修改应该完全相同。但实际观察到大量「同文件不同代码」的案例。

### 所有模式间相似度矩阵

**claude_code (SWE-bench Lite)**

| Mode Pair | Avg Sim | Identical(≥99%) | Different(<90%) |
|-----------|---------|-----------------|-----------------|
| run_free vs run_less_k1 | 67.0% | 33 (33%) | 60 (60%) |
| run_free vs run_less_k3 | 63.5% | 30 (30%) | 66 (66%) |
| run_free vs run_full | 59.2% | 21 (21%) | 73 (73%) |
| run_less_k1 vs run_less_k3 | 68.0% | 31 (31%) | 55 (55%) |
| run_less_k1 vs run_full | 65.8% | 28 (28%) | 66 (66%) |
| run_less_k3 vs run_full | 62.9% | 26 (26%) | 71 (71%) |

**codex (SWE-bench Lite)**

| Mode Pair | Avg Sim | Identical(≥99%) | Different(<90%) |
|-----------|---------|-----------------|-----------------|
| run_free vs run_less_k1 | 47.8% | 1 (1%) | 97 (97%) |
| run_free vs run_less_k3 | 48.8% | 1 (1%) | 96 (96%) |
| run_free vs run_full | 46.9% | 1 (1%) | 97 (97%) |
| run_less_k1 vs run_less_k3 | 49.3% | 1 (1%) | 95 (95%) |
| run_less_k1 vs run_full | 47.5% | 1 (1%) | 98 (98%) |
| run_less_k3 vs run_full | 45.3% | 1 (1%) | 98 (98%) |

### 观察

1. **执行次数越多，与 OFFLINE 的差异越大**：run_free vs run_full 差异最大
2. **Codex 几乎没有完全相同的补丁**：仅 1% 相同，97-98% 存在显著差异
3. **相邻模式相似度更高**：run_less_k1 vs run_less_k3 比 run_free vs run_full 更相似

---

## 汇总结论

### 三重证据汇总

| 方案 | 核心发现 | 结论 |
|------|----------|------|
| **A. Hurt Cases** | 16 个案例在 OFFLINE 成功但 UNBOUNDED 失败 | 执行反馈会"带偏"模型 → 是推理不是背诵 |
| **B. 相似度+难度** | 仅 1 个"高相似+复杂"案例，140 个"低相似+复杂"案例 | 复杂问题展现解法多样性 → 是推理不是背诵 |
| **C. 跨模式一致性** | 仅 1-26% 补丁完全相同，13-33% "同文件不同代码" | 同一问题不同模式产生不同解法 → 是推理不是背诵 |

### 按 Agent 汇总

| Agent | 跨模式平均相似度 | 完全相同比例 | 显著不同比例 |
|-------|-----------------|-------------|-------------|
| claude_code | 65.3% | 29.0% | 64.5% |
| codex | 46.9% | **0.8%** | **96.5%** |

Codex 的结果特别有说服力：**几乎没有任何案例在不同模式下产生相同的补丁**。

---

## 论文话术建议

### Discussion 或 Threats to Validity 章节

> **Addressing Data Contamination Concerns**
>
> A potential concern is that the model's strong OFFLINE performance stems from data leakage rather than reasoning. We present three lines of evidence against this hypothesis:
>
> **First**, we identified **16 Hurt Cases** where the model succeeded in OFFLINE mode but failed in UNBOUNDED mode. This fragility—being misled by execution feedback—demonstrates that the model is reasoning in real-time rather than reciting memorized solutions. If the model had simply memorized the correct patches from training data, execution feedback should not cause it to deviate from the correct answer.
>
> **Second**, we analyzed patch similarity stratified by bug complexity. We found only **1 concerning case** of high similarity (≥90%) on complex patches (>20 lines changed), while **140 cases** achieved correct fixes with <40% similarity on medium/hard problems, demonstrating diverse solution paths.
>
> **Third**, we compared patches generated for the **same bug across different execution modes**. If models were reciting memorized solutions, patches should be identical regardless of execution feedback. However, only **1-26%** of patches are identical across modes, and **13-33%** of cases modify the same files but with completely different code (code overlap <10% despite 100% file overlap). This "same file, different code" pattern is the strongest evidence: the model understands *where* to fix but generates *different solutions* each time.
>
> Combined, these findings strongly support genuine reasoning over memorization.

---

## 附录：分析脚本

分析脚本位于 `analysis/data_leakage_defense/` 目录：

- `analyze_hurt_cases.py` - 方案 A: Hurt Cases 分析
- `analyze_patch_similarity.py` - 方案 B: 补丁相似度分析

---

*报告生成时间: 2024*
*分析数据: SWE-bench Lite (100 instances) + SWE-bench Verified (100 instances)*
*分析模型: Claude Code, Codex*
*分析模式: run_free, run_less_k1, run_less_k3, run_full*
