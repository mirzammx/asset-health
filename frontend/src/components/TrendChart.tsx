import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Point } from "@/api/client";

interface Props {
  data: Point[];
  unit: string;
  alarmLimit: number;
  baseline: number;
  color?: string;
  height?: number;
  yDomain?: [number, number]; // fixed axis range, e.g. [0, 100] for health
}

const fmtDay = (v: number) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export function TrendChart({ data, unit, alarmLimit, baseline, color = "#60a5fa", height = 220, yDomain }: Props) {
  const rows = data.map((p) => ({ ts: new Date(p.t).getTime(), value: p.value }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <XAxis dataKey="ts" type="number" scale="time" domain={["dataMin", "dataMax"]} tickFormatter={fmtDay}
               tickLine={false} axisLine={false} stroke="#737373" fontSize={12} minTickGap={40} />
        <YAxis width={44} tickLine={false} axisLine={false} stroke="#737373" fontSize={12}
               ticks={yDomain ? [0, 25, 50, 75, 100] : undefined}
               domain={yDomain ?? [
                 (min: number) => Math.floor(Math.min(min, baseline) * 0.9),
                 (max: number) => Math.ceil(Math.max(max, alarmLimit) * 1.05),
               ]} />
        <Tooltip contentStyle={{ background: "#1c1c1c", border: "1px solid #333", borderRadius: 8 }}
                 labelFormatter={(v) => new Date(v as number).toLocaleString()}
                 formatter={(v: number) => [`${v.toFixed(2)} ${unit}`, "Reading"]} />
        <ReferenceLine y={alarmLimit} stroke="#fb497a" strokeDasharray="4 4" />
        <Line dataKey="value" stroke={color} dot={false} strokeWidth={2} isAnimationActive={false} connectNulls={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
