import React from 'react';
import { 
  Zap, 
  RotateCw, 
  Trash2, 
  RotateCcw, 
  Globe, 
  Radio, 
  ShieldCheck, 
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { Language } from '../types';
import { translations } from '../i18n';

interface HeaderProps {
  lang: Language;
  onToggleLang: () => void;
  isLive: boolean;
  version: string;
  onRefresh: () => void;
  onClearCache: () => void;
  onResetStats: () => void;
  isClearingCache: boolean;
  isResettingStats: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  lang,
  onToggleLang,
  isLive,
  version,
  onRefresh,
  onClearCache,
  onResetStats,
  isClearingCache,
  isResettingStats,
}) => {
  const t = translations[lang];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-surface-700/60 bg-surface-950/85 backdrop-blur-xl px-6 py-4 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center space-x-3.5">
          <div className="relative group">
            <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-brand-600 via-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-brand-500/25 group-hover:scale-105 transition-all">
              <span className="text-2xl filter drop-shadow">🍯</span>
            </div>
            <div className="absolute -bottom-1 -right-1 h-3.5 w-3.5 bg-brand-400 rounded-full border-2 border-surface-950 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                {t.title}
              </h1>
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-surface-800 text-brand-400 border border-brand-500/20 shadow-sm">
                v{version}
              </span>
              <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm transition-all"
                style={{
                  backgroundColor: isLive ? 'rgba(16, 185, 129, 0.12)' : 'rgba(234, 179, 8, 0.12)',
                  borderColor: isLive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(234, 179, 8, 0.3)',
                  color: isLive ? '#34d399' : '#facc15',
                }}
              >
                <Radio className={`w-3 h-3 ${isLive ? 'animate-pulse text-brand-400' : 'text-yellow-400'}`} />
                <span>{isLive ? t.badgeLive : t.badgeOffline}</span>
              </div>
            </div>
            <p className="text-xs text-slate-400 font-medium mt-0.5">
              {t.subtitle}
            </p>
          </div>
        </div>

        {/* Global actions */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Purge Cache Button */}
          <button
            onClick={onClearCache}
            disabled={isClearingCache}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-surface-850 hover:bg-surface-800 text-slate-300 hover:text-white border border-surface-700/80 text-xs font-semibold shadow-sm transition-all active:scale-95 disabled:opacity-50"
            title={t.btnClearCache}
          >
            <Trash2 className={`w-3.5 h-3.5 text-rose-400 ${isClearingCache ? 'animate-spin' : ''}`} />
            <span>{isClearingCache ? t.clearingCache : t.btnClearCache}</span>
          </button>

          {/* Reset Stats Button */}
          <button
            onClick={onResetStats}
            disabled={isResettingStats}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-surface-850 hover:bg-surface-800 text-slate-300 hover:text-white border border-surface-700/80 text-xs font-semibold shadow-sm transition-all active:scale-95 disabled:opacity-50"
            title={t.btnResetStats}
          >
            <RotateCcw className={`w-3.5 h-3.5 text-amber-400 ${isResettingStats ? 'animate-spin' : ''}`} />
            <span>{isResettingStats ? t.resettingStats : t.btnResetStats}</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-surface-850 hover:bg-surface-800 text-slate-300 hover:text-white border border-surface-700/80 text-xs font-semibold shadow-sm transition-all active:scale-95"
            title={t.btnRefresh}
          >
            <RotateCw className="w-3.5 h-3.5 text-brand-400" />
            <span>{t.btnRefresh}</span>
          </button>

          {/* Language Toggle */}
          <button
            onClick={onToggleLang}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 hover:text-brand-200 border border-brand-500/30 text-xs font-bold font-mono transition-all active:scale-95 shadow-sm"
            title="Dili Değiştir / Change Language"
          >
            <Globe className="w-3.5 h-3.5 text-brand-400" />
            <span>{lang === 'en' ? 'TR (Türkçe)' : 'EN (English)'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
