# Prompt 示例文档

本文档展示了三种执行模式的 prompt 示例，使用 SWE-bench Lite 数据集的第一个实例。

## 实例信息

- **仓库**: astropy/astropy
- **实例 ID**: astropy__astropy-12907
- **Base Commit**: d16bfe05a744...

---

## 1. Run-Free 模式（完全不执行代码）

**核心理念**: Agent 必须通过纯推理来修复 bug，不能运行任何代码来验证。

```
你是一个代码修复专家。你的任务是修复以下 bug。

**重要限制：你不能执行任何代码。**

你必须通过阅读代码、理解逻辑、推理问题根源来生成修复补丁。你可以多次阅读代码、反复思考和修改方案，但不能通过运行代码来验证你的修复。

## 仓库信息
- 仓库: astropy/astropy
- Base Commit: d16bfe05a744909de4b27f5875fe0d4ed41ce607

## 问题描述
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


## 任务要求
1. 仔细阅读相关代码文件（可以多次阅读）
2. 分析问题的根本原因
3. 推理出正确的修复方案
4. 反复检查你的修复逻辑
5. 生成 git diff 格式的补丁

## 输出格式
请以 git diff 格式输出你的修复补丁。

记住：你可以反复阅读代码和思考，但不能运行代码来验证。请通过仔细的逻辑推理来确保修复的正确性。

```

**关键特点**:
- ❌ 不能执行任何代码
- 🧠 必须通过阅读代码和逻辑推理
- 🔄 可以多次阅读代码、反复思考和修改方案
- 📝 输出 git diff 格式的补丁

---

## 2. Run-Less 模式（有限次执行，K=2）

**核心理念**: Agent 有有限的执行预算（K次），必须把每次执行当作"高价值实验"，强调日志插桩策略。

```
你是一个代码修复专家。你的任务是修复以下 bug。

**重要限制：你最多只能执行 2 次代码（包括运行测试、执行脚本等）。**

执行次数是稀缺资源，你必须把每次执行都当作"高价值实验"。

## 仓库信息
- 仓库: astropy/astropy
- Base Commit: d16bfe05a744909de4b27f5875fe0d4ed41ce607

## 问题描述
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


## 执行策略（关键！）
在执行代码之前，你必须：

1. **提出假设**: 明确说明你怀疑问题出在哪里
2. **插入日志**: 在关键位置添加 print/log 语句来捕获：
   - 变量的值
   - 函数的输入输出
   - 分支路径
   - 异常上下文
3. **执行验证**: 运行代码获取高密度的调试信息
4. **分析结果**: 基于日志输出确定修复方案

## 日志插桩示例
```python
# 假设：怀疑 calculate() 函数在处理负数时有问题
def calculate(x):
    print(f"DEBUG: calculate() 输入 x={x}, type={type(x)}")  # 插桩
    result = x * 2
    print(f"DEBUG: calculate() 输出 result={result}")  # 插桩
    return result
```

## 执行预算
- 当前剩余执行次数: 2
- 每次执行前请说明：你的假设是什么，你要验证什么
- 执行后请分析：日志告诉了你什么信息

## 输出格式
最终以 git diff 格式输出你的修复补丁。

记住：把执行当作昂贵的实验，而不是免费的试错按钮。一次聪明的执行胜过十次盲目的尝试。

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
你是一个代码修复专家。你的任务是修复以下 bug。

你可以自由执行代码来调试和验证你的修复。

## 仓库信息
- 仓库: astropy/astropy
- Base Commit: d16bfe05a744909de4b27f5875fe0d4ed41ce607

## 问题描述
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


## 工作流程
1. 阅读相关代码
2. 运行测试查看失败情况
3. 分析错误信息
4. 尝试修复
5. 运行测试验证
6. 如果测试失败，重复步骤 3-5

## 输出格式
最终以 git diff 格式输出你的修复补丁。

你可以多次运行代码和测试，直到所有测试通过。

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

生成时间: 1768335490.4406393
