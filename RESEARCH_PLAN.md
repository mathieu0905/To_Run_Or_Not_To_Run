# Run-Free / Run-Less / Run-Full: Research Execution Plan

## 1. Research Overview

### 1.1 Core Question
> In code repair tasks, is the execution environment a "necessary capability" or an "engineering shortcut"?

### 1.2 Four Execution Paradigms

| Mode | Academic Name | Meaning | Agent Behavior | Constraint Type |
|------|---------------|---------|----------------|-----------------|
| **Run-Free** | Zero-Exec | No execution, pure reasoning-based repair | Read → Infer → Fix | Hard prohibition |
| **Run-Less** | Budget-Exec | Limited executions (K-time budget) | Hypothesize → Instrument → Execute → Fix | Hard limit |
| **Run-Cost** | Cost-Aware-Exec | Cost-constrained, model makes autonomous decisions | Assess Confidence → Decide → Execute (if needed) → Fix | Soft constraint |
| **Run-Full** | Unrestricted-Exec | Unlimited execution | Write → Run → See Error → Revise → Repeat | No constraint |

### 1.3 Core Arguments
1. Existing Agent research over-relies on Run-Full, making Agents "lazy"
2. Execution should be viewed as an "expensive decision resource", not a "free button"
3. **"We trade execution frequency for execution informativeness"**

---

## 2. Experimental Design

### 2.1 Experimental Variables

**Single Control Variable**: Execution Access

| Setting | Execution Count | Fine-grained Logging | Constraint Type |
|---------|-----------------|---------------------|-----------------|
| A (Run-Full) | Unlimited | No (stderr only) | No constraint |
| B (Run-Less) | K times | No | Hard limit |
| C (Run-Less + Log) | K times | Yes (Agent free instrumentation) | Hard limit |
| D (Run-Cost) | Unlimited but costly | Optional (Agent decides) | Soft constraint |
| E (Run-Free) | 0 | - | Hard prohibition |

**K Value Settings**: K ∈ {1, 2, 3}, run multiple times for each value and take average

### 2.2 Research Questions

**RQ1: Performance vs. Budget**
- X-axis: Execution budget (0, 1, 3, 5, 10, ∞)
- Y-axis: Pass@1 success rate
- Expected: Diminishing marginal returns, Run-Less may ≈ Run-Full

**RQ2: Information Density**
- Compare Standard Output vs. Instrumented Logging
- Expected: 1 execution with logging ≈ 5 regular executions

**RQ3: Behavior Analysis**
- Analyze Agent's token distribution
- Run-Free: All tokens spent on reasoning
- Run-Full: All tokens spent on reading errors and retrying
- Run-Less: Exhibits "hypothesis-validation" behavior pattern

**RQ4: Code Quality**
- Evaluate readability and generalizability of repaired code
- Expected: Run-Full produces Spaghetti Code, Run-Less is more concise

**RQ5: Self-Confidence Calibration (Run-Cost specific)**
- Does the model's confidence level match actual success rate?
- Evaluation metrics:
  - Success rate when not running tests at high confidence (>90%)
  - Value of running tests at low confidence (<50%)
  - Confidence-success rate calibration curve
  - Whether the model is overconfident or overly cautious

### 2.3 Benchmark
- **SWE-bench Lite**: 300 problems, quick validation
- **SWE-bench Verified**: 500 problems, more rigorous validation set

### 2.4 Model and Agent Selection
- **Primary**: Claude Opus + Claude Code
- **Optional Extension**: GPT-5.2 + Codex (if necessary)

### 2.5 Evaluation Metrics System

| Metric | Type | Description |
|--------|------|-------------|
| **Pass@1** | Basic metric | First submission pass rate |
| **Token Cost** | Performance metric | Total token consumption |
| **Turn Count** | Efficiency metric | Number of interaction rounds |
| **Execution Count** | Resource metric | Actual number of executions |
| **First Correct Turn** | Efficiency metric | Round number when first correct patch appears |
| **Patch Size** | Quality metric | Lines of patch code (smaller is better) |
| **Reasoning Ratio** | Behavior metric | Reasoning tokens / Total tokens (distinguishes three modes) |
| **Retry Rate** | Behavior metric | Retry count / Total attempts (expected higher for Run-Full) |

---

## 3. Technical Implementation

### 3.1 Agent Architecture

```
┌─────────────────────────────────────────────┐
│                Agent Core                    │
├─────────────────────────────────────────────┤
│  1. Code Reader (read code)                  │
│  2. Reasoner (infer bug location)            │
│  3. Instrumenter (generate instrumentation)  │
│     [Run-Less]                               │
│  4. Executor (execute code)                  │
│     [Run-Less/Full]                          │
│  5. Patcher (generate repair patch)          │
└─────────────────────────────────────────────┘
```

### 3.2 Run-Less Core Mechanism

**Planner**: Agent outputs an Action at each step:
1. **Thinking**: Continue reasoning, doesn't consume Run budget
2. **Instrumentation**: Write and insert Log code
3. **Execution**: Consumes 1 Run budget, obtains Log
4. **Submission**: Submit repair

