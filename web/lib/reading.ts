import type { Indicator, Stats } from "./data";

export const PERSPECTIVES: Record<string, string> = {
  kondratiev: "Kondratiev — preços, juros e produção", schumpeter: "Schumpeter — inovação", perez: "Perez — capital financeiro",
  freeman: "Freeman — paradigmas tecnoeconômicos", minsky: "Minsky — fragilidade financeira",
};
const MEANING: Record<string, string> = {
  kondratiev: "mais expansão (fase A)", schumpeter: "mais aceleração da inovação", perez: "mais calor financeiro (euforia)",
  freeman: "mais difusão do novo paradigma", minsky: "mais fragilidade financeira",
};
const fmt = (v: number, d = 2) => v.toLocaleString("pt-BR", { maximumFractionDigits: d });
const year = (s: string) => s.slice(0, 4);

/** What a reading is about: the level of the series or its change (e.g. 12-month inflation). */
export type Basis = { label: string; unit: string | null; value: number; ref_date: string; stats: Stats };

export function bases(i: Indicator): Basis[] {
  const out: Basis[] = [];
  if (i.view) out.push({ label: i.view.label, unit: i.view.unit, value: i.view.value, ref_date: i.view.ref_date, stats: i.view.stats });
  if (i.stats && i.value !== null && i.ref_date) out.push({ label: "Nível", unit: i.unit, value: i.value, ref_date: i.ref_date, stats: i.stats });
  return out;
}

/** Plain-language reading of one indicator against its own history. Descriptive only, never a forecast. */
export function reading(i: Indicator, b: Basis | undefined = bases(i)[0]): string[] {
  if (!b) return ["Sem dados coletados para esta série."];
  const s = b.stats;
  const u = b.unit ? ` ${b.unit}` : "";
  const what = b.label === "Nível" ? "O valor atual" : `A ${b.label.toLowerCase()}`;
  const out: string[] = [];
  out.push(
    `${what} (${fmt(b.value)}${u}, referência ${b.ref_date}) está no percentil ${fmt(s.percentile, 0)} da história disponível desde ${year(s.since)} — zona "${s.zone}". ` +
      `A máxima foi ${fmt(s.ath.value)} (${year(s.ath.date)}) e a mínima, ${fmt(s.atl.value)} (${year(s.atl.date)}).`,
  );
  const moves: string[] = [];
  if (s.year_ago !== null) moves.push(`há 1 ano: ${fmt(s.year_ago)} (diferença ${b.value - s.year_ago >= 0 ? "+" : "−"}${fmt(Math.abs(b.value - s.year_ago))})`);
  if (s.five_years_ago !== null) moves.push(`há 5 anos: ${fmt(s.five_years_ago)}`);
  if (moves.length) out.push(`Movimento: ${moves.join("; ")}.`);
  out.push(
    `Frente à tendência de longo prazo (filtro Hodrick-Prescott), está ${s.gap >= 0 ? "acima" : "abaixo"} em ${fmt(Math.abs(s.gap))}${u.replace(/\.$/, "")}. ` +
      `A tendência é uma referência de contexto e é revisada nas pontas da série.`,
  );
  if (i.view && b.label === "Nível") {
    out.push(`Esta série cresce ao longo do tempo, então o nível tende a ficar sempre perto da máxima. A leitura relevante é a ${i.view.label.toLowerCase()}.`);
  }
  if (i.polarity !== 0 && i.score !== null) {
    const how = i.transform === "chg12" ? "sobre a variação de 12 meses" : i.transform === "chg60" ? "sobre a variação de 5 anos" : "sobre o nível";
    out.push(
      `Na ótica ${PERSPECTIVES[i.perspective].split(" — ")[0]}, este indicador pontua ${fmt(i.score, 0)}/100 (${how}; ` +
        `${i.polarity > 0 ? "valores altos" : "valores baixos"} são lidos como ${MEANING[i.perspective]}).`,
    );
  }
  return out;
}
