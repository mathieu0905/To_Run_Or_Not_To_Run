# RQ3 Supplementary Analysis: Complete Verification/Reproduction Statistics

*Generated: 2026-01-28 21:13:09*

## 1. Reproduction Execution Statistics

**Definition**: Test executions that occur BEFORE the first file edit, used for understanding/locating the bug.

- **Actionable**: Execution results contain useful information (file paths, stacktrace, line numbers) that can be used for localization
- **Non-actionable**: Environment errors or no useful information

### P→P Cases (Unrestricted Mode)

| Agent | Has Repro. | Total Execs | Actionable | Non-actionable |
|-------|-----------|-------------|------------|----------------|
| Claude Code | 64 (55.2%) | 164 | 80 (48.8%) | 84 |
| Codex | 9 (6.3%) | 17 | 11 (64.7%) | 6 |

## 2. Verification Execution Statistics

**Definition**: Test executions that occur AFTER the first file edit, used for validating the patch.

### P→P Cases (Unrestricted Mode)

| Agent | Has Verif. | Total Execs | Success | Test Fail | Env Error |
|-------|-----------|-------------|---------|-----------|-----------|
| Claude Code | 100 (86.2%) | 851 | 414 (48.6%) | 154 (18.1%) | 127 (14.9%) |
| Codex | 138 (97.2%) | 445 | 230 (51.7%) | 60 (13.5%) | 152 (34.2%) |

### F→F Cases (Unrestricted Mode)

| Agent | Has Verif. | Total Execs | Success | Test Fail | Env Error |
|-------|-----------|-------------|---------|-----------|-----------|
| Claude Code | 80 (95.2%) | 668 | 272 (40.7%) | 102 (15.3%) | 121 (18.1%) |
| Codex | 52 (94.5%) | 153 | 85 (55.6%) | 17 (11.1%) | 49 (32.0%) |

## 3. Average Executions Per Instance

| Agent | Outcome | Avg. Repro/Instance | Avg. Verif/Instance |
|-------|---------|---------------------|---------------------|
| Claude Code | P→P | 1.41 | 7.34 |
| Claude Code | F→F | 2.02 | 7.95 |
| Codex | P→P | 0.12 | 3.13 |
| Codex | F→F | 0.18 | 2.78 |

## 4. Key Findings

### Claude Code

- **Reproduction**: Out of 164 executions, 80 (48.8%) provided information useful for localization
- **Verification**: Out of 851 executions, 414 (48.6%) succeeded, 127 (14.9%) were environment errors

### Codex

- **Reproduction**: Out of 17 executions, 11 (64.7%) provided information useful for localization
- **Verification**: Out of 445 executions, 230 (51.7%) succeeded, 152 (34.2%) were environment errors
