import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { AlertItem } from "../lib/types";

const BASE_URL = "http://127.0.0.1:8000";

export default function History() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const fetchAlerts = useCallback(() => {
    api.getAlerts(page, 50, search || undefined).then((r) => {
      setAlerts(r.data);
      setTotal(r.meta?.total ?? 0);
    });
  }, [page, search]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleExportCsv = () => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    window.open(`${BASE_URL}/api/alerts/export/csv?${params}`, "_blank");
  };

  const handleExportPdf = () => {
    window.print();
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">📜 历史记录</h1>

      <div className="flex gap-3 mb-4 no-print">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="🔍 搜索 IP..."
          className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm outline-none focus:border-slate-500"
        />
        <button
          onClick={handleExportCsv}
          className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 text-sm"
        >
          📥 CSV
        </button>
        <button
          onClick={handleExportPdf}
          className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 text-sm"
        >
          📄 PDF
        </button>
      </div>

      <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
        <table className="w-full text-sm text-left text-slate-300">
          <thead className="bg-slate-800 text-slate-400 text-xs uppercase">
            <tr>
              <th className="px-4 py-3">时间</th>
              <th className="px-4 py-3">源 IP</th>
              <th className="px-4 py-3">目标 IP</th>
              <th className="px-4 py-3">协议</th>
              <th className="px-4 py-3">判定</th>
              <th className="px-4 py-3">置信度</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr
                key={a.id}
                className="cursor-pointer hover:bg-slate-800/50"
                onClick={() => navigate(`/traffic/${a.id}`)}
              >
                <td className="px-4 py-2">{new Date(a.created_at).toLocaleTimeString()}</td>
                <td className="px-4 py-2">{a.src_ip}</td>
                <td className="px-4 py-2">{a.dst_ip}</td>
                <td className="px-4 py-2">{a.protocol}</td>
                <td className={`px-4 py-2 ${a.prediction === "Normal" ? "text-green-400" : "text-red-400"}`}>
                  {a.prediction}
                </td>
                <td className="px-4 py-2">{(a.confidence * 100).toFixed(1)}%</td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">暂无记录</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center mt-4 text-slate-400 text-sm">
        <span>共 {total} 条</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 bg-slate-800 rounded disabled:opacity-50"
          >
            ←
          </button>
          <span className="px-2">{page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * 50 >= total}
            className="px-3 py-1 bg-slate-800 rounded disabled:opacity-50"
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}
