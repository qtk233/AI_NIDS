import { useCallback } from "react";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";

interface ModelInfo {
  version: string;
  params_count: number;
  inference_time_ms: number;
}

interface ModelMetrics {
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  confusion_matrix: number[][];
  class_names: string[];
}

export default function ModelManagement() {
  const infoFetcher = useCallback(() => api.getModelInfo(), []);
  const metricsFetcher = useCallback(() => api.getModelMetrics(), []);
  const { data: info } = useApi<ModelInfo>(infoFetcher);
  const { data: metrics } = useApi<ModelMetrics>(metricsFetcher);

  if (!info || !metrics) {
    return <div className="p-8 text-slate-400">Loading...</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">🧪 模型管理</h1>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">版本信息</h3>
          <p className="text-white text-lg font-bold">{info.version}</p>
          <p className="text-slate-400 text-xs mt-1">参数: {(info.params_count / 1e6).toFixed(1)}M</p>
          <p className="text-slate-400 text-xs">推理: {info.inference_time_ms}ms/流</p>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-slate-400 text-xs mb-3">性能指标</h3>
          <p className="text-green-400 text-lg font-bold">准确率: {(metrics.accuracy * 100).toFixed(1)}%</p>
          <p className="text-blue-400 text-sm">Macro F1: {(metrics.macro_f1 * 100).toFixed(1)}%</p>
          <p className="text-blue-400 text-sm">Weighted F1: {(metrics.weighted_f1 * 100).toFixed(1)}%</p>
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
            {metrics.class_names.map((name, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-slate-400 w-20 truncate">{name}</span>
                <div className="flex-1 flex gap-0.5">
                  {(metrics.confusion_matrix[i] ?? []).map((val, j) => {
                    const maxVal = Math.max(...metrics.confusion_matrix.flat(), 1);
                    return (
                      <div
                        key={j}
                        className="h-4 rounded-sm"
                        style={{
                          width: `${(val / maxVal) * 100}%`,
                          backgroundColor: i === j ? "#2ecc71" : "#e94560",
                          opacity: val ? 1 : 0,
                        }}
                        title={`${name}→${metrics.class_names[j]}: ${val}`}
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
          <p className="text-slate-500 text-sm">训练完成后加载 ROC 曲线数据</p>
        </div>
      </div>
    </div>
  );
}
