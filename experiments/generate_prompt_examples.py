#!/usr/bin/env python3
"""
Generate prompt example documentation
"""
import json
from pathlib import Path
from prompt_builder import PromptBuilder

# Load a sample instance
data_path = Path(__file__).parent.parent / "data" / "swe_bench_lite.json"
with open(data_path, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

instance = dataset[0]

# Generate prompts for three modes
run_free = PromptBuilder.build_run_free_prompt(instance)
run_less = PromptBuilder.build_run_less_prompt(instance, k=2)
run_full = PromptBuilder.build_run_full_prompt(instance)

# Generate markdown document
md_content = f"""# Prompt Example Documentation

This document demonstrates prompt examples for three execution modes, using the first instance from the SWE-bench Lite dataset.

## Instance Information

- **Repository**: {instance['repo']}
- **Instance ID**: {instance['instance_id']}
- **Base Commit**: {instance.get('base_commit', 'N/A')[:12]}...

---

## 1. Run-Free Mode (No Code Execution)

**Core Concept**: Agent must fix bugs through pure reasoning, cannot run any code for verification.

```
{run_free}
```

**Key Features**:
- ❌ Cannot execute any code
- 🧠 Must rely on code reading and logical reasoning
- 🎯 Only one chance, must get it right the first time
- 📝 Output git diff format patch

---

## 2. Run-Less Mode (Limited Executions, K=2)

**Core Concept**: Agent has limited execution budget (K times), must treat each execution as a "high-value experiment", emphasizing log instrumentation strategy.

```
{run_less}
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
{run_full}
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

Generation time: {Path(__file__).stat().st_mtime}
"""

# Save to file
output_path = Path(__file__).parent / "PROMPT_EXAMPLES.md"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

print(f"✅ Prompt example documentation generated: {output_path}")
print(f"📄 File size: {output_path.stat().st_size / 1024:.1f} KB")
