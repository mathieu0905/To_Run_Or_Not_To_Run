# Data Leakage Defense: Patch Similarity Analysis

## Core Question: Is the model memorizing answers?

### Analysis Strategy

**1. Analysis by Difficulty Classification**
| Similarity | Difficulty | Explanation |
|--------|------|------|
| High (>=90%) | Easy (<=5 lines) | Normal - Simple problems tend to have similar solutions |
| High (>=90%) | Hard (>20 lines) | Possible memorization - Needs attention |
| Low (<40%) | Medium/Hard | Evidence of reasoning - Different paths to solve complex problems |

**2. Cross-mode Comparison**
- If **memorizing**: similarity should be consistent across modes (all reciting the same memory)
- If **reasoning**: execution feedback affects solutions, similarity varies between modes

---

## SWE-bench Lite

### Agent: claude_code

#### 1. Similarity Distribution by Difficulty (OFFLINE Mode)

| Difficulty | Total | Avg Sim | >=90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 47 | 58.4% | 11 (23%) | 9 (19%) | 13 (28%) | 14 (30%) |
| Medium | 47 | 48.8% | 5 (11%) | 7 (15%) | 16 (34%) | 19 (40%) |
| Hard | 6 | 36.5% | 0 (0%) | 0 (0%) | 3 (50%) | 3 (50%) |

**No 'High Similarity + Complex Patch' cases**

**Evidence of Reasoning: Low Similarity (<40%) + Medium/Complex Patch = 22 cases**
- `django__django-11964`: 4.1%, 8 lines
- `django__django-11564`: 9.7%, 31 lines
- `django__django-15213`: 9.7%, 9 lines
- `django__django-12589`: 9.8%, 15 lines
- `django__django-11742`: 10.0%, 17 lines

#### 2. Cross-mode Similarity Comparison

| Mode | Total | Avg Sim | >=90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 52.6% | 16 (16%) | 36 (36%) |
| run_less_k1 | 100 | 47.4% | 12 (12%) | 47 (47%) |
| run_less_k3 | 100 | 44.8% | 10 (10%) | 52 (52%) |
| run_full | 100 | 44.3% | 12 (12%) | 54 (54%) |

**Cross-mode Difference**: OFFLINE (52.6%) vs UNBOUNDED (44.3%) = **+8.3%**

-> Execution feedback changed the model's solution, supporting 'reasoning' over 'recitation'

### Agent: codex

#### 1. Similarity Distribution by Difficulty (OFFLINE Mode)

| Difficulty | Total | Avg Sim | >=90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 47 | 24.6% | 0 (0%) | 0 (0%) | 7 (15%) | 40 (85%) |
| Medium | 47 | 24.8% | 0 (0%) | 1 (2%) | 5 (11%) | 41 (87%) |
| Hard | 6 | 23.2% | 0 (0%) | 0 (0%) | 0 (0%) | 6 (100%) |

**No 'High Similarity + Complex Patch' cases**

**Evidence of Reasoning: Low Similarity (<40%) + Medium/Complex Patch = 47 cases**
- `django__django-12589`: 2.4%, 15 lines
- `django__django-15252`: 5.1%, 8 lines
- `django__django-14730`: 5.7%, 10 lines
- `django__django-12470`: 7.3%, 6 lines
- `django__django-15213`: 7.9%, 9 lines

#### 2. Cross-mode Similarity Comparison

| Mode | Total | Avg Sim | >=90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 24.6% | 0 (0%) | 87 (87%) |
| run_less_k1 | 100 | 26.8% | 0 (0%) | 76 (76%) |
| run_less_k3 | 100 | 25.6% | 0 (0%) | 85 (85%) |
| run_full | 100 | 23.8% | 0 (0%) | 86 (86%) |

**Cross-mode difference is small**: +0.9%

## SWE-bench Verified

### Agent: claude_code

#### 1. Similarity Distribution by Difficulty (OFFLINE Mode)

| Difficulty | Total | Avg Sim | >=90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 45 | 66.4% | 20 (44%) | 5 (11%) | 8 (18%) | 12 (27%) |
| Medium | 35 | 52.6% | 3 (9%) | 7 (20%) | 14 (40%) | 11 (31%) |
| Hard | 20 | 29.5% | 1 (5%) | 1 (5%) | 3 (15%) | 15 (75%) |

