# Prompt Design for Execution-Constrained Code Repair

## 1. Overview

This document describes the prompt design methodology used to study the impact of execution constraints on LLM code repair capabilities. We designed 4 execution modes, using strict variable control to isolate the influence of the single factor of "execution capability".

## 2. Design Principles

### 2.1 Controlled Variables

To ensure comparability of experimental results, we adopted a strict controlled variable design:

- **Unified Base Structure**: All mode prompts follow a completely consistent structural framework
- **Single Point of Difference**: The only difference is in the "Execution Constraint" section
- **Minimal Guidance**: Avoid introducing additional workflow suggestions, code examples, or strategy guidance
- **Consistent Output Requirements**: All modes use the same output format requirements

### 2.2 Prompt Structure

All mode prompts follow this unified structure:

```
1. Task Description
2. Repository Information
3. Problem Description
4. Execution Constraint ← The only point of difference
5. What You CAN Do
6. What You CANNOT Do
7. Output Format
```

### 2.3 Cost Model Design

For modes involving cost assessment (Run-Less and Run-Cost), we adopted the following design principles:

- **No Hard-Coded Cost Values**: Only provide reference ranges (~1.0 and ~0.3), letting the Agent estimate autonomously
- **Distinguish Execution Types**:
  - High-cost execution: Full test suites (pytest, unittest, Django tests, etc.) ≈ 1.0 point
  - Low-cost execution: Simple scripts (python script.py) ≈ 0.3 point
- **Require Explicit Output**: Force the Agent to output cost assessment and budget tracking before and after execution

## 3. Execution Modes

### 3.1 Run-Free (No Execution)

**Definition**: The Agent cannot run tests or execute Python scripts at all, and can only fix code through static analysis.

**Execution Constraint**:
```
You CANNOT run tests or execute Python scripts.
You must generate a fix by reading code and reasoning about the root cause.
```

**Characteristics**:
- Can only use bash commands to view files (ls, cat, grep, etc.)
- Cannot verify the correctness of fixes
- Completely relies on code understanding and logical reasoning capabilities

**Research Purpose**: Serves as a performance lower bound baseline, testing pure static analysis repair capabilities.

---

### 3.2 Run-Less (Limited Cost Budget)

**Definition**: The Agent has a limited execution cost budget (k points) and needs to strategically allocate resources.

**Execution Constraint**:
```
You have a limited execution budget of k.0 cost points.

Different executions have different costs. Estimate the cost before each execution:
- Running full test suites (pytest, unittest, Django tests, etc.): ~1.0 point
- Running simple scripts (python script.py): ~0.3 point

Before each execution, output:
[EXECUTION] Estimated cost: X.X points | Remaining budget: Y.Y points | Purpose: ...

After each execution, output:
Remaining budget: X.X points
```

**Characteristics**:
- Need to estimate cost before execution
- Must track remaining budget
- Forced to make strategic decisions (when to execute, what to execute)

**Research Purpose**: Test the Agent's decision-making ability and resource management capability under resource constraints.

**Experimental Parameters**:
- k=1: Extremely constrained (approximately 1 full test or 3 script executions)
- k=2: Moderately constrained (approximately 2 full tests or 6 script executions)
- k=3: Lightly constrained (approximately 3 full tests or 10 script executions)

---

### 3.3 Run-Cost (Cost-Aware but Unlimited)

**Definition**: The Agent can execute unlimited times, but needs to be aware that each execution has a cost.

**Execution Constraint**:
```
Every Python execution has a cost (time, compute, money).
You can run code without hard limits, but be cost-aware in your decisions.

Different executions have different costs. Estimate the cost before each execution:
- Running full test suites (pytest, unittest, Django tests, etc.): ~1.0 point
- Running simple scripts (python script.py): ~0.3 point

Before each execution, output:
[EXECUTION] Estimated cost: X.X points | Purpose: ...
```

**Characteristics**:
- No hard budget limit
- Need to assess cost before execution
- Encourages cost-benefit trade-offs

**Research Purpose**: Test whether cost awareness can reduce resource consumption without sacrificing performance.

---

### 3.4 Run-Full (Unlimited Execution)

**Definition**: The Agent can freely run tests and scripts without any restrictions.

**Execution Constraint**:
```
You have UNLIMITED Python executions.
Feel free to run tests and scripts as many times as needed.
```

**Characteristics**:
- Completely unrestricted
- No cost assessment needed
- Closest to "ideal state"

**Research Purpose**: Serves as a performance upper bound baseline, representing the Agent's best performance under unconstrained conditions.

## 4. Experimental Hypotheses

Based on the above design, we propose the following research hypotheses:

### H1: Impact of Execution Capability
```
Performance: Run-Free < Run-Less < Run-Cost ≤ Run-Full
```
Execution capability has a significant positive impact on repair success rate.

