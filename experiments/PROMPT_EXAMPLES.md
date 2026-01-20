# Prompt Example Documentation

This document demonstrates prompt examples for three execution modes, using the first instance from the SWE-bench Lite dataset.

## Instance Information

- **Repository**: astropy/astropy
- **Instance ID**: astropy__astropy-12907
- **Base Commit**: d16bfe05a744...

---

## 1. Run-Free Mode (No Code Execution)

**Core Concept**: Agent must fix bugs through pure reasoning, cannot run any code for verification.

```
You are a code repair expert. Your task is to fix the following bug.

**Important restriction: You cannot execute any code.**

You must generate a fix by reading code, understanding logic, and reasoning about the root cause. You can read code multiple times, think repeatedly, and revise your approach, but you cannot verify your fix by running code.

## Repository Information
- Repository: astropy/astropy
- Base Commit: d16bfe05a744909de4b27f5875fe0d4ed41ce607

## Problem Description
Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels
Consider the following model:

```python
from astropy.modeling import models as m
from astropy.modeling.separable import separability_matrix

cm = m.Linear1D(10) & m.Linear1D(5)
```

It's separability matrix as you might expect is a diagonal:

```python
>>> separability_matrix(cm)
array([[ True, False],
       [False,  True]])
```

If I make the model more complex:
```python
>>> separability_matrix(m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5))
array([[ True,  True, False, False],
       [ True,  True, False, False],
       [False, False,  True, False],
       [False, False, False,  True]])
```

The output matrix is again, as expected, the outputs and inputs to the linear models are separable and independent of each other.

If however, I nest these compound models:
```python
>>> separability_matrix(m.Pix2Sky_TAN() & cm)
array([[ True,  True, False, False],
       [ True,  True, False, False],
       [False, False,  True,  True],
       [False, False,  True,  True]])
```
Suddenly the inputs and outputs are no longer separable?

This feels like a bug to me, but I might be missing something?


## Task Requirements
1. Carefully read relevant code files (can read multiple times)
2. Analyze the root cause of the problem
3. Reason out the correct fix
4. Repeatedly check your fix logic
5. Generate a patch in git diff format

## Output Format
Please output your fix patch in git diff format.

Remember: You can repeatedly read code and think, but cannot run code to verify. Please ensure correctness through careful logical reasoning.

```

**Key Features**:
- ❌ Cannot execute any code
- 🧠 Must rely on code reading and logical reasoning
- 🔄 Can read code multiple times, think repeatedly, and revise approach
- 📝 Output git diff format patch

---

## 2. Run-Less Mode (Limited Executions, K=2)

**Core Concept**: Agent has limited execution budget (K times), must treat each execution as a "high-value experiment", emphasizing log instrumentation strategy.

```
You are a code repair expert. Your task is to fix the following bug.

**Important restriction: You can execute code at most 2 times (including running tests, executing scripts, etc.).**

Execution count is a scarce resource, you must treat each execution as a "high-value experiment".

## Repository Information
- Repository: astropy/astropy
- Base Commit: d16bfe05a744909de4b27f5875fe0d4ed41ce607

## Problem Description
Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels
Consider the following model:

```python
from astropy.modeling import models as m
from astropy.modeling.separable import separability_matrix

cm = m.Linear1D(10) & m.Linear1D(5)
```

It's separability matrix as you might expect is a diagonal:

```python
>>> separability_matrix(cm)
array([[ True, False],
       [False,  True]])
```

If I make the model more complex:
```python
>>> separability_matrix(m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5))
array([[ True,  True, False, False],
       [ True,  True, False, False],
       [False, False,  True, False],
       [False, False, False,  True]])
```

The output matrix is again, as expected, the outputs and inputs to the linear models are separable and independent of each other.

If however, I nest these compound models:
```python
>>> separability_matrix(m.Pix2Sky_TAN() & cm)
array([[ True,  True, False, False],
       [ True,  True, False, False],
       [False, False,  True,  True],
       [False, False,  True,  True]])
