import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchAssets, fetchSummary } from "@/api/client";
import { HealthRing } from "@/components/HealthRing";
import { Sparkline } from "@/components/Sparkline";
import { StatusBadge } from "@/components/StatusBadge";
import { usePolling } from "@/hooks/usePolling";
import { STATUS_HEX } from "@/lib/status";

function Kpi({ title, value, sub, tone }: { title: string; value: string | number; sub: string; tone?: string }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{title}</CardDescription>
        <CardTitle className={`text-3xl ${tone ?? ""}`}>{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{sub}</CardContent>
    </Card>
  );
}

export function Overview() {
  const assets = usePolling(fetchAssets, []);
  const summary = usePolling(fetchSummary, []);
  const s = summary.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Fleet overview</h1>
        <p className="text-muted-foreground">Current condition of monitored equipment, refreshed automatically.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi title="Assets monitored" value={s?.asset_count ?? "—"} sub="Pumps, compressors, gearboxes, motors, wellheads" />
        <Kpi title="Average health" value={s?.avg_health != null ? `${Math.round(s.avg_health)}%` : "—"} sub="Across all assets" />
        <Kpi title="Degrading" value={s?.status_counts.degrading ?? "—"} sub="Plan maintenance" tone="text-warn" />
        <Kpi title="Needs attention" value={s?.status_counts.attention ?? "—"} sub="Act before failure" tone="text-bad" />
      </div>

      {assets.error && <p className="text-bad">Cannot reach API: {assets.error}</p>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(assets.data ?? []).map((a) => (
          <a key={a.id} href={`#/assets/${a.id}`} className="block rounded-xl transition hover:ring-1 hover:ring-foreground/20">
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-lg">{a.name}</CardTitle>
                    <CardDescription className="capitalize">{a.type} · {a.area}</CardDescription>
                  </div>
                  <StatusBadge status={a.status} />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-4">
                  <HealthRing value={a.health_index} status={a.status} />
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 text-xs text-muted-foreground">Health, last 14 days</div>
                    <Sparkline values={a.trend} color={STATUS_HEX[a.status]} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </a>
        ))}
        {!assets.data && !assets.error && <p className="text-muted-foreground">Loading…</p>}
      </div>
    </div>
  );
}
