import React from 'react';
import { Layers } from 'lucide-react';
import { CategoryMetric, Language } from '../types';
import { translations } from '../i18n';

interface CategoryBreakdownProps {
  categories: Record<string, CategoryMetric>;
  lang: Language;
}

export const CategoryBreakdown: React.FC<CategoryBreakdownProps> = ({ categories, lang }) => {
  const t = translations[lang];

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
      <div className="flex items-center space-x-2.5 mb-1.5">
        <Layers className="w-5 h-5 text-brand-400" />
        <h2 className="text-base font-bold text-white tracking-tight">
          {t.categoriesHeader}
        </h2>
      </div>
      <p className="text-xs text-slate-400 mb-6">
        {t.categoriesDesc}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(categories).map(([key, cat]) => (
          <div
            key={key}
            className="p-4 rounded-xl bg-surface-900/80 border border-surface-700/60 hover:border-brand-500/30 transition-all group"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2.5">
                <span className="text-xl p-1.5 rounded-lg bg-surface-800 border border-surface-700/80 group-hover:scale-110 transition-transform">
                  {cat.icon}
                </span>
                <div>
                  <h3 className="text-xs font-bold text-slate-200 group-hover:text-white transition-colors">
                    {cat.name}
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {cat.count.toLocaleString()} {cat.unit}
                  </span>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded-full border border-brand-500/20">
                {cat.pct}%
              </span>
            </div>

            {/* Savings Progress Bar */}
            <div className="w-full bg-surface-800 h-2 rounded-full overflow-hidden mb-2">
              <div
                className="bg-gradient-to-r from-brand-500 to-teal-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(8, cat.pct))}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Saved</span>
              <span className="font-mono font-bold text-white">
                {cat.saved.toLocaleString()} tokens
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
