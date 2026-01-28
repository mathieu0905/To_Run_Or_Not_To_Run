# RQ1: Test Execution Analysis Report

This report analyzes **test executions** (pytest, unittest, tox, nosetests, python xxx.py) across 7,619 public SWE-bench agent traces.

## Definitions

- **Test Execution**: Commands matching pytest, unittest, tox, nosetests, or `python xxx.py` patterns
- **Success**: Test execution passes (pytest: "passed" without "FAILED"; unittest: "OK"; return code 0)
- **Failure**: Test execution fails (pytest: "FAILED"/"ERROR"; unittest: "FAILED"; Python exceptions; non-zero exit)
- **Position**: Normalized position in agent conversation (0.0 = start, 1.0 = end)
  - Early: 0-33%
  - Middle: 33-66%
  - Late: 66-100%

---

## Summary Table

| Agent | Model | Benchmark | Traces | Total Execs | Avg/Task | Early | Middle | Late | Success | Failure |
|-------|-------|-----------|--------|-------------|----------|-------|--------|------|---------|---------|
| SWE-agent | GPT-4 | Lite | 254 | 805 | 3.2 | 42.4% | 28.1% | 29.6% | 46.1% | 53.9% |
| SWE-agent | Claude-3.5-Sonnet | Lite | 259 | 1,623 | 6.3 | 23.5% | 33.0% | 43.4% | 38.7% | 61.3% |
| SWE-agent | GPT-4o | Lite | 259 | 1,920 | 7.4 | 32.3% | 33.4% | 34.2% | 36.7% | 63.3% |
| OpenHands | Claude-3.5-Sonnet | Lite | 291 | 1,755 | 6.0 | 19.8% | 33.7% | 46.4% | 57.8% | 42.2% |
| SWE-agent | GPT-4 | Verified | 400 | 1,324 | 3.3 | 42.7% | 27.9% | 29.4% | 45.8% | 54.2% |
| SWE-agent | Claude-3-Opus | Verified | 366 | 1,351 | 3.7 | 35.8% | 31.2% | 32.9% | 45.3% | 54.7% |
| SWE-agent | Claude-3.5-Sonnet | Verified | 434 | 2,992 | 6.9 | 24.8% | 34.5% | 40.8% | 40.3% | 59.7% |
| SWE-agent | GPT-4o | Verified | 425 | 3,176 | 7.5 | 31.2% | 33.2% | 35.6% | 30.4% | 69.6% |
| OpenHands | Claude-3.5-Sonnet | Verified | 488 | 3,293 | 6.7 | 22.7% | 33.4% | 43.9% | 58.6% | 41.4% |
| OpenHands | Claude-4-Sonnet | Verified | 500 | 9,333 | 18.7 | 15.4% | 30.9% | 53.7% | 70.4% | 29.6% |
| OpenHands | Kimi-K2 | Verified | 500 | 7,729 | 15.5 | 11.7% | 34.9% | 53.3% | 66.4% | 33.6% |
| OpenHands | Qwen3-480B | Verified | 500 | 9,326 | 18.7 | 12.4% | 31.7% | 55.9% | 70.3% | 29.7% |
| OpenHands | GPT-5 | Verified | 479 | 1,957 | 4.1 | 11.5% | 38.6% | 49.9% | 68.1% | 31.9% |
| LiveSWEAgent | Gemini-3-Pro | Verified | 500 | 6,310 | 12.6 | 28.7% | 38.2% | 33.2% | 77.8% | 22.2% |
| LiveSWEAgent | Claude-Opus-4.5 | Verified | 500 | 7,960 | 15.9 | 23.6% | 40.1% | 36.3% | 79.3% | 20.7% |
| Mini-SWE-agent | Claude-Opus-4.5 | Verified | 495 | 5,193 | 10.5 | 12.6% | 38.3% | 49.1% | 78.7% | 21.3% |
| Mini-SWE-agent | Gemini-3-Pro | Verified | 495 | 4,273 | 8.6 | 23.1% | 36.6% | 40.3% | 71.8% | 28.2% |
| Mini-SWE-agent | DeepSeek-V3.2 | Verified | 485 | 5,114 | 10.5 | 14.2% | 34.9% | 50.9% | 59.9% | 40.1% |
| Mini-SWE-agent | GPT-5.2 | Verified | 115 | 228 | 2.0 | 1.8% | 21.9% | 76.3% | 58.0% | 42.0% |

