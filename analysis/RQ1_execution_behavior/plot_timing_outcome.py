#!/usr/bin/env python3
"""
生成 Timing vs Outcome 关系图
数据来源：rq1_execution_analysis_report.md
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 数据来自 rq1_execution_analysis_report.md 第104-117行
data = [
    # (Agent, Model, Early, Middle, Late)
    ("SWE-agent", "GPT-4", 42.0, 37.0, 58.0),
    ("SWE-agent", "Claude-3.5-Sonnet", 37.0, 29.0, 48.0),
    ("SWE-agent", "GPT-4o", 27.0, 24.0, 39.0),
    ("OpenHands", "Claude-3.5-Sonnet", 42.0, 52.0, 72.0),
    ("OpenHands", "Claude-4-Sonnet", 71.0, 61.0, 76.0),
    ("OpenHands", "GPT-5", 55.0, 67.0, 72.0),
    ("LiveSWEAgent", "Claude-Opus-4.5", 74.0, 81.0, 81.0),
    ("Mini-SWE-agent", "Claude-Opus-4.5", 70.0, 79.0, 81.0),
    ("Mini-SWE-agent", "GPT-5.2", 25.0, 30.0, 67.0),
]

# 设置图形
plt.figure(figsize=(8, 5))
plt.rcParams['font.size'] = 10

stages = ['Early\n(0-33%)', 'Middle\n(33-66%)', 'Late\n(66-100%)']
x = np.arange(len(stages))

# 颜色方案
colors = plt.cm.tab10(np.linspace(0, 1, len(data)))

# 绘制每条线
for i, (agent, model, early, middle, late) in enumerate(data):
    label = f"{agent} + {model}"
    if len(label) > 30:
        label = f"{agent[:10]}... + {model[:15]}..."
    plt.plot(x, [early, middle, late], 'o-', label=f"{agent}, {model}",
             color=colors[i], linewidth=1.5, markersize=6)

plt.xlabel('Execution Timing Stage', fontsize=11)
plt.ylabel('Success Rate (%)', fontsize=11)
plt.title('Test Execution Success Rate by Timing Stage', fontsize=12)
plt.xticks(x, stages)
plt.ylim(0, 100)
plt.grid(True, alpha=0.3)
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
plt.tight_layout()

# Save figures.
project_root = Path(__file__).resolve().parents[2]
output_path = project_root / 'figures' / 'timing_outcome.pdf'
plt.savefig(output_path, bbox_inches='tight', dpi=300)
print(f"Figure saved to: {output_path}")

# Also save a PNG preview.
png_path = Path(__file__).resolve().parent / 'timing_outcome.png'
plt.savefig(png_path, bbox_inches='tight', dpi=150)
print(f"PNG preview saved to: {png_path}")

plt.close()
