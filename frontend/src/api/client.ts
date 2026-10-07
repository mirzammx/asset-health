const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Status = "normal" | "degrading" | "attention" | "unknown";

export interface AssetSummary {
  id: string; name: string; type: string; area: string;
  health_index: number | null; status: Status; as_of: string | null;
  trend: (number | null)[];
}
export interface Summary {
  asset_count: number; avg_health: number | null; status_counts: Record<Status, number>;
}
export interface SensorInfo {
  tag: string; kind: string; unit: string; baseline: number; alarm_limit: number;
  level: number | null; score: number | null; status: Status;
}
export interface AssetDetail {
  id: string; name: string; type: string; site: string; area: string;
  health_index: number | null; status: Status; as_of: string | null; sensors: SensorInfo[];
}
export interface Point { t: string; value: number | null; quality: string }
export interface HealthPoint { t: string; health_index: number | null }

async function get<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const fetchAssets = () => get<AssetSummary[]>("/assets");
export const fetchSummary = () => get<Summary>("/summary");
export const fetchAsset = (id: string) => get<AssetDetail>(`/assets/${id}`);
export const fetchHealthHistory = (id: string) => get<HealthPoint[]>(`/assets/${id}/health/history?days=14`);
export const fetchSeries = (id: string, tag: string) =>
  get<Point[]>(`/assets/${id}/timeseries?tag=${encodeURIComponent(tag)}&hours=240&interval_minutes=30`);
