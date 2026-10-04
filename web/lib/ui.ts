import { GROUP_LABELS, PERSPECTIVES } from "./reading";

// Lens identity colors: the validated categorical palette (dark steps), one fixed hue per lens. "ciclo" is not a lens: neutral gray.
export const TONE: Record<string, string> = {
  kondratiev: "#3987e5", schumpeter: "#d95926", perez: "#199e70", freeman: "#c98500", minsky: "#d55181", ciclo: "#8b95a5",
};
export const LENSES = Object.keys(PERSPECTIVES);
export const SHORT = (p: string) => (GROUP_LABELS[p] ?? p).split(" — ")[0];
export const fmt = (n: number, d = 2) => n.toLocaleString("pt-BR", { maximumFractionDigits: d });
export const signed = (n: number, d = 0) => `${n >= 0 ? "+" : "−"}${fmt(Math.abs(n), d)}`;
