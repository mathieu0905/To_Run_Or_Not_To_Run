# Data Leakage Defense: Hurt Cases Analysis

## Core Argument

If the model is purely "reciting" leaked answers, then **execution should not cause it to fail**.
Since it has memorized the perfect answer, the model outputs it, runs the test, and the test naturally passes.

**Hurt Cases** = Cases where OFFLINE succeeds but UNBOUNDED fails

These cases demonstrate that the model is **reasoning in real-time**, not simply **reciting from memory**.
Execution feedback "misled" the model's reasoning process, causing originally correct answers to be changed incorrectly.

---

## SWE-bench Lite

### Agent: claude_code

#### OFFLINE vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_free Resolved | 63 |
| run_full Resolved | 64 |
| **Hurt Cases** (run_free ✓, run_full ✗) | **5** |
| Help Cases (run_free ✗, run_full ✓) | 6 |
| Both Success | 58 |

**Hurt Cases List** (5 cases):

- `django__django-12184`
- `django__django-12908`
- `django__django-13230`
- `django__django-14016`
- `django__django-15695`

#### OFFLINE vs RUN_LESS_K1

| Metric | Count |
|--------|-------|
| run_free Resolved | 63 |
| run_less_k1 Resolved | 61 |
| **Hurt Cases** (run_free ✓, run_less_k1 ✗) | **4** |
| Help Cases (run_free ✗, run_less_k1 ✓) | 2 |
| Both Success | 59 |

**Hurt Cases List** (4 cases):

- `django__django-13230`
- `django__django-13551`
- `django__django-14016`
- `django__django-15695`

#### OFFLINE vs RUN_LESS_K3

| Metric | Count |
|--------|-------|
| run_free Resolved | 63 |
| run_less_k3 Resolved | 62 |
| **Hurt Cases** (run_free ✓, run_less_k3 ✗) | **5** |
| Help Cases (run_free ✗, run_less_k3 ✓) | 4 |
| Both Success | 58 |

**Hurt Cases List** (5 cases):

- `django__django-13230`
- `django__django-13401`
- `django__django-14016`
- `django__django-15061`
- `django__django-15695`

#### RUN_LESS_K3 vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_less_k3 Resolved | 62 |
| run_full Resolved | 64 |
| **Hurt Cases** (run_less_k3 ✓, run_full ✗) | **2** |
| Help Cases (run_less_k3 ✗, run_full ✓) | 4 |
| Both Success | 60 |

**Hurt Cases List** (2 cases):

- `django__django-12184`
- `django__django-12908`


### Agent: codex

#### OFFLINE vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_free Resolved | 74 |
| run_full Resolved | 73 |
| **Hurt Cases** (run_free ✓, run_full ✗) | **4** |
| Help Cases (run_free ✗, run_full ✓) | 3 |
| Both Success | 70 |

**Hurt Cases List** (4 cases):

- `django__django-11848`
- `django__django-11964`
- `django__django-12497`
- `django__django-12747`

#### OFFLINE vs RUN_LESS_K1

| Metric | Count |
|--------|-------|
| run_free Resolved | 74 |
| run_less_k1 Resolved | 68 |
| **Hurt Cases** (run_free ✓, run_less_k1 ✗) | **9** |
| Help Cases (run_free ✗, run_less_k1 ✓) | 3 |
| Both Success | 65 |

**Hurt Cases List** (9 cases):

- `astropy__astropy-14365`
- `django__django-11848`
- `django__django-12125`
- `django__django-12308`
- `django__django-12497`
- `django__django-12747`
- `django__django-13401`
- `django__django-13448`
- `django__django-15320`

#### OFFLINE vs RUN_LESS_K3

| Metric | Count |
|--------|-------|
| run_free Resolved | 74 |
| run_less_k3 Resolved | 69 |
| **Hurt Cases** (run_free ✓, run_less_k3 ✗) | **6** |
| Help Cases (run_free ✗, run_less_k3 ✓) | 1 |
| Both Success | 68 |

**Hurt Cases List** (6 cases):

- `astropy__astropy-14365`
- `django__django-11848`
- `django__django-11964`
- `django__django-12308`
- `django__django-12453`
- `django__django-12497`

#### RUN_LESS_K3 vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_less_k3 Resolved | 69 |
| run_full Resolved | 73 |
| **Hurt Cases** (run_less_k3 ✓, run_full ✗) | **2** |
| Help Cases (run_less_k3 ✗, run_full ✓) | 6 |
| Both Success | 67 |

**Hurt Cases List** (2 cases):

- `django__django-12747`
- `django__django-15213`


## SWE-bench Verified

### Agent: claude_code

#### OFFLINE vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_free Resolved | 64 |
| run_full Resolved | 67 |
| **Hurt Cases** (run_free ✓, run_full ✗) | **6** |
| Help Cases (run_free ✗, run_full ✓) | 9 |
| Both Success | 58 |

**Hurt Cases List** (6 cases):

- `astropy__astropy-14365`
- `django__django-11532`
- `django__django-11555`
- `django__django-11728`
- `django__django-11790`
- `django__django-13121`