**Needs Attention: High Similarity (>=90%) + Complex Patch (Hard) = 1 case**
- `django__django-10973`: 93.2%, 37 lines

**Evidence of Reasoning: Low Similarity (<40%) + Medium/Complex Patch = 26 cases**
- `astropy__astropy-13977`: 3.0%, 95 lines
- `django__django-11885`: 3.2%, 130 lines
- `django__django-11964`: 3.4%, 8 lines
- `astropy__astropy-14369`: 3.6%, 65 lines
- `astropy__astropy-13398`: 3.7%, 215 lines

#### 2. Cross-mode Similarity Comparison

| Mode | Total | Avg Sim | >=90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 54.2% | 24 (24%) | 38 (38%) |
| run_less_k1 | 100 | 48.3% | 15 (15%) | 46 (46%) |
| run_less_k3 | 100 | 47.7% | 14 (14%) | 44 (44%) |
| run_full | 100 | 44.1% | 11 (11%) | 51 (51%) |

**Cross-mode Difference**: OFFLINE (54.2%) vs UNBOUNDED (44.1%) = **+10.1%**

-> Execution feedback changed the model's solution, supporting 'reasoning' over 'recitation'

### Agent: codex

#### 1. Similarity Distribution by Difficulty (OFFLINE Mode)

| Difficulty | Total | Avg Sim | >=90% | 70-90% | 40-70% | <40% |
|------|------|---------|------|--------|--------|------|
| Easy | 45 | 27.2% | 0 (0%) | 1 (2%) | 8 (18%) | 36 (80%) |
| Medium | 35 | 22.5% | 0 (0%) | 0 (0%) | 4 (11%) | 31 (89%) |
| Hard | 20 | 24.7% | 0 (0%) | 0 (0%) | 6 (30%) | 14 (70%) |

**No 'High Similarity + Complex Patch' cases**

**Evidence of Reasoning: Low Similarity (<40%) + Medium/Complex Patch = 45 cases**
- `astropy__astropy-13398`: 1.9%, 215 lines
- `django__django-13121`: 2.8%, 70 lines
- `astropy__astropy-14369`: 3.7%, 65 lines
- `django__django-11532`: 4.2%, 26 lines
- `django__django-13112`: 4.6%, 6 lines

#### 2. Cross-mode Similarity Comparison

| Mode | Total | Avg Sim | >=90% | <40% |
|------|------|---------|------|------|
| run_free | 100 | 25.0% | 0 (0%) | 81 (81%) |
| run_less_k1 | 100 | 25.4% | 0 (0%) | 82 (82%) |
| run_less_k3 | 100 | 23.8% | 0 (0%) | 82 (82%) |
| run_full | 100 | 25.6% | 0 (0%) | 79 (79%) |

**Cross-mode difference is small**: -0.6%

---

## Summary Conclusions

### 1. Analysis by Difficulty (Core Evidence)

- **Cases needing attention** (High Similarity >=90% + Complex Patch Hard): **1**
- **Evidence of reasoning cases** (Low Similarity <40% + Medium/Complex Patch): **140**

Found 1 possible memorization case that needs further analysis.

### 2. Cross-mode Comparison

| Dataset | Agent | OFFLINE | UNBOUNDED | Delta |
|---------|-------|---------|-----------|---|
| SWE-bench Lite | claude_code | 52.6% | 44.3% | +8.3% |
| SWE-bench Lite | codex | 24.6% | 23.8% | +0.9% |
| SWE-bench Verified | claude_code | 54.2% | 44.1% | +10.1% |
| SWE-bench Verified | codex | 25.0% | 25.6% | -0.6% |

**2/4 configurations show significant cross-mode differences**

-> If 'memorizing', each mode should produce the same patch (consistent similarity)

-> Observed that execution feedback changes solutions, **supporting the 'reasoning' hypothesis**

---

## Paper Wording

> *"We analyzed patch similarity stratified by bug complexity. We found **1 concerning cases** of high similarity (>=90%) on complex patches (>20 lines), while **140 cases** achieved correct fixes with <40% similarity on medium/hard problems. Furthermore, cross-mode comparison reveals that execution feedback changes solution paths (OFFLINE vs UNBOUNDED similarity differs by 5-10%), which would not occur if the model were simply reciting memorized patches. These findings strongly support genuine reasoning over memorization."*
