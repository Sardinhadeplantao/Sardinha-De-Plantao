import { loadIndicators, loadRuns, type Indicator } from "@/lib/db";

export const dynamic = "force-dynamic";

const PERSPECTIVES: Record<string, string> = {
  kondratiev: "Kondratiev — preços, juros e produção", schumpeter: "Schumpeter — inovação", perez: "Perez — capital financeiro",
  freeman: "Freeman — paradigmas tecnoeconômicos", minsky: "Minsky — fragilidade financeira",
};
const LAYERS: Record<string, string> = { structure: "estrutura", regime: "regime", timing: "timing" };
const BADGE = { ok: "bg-emerald-900 text-emerald-300", atrasado: "bg-amber-900 text-amber-300", obsoleto: "bg-red-900 text-red-300" };
const fmt = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 2 });

function Card({ i }: { i: Indicator }) {
  const delta = i.value !== null && i.previous !== null ? i.value - i.previous : null;
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium">{i.name}</h3>
        {i.status && <span className={`rounded px-2 py-0.5 text-xs ${BADGE[i.status]}`}>{i.status}</span>}
      </div>
      {i.value === null ? (
        <p className="mt-3 text-sm text-slate-500">Sem dados. A ingestão ainda não rodou para esta série.</p>
      ) : (
        <>
          <p className="mt-2 text-2xl font-semibold">{fmt(i.value)} <span className="text-sm font-normal text-slate-400">{i.unit}</span></p>
          {delta !== null && <p className="text-xs text-slate-400">{delta >= 0 ? "▲" : "▼"} {fmt(Math.abs(delta))} vs. observação anterior</p>}
          <p className="mt-2 text-xs text-slate-400">Referência: {i.refDate} · coletado em {i.asOf?.slice(0, 10)}</p>
        </>
      )}
      <p className="mt-2 text-xs text-slate-500">{i.rationale}</p>
      <p className="mt-2 text-xs text-slate-500">
        {i.source.toUpperCase()} · {i.frequency} · {LAYERS[i.layer]} ·{" "}
        {i.sourceUrl && <a className="underline" href={i.sourceUrl} target="_blank" rel="noreferrer">{i.code}</a>}
      </p>
    </div>
  );
}

export default async function Home() {
  let indicators: Indicator[] = [], runs: Awaited<ReturnType<typeof loadRuns>> = [], error: string | null = null;
  try { [indicators, runs] = await Promise.all([loadIndicators(), loadRuns()]); }
  catch { error = "Não foi possível ler o banco de dados. Verifique DATABASE_URL e se a ingestão já criou as tabelas."; }
  const groups = Object.keys(PERSPECTIVES).map((p) => [p, indicators.filter((i) => i.perspective === p)] as const).filter(([, l]) => l.length);

  return (
    <>
      <h1 className="text-2xl font-bold">Kondratiev Monitor</h1>
      <p className="mt-1 text-sm text-slate-400">Ciclos econômicos de longa duração sob 5 óticas, com dados oficiais e frescor visível.</p>
      {error && <p className="mt-6 rounded border border-red-800 bg-red-950 p-3 text-sm text-red-300">{error}</p>}
      {!error && indicators.length === 0 && (
        <p className="mt-6 rounded border border-slate-700 p-3 text-sm text-slate-300">
          Banco vazio. Rode a ingestão (<code>python -m kondratiev.ingest</code> em <code>jobs/</code>) para carregar dados reais.
        </p>
      )}
      {groups.map(([p, list]) => (
        <section key={p} className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">{PERSPECTIVES[p]}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{list.map((i) => <Card key={i.id} i={i} />)}</div>
        </section>
      ))}
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-semibold">Qualidade dos dados</h2>
        {runs.length === 0 ? <p className="text-sm text-slate-500">Nenhuma execução registrada.</p> : (
          <table className="w-full text-left text-xs"><thead className="text-slate-400"><tr><th>Fonte</th><th>Início</th><th>Status</th><th>Linhas</th><th>Erro</th></tr></thead>
            <tbody>{runs.map((r, k) => (<tr key={k} className="border-t border-slate-800"><td className="py-1">{r.source}</td><td>{r.started_at.slice(0, 16)}</td><td>{r.status}</td><td>{r.rows}</td><td className="text-red-400">{r.error}</td></tr>))}</tbody></table>
        )}
      </section>
    </>
  );
}
