# Plano de evolução

Achados sobre as fontes (validar antes de usar): FRED exige chave gratuita (120 req/min), mantida no backend; BIS tem API SDMX e bulk CSV com credit-to-GDP gaps prontos (HP); Shiller `ie_data.xls` mensal desde 1881 (últimas observações provisórias); OECD SDMX sem chave; Tesouro dos EUA publica a curva sem chave.

## 1. Princípios
1. Separar por escala de tempo: estrutura (anual), regime (trimestral), timing (diário/mensal), cada uma com score próprio, sem composto único.
2. Cada ótica responde a uma pergunta própria: Kondratiev fase A/B; Schumpeter cluster em formação; Perez instalação/inflexão/implantação; Freeman insumo-chave barato e universal; Minsky fragilidade baixa/média/alta.
3. Sinal estatístico: percentil sem look-ahead, z-score do gap, momentum, aceleração, histerese.
4. Todo dado com `as_of`, frequência e frescor; todo score com cobertura.

## 2. Fontes
| Fonte | Acesso | Frequência | Traz |
|---|---|---|---|
| FRED | chave grátis | diária–trimestral | CPI, Fed Funds, DGS10/2, T10Y2Y, spreads, M2, INDPRO, Z.1 |
| BIS | sem chave | trimestral | credit gap, total credit, DSR |
| Shiller | arquivo | mensal | CAPE, preço, lucros, dividendos desde 1871 |
| US Treasury | sem chave | diária | curva |
| OECD SDMX | sem chave | mensal–anual | CLI, P&D, juros, ações |
| Banco Mundial | sem chave | anual | camada estrutural |
| SEC EDGAR | User-Agent com contato | trimestral | capex, P&D, fluxo de caixa |
| EIA/Ember/IRENA | EIA com chave | mensal/anual | matriz elétrica, renováveis |
| BCB SGS/IBGE | sem chave | mensal | Brasil (fase 4) |

Cuidados: sem Yahoo (não oficial); só provedor pago se o timing diário for essencial. IDs de série vêm de memória: validar via API e conferir termos de uso.

## 3. Arquitetura
Fontes → workers Python agendados (GitHub Actions/Supabase cron) → Postgres (Supabase) → workers de analytics (HP, CF, z-score, regime) → Next.js (só lê do banco). Segredos (`FRED_API_KEY`, `EIA_API_KEY`, `SEC_USER_AGENT`) só no backend.

## 4. Modelo de dados
`series_catalog`, `observations` (com `as_of`, vintage, provisório), `derived`, `scores` (com cobertura, incerteza, versão da metodologia), `runs` (auditoria).

## 5. Pipeline analítico
Transformações → ciclo (HP para gaps, CF e FFT para banda 40–60 anos) → sinais → estado por ótica com regras versionadas → regime probabilístico opcional → backtest com vintage (ALFRED).

## 6. Limites a declarar
Poucos ciclos completos (risco de sobreajuste); viés de borda do HP (usar versões unilaterais no backtest); datação das ondas é interpretativa. Leitura de contexto, não previsão nem recomendação.

## 7. Roadmap
| Fase | Entrega | Aceite |
|---|---|---|
| 0 | Repo, banco, ingestão, FRED + WB | 1 indicador com `as_of`, atualizado por cron |
| 1 | FRED, Treasury, Shiller, BIS, WB; ~40 indicadores | Nenhum card sem `as_of`; alerta de staleness |
| 2 | Percentil, z-score, HP/CF, estado por ótica | Cada ótica com estado, cobertura, justificativa |
| 3 | EDGAR, OECD, energia | Capex de IA vs. caixa operacional trimestral |
| 4 | Alertas, backtest, multi-geografia | Relatório de backtest versionado |
| 5 | Cenários de alocação | Premissas explícitas e aviso de não recomendação |
