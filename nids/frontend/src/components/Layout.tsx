import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { to: "/dashboard", label: "仪表盘", icon: "📊" },
  { to: "/live", label: "实时检测", icon: "🔴" },
  { to: "/bigscreen", label: "可视化大屏", icon: "🖥️" },
  { to: "/history", label: "历史记录", icon: "📜" },
  { to: "/model", label: "模型管理", icon: "🧪" },
];

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-white flex">
      <nav className="w-56 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-1 shrink-0">
        <div className="text-lg font-bold text-cyan-400 mb-6 px-3">🛡️ NIDS</div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
              }`
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
