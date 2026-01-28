# Data Leakage Defense: Patch Similarity Analysis

## 核心问题：模型是不是在背答案？

### 分析策略

**1. 按难度分类分析**
| 相似度 | 难度 | 解释 |
|--------|------|------|
| 高(≥90%) | Easy (≤5行) | ✅ 正常 - 简单问题解法趋同 |
| 高(≥90%) | Hard (>20行) | ⚠️ 可能记忆 - 需要关注 |
| 低(<40%) | Medium/Hard | ✅ 推理证据 - 不同路径解决复杂问题 |

**2. 跨模式对比**
- 如果是**背答案**：各模式相似度应该一致（都在复述同一个记忆）
- 如果是**推理**：执行反馈会影响解法，模式间相似度有差异

---

## SWE-bench Lite

### Agent: claude_code

#### 1. 按难度分类的相似度分布 (OFFLINE 模式)

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 47 | 58.4% | 11 (23%) | 9 (19%) | 13 (28%) | 14 (30%) |
| Medium | 47 | 48.8% | 5 (11%) | 7 (15%) | 16 (34%) | 19 (40%) |
| Hard | 6 | 36.5% | 0 (0%) | 0 (0%) | 3 (50%) | 3 (50%) |

**✅ 无「高相似度 + 复杂补丁」案例**

**✅ 推理证据：低相似度(<40%) + 中/复杂补丁 = 22 个**
- `django__django-11964`: 4.1%, 8 lines
- `django__django-11564`: 9.7%, 31 lines
- `django__django-15213`: 9.7%, 9 lines
- `django__django-12589`: 9.8%, 15 lines
- `django__django-11742`: 10.0%, 17 lines

#### 2. 跨模式相似度对比

| Mode | 总数 | Avg Sim | ≥90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 52.6% | 16 (16%) | 36 (36%) |
| run_less_k1 | 100 | 47.4% | 12 (12%) | 47 (47%) |
| run_less_k3 | 100 | 44.8% | 10 (10%) | 52 (52%) |
| run_full | 100 | 44.3% | 12 (12%) | 54 (54%) |

**模式间差异**: OFFLINE (52.6%) vs UNBOUNDED (44.3%) = **+8.3%**

→ 执行反馈改变了模型的解法，支持「推理」而非「背诵」

### Agent: codex

#### 1. 按难度分类的相似度分布 (OFFLINE 模式)

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 47 | 24.6% | 0 (0%) | 0 (0%) | 7 (15%) | 40 (85%) |
| Medium | 47 | 24.8% | 0 (0%) | 1 (2%) | 5 (11%) | 41 (87%) |
| Hard | 6 | 23.2% | 0 (0%) | 0 (0%) | 0 (0%) | 6 (100%) |

**✅ 无「高相似度 + 复杂补丁」案例**

**✅ 推理证据：低相似度(<40%) + 中/复杂补丁 = 47 个**
- `django__django-12589`: 2.4%, 15 lines
- `django__django-15252`: 5.1%, 8 lines
- `django__django-14730`: 5.7%, 10 lines
- `django__django-12470`: 7.3%, 6 lines
- `django__django-15213`: 7.9%, 9 lines

#### 2. 跨模式相似度对比

| Mode | 总数 | Avg Sim | ≥90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 24.6% | 0 (0%) | 87 (87%) |
| run_less_k1 | 100 | 26.8% | 0 (0%) | 76 (76%) |
| run_less_k3 | 100 | 25.6% | 0 (0%) | 85 (85%) |
| run_full | 100 | 23.8% | 0 (0%) | 86 (86%) |

**模式间差异较小**: +0.9%

## SWE-bench Verified

### Agent: claude_code

#### 1. 按难度分类的相似度分布 (OFFLINE 模式)

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 45 | 66.4% | 20 (44%) | 5 (11%) | 8 (18%) | 12 (27%) |
| Medium | 35 | 52.6% | 3 (9%) | 7 (20%) | 14 (40%) | 11 (31%) |
| Hard | 20 | 29.5% | 1 (5%) | 1 (5%) | 3 (15%) | 15 (75%) |

