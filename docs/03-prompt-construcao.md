# Prompt de construção (Kondratiev Monitor)

````
Você é um engenheiro sênior full-stack e de dados quantitativos. Construa o "Kondratiev Monitor": sistema web que monitora ciclos econômicos de longa duração sob 5 óticas (Kondratiev, Schumpeter, Perez, Freeman, Minsky) com dados oficiais atualizados automaticamente. Antes de codar, apresente um plano curto com suas decisões e confirme comigo. Depois execute fase por fase, parando ao fim de cada uma para validação.

## OBJETIVO
Leitura objetiva, auditável e atualizada do ponto do ciclo longo, para apoiar alocação estratégica (10–20 anos), SEM previsões nem recomendações de investimento.

## STACK
- Frontend: Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts. Só lê do banco; nunca chama fontes externas nem expõe chaves.
- Banco: Supabase (Postgres).
- Jobs: Python 3.11 (pandas, statsmodels, scipy, requests, openpyxl) via GitHub Actions cron. Diário (mercado/juros), semanal (trimestrais), mensal (resto).
- Segredos: FRED_API_KEY, EIA_API_KEY, SEC_USER_AGENT.
- Interface em português (Brasil); código e comentários em inglês.

## FONTES
FRED (120 req/min, rate limiter + backoff), BIS (stats.bis.org/api/v1 e bulk CSV), Shiller (ie_data.xls), US Treasury, OECD (sdmx.oecd.org/public/rest/data), Banco Mundial, SEC EDGAR companyfacts (User-Agent), EIA/Ember/IRENA. Sem scraping de Yahoo. VALIDE cada ID de série via API da fonte e registre a decisão.

## MODELO DE DADOS
series_catalog (id, perspective, layer[structure|regime|timing], source, code, country, unit, frequency, transform, role[procyclical|fragility|valuation_excess], rationale, stale_after_days); observations (series_id, ref_date, value, as_of, vintage, is_provisional); derived (series_id, date, trend, cycle_gap, percentile, zscore, momentum, acceleration); scores (date, perspective, state, value, coverage, uncertainty, methodology_version); runs (source, started_at, status, rows, error). Ingestões idempotentes (upsert) e registradas em runs.

## CATÁLOGO INICIAL (validar IDs)
- Kondratiev: CPIAUCSL e juros longos Shiller, DGS10, DFII10, FEDFUNDS, PPIACO, DCOILWTICO, INDPRO, inflação global (WB).
- Schumpeter: P&D % PIB (OECD/WB), patentes (WB), novos negócios (FRED), P&D de big techs (EDGAR).
- Perez: Buffett (Z.1/PIB), CAPE, Wilshire 5000/PIB, investimento em TI e software (BEA), capex dos hyperscalers / fluxo de caixa operacional (EDGAR).
- Freeman: renováveis na geração (Ember/EIA), intensidade energética (WB), capacidade solar/eólica (IRENA), preço de energia.
- Minsky: BIS credit gap, DSR, total credit, BAA10Y, high yield, T10Y2Y, T10Y3M, TDSP, dívida das famílias/PIB, NFCI, SLOOS.

## METODOLOGIA (documentar em /docs/methodology.md)
1. Transformações: real, % PIB, log.
2. Sinal: percentil com janela expansiva (sem look-ahead), z-score do gap, momentum 1a/3a, aceleração, histerese.
3. Ciclo: HP (lambda BIS) para gaps; Christiano-Fitzgerald e FFT para banda de 40–60 anos.
4. Estado por ótica com regras versionadas: Kondratiev A/B; Schumpeter cluster sim/não e intensidade; Perez irrupção/frenesi/inflexão/sinergia/maturidade; Freeman custo caindo e difusão; Minsky baixa/média/alta.
5. Sem score mestre por padrão: 3 camadas + 5 estados. Composto opcional (PCA/pesos) com incerteza e cobertura.
6. Cada indicador exibe valor, as_of, frequência, frescor (ok/atrasado/obsoleto), percentil, zona e justificativa.

## TELAS
1. Visão geral (5 óticas + 3 camadas, cobertura, última atualização por fonte). 2. Página por ótica. 3. Detalhe do indicador (histórico, HP, zonas, ATH/ATL, fonte, vintage). 4. Qualidade de dados. 5. (Fase 4) Alertas e backtest.

## OPERAÇÃO E GOVERNANÇA
Alerta por e-mail em falha de ingestão ou série obsoleta; methodology_version em cada score, nunca sobrescrever; testes unitários, de não-look-ahead e de contrato por fonte. Aviso permanente: "Leitura de contexto baseada em dados públicos. Não é recomendação de investimento. Evidência estatística sobre ciclos de Kondratiev é limitada."

## FASES (parar ao fim de cada)
0. Fundação (repo, banco, ingestão, FRED + WB, 1 indicador com as_of e cron). 1. Dados frescos (~40 indicadores, frescor). 2. Analytics. 3. Empresas e estrutura (EDGAR, OECD, energia). 4. Alertas, backtest com vintage, multi-geografia. 5. Cenários de alocação.

## ACEITE
Nenhum número sem fonte, as_of e frescor. Nenhuma chave no cliente. Regras documentadas e reproduzíveis. Falha de fonte não derruba o app: mostra último dado com alerta de obsolescência.

Comece pelo plano e liste as dúvidas antes da Fase 0.
````
