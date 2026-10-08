import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Activity, BarChart2, Compass, LayoutDashboard, Settings, Video, Zap } from 'lucide-react';

const SidebarLink = ({ to, icon: Icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
        isActive 
          ? 'bg-blue-600 text-white font-medium shadow-md' 
          : 'text-slate-400 hover:bg-slate-800 hover:text-white'
      }`
    }
  >
    <Icon size={20} />
    <span>{label}</span>
  </NavLink>
);

export default function Layout() {
  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col shadow-xl z-10">
        <div className="p-6 flex items-center gap-3 border-b border-slate-800">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Activity size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">TrendPulse</h1>
            <p className="text-xs text-slate-400 font-medium">Big Data Analytics</p>
          </div>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          <SidebarLink to="/" icon={LayoutDashboard} label="Overview" />
          <SidebarLink to="/factors" icon={BarChart2} label="Trending Factors" />
          <SidebarLink to="/strategy" icon={Compass} label="Content Strategy" />
          <SidebarLink to="/explorer" icon={Video} label="Video Explorer" />
          <SidebarLink to="/breakouts" icon={Zap} label="Breakout Videos" />
        </nav>
        
        <div className="p-4 border-t border-slate-800">
          <SidebarLink to="/pipeline" icon={Settings} label="Pipeline Monitor" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-8 shrink-0 justify-between">
          <h2 className="text-lg font-semibold text-slate-800">Real-Time Intelligence Platform</h2>
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Pipeline Active
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
