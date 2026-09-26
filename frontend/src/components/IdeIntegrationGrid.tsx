import React, { useState } from 'react';
import { 
  Bot, 
  Check, 
  Copy, 
  Power, 
  ExternalLink, 
  Sparkles, 
  Terminal, 
  Code2, 
  Workflow 
} from 'lucide-react';
import { IdeInfo, Language } from '../types';
import { translations } from '../i18n';

interface IdeIntegrationGridProps {
  ides: IdeInfo[];
  lang: Language;
  onToggleIde: (ideName: string) => Promise<void>;
}

export const IdeIntegrationGrid: React.FC<IdeIntegrationGridProps> = ({
  ides,
  lang,
  onToggleIde,
}) => {
  const t = translations[lang];
  const [toggling, setToggling] = useState<string | null>(null);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const handleToggle = async (name: string) => {
    try {
      setToggling(name);
      await onToggleIde(name);
    } finally {
      setToggling(null);
    }
  };

  const handleCopyPath = (path: string) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const getIdeIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('antigravity')) return <Sparkles className="w-5 h-5 text-purple-400" />;
    if (n.includes('cursor')) return <Code2 className="w-5 h-5 text-cyan-400" />;
    if (n.includes('claude code')) return <Terminal className="w-5 h-5 text-amber-400" />;
    if (n.includes('claude')) return <Bot className="w-5 h-5 text-orange-400" />;
    if (n.includes('windsurf')) return <Workflow className="w-5 h-5 text-teal-400" />;
    return <Code2 className="w-5 h-5 text-slate-400" />;
  };

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-2.5">
          <Bot className="w-5 h-5 text-brand-400" />
          <h2 className="text-base font-bold text-white tracking-tight">
            {t.idesHeader}
          </h2>
        </div>
        <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
          {ides.filter((i) => i.active).length} / {ides.length} {t.statusEnabled}
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-6">
        {t.idesDesc}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ides.map((ide) => {
          const isBusy = toggling === ide.name;
          const isCopied = copiedPath === ide.path;

          return (
            <div
              key={ide.name}
              className={`p-5 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                ide.active
                  ? 'bg-surface-900/90 border-brand-500/35 shadow-lg shadow-brand-500/5'
                  : 'bg-surface-900/50 border-surface-700/60 opacity-80 hover:opacity-100 hover:border-surface-600'
              }`}
            >
              <div>
                {/* Header row */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-surface-800 border border-surface-700/80">
                      {getIdeIcon(ide.name)}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">
                        {ide.name}
                      </h3>
                      <div className="flex items-center space-x-1.5 mt-0.5">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            ide.active ? 'bg-brand-400 animate-pulse' : 'bg-slate-500'
                          }`}
                        />
                        <span className="text-[11px] font-semibold text-slate-300">
                          {ide.active ? t.statusEnabled : t.statusDisabled}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Toggle Button */}
                  <button
                    onClick={() => handleToggle(ide.name)}
                    disabled={isBusy}
                    className={`p-2 rounded-xl border text-xs font-semibold flex items-center space-x-1.5 transition-all active:scale-95 disabled:opacity-50 ${
                      ide.active
                        ? 'bg-brand-500/15 hover:bg-rose-500/15 border-brand-500/30 hover:border-rose-500/30 text-brand-400 hover:text-rose-400'
                        : 'bg-surface-800 hover:bg-brand-500/20 border-surface-700 hover:border-brand-500/30 text-slate-300 hover:text-brand-300'
                    }`}
                    title={ide.active ? 'Disable' : 'Enable'}
                  >
                    <Power className={`w-3.5 h-3.5 ${isBusy ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {/* Path preview */}
                <div className="mt-3 p-2.5 rounded-lg bg-surface-950/80 border border-surface-800 flex items-center justify-between group">
                  <p className="text-[10px] font-mono text-slate-400 truncate max-w-[200px]" title={ide.path}>
                    {ide.path}
                  </p>
                  <button
                    onClick={() => handleCopyPath(ide.path)}
                    className="text-slate-400 hover:text-white p-1 rounded hover:bg-surface-800 transition-colors"
                    title={t.btnCopyPath}
                  >
                    {isCopied ? (
                      <Check className="w-3 h-3 text-brand-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              </div>

              {/* Status pill */}
              <div className="mt-4 pt-3 border-t border-surface-800/80 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Environment</span>
                <span
                  className={`font-semibold ${
                    ide.installed ? 'text-slate-300' : 'text-slate-500'
                  }`}
                >
                  {ide.installed ? t.statusInstalled : t.statusNotInstalled}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
