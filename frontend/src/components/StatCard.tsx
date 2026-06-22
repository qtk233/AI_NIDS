import type { ReactNode } from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: string;
  color?: string;
}

export function StatCard({ title, value, icon, trend, color = "#2ecc71" }: StatCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex items-center gap-3">
      <div
        className="text-2xl p-2 rounded-lg"
        style={{ backgroundColor: `${color}20`, color }}
      >
        {icon}
      </div>
      <div>
        <p className="text-slate-400 text-xs">{title}</p>
        <p className="text-white text-xl font-bold">{value}</p>
        {trend && <p className="text-green-400 text-xs">↑ {trend}</p>}
      </div>
    </div>
  );
}