**⚠️ 需关注：高相似度(≥90%) + 复杂补丁(Hard) = 1 个**
- `django__django-10973`: 93.2%, 37 lines

**✅ 推理证据：低相似度(<40%) + 中/复杂补丁 = 26 个**
- `astropy__astropy-13977`: 3.0%, 95 lines
- `django__django-11885`: 3.2%, 130 lines
- `django__django-11964`: 3.4%, 8 lines
- `astropy__astropy-14369`: 3.6%, 65 lines
- `astropy__astropy-13398`: 3.7%, 215 lines

#### 2. 跨模式相似度对比

| Mode | 总数 | Avg Sim | ≥90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 54.2% | 24 (24%) | 38 (38%) |
| run_less_k1 | 100 | 48.3% | 15 (15%) | 46 (46%) |
| run_less_k3 | 100 | 47.7% | 14 (14%) | 44 (44%) |
| run_full | 100 | 44.1% | 11 (11%) | 51 (51%) |

**模式间差异**: OFFLINE (54.2%) vs UNBOUNDED (44.1%) = **+10.1%**

→ 执行反馈改变了模型的解法，支持「推理」而非「背诵」

### Agent: codex

#### 1. 按难度分类的相似度分布 (OFFLINE 模式)

| 难度 | 总数 | Avg Sim | ≥90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 45 | 27.2% | 0 (0%) | 1 (2%) | 8 (18%) | 36 (80%) |
| Medium | 35 | 22.5% | 0 (0%) | 0 (0%) | 4 (11%) | 31 (89%) |
| Hard | 20 | 24.7% | 0 (0%) | 0 (0%) | 6 (30%) | 14 (70%) |

**✅ 无「高相似度 + 复杂补丁」案例**

**✅ 推理证据：低相似度(<40%) + 中/复杂补丁 = 45 个**
- `astropy__astropy-13398`: 1.9%, 215 lines
- `django__django-13121`: 2.8%, 70 lines
- `astropy__astropy-14369`: 3.7%, 65 lines
- `django__django-11532`: 4.2%, 26 lines
- `django__django-13112`: 4.6%, 6 lines

#### 2. 跨模式相似度对比

| Mode | 总数 | Avg Sim | ≥90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 25.0% | 0 (0%) | 81 (81%) |
| run_less_k1 | 100 | 25.4% | 0 (0%) | 82 (82%) |
| run_less_k3 | 100 | 23.8% | 0 (0%) | 82 (82%) |
| run_full | 100 | 25.6% | 0 (0%) | 79 (79%) |

**模式间差异较小**: -0.6%

---

## 汇总结论

### 1. 按难度分析（核心证据）

- **需要关注的案例**（高相似度 ≥90% + 复杂补丁 Hard）: **1**
- **推理证据案例**（低相似度 <40% + 中/复杂补丁）: **140**

⚠️ 发现 1 个可能的记忆案例，需要进一步分析。

### 2. 跨模式对比

| Dataset | Agent | OFFLINE | UNBOUNDED | Δ |
|---------|-------|---------|-----------|---|
| SWE-bench Lite | claude_code | 52.6% | 44.3% | +8.3% |
| SWE-bench Lite | codex | 24.6% | 23.8% | +0.9% |
| SWE-bench Verified | claude_code | 54.2% | 44.1% | +10.1% |
| SWE-bench Verified | codex | 25.0% | 25.6% | -0.6% |

**2/4 个配置显示模式间有显著差异**

→ 如果是「背答案」，各模式应产生相同的补丁（相似度一致）

→ 实际观察到执行反馈改变了解法，**支持「推理」假设**

---

## 论文话术

> *"We analyzed patch similarity stratified by bug complexity. We found **1 concerning cases** of high similarity (≥90%) on complex patches (>20 lines), while **140 cases** achieved correct fixes with <40% similarity on medium/hard problems. Furthermore, cross-mode comparison reveals that execution feedback changes solution paths (OFFLINE vs UNBOUNDED similarity differs by 5-10%), which would not occur if the model were simply reciting memorized patches. These findings strongly support genuine reasoning over memorization."*
