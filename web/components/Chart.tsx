"use client";
import { useMemo, useState } from "react";

type Pt = [string, number];
type Band = { from: number; to: number; color: string };
const t = (d: string) => new Date(d.length === 7 ? d + "-01" : d).getTime();

export function Chart({ data, trend, recessions = [], bands = [], fixedY, height = 260, color = "#38bdf8", unit = "", digits = 2 }: {
  data: Pt[]; trend?: number[]; recessions?: [string, string][]; bands?: Band[]; fixedY?: [number, number];
  height?: number; color?: string; unit?: string; digits?: number;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 800, H = height, L = 48, R = 12, T = 12, B = 24;
  const g = useMemo(() => {
    if (data.length < 2) return null;
    const xs = data.map((d) => t(d[0])), x0 = xs[0], x1 = xs[xs.length - 1];
    const ys = data.map((d) => d[1]).concat(trend ?? []);
    let lo = fixedY ? fixedY[0] : Math.min(...ys), hi = fixedY ? fixedY[1] : Math.max(...ys);
    if (!fixedY) { const pad = (hi - lo || 1) * 0.06; lo -= pad; hi += pad; }
    const X = (v: number) => L + ((v - x0) / (x1 - x0 || 1)) * (W - L - R);
    const Y = (v: number) => T + (1 - (v - lo) / (hi - lo || 1)) * (H - T - B);
    return { xs, x0, x1, lo, hi, X, Y };
  }, [data, trend, fixedY, H]);
  if (!g) return <p className="text-sm text-slate-500">Histórico insuficiente para o gráfico.</p>;
  const path = (vals: number[]) => vals.map((v, i) => `${i ? "L" : "M"}${g.X(g.xs[i]).toFixed(1)},${g.Y(v).toFixed(1)}`).join("");
  const yTicks = Array.from({ length: 5 }, (_, i) => g.lo + ((g.hi - g.lo) * i) / 4);
  const yearStep = Math.max(1, Math.round((new Date(g.x1).getFullYear() - new Date(g.x0).getFullYear()) / 7));
  const startY = new Date(g.x0).getFullYear() + 1;
  const xTicks: number[] = [];
  for (let y = startY; y <= new Date(g.x1).getFullYear(); y += yearStep) xTicks.push(y);
  const fmt = (v: number) => v.toLocaleString("pt-BR", { maximumFractionDigits: digits });
  const h = hover !== null ? data[hover] : null;
  return (
    <div className="relative">
      {h && (
        <div className="pointer-events-none absolute right-2 top-0 z-10 rounded bg-slate-800 px-2 py-1 text-xs shadow">
          {h[0].slice(0, 7)}: <b>{fmt(h[1])}</b> {unit}
        </div>
      )}
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full touch-none select-none"
        onPointerMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          const px = ((e.clientX - r.left) / r.width) * W;
          const target = g.x0 + ((px - L) / (W - L - R)) * (g.x1 - g.x0);
          let best = 0, d = Infinity;
          g.xs.forEach((x, i) => { const dd = Math.abs(x - target); if (dd < d) { d = dd; best = i; } });
          setHover(best);
        }} onPointerLeave={() => setHover(null)}>
        {recessions.map(([a, b], i) => {
          const s = Math.max(t(a), g.x0), e = Math.min(t(b), g.x1);
          return e > s ? <rect key={i} x={g.X(s)} y={T} width={Math.max(1.5, g.X(e) - g.X(s))} height={H - T - B} fill="#94a3b8" opacity="0.18" /> : null;
        })}
        {bands.map((b, i) => <rect key={i} x={L} width={W - L - R} y={g.Y(Math.min(g.hi, b.to))} height={Math.max(0, g.Y(Math.max(g.lo, b.from)) - g.Y(Math.min(g.hi, b.to)))} fill={b.color} opacity="0.12" />)}
        {yTicks.map((v, i) => (
          <g key={i}><line x1={L} x2={W - R} y1={g.Y(v)} y2={g.Y(v)} stroke="#1e293b" /><text x={L - 6} y={g.Y(v) + 3} textAnchor="end" fontSize="10" fill="#64748b">{fmt(v)}</text></g>
        ))}
        {xTicks.map((y) => <text key={y} x={g.X(new Date(y, 0, 1).getTime())} y={H - 6} textAnchor="middle" fontSize="10" fill="#64748b">{y}</text>)}
        {trend && <path d={path(trend)} fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="5 3" />}
        <path d={path(data.map((d) => d[1]))} fill="none" stroke={color} strokeWidth="1.8" />
        <circle cx={g.X(g.xs[g.xs.length - 1])} cy={g.Y(data[data.length - 1][1])} r="3.5" fill={color} />
        {hover !== null && <g><line x1={g.X(g.xs[hover])} x2={g.X(g.xs[hover])} y1={T} y2={H - B} stroke="#475569" /><circle cx={g.X(g.xs[hover])} cy={g.Y(data[hover][1])} r="4" fill="#fff" /></g>}
      </svg>
    </div>
  );
}
