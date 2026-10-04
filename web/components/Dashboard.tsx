"use client";
import { useMemo, useState } from "react";
import { Chart } from "./Chart";
import { DetailModal } from "./DetailModal";
import type { Data, Indicator, Index } from "@/lib/data";
import { PERSPECTIVES, bases } from "@/lib/reading";

// Lens identity colors: the validated categorical palette (dark steps), one fixed hue per lens.
const TONE: Record<string, string> = { kondratiev: "#3987e5", schumpeter: "#d95926", perez: "#199e70", freeman: "#c98500", minsky: "#d55181" };
const LENSES = Object.keys(PERSPECTIVES);
const SHORT = (p: string) => PERSPECTIVES[p].split(" — ")[0];
const BADGE = { ok: "bg-emerald-950 text-emerald-300 ring-emerald-800", atrasado: "bg-amber-950 text-amber-300 ring-amber-800", obsoleto: "bg-red-950 text-red-300 ring-red-800" };
const ZONE: Record<string, string> = { "muito baixo": "text-sky-300", baixo: "text-sky-400", neutro: "text-slate-300", alto: "text-amber-300", "muito alto": "text-red-300" };
const fmt = (n: number, d = 2) => n.toLocaleString("pt-BR", { maximumFractionDigits: d });
const SECTIONS: [string, string][] = [["resumo", "Resumo"], ["oticas", "Óticas"], ["cruzamentos", "Cruzamentos"], ["indicadores", "Indicadores"],
  ["valuation", "Valuation"], ["validacao", "Validação"], ["dados", "Dados"]];

/** State tone with its own label: the color never carries the meaning alone. */
function stateTone(p: string, v: number | null) {
  if (v === null) return "text-slate-400";
  if (p === "minsky") return v >= 67 ? "text-red-300" : v >= 33 ? "text-amber-300" : "text-emerald-300";
  if (p === "perez") return v >= 75 ? "text-red-300" : v >= 40 ? "text-amber-300" : "text-emerald-300";
  return v >= 60 ? "text-emerald-300" : v >= 40 ? "text-amber-300" : "text-sky-300";
}

function Gauge({ value, cuts, color }: { value: number; cuts: number[]; color: string }) {
  return (
    <div className="relative mt-2 h-2 rounded-full bg-slate-800" role="img" aria-label={`Índice ${Math.round(value)} de 100`}>
      <div className="absolute inset-y-0 left-0 rounded-full" style={{ width: `${value}%`, background: color }} />
      {cuts.map((c) => <div key={c} className="absolute inset-y-[-3px] w-px bg-slate-400/60" style={{ left: `${c}%` }} title={`limiar ${c}`} />)}
    </div>
  );
}

function SummaryTile({ p, idx, cuts }: { p: string; idx: Index | undefined; cuts: number[] }) {
  return (
    <a href={`#otica-${p}`} className="block rounded-xl border border-slate-800 bg-slate-900/80 p-3 transition hover:border-slate-600">
      <div className="flex items-center gap-2 text-xs text-slate-400"><span className="h-2 w-2 rounded-full" style={{ background: TONE[p] }} />{SHORT(p)}</div>
      <div className={`mt-1 min-h-[2.5rem] text-sm font-semibold leading-tight ${stateTone(p, idx?.value ?? null)}`}>{idx?.state ?? "Dados insuficientes"}</div>
      {idx?.value != null ? (
        <>
          <div className="mt-1 flex items-baseline gap-2"><span className="text-2xl font-bold text-slate-100">{Math.round(idx.value)}</span><span className="text-xs text-slate-500">/100</span>
            {idx.change_12m != null && <span className="text-xs text-slate-400">{idx.change_12m >= 0 ? "▲" : "▼"}{Math.round(Math.abs(idx.change_12m))} em 12m</span>}</div>
          <Gauge value={idx.value} cuts={cuts} color={TONE[p]} />
          <div className={`mt-1 text-[11px] ${idx.stale ? "text-amber-400" : "text-slate-500"}`}>dado de {idx.as_of}{idx.stale ? " · desatualizado" : ""}</div>
        </>
      ) : <div className="mt-2 text-[11px] text-slate-500">menos de 3 indicadores atuais</div>}
    </a>
  );
}

