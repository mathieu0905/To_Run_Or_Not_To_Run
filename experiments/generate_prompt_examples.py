#!/usr/bin/env python3
"""
生成 prompt 示例文档
"""
import json
from pathlib import Path
from prompt_builder import PromptBuilder

# 加载一个示例实例
data_path = Path(__file__).parent.parent / "data" / "swe_bench_lite.json"
with open(data_path, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

instance = dataset[0]

# 生成三种模式的 prompt
run_free = PromptBuilder.build_run_free_prompt(instance)
run_less = PromptBuilder.build_run_less_prompt(instance, k=2)
run_full = PromptBuilder.build_run_full_prompt(instance)

# 生成 markdown 文档
md_content = f"""# Prompt 示例文档

本文档展示了三种执行模式的 prompt 示例，使用 SWE-bench Lite 数据集的第一个实例。

## 实例信息

- **仓库**: {instance['repo']}
- **实例 ID**: {instance['instance_id']}
- **Base Commit**: {instance.get('base_commit', 'N/A')[:12]}...

---

## 1. Run-Free 模式（完全不执行代码）

**核心理念**: Agent 必须通过纯推理来修复 bug，不能运行任何代码来验证。

```
{run_free}
```

**关键特点**:
- ❌ 不能执行任何代码
- 🧠 必须通过阅读代码和逻辑推理
- 🎯 只有一次机会，必须第一次就做对
- 📝 输出 git diff 格式的补丁

---

## 2. Run-Less 模式（有限次执行，K=2）

**核心理念**: Agent 有有限的执行预算（K次），必须把每次执行当作"高价值实验"，强调日志插桩策略。

```
{run_less}
```

**关键特点**:
- 🔢 最多执行 K 次（本例 K=2）
- 🔬 每次执行前必须提出假设
- 📊 强调日志插桩（print/log）来获取高密度调试信息
- 💡 执行是稀缺资源，不是免费的试错按钮
- 📝 最终输出 git diff 格式的补丁

**日志插桩策略**:
- 在关键位置添加 print/log 语句
- 捕获变量值、函数输入输出、分支路径、异常上下文
- 一次聪明的执行胜过十次盲目的尝试

---

## 3. Run-Full 模式（不限制执行次数）

**核心理念**: Agent 可以自由执行代码来调试和验证修复，类似传统的开发流程。

```
{run_full}
```

**关键特点**:
- ✅ 可以自由执行代码
- 🔄 可以多次运行测试验证
- 🐛 可以迭代调试直到所有测试通过
- 📝 最终输出 git diff 格式的补丁

**工作流程**:
1. 阅读相关代码
2. 运行测试查看失败情况
3. 分析错误信息
4. 尝试修复
5. 运行测试验证
6. 如果测试失败，重复步骤 3-5

---

## 对比总结

| 特性 | Run-Free | Run-Less (K=2) | Run-Full |
|------|----------|----------------|----------|
| 执行次数 | 0 次 | 最多 K 次 | 不限制 |
| 策略重点 | 纯推理 | 日志插桩 | 迭代调试 |
| 难度 | 最高 | 中等 | 最低 |
| Token 成本 | 最低 | 中等 | 最高 |
| 适用场景 | 简单 bug | 中等复杂度 | 复杂 bug |

---

## 研究假设

我们的研究旨在探索：

1. **Run-Free vs Run-Full**: 执行环境对代码修复能力的影响有多大？
2. **Run-Less 的最优 K 值**: 有限次执行能否接近 Run-Full 的效果？
3. **成本效益分析**: Run-Less 是否能在成本和效果之间取得最佳平衡？
4. **日志插桩策略**: 强调日志插桩是否能提高 Run-Less 的成功率？

---

生成时间: {Path(__file__).stat().st_mtime}
"""

# 保存到文件
output_path = Path(__file__).parent / "PROMPT_EXAMPLES.md"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

print(f"✅ Prompt 示例文档已生成: {output_path}")
print(f"📄 文件大小: {output_path.stat().st_size / 1024:.1f} KB")
