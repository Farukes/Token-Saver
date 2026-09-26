import React from 'react';
import { 
  LayoutDashboard, 
  FlaskConical, 
  Bot, 
  Sliders, 
  Network, 
  Sparkles 
} from 'lucide-react';
import { Language } from '../types';

export type TabType = 'overview' | 'playground' | 'ides' | 'rules' | 'gateway';

interface NavigationTabsProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  lang: Language;
}

export const NavigationTabs: React.FC<NavigationTabsProps> = ({
  activeTab,
  onTabChange,
  lang,
}) => {
  const tabs: { id: TabType; labelEn: string; labelTr: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'overview',
      labelEn: 'Telemetry & Metrics',
      labelTr: 'Telemetri ve Metrikler',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      id: 'playground',
      labelEn: 'Interactive Playground',
      labelTr: 'İnteraktif Deneme Alanı',
      icon: <FlaskConical className="w-4 h-4 text-emerald-400" />,
      badge: 'NEW',
    },
    {
      id: 'ides',
      labelEn: 'IDE & Agent Hub',
      labelTr: 'IDE ve Ajan Merkezi',
      icon: <Bot className="w-4 h-4" />,
    },
    {
      id: 'rules',
      labelEn: 'Optimization Policies',
      labelTr: 'Optimizasyon Kuralları',
      icon: <Sliders className="w-4 h-4" />,
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
    <div className="flex items-center justify-start space-x-1.5 p-1.5 rounded-2xl bg-surface-900/90 border border-surface-700/80 backdrop-blur-xl overflow-x-auto custom-scrollbar">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const label = lang === 'tr' ? tab.labelTr : tab.labelEn;

        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap relative ${
              isActive
                ? 'bg-gradient-to-r from-brand-600/90 to-emerald-600 text-white shadow-lg shadow-brand-500/25 border border-brand-400/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800/80 border border-transparent'
            }`}
          >
            {tab.icon}
            <span>{label}</span>
            {tab.badge && (
              <span
                className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full font-black ${
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'bg-brand-500/15 text-brand-300 border border-brand-500/30'
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