function IndexPanel({ p, idx, cuts, recessions, onPick, indicators }: { p: string; idx: Index; cuts: number[]; recessions: [string, string][]; onPick: (i: Indicator) => void; indicators: Indicator[] }) {
  const hist = idx.history.map((h) => [h[0], h[1]] as [string, number]);
  return (
    <div id={`otica-${p}`} className="scroll-mt-24 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200"><span className="h-2.5 w-2.5 rounded-full" style={{ background: TONE[p] }} />{PERSPECTIVES[p]}</h3>
        {idx.value !== null && <span className="text-xs text-slate-500">{idx.n}/{idx.total} indicadores</span>}
      </div>
      <p className={`mt-1 text-lg font-bold ${stateTone(p, idx.value)}`}>{idx.state ?? "Dados insuficientes"}</p>
      {idx.value !== null ? (
        <>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <span>Índice <b className="text-slate-100">{Math.round(idx.value)}</b>/100</span>
            {idx.change_12m != null && <span>{idx.change_12m >= 0 ? "▲" : "▼"} {Math.round(Math.abs(idx.change_12m))} pts em 12 meses</span>}
            {idx.as_of && <span className={idx.stale ? "text-amber-400" : ""}>dado de {idx.as_of}{idx.stale ? " (desatualizado)" : ""}</span>}
          </div>
          <div className="mt-2"><Chart data={hist} recessions={recessions} fixedY={[0, 100]} height={150} color={TONE[p]} digits={0} guides={cuts} label={`${PERSPECTIVES[p]}: ${idx.label}`} /></div>
          <p className="mt-1 text-[11px] text-slate-500">{idx.label}. Linhas tracejadas = limiares dos estados. Sombra cinza = recessões dos EUA.</p>
          {idx.groups.length > 1 && (
            <div className="mt-3 space-y-1">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">Composição (média de cada subgrupo)</div>
              {idx.groups.map((g) => (
                <div key={g.group} className="flex items-center gap-2 text-xs">
                  <span className="w-32 shrink-0 text-slate-400">{g.group} <span className="text-slate-600">({g.n})</span></span>
                  <div className="h-1.5 flex-1 rounded-full bg-slate-800"><div className="h-1.5 rounded-full" style={{ width: `${g.score}%`, background: TONE[p] }} /></div>
                  <span className="w-8 text-right tabular-nums text-slate-300">{Math.round(g.score)}</span>
                </div>
              ))}
            </div>
          )}
          <p className="mt-3 text-xs text-slate-300">{idx.summary}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {idx.drivers.slice(0, 4).map((d) => {
              const ind = indicators.find((i) => i.id === d.id);
              return ind ? <button key={d.id} onClick={() => onPick(ind)} className="rounded border border-slate-700 px-2 py-0.5 text-[11px] text-slate-300 hover:bg-slate-800">{d.name} · {Math.round(d.score)}</button> : null;
            })}
          </div>
        </>
      ) : <p className="mt-2 text-xs text-slate-400">{idx.summary}</p>}
    </div>
  );
}

function Spark({ h, color = "#3987e5" }: { h: [string, number][]; color?: string }) {
  const pts = h.slice(-60);
  if (pts.length < 2) return null;
  const v = pts.map((p) => p[1]), min = Math.min(...v), max = Math.max(...v), r = max - min || 1;
  const d = v.map((y, k) => `${(k / (v.length - 1)) * 100},${18 - ((y - min) / r) * 16}`).join(" ");
  return <svg viewBox="0 0 100 20" className="h-5 w-24" aria-hidden="true"><polyline points={d} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" /></svg>;
}

function PercentileBar({ p }: { p: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-1.5 w-20 rounded-full bg-gradient-to-r from-sky-800 via-slate-700 to-red-800">
        <div className="absolute top-[-3px] h-3 w-0.5 rounded bg-white" style={{ left: `calc(${p}% - 1px)` }} />
      </div>
      <span className="w-6 text-right tabular-nums text-slate-300">{Math.round(p)}</span>
    </div>
  );
}

