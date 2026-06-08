import { useEffect, useRef, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from "recharts";
import * as d3 from "d3";
import { api } from "../lib/api";
import type { SystemStats } from "../lib/types";
import { useApi } from "../hooks/useApi";

const timelineData = [
  { hour: "06:00", DoS: 8, DDoS: 2, BruteForce: 15, Botnet: 3 },
  { hour: "10:00", DoS: 25, DDoS: 12, BruteForce: 30, Botnet: 8 },
  { hour: "14:00", DoS: 45, DDoS: 20, BruteForce: 28, Botnet: 15 },
  { hour: "18:00", DoS: 30, DDoS: 15, BruteForce: 22, Botnet: 10 },
  { hour: "22:00", DoS: 12, DDoS: 5, BruteForce: 10, Botnet: 4 },
];

interface CounterProps {
  value: number;
  label: string;
}

function Counter({ value, label }: CounterProps) {
  return (
    <div className="text-center">
      <div className="text-3xl font-mono font-bold text-cyan-400">{value.toLocaleString()}</div>
      <div className="text-slate-500 text-xs mt-1">{label}</div>
    </div>
  );
}

export default function BigScreen() {
  const svgRef = useRef<SVGSVGElement>(null);
  const fetcher = useCallback(() => api.getStats(), []);
  const { data: stats } = useApi<SystemStats>(fetcher);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const nodes = [
      { id: "Internet", x: 50, y: 140 },
      { id: "Router", x: 160, y: 80 },
      { id: "Firewall", x: 160, y: 200 },
      { id: "Server", x: 300, y: 60 },
      { id: "DB", x: 300, y: 140 },
      { id: "Workstation", x: 300, y: 220 },
    ];
    const links: Array<{ source: string; target: string }> = [
      { source: "Internet", target: "Router" },
      { source: "Internet", target: "Firewall" },
      { source: "Router", target: "Server" },
      { source: "Firewall", target: "DB" },
      { source: "Router", target: "Workstation" },
    ];

    svg.selectAll("line").data(links).enter()
      .append("line")
      .attr("x1", (d) => nodes.find((n) => n.id === d.source)!.x)
      .attr("y1", (d) => nodes.find((n) => n.id === d.source)!.y)
      .attr("x2", (d) => nodes.find((n) => n.id === d.target)!.x)
      .attr("y2", (d) => nodes.find((n) => n.id === d.target)!.y)
      .attr("stroke", "#334155").attr("stroke-width", 2);

    svg.selectAll("circle").data(nodes).enter()
      .append("circle")
      .attr("cx", (d) => d.x).attr("cy", (d) => d.y).attr("r", 18)
      .attr("fill", (d) => d.id === "Internet" ? "#e94560" : "#5dade2");

    svg.selectAll("text").data(nodes).enter()
      .append("text")
      .attr("x", (d) => d.x).attr("y", (d) => d.y + 30)
      .attr("text-anchor", "middle").attr("fill", "#94a3b8").attr("font-size", "10")
      .text((d) => d.id);
  }, []);

  return (
    <div className="p-6" style={{ fontFamily: "'Orbitron', monospace" }}>
      <div className="text-center mb-6 border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold tracking-wider text-cyan-400">🛡️ NIDS 实时监控大屏</h1>
        <p className="text-slate-500 text-sm mt-1">NETWORK INTRUSION DETECTION SYSTEM</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <Counter value={stats?.total_detections ?? 0} label="检测总数" />
        <Counter value={stats?.total_alerts ?? 0} label="告警数" />
        <Counter value={stats ? parseFloat((stats.accuracy * 100).toFixed(1)) : 0} label="准确率 %" />
        <Counter value={stats?.detection_rate ?? 0} label="速率 (条/秒)" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-slate-400 text-xs mb-2">🌐 攻击路径拓扑</h3>
          <svg ref={svgRef} width={400} height={280} className="bg-slate-900 rounded-xl border border-slate-800" />
        </div>
        <div>
          <h3 className="text-slate-400 text-xs mb-2">⏱️ 24h 攻击时间线</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="hour" stroke="#666" />
              <YAxis stroke="#666" />
              <Tooltip />
              <Legend />
              <Bar dataKey="DoS" stackId="a" fill="#e94560" />
              <Bar dataKey="DDoS" stackId="a" fill="#f0c060" />
              <Bar dataKey="BruteForce" stackId="a" fill="#5dade2" />
              <Bar dataKey="Botnet" stackId="a" fill="#9b59b6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
