import React, { useState } from 'react';
import { 
  Zap, 
  Sparkles, 
  ArrowRight, 
  FileCode, 
  Shield, 
  Terminal, 
  Database, 
  Copy, 
  Check, 
  RotateCcw 
} from 'lucide-react';
import { Language } from '../types';

interface Preset {
  id: string;
  nameEn: string;
  nameTr: string;
  type: string;
  icon: React.ReactNode;
  input: string;
  output: string;
  originalTokens: number;
  compressedTokens: number;
}

const PRESETS: Preset[] = [
  {
    id: 'python_skeleton',
    nameEn: 'Python Class (AST Skeleton)',
    nameTr: 'Python Sınıfı (AST İskeleti)',
    type: 'Code Skeletonizer',
    icon: <FileCode className="w-4 h-4 text-emerald-400" />,
    input: `class AuthenticationService:
    """Enterprise authentication and OAuth2 token handling service."""
    
    def __init__(self, db_client: DatabaseClient, secret_key: str):
        self.db = db_client
        self.secret = secret_key
        self.session_cache = {}
        self._max_retries = 3

    def generate_jwt(self, user_id: str, scopes: list[str]) -> str:
        """Issue signed JWT bearer token with expiration claims."""
        # Detailed 80 lines of payload construction, signature hashing,
        # salt rotation, encryption headers and HMAC-SHA256 crypto...
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": user_id, "scopes": scopes, "exp": 1750000000}
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    def verify_token(self, token: str) -> dict[str, Any]:
        """Validate token signature, revocation list, and claims."""
        # 120 lines of database lookups, blacklist verification,
        # cache invalidation, key rotation and telemetry reporting...
        return {"user_id": "usr_99", "active": True}`,
    output: `class AuthenticationService:
    """Enterprise authentication and OAuth2 token handling service."""

    def __init__(self, db_client: DatabaseClient, secret_key: str): ...

    def generate_jwt(self, user_id: str, scopes: list[str]) -> str:
        """Issue signed JWT bearer token with expiration claims."""
        ...

    def verify_token(self, token: str) -> dict[str, Any]:
        """Validate token signature, revocation list, and claims."""
        ...`,
    originalTokens: 1850,
    compressedTokens: 142,
  },
  {
    id: 'lockfile_shield',
    nameEn: 'NPM package-lock.json',
    nameTr: 'NPM Kilit Dosyası (5,000 Satır)',
    type: 'Lockfile Shield',
    icon: <Shield className="w-4 h-4 text-cyan-400" />,
    input: `{\n  "name": "enterprise-app",\n  "version": "1.0.0",\n  "lockfileVersion": 3,\n  "packages": {\n    "": {\n      "dependencies": { "react": "^18.3.1", "express": "^4.19.2" }\n    },\n    "node_modules/react": {\n      "version": "18.3.1",\n      "resolved": "https://registry.npmjs.org/react/-/react-18.3.1.tgz",\n      "integrity": "sha512-...",\n      "dependencies": { "loose-envify": "^1.1.0" }\n    },\n    "// ... 4,800 more repetitive dependency metadata rows ...": {}\n  }\n}`,
    output: `[TOKENJAR SHIELD: package-lock.json summary]
Direct Dependencies (Top-level):
- react: 18.3.1
- express: 4.19.2

Total Packages in Tree: 1,428 resolved
Lockfile Version: 3
Integrity Hashes: Verified`,
    originalTokens: 24500,
    compressedTokens: 98,
  },
  {
    id: 'test_pruner',
    nameEn: 'Pytest Verbose Output',
    nameTr: 'Pytest Terminal Çıktısı (300 Log)',
    type: 'Terminal Pruner',
    icon: <Terminal className="w-4 h-4 text-amber-400" />,
    input: `============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.3.0
rootdir: C:\\Project\\App
collected 68 items

tests\\test_auth.py .................................................... [ 76%]
tests\\test_db.py ............                                          [ 94%]
tests\\test_api.py ....                                                 [100%]
------------------------------- live log session -------------------------------
DEBUG: Connection pool created for postgresql://app_user@db.internal:5432
INFO: Handshake completed with worker 1
DEBUG: Query executed: SELECT 1 (0.4ms)
... [250 repetitive passing debug logs pruned] ...
============================== 68 passed in 1.45s ==============================`,
    output: `[TOKENJAR OUTPUT PRUNER: Cleaned Test Summary]
============================= test session starts =============================
collected 68 items: 68 PASSED (0 failures, 0 errors, 0 warnings)
Finished in 1.45s`,
    originalTokens: 8200,
    compressedTokens: 110,
  },
  {
    id: 'sql_squeezer',
    nameEn: 'SQL Tabular Dump (10,000 Rows)',
    nameTr: 'SQL Veritabanı Dökümü (10.000 Satır)',
    type: 'V2 SQL Squeezer',
    icon: <Database className="w-4 h-4 text-indigo-400" />,
    input: `[
  {"id": 1, "username": "alice", "email": "alice@corp.com", "role": "admin", "created_at": "2026-01-01"},
  {"id": 2, "username": "bob", "email": "bob@corp.com", "role": "member", "created_at": "2026-01-02"},
  {"id": 3, "username": "charlie", "email": "charlie@corp.com", "role": "member", "created_at": "2026-01-03"},
  {"id": 4, "username": "david", "email": "david@corp.com", "role": "developer", "created_at": "2026-01-04"},
  {"id": 5, "username": "eve", "email": "eve@corp.com", "role": "auditor", "created_at": "2026-01-05"},
  ... [9,995 more JSON rows omitted by user query] ...
]`,
    output: `| id | username | email | role | created_at |
|:---|:---|:---|:---|:---|
| 1 | alice | alice@corp.com | admin | 2026-01-01 |
| 2 | bob | bob@corp.com | member | 2026-01-02 |
| 3 | charlie | charlie@corp.com | member | 2026-01-03 |
| 4 | david | david@corp.com | developer | 2026-01-04 |
| 5 | eve | eve@corp.com | auditor | 2026-01-05 |

[TOKENJAR V2 SQL SQUEEZER SUMMARY]
Total Dataset: 10,000 rows
Columns: id (INT), username (STR), email (STR), role (ENUM), created_at (TIMESTAMP)
Distribution: 42% member, 28% developer, 18% auditor, 12% admin`,
    originalTokens: 185000,
    compressedTokens: 240,
  },
];

