import React from 'react';
import { 
  Zap, 
  Cpu, 
  Database, 
  DollarSign, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2 
} from 'lucide-react';
import { TelemetryData, Language } from '../types';
import { translations } from '../i18n';

interface MetricCardsProps {
  telemetry: TelemetryData;
  lang: Language;
}

function formatNumber(num: number): string {
  if (num >= 1_000_000) {
    return (num / 1_000_000).toFixed(2) + 'M';
  }
  if (num >= 1_000) {
    return (num / 1_000).toFixed(1) + 'K';
  }
  return num.toLocaleString();
}

export const MetricCards: React.FC<MetricCardsProps> = ({ telemetry, lang }) => {
  const t = translations[lang];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Tokens Saved */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-brand-500/40 transition-all duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/10 rounded-full blur-2xl group-hover:bg-brand-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {t.tokensSaved}
          </span>
          <div className="h-9 w-9 rounded-xl bg-brand-500/15 border border-brand-500/30 flex items-center justify-center text-brand-400 group-hover:scale-110 transition-transform">
            <Zap className="w-4 h-4 fill-brand-400" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
            {formatNumber(telemetry.total_saved)}
          </span>
          <span className="inline-flex items-center text-xs font-bold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded-full border border-brand-500/20">
            <TrendingUp className="w-3 h-3 mr-1" />
            {telemetry.savings_pct}%
          </span>
        </div>
        <p className="text-[11px] text-slate-400 mt-2 flex items-center space-x-1">
          <CheckCircle2 className="w-3 h-3 text-brand-400" />
          <span>AST skeleton, diff cache & pruners</span>
        </p>
      </div>

      {/* 2. Tokens Processed */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-cyan-500/40 transition-all duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {t.tokensProcessed}
          </span>
          <div className="h-9 w-9 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
            <Cpu className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
            {formatNumber(telemetry.total_processed)}
          </span>
          <span className="text-xs font-medium text-slate-400">raw payload</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-2">
          Dispatched without context window bloat
        </p>
      </div>

      {/* 3. Cache Storage & L2 Database */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-indigo-500/40 transition-all duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {t.l2Storage}
          </span>
          <div className="h-9 w-9 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
            <Database className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
            {telemetry.l2_cache.disk_mb} MB
          </span>
          <span className="text-xs font-semibold text-indigo-300 font-mono">
            {telemetry.l2_cache.entries} keys
          </span>
        </div>
        <div className="mt-2">
          {telemetry.l2_cache.warning ? (
            <p className="text-[11px] text-amber-400 flex items-center space-x-1 font-medium">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>{t.l2Warning}</span>
            </p>
          ) : (
            <p className="text-[11px] text-slate-400">
              High-speed SQLite WAL persistent memory
            </p>
          )}
        </div>
      </div>

      {/* 4. Financial Savings */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:border-emerald-500/40 transition-all duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            {t.estimatedSavings}
          </span>
          <div className="h-9 w-9 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
            <DollarSign className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
            ${telemetry.dollars_saved.toFixed(2)}
          </span>
          <span className="text-xs font-medium text-emerald-400">saved</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-2">
          Estimated across Sonnet & GPT-4o usage
        </p>
      </div>
    </div>
  );
};