**Instrumentation Format**:
```python
# Agent must answer:
# Hypothesis: I suspect the calculation() function has issues when handling negative numbers
# Probe: Insert at entry point
print(f"DEBUG: input={x}, state={self.state}")
# Outcome: Obtain Trace instead of just Error
```

### 3.3 System Prompt Design

**Run-Free Prompt**:
```
You are a code repair agent. You CANNOT execute any code.
Read the buggy code, understand the logic, and generate a fix.
You must get it right on the first try.
```

**Run-Less Prompt**:
```
You have a strict budget of {K} executions. You cannot waste them.
Before you run the code, you must:
1. Formulate a hypothesis (what might be wrong?)
2. Insert detailed logging/print statements to capture specific variables
3. Only then execute
Treat every execution as a high-stakes experiment.
```

**Run-Cost Prompt**:
```
Every test execution has a cost (time, resources, money).
Before running tests, evaluate your confidence level:
- High confidence (>90%): Consider not running tests
- Medium confidence (50-90%): Evaluate if the information gain is worth the cost
- Low confidence (<50%): Usually worth running tests

For each decision, output:
- Current confidence level: X%
- Decision: [Run / Don't Run]
- Reasoning: [Explain why]
```

**Run-Full Prompt**:
```
You can execute code freely. Fix the bug by running tests,
observing errors, and iterating until all tests pass.
```

---

## 4. Execution Steps

### Phase 1: Environment Setup
- [ ] Set up SWE-bench evaluation environment
- [ ] Prepare Docker sandbox for code execution
- [ ] Implement Agent framework (supports switching between three modes)
- [ ] Implement logging instrumentation module

### Phase 2: MVP Experiment
- [ ] Select 20 SWE-bench Lite problems
- [ ] Implement Group A (Run-Full): Allow 10 executions
- [ ] Implement Group B (Run-Less + Log): Only allow 1-2 executions, must instrument first
- [ ] Compare success rate, token consumption, code quality

### Phase 3: Full Experiment
- [ ] Extend to full SWE-bench Lite (300 problems)
- [ ] Test different execution budgets (K = 0, 1, 3, 5, 10, ∞)
- [ ] Collect behavioral data (token distribution, execution patterns)
- [ ] Code quality evaluation (manual + GPT-4 scoring)

### Phase 4: Analysis and Writing
- [ ] Draw Efficiency-Effectiveness Frontier graph
- [ ] Behavior pattern analysis (Gambler vs. Scientist)
- [ ] Write paper

---

## 5. Expected Results

### 5.1 Core Finding
> **"One smart run is worth ten blind runs."**

### 5.2 Expected Curve
```
Success Rate
    │
    │         ┌─────────── Run-Full (plateau)
    │        /
    │   ┌───/─────────── Run-Less + Log (reaches quickly)
    │  /
    │ /
    │/
    └──────────────────────────────────────── Execution Budget
       0    1    3    5    10   ∞
```

### 5.3 Paper Narrative
1. **Status Quo**: Everyone thinks giving Agents more executions is better
2. **Problem**: Unlimited execution makes Agents lazy, falling into "patch loops"
3. **Method**: Log-Driven Budgeted Execution
4. **Results**: 2 executions with instrumentation ≈ or > 50 blind executions
5. **Conclusion**: Agent design should focus on "experimental design" rather than Sandbox concurrency capabilities

---

## 6. Paper Positioning

### 6.1 Target Conference
- **First Choice**: ISSTA 2026 (aligns with dynamic analysis/instrumentation tradition)
- **Alternatives**: FSE / ICSE

### 6.2 Title Candidates
- *Is More Execution Always Better? The "Less is More" Paradox in LLM-based Program Repair*
- *Agent as a Scientist: Hypothesis-Driven Debugging with Budget-Constrained Execution*
- *Quality over Quantity: Why Constraint Elicits Better Reasoning in Code Agents*

### 6.3 Distinguished Paper Elements
1. **Counter-intuitive**: Run less, think more
2. **Green AI**: Reduce execution costs
3. **Theoretical Height**: Debug = Experimental Design Problem
4. **Practical Significance**: Production/confidential environments are inherently Run-Less

---

## 7. Confirmed Decisions

1. **Execution Budget K**: K ∈ {1, 2, 3}, run multiple times for each value and take average
2. **Instrumentation Granularity**: Agent free instrumentation (no template restrictions)
3. **Benchmark**: SWE-bench Lite + SWE-bench Verified
4. **Model**: Claude Opus + Claude Code (primary), GPT-5.2 + Codex (optional extension)
5. **Evaluation Metrics**: Pass@1 (basic) + Token Cost (performance) + behavioral metrics (see 2.5)

---

## 8. Next Steps

1. **Immediate**: Set up SWE-bench environment
2. **This Week**: Complete MVP experiment (20 problems comparison)
3. **Validate Hypothesis**: Run-Less + Log ≈ Run-Full
4. **Based on Results**: Adjust experimental design, expand scale
