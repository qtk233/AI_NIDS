import type { DetectionResult } from "../lib/types";

interface FlowTableProps {
  results: DetectionResult[];
}

export function FlowTable({ results }: FlowTableProps) {
  return (
    <div className="max-h-[500px] overflow-y-auto bg-slate-900 rounded-lg border border-slate-800">
      <table className="w-full text-sm text-left text-slate-300">
        <thead className="sticky top-0 bg-slate-800 text-slate-400 text-xs uppercase">
          <tr>
            <th className="px-4 py-2">源 IP</th>
            <th className="px-4 py-2">目标 IP</th>
            <th className="px-4 py-2">协议</th>
            <th className="px-4 py-2">判定</th>
            <th className="px-4 py-2">置信度</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={i} className={r.prediction !== "Normal" ? "bg-red-950/30" : ""}>
              <td className="px-4 py-2">{r.src_ip}</td>
              <td className="px-4 py-2">{r.dst_ip}</td>
              <td className="px-4 py-2">{r.protocol}</td>
              <td className={`px-4 py-2 ${r.prediction === "Normal" ? "text-green-400" : "text-red-400"}`}>
                {r.prediction === "Normal" ? "✅" : "⚠️"} {r.prediction}
              </td>
              <td className="px-4 py-2">{(r.confidence * 100).toFixed(1)}%</td>
            </tr>
          ))}
          {results.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                暂无检测数据
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
