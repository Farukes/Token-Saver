import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { NavigationTabs, TabType } from './components/NavigationTabs';
import { MetricCards } from './components/MetricCards';
import { CategoryBreakdown } from './components/CategoryBreakdown';
import { IdeIntegrationGrid } from './components/IdeIntegrationGrid';
import { RulesConfigManager } from './components/RulesConfigManager';
import { GatewayPreview } from './components/GatewayPreview';
import { LiveEventStream } from './components/LiveEventStream';
import { PlaygroundTab } from './components/PlaygroundTab';
import { SystemStatus, Language, ConfigData } from './types';
import { translations } from './i18n';
import { ShieldCheck, Github, Lock, Sparkles, Activity } from 'lucide-react';

const defaultStatus: SystemStatus = {
  version: "1.0.1",
  active: true,
  overall_status: "ACTIVE",
  telemetry: {
    total_saved: 1245890,
    total_processed: 1358000,
    savings_pct: 91.7,
    dollars_saved: 3.74,
    categories: {
      skeleton: {
        name: "AST Skeletonizer",
        saved: 420800,
        count: 148,
        pct: 94.2,
        unit: "files",
        icon: "🦴",
      },
      cache: {
        name: "Smart File Cache",
        saved: 312400,
        count: 285,
        pct: 96.5,
        unit: "reads",
        icon: "⚡",
      },
      command: {
        name: "Terminal Pruner",
        saved: 245100,
        count: 92,
        pct: 88.4,
        unit: "runs",
        icon: "✂️",
      },
      lockfile: {
        name: "Lockfile Shield",
        saved: 168200,
        count: 24,
        pct: 99.1,
        unit: "shields",
        icon: "🛡️",
      },
      repo_map: {
        name: "Repo Map Engine",
        saved: 64200,
        count: 18,
        pct: 95.0,
        unit: "maps",
        icon: "🗺️",
      },
      symbol_search: {
        name: "Global Symbol Search",
        saved: 35190,
        count: 56,
        pct: 85.3,
        unit: "searches",
        icon: "🔍",
      },
    },
    l2_cache: {
      disk_bytes: 3840210,
      disk_mb: 3.66,
      entries: 342,
      warning: false,
    },
  },
  ides: [
    {
      name: "Antigravity (AGY)",
      installed: true,
      active: true,
      path: "C:\\Users\\omere\\.gemini\\antigravity-cli\\mcp_config.json",
    },
    {
      name: "Claude Desktop",
      installed: true,
      active: true,
      path: "C:\\Users\\omere\\AppData\\Roaming\\Claude\\claude_desktop_config.json",
    },
    {
      name: "Cursor",
      installed: true,
      active: true,
      path: "C:\\Users\\omere\\.cursor\\mcp.json",
    },
    {
      name: "Windsurf",
      installed: true,
      active: true,
      path: "C:\\Users\\omere\\.codeium\\windsurf\\mcp_config.json",
    },
    {
      name: "Claude Code",
      installed: true,
      active: true,
      path: "C:\\Users\\omere\\.claude.json",
    },
    {
      name: "Continue.dev",
      installed: true,
      active: false,
      path: "C:\\Users\\omere\\.continue\\config.json",
    },
  ],
  rules: {
    installed: true,
    compact_output: true,
  },
  config: {
    lockfile_shield: true,
    compact_output: true,
    prevent_truncation: true,
  },
};

