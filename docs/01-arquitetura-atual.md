# Ondas de Kondratiev — Monitor Global
## Arquitetura, Metodologia e Roadmap (estado atual)

Sistema de monitoramento dos ciclos longos (~40–60 anos) sob 5 óticas: Kondratiev (preços/juros), Schumpeter (inovação), Perez (capital financeiro vs. produtivo), Freeman (paradigmas tecnoeconômicos) e Minsky (fragilidade financeira). Objetivo: embasar alocação estratégica de ativos com dados oficiais.

## 1. Arquitetura
- Stack: React 18 + Vite + Tailwind + shadcn/ui, Recharts, React Router, Base44 (auth, entidades, hosting). Sem backend (plano Free): toda a lógica roda no cliente.

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Dados | `src/lib/worldBankApi.js` | Fetch do Banco Mundial; tendência, sinal, percentil, estatísticas |
| Catálogo | `src/lib/indicatorCatalog.js` | 5 óticas + 18 indicadores (código, país, unidade, `upswingWhen`, justificativa) |
| UI | `PerspectivePanel`, `IndicatorCard`, `IndicatorDetail`, `ConsolidatedChart`, `WaveAssessment` | Painéis, cards, modal histórico, composto, leitura da onda |
| Orquestração | `src/pages/Dashboard.jsx` | Estado, snapshots, históricos, refresh |
| Armazenamento | `base44/entities/IndicatorSnapshot.jsonc` | Persistência dos snapshots |

Fluxo: na carga lê snapshots da entidade e busca históricos 1960–2024 (18 em paralelo); no "Atualizar" busca 2 pontos, recalcula sinal e grava um lote (`bulkCreate`); no clique abre o modal com o histórico em cache.

## 2. Indicadores (18, todos agregados globais `WLD`)
- **Kondratiev:** `FP.CPI.TOTL.ZG`, `NY.GDP.DEFL.KD.ZG`, `NY.GDP.MKTP.KD.ZG`, `FR.INR.RINR` (todos rising)
- **Schumpeter:** `GB.XPD.RSDV.GD.ZS`, `IP.PAT.RESD`, `SP.POP.SCIE.RD.P6`, `TX.VAL.TECH.MF.ZS` (rising)
- **Perez:** `CM.MKT.LCAP.GD.ZS`, `CM.MKT.TRAD.GD.ZS`, `TX.VAL.ICT.GD.ZS`, `CM.MKT.INDX.ZG` (rising)
- **Freeman:** `EG.FEC.RNEW.ZS` (rising), `EN.ATM.CO2E.PC` (falling), `EG.EGY.PRIM.PP.KD` (falling)
- **Minsky:** `FS.AST.PRVT.GD.ZS` (falling), `FS.AST.DOMS.GD.ZS` (falling), `FB.BNK.CAPA.ZS` (rising)

## 3. Metodologia atual
- **Sinal:** `trend = latest > previous ? up : latest < previous ? down : flat`; `signal = trend == upswingWhen ? expansion : flat ? neutral : contraction` (2 últimos pontos anuais).
- **Leitura da 6ª Onda:** expansão > contração+neutro → Fase A; contração > expansão+neutro → Fase B; senão transição.
- **Índice do ciclo:** min-max 0–100 por série, inversão se `falling`, média por ano (mín. 3 indicadores).
- **Detalhe:** atual, 1 ano atrás, ATH/ATL, tercis como zonas, marcador de percentil.

## 4. Fonte atual
Banco Mundial: `https://api.worldbank.org/v2/country/WLD/indicator/{CODE}?format=json&date=1960:2024&per_page=200`. Sem chave, CORS liberado, anual.

## 5. Pontos fortes
Integração multi-teórica; dados oficiais; metodologia padronizada e auditável; contexto histórico clicável; composto visual; infraestrutura leve; responsivo.

## 6. Limitações
1. Defasagem de 1–2 anos (intrínseca à fonte). 2. Frequência anual. 3. Sem dados de mercado em tempo real. 4. Sem valuation (CAPE, Q de Tobin, ERP, etc.). 5. Sinal heurístico de 2 pontos (já deu 12/12 contração). 6. Sem extração formal de ciclo (HP, espectral, Bry-Boschan, band-pass). 7. Composto min-max com pesos iguais. 8. Zonas em tercis arbitrários. 9. Sem indicador de cobertura. 10. Só geografia global. 11. Sem alertas, backtest ou alocação. 12. Inversão por `upswingWhen` é um patch.

## 7. Defasagem: causa e solução
O Banco Mundial publica agregados anuais com lag de 1–2 anos. Fontes para resolver (exigem backend + segredos, a chave não pode viver no cliente): FRED (diária/mensal), Shiller (mensal), OECD (trimestral, sem chave), BIS (trimestral), IMF (mensal/trimestral). Estratificar: diário (timing), trimestral (regime), anual (estrutura/Kondratiev). O Banco Mundial é o teto de frescor no plano atual.

## 8. Roadmap resumido
- Dados: FRED, Shiller, OECD, BIS via backend; conjunto de valuation; `as_of` e alerta de staleness.
- Ciclo: HP, FFT, Christiano-Fitzgerald (40–60 anos), Bry-Boschan, credit-to-GDP gap.
- Sinal: z-score, regime (Markov-switching), aceleração, thresholds fundamentados.
- Composto: pesos teóricos ou PCA, sub-índices por ótica, banda de incerteza.
- Operação: cron, alertas, backtest (1929, 1973, 2000, 2008, 2020), multi-geografia, overlay de alocação.
- Governança: proveniência, versionamento de metodologia, auditoria.

## 9. Schema `IndicatorSnapshot`
Campos: `indicator_id`, `perspective` (kondratiev|schumpeter|perez|freeman|minsky), `name`, `value`, `previous_value`, `unit`, `trend` (up|down|flat), `signal` (expansion|contraction|neutral), `source`, `source_url`, `date`, `rationale`, `batch_id`. Obrigatórios: `indicator_id`, `perspective`, `name`, `value`, `source`.
