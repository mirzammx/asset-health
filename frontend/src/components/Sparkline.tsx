/** Tiny trend line for 0-100 health values. Null gaps are skipped. */
export function Sparkline({ values, color, height = 40 }: { values: (number | null)[]; color: string; height?: number }) {
  const pts = values.filter((v): v is number => v !== null);
  if (pts.length < 2) return <div style={{ height }} />;
  const w = 200;
  const x = (i: number) => (i / (pts.length - 1)) * w;
  const y = (v: number) => height - 4 - (Math.min(Math.max(v, 0), 100) / 100) * (height - 8);
  const line = pts.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${height}`} width="100%" height={height} preserveAspectRatio="none">
      <polyline points={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      <circle cx={x(pts.length - 1)} cy={y(pts[pts.length - 1])} r={3} fill={color} />
    </svg>
  );
}
