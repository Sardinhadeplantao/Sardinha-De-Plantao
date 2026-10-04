"""Alerts: compare the previous published data.json with the new one and write a markdown body when something
that matters changed. Usage: python -m kondratiev.alerts prev.json new.json out.md  (out.md is written only if there are alerts)."""
import json
import sys

LABELS = {"kondratiev": "Kondratiev", "schumpeter": "Schumpeter", "perez": "Perez", "freeman": "Freeman", "minsky": "Minsky"}


def _value(data, ind_id):
    for i in data.get("indicators", []):
        if i["id"] == ind_id:
            return i.get("value")
    return None


def compare(prev, new):
    out = []
    same_method = prev.get("methodology_version") == new.get("methodology_version")
    for p, label in LABELS.items():
        if not same_method:
            break
        a = prev.get("indices", {}).get("usa", {}).get(p, {}).get("state")
        b = new.get("indices", {}).get("usa", {}).get(p, {}).get("state")
        if a and b and a != b:
            v = new["indices"]["usa"][p].get("value")
            out.append(f"**{label} (EUA)** mudou de estado: _{a}_ → **{b}** (índice {v:.0f}/100)." if v is not None else f"**{label}**: {a} → {b}.")
    a, b = _value(prev, "fred_t10y2y"), _value(new, "fred_t10y2y")
    if a is not None and b is not None and (a < 0) != (b < 0):
        out.append("**Curva de juros 10 anos − 2 anos (EUA)** " + (f"inverteu (agora {b:.2f} p.p.)." if b < 0 else f"voltou a ficar positiva ({b:.2f} p.p.)."))
    gap_a, gap_b = _value(prev, "bis_us_credit_gap"), _value(new, "bis_us_credit_gap")
    if gap_a is not None and gap_b is not None and (gap_a >= 10) != (gap_b >= 10):
        out.append(f"**Hiato de crédito sobre o PIB (BIS, EUA)** {'ultrapassou' if gap_b >= 10 else 'voltou abaixo de'} 10 p.p. (agora {gap_b:.1f}).")
    sa, sb = _value(prev, "x_sahm"), _value(new, "x_sahm")
    if sa is not None and sb is not None and (sa >= 0.5) != (sb >= 0.5):
        out.append(f"**Regra de Sahm (EUA)** {'acionada' if sb >= 0.5 else 'desligada'}: agora {sb:.2f} p.p. (limiar 0,5).")
    failed = [r for r in new.get("runs", []) if r.get("status") == "failed"]  # each run starts from an empty database
    if failed:
        out.append("Falha de coleta em: " + ", ".join(sorted({r["source"] for r in failed})) + ".")
    if out and not same_method:  # a methodology change alone is not an alert; just explain it next to real ones
        out.insert(0, f"Metodologia atualizada ({prev.get('methodology_version') or '?'} → {new.get('methodology_version')}): "
                      "mudanças de estado nesta atualização refletem as regras novas e não são alertadas.")
    return out


if __name__ == "__main__":
    prev_path, new_path, out_path = sys.argv[1:4]
    try:
        prev = json.load(open(prev_path))
    except (OSError, ValueError):
        prev = {}
    new = json.load(open(new_path))
    items = compare(prev, new) if prev.get("indices") else []
    if items:
        body = "Alerta automático do Kondratiev Monitor.\n\n" + "\n".join(f"- {i}" for i in items) + \
            "\n\n_Leitura de contexto baseada em dados públicos. Não é recomendação de investimento._\n"
        open(out_path, "w").write(body)
        print(body)
    else:
        print("no alerts")
