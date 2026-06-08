import { useCallback } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";
import { Shield, AlertTriangle, CheckCircle, Zap } from "lucide-react";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";
import type { SystemStats } from "../lib/types";
import { StatCard } from "../components/StatCard";

const COLORS = ["#2ecc71", "#e94560", "#f0c060", "#5dade2", "#9b59b6", "#e67e22", "#1abc9c", "#e74c3c"];

const trendData = [
  { hour: "00:00", attacks: 12 }, { hour: "04:00", attacks: 8 },
  { hour: "08:00", attacks: 35 }, { hour: "12:00", attacks: 67 },
  { hour: "16:00", attacks: 45 }, { hour: "20:00", attacks: 28 },
];

export default function Dashboard() {
  const fetcher = useCallback(() => api.getStats(), []);
  const { data: stats, loading, error } = useApi<SystemStats>(fetcher);

  const displayStats = stats || {
    total_detections: 0, total_alerts: 0, accuracy: 0, detection_rate: 0,
    attack_distribution: {},
  };

  const pieData = Object.entries(displayStats.attack_distribution).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">📊 仪表盘</h1>

      {error && (
        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3 mb-4 text-yellow-400 text-sm">
          后端未连接 — 显示演示数据
        </div>
      )}

      {loading && !stats && (
        <div className="p-8 text-slate-400">Loading...</div>
      )}

      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard title="检测总数" value={displayStats.total_detections.toLocaleString()} icon={<Shield size={20} />} color="#5dade2" trend="12%" />
        <StatCard title="告警数" value={displayStats.total_alerts.toLocaleString()} icon={<AlertTriangle size={20} />} color="#e94560" />
        <StatCard title="准确率" value={`${(displayStats.accuracy * 100).toFixed(1)}%`} icon={<CheckCircle size={20} />} color="#2ecc71" />
        <StatCard title="检测速率" value={`${displayStats.detection_rate}/秒`} icon={<Zap size={20} />} color="#f0c060" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-white text-sm mb-4">近 24h 检测趋势</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="hour" stroke="#666" />
              <YAxis stroke="#666" />
              <Tooltip />
              <Line type="monotone" dataKey="attacks" stroke="#e94560" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h3 className="text-white text-sm mb-4">攻击类型分布</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name }) => name}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
