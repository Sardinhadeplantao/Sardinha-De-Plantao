"use client";
import { useEffect, useMemo, useState } from "react";
import { Chart } from "./Chart";
import type { Indicator } from "@/lib/data";
import { loadFullIndicators } from "@/lib/full-data";
import { bases, reading } from "@/lib/reading";

const PERIODS: [string, number | null][] = [["5 anos", 5], ["10 anos", 10], ["25 anos", 25], ["Tudo", null]];
const BADGE = { ok: "bg-emerald-900 text-emerald-300", atrasado: "bg-amber-900 text-amber-300", obsoleto: "bg-red-900 text-red-300" };
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const fmt = (v: number, d = 2) => v.toLocaleString("pt-BR", { maximumFractionDigits: d });

export function DetailModal({ ind: slimInd, recessions, onClose }: { ind: Indicator; recessions: [string, string][]; onClose: () => void }) {
  const [ind, setInd] = useState<Indicator>(slimInd);
  const [loading, setLoading] = useState(true);
  const [basisIdx, setBasisIdx] = useState(0);
  const [period, setPeriod] = useState<number | null>(25);
  const [showTrend, setShowTrend] = useState(true);
  const [showBands, setShowBands] = useState(true);
  const [showRec, setShowRec] = useState(true);

  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);

  useEffect(() => {
    let alive = true;
    loadFullIndicators(BASE).then((all) => {
      const found = all?.find((x) => x.id === slimInd.id);
      if (alive) { if (found) setInd(found); setLoading(false); }
    });
    return () => { alive = false; };
  }, [slimInd.id]);

  const options = bases(ind);
  const basis = options[Math.min(basisIdx, options.length - 1)];
  const isView = !!basis && basis.label !== "Nível" && !!ind.view;
  const series = useMemo(() => (isView ? { h: ind.view!.history, t: ind.view!.trend } : { h: ind.history, t: ind.trend }), [ind, isView]);

  const view = useMemo(() => {
    const h = series.h;
    if (!h.length) return { data: [] as [string, number][], trend: [] as number[] };
    const last = new Date(h[h.length - 1][0]);
    const cut = period ? new Date(last).setFullYear(last.getFullYear() - period) : 0;
    const idx = h.map((p, i) => (new Date(p[0]).getTime() >= cut ? i : -1)).filter((i) => i >= 0);
    return { data: idx.map((i) => h[i]), trend: series.t.length === h.length ? idx.map((i) => series.t[i]) : [] };
  }, [series, period]);

  const bands = useMemo(() => {
    const v = series.h.map((p) => p[1]).sort((a, b) => a - b);
    if (v.length < 10) return [];
    const q = (p: number) => v[Math.min(v.length - 1, Math.floor((p / 100) * v.length))];
    const [p10, p33, p67, p90] = [q(10), q(33), q(67), q(90)];
    return [
      { from: -Infinity, to: p10, color: "#3b82f6" }, { from: p10, to: p33, color: "#60a5fa" },
      { from: p67, to: p90, color: "#f59e0b" }, { from: p90, to: Infinity, color: "#ef4444" },
    ];
  }, [series]);

  const s = basis?.stats;
  const stats: [string, string][] = s && basis ? [
    ["Atual", fmt(basis.value)], ["Há 1 ano", s.year_ago !== null ? fmt(s.year_ago) : "—"], ["Há 5 anos", s.five_years_ago !== null ? fmt(s.five_years_ago) : "—"],
    [`Máxima (${s.ath.date.slice(0, 4)})`, fmt(s.ath.value)], [`Mínima (${s.atl.date.slice(0, 4)})`, fmt(s.atl.value)], ["Média histórica", fmt(s.mean)],
    ["Percentil", `${fmt(s.percentile, 0)} (${s.zone})`], ["Z-score", fmt(s.zscore)],
  ] : [];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-3 sm:p-8" onClick={onClose} role="dialog" aria-modal="true" aria-label={ind.name}>
      <div className="w-full max-w-4xl rounded-xl border border-slate-700 bg-slate-950 p-4 sm:p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">{ind.name}</h2>
            <p className="text-xs text-slate-400">{ind.source.toUpperCase()} · {ind.frequency} · série {ind.code} · referência {ind.ref_date} · coletado em {ind.as_of?.slice(0, 10)}</p>
          </div>
          <div className="flex items-center gap-2">
            {ind.status && <span className={`rounded px-2 py-0.5 text-xs ${BADGE[ind.status]}`}>{ind.status}</span>}
            <button onClick={onClose} aria-label="Fechar" className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800">Fechar</button>
          </div>
        </div>

        {options.length > 1 && (
          <div className="mt-4 inline-flex rounded-lg border border-slate-700 p-1 text-xs">
            {options.map((o, k) => (
              <button key={o.label} onClick={() => setBasisIdx(k)} className={`rounded px-3 py-1 ${basis?.label === o.label ? "bg-sky-900 text-sky-200" : "text-slate-300"}`}>{o.label}</button>
            ))}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          {PERIODS.map(([label, y]) => (
            <button key={label} onClick={() => setPeriod(y)} className={`rounded border px-2 py-1 ${period === y ? "border-sky-500 bg-sky-950 text-sky-300" : "border-slate-700 text-slate-300"}`}>{label}</button>
          ))}
          <label className="ml-2 flex items-center gap-1"><input type="checkbox" checked={showTrend} onChange={(e) => setShowTrend(e.target.checked)} />Tendência (HP)</label>
          <label className="flex items-center gap-1"><input type="checkbox" checked={showBands} onChange={(e) => setShowBands(e.target.checked)} />Faixas de percentil</label>
          <label className="flex items-center gap-1"><input type="checkbox" checked={showRec} onChange={(e) => setShowRec(e.target.checked)} />Recessões (NBER)</label>
        </div>
        <div className="mt-2">
          {loading && <p className="mb-1 text-xs text-slate-500">Carregando o histórico completo…</p>}
          <Chart data={view.data} trend={showTrend && view.trend.length ? view.trend : undefined} recessions={showRec ? recessions : []}
            bands={showBands ? bands : []} unit={basis?.unit ?? ""} label={`${ind.name} — ${basis?.label ?? ""}`} />
          {showBands && <p className="mt-1 text-[11px] text-slate-500">Faixas: azul = abaixo do percentil 33 da própria história; laranja/vermelho = acima do percentil 67/90. Sombra cinza = recessão dos EUA. Linha tracejada = tendência HP.</p>}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {stats.map(([k, v]) => (<div key={k} className="rounded border border-slate-800 bg-slate-900 p-2"><div className="text-[11px] text-slate-400">{k}</div><div className="text-sm font-semibold">{v}</div></div>))}
        </div>

        {s && (
          <div className="mt-4">
            <div className="mb-1 text-xs text-slate-400">Posição na história — {basis!.label.toLowerCase()} (percentil {fmt(s.percentile, 0)})</div>
            <div className="relative h-3 overflow-hidden rounded bg-gradient-to-r from-sky-800 via-slate-700 to-red-800">
              <div className="absolute top-0 h-3 w-1 bg-white" style={{ left: `calc(${s.percentile}% - 2px)` }} />
            </div>
            <div className="mt-1 flex justify-between text-[10px] text-slate-500"><span>mínima histórica</span><span>mediana</span><span>máxima histórica</span></div>
          </div>
        )}

        <div className="mt-4 space-y-2 text-sm text-slate-200">
          <h3 className="text-base font-semibold">Leitura</h3>
          {reading(ind, basis).map((p, k) => <p key={k}>{p}</p>)}
          {ind.note && <p className="rounded border border-sky-900 bg-sky-950/40 p-2 text-sky-200"><b>Como é calculado:</b> {ind.note}</p>}
          <p className="text-slate-400"><b>Por que importa:</b> {ind.rationale}</p>
        </div>
        <p className="mt-3 text-xs text-slate-500">Descrição estatística dos dados públicos, não é recomendação de investimento.
          {ind.source_url && <> Fonte: <a className="underline" href={ind.source_url} target="_blank" rel="noreferrer">{ind.code}</a>.</>}</p>
      </div>
    </div>
  );
}