export const App: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus>(defaultStatus);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [lang, setLang] = useState<Language>('tr');
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isClearingCache, setIsClearingCache] = useState<boolean>(false);
  const [isResettingStats, setIsResettingStats] = useState<boolean>(false);
  const [toast, setToast] = useState<string | null>(null);

  const t = translations[lang];

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/status', { cache: 'no-store' });
      if (res.ok) {
        const data: SystemStatus = await res.json();
        setStatus(data);
        setIsLive(true);
      } else {
        setIsLive(false);
      }
    } catch {
      setIsLive(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleToggleLang = () => {
    setLang((prev) => (prev === 'en' ? 'tr' : 'en'));
  };

  const handleClearCache = async () => {
    try {
      setIsClearingCache(true);
      const res = await fetch('/api/cache/clear', { method: 'POST' });
      if (res.ok) {
        showToast(t.cacheCleared);
        await fetchStatus();
      }
    } catch {
      showToast(t.cacheCleared);
    } finally {
      setIsClearingCache(false);
    }
  };

  const handleResetStats = async () => {
    try {
      setIsResettingStats(true);
      const res = await fetch('/api/stats/reset', { method: 'POST' });
      if (res.ok) {
        showToast(t.statsReset);
        await fetchStatus();
      }
    } catch {
      showToast(t.statsReset);
    } finally {
      setIsResettingStats(false);
    }
  };

  const handleToggleIde = async (ideName: string) => {
    setStatus((prev) => ({
      ...prev,
      ides: prev.ides.map((ide) =>
        ide.name === ideName ? { ...ide, active: !ide.active } : ide
      ),
    }));

    try {
      await fetch('/api/ides/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ide: ideName }),
      });
      await fetchStatus();
    } catch {
      // In demo mode keep optimistic state
    }
  };

  const handleUpdateConfig = async (updated: Partial<ConfigData>) => {
    setStatus((prev) => ({
      ...prev,
      config: { ...prev.config, ...updated },
    }));

    try {
      await fetch('/api/config/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated),
      });
      await fetchStatus();
    } catch {
      // In demo mode keep optimistic state
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-surface-950 text-slate-100 selection:bg-brand-500 selection:text-white">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-xl bg-brand-500 text-surface-950 font-bold text-xs shadow-2xl flex items-center space-x-2 animate-bounce">
          <ShieldCheck className="w-4 h-4" />
          <span>{toast}</span>
        </div>
      )}

      {/* Header */}
      <Header
        lang={lang}
        onToggleLang={handleToggleLang}
        isLive={isLive}
        version={status.version}
        onRefresh={fetchStatus}
        onClearCache={handleClearCache}
        onResetStats={handleResetStats}
        isClearingCache={isClearingCache}
        isResettingStats={isResettingStats}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {/* Navigation Tabs */}
        <NavigationTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          lang={lang}
        />

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <div className="space-y-6 animate-fadeIn">
            {/* Metric Cards Row */}
            <MetricCards telemetry={status.telemetry} lang={lang} />

            {/* Compression Pipelines & IDE Quick Status */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7">
                <CategoryBreakdown categories={status.telemetry.categories} lang={lang} />
              </div>
              <div className="lg:col-span-5">
                <IdeIntegrationGrid
                  ides={status.ides}
                  lang={lang}
                  onToggleIde={handleToggleIde}
                />
              </div>
            </div>

            {/* Live Activity Stream */}
            <LiveEventStream lang={lang} />
          </div>
        )}

        {/* Tab 2: Interactive Playground */}
        {activeTab === 'playground' && (
          <div className="animate-fadeIn">
            <PlaygroundTab lang={lang} />
          </div>
        )}

        {/* Tab 3: IDE Matrix */}
        {activeTab === 'ides' && (
          <div className="space-y-6 animate-fadeIn">
            <IdeIntegrationGrid
              ides={status.ides}
              lang={lang}
              onToggleIde={handleToggleIde}
            />
          </div>
        )}

        {/* Tab 4: Optimization Policies */}
        {activeTab === 'rules' && (
          <div className="space-y-6 animate-fadeIn">
            <RulesConfigManager
              config={status.config}
              rules={status.rules}
              lang={lang}
              onUpdateConfig={handleUpdateConfig}
            />
          </div>
        )}

        {/* Tab 5: V2 Universal Gateway */}
        {activeTab === 'gateway' && (
          <div className="space-y-6 animate-fadeIn">
            <GatewayPreview lang={lang} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="glass-panel border-t border-surface-700/60 bg-surface-950/80 py-5 px-6 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-200">TokenJar</span>
            <span>&bull;</span>
            <span className="flex items-center space-x-1 text-brand-400 font-medium">
              <Lock className="w-3 h-3" />
              <span>Zero Telemetry &bull; 100% Local Processing</span>
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/Farukes/TokenJar"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white flex items-center space-x-1 transition-colors"
            >
              <Github className="w-4 h-4" />
              <span>GitHub</span>
            </a>
            <a
              href="https://pypi.org/project/tokenjar/"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors"
            >
              PyPI
            </a>
            <a
              href="https://crates.io/crates/tokenjar"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors"
            >
              Crates.io
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
