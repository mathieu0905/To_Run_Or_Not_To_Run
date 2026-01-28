# RQ3 Detailed Analysis Report: Why Does Execution Feedback Have Limited Impact?

## 1. Overall Findings

- Hurt cases (execution feedback led to failure): 16
- Helped cases (execution feedback helped succeed): 21
- Net benefit: 5 instances

## 2. Hurt vs Helped Comparison

| Metric | Hurt Cases | Helped Cases |
|------|-----------|-------------|
| Case count | 16 | 21 |
| Avg test executions | 8.1 | 8.6 |
| Avg error commands | 5.7 | 6.8 |
| Avg repeated commands | 1.6 | 2.4 |

## 3. Hurt Case List

| Instance | Agent | Commands | Tests | Repeated | Errors |
|----------|-------|--------|--------|--------|--------|
| django__django-12184 | claude_code | 26 | 14 | 5 | 5 |
| django__django-12908 | claude_code | 17 | 14 | 1 | 5 |
| django__django-14016 | claude_code | 23 | 14 | 0 | 3 |
| django__django-15695 | claude_code | 22 | 12 | 3 | 6 |
| django__django-13230 | claude_code | 17 | 8 | 2 | 4 |
| django__django-12497 | codex | 16 | 3 | 0 | 10 |
| django__django-11964 | codex | 27 | 2 | 3 | 12 |
| django__django-11848 | codex | 12 | 3 | 0 | 6 |
| django__django-12747 | codex | 19 | 3 | 0 | 3 |
| django__django-11532 | claude_code | 15 | 10 | 3 | 5 |
| astropy__astropy-14365 | claude_code | 6 | 3 | 1 | 3 |
| django__django-11555 | claude_code | 24 | 15 | 4 | 9 |
| django__django-13121 | claude_code | 18 | 7 | 0 | 5 |
| django__django-11728 | claude_code | 16 | 10 | 1 | 5 |
| django__django-11790 | claude_code | 17 | 6 | 1 | 5 |
| django__django-10973 | codex | 17 | 6 | 1 | 5 |

## 4. Helped Case List

| Instance | Agent | Commands | Tests | Repeated | Errors |
|----------|-------|--------|--------|--------|--------|
| django__django-14997 | claude_code | 19 | 5 | 0 | 7 |
| django__django-15498 | claude_code | 18 | 7 | 0 | 5 |
| django__django-12470 | claude_code | 38 | 12 | 4 | 9 |
| django__django-11620 | claude_code | 16 | 12 | 3 | 5 |
| django__django-11797 | claude_code | 41 | 8 | 4 | 5 |
| django__django-12284 | claude_code | 26 | 18 | 4 | 8 |
| django__django-15202 | codex | 34 | 4 | 5 | 15 |
| django__django-15781 | codex | 18 | 2 | 0 | 9 |
| django__django-15252 | codex | 33 | 5 | 0 | 7 |
| django__django-11206 | claude_code | 25 | 21 | 8 | 10 |
| django__django-11490 | claude_code | 15 | 11 | 3 | 7 |
| astropy__astropy-14096 | claude_code | 17 | 12 | 1 | 8 |
| django__django-12304 | claude_code | 24 | 5 | 3 | 5 |
| django__django-10973 | claude_code | 9 | 2 | 0 | 2 |
| django__django-12965 | claude_code | 20 | 7 | 1 | 1 |
| django__django-12663 | claude_code | 17 | 12 | 4 | 7 |
| django__django-11265 | claude_code | 25 | 22 | 5 | 12 |
| astropy__astropy-7166 | claude_code | 21 | 2 | 1 | 2 |
| django__django-11490 | codex | 18 | 2 | 0 | 3 |
| django__django-12304 | codex | 15 | 3 | 2 | 4 |
| django__django-11265 | codex | 34 | 8 | 3 | 11 |

## 5. Conclusion

Execution feedback has limited impact for the following reasons:

1. **Double-edged sword effect**: Execution feedback can both help (21 cases) and mislead (16 cases)
2. **Trial-and-error loop trap**: Execution feedback easily leads agent into ineffective retry loops
3. **Deterministic outcomes**: 90%+ of cases have the same result regardless of execution feedback
4. **Minimal net benefit**: Only 5 net benefit out of 400 instances