---

## 1. Execution Count Analysis

### Average Test Executions per Task

| Agent | Range | Notes |
|-------|-------|-------|
| SWE-agent | 3.2 - 7.5 | Lower execution frequency |
| OpenHands | 4.1 - 18.7 | Higher with newer models (Claude-4-Sonnet: 18.7) |
| LiveSWEAgent | 12.6 - 15.9 | Moderate-high execution frequency |
| Mini-SWE-agent | 2.0 - 10.5 | GPT-5.2 has lowest (2.0), others moderate |

**Key Finding**: Newer models (Claude-4-Sonnet, Qwen3-480B) execute significantly more tests per task (~18-19) compared to older models (GPT-4: ~3.2).

---

## 2. Execution Position Analysis

### Distribution by Agent Type

| Agent | Early (0-33%) | Middle (33-66%) | Late (66-100%) |
|-------|---------------|-----------------|----------------|
| **SWE-agent** | 24-43% | 28-35% | 29-43% |
| **OpenHands** | 11-23% | 31-39% | 44-56% |
| **LiveSWEAgent** | 24-29% | 38-40% | 33-36% |
| **Mini-SWE-agent** | 2-23% | 22-38% | 40-76% |

**Key Finding**:
- SWE-agent distributes executions more evenly, with higher early execution (up to 43%)
- OpenHands and Mini-SWE-agent concentrate executions in late stages (50-76%)
- LiveSWEAgent has relatively even distribution

---

## 3. Execution Results Analysis

### Success Rate by Agent-Model

| Category | Success Rate Range | Examples |
|----------|-------------------|----------|
| **High Success (>70%)** | 70-79% | LiveSWEAgent+Claude-Opus-4.5 (79.3%), Mini-SWE-agent+Claude-Opus-4.5 (78.7%) |
| **Medium Success (50-70%)** | 58-70% | OpenHands+Claude-4-Sonnet (70.4%), OpenHands+GPT-5 (68.1%) |
| **Low Success (<50%)** | 30-58% | SWE-agent+GPT-4o (30.4%), SWE-agent+Claude-3.5-Sonnet (38.7-40.3%) |

### Top Error Types (Aggregated)

| Error Type | Description |
|------------|-------------|
| **TestFailure** | Test assertions failed (pytest FAILED, unittest FAILED) |
| **OtherError** | Generic errors with Traceback |
| **TestError** | Test collection/setup errors |
| **ModuleNotFoundError** | Missing Python modules |
| **AttributeError** | Accessing non-existent attributes |
| **TypeError** | Type mismatches |
| **FileNotFoundError** | Missing files |

---

## 4. Position vs Execution Results

### Success Rate by Position (All Agent-Model Combinations)

| Agent-Model | Early Success | Middle Success | Late Success | Trend |
|-------------|---------------|----------------|--------------|-------|
| SWE-agent + GPT-4 (Lite) | 44.6% | 37.6% | 56.3% | ↗ Late better |
| SWE-agent + GPT-4o (Lite) | 35.3% | 27.7% | 46.9% | ↗ Late better |
| OpenHands + Claude-3.5-Sonnet (Lite) | 44.3% | 49.7% | 69.4% | ↗ Late better |
| SWE-agent + GPT-4 (Verified) | 41.5% | 36.9% | 60.4% | ↗ Late better |
| SWE-agent + GPT-4o (Verified) | 27.3% | 24.2% | 38.8% | ↗ Late better |
| OpenHands + Claude-3.5-Sonnet (Verified) | 41.9% | 51.8% | 72.4% | ↗ Late better |
| OpenHands + Claude-4-Sonnet (Verified) | 70.7% | 60.5% | 76.0% | ↗ Late better |
| OpenHands + GPT-5 (Verified) | 54.7% | 67.0% | 72.0% | ↗ Late better |
| LiveSWEAgent + Gemini-3-Pro (Verified) | 71.1% | 78.8% | 82.4% | ↗ Late better |
| LiveSWEAgent + Claude-Opus-4.5 (Verified) | 73.8% | 80.8% | 81.1% | ↗ Late better |
| Mini-SWE-agent + Claude-Opus-4.5 (Verified) | 70.2% | 78.8% | 80.9% | ↗ Late better |
| Mini-SWE-agent + GPT-5.2 (Verified) | 25.0% | 30.0% | 67.1% | ↗↗ Strong late improvement |

