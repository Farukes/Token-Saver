import React from 'react';
import { Zap, TrendingUp, Sparkles, Cpu, DollarSign, CheckCircle2, Shield } from 'lucide-react';
import { TelemetryData, Language } from '../types';

interface SavingsHeroProps {
  telemetry: TelemetryData;
  lang: Language;
}

export const SavingsHero: React.FC<SavingsHeroProps> = ({ telemetry, lang }) => {
  const pct = telemetry.savings_pct || 91.7;
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  return (
    <div className="glass-panel p-6 sm:p-8 rounded-3xl relative overflow-hidden border border-brand-500/25 shadow-2xl shadow-brand-500/10">
      {/* Background radial glow */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-brand-500/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-8">
        {/* Left: Headline & Numbers */}
        <div className="space-y-4 max-w-xl text-center lg:text-left">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-300 text-xs font-bold font-mono">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            <span>{lang === 'tr' ? 'TOKEN KUMBARASI AKTİF' : 'TOKEN SAVINGS ENGINE ACTIVE'}</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            {lang === 'tr' ? (
              <>
                Bağlam Pencerenizi <span className="bg-gradient-to-r from-brand-400 via-emerald-300 to-teal-200 bg-clip-text text-transparent">Koruyun</span>, Maliyeti <span className="bg-gradient-to-r from-brand-400 to-teal-300 bg-clip-text text-transparent">%95 Azaltın</span>.
              </>
            ) : (
              <>
                Preserve Context Windows, <span className="bg-gradient-to-r from-brand-400 via-emerald-300 to-teal-200 bg-clip-text text-transparent">Cut Tokens by 95%</span>.
              </>
            )}
          </h2>

          <p className="text-xs sm:text-sm text-slate-300 font-medium leading-relaxed">
            {lang === 'tr'
              ? 'TokenJar, yapay zekâ asistanınız ile kod tabanınız arasında çalışarak Tree-sitter AST iskeletleri, fark önbelleği ve akıllı log budama filtreleriyle token israfını önler.'
              : 'TokenJar intercepts and compresses code reads, terminal runs, and file operations with Tree-sitter AST skeletons and differential caching.'}
          </p>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-2xl bg-surface-900/80 border border-surface-700/60">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">
                {lang === 'tr' ? 'Kazanılan Token' : 'Tokens Saved'}
              </span>
              <span className="text-xl sm:text-2xl font-extrabold font-mono text-brand-400">
                {(telemetry.total_saved / 1000).toFixed(1)}K
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-surface-900/80 border border-surface-700/60">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">
                {lang === 'tr' ? 'İşlenen Ham Veri' : 'Processed'}
              </span>
              <span className="text-xl sm:text-2xl font-extrabold font-mono text-cyan-400">
                {(telemetry.total_processed / 1000).toFixed(1)}K
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-surface-900/80 border border-surface-700/60">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">
                {lang === 'tr' ? 'Tasarruf ($)' : 'Dollars Saved'}
              </span>
              <span className="text-xl sm:text-2xl font-extrabold font-mono text-emerald-300">
                ${telemetry.dollars_saved.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Circular Radial Progress Meter */}
        <div className="flex flex-col items-center justify-center p-6 rounded-3xl bg-surface-900/90 border border-brand-500/25 shadow-xl relative group">
          <div className="relative flex items-center justify-center">
            {/* SVG Progress Ring */}
            <svg className="w-48 h-48 transform -rotate-90">
              {/* Background Track */}
              <circle
                cx="96"
                cy="96"
                r={radius}
                className="text-surface-800"
                strokeWidth="14"
                stroke="currentColor"
                fill="transparent"
              />
              {/* Active Animated Progress */}
              <circle
                cx="96"
                cy="96"
                r={radius}
                className="text-brand-400 transition-all duration-1000 ease-out"
                strokeWidth="14"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                stroke="url(#brandGradient)"
                fill="transparent"
              />
              <defs>
                <linearGradient id="brandGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#34d399" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
              </defs>
            </svg>

            {/* Inner Content */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <Zap className="w-5 h-5 text-brand-400 fill-brand-400 mb-1 animate-pulse" />
              <span className="text-3xl font-black font-mono text-white tracking-tight">
                {pct}%
              </span>
              <span className="text-[10px] uppercase font-mono font-bold text-slate-400 tracking-wider">
                {lang === 'tr' ? 'NET TASARRUF' : 'REDUCTION'}
              </span>
            </div>
          </div>

          <div className="mt-4 flex items-center space-x-2 text-xs text-brand-300 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" />
            <span>{lang === 'tr' ? 'Sıfır Fonksiyon Kaybı' : 'Zero Functionality Loss'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
