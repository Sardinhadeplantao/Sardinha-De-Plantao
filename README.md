# Kondratiev Monitor

Monitor de ciclos econômicos de longa duração (Kondratiev, Schumpeter, Perez, Freeman, Minsky) com dados oficiais reais.
**Nenhum dado simulado:** o site só exibe o que foi coletado das fontes oficiais. Documentação em `docs/`.

## Como funciona
Todo dia o GitHub Actions (`.github/workflows/ingest.yml`) coleta os dados, gera `web/data/data.json`, monta o site e publica no GitHub Pages.
Sem banco de dados e sem servidor.

- `jobs/` — coleta em Python (Banco Mundial, Tesouro dos EUA, FRED opcional), frescor, testes.
- `web/` — site Next.js estático.

## Fontes
Banco Mundial e Tesouro dos EUA (sem chave). FRED é opcional: só entra se existir o segredo `FRED_API_KEY`.

## Configuração (uma vez)
1. Settings → Secrets and variables → Actions → New repository secret: `FRED_API_KEY` (opcional).
2. Settings → Pages → Source: **GitHub Actions**.
3. Junte este código na branch `main`. A publicação roda sozinha e depois todo dia.

## Local
```
cd jobs && pip install -r requirements.txt && pytest
python -m kondratiev.ingest && python -m kondratiev.export ../web/data/data.json
cd ../web && npm install && npm run dev
```
Os testes usam respostas HTTP falsas só para validar o código; esses dados nunca vão ao site.

*Leitura de contexto baseada em dados públicos. Não é recomendação de investimento.*
