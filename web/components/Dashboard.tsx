"use client";
import { useMemo, useState } from "react";
import { Chart } from "./Chart";
import { DetailModal } from "./DetailModal";
import type { Data, Indicator, Index } from "@/lib/data";
import { PERSPECTIVES, bases } from "@/lib/reading";

const BADGE = { ok: "bg-emerald-900 text-emerald-300", atrasado: "bg-amber-900 text-amber-300", obsoleto: "bg-red-900 text-red-300" };
const ZONE: Record<string, string> = { "muito baixo": "text-sky-300", baixo: "text-sky-400", neutro: "text-slate-300", alto: "text-amber-400", "muito alto": "text-red-400" };
const fmt = (n: number, d = 2) => n.toLocaleString("pt-BR", { maximumFractionDigits: d });
const TONE: Record<string, string> = { kondratiev: "#38bdf8", schumpeter: "#a78bfa", perez: "#f59e0b", freeman: "#34d399", minsky: "#f87171" };

function stateColor(p: string, v: number | null) {
  if (v === null) return "text-slate-400";
  if (p === "minsky") return v >= 67 ? "text-red-400" : v >= 33 ? "text-amber-300" : "text-emerald-300";
  if (p === "perez") return v >= 75 ? "text-red-400" : v >= 40 ? "text-amber-300" : "text-emerald-300";
  return v >= 60 ? "text-emerald-300" : v >= 40 ? "text-amber-300" : "text-sky-300";
}

function IndexPanel({ persp, idx, recessions, onPick, indicators }: { persp: string; idx: Index; recessions: [string, string][]; onPick: (i: Indicator) => void; indicators: Indicator[] }) {
  const hist = idx.history.map((h) => [h[0], h[1]] as [string, number]);
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-300">{PERSPECTIVES[persp]}</h3>
        {idx.value !== null && <span className="text-xs text-slate-500">{idx.n}/{idx.total} indicadores</span>}
      </div>
      <p className={`mt-1 text-lg font-bold ${stateColor(persp, idx.value)}`}>{idx.state ?? "Dados insuficientes"}</p>
      {idx.value !== null && (
        <>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <span>Índice <b className="text-slate-100">{Math.round(idx.value)}</b>/100</span>
            {idx.change_12m != null && <span>{idx.change_12m >= 0 ? "▲" : "▼"} {Math.round(Math.abs(idx.change_12m))} pts em 12 meses</span>}
            {idx.as_of && <span className={idx.stale ? "text-amber-400" : ""}>dado de {idx.as_of}{idx.stale ? " (desatualizado)" : ""}</span>}
          </div>
          <div className="mt-2"><Chart data={hist} recessions={recessions} fixedY={[0, 100]} height={150} color={TONE[persp]} digits={0} label={`${PERSPECTIVES[persp]}: ${idx.label}`} /></div>
          <p className="mt-1 text-[11px] text-slate-500">{idx.label}. Sombra cinza = recessões dos EUA.</p>
          <p className="mt-2 text-xs text-slate-300">{idx.summary}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {idx.drivers.slice(0, 3).map((d) => {
              const ind = indicators.find((i) => i.id === d.id);
              return ind ? <button key={d.id} onClick={() => onPick(ind)} className="rounded border border-slate-700 px-2 py-0.5 text-[11px] text-slate-300 hover:bg-slate-800">{d.name} · {Math.round(d.score)}</button> : null;
            })}
          </div>
        </>
      )}
      {idx.value === null && <p className="mt-2 text-xs text-slate-400">{idx.summary}</p>}
    </div>
  );
}

function Spark({ h }: { h: [string, number][] }) {
  const pts = h.slice(-60);
  if (pts.length < 2) return null;
  const v = pts.map((p) => p[1]), min = Math.min(...v), max = Math.max(...v), r = max - min || 1;
  const d = v.map((y, k) => `${(k / (v.length - 1)) * 200},${28 - ((y - min) / r) * 26}`).join(" ");
  return <svg viewBox="0 0 200 30" className="mt-2 h-8 w-full"><polyline points={d} fill="none" stroke="#38bdf8" strokeWidth="1.5" /></svg>;
}

