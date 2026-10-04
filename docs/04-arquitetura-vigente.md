# Arquitetura vigente

```
Fontes oficiais ──► jobs/ (Python, diário no GitHub Actions)
  FRED, Tesouro,        ingest  → SQLite temporário (upsert idempotente, tabela runs)
  Banco Mundial, BIS,   export  → analytics (percentil, HP, índices, backtest, valuation) → data.json
  Shiller, EDGAR        alerts  → compara com o data.json publicado → Issue no GitHub
                          │
                          ▼
                     web/ (Next.js estático) ──► GitHub Pages
```

| Parte | Arquivo | Função |
|---|---|---|
| Catálogo | `jobs/kondratiev/catalog.py` | 57 séries: escopo (EUA/global/contexto), ótica, camada, fonte, justificativa, prazo de frescor |
| Fontes | `jobs/kondratiev/sources/*.py` | uma por fonte; erros de rede não vazam chaves |
| Coleta | `jobs/kondratiev/ingest.py` | isola falhas por fonte, aborta fonte inalcançável, registra cada execução |
| Análise | `jobs/kondratiev/analytics.py` | percentil expansivo (sem olhar o futuro), HP, índices, estados, backtest, valuation |
| Exportação | `jobs/kondratiev/export.py` | gera `data.json` (também publicado em `/data.json`) |
| Alertas | `jobs/kondratiev/alerts.py` | regras de mudança de estado |
| Site | `web/app`, `web/components`, `web/lib` | leitura consolidada, índices, detalhe, contexto, qualidade |
| Automação | `.github/workflows/ingest.yml` | testes, coleta, alertas, build e deploy (deploy só na `main`) |

Princípios: nenhum número sem fonte, data de referência e frescor; falha de uma fonte não derruba o site; regras versionadas (`METHODOLOGY_VERSION`).

> Os arquivos `01` a `03` registram o ponto de partida e o plano original (Base44, Supabase) e permanecem como histórico.
