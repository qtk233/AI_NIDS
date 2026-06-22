import { useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";

interface ModelInfo {
  version: string;
  params_count: number;
  inference_time_ms: number;
}

interface RocCurve {
  class: string;
  auc: number;
  points: Array<{ fpr: number; tpr: number }>;
}

interface ModelMetrics {
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  confusion_matrix: number[][];
  class_names: string[];
  roc_curves: RocCurve[];
}

export default function ModelManagement() {
  const infoFetcher = useCallback(() => api.getModelInfo(), []);
  const metricsFetcher = useCallback(() => api.getModelMetrics(), []);
  const { data: info, loading: infoLoading } = useApi<ModelInfo>(infoFetcher);
  const { data: metrics, loading: metricsLoading } = useApi<ModelMetrics>(metricsFetcher);

  const displayInfo = info || { version: "—", params_count: 0, inference_time_ms: 0 };
  const displayMetrics = metrics || {
    accuracy: 0, macro_f1: 0, weighted_f1: 0,
    confusion_matrix: [], class_names: [],
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">🧪 模型管理</h1>

      {(infoLoading || metricsLoading) && !info && !metrics && (
        <div className="p-8 text-slate-400">Loading...</div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">版本信息</h3>
          <p className="text-white text-lg font-bold">{displayInfo.version}</p>
          <p className="text-slate-400 text-xs mt-1">参数: {(displayInfo.params_count / 1e6).toFixed(1)}M</p>
          <p className="text-slate-400 text-xs">推理: {displayInfo.inference_time_ms}ms/流</p>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">性能指标</h3>
          <p className="text-green-400 text-lg font-bold">准确率: {(displayMetrics.accuracy * 100).toFixed(1)}%</p>
          <p className="text-blue-400 text-sm">Macro F1: {(displayMetrics.macro_f1 * 100).toFixed(1)}%</p>
          <p className="text-blue-400 text-sm">Weighted F1: {(displayMetrics.weighted_f1 * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">操作</h3>
          <button
            onClick={() => api.post("/api/model/reload")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500"
          >
            🔄 重新加载模型
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">🧩 混淆矩阵</h3>
          <div className="grid gap-1">
            {displayMetrics.class_names.map((name, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-slate-400 w-20 truncate">{name}</span>
                <div className="flex-1 flex gap-0.5">
                  {(displayMetrics.confusion_matrix[i] ?? []).map((val, j) => {
                    const maxVal = Math.max(...displayMetrics.confusion_matrix.flat(), 1);
                    return (
                      <div
                        key={j}
                        className="h-4 rounded-sm"
                        style={{
                          width: `${(val / maxVal) * 100}%`,
                          backgroundColor: i === j ? "#2ecc71" : "#e94560",
                          opacity: val ? 1 : 0,
                        }}
                        title={`${name}→${displayMetrics.class_names[j]}: ${val}`}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">📊 ROC 曲线</h3>
          {displayMetrics.roc_curves && displayMetrics.roc_curves.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="fpr" stroke="#666" tick={{ fontSize: 10 }}
                  label={{ value: "FPR", position: "insideBottom", offset: -5, fill: "#666", fontSize: 10 }}
                />
                <YAxis dataKey="tpr" stroke="#666" tick={{ fontSize: 10 }} domain={[0, 1]}
                  label={{ value: "TPR", angle: -90, position: "insideLeft", fill: "#666", fontSize: 10 }}
                />
                <Tooltip />
                <Legend />
                <Line type="monotone" data={[{ fpr: 0, tpr: 0 }, { fpr: 1, tpr: 1 }]}
                  dataKey="tpr" stroke="#444" strokeDasharray="4 4" name="Random" dot={false} />
                {displayMetrics.roc_curves.map((curve, i) => (
                  <Line key={curve.class} type="monotone"
                    data={curve.points}
                    dataKey="tpr"
                    name={`${curve.class} (AUC=${curve.auc.toFixed(3)})`}
                    stroke={["#2ecc71", "#e94560", "#f0c060"][i % 3]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-500 text-sm">训练完成后加载 ROC 曲线数据</p>
          )}
        </div>
      </div>
    </div>
  );
}
