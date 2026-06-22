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

interface TopoNode {
  id: string;
  traffic: number;
}

interface TopoLink {
  source: string;
  target: string;
  attack: string;
  count: number;
}

export default function BigScreen() {
  const svgRef = useRef<SVGSVGElement>(null);

  const statsFetcher = useCallback(() => api.getStats(), []);
  const topoFetcher = useCallback(() => api.getTopology(), []);
  const { data: stats } = useApi<SystemStats>(statsFetcher);
  const { data: topo } = useApi<{ nodes: TopoNode[]; links: TopoLink[] }>(topoFetcher);

  useEffect(() => {
    if (!svgRef.current || !topo) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const nodes = topo.nodes;
    const links = topo.links;

    if (nodes.length === 0) {
      svg.append("text")
        .attr("x", 200).attr("y", 140)
        .attr("text-anchor", "middle")
        .attr("fill", "#64748b").attr("font-size", "12")
        .text("等待检测数据...");
      return;
    }

    // Layout: circle for nodes < 12, grid otherwise
    const w = 400, h = 280;
    if (nodes.length <= 12) {
      const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 30;
      nodes.forEach((n, i) => {
        const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
        (n as TopoNode & { x: number; y: number }).x = cx + r * Math.cos(angle);
        (n as TopoNode & { x: number; y: number }).y = cy + r * Math.sin(angle);
      });
    } else {
      const cols = Math.ceil(Math.sqrt(nodes.length));
      nodes.forEach((n, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        (n as TopoNode & { x: number; y: number }).x = 40 + (w - 80) * (col / (cols - 1 || 1));
        (n as TopoNode & { x: number; y: number }).y = 30 + (h - 60) * (row / (Math.ceil(nodes.length / cols) - 1 || 1));
      });
    }

    const typedNodes = nodes as (TopoNode & { x: number; y: number })[];

    // Node size based on traffic
    const maxTraffic = Math.max(...nodes.map((n) => n.traffic), 1);
    const nodeRadius = (n: TopoNode) => 6 + (n.traffic / maxTraffic) * 16;

    // Links
    svg.selectAll("line").data(links).enter()
      .append("line")
      .attr("x1", (d) => typedNodes.find((n) => n.id === d.source)?.x ?? 0)
      .attr("y1", (d) => typedNodes.find((n) => n.id === d.source)?.y ?? 0)
      .attr("x2", (d) => typedNodes.find((n) => n.id === d.target)?.x ?? 0)
      .attr("y2", (d) => typedNodes.find((n) => n.id === d.target)?.y ?? 0)
      .attr("stroke", (d) => d.attack === "Normal" ? "#334155" : "#e94560")
      .attr("stroke-width", (d) => Math.max(1, Math.log2(d.count + 1)))
      .attr("opacity", 0.5);

    // Nodes
    svg.selectAll("circle").data(typedNodes).enter()
      .append("circle")
      .attr("cx", (d) => d.x).attr("cy", (d) => d.y)
      .attr("r", (d) => nodeRadius(d))
      .attr("fill", (d) => d.traffic > maxTraffic * 0.5 ? "#e94560" : "#5dade2")
      .attr("opacity", 0.9);

    // Labels
    svg.selectAll("text").data(typedNodes).enter()
      .append("text")
      .attr("x", (d) => d.x).attr("y", (d) => d.y + nodeRadius(d) + 12)
      .attr("text-anchor", "middle").attr("fill", "#94a3b8").attr("font-size", "9")
      .text((d) => d.id.length > 15 ? d.id.slice(0, 13) + ".." : d.id);
  }, [topo]);

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
          <h3 className="text-slate-400 text-xs mb-2">🌐 实时攻击路径拓扑</h3>
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
