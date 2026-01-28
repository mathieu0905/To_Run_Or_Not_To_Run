# RQ2 In-Depth Analysis: Why Doesn't Codex Show Significant Token Reduction in run_free Mode?

## Core Question

- Codex run_free vs run_full token savings only 0.8-13.4%
- Claude Code savings reach 56-62%
- This indicates fundamental behavioral differences between Codex and Claude Code

---

## 1. Overall Behavior Comparison

### SWE-bench Lite

| Metric | Codex run_free | Codex run_full | CC run_free | CC run_full |
|------|----------------|----------------|-------------|-------------|
| Avg Commands | 21.6 | 23.2 | 6.9 | 17.9 |
| Avg Input Tokens | 400,765 | 464,133 | 66,943 | 154,144 |
| Avg Reasoning | 15.4 | 16.5 | 17.1 | 33.0 |
| Avg File Changes | 2.9 | 3.1 | 2.0 | 5.4 |
| **Token Change** | -13.7% | - | -56.6% | - |
| **Command Count Change** | -6.7% | - | -61.2% | - |

### SWE-bench Verified

| Metric | Codex run_free | Codex run_full | CC run_free | CC run_full |
|------|----------------|----------------|-------------|-------------|
| Avg Commands | 25.2 | 24.3 | 6.4 | 17.6 |
| Avg Input Tokens | 529,305 | 534,277 | 61,614 | 164,054 |
| **Token Change** | -0.9% | - | -62.4% | - |
| **Command Count Change** | +3.5% | - | -63.6% | - |

---

## 2. Command Type Distribution Comparison

### SWE-bench Lite

| Mode | Agent | Test Exec | Python Snippet | File View | Search | Dir Browse | Other |
|------|-------|-----------|----------------|-----------|--------|------------|-------|
| run_free | Codex | 0 | 1 | 1,237 | 791 | 47 | 86 |
| run_full | Codex | 62 | 124 | 1,135 | 575 | 108 | 314 |
| run_free | CC | 16 | 57 | 358 | 107 | 40 | 115 |
| run_full | CC | 132 | 480 | 426 | 93 | 20 | 632 |

**Key Findings:**
- Codex run_free code exploration commands (File View + Search + Dir Browse) = **2,075**
- Codex run_full code exploration commands = **1,818**
- **Codex actually increased code exploration commands by 14% in run_free mode!**

- Claude Code run_free code exploration commands = **505**
- Claude Code run_full code exploration commands = **539**
- Claude Code maintains similar code exploration commands across both modes

---

## 3. Command Pattern Distribution (Top Commands)

### Codex

| Command | run_free | run_full |
|------|----------|----------|
| grep | 1,034 | 0 |
| head | 284 | 32 |
| cat | 305 | 4 |
| sed | 250 | 620 |
| find | 122 | 17 |
| rg | 1 | 777 |
| python | 1 | 465 |
| ls | 142 | 215 |

**Key Findings:**
- Codex run_free heavily uses `grep`, `head`, `cat` to read code
- Codex run_full uses more `rg` (ripgrep) and `python` execution

### Claude Code

| Command | run_free | run_full |
|------|----------|----------|
| find | 221 | 208 |
| grep | 148 | 78 |
| python | 210 | 1,401 |
| cat | 70 | 38 |
| ls | 35 | 17 |

**Key Findings:**
- Claude Code run_free has only 210 python commands
- Claude Code run_full has 1,401 python commands
- **Claude Code significantly reduces python execution in run_free mode**

---

## 4. Token Consumption Distribution

### SWE-bench Lite

| Agent | Mode | Mean | Median | Stdev | Min | Max |
|-------|------|------|--------|-------|-----|-----|
| Codex | run_free | 400,765 | 312,916 | 313,667 | 102,553 | 1,867,927 |
| Codex | run_full | 464,133 | 364,126 | 316,817 | 75,272 | 1,739,115 |
| CC | run_free | 66,943 | 37,778 | 79,825 | 4,173 | 497,711 |
| CC | run_full | 155,701 | 115,307 | 140,524 | 6,113 | 730,495 |

**Key Findings:**
- Codex has high token consumption variance (stdev ~314K)
- Claude Code has more stable token consumption (stdev ~80-140K)
- Codex median is much lower than mean, indicating many high-consumption outlier instances

---

## 5. Tool Output Size Analysis

### SWE-bench Lite

| Agent | Mode | Avg Total Output | Avg Call Count | Output per Call | Estimated Tokens |
|-------|------|-------------|-----------|-------------|-------------|
| Codex | run_free | 59,116 chars | 21.6 | 2,734 chars | ~14,779 |
| Codex | run_full | 281,080 chars | 23.2 | 12,126 chars | ~70,270 |
| CC | run_free | 50,536 chars | 18.1 | 2,800 chars | ~12,634 |
| CC | run_full | 72,997 chars | 35.8 | 2,041 chars | ~18,249 |

**Key Findings:**
- Codex run_full output per call (12,126 chars) is far higher than run_free (2,734 chars)
- This is because run_full executes python/pytest which produces large outputs
- But Codex run_free total output is still high (59K chars) because it executes more code reading commands

---

## 6. Root Cause Analysis

### Codex's "Compensatory Behavior"

When Codex is restricted from executing tests, it:
1. **Increases code exploration commands**: run_free has 14-28% more code exploration commands than run_full
2. **Uses more grep/head/cat**: Attempts to "simulate" execution effects by reading more code
3. **Maintains similar interaction rounds**: Reasoning count remains nearly unchanged (15-17 times)

This leads to:
- Although there's no test execution output
- More code exploration commands produce large amounts of file content output
- These outputs accumulate in context, keeping input_tokens high

### Claude Code's "Adaptive Behavior"

When Claude Code is restricted from executing tests, it:
1. **Significantly reduces command execution**: run_free has 61-64% fewer commands than run_full
2. **Reduces python execution**: From 1,401 times down to 210 times
3. **Maintains code exploration commands relatively unchanged**: 505 vs 539

This leads to:
- Reduced command execution, reduced output
- Less context accumulation
- 56-62% reduction in token consumption

---

## 7. Conclusion

| Behavior Pattern | Codex | Claude Code |
|----------|-------|-------------|
| Response to run_free | Increase code exploration | Reduce overall interaction |
| Command execution strategy | Heavy head/sed/grep | Precise reading |
| Token efficiency | Low (~400-530K/instance) | High (~62-67K/instance) |
| Adaptability | Weak (compensatory behavior) | Strong (adaptive behavior) |

**Core Finding: Different agents have completely different response strategies to execution restrictions, which directly affects cost savings effectiveness.**

- **Codex** seems more reliant on "trial-and-error" mode; even when test execution is prohibited, it attempts to "simulate" execution effects through extensive code reading
- **Claude Code** is better at "one-shot reasoning" and can reduce unnecessary interactions in run_free mode

This finding provides important supplementation to RQ2 conclusions: **The cost savings effect of Run-Free mode is highly dependent on the agent's architecture and behavioral patterns.**
