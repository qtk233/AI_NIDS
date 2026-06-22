import { useWebSocket } from "../hooks/useWebSocket";
import { FlowTable } from "../components/FlowTable";

export default function LiveDetection() {
  const { results, connected, clear } = useWebSocket();
  const alertCount = results.filter((r) => r.prediction !== "Normal").length;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">🔴 实时检测</h1>
        <div className="flex items-center gap-4">
          <span className={`inline-block w-2 h-2 rounded-full ${connected ? "bg-green-400" : "bg-red-400"}`} />
          <span className="text-slate-400 text-sm">{connected ? "监控中" : "重连中..."}</span>
          <span className="text-slate-400 text-sm">
            检测: {results.length} 条 | 告警: {alertCount}
          </span>
          <button
            onClick={clear}
            className="px-3 py-1 text-sm bg-slate-800 text-slate-300 rounded hover:bg-slate-700"
          >
            清空
          </button>
        </div>
      </div>
      <FlowTable results={results} />
    </div>
  );
}
