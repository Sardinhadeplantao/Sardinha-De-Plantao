# Kondratiev Monitor

Monitor de ciclos econômicos de longa duração (Kondratiev, Schumpeter, Perez, Freeman, Minsky), aplicado aos Estados Unidos.
**Dados oficiais reais, sem nenhum dado simulado.** Site: https://sardinhadeplantao.github.io/Sardinha-De-Plantao/

## O que o site mostra
- **Leitura consolidada** com o estado de cada ótica (por exemplo, "Fragilidade média"), regras documentadas em [`docs/methodology.md`](docs/methodology.md).
- **Índice de 0 a 100 por ótica ao longo do tempo**, com as recessões dos EUA marcadas.
- **Detalhe de cada indicador:** histórico completo, tendência de longo prazo, percentil, máxima e mínima históricas, frescor e leitura em texto.
- **Contexto de valuation** (retornos históricos após CAPE parecido) e **validação histórica** (os índices subiram antes das recessões?).
- **Painel de qualidade** com o resultado de cada coleta.

## Fontes
FRED (PIB real, inflação, juros, crédito, desemprego, produtividade, semicondutores, commodities, cobre, VIX, crédito bancário, inadimplência, seguro-desemprego, licenças de construção, indicador Buffett do Fed, S&P 500, Nasdaq, P&D, novos negócios), Tesouro dos EUA, Banco Mundial (séries estruturais), BIS (crédito total, hiato de crédito, serviço da dívida), Shiller (CAPE, estendido até o mês atual com S&P 500 e CPI), SEC EDGAR (investimento das grandes de tecnologia) e Ember (eletricidade mensal: renováveis, eólica e solar, intensidade de CO₂, demanda). Séries calculadas: juro real do Fed, prêmio de risco das ações, regra de Sahm e probabilidade de recessão pela curva de juros.

## Como funciona
Todo dia o GitHub Actions (`.github/workflows/ingest.yml`) coleta os dados, calcula os índices, monta o site e publica no GitHub Pages. Sem servidor e sem banco externo.
Quando uma ótica muda de estado, a curva de juros inverte, o hiato de crédito cruza 10 p.p. ou uma fonte falha, abre-se uma **Issue** com o rótulo `alerta`.

- `jobs/` — coleta e cálculos em Python (testes em `jobs/tests`).
- `web/` — site Next.js estático.
- `docs/` — metodologia, arquitetura e plano.

## Configuração (já feita; para referência)
- Settings → Pages → Source: **GitHub Actions**.
- Segredo `FRED_API_KEY` (chave gratuita do FRED).
- Segredo opcional `SEC_USER_AGENT`: identificação com e-mail de contato exigida pela SEC (padrão: e-mail no-reply do GitHub do dono do repositório).

## Atualizar na hora
Aba **Actions → Atualizar dados e publicar site → Run workflow**.

## Local
```
cd jobs && pip install -r requirements.txt && pytest
FRED_API_KEY=... python -m kondratiev.ingest && python -m kondratiev.export ../web/data/data.json
mkdir -p ../web/public && cp ../web/data/data.json ../web/public/data.json   # o detalhe carrega o histórico daqui
cd ../web && npm install && npm run dev
```
Os testes usam respostas HTTP e dados sintéticos só para validar o código; nada disso vai ao site.

*Leitura de contexto baseada em dados públicos. Não é recomendação de investimento. A evidência estatística sobre ondas de Kondratiev é limitada.*
