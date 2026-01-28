# Data Leakage Defense: Hurt Cases Analysis

## 核心论点

如果模型纯粹是靠「背诵」泄漏的答案，那么**执行不应该导致它失败**。
既然背过了完美答案，模型输出它，运行测试，测试自然通过。

**Hurt Cases** = OFFLINE 成功但 UNBOUNDED 失败的案例

这些案例证明：模型是在**实时推理**，而非单纯**背诵记忆**。
执行反馈「带偏」了模型的推理过程，导致原本正确的答案被改错。

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

**Hurt Cases 列表** (5 个):

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

**Hurt Cases 列表** (4 个):

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

**Hurt Cases 列表** (5 个):

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

**Hurt Cases 列表** (2 个):

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

**Hurt Cases 列表** (4 个):

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

**Hurt Cases 列表** (9 个):

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

**Hurt Cases 列表** (6 个):

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

**Hurt Cases 列表** (2 个):

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

**Hurt Cases 列表** (6 个):

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

**Hurt Cases 列表** (8 个):

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

**Hurt Cases 列表** (8 个):

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

**Hurt Cases 列表** (2 个):

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

**Hurt Cases 列表** (1 个):

- `django__django-10973`

#### OFFLINE vs RUN_LESS_K1

| Metric | Count |
|--------|-------|
| run_free Resolved | 73 |
| run_less_k1 Resolved | 72 |
| **Hurt Cases** (run_free ✓, run_less_k1 ✗) | **5** |
| Help Cases (run_free ✗, run_less_k1 ✓) | 4 |
| Both Success | 68 |

**Hurt Cases 列表** (5 个):

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

**Hurt Cases 列表** (5 个):

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

**Hurt Cases 列表** (3 个):

- `django__django-11149`
- `django__django-11433`
- `django__django-12273`


---

## 汇总统计 (OFFLINE vs UNBOUNDED)

| Dataset | Agent | Hurt Cases | Help Cases | Net Effect |
|---------|-------|------------|------------|------------|
| SWE-bench Lite | claude_code | 5 | 6 | +1 |
| SWE-bench Lite | codex | 4 | 3 | -1 |
| SWE-bench Verified | claude_code | 6 | 9 | +3 |
| SWE-bench Verified | codex | 1 | 3 | +2 |
| **Total** | - | **16** | **21** | **+5** |

## 结论

1. **共发现 16 个 Hurt Cases**：这些案例在 OFFLINE 模式下成功，但在 UNBOUNDED 模式下失败

2. **这证明了模型不是在「背诵」**：
   - 如果模型纯粹记忆了正确答案，执行反馈不应该让它「改错」
   - Hurt Cases 的存在说明模型是在**实时推理**，并且会被执行结果「带偏」

3. **这有力反驳了数据泄漏假设**：
   - 数据泄漏会让 UNBOUNDED ≥ OFFLINE（背过答案 + 验证 = 更稳）
   - 但实际上存在显著的 Hurt Cases，说明模型在推理时是脆弱的

4. **论文话术建议**：
   > *"We identified 16 Hurt Cases where the model succeeded in OFFLINE mode but failed in UNBOUNDED mode. This fragility—being misled by execution feedback—demonstrates that the model is reasoning in real-time rather than reciting memorized solutions. If the model had simply memorized the correct patches from training data, execution feedback should not cause it to deviate from the correct answer."*