```
Suddenly the inputs and outputs are no longer separable?

This feels like a bug to me, but I might be missing something?


## Execution Strategy (Critical!)
Before executing code, you must:

1. **Propose hypothesis**: Clearly state where you suspect the problem is
2. **Insert logs**: Add print/log statements at key locations to capture:
   - Variable values
   - Function inputs/outputs
   - Branch paths
   - Exception contexts
3. **Execute verification**: Run code to obtain high-density debugging information
4. **Analyze results**: Determine fix based on log output

## Log Instrumentation Example
```python
# Hypothesis: Suspect calculate() function has issues with negative numbers
def calculate(x):
    print(f"DEBUG: calculate() input x={x}, type={type(x)}")  # Instrumentation
    result = x * 2
    print(f"DEBUG: calculate() output result={result}")  # Instrumentation
    return result
```

## Execution Budget
- Current remaining executions: 2
- Before each execution, state: what is your hypothesis, what are you verifying
- After execution, analyze: what information did the logs tell you

## Output Format
Finally output your fix patch in git diff format.

Remember: Treat execution as expensive experiments, not free trial-and-error buttons. One smart execution beats ten blind attempts.

```

**Key Features**:
- 🔢 Maximum K executions (K=2 in this example)
- 🔬 Must propose hypothesis before each execution
- 📊 Emphasize log instrumentation (print/log) to obtain high-density debugging information
- 💡 Execution is a scarce resource, not a free trial-and-error button
- 📝 Final output in git diff format patch

**Log Instrumentation Strategy**:
- Add print/log statements at key locations
- Capture variable values, function inputs/outputs, branch paths, exception contexts
- One smart execution beats ten blind attempts

---

## 3. Run-Full Mode (Unlimited Executions)

**Core Concept**: Agent can freely execute code to debug and verify fixes, similar to traditional development workflow.

```
You are a code repair expert. Your task is to fix the following bug.

You can freely execute code to debug and verify your fix.

## Repository Information
- Repository: astropy/astropy
- Base Commit: d16bfe05a744909de4b27f5875fe0d4ed41ce607

## Problem Description
Modeling's `separability_matrix` does not compute separability correctly for nested CompoundModels
Consider the following model:

```python
from astropy.modeling import models as m
from astropy.modeling.separable import separability_matrix

cm = m.Linear1D(10) & m.Linear1D(5)
```

It's separability matrix as you might expect is a diagonal:

```python
>>> separability_matrix(cm)
array([[ True, False],
       [False,  True]])
```

If I make the model more complex:
```python
>>> separability_matrix(m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5))
array([[ True,  True, False, False],
       [ True,  True, False, False],
       [False, False,  True, False],
       [False, False, False,  True]])
```

The output matrix is again, as expected, the outputs and inputs to the linear models are separable and independent of each other.

If however, I nest these compound models:
```python
>>> separability_matrix(m.Pix2Sky_TAN() & cm)
array([[ True,  True, False, False],
       [ True,  True, False, False],
       [False, False,  True,  True],
       [False, False,  True,  True]])
```
Suddenly the inputs and outputs are no longer separable?

This feels like a bug to me, but I might be missing something?


## Workflow
1. Read relevant code
2. Run tests to see failure cases
3. Analyze error messages
4. Attempt fixes
5. Run tests for verification
6. If tests fail, repeat steps 3-5

## Output Format
Finally output your fix patch in git diff format.

You can run code and tests multiple times until all tests pass.

```

**Key Features**:
- ✅ Can freely execute code
- 🔄 Can run tests multiple times for verification
- 🐛 Can iteratively debug until all tests pass
- 📝 Final output in git diff format patch

**Workflow**:
1. Read relevant code
2. Run tests to see failure cases
3. Analyze error messages
4. Attempt fixes
5. Run tests for verification
6. If tests fail, repeat steps 3-5

---

## Comparison Summary

| Feature | Run-Free | Run-Less (K=2) | Run-Full |
|---------|----------|----------------|----------|
| Execution Count | 0 times | Max K times | Unlimited |
| Strategy Focus | Pure reasoning | Log instrumentation | Iterative debugging |
| Difficulty | Highest | Medium | Lowest |
| Token Cost | Lowest | Medium | Highest |
| Use Case | Simple bugs | Medium complexity | Complex bugs |

---

## Research Hypotheses

Our research aims to explore:

1. **Run-Free vs Run-Full**: How much does execution environment impact code repair capability?
2. **Optimal K Value for Run-Less**: Can limited executions approach Run-Full effectiveness?
3. **Cost-Benefit Analysis**: Can Run-Less achieve optimal balance between cost and effectiveness?
4. **Log Instrumentation Strategy**: Does emphasizing log instrumentation improve Run-Less success rate?

---

Generation time: 1768335490.4406393
