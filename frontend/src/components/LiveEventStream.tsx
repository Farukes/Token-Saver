import React, { useState, useEffect } from 'react';
import { Activity, Clock, Zap, Check, Terminal, FileCode, Search, MapPin } from 'lucide-react';
import { Language } from '../types';
import { translations } from '../i18n';

interface LogEvent {
  id: string;
  time: string;
  tool: string;
  action: string;
  originalTokens: number;
  savedTokens: number;
  pct: number;
  cacheHit?: boolean;
}

interface LiveEventStreamProps {
  lang: Language;
}

export const LiveEventStream: React.FC<LiveEventStreamProps> = ({ lang }) => {
  const t = translations[lang];

  const initialEvents: LogEvent[] = [
    {
      id: '1',
      time: 'Just now',
      tool: 'read_file_smart',
      action: 'Targeted line slice (lines 1-80) with semantic diff cache',
      originalTokens: 14200,
      savedTokens: 13490,
      pct: 95.0,
      cacheHit: true,
    },
    {
      id: '2',
      time: '12s ago',
      tool: 'tool_get_code_skeleton',
      action: 'Extracted Tree-sitter signatures and AST types',
      originalTokens: 8400,
      savedTokens: 7644,
      pct: 91.0,
      cacheHit: false,
    },
    {
      id: '3',
      time: '34s ago',
      tool: 'run_command_smart',
      action: 'Pruned repetitive pytest passing logs and tracebacks',
      originalTokens: 18500,
      savedTokens: 16280,
      pct: 88.0,
      cacheHit: false,
    },
    {
      id: '4',
      time: '1m ago',
      tool: 'get_repo_map_tool',
      action: 'Ranked PageRank architecture map within 2,000 token budget',
      originalTokens: 42000,
      savedTokens: 40000,
      pct: 95.2,
      cacheHit: true,
    },
  ];

  const [events, setEvents] = useState<LogEvent[]>(initialEvents);

  const getToolIcon = (tool: string) => {
    switch (tool) {
      case 'read_file_smart':
        return <FileCode className="w-4 h-4 text-emerald-400" />;
      case 'tool_get_code_skeleton':
        return <Zap className="w-4 h-4 text-cyan-400" />;
      case 'run_command_smart':
      case 'filter_output':
        return <Terminal className="w-4 h-4 text-amber-400" />;
      case 'find_symbol_global':
        return <Search className="w-4 h-4 text-purple-400" />;
      case 'get_repo_map_tool':
        return <MapPin className="w-4 h-4 text-teal-400" />;
      default:
        return <Activity className="w-4 h-4 text-brand-400" />;
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-2.5">
          <Activity className="w-5 h-5 text-brand-400 animate-pulse" />
          <h2 className="text-base font-bold text-white tracking-tight">
            {t.streamHeader}
          </h2>
        </div>
        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-surface-800 text-slate-300 border border-surface-700">
          Live Interceptor
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-6">
        {t.streamDesc}
      </p>

      <div className="space-y-3 font-mono">
        {events.map((ev) => (
          <div
            key={ev.id}
            className="p-3.5 rounded-xl bg-surface-900/90 border border-surface-700/60 hover:border-brand-500/30 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-surface-800 border border-surface-700/80">
                {getToolIcon(ev.tool)}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-brand-300 font-mono">
                    {ev.tool}
                  </span>
                  {ev.cacheHit && (
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      L2 CACHE HIT
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-[11px] font-sans mt-0.5">
                  {ev.action}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 self-end sm:self-auto">
              <div className="text-right">
                <span className="font-bold text-brand-400 text-xs">
                  +{ev.savedTokens.toLocaleString()} saved
                </span>
                <span className="text-[10px] text-slate-500 block">
                  ({ev.pct}% cut)
                </span>
              </div>
              <span className="text-[10px] text-slate-500 flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>{ev.time}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
