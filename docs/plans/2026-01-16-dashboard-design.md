# SWE-bench 实验控制面板设计

## 概述

创建一个 Next.js 前端，用于启动、配置和监控 SWE-bench 实验脚本。

## 功能需求

1. **脚本启动**：点击按钮启动对应脚本
2. **参数配置**：在前端修改脚本参数
3. **实时监控**：WebSocket/SSE 实时查看日志
4. **执行顺序**：支持顺序执行和并行执行

## 架构

```
dashboard/
├── app/
│   ├── page.tsx              # 主页面
│   ├── api/
│   │   ├── scripts/route.ts  # 启动/停止脚本
│   │   └── logs/route.ts     # SSE 日志流
│   └── layout.tsx
├── components/
│   ├── ScriptCard.tsx        # 脚本卡片
│   ├── ConfigForm.tsx        # 配置表单
│   └── LogViewer.tsx         # 日志查看器
└── lib/
    └── scripts.ts            # 脚本管理
```

## 技术选型

- Next.js 15 (App Router)
- Server-Sent Events (SSE) 实时日志
- Tailwind CSS
- 无数据库，状态存内存

## API 设计

### POST /api/scripts/start
```json
{
  "scripts": ["claude_lite", "claude_verified"],
  "mode": "sequential" | "parallel",
  "config": {
    "numInstances": 100,
    "workers": 30,
    "timeout": 1200,
    "claudeModel": "sonnet",
    "codexModel": "gpt-5.2",
    "anthropicBaseUrl": "http://...",
    "modes": ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]
  }
}
```

### POST /api/scripts/stop
```json
{ "scriptId": "optional" }
```

### GET /api/logs?script=claude_lite
返回 SSE 流

## 界面设计

- 4 个脚本卡片（可多选）
- 执行方式选择（并行/顺序）
- 配置面板（可折叠）
- 实时日志区域
