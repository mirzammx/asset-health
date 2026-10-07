import { ArrowLeft } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchAsset, fetchHealthHistory, fetchSeries, type SensorInfo } from "@/api/client";
import { HealthRing } from "@/components/HealthRing";
import { StatusBadge } from "@/components/StatusBadge";
import { TrendChart } from "@/components/TrendChart";
import { usePolling } from "@/hooks/usePolling";
import { STATUS_HEX, STATUS_TEXT } from "@/lib/status";

const KIND_LABEL: Record<string, string> = {
  vibration: "Vibration", temperature: "Temperature", pressure: "Pressure", current: "Current / power",
};

function SensorCard({ assetId, s }: { assetId: string; s: SensorInfo }) {
  const series = usePolling(() => fetchSeries(assetId, s.tag), [assetId, s.tag], 60000);
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{KIND_LABEL[s.kind] ?? s.kind}</CardTitle>
            <CardDescription className="break-all">{s.tag}</CardDescription>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-semibold ${STATUS_TEXT[s.status]}`}>
              {s.level != null ? s.level.toFixed(1) : "—"} <span className="text-sm font-normal text-muted-foreground">{s.unit}</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {s.score != null ? `sensor health ${Math.round(s.score)}%` : "no good data"} · alarm {s.alarm_limit} {s.unit}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {series.data
          ? <TrendChart data={series.data} unit={s.unit} alarmLimit={s.alarm_limit} baseline={s.baseline} />
          : <div className="h-[220px]" />}
      </CardContent>
    </Card>
  );
}

export function AssetDetail({ id }: { id: string }) {
  const asset = usePolling(() => fetchAsset(id), [id]);
  const history = usePolling(() => fetchHealthHistory(id), [id], 60000);
  const a = asset.data;

  if (asset.error) return <p className="text-bad">Could not load asset: {asset.error}</p>;
  if (!a) return <p className="text-muted-foreground">Loading…</p>;

  const historyPoints = (history.data ?? []).map((p) => ({ t: p.t, value: p.health_index, quality: "good" }));

  return (
    <div className="space-y-6">
      <a href="#/assets" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> All assets
      </a>
      <div className="flex items-center gap-5">
        <HealthRing value={a.health_index} status={a.status} size={112} />
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{a.name}</h1>
            <StatusBadge status={a.status} />
          </div>
          <p className="capitalize text-muted-foreground">{a.type} · {a.site} / {a.area}</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Health index</CardTitle>
          <CardDescription>Last 14 days. Below 75 is degrading, below 50 needs attention.</CardDescription>
        </CardHeader>
        <CardContent>
          {historyPoints.length > 0 && (
            <TrendChart data={historyPoints} unit="%" alarmLimit={50} baseline={100} color={STATUS_HEX[a.status]} yDomain={[0, 100]} />
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        {a.sensors.map((s) => <SensorCard key={s.tag} assetId={a.id} s={s} />)}
      </div>
    </div>
  );
}
