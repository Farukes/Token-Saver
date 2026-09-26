import React from 'react';
import { Network, Database, ShieldAlert, GitFork, ArrowRight, Sparkles } from 'lucide-react';
import { Language } from '../types';
import { translations } from '../i18n';

interface GatewayPreviewProps {
  lang: Language;
}

export const GatewayPreview: React.FC<GatewayPreviewProps> = ({ lang }) => {
  const t = translations[lang];

  const features = [
    {
      title: t.sqlSqueezer,
      desc: t.sqlSqueezerDesc,
      icon: <Database className="w-5 h-5 text-emerald-400" />,
      badge: "95-99% Savings",
    },
    {
      title: t.jsonStripper,
      desc: t.jsonStripperDesc,
      icon: <Network className="w-5 h-5 text-cyan-400" />,
      badge: "40-70% Savings",
    },
    {
      title: t.circuitBreaker,
      desc: t.circuitBreakerDesc,
      icon: <ShieldAlert className="w-5 h-5 text-rose-400" />,
      badge: "100% Protection",
    },
    {
      title: t.routerMux,
      desc: t.routerMuxDesc,
      icon: <GitFork className="w-5 h-5 text-purple-400" />,
      badge: "Universal Bridge",
    },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-2.5">
          <Sparkles className="w-5 h-5 text-brand-400" />
          <h2 className="text-base font-bold text-white tracking-tight">
            {t.gatewayHeader}
          </h2>
        </div>
        <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          Architecture V2.0
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-6">
        {t.gatewayDesc}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {features.map((f, i) => (
          <div
            key={i}
            className="p-4 rounded-xl bg-surface-900/80 border border-surface-700/60 hover:border-brand-500/30 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <div className="p-2 rounded-lg bg-surface-800 border border-surface-700/80">
                  {f.icon}
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-surface-800 text-brand-400 border border-brand-500/20">
                  {f.badge}
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-200 mb-1">
                {f.title}
              </h3>
              <p className="text-xs text-slate-400">
                {f.desc}
              </p>
            </div>
            <div className="mt-4 pt-2.5 border-t border-surface-800/80 flex items-center justify-between text-[11px] text-brand-400/90 font-semibold">
              <span>Cloudflare-grade MCP Proxy</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
