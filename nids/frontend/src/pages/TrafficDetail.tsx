import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { AlertItem } from "../lib/types";

export default function TrafficDetail() {
  const { id } = useParams<{ id: string }>();
  const [alert, setAlert] = useState<AlertItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      setLoading(true);
      api.getAlert(id).then((r) => {
        setAlert(r.data);
      }).finally(() => setLoading(false));
    }
  }, [id]);

  if (loading || !alert) {
    return <div className="p-8 text-slate-400">Loading...</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">🔍 流量详情</h1>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">📋 流量元信息</h3>
          <dl className="grid grid-cols-2 gap-2 text-sm text-slate-300">
            <dt className="text-slate-500">源 IP</dt><dd>{alert.src_ip}</dd>
            <dt className="text-slate-500">目标 IP</dt><dd>{alert.dst_ip}</dd>
            <dt className="text-slate-500">协议</dt><dd>{alert.protocol}</dd>
          </dl>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">🏷️ 检测结果</h3>
          <p className={`text-3xl font-bold ${alert.prediction === "Normal" ? "text-green-400" : "text-red-400"}`}>
            {alert.prediction === "Normal" ? "✅" : "⚠️"} {alert.prediction}
          </p>
          <p className="text-slate-400 text-sm mt-2">置信度: {(alert.confidence * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 mb-4">
        <h3 className="text-slate-400 text-xs mb-3">🔥 注意力热力图</h3>
        <p className="text-slate-500 text-sm">模型注意力权重可视化（加载中...）</p>
      </div>

      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
        <h3 className="text-slate-400 text-xs mb-3">📊 SHAP 特征重要性 Top-10</h3>
        <p className="text-slate-500 text-sm">特征重要性分析（加载中...）</p>
      </div>
    </div>
  );
}