function Card({ i, onPick }: { i: Indicator; onPick: (i: Indicator) => void }) {
  const delta = i.value !== null && i.previous !== null ? i.value - i.previous : null;
  return (
    <button onClick={() => onPick(i)} className="rounded-lg border border-slate-800 bg-slate-900 p-4 text-left transition hover:border-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-600">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium">{i.name}</h4>
        {i.status && <span className={`shrink-0 rounded px-2 py-0.5 text-xs ${BADGE[i.status]}`}>{i.status}</span>}
      </div>
      {i.value === null ? <p className="mt-3 text-sm text-slate-500">Sem dados.</p> : (
        <>
          <p className="mt-2 text-2xl font-semibold">{fmt(i.value)} <span className="text-sm font-normal text-slate-400">{i.unit}</span></p>
          <Spark h={i.history} />
          {delta !== null && <p className="text-xs text-slate-400">{delta >= 0 ? "▲" : "▼"} {fmt(Math.abs(delta))} vs. observação anterior</p>}
          {(() => {
            const b = bases(i)[0];
            if (!b) return null;
            const change = b.label !== "Nível";
            return <p className="mt-1 text-xs">{change && <>{b.label}: <b>{b.value >= 0 ? "+" : ""}{fmt(b.value, 1)}{b.unit === "%" ? "%" : ` ${b.unit ?? ""}`}</b> · </>}
              Percentil <b>{fmt(b.stats.percentile, 0)}</b>{change ? "" : " da história"} · <span className={ZONE[b.stats.zone]}>{b.stats.zone}</span></p>;
          })()}
          <p className="mt-1 text-xs text-slate-400">Referência {i.ref_date} · {i.source.toUpperCase()} · {i.frequency}</p>
        </>
      )}
      <p className="mt-2 text-xs text-sky-400">Ver histórico e leitura →</p>
    </button>
  );
}

function monthsBetween(yyyymm: string, iso: string) {
  const a = Number(yyyymm.slice(0, 4)) * 12 + Number(yyyymm.slice(5, 7));
  const b = Number(iso.slice(0, 4)) * 12 + Number(iso.slice(5, 7));
  return b - a;
}

