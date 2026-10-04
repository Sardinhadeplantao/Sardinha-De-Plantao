"use client";
import { useMemo, useState } from "react";
import type { Analogs, Data, Index, Indicator, Mover, RecessionWatch } from "@/lib/data";
import { LENSES, SHORT, TONE, fmt, signed } from "@/lib/ui";

const card = "rounded-xl border border-slate-800 bg-slate-900 p-4";

/** Short-cycle recession signals. Each signal shows its rule; the state always has text, never color alone. */
export function RecessionWatchSection({ watch, indicators, onPick }: { watch: RecessionWatch | null; indicators: Indicator[]; onPick: (i: Indicator) => void }) {
  if (!watch || !watch.signals.length) return null;
  const level = watch.on >= 3 ? ["Vários sinais ligados", "text-red-300"] : watch.on >= 1 ? ["Sinais isolados", "text-amber-300"] : ["Nenhum sinal ligado", "text-emerald-300"];
  return (
    <section id="recessao" className="scroll-mt-24 mt-10">
      <h2 className="text-xl font-bold">Termômetro de recessão — ciclo curto</h2>
      <p className="text-sm text-slate-400">Sinais clássicos e públicos de recessão nos EUA, cada um com sua regra. As óticas olham décadas; estes olham os próximos 12 meses.</p>
      <div className={`${card} mt-3`}>
        <div className="flex flex-wrap items-baseline gap-3">
          <span className="text-3xl font-bold tabular-nums text-slate-100">{watch.on}<span className="text-base text-slate-500">/{watch.total}</span></span>
          <span className={`text-lg font-semibold ${level[1]}`}>{level[0]}</span>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {watch.signals.map((s) => {
            const ind = indicators.find((i) => i.id === s.id);
            const shown = s.signal_value !== null ? `${signed(s.signal_value, 1)}% vs. mínima` : `${fmt(s.value)} ${s.unit ?? ""}`;
            return (
              <button key={s.id} onClick={() => ind && onPick(ind)}
                className={`rounded-lg border p-3 text-left hover:bg-slate-800/60 ${s.triggered ? "border-red-800 bg-red-950/30" : "border-slate-800"}`}>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-medium text-slate-200">{s.name.replace(" (EUA)", "")}</span>
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] ring-1 ${s.triggered ? "bg-red-950 text-red-300 ring-red-800" : "bg-emerald-950 text-emerald-300 ring-emerald-800"}`}>
                    {s.triggered ? "● ligado" : "○ desligado"}
                  </span>
                </div>
                <div className="mt-1 text-lg font-bold tabular-nums text-slate-100">{shown}</div>
                <div className="text-[11px] text-slate-500">Regra: {s.rule} · dado de {s.ref_date}{s.status !== "ok" ? ` · ${s.status}` : ""}</div>
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-[11px] text-slate-500">
          Nenhum sinal sozinho é previsão: a curva invertida já errou o momento por anos, e a regra de Sahm costuma disparar quando a recessão já começou.
          Vários sinais ao mesmo tempo merecem mais atenção.
        </p>
      </div>
    </section>
  );
}

/** Biggest 3-month moves in indicator scores: what changed recently. */
export function Movers({ movers, indicators, onPick }: { movers: Mover[]; indicators: Indicator[]; onPick: (i: Indicator) => void }) {
  if (!movers.length) return null;
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-3">
      <h3 className="text-sm font-semibold text-slate-200">O que mais mudou nos últimos 3 meses</h3>
      <p className="text-[11px] text-slate-500">Variação da pontuação (0 a 100) de cada indicador dentro da sua ótica.</p>
      <ul className="mt-2 grid gap-1 sm:grid-cols-2">
        {movers.map((m) => {
          const ind = indicators.find((i) => i.id === m.id);
          return (
            <li key={m.id} className="min-w-0">
              <button onClick={() => ind && onPick(ind)} className="flex w-full items-center gap-2 rounded px-1 py-0.5 text-left text-xs hover:bg-slate-800">
                <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: TONE[m.perspective] }} title={SHORT(m.perspective)} />
                <span className="min-w-0 flex-1 truncate text-slate-300">{m.name.replace(" (EUA)", "")}</span>
                <span className={`w-12 text-right tabular-nums font-semibold ${m.change >= 0 ? "text-amber-300" : "text-sky-300"}`}>{m.change >= 0 ? "▲" : "▼"} {fmt(Math.abs(m.change), 0)}</span>
                <span className="w-10 text-right tabular-nums text-slate-500">→ {fmt(m.score, 0)}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

const QUADRANTS: Record<string, [string, string, string, string]> = {
  // [low x / high y, high x / high y, low x / low y, high x / low y]
  "perez|minsky": ["Desalavancagem / crise", "Euforia frágil (zona de risco)", "Implantação calma", "Euforia com balanço sólido"],
};

/** Two lens indices plotted against each other over time: where the cycle has been and where it is now. */
export function CycleClock({ indices }: { indices: Record<string, Index> }) {
  const [x, setX] = useState("perez");
  const [y, setY] = useState("minsky");
  const [years, setYears] = useState(15);
  const pts = useMemo(() => {
    const ym = new Map((indices[y]?.history ?? []).map((h) => [h[0], h[1]]));
    const all = (indices[x]?.history ?? []).filter((h) => ym.has(h[0])).map((h) => ({ m: h[0], x: h[1], y: ym.get(h[0])! }));
    return all.slice(-years * 12);
  }, [indices, x, y, years]);
  const W = 420, H = 320, P = 34;
  const sx = (v: number) => P + (v / 100) * (W - 2 * P);
  const sy = (v: number) => H - P - (v / 100) * (H - 2 * P);
  const q = QUADRANTS[`${x}|${y}`];
  const ctl = "rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200";
  const last = pts[pts.length - 1];
  const step = Math.max(2, Math.ceil(years / 5));  // label a few years only, so labels do not collide
  const first = pts[0];
  return (
    <section id="relogio" className="scroll-mt-24 mt-10">
      <h2 className="text-xl font-bold">Relógio do ciclo — trajetória entre duas óticas</h2>
      <p className="text-sm text-slate-400">Cada ponto é um mês. O caminho mostra como a economia se moveu; o ponto maior é o mês mais recente.</p>
      <div className={`${card} mt-3`}>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <label>Eixo horizontal <select className={ctl} value={x} onChange={(e) => setX(e.target.value)}>{LENSES.filter((p) => p !== y).map((p) => <option key={p} value={p}>{SHORT(p)}</option>)}</select></label>
          <label>Eixo vertical <select className={ctl} value={y} onChange={(e) => setY(e.target.value)}>{LENSES.filter((p) => p !== x).map((p) => <option key={p} value={p}>{SHORT(p)}</option>)}</select></label>
          <label>Período <select className={ctl} value={years} onChange={(e) => setYears(Number(e.target.value))}>{[5, 10, 15, 25, 40].map((n) => <option key={n} value={n}>{n} anos</option>)}</select></label>
        </div>
        {pts.length < 2 ? <p className="mt-3 text-sm text-slate-400">Sem meses em comum suficientes entre essas duas óticas.</p> : (
          <div className="mt-1 grid items-center gap-4 lg:grid-cols-[3fr_2fr]">
          <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full max-w-2xl" role="img" aria-label={`Trajetória de ${SHORT(x)} contra ${SHORT(y)} nos últimos ${years} anos; agora ${Math.round(last.x)} e ${Math.round(last.y)}`}>
            <rect x={P} y={P} width={W - 2 * P} height={H - 2 * P} fill="none" stroke="#334155" />
            <line x1={sx(50)} x2={sx(50)} y1={P} y2={H - P} stroke="#334155" strokeDasharray="3 3" />
            <line x1={P} x2={W - P} y1={sy(50)} y2={sy(50)} stroke="#334155" strokeDasharray="3 3" />
            {q && [[25, 92, q[0]], [75, 92, q[1]], [25, 8, q[2]], [75, 8, q[3]]].map(([a, b, t]) => (
              <text key={String(t)} x={sx(Number(a))} y={sy(Number(b))} textAnchor="middle" className="fill-slate-500" fontSize="10">{t}</text>
            ))}
            {pts.slice(1).map((p, k) => (
              <line key={p.m} x1={sx(pts[k].x)} y1={sy(pts[k].y)} x2={sx(p.x)} y2={sy(p.y)} stroke={TONE[x]} strokeWidth="2" strokeOpacity={0.15 + 0.85 * (k / pts.length)} />
            ))}
            {pts.map((p) => p.m.endsWith("-01") && (
              <g key={`y${p.m}`}>
                <circle cx={sx(p.x)} cy={sy(p.y)} r="3" fill="#0f172a" stroke="#94a3b8" strokeWidth="1.5"><title>{`${p.m}: ${SHORT(x)} ${Math.round(p.x)}, ${SHORT(y)} ${Math.round(p.y)}`}</title></circle>
                {(Number(p.m.slice(0, 4)) - Number(last.m.slice(0, 4))) % step === 0 && p.m.slice(0, 4) !== last.m.slice(0, 4) && (
                  <text x={sx(p.x) + 5} y={sy(p.y) - 4} fontSize="9" className="fill-slate-400">{p.m.slice(0, 4)}</text>)}
              </g>
            ))}
            {pts.map((p) => <circle key={`h${p.m}`} cx={sx(p.x)} cy={sy(p.y)} r="6" fill="transparent"><title>{`${p.m}: ${SHORT(x)} ${Math.round(p.x)}, ${SHORT(y)} ${Math.round(p.y)}`}</title></circle>)}
            <circle cx={sx(last.x)} cy={sy(last.y)} r="7" fill={TONE[x]} stroke="#0f172a" strokeWidth="2"><title>{`Agora (${last.m}): ${SHORT(x)} ${Math.round(last.x)}, ${SHORT(y)} ${Math.round(last.y)}`}</title></circle>
            <text x={sx(last.x)} y={sy(last.y) + 18} textAnchor="middle" fontSize="11" fontWeight="bold" className="fill-slate-100">agora</text>
            <text x={W / 2} y={H - 6} textAnchor="middle" fontSize="11" className="fill-slate-300">{SHORT(x)} (0 a 100) →</text>
            <text x={12} y={H / 2} textAnchor="middle" fontSize="11" className="fill-slate-300" transform={`rotate(-90 12 ${H / 2})`}>{SHORT(y)} (0 a 100) →</text>
            {[0, 50, 100].map((v) => <text key={`xt${v}`} x={sx(v)} y={H - P + 12} textAnchor="middle" fontSize="9" className="fill-slate-500">{v}</text>)}
            {[0, 50, 100].map((v) => <text key={`yt${v}`} x={P - 4} y={sy(v) + 3} textAnchor="end" fontSize="9" className="fill-slate-500">{v}</text>)}
          </svg>
          <div className="space-y-2 text-xs text-slate-300">
            <p><b className="text-slate-100">Agora ({last.m}):</b> {SHORT(x)} {Math.round(last.x)} e {SHORT(y)} {Math.round(last.y)}.</p>
            <p>Há {years} anos ({first.m}): {SHORT(x)} {Math.round(first.x)} e {SHORT(y)} {Math.round(first.y)}.
              Movimento no período: {signed(last.x - first.x)} e {signed(last.y - first.y)} pontos.</p>
            {q && <p className="text-slate-400">No par Perez × Minsky, o canto superior direito junta euforia financeira e fragilidade alta, a combinação que Minsky e Perez associam às crises.
              O canto inferior esquerdo é o de capital produtivo e balanços sólidos. Use o período de 25 ou 40 anos para ver os ciclos anteriores.</p>}
            <p className="text-[11px] text-slate-500">Círculos vazios marcam janeiro de cada ano; passe o mouse sobre a linha para ver o mês. A linha fica mais forte nos meses recentes.</p>
          </div>
          </div>
        )}
      </div>
    </section>
  );
}

/** Past months whose lens readings looked most like today, and what followed. */
export function AnalogsSection({ analogs }: { analogs: Analogs | null }) {
  if (!analogs || !analogs.matches.length) return null;
  const pct = (v: number | null) => (v === null ? "—" : `${signed(v, 1)}% a.a.`);
  const recs = analogs.matches.filter((m) => m.recession_within_24m).length;
  return (
    <section id="analogos" className="scroll-mt-24 mt-10">
      <h2 className="text-xl font-bold">Períodos parecidos com hoje</h2>
      <p className="text-sm text-slate-400">
        Os meses desde {analogs.since.slice(0, 4)} em que {analogs.lenses.map(SHORT).join(", ")} estavam mais perto da leitura atual, com pelo menos 2 anos entre um e outro, e o que veio depois.
      </p>
      <div className={`${card} mt-3`}>
        <div className="flex flex-wrap gap-3 text-xs text-slate-300">
          <span className="text-slate-400">Hoje ({analogs.current.month}):</span>
          {analogs.lenses.map((p) => <span key={p}><span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: TONE[p] }} />{SHORT(p)} <b>{Math.round(analogs.current.values[p])}</b></span>)}
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-xs">
            <thead className="text-slate-400"><tr className="[&>th]:py-1 [&>th]:pr-3 [&>th]:font-medium">
              <th>Mês parecido</th>{analogs.lenses.map((p) => <th key={p}>{SHORT(p)}</th>)}<th>Distância</th><th>Recessão em até 2 anos?</th><th>Ações 1 ano depois</th><th>Ações 3 anos depois</th>
            </tr></thead>
            <tbody>{analogs.matches.map((m) => (
              <tr key={m.month} className="border-t border-slate-800 [&>td]:py-1.5 [&>td]:pr-3">
                <td className="font-semibold text-slate-100">{m.month}</td>
                {analogs.lenses.map((p) => <td key={p} className="tabular-nums">{Math.round(m.values[p])}</td>)}
                <td className="tabular-nums text-slate-400">{fmt(m.distance, 1)}</td>
                <td>{m.recession_within_24m ? <span className="text-red-300">sim (início {m.recession_start})</span> : <span className="text-emerald-300">não</span>}</td>
                <td className="tabular-nums">{pct(m.return_12m)}</td><td className="tabular-nums">{pct(m.return_36m)}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-slate-300">Em {recs} de {analogs.matches.length} períodos parecidos houve recessão nos 2 anos seguintes.</p>
        <p className="mt-1 text-[11px] text-slate-500">
          Distância = quão diferente era a combinação das óticas (0 = idêntica). Retorno real anualizado do S&P 500 com dividendos (Shiller; depois do último mês publicado por Shiller, só a variação de preço do S&P 500 descontada a inflação). “—” quando ainda não há dado.
          Poucos casos, dentro da amostra: é contexto histórico, não previsão nem recomendação.
        </p>
      </div>
    </section>
  );
}

/** Download the indicator table as CSV (values as shown, real data). */
export function downloadCsv(list: Indicator[], data: Data) {
  const head = ["id", "nome", "grupo", "fonte", "codigo", "frequencia", "valor", "unidade", "referencia", "percentil", "pontuacao", "frescor"];
  const esc = (v: unknown) => (v === null || v === undefined ? "" : /[",;\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  const rows = list.map((i) => [i.id, i.name, SHORT(i.perspective), i.source, i.code, i.frequency, i.value, i.unit, i.ref_date,
    (i.view ?? i).stats?.percentile ?? "", i.score, i.status].map(esc).join(","));
  const blob = new Blob([`﻿${head.join(",")}\n${rows.join("\n")}\n`], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `kondratiev-monitor-${(data.generated_at ?? "").slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