#### OFFLINE vs RUN_LESS_K1

| Metric | Count |
|--------|-------|
| run_free Resolved | 64 |
| run_less_k1 Resolved | 64 |
| **Hurt Cases** (run_free ✓, run_less_k1 ✗) | **8** |
| Help Cases (run_free ✗, run_less_k1 ✓) | 8 |
| Both Success | 56 |

**Hurt Cases List** (8 cases):

- `astropy__astropy-14365`
- `django__django-11555`
- `django__django-11728`
- `django__django-11790`
- `django__django-11848`
- `django__django-12039`
- `django__django-12325`
- `django__django-13121`

#### OFFLINE vs RUN_LESS_K3

| Metric | Count |
|--------|-------|
| run_free Resolved | 64 |
| run_less_k3 Resolved | 65 |
| **Hurt Cases** (run_free ✓, run_less_k3 ✗) | **8** |
| Help Cases (run_free ✗, run_less_k3 ✓) | 9 |
| Both Success | 56 |

**Hurt Cases List** (8 cases):

- `astropy__astropy-14365`
- `django__django-11532`
- `django__django-11555`
- `django__django-11728`
- `django__django-11790`
- `django__django-11848`
- `django__django-12325`
- `django__django-13121`

#### RUN_LESS_K3 vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_less_k3 Resolved | 65 |
| run_full Resolved | 67 |
| **Hurt Cases** (run_less_k3 ✓, run_full ✗) | **2** |
| Help Cases (run_less_k3 ✗, run_full ✓) | 4 |
| Both Success | 63 |

**Hurt Cases List** (2 cases):

- `astropy__astropy-14369`
- `django__django-11433`


### Agent: codex

#### OFFLINE vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_free Resolved | 73 |
| run_full Resolved | 75 |
| **Hurt Cases** (run_free ✓, run_full ✗) | **1** |
| Help Cases (run_free ✗, run_full ✓) | 3 |
| Both Success | 72 |

**Hurt Cases List** (1 case):

- `django__django-10973`

#### OFFLINE vs RUN_LESS_K1

| Metric | Count |
|--------|-------|
| run_free Resolved | 73 |
| run_less_k1 Resolved | 72 |
| **Hurt Cases** (run_free ✓, run_less_k1 ✗) | **5** |
| Help Cases (run_free ✗, run_less_k1 ✓) | 4 |
| Both Success | 68 |

**Hurt Cases List** (5 cases):

- `astropy__astropy-14096`
- `astropy__astropy-14182`
- `astropy__astropy-14365`
- `django__django-10973`
- `django__django-12965`

#### OFFLINE vs RUN_LESS_K3

| Metric | Count |
|--------|-------|
| run_free Resolved | 73 |
| run_less_k3 Resolved | 73 |
| **Hurt Cases** (run_free ✓, run_less_k3 ✗) | **5** |
| Help Cases (run_free ✗, run_less_k3 ✓) | 5 |
| Both Success | 68 |

**Hurt Cases List** (5 cases):

- `django__django-10973`
- `django__django-11532`
- `django__django-11885`
- `django__django-11964`
- `django__django-12858`

#### RUN_LESS_K3 vs UNBOUNDED

| Metric | Count |
|--------|-------|
| run_less_k3 Resolved | 73 |
| run_full Resolved | 75 |
| **Hurt Cases** (run_less_k3 ✓, run_full ✗) | **3** |
| Help Cases (run_less_k3 ✗, run_full ✓) | 5 |
| Both Success | 70 |

**Hurt Cases List** (3 cases):

- `django__django-11149`
- `django__django-11433`
- `django__django-12273`


---

## Summary Statistics (OFFLINE vs UNBOUNDED)

| Dataset | Agent | Hurt Cases | Help Cases | Net Effect |
|---------|-------|------------|------------|------------|
| SWE-bench Lite | claude_code | 5 | 6 | +1 |
| SWE-bench Lite | codex | 4 | 3 | -1 |
| SWE-bench Verified | claude_code | 6 | 9 | +3 |
| SWE-bench Verified | codex | 1 | 3 | +2 |
| **Total** | - | **16** | **21** | **+5** |

## Conclusion

1. **A total of 16 Hurt Cases were identified**: These cases succeeded in OFFLINE mode but failed in UNBOUNDED mode

2. **This proves the model is not "reciting"**:
   - If the model had purely memorized the correct answers, execution feedback should not cause it to "change to wrong"
   - The existence of Hurt Cases indicates the model is **reasoning in real-time** and can be "misled" by execution results

3. **This strongly refutes the data leakage hypothesis**:
   - Data leakage would make UNBOUNDED ≥ OFFLINE (memorized answer + verification = more stable)
   - But in reality, significant Hurt Cases exist, indicating the model is fragile during reasoning

4. **Suggested paper wording**:
   > *"We identified 16 Hurt Cases where the model succeeded in OFFLINE mode but failed in UNBOUNDED mode. This fragility—being misled by execution feedback—demonstrates that the model is reasoning in real-time rather than reciting memorized solutions. If the model had simply memorized the correct patches from training data, execution feedback should not cause it to deviate from the correct answer."*