function Context({ data }: { data: Data }) {
  const v = data.valuation;
  const bt = Object.entries(data.backtest);
  return (
    <>
      {v && (
        <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-bold">Contexto de valuation — o que aconteceu depois de CAPE parecido</h2>
          <p className="mt-1 text-sm text-slate-300">
            Último CAPE disponível do S&P 500: <b>{fmt(v.current, 1)}</b> ({v.current_date}), no percentil <b>{fmt(v.percentile, 0)}</b> da história desde {v.since.slice(0, 4)}.
            A tabela mostra o retorno real anualizado nos meses em que o CAPE esteve entre os percentis {v.band[0]} e {v.band[1]}, contra todos os meses.
          </p>
          {data.generated_at && monthsBetween(v.current_date, data.generated_at) > 6 && (
            <p className="mt-2 rounded border border-amber-800 bg-amber-950/40 p-2 text-xs text-amber-300">
              Atenção: o arquivo público do Shiller está desatualizado ({monthsBetween(v.current_date, data.generated_at)} meses). A tabela usa o último CAPE publicado,
              que pode ser diferente do atual. Para um valuation atualizado, veja o indicador Buffett (Fed) e o Nasdaq na seção Perez.
            </p>
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
          <p className="mt-2 text-[11px] text-slate-500">Estatística descritiva dentro da amostra. As janelas se sobrepõem, então o número efetivo de episódios independentes é muito menor que o de meses.
            O passado não garante o futuro, e isto não é recomendação de investimento.</p>
        </section>
      )}
      {bt.length > 0 && (
        <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="text-lg font-bold">Validação histórica — os índices subiram antes das recessões?</h2>
          <p className="mt-1 text-sm text-slate-300">Média de cada índice nos 24 meses que antecederam cada recessão dos EUA, comparada com a média fora de recessões.</p>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400"><tr><th className="py-1">Ótica</th><th>Recessões</th><th>Antes (média)</th><th>Fora de recessão</th><th>Diferença</th><th>Acertos no limiar</th><th>Alarmes falsos</th></tr></thead>
              <tbody>{bt.map(([p, b]) => (
                <tr key={p} className="border-t border-slate-800">
                  <td className="py-1">{PERSPECTIVES[p].split(" — ")[0]}</td><td>{b.recessions}</td>
                  <td>{b.avg_before !== null ? fmt(b.avg_before, 0) : "—"}</td><td>{b.avg_other !== null ? fmt(b.avg_other, 0) : "—"}</td>
                  <td className={b.difference !== undefined && Math.abs(b.difference) >= 5 ? "font-semibold" : ""}>{b.difference !== undefined ? (b.difference > 0 ? "+" : "") + fmt(b.difference, 0) : "—"}</td>
                  <td>{b.threshold !== undefined ? `${b.hits}/${b.recessions} (índice ≥ ${b.threshold})` : "—"}</td>
                  <td>{b.false_alarm_rate != null ? `${b.false_alarm_rate}%` : "—"}</td>
                </tr>))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[11px] text-slate-500">Limites: poucas recessões na janela de dados, limiares escolhidos dentro da amostra, dados revisados (não são os divulgados na época) e defasagens de publicação aproximadas.
            Um índice sem diferença relevante não ajuda a antecipar recessões, e isso faz parte do resultado.</p>
        </section>
      )}
    </>
  );
}

export function Dashboard({ data }: { data: Data }) {
  const [scope, setScope] = useState<"usa" | "global">("usa");
  const [open, setOpen] = useState<Indicator | null>(null);
  const indices = data.indices[scope];
  const all = useMemo(() => data.indicators.filter((i) => i.scope === scope), [data, scope]);
  const list = useMemo(() => all.filter((i) => i.value !== null), [all]);
  const missing = all.filter((i) => i.value === null);
  const empty = data.indicators.length === 0;
  const stale = list.filter((i) => i.status === "obsoleto").length;

  return (
    <>
      <h1 className="text-2xl font-bold">Kondratiev Monitor</h1>
      <p className="mt-1 text-sm text-slate-400">
        Ciclos econômicos de longa duração sob 5 óticas, com dados oficiais e frescor visível.
        {data.generated_at && <> Última atualização: {data.generated_at.slice(0, 16).replace("T", " ")} UTC · metodologia v{data.methodology_version}.</>}
      </p>
      {empty && <p className="mt-6 rounded border border-slate-700 p-3 text-sm text-slate-300">Ainda não há dados. A primeira atualização automática coleta os dados reais das fontes oficiais.</p>}

      {!empty && (
        <>
          <div className="mt-5 inline-flex rounded-lg border border-slate-700 p-1 text-sm">
            {([["usa", "Estados Unidos (foco)"], ["global", "Visão global"]] as const).map(([k, l]) => (
              <button key={k} onClick={() => setScope(k)} className={`rounded px-3 py-1 ${scope === k ? "bg-sky-900 text-sky-200" : "text-slate-300"}`}>{l}</button>
            ))}
          </div>

          <section className="mt-6 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <h2 className="text-lg font-bold">Leitura consolidada — {scope === "usa" ? "Estados Unidos" : "Mundo"}</h2>
            <ul className="mt-2 grid gap-1 text-sm sm:grid-cols-2">
              {Object.keys(PERSPECTIVES).map((p) => (
                <li key={p}><span className="text-slate-400">{PERSPECTIVES[p].split(" — ")[0]}:</span>{" "}
                  <b className={stateColor(p, indices[p]?.value ?? null)}>{indices[p]?.state ?? "dados insuficientes"}</b>
                  {indices[p]?.value != null && <span className="text-slate-500"> (índice {Math.round(indices[p].value!)}{indices[p].stale ? `, dado de ${indices[p].as_of}` : ""})</span>}</li>
              ))}
            </ul>
            {(data.extremes?.[scope]?.length ?? 0) > 0 && (
              <div className="mt-3">
                <h3 className="text-sm font-semibold text-slate-200">Nos extremos da própria história agora</h3>
                <ul className="mt-1 flex flex-wrap gap-1">
                  {data.extremes[scope].map((e) => {
                    const ind = list.find((i) => i.id === e.id);
                    return (
                      <li key={e.id}>
                        <button onClick={() => ind && setOpen(ind)} className={`rounded border px-2 py-0.5 text-[11px] hover:bg-slate-800 ${e.direction === "máxima" ? "border-red-900 text-red-300" : "border-sky-900 text-sky-300"}`}>
                          {e.name}{e.basis !== "nível" ? ` (${e.basis.toLowerCase()})` : ""} · percentil {Math.round(e.percentile)}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
            <p className="mt-3 text-xs text-slate-400">
              Cada ótica é um índice de 0 a 100 construído com a posição de cada indicador na sua própria história (percentil sem olhar o futuro). Os estados vêm de regras
              fixas documentadas na metodologia. É uma leitura descritiva de contexto: não prevê nada e não é recomendação de investimento. A evidência estatística sobre ondas
              de Kondratiev é limitada (poucos ciclos completos).
            </p>
            {stale > 0 && <p className="mt-2 text-xs text-amber-400">{stale} indicador(es) com dado obsoleto nesta visão.</p>}
          </section>

          <section className="mt-6">
            <h2 className="mb-3 text-lg font-bold">Índices por ótica ao longo do tempo</h2>
            <div className="grid gap-4 lg:grid-cols-2">
              {Object.keys(PERSPECTIVES).map((p) => indices[p] && (
                <IndexPanel key={p} persp={p} idx={indices[p]} recessions={data.recessions} onPick={setOpen} indicators={list} />
              ))}
            </div>
          </section>

          <section className="mt-8">
            <h2 className="text-lg font-bold">Indicadores</h2>
            <p className="text-sm text-slate-400">Clique em um indicador para ver o histórico completo, a tendência, os extremos e a leitura.</p>
            {Object.keys(PERSPECTIVES).map((p) => {
              const l = list.filter((i) => i.perspective === p);
              return l.length ? (
                <div key={p} className="mt-5">
                  <h3 className="mb-2 font-semibold">{PERSPECTIVES[p]}</h3>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{l.map((i) => <Card key={i.id} i={i} onPick={setOpen} />)}</div>
                </div>
              ) : null;
            })}
          </section>
        </>
      )}

      {!empty && scope === "usa" && <Context data={data} />}

      <section className="mt-10">
        <h2 className="mb-3 text-lg font-semibold">Qualidade dos dados</h2>
        {missing.length > 0 && <p className="mb-2 text-xs text-amber-400">Séries sem dados nesta visão ({missing.length}): {missing.map((m) => m.name).join("; ")}. Veja a última coleta abaixo.</p>}
        {data.runs.length === 0 ? <p className="text-sm text-slate-500">Nenhuma execução registrada.</p> : (
          <table className="w-full text-left text-xs"><thead className="text-slate-400"><tr><th>Fonte</th><th>Início</th><th>Status</th><th>Linhas</th><th>Erro</th></tr></thead>
            <tbody>{data.runs.map((r, k) => (<tr key={k} className="border-t border-slate-800"><td className="py-1">{r.source}</td><td>{r.started_at.slice(0, 16)}</td><td>{r.status}</td><td>{r.rows}</td><td className="break-all text-red-400">{r.error ? r.error.slice(0, 300) : ""}</td></tr>))}</tbody></table>
        )}
      </section>
      {open && <DetailModal ind={open} recessions={data.recessions} onClose={() => setOpen(null)} />}
    </>
  );
}
