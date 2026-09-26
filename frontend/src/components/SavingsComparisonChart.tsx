import React from 'react';
import { TrendingDown, ShieldAlert, Zap } from 'lucide-react';
import { Language } from '../types';

export const SavingsComparisonChart: React.FC<{ lang: Language }> = ({ lang }) => {
  return (
    <div className="glass-panel p-6 rounded-3xl relative overflow-hidden">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-6">
        <div>
          <div className="flex items-center space-x-2">
            <TrendingDown className="w-5 h-5 text-brand-400" />
            <h3 className="text-base font-bold text-white tracking-tight">
              {lang === 'tr' ? 'Bağlam Penceresi Tüketim Eğrisi' : 'Context Window Consumption Curve'}
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {lang === 'tr'
              ? 'Standart AI asistanı veri patlaması vs. TokenJar akıllı sıkıştırma hattı'
              : 'Standard unbounded AI context dumps vs. TokenJar intelligent compression'}
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4 text-xs font-semibold">
          <div className="flex items-center space-x-1.5 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span>{lang === 'tr' ? 'TokenJar Olmadan (Bağlam Taşması)' : 'Without TokenJar (Context Bloat)'}</span>
          </div>
          <div className="flex items-center space-x-1.5 text-brand-400">
            <span className="w-2.5 h-2.5 rounded-full bg-brand-400" />
            <span>{lang === 'tr' ? 'TokenJar ile (-%92)' : 'With TokenJar (-92%)'}</span>
          </div>
        </div>
      </div>

      {/* SVG Chart Graphic */}
      <div className="relative h-44 w-full">
        <svg className="w-full h-full overflow-visible" viewBox="0 0 800 160" preserveAspectRatio="none">
          <defs>
            <linearGradient id="unboundedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="tokenjarGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1="0" y1="40" x2="800" y2="40" stroke="rgba(255,255,255,0.05)" strokeDasharray="4" />
          <line x1="0" y1="80" x2="800" y2="80" stroke="rgba(255,255,255,0.05)" strokeDasharray="4" />
          <line x1="0" y1="120" x2="800" y2="120" stroke="rgba(255,255,255,0.05)" strokeDasharray="4" />

          {/* Unbounded Area Fill (Red) */}
          <polygon
            points="0,150 100,130 200,110 300,95 400,65 500,45 600,25 700,15 800,10 800,155 0,155"
            fill="url(#unboundedGrad)"
          />
          {/* Unbounded Line */}
          <polyline
            points="0,150 100,130 200,110 300,95 400,65 500,45 600,25 700,15 800,10"
            fill="none"
            stroke="#f43f5e"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* TokenJar Area Fill (Green) */}
          <polygon
            points="0,150 100,148 200,145 300,143 400,142 500,140 600,138 700,137 800,136 800,155 0,155"
            fill="url(#tokenjarGrad)"
          />
          {/* TokenJar Line */}
          <polyline
            points="0,150 100,148 200,145 300,143 400,142 500,140 600,138 700,137 800,136"
            fill="none"
            stroke="#10b981"
            strokeWidth="3.5"
            strokeLinecap="round"
          />

          {/* Markers */}
          <circle cx="800" cy="10" r="5" fill="#f43f5e" />
          <circle cx="800" cy="136" r="5" fill="#10b981" />
        </svg>

        {/* Dynamic Badges on graph */}
        <div className="absolute top-2 right-4 text-[10px] font-mono font-bold text-rose-300 bg-rose-500/20 px-2 py-0.5 rounded border border-rose-500/30">
          {lang === 'tr' ? '128K Token (Tavan Limiti)' : '128K Limit (Context Crash)'}
        </div>
        <div className="absolute bottom-2 right-4 text-[10px] font-mono font-bold text-brand-300 bg-brand-500/20 px-2 py-0.5 rounded border border-brand-500/30">
          {lang === 'tr' ? '12.4K Token (Hafif ve Hızlı)' : '12.4K Stable (Zero Compaction)'}
        </div>
      </div>
    </div>
  );
};
