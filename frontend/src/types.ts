export interface CategoryMetric {
  name: string;
  saved: number;
  count: number;
  pct: number;
  unit: string;
  icon: string;
}

export interface IdeInfo {
  name: string;
  installed: boolean;
  active: boolean;
  path: string;
}

export interface L2CacheInfo {
  disk_bytes: number;
  disk_mb: number;
  entries: number;
  warning: boolean;
}

export interface TelemetryData {
  total_saved: number;
  total_processed: number;
  savings_pct: number;
  dollars_saved: number;
  categories: Record<string, CategoryMetric>;
  l2_cache: L2CacheInfo;
}

export interface RulesData {
  installed: boolean;
  compact_output: boolean;
}

export interface ConfigData {
  lockfile_shield: boolean;
  compact_output: boolean;
  prevent_truncation: boolean;
}

export interface SystemStatus {
  version: string;
  active: boolean;
  overall_status: 'ACTIVE' | 'INACTIVE';
  telemetry: TelemetryData;
  ides: IdeInfo[];
  rules: RulesData;
  config: ConfigData;
}

export type Language = 'en' | 'tr';
