"use client";

import { useState, useEffect, useRef } from "react";

interface Script {
  id: string;
  name: string;
  status: "idle" | "running" | "completed" | "failed";
}

interface Config {
  numInstances: number;
  workers: number;
  timeout: number;
  claudeModel: string;
  codexModel: string;
  anthropicBaseUrl: string;
  modes: string[];
}

interface TraceInfo {
  path: string;
  instance: string;
  mode: string;
  agent: string;
  size: number;
  mtime: number;
}

const ALL_MODES = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"];

export default function Home() {
  const [scripts, setScripts] = useState<Script[]>([
    { id: "claude_lite", name: "Claude + Lite", status: "idle" },
    { id: "claude_verified", name: "Claude + Verified", status: "idle" },
    { id: "codex_lite", name: "Codex + Lite", status: "idle" },
    { id: "codex_verified", name: "Codex + Verified", status: "idle" },
  ]);
  const [selected, setSelected] = useState<string[]>([]);
  const [execMode, setExecMode] = useState<"parallel" | "sequential">("parallel");
  const [config, setConfig] = useState<Config>({
    numInstances: 100,
    workers: 30,
    timeout: 1200,
    claudeModel: "sonnet",
    codexModel: "gpt-5.2",
    anthropicBaseUrl: "http://uk.frp.one:60660",
    modes: [...ALL_MODES],
  });
  const [logs, setLogs] = useState<Record<string, string[]>>({});
  const [traces, setTraces] = useState<Record<string, TraceInfo[]>>({});
  const [showConfig, setShowConfig] = useState(false);
  const [activeLogTab, setActiveLogTab] = useState<string | null>(null);
  const [activeMode, setActiveMode] = useState<string | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<TraceInfo | null>(null);
  const [traceContent, setTraceContent] = useState<string>("");
  const [loadingTrace, setLoadingTrace] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportContent, setReportContent] = useState<any>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const eventSourcesRef = useRef<Map<string, EventSource>>(new Map());

  // 从后端脚本加载默认配置
  const loadConfig = async () => {
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        const data = await res.json();
        setConfig({
          numInstances: data.numInstances,
          workers: data.workersClaudeCode, // 默认使用 Claude 的并发数
          timeout: data.timeout,
          claudeModel: data.claudeModel,
          codexModel: data.codexModel,
          anthropicBaseUrl: data.anthropicBaseUrl,
          modes: data.modes.map((m: string) => {
            const parts = m.split(" ");
            return parts[0] === "run_less" ? `${parts[0]}_k${parts[1]}` : parts[0];
          }).filter((m: string) => ALL_MODES.includes(m)),
        });
      }
    } catch (error) {
      console.error("Failed to load config:", error);
    }
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]));
  };

  const toggleMode = (mode: string) => {
    setConfig((prev) => ({
      ...prev,
      modes: prev.modes.includes(mode) ? prev.modes.filter((m) => m !== mode) : [...prev.modes, mode],
    }));
  };

  // 刷新脚本状态
  const refreshStatus = async () => {
    const res = await fetch("/api/scripts");
    if (res.ok) {
      const data = await res.json();
      setScripts(data);
    }
  };

  // 刷新 trace 文件
  const refreshTraces = async (scriptId: string) => {
    const res = await fetch(`/api/traces?script=${scriptId}`);
    if (res.ok) {
      const data = await res.json();
      setTraces((prev) => ({ ...prev, [scriptId]: data.traces }));
    }
  };

  const startScripts = async () => {
    if (selected.length === 0) return;

    const res = await fetch("/api/scripts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "start", scripts: selected, mode: execMode, config }),
    });

    if (res.ok) {
      await refreshStatus();
      // 为每个选中的脚本启动日志流
      for (const id of selected) {
        startLogStream(id);
      }
      if (selected.length > 0) {
        setActiveLogTab(selected[0]);
      }
    }
  };

  const stopScripts = async () => {
    await fetch("/api/scripts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "stop" }),
    });
    await refreshStatus();
    // 关闭所有日志流
    for (const es of eventSourcesRef.current.values()) {
      es.close();
    }
    eventSourcesRef.current.clear();
  };

  const startLogStream = (scriptId: string) => {
    // 关闭已有的连接
    const existing = eventSourcesRef.current.get(scriptId);
    if (existing) {
      existing.close();
    }

    const es = new EventSource(`/api/logs?script=${scriptId}`);
    es.onmessage = (e) => {
      setLogs((prev) => ({
        ...prev,
        [scriptId]: [...(prev[scriptId] || []).slice(-500), e.data],
      }));
    };
    es.onerror = () => {
      // 连接错误时尝试重连
      setTimeout(() => startLogStream(scriptId), 3000);
    };
    eventSourcesRef.current.set(scriptId, es);
  };

  // 页面加载时加载配置和刷新状态
  useEffect(() => {
    loadConfig();
    refreshStatus();
    const interval = setInterval(refreshStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // 定期刷新 trace
  useEffect(() => {
    if (activeLogTab) {
      refreshTraces(activeLogTab);
      const interval = setInterval(() => refreshTraces(activeLogTab), 10000);
      return () => clearInterval(interval);
    }
  }, [activeLogTab]);

  // 自动滚动日志
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs, activeLogTab]);

  // 清理
  useEffect(() => {
    return () => {
      for (const es of eventSourcesRef.current.values()) {
        es.close();
      }
    };
  }, []);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleString("zh-CN");
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const loadTraceContent = async (trace: TraceInfo) => {
    setSelectedTrace(trace);
    setLoadingTrace(true);
    try {
      const res = await fetch(`/api/trace-content?path=${encodeURIComponent(trace.path)}`);
      if (res.ok) {
        const data = await res.json();
        setTraceContent(data.content);
      }
    } catch (error) {
      console.error("Failed to load trace:", error);
    } finally {
      setLoadingTrace(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">SWE-bench 实验控制面板</h1>

      {/* Script Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {scripts.map((s) => (
          <div
            key={s.id}
            onClick={() => toggleSelect(s.id)}
            className={`p-4 rounded-lg cursor-pointer border-2 transition ${
              selected.includes(s.id) ? "border-blue-500 bg-blue-900/30" : "border-gray-700 bg-gray-800"
            }`}
          >
            <div className="font-medium">{s.name}</div>
            <div className="text-sm mt-1">{selected.includes(s.id) ? "[x]" : "[ ]"} 选中</div>
            <div
              className={`text-sm mt-1 ${
                s.status === "running" ? "text-green-400" : s.status === "failed" ? "text-red-400" : "text-gray-400"
              }`}
            >
              状态: {s.status === "idle" ? "空闲" : s.status === "running" ? "运行中" : s.status === "completed" ? "完成" : "失败"}
            </div>
          </div>
        ))}
      </div>

      {/* Execution Mode */}
      <div className="mb-4 flex items-center gap-4">
        <span>执行方式:</span>
        <label className="flex items-center gap-1">
          <input type="radio" checked={execMode === "parallel"} onChange={() => setExecMode("parallel")} />
          并行执行
        </label>
        <label className="flex items-center gap-1">
          <input type="radio" checked={execMode === "sequential"} onChange={() => setExecMode("sequential")} />
          顺序执行
        </label>
        <button onClick={refreshStatus} className="ml-4 px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm">
          刷新状态
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={startScripts}
          disabled={selected.length === 0}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded"
        >
          启动选中脚本
        </button>
        <button onClick={stopScripts} className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded">
          停止所有
        </button>
      </div>

      {/* Config Panel */}
      <div className="mb-6">
        <button onClick={() => setShowConfig(!showConfig)} className="text-blue-400 hover:underline mb-2">
          {showConfig ? "收起配置" : "展开配置"}
        </button>
        {showConfig && (
          <div className="bg-gray-800 p-4 rounded-lg space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <label className="block">
                <span className="text-sm">实例数</span>
                <input
                  type="number"
                  value={config.numInstances}
                  onChange={(e) => setConfig({ ...config, numInstances: +e.target.value })}
                  className="w-full mt-1 p-2 bg-gray-700 rounded"
                />
              </label>
              <label className="block">
                <span className="text-sm">并发数</span>
                <input
                  type="number"
                  value={config.workers}
                  onChange={(e) => setConfig({ ...config, workers: +e.target.value })}
                  className="w-full mt-1 p-2 bg-gray-700 rounded"
                />
              </label>
              <label className="block">
                <span className="text-sm">超时(s)</span>
                <input
                  type="number"
                  value={config.timeout}
                  onChange={(e) => setConfig({ ...config, timeout: +e.target.value })}
                  className="w-full mt-1 p-2 bg-gray-700 rounded"
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <label className="block">
                <span className="text-sm">Claude Model</span>
                <select
                  value={config.claudeModel}
                  onChange={(e) => setConfig({ ...config, claudeModel: e.target.value })}
                  className="w-full mt-1 p-2 bg-gray-700 rounded"
                >
                  <option value="sonnet">sonnet</option>
                  <option value="opus">opus</option>
                  <option value="haiku">haiku</option>
                </select>
              </label>
              <label className="block">
                <span className="text-sm">Base URL</span>
                <input
                  type="text"
                  value={config.anthropicBaseUrl}
                  onChange={(e) => setConfig({ ...config, anthropicBaseUrl: e.target.value })}
                  className="w-full mt-1 p-2 bg-gray-700 rounded"
                />
              </label>
            </div>
            <div>
              <span className="text-sm">运行模式</span>
              <div className="flex flex-wrap gap-2 mt-1">
                {ALL_MODES.map((mode) => (
                  <label key={mode} className="flex items-center gap-1">
                    <input type="checkbox" checked={config.modes.includes(mode)} onChange={() => toggleMode(mode)} />
                    {mode}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Log Tabs */}
      <div className="bg-gray-800 rounded-lg">
        <div className="flex border-b border-gray-700">
          {scripts.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                setActiveLogTab(s.id);
                if (!eventSourcesRef.current.has(s.id) && s.status === "running") {
                  startLogStream(s.id);
                }
              }}
              className={`px-4 py-2 ${activeLogTab === s.id ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"}`}
            >
              {s.name}
              {s.status === "running" && <span className="ml-1 text-green-400">*</span>}
            </button>
          ))}
        </div>

        {activeLogTab && (
          <div className="p-4">
            {/* Log Viewer */}
            <h3 className="font-medium mb-2">实时日志</h3>
            <div ref={logRef} className="h-48 overflow-y-auto font-mono text-sm bg-black p-2 rounded mb-4">
              {(logs[activeLogTab] || []).length === 0 ? (
                <div className="text-gray-500">等待日志...</div>
              ) : (
                (logs[activeLogTab] || []).map((line, i) => <div key={i}>{line}</div>)
              )}
            </div>

            {/* Trace Files */}
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-medium">Trace 文件</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => refreshTraces(activeLogTab)}
                  className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                >
                  刷新
                </button>
                <button
                  onClick={async () => {
                    const dataset = activeLogTab.includes("verified") ? "swebenchverified" : "swebenchlite";
                    const agent = activeLogTab.includes("claude") ? "claude_code" : "codex";
                    const mode = activeMode || "run_free";

                    if (!confirm(`确定要提交评测 ${agent}/${mode} 吗？\n流程：生成 predictions -> 提交到 SWE-bench`)) return;

                    try {
                      // 1. 生成 predictions
                      const genRes = await fetch("/api/generate-predictions", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ dataset, agent, mode }),
                      });
                      const genData = await genRes.json();
                      if (!genData.success) {
                        alert(`生成 predictions 失败: ${genData.error}`);
                        return;
                      }

                      // 2. 提交评测（后台任务，静默运行）
                      const runId = `${dataset}_${agent}_${mode}`;
                      fetch("/api/submit-evaluation", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ dataset, agent, mode, runId }),
                      });
                    } catch (error: any) {
                      alert(`错误: ${error.message}`);
                    }
                  }}
                  className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                >
                  提交评测
                </button>
                <button
                  onClick={async () => {
                    try {
                      const res = await fetch("/api/reports?action=list");
                      const data = await res.json();
                      if (data.reports && data.reports.length > 0) {
                        const reportList = data.reports.map((r: any, i: number) =>
                          `${i + 1}. ${r.filename} (${(r.size / 1024).toFixed(1)} KB)`
                        ).join("\n");
                        const choice = prompt(`选择报告（输入序号）:\n${reportList}`);
                        if (choice) {
                          const idx = parseInt(choice) - 1;
                          if (idx >= 0 && idx < data.reports.length) {
                            const filename = data.reports[idx].filename;
                            const reportRes = await fetch(`/api/reports?action=read&filename=${filename}`);
                            const reportData = await reportRes.json();
                            if (reportData.report) {
                              setReportContent(reportData.report);
                              setShowReportModal(true);
                            }
                          }
                        }
                      } else {
                        alert("暂无本地报告");
                      }
                    } catch (error: any) {
                      alert(`错误: ${error.message}`);
                    }
                  }}
                  className="px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-sm"
                >
                  查看报告
                </button>
              </div>
            </div>
            {(() => {
              const tracesByMode = (traces[activeLogTab] || []).reduce((acc, t) => {
                if (!acc[t.mode]) acc[t.mode] = [];
                acc[t.mode].push(t);
                return acc;
              }, {} as Record<string, TraceInfo[]>);

              const modes = Object.keys(tracesByMode).sort();

              if (modes.length === 0) {
                return <div className="p-4 text-center text-gray-500 bg-gray-800 rounded">暂无 trace 文件</div>;
              }

              // 自动选择第一个 mode
              if (!activeMode || !modes.includes(activeMode)) {
                setActiveMode(modes[0]);
              }

              const currentMode = activeMode || modes[0];

              return (
                <div className="bg-gray-800 rounded">
                  {/* Mode Tabs */}
                  <div className="flex border-b border-gray-700 overflow-x-auto">
                    {modes.map(mode => (
                      <button
                        key={mode}
                        onClick={() => setActiveMode(mode)}
                        className={`px-4 py-2 text-sm whitespace-nowrap ${
                          currentMode === mode ? "bg-gray-700 text-white border-b-2 border-blue-500" : "text-gray-400 hover:text-white"
                        }`}
                      >
                        {mode} ({tracesByMode[mode].length})
                      </button>
                    ))}
                  </div>
                  {/* Trace Table */}
                  <div className="overflow-x-auto max-h-80 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-gray-800">
                        <tr>
                          <th className="text-left p-2">实例</th>
                          <th className="text-right p-2">大小</th>
                          <th className="text-right p-2">更新时间</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tracesByMode[currentMode].map((t, i) => (
                          <tr
                            key={i}
                            onClick={() => loadTraceContent(t)}
                            className="border-t border-gray-700 hover:bg-gray-700 cursor-pointer"
                          >
                            <td className="p-2 font-mono text-xs">{t.instance}</td>
                            <td className="p-2 text-right">{formatSize(t.size)}</td>
                            <td className="p-2 text-right text-gray-400">{formatTime(t.mtime)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* Trace Modal */}
      {selectedTrace && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedTrace(null)}
        >
          <div
            className="bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-gray-700 flex justify-between items-center">
              <div>
                <h3 className="font-medium text-lg">{selectedTrace.instance}</h3>
                <div className="text-sm text-gray-400 mt-1">
                  {selectedTrace.mode} | {selectedTrace.agent} | {formatSize(selectedTrace.size)} | {formatTime(selectedTrace.mtime)}
                </div>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
              >
                关闭
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {loadingTrace ? (
                <div className="text-center text-gray-400">加载中...</div>
              ) : (
                <pre className="text-xs font-mono whitespace-pre-wrap break-words">{traceContent}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>

      {/* Report Modal */}
      {showReportModal && reportContent && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowReportModal(false)}
        >
          <div
            className="bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-gray-700 flex justify-between items-center">
              <h3 className="font-medium text-lg">评测报告</h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
              >
                关闭
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 p-3 rounded">
                    <div className="text-sm text-gray-400">Resolved</div>
                    <div className="text-2xl font-bold text-green-400">{reportContent.resolved || 0}</div>
                  </div>
                  <div className="bg-gray-900 p-3 rounded">
                    <div className="text-sm text-gray-400">Applied</div>
                    <div className="text-2xl font-bold text-blue-400">{reportContent.applied || 0}</div>
                  </div>
                </div>
                <div className="bg-gray-900 p-3 rounded">
                  <div className="text-sm text-gray-400 mb-2">完整报告</div>
                  <pre className="text-xs font-mono whitespace-pre-wrap break-words">{JSON.stringify(reportContent, null, 2)}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