### H2: Resource Management Capability
Under limited budget (Run-Less), the Agent can:
- Correctly estimate the cost of different executions
- Make reasonable resource allocation decisions
- Complete repair tasks within budget constraints

### H3: Effect of Cost Awareness
Run-Cost mode compared to Run-Full:
- Significantly reduced execution count (resource savings)
- No significant difference in repair success rate (performance maintained)

### H4: Budget Threshold
There exists a budget threshold k*, where when k ≥ k*, Run-Less performance approaches Run-Full.

## 5. Implementation Details

### 5.1 Cost Tracking

In Run-Less and Run-Cost modes, we track costs by analyzing the Agent's output:

- **Pre-execution Declaration**: Match `[EXECUTION]` markers, extract estimated cost
- **Post-execution Tracking**: Match `Remaining budget` output, verify budget management
- **Actual Cost Calculation**: Automatically categorize based on executed command type:
  - High-cost: pytest, unittest, Django tests and other test frameworks
  - Low-cost: python script.py and other script executions

### 5.2 Metrics

We collect the following metrics to evaluate the performance of different modes:

- **Repair Success Rate**: Verified through SWE-bench test suite
- **Execution Count**:
  - Total execution count
  - High-cost execution count
  - Low-cost execution count
- **Cost Consumption**: Total cost points (high-cost × 1.0 + low-cost × 0.3)
- **Interaction Rounds**: Number of interactions between Agent and environment
- **Execution Time**: Total time to complete the task

## 6. Design Rationale

### 6.1 Why Not Hard-Code Cost Values?

We chose to provide reference ranges (~1.0 and ~0.3) rather than exact values for the following reasons:

1. **Avoid Over-Constraint**: Exact values may lead the Agent to mechanically follow rules rather than truly understand cost
2. **Encourage Autonomous Judgment**: The Agent needs to estimate based on specific circumstances (test scale, complexity)
3. **Closer to Real Scenarios**: In actual development, execution costs are often estimates rather than exact values

### 6.2 Why Distinguish High-Cost and Low-Cost Execution?

Preliminary experiments found that if execution types are not distinguished, the Agent may bypass budget limits through multiple low-cost executions (scripts). Distinguishing execution types can:

1. **More Accurately Reflect Real Costs**: Full test suites cost far more than simple scripts
2. **Prevent Budget Circumvention**: Avoid the Agent replacing one test execution with multiple script executions
3. **Encourage Efficient Strategies**: Guide the Agent to first use low-cost scripts to locate problems, then use high-cost tests to verify

### 6.3 Why Doesn't Run-Cost Limit Budget?

The design purpose of Run-Cost mode is to test "cost awareness" rather than "cost limitation":

1. **Isolate the Impact of Cost Awareness**: Compare with Run-Full to evaluate the effect of cost awareness itself
2. **Avoid Hard Constraints**: Test whether the Agent can autonomously save resources without mandatory requirements
3. **Closer to Real Scenarios**: In actual development, developers usually have cost awareness but no hard limits

## 7. Validation

### 7.1 Prompt Consistency Validation

We validate prompt consistency through the following methods:

- Non-constraint parts of all modes are completely identical (string matching)
- The only difference is in the "Execution Constraint" section
- No additional workflow suggestions or code examples

### 7.2 Cost Tracking Validation

We validate whether the Agent correctly follows cost tracking requirements:

- Run-Less: Check if budget tracking information is output
- Run-Cost: Check if cost assessment information is output
- Verify if actual execution count is consistent with declared costs

## 8. Limitations and Future Work

### 8.1 Current Limitations

1. **Simplified Cost Model**: Actual execution costs are affected by multiple factors (test count, complexity, environment, etc.)
2. **Budget Compliance Depends on Agent**: The Agent may not fully comply with budget constraints
3. **Single Task Type**: Currently only validated on code repair tasks

### 8.2 Future Directions

1. **Dynamic Cost Model**: Dynamically adjust costs based on actual execution time
2. **Enforce Budget Constraints**: Enforce budget limits at the system level
3. **Extend to Other Tasks**: Test effects on code generation, refactoring, and other tasks

## 9. Conclusion

This prompt design isolates the influence of the single factor of "execution capability" through a strict controlled variable method. The 4 execution modes form a continuous spectrum from completely constrained to completely free, enabling us to systematically study the impact of execution constraints on LLM code repair capabilities.

Key innovations of the design include:
1. Unified prompt structure ensuring experimental comparability
2. Flexible cost model encouraging Agent autonomous judgment
3. Distinguishing high-cost and low-cost execution to more accurately reflect real scenarios
4. Run-Cost mode isolating the independent effect of cost awareness

---

**Document Version**: 1.0
**Last Updated**: 2026-01-14
**Implementation File**: `prompt_builder.py`
