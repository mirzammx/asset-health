import type { Status } from "@/api/client";
import { STATUS_HEX } from "@/lib/status";

export function HealthRing({ value, status, size = 96 }: { value: number | null; status: Status; size?: number }) {
  const stroke = Math.max(6, size / 10);
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = value === null ? 0 : Math.min(Math.max(value, 0), 100);
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="currentColor" className="text-muted" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={STATUS_HEX[status]} strokeWidth={stroke}
                strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
                style={{ transition: "stroke-dashoffset .6s" }} />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-semibold" style={{ fontSize: size / 4 }}>
        {value === null ? "—" : `${Math.round(value)}%`}
      </div>
    </div>
  );
}