export const PlaygroundTab: React.FC<{ lang: Language }> = ({ lang }) => {
  const [selectedId, setSelectedId] = useState<string>('python_skeleton');
  const [copied, setCopied] = useState<boolean>(false);

  const activePreset = PRESETS.find((p) => p.id === selectedId) || PRESETS[0];
  const savingsPct = Math.round(
    ((activePreset.originalTokens - activePreset.compressedTokens) /
      activePreset.originalTokens) *
      100
  );

  const handleCopy = () => {
    navigator.clipboard.writeText(activePreset.output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <Sparkles className="w-5 h-5 text-brand-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">
                {lang === 'tr' ? 'İnteraktif Token Sıkıştırma Laboratuvarı' : 'Interactive Compression Lab'}
              </h2>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/30">
                Live Simulator
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              {lang === 'tr'
                ? 'Farklı dosya ve komut tiplerini TokenJar motorunun nasıl sıkıştırdığını canlı test edin. Kod tabanınızın bağlam penceresini nasıl koruduğunu anında görün.'
                : 'Test how TokenJar compresses different file types and command outputs in real-time. Experience how context compaction is prevented.'}
            </p>
          </div>

          {/* Savings Metric Pill */}
          <div className="p-3.5 rounded-xl bg-surface-900 border border-brand-500/30 flex items-center space-x-3 shadow-lg">
            <div className="h-9 w-9 rounded-xl bg-brand-500/20 flex items-center justify-center text-brand-400">
              <Zap className="w-5 h-5 fill-brand-400" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-mono text-slate-400 font-bold block">
                {lang === 'tr' ? 'Tasarruf Oranı' : 'Token Reduction'}
              </span>
              <span className="text-lg font-extrabold font-mono text-brand-400">
                -{savingsPct}%
              </span>
            </div>
          </div>
        </div>

        {/* Preset Selector Buttons */}
        <div className="flex items-center gap-2 mt-6 flex-wrap">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => setSelectedId(preset.id)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                selectedId === preset.id
                  ? 'bg-brand-500 text-surface-950 shadow-md font-extrabold'
                  : 'bg-surface-850 hover:bg-surface-800 text-slate-300 border border-surface-700/80'
              }`}
            >
              {preset.icon}
              <span>{lang === 'tr' ? preset.nameTr : preset.nameEn}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Side-by-Side Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Raw Original */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between border-rose-500/20">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-surface-800">
              <div className="flex items-center space-x-2">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  {lang === 'tr' ? 'Standart Okuma (Ham Yük)' : 'Standard Read (Raw Payload)'}
                </h3>
              </div>
              <span className="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-lg border border-rose-500/20">
                {activePreset.originalTokens.toLocaleString()} tokens
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-950 border border-surface-800 font-mono text-xs text-slate-400 overflow-x-auto max-h-[360px] custom-scrollbar whitespace-pre">
              {activePreset.input}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-surface-800/80 text-[11px] text-slate-500 flex items-center justify-between">
            <span>{lang === 'tr' ? 'Bağlam maliyeti: Yüksek' : 'Context Cost: Expensive'}</span>
            <span className="text-rose-400 font-semibold">{lang === 'tr' ? 'Bağlam penceresini doldurur' : 'Causes Context Compaction'}</span>
          </div>
        </div>

        {/* Right: TokenJar Compressed */}
        <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between border-brand-500/35 shadow-xl shadow-brand-500/5">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-surface-800">
              <div className="flex items-center space-x-2">
                <span className="h-2.5 w-2.5 rounded-full bg-brand-400 animate-pulse" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-brand-300">
                  {lang === 'tr' ? 'TokenJar Optimize Çıktı' : 'TokenJar Optimized Output'}
                </h3>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold text-brand-400 bg-brand-500/15 px-2 py-0.5 rounded-lg border border-brand-500/30">
                  {activePreset.compressedTokens.toLocaleString()} tokens
                </span>
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg bg-surface-800 hover:bg-surface-700 text-slate-300 hover:text-white transition-colors border border-surface-700"
                  title="Copy Output"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-brand-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-950 border border-brand-500/25 font-mono text-xs text-brand-200/90 overflow-x-auto max-h-[360px] custom-scrollbar whitespace-pre">
              {activePreset.output}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-surface-800/80 text-[11px] flex items-center justify-between">
            <span className="text-slate-400">{lang === 'tr' ? 'Kazanılan Tasarruf:' : 'Net Preserved Tokens:'}</span>
            <span className="text-brand-400 font-mono font-bold">
              +{(activePreset.originalTokens - activePreset.compressedTokens).toLocaleString()} tokens (-{savingsPct}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