**Key Finding**:
- **Late executions consistently have higher success rates** across all agent-model combinations
- Improvement from Early to Late: typically 10-25pp, up to 40pp for some configurations
- This suggests agents improve their understanding over time and execute more targeted tests later

---

## 5. Key Observations

### Observation 1: Execution frequency varies widely (2-19 per task)
- GPT-5.2 with Mini-SWE-agent: only 2.0 executions/task
- Claude-4-Sonnet with OpenHands: 18.7 executions/task
- This 9x difference suggests different agent strategies

### Observation 2: Execution timing differs by agent architecture
- SWE-agent: More uniform distribution (early ~35%, middle ~32%, late ~33%)
- OpenHands/Mini-SWE-agent: Late-heavy distribution (late ~50-55%)

### Observation 3: Failure rates vary significantly (20-70%)
- Newest agents (LiveSWEAgent, Mini-SWE-agent with Claude-Opus-4.5): 20-21% failure rate
- Older agents (SWE-agent with GPT-4o): 64-70% failure rate
- This suggests significant improvements in test execution quality

### Observation 4: Late executions are more successful
- Consistent pattern across all configurations
- Late success rate is typically 10-25pp higher than early/middle
- Exception: LiveSWEAgent maintains high success throughout (71-82%)

---

## 6. Detailed Results by Agent-Model

### SWE-agent + GPT-4 (Lite)
- Traces: 254, Total Execs: 805, Avg: 3.2/task
- Position: Early 42.4%, Middle 28.1%, Late 29.6%
- Results: Success 46.1%, Failure 53.9%
- Top Errors: OtherError (116), AttributeError (64), TypeError (56), TestFailure (45)
- Position vs Results: Early 44.6%, Middle 37.6%, Late 56.3%

### SWE-agent + Claude-3.5-Sonnet (Lite)
- Traces: 259, Total Execs: 1,623, Avg: 6.3/task
- Position: Early 23.5%, Middle 33.0%, Late 43.4%
- Results: Success 38.7%, Failure 61.3%
- Top Errors: TestFailure (378), OtherError (128), ImportError (81), TypeError (66)
- Position vs Results: Early 39.8%, Middle 27.4%, Late 46.7%

### OpenHands + Claude-4-Sonnet (Verified)
- Traces: 500, Total Execs: 9,333, Avg: 18.7/task
- Position: Early 15.4%, Middle 30.9%, Late 53.7%
- Results: Success 70.4%, Failure 29.6%
- Top Errors: TestFailure (1,451), TestError (451), AttributeError (151)
- Position vs Results: Early 70.7%, Middle 60.5%, Late 76.0%

### LiveSWEAgent + Claude-Opus-4.5 (Verified)
- Traces: 500, Total Execs: 7,960, Avg: 15.9/task
- Position: Early 23.6%, Middle 40.1%, Late 36.3%
- Results: Success 79.3%, Failure 20.7%
- Top Errors: TestFailure (598), TestError (245), ValueError (209)
- Position vs Results: Early 73.8%, Middle 80.8%, Late 81.1%

### Mini-SWE-agent + GPT-5.2 (Verified)
- Traces: 115, Total Execs: 228, Avg: 2.0/task
- Position: Early 1.8%, Middle 21.9%, Late 76.3%
- Results: Success 58.0%, Failure 42.0%
- Top Errors: TestFailure (33), NonZeroExit (33), TestError (17)
- Position vs Results: Early 25.0%, Middle 30.0%, Late 67.1%

---

*Report generated: 2025-01-28*
*Data source: 7,619 public SWE-bench agent traces*
*Test execution definition: pytest, unittest, tox, nosetests, python xxx.py*
