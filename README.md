# Kondratiev Monitor

Monitor de ciclos econômicos de longa duração (Kondratiev, Schumpeter, Perez, Freeman, Minsky) com dados oficiais reais.
Documentação em `docs/`. **Nenhum dado simulado:** o app só exibe o que a ingestão coletou das fontes.

## Estado: Fase 0 (fundação)
- `jobs/` — ingestão em Python (FRED, Banco Mundial), upsert idempotente, auditoria em `runs`, frescor. SQLite local ou Postgres.
- `web/` — Next.js; só lê do banco. Cards com valor, data de referência, `as_of`, frescor, fonte e justificativa; painel de qualidade.
- `.github/workflows/ingest.yml` — cron diário, roda com acesso livre às fontes.

## Colocar no ar (dados reais)
1. Crie um projeto Supabase e copie a connection string (Postgres).
2. Obtenha uma chave gratuita do FRED: https://fred.stlouisfed.org/docs/api/api_key.html
3. No GitHub, em Settings → Secrets → Actions, crie `DATABASE_URL` e `FRED_API_KEY`.
4. Rode o workflow "Ingest data" (Actions → Run workflow). Ele valida os IDs das séries nas APIs reais antes de ingerir.
5. Faça deploy de `web/` (ex.: Vercel) com a variável `DATABASE_URL` (somente leitura, se possível).

## Local
```
cd jobs && pip install -r requirements.txt && pytest && FRED_API_KEY=... python -m kondratiev.ingest
cd web && npm install && npm run dev
```
Os testes usam respostas HTTP falsas só para validar o código; esses dados nunca vão ao banco do app.
