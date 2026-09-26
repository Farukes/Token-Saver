import React from 'react';
import { 
  LayoutDashboard, 
  FlaskConical, 
  Bot, 
  Sliders, 
  Network, 
  FileText, 
  Trash2, 
  RotateCcw, 
  Globe, 
  Radio, 
  Lock,
  ExternalLink,
  Zap
} from 'lucide-react';
import { Language } from '../types';

export type ViewTab = 'overview' | 'playground' | 'ides' | 'rules' | 'gateway';

interface SidebarProps {
  activeTab: ViewTab;
  onTabChange: (tab: ViewTab) => void;
  lang: Language;
  onToggleLang: () => void;
  isLive: boolean;
  version: string;
  onClearCache: () => void;
  onResetStats: () => void;
  isClearingCache: boolean;
  isResettingStats: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  lang,
  onToggleLang,
  isLive,
  version,
  onClearCache,
  onResetStats,
  isClearingCache,
  isResettingStats,
}) => {
  const navItems: { id: ViewTab; labelEn: string; labelTr: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'overview',
      labelEn: 'Live Analytics',
      labelTr: 'Canlı Analitik',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      id: 'playground',
      labelEn: 'Token Playground',
      labelTr: 'Token Laboratuvarı',
      icon: <FlaskConical className="w-4 h-4 text-emerald-400" />,
      badge: 'LIVE',
    },
    {
      id: 'ides',
      labelEn: 'Connected IDEs',
      labelTr: 'Bağlı IDE\'ler',
      icon: <Bot className="w-4 h-4 text-cyan-400" />,
    },
    {
      id: 'rules',
      labelEn: 'Compression Rules',
      labelTr: 'Sıkıştırma Kuralları',
      icon: <Sliders className="w-4 h-4 text-amber-400" />,
    },
    {
      id: 'gateway',
      labelEn: 'V2 MCP Gateway',
      labelTr: 'V2 MCP Ağ Geçidi',
      icon: <Network className="w-4 h-4 text-indigo-400" />,
      badge: 'V2.0',
    },
  ];

  return (
    <aside className="w-64 bg-surface-900/95 border-r border-surface-700/70 flex flex-col justify-between p-5 backdrop-blur-2xl z-40 flex-shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="flex items-center space-x-3 pb-6 mb-6 border-b border-surface-700/60">
          <div className="relative">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-brand-600 via-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-brand-500/25">
              <span className="text-xl">🍯</span>
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 bg-brand-400 rounded-full border-2 border-surface-900 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-extrabold tracking-tight text-white font-sans">
                TokenJar
              </h1>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-surface-800 text-brand-400 border border-brand-500/20">
                v{version}
              </span>
            </div>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <Radio className={`w-2.5 h-2.5 ${isLive ? 'text-brand-400 animate-pulse' : 'text-amber-400'}`} />
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
                {isLive ? (lang === 'tr' ? 'Canlı Motor' : 'Engine Live') : (lang === 'tr' ? 'Demo Modu' : 'Demo Mode')}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 px-3 mb-2 block">
            {lang === 'tr' ? 'Gezinme' : 'Navigation'}
          </span>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            const label = lang === 'tr' ? item.labelTr : item.labelEn;

            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-600 to-emerald-600 text-white shadow-lg shadow-brand-500/20 border border-brand-400/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-surface-800/80 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  {item.icon}
                  <span>{label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full font-black ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-brand-500/15 text-brand-300 border border-brand-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Controls & System Info */}
      <div className="pt-5 border-t border-surface-700/60 space-y-3">
        {/* Quick actions row */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onClearCache}
            disabled={isClearingCache}
            className="flex items-center justify-center space-x-1 px-2.5 py-2 rounded-xl bg-surface-850 hover:bg-surface-800 text-slate-300 hover:text-white border border-surface-700/80 text-[11px] font-semibold transition-all disabled:opacity-50"
            title="Purge L2 Persistent Cache"
          >
            <Trash2 className={`w-3 h-3 text-rose-400 ${isClearingCache ? 'animate-spin' : ''}`} />
            <span>{isClearingCache ? '...' : (lang === 'tr' ? 'Önbellek' : 'Purge')}</span>
          </button>

          <button
            onClick={onResetStats}
            disabled={isResettingStats}
            className="flex items-center justify-center space-x-1 px-2.5 py-2 rounded-xl bg-surface-850 hover:bg-surface-800 text-slate-300 hover:text-white border border-surface-700/80 text-[11px] font-semibold transition-all disabled:opacity-50"
            title="Reset Session Telemetry"
          >
            <RotateCcw className={`w-3 h-3 text-amber-400 ${isResettingStats ? 'animate-spin' : ''}`} />
            <span>{isResettingStats ? '...' : (lang === 'tr' ? 'Sıfırla' : 'Reset')}</span>
          </button>
        </div>

        {/* Language switch button */}
        <button
          onClick={onToggleLang}
          className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-xl bg-surface-850 hover:bg-surface-800 text-brand-300 border border-surface-700/80 text-xs font-bold transition-all"
        >
          <Globe className="w-3.5 h-3.5 text-brand-400" />
          <span>{lang === 'en' ? 'Türkçe (TR)' : 'English (EN)'}</span>
        </button>

        {/* System Footprint Badge */}
        <div className="p-3 rounded-xl bg-surface-950/80 border border-surface-800 text-[10px] text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1 text-slate-300">
              <Lock className="w-3 h-3 text-brand-400" />
              <span className="font-semibold">Zero-Telemetry</span>
            </span>
            <span className="text-brand-400 font-mono font-bold">100% Local</span>
          </div>
          <p className="text-[9px] text-slate-500">
            Zero background RAM &bull; Port: 4141
          </p>
        </div>
      </div>
    </aside>
  );
};
