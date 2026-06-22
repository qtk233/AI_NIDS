import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { AlertItem } from "../lib/types";

interface ShapItem {
  feature: string;
  value: number;
  importance: number;
}

interface ExplainData {
  shap_values: ShapItem[];
  attention: Array<{ layer: number; weights: number[][][] }>;
  prediction: string;
  confidence: number;
}

const HEATMAP_COLORS = [
  "#1a1a2e", "#16213e", "#0f3460", "#533483",
  "#e94560", "#f0c060", "#2ecc71",
];

function colorForValue(val: number, maxVal: number): string {
  if (maxVal === 0) return HEATMAP_COLORS[0];
  const idx = Math.min(Math.floor((val / maxVal) * (HEATMAP_COLORS.length - 0.01)), HEATMAP_COLORS.length - 1);
  return HEATMAP_COLORS[idx];
}

export default function TrafficDetail() {
  const { id } = useParams<{ id: string }>();
  const [alert, setAlert] = useState<AlertItem | null>(null);
  const [explain, setExplain] = useState<ExplainData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      api.getAlert(id),
      api.explainAlert(id).catch(() => null),
    ]).then(([alertRes, explainRes]) => {
      setAlert(alertRes.data);
      setExplain(explainRes);
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading || !alert) {
    return <div className="p-8 text-slate-400">Loading...</div>;
  }

  const maxImportance = explain?.shap_values[0]?.importance ?? 0;
  const maxAttnVal = explain?.attention[0]?.weights
    ? Math.max(...explain.attention[0].weights.flat(2))
    : 0;

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

      {/* ── Attention Heatmap ── */}
      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 mb-4">
        <h3 className="text-slate-400 text-xs mb-3">🔥 注意力热力图 (层 0)</h3>
        {explain?.attention && explain.attention.length > 0 ? (
          <div className="overflow-x-auto">
            {explain.attention[0].weights.slice(0, 4).map((headWeights, headIdx) => {
              const seqLen = headWeights.length;
              return (
                <div key={headIdx} className="mb-2">
                  <span className="text-slate-500 text-xs">Head {headIdx}</span>
                  <div className="flex gap-px" style={{ height: seqLen > 32 ? 6 : 12 }}>
                    {headWeights.slice(0, 32).map((row, i) => (
                      <div key={i} className="flex flex-col gap-px" style={{ flex: 1 }}>
                        {row.slice(0, 32).map((val, j) => (
                          <div
                            key={j}
                            className="w-full"
                            style={{
                              height: seqLen > 32 ? 6 : 12,
                              backgroundColor: colorForValue(val, maxAttnVal),
                              opacity: val > maxAttnVal * 0.01 ? 1 : 0.1,
                            }}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-500 text-sm">暂无注意力数据</p>
        )}
      </div>

      {/* ── SHAP Feature Importance ── */}
      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
        <h3 className="text-slate-400 text-xs mb-3">
          📊 特征重要性 Top-10（Gradient × Input）
        </h3>
        {explain?.shap_values && explain.shap_values.length > 0 ? (
          <div className="space-y-1.5">
            {explain.shap_values.map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-slate-400 w-40 truncate text-right" title={item.feature}>
                  {item.feature}
                </span>
                <div className="flex-1 bg-slate-800 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${maxImportance > 0 ? (item.importance / maxImportance) * 100 : 0}%`,
                      backgroundColor: item.importance > 0 ? "#5dade2" : "#e94560",
                    }}
                  />
                </div>
                <span className="text-slate-500 w-20 text-right text-xs">
                  {item.importance.toExponential(2)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-sm">需要上传 PCAP 或等待模拟器产生带 stat_features 的记录</p>
        )}
      </div>
    </div>
  );
}