function IndicatorTable({ list, onPick }: { list: Indicator[]; onPick: (i: Indicator) => void }) {
  const [q, setQ] = useState("");
  const [lens, setLens] = useState("todas");
  const [fresh, setFresh] = useState("todos");
  const [sort, setSort] = useState<"otica" | "extremo" | "frescor">("otica");
  const rows = useMemo(() => {
    const term = q.trim().toLowerCase();
    let r = list.filter((i) => (lens === "todas" || i.perspective === lens) && (fresh === "todos" || i.status === fresh)
      && (!term || i.name.toLowerCase().includes(term) || i.code.toLowerCase().includes(term)));
    const pct = (i: Indicator) => bases(i)[0]?.stats.percentile ?? 50;
    if (sort === "extremo") r = [...r].sort((a, b) => Math.abs(pct(b) - 50) - Math.abs(pct(a) - 50));
    else if (sort === "frescor") r = [...r].sort((a, b) => (b.ref_date ?? "").localeCompare(a.ref_date ?? ""));
    else r = [...r].sort((a, b) => LENSES.indexOf(a.perspective) - LENSES.indexOf(b.perspective) || a.name.localeCompare(b.name));
    return r;
  }, [list, q, lens, fresh, sort]);
  const ctl = "rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200";
  return (
    <>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar indicador ou código…" className={`${ctl} w-56`} aria-label="Buscar" />
        <select value={lens} onChange={(e) => setLens(e.target.value)} className={ctl} aria-label="Ótica">
          <option value="todas">Todas as óticas</option>{LENSES.map((p) => <option key={p} value={p}>{SHORT(p)}</option>)}
        </select>
        <select value={fresh} onChange={(e) => setFresh(e.target.value)} className={ctl} aria-label="Frescor">
          <option value="todos">Qualquer frescor</option><option value="ok">Só ok</option><option value="atrasado">Atrasados</option><option value="obsoleto">Obsoletos</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)} className={ctl} aria-label="Ordenar">
          <option value="otica">Ordenar por ótica</option><option value="extremo">Mais extremos primeiro</option><option value="frescor">Mais recentes primeiro</option>
        </select>
        <span className="text-xs text-slate-500">{rows.length} indicadores</span>
      </div>
      <div className="mt-2 overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full min-w-[860px] text-left text-xs">
          <thead className="bg-slate-900 text-slate-400">
            <tr className="[&>th]:px-3 [&>th]:py-2 [&>th]:font-medium"><th>Indicador</th><th>Valor</th><th>Leitura</th><th>Percentil na história</th><th>Últimos 5 anos</th><th>Referência</th><th>Frescor</th></tr>
          </thead>
          <tbody>
            {rows.map((i) => {
              const b = bases(i)[0];
              const change = b && b.label !== "Nível";
              return (
                <tr key={i.id} onClick={() => onPick(i)} onKeyDown={(e) => e.key === "Enter" && onPick(i)} tabIndex={0}
                  className="cursor-pointer border-t border-slate-800 hover:bg-slate-900 focus:bg-slate-900 focus:outline-none [&>td]:px-3 [&>td]:py-2">
                  <td>
                    <div className="flex items-center gap-2"><span className="h-2 w-2 shrink-0 rounded-full" style={{ background: TONE[i.perspective] }} title={SHORT(i.perspective)} />
                      <span className="font-medium text-slate-100">{i.name}</span>
                      {i.note && <span className="rounded bg-sky-950 px-1.5 text-[10px] text-sky-300" title={i.note}>{i.source === "derivado" ? "calculado" : "estimado"}</span>}</div>
                    <div className="ml-4 text-[11px] text-slate-500">{SHORT(i.perspective)} · {i.source.toUpperCase()} · {i.frequency}</div>
                  </td>
                  <td className="whitespace-nowrap tabular-nums text-slate-100">{i.value !== null ? fmt(i.value) : "—"} <span className="text-slate-500">{i.unit}</span></td>
                  <td className="whitespace-nowrap">{b ? (change ? <span>{b.label.replace("Variação em ", "Var. ")}: <b className="tabular-nums">{b.value >= 0 ? "+" : ""}{fmt(b.value, 1)}{b.unit === "%" ? "%" : ` ${b.unit ?? ""}`}</b></span> : <span className="text-slate-400">nível</span>) : "—"}
                    {b && <span className={`ml-1 ${ZONE[b.stats.zone]}`}>· {b.stats.zone}</span>}</td>
                  <td>{b ? <PercentileBar p={b.stats.percentile} /> : "—"}</td>
                  <td><Spark h={i.history} color={TONE[i.perspective]} /></td>
                  <td className="whitespace-nowrap tabular-nums text-slate-400">{i.ref_date}</td>
                  <td>{i.status && <span className={`rounded px-1.5 py-0.5 ring-1 ${BADGE[i.status]}`}>{i.status}</span>}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

function monthsBetween(yyyymm: string, iso: string) {
  return Number(iso.slice(0, 4)) * 12 + Number(iso.slice(5, 7)) - (Number(yyyymm.slice(0, 4)) * 12 + Number(yyyymm.slice(5, 7)));
}

function Valuation({ data }: { data: Data }) {
  const v = data.valuation;
  if (!v) return null;
  const cape = data.indicators.find((i) => i.id === "shiller_cape");
  return (
    <section id="valuation" className="scroll-mt-24 mt-10">
      <h2 className="text-xl font-bold">Valuation — o que aconteceu depois de CAPE parecido</h2>
      <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <p className="text-sm text-slate-300">
          CAPE do S&P 500: <b>{fmt(v.current, 1)}</b> ({v.current_date}), no percentil <b>{fmt(v.percentile, 0)}</b> da história desde {v.since.slice(0, 4)}.
          A tabela mostra o retorno real anualizado nos meses em que o CAPE esteve entre os percentis {v.band[0]} e {v.band[1]}, contra todos os meses.
        </p>
        {cape?.note && <p className="mt-2 rounded border border-sky-900 bg-sky-950/40 p-2 text-xs text-sky-200">{cape.note}</p>}
        {data.generated_at && monthsBetween(v.current_date, data.generated_at) > 6 && (
          <p className="mt-2 rounded border border-amber-800 bg-amber-950/40 p-2 text-xs text-amber-300">Atenção: o último CAPE disponível tem {monthsBetween(v.current_date, data.generated_at)} meses.</p>
        )}
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400"><tr><th className="py-1">Horizonte</th><th>CAPE parecido: mediana</th><th>pior 10%</th><th>melhor 10%</th><th>% negativos</th><th>meses</th><th>Todos os meses: mediana</th></tr></thead>
            <tbody>{v.horizons.map((h) => (
              <tr key={h.years} className="border-t border-slate-800">
                <td className="py-1">{h.years} {h.years === 1 ? "ano" : "anos"}</td>
                <td className="font-semibold">{fmt(h.similar.median, 1)}% a.a.</td><td>{fmt(h.similar.p10, 1)}%</td><td>{fmt(h.similar.p90, 1)}%</td>
                <td>{h.similar.negative_share}%</td><td>{h.similar.n}</td><td>{fmt(h.all.median, 1)}% a.a.</td>
              </tr>))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[11px] text-slate-500">Estatística descritiva dentro da amostra; as janelas se sobrepõem, então há bem menos episódios independentes que meses. O passado não garante o futuro, e isto não é recomendação de investimento.</p>
      </div>
    </section>
  );
}

function Validation({ data }: { data: Data }) {
  const bt = Object.entries(data.backtest);
  if (!bt.length) return null;
  return (
    <section id="validacao" className="scroll-mt-24 mt-10">
      <h2 className="text-xl font-bold">Validação histórica — os índices subiram antes das recessões?</h2>
      <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <p className="text-sm text-slate-300">Média de cada índice nos 24 meses que antecederam cada recessão dos EUA, comparada com a média fora de recessões.</p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400"><tr><th className="py-1">Ótica</th><th>Recessões</th><th>Antes (média)</th><th>Fora de recessão</th><th>Diferença</th><th>Acertos no limiar</th><th>Alarmes falsos</th></tr></thead>
            <tbody>{bt.map(([p, b]) => (
              <tr key={p} className="border-t border-slate-800">
                <td className="py-1"><span className="mr-2 inline-block h-2 w-2 rounded-full" style={{ background: TONE[p] }} />{SHORT(p)}</td><td>{b.recessions}</td>
                <td>{b.avg_before !== null ? fmt(b.avg_before, 0) : "—"}</td><td>{b.avg_other !== null ? fmt(b.avg_other, 0) : "—"}</td>
                <td className={b.difference !== undefined && Math.abs(b.difference) >= 5 ? "font-semibold" : ""}>{b.difference !== undefined ? (b.difference > 0 ? "+" : "") + fmt(b.difference, 0) : "—"}</td>
                <td>{b.threshold !== undefined ? `${b.hits}/${b.recessions} (índice ≥ ${b.threshold})` : "—"}</td>
                <td>{b.false_alarm_rate != null ? `${b.false_alarm_rate}%` : "—"}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[11px] text-slate-500">Limites: poucas recessões na janela de dados, limiares escolhidos dentro da amostra, dados revisados (não são os divulgados na época). Um índice sem diferença relevante não ajuda a antecipar recessões, e isso também é resultado.</p>
      </div>
    </section>
  );
}

export function Dashboard({ data }: { data: Data }) {
  const [scope, setScope] = useState<"usa" | "global">("usa");
  const [open, setOpen] = useState<Indicator | null>(null);
  const indices = data.indices[scope];
  const all = useMemo(() => data.indicators.filter((i) => i.scope === scope), [data, scope]);
  const list = useMemo(() => all.filter((i) => i.value !== null), [all]);
  const crossed = list.filter((i) => i.note);
  const missing = all.filter((i) => i.value === null);
  const counts = { ok: list.filter((i) => i.status === "ok").length, atrasado: list.filter((i) => i.status === "atrasado").length, obsoleto: list.filter((i) => i.status === "obsoleto").length };
  const empty = data.indicators.length === 0;
  const cuts = (p: string) => data.thresholds?.[p] ?? [];

  return (
    <>
      <header className="sticky top-0 z-40 -mx-4 border-b border-slate-800 bg-slate-950/95 px-4 py-3 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-bold">Kondratiev Monitor</h1>
            <p className="text-[11px] text-slate-400">{data.generated_at ? `Atualizado em ${data.generated_at.slice(0, 16).replace("T", " ")} UTC · metodologia v${data.methodology_version}` : "Sem dados ainda"}</p>
          </div>
          <div className="inline-flex rounded-lg border border-slate-700 p-0.5 text-xs" role="group" aria-label="Escopo">
            {([["usa", "Estados Unidos"], ["global", "Global"]] as const).map(([k, l]) => (
              <button key={k} onClick={() => setScope(k)} aria-pressed={scope === k} className={`rounded px-3 py-1 ${scope === k ? "bg-sky-900 text-sky-100" : "text-slate-300"}`}>{l}</button>
            ))}
          </div>
        </div>
        <nav className="mt-2 flex gap-3 overflow-x-auto text-xs text-slate-400" aria-label="Seções">
          {SECTIONS.filter(([id]) => scope === "usa" || !["cruzamentos", "valuation", "validacao"].includes(id)).map(([id, l]) => (
            <a key={id} href={`#${id}`} className="whitespace-nowrap hover:text-slate-100">{l}</a>
          ))}
        </nav>
      </header>

      {empty && <p className="mt-6 rounded border border-slate-700 p-3 text-sm text-slate-300">Ainda não há dados. A primeira atualização automática coleta os dados reais das fontes oficiais.</p>}

      {!empty && (
        <>
          <section id="resumo" className="scroll-mt-24 mt-6">
            <h2 className="text-xl font-bold">Onde estamos no ciclo — {scope === "usa" ? "Estados Unidos" : "Mundo"}</h2>
            <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
              {LENSES.map((p) => <SummaryTile key={p} p={p} idx={indices[p]} cuts={cuts(p)} />)}
            </div>
            {(data.extremes?.[scope]?.length ?? 0) > 0 && (
              <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                <h3 className="text-sm font-semibold text-slate-200">Nos extremos da própria história agora</h3>
                <ul className="mt-2 flex flex-wrap gap-1">
                  {data.extremes[scope].map((e) => {
                    const ind = list.find((i) => i.id === e.id);
                    return (
                      <li key={e.id}>
                        <button onClick={() => ind && setOpen(ind)} className={`rounded border px-2 py-0.5 text-[11px] hover:bg-slate-800 ${e.direction === "máxima" ? "border-red-900 text-red-300" : "border-sky-900 text-sky-300"}`}>
                          {e.direction === "máxima" ? "▲" : "▼"} {e.name}{e.basis !== "nível" ? ` (${e.basis.toLowerCase()})` : ""} · p{Math.round(e.percentile)}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
            <p className="mt-3 text-xs text-slate-400">
              Cada ótica é um índice de 0 a 100 feito da posição de cada indicador na sua própria história (percentil sem olhar o futuro), com subgrupos de peso igual.
              Os estados seguem regras fixas da metodologia. Leitura descritiva de contexto: não prevê nada e não é recomendação de investimento.
            </p>
          </section>

          <section id="oticas" className="scroll-mt-24 mt-10">
            <h2 className="text-xl font-bold">As cinco óticas ao longo do tempo</h2>
            <div className="mt-3 grid gap-4 lg:grid-cols-2">
              {LENSES.map((p) => indices[p] && <IndexPanel key={p} p={p} idx={indices[p]} cuts={cuts(p)} recessions={data.recessions} onPick={setOpen} indicators={list} />)}
            </div>
          </section>

          {crossed.length > 0 && (
            <section id="cruzamentos" className="scroll-mt-24 mt-10">
              <h2 className="text-xl font-bold">Cruzamentos — indicadores calculados a partir de várias fontes</h2>
              <p className="text-sm text-slate-400">Quando nenhuma fonte publica o dado pronto ou atualizado, ele é calculado com séries oficiais. A fórmula aparece em cada um.</p>
              <div className="mt-3 grid gap-3 md:grid-cols-3">
                {crossed.map((i) => {
                  const b = bases(i)[0];
                  return (
                    <button key={i.id} onClick={() => setOpen(i)} className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-left hover:border-slate-600">
                      <div className="text-sm font-medium text-slate-100">{i.name}</div>
                      <div className="mt-1 text-2xl font-bold tabular-nums">{fmt(i.value!)} <span className="text-sm font-normal text-slate-400">{i.unit}</span></div>
                      {b && <div className="mt-1"><PercentileBar p={b.stats.percentile} /></div>}
                      <p className="mt-2 text-[11px] text-slate-400">{i.note}</p>
                      <p className="mt-1 text-[11px] text-slate-500">Referência {i.ref_date}</p>
                    </button>
                  );
                })}
              </div>
            </section>
          )}

          <section id="indicadores" className="scroll-mt-24 mt-10">
            <h2 className="text-xl font-bold">Todos os indicadores</h2>
            <p className="text-sm text-slate-400">Clique em uma linha para ver o histórico completo, a tendência, os extremos e a leitura. Séries que sempre crescem são lidas pela variação.</p>
            <IndicatorTable list={list} onPick={setOpen} />
          </section>

          {scope === "usa" && <Valuation data={data} />}
          {scope === "usa" && <Validation data={data} />}
        </>
      )}

      <section id="dados" className="scroll-mt-24 mt-10">
        <h2 className="text-xl font-bold">Qualidade dos dados</h2>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className={`rounded px-2 py-1 ring-1 ${BADGE.ok}`}>{counts.ok} ok</span>
          <span className={`rounded px-2 py-1 ring-1 ${BADGE.atrasado}`}>{counts.atrasado} atrasados</span>
          <span className={`rounded px-2 py-1 ring-1 ${BADGE.obsoleto}`}>{counts.obsoleto} obsoletos</span>
        </div>
        {missing.length > 0 && <p className="mt-2 text-xs text-amber-400">Séries sem dados nesta visão ({missing.length}): {missing.map((m) => m.name).join("; ")}.</p>}
        {data.runs.length === 0 ? <p className="mt-2 text-sm text-slate-500">Nenhuma execução registrada.</p> : (
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs"><thead className="bg-slate-900 text-slate-400"><tr><th className="px-3 py-2">Fonte</th><th>Início</th><th>Status</th><th>Linhas</th><th>Erro</th></tr></thead>
              <tbody>{data.runs.map((r, k) => (<tr key={k} className="border-t border-slate-800"><td className="px-3 py-1">{r.source}</td><td>{r.started_at.slice(0, 16)}</td><td>{r.status}</td><td className="tabular-nums">{r.rows}</td><td className="break-all text-red-400">{r.error ? r.error.slice(0, 300) : ""}</td></tr>))}</tbody></table>
          </div>
        )}
      </section>
      {open && <DetailModal ind={open} recessions={data.recessions} onClose={() => setOpen(null)} />}
    </>
  );
}
