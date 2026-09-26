import React, { useState } from 'react';
import { Sliders, Shield, Terminal, Scissors, FileCode, CheckCircle2 } from 'lucide-react';
import { ConfigData, RulesData, Language } from '../types';
import { translations } from '../i18n';

interface RulesConfigManagerProps {
  config: ConfigData;
  rules: RulesData;
  lang: Language;
  onUpdateConfig: (updated: Partial<ConfigData>) => Promise<void>;
}

export const RulesConfigManager: React.FC<RulesConfigManagerProps> = ({
  config,
  rules,
  lang,
  onUpdateConfig,
}) => {
  const t = translations[lang];
  const [updatingKey, setUpdatingKey] = useState<string | null>(null);

  const handleToggle = async (key: keyof ConfigData) => {
    try {
      setUpdatingKey(key);
      await onUpdateConfig({ [key]: !config[key] });
    } finally {
      setUpdatingKey(null);
    }
  };

  const ruleItems = [
    {
      key: 'lockfile_shield' as keyof ConfigData,
      title: 'Lockfile Shield',
      desc: t.ruleLockfile,
      enabled: config.lockfile_shield,
      icon: <Shield className="w-4 h-4 text-emerald-400" />,
      tag: '99% savings',
    },
    {
      key: 'compact_output' as keyof ConfigData,
      title: 'Output & Log Pruner',
      desc: t.ruleCompact,
      enabled: config.compact_output,
      icon: <Terminal className="w-4 h-4 text-cyan-400" />,
      tag: '80% savings',
    },
    {
      key: 'prevent_truncation' as keyof ConfigData,
      title: 'Zero Truncation Mandate',
      desc: t.ruleTruncation,
      enabled: config.prevent_truncation,
      icon: <CheckCircle2 className="w-4 h-4 text-teal-400" />,
      tag: 'Strict Code Quality',
    },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
      <div className="flex items-center space-x-2.5 mb-1.5">
        <Sliders className="w-5 h-5 text-brand-400" />
        <h2 className="text-base font-bold text-white tracking-tight">
          {t.rulesHeader}
        </h2>
      </div>
      <p className="text-xs text-slate-400 mb-6">
        {t.rulesDesc}
      </p>

      <div className="space-y-3.5">
        {ruleItems.map((item) => {
          const isBusy = updatingKey === item.key;

          return (
            <div
              key={item.key}
              className="p-4 rounded-xl bg-surface-900/80 border border-surface-700/60 hover:border-surface-600 transition-all flex items-center justify-between gap-4"
            >
              <div className="flex items-start space-x-3.5">
                <div className="p-2 rounded-lg bg-surface-800 border border-surface-700/70 mt-0.5">
                  {item.icon}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-white">
                      {item.title}
                    </h3>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-surface-800 text-brand-400 border border-brand-500/20">
                      {item.tag}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 max-w-xl">
                    {item.desc}
                  </p>
                </div>
              </div>

              {/* Custom Toggle Switch */}
              <button
                type="button"
                onClick={() => handleToggle(item.key)}
                disabled={isBusy}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50 ${
                  item.enabled ? 'bg-brand-500' : 'bg-surface-700'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    item.enabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
