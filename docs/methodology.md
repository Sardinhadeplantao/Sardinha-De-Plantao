# Metodologia (versão 0.4)

Tudo é descritivo e reproduzível. Nada aqui é previsão nem recomendação de investimento.

## 1. Dados
Fontes oficiais: FRED (EUA), Tesouro dos EUA, Banco Mundial, BIS, Shiller e SEC EDGAR. Cada série traz data de referência, data de coleta e frescor.
Frescor: **ok** (dentro do prazo da série), **atrasado** (até 2x o prazo), **obsoleto** (acima disso). Os prazos consideram como cada fonte data e publica:
mensais do FRED 90 dias (a referência é o 1º dia do mês e a divulgação sai semanas depois), trimestrais 270 a 280 dias, anuais do Banco Mundial 900 dias.
Recessões marcadas nos gráficos vêm do NBER (série USREC do FRED).

## 2. Estatísticas de cada indicador
- **Nível ou variação:** séries que crescem ao longo do tempo (índices de preço, produção, M2, Nasdaq, capex, patentes) são lidas pela **variação** de 12 meses
  ou de 5 anos; o nível delas fica sempre perto da máxima e não informa nada. Para elas, o cartão e a leitura mostram a variação, e o nível continua disponível no detalhe.
- **Percentil**: posição do valor atual entre todos os valores históricos da própria série. Zonas: <10 muito baixo, <33 baixo, <67 neutro, <90 alto, ≥90 muito alto.
- **Z-score**, **máxima/mínima** com data, **média histórica**.
- **Tendência (filtro Hodrick-Prescott)**: lambda 100 (anual), 1.600 (trimestral), 129.600 (mensal). É bilateral, portanto revisada nas pontas; serve só como contexto visual e **nunca entra em pontuações ou estados**.
- **Extremos atuais:** indicadores com dado não obsoleto no percentil ≥95 ou ≤5 da própria história (na base de leitura acima).

## 3. Índice por ótica (0 a 100)
1. Cada indicador é transformado: nível, variação de 12 meses ou variação de 5 anos (`SCORING` em `jobs/kondratiev/analytics.py`).
2. Calcula-se o **percentil em janela expansiva** (só dados até aquela data, sem olhar o futuro). Mínimo de 15 observações (anual), 28 (trimestral) e 60 (mensal);
   séries com histórico curto, como o capex das grandes de tecnologia (31 trimestres), pontuam só nos períodos mais recentes.
3. Se a polaridade é negativa, inverte-se (100 menos o percentil).
4. **Subgrupos equilibrados:** o índice é a média dos subgrupos, e cada subgrupo é a média dos seus indicadores (`GROUPS`). Assim, cinco séries de juros, muito
   parecidas entre si, não pesam mais que os preços ou a atividade. Subgrupos: Kondratiev = preços, juros, atividade; Minsky = alavancagem, preço do risco,
   curva e política; Perez = valuation, investimento. Exige pelo menos 3 indicadores no mês, senão "dados insuficientes".
5. Defasagem de publicação assumida: anual 12 meses, trimestral 3, mensal 1. Uma leitura sai do cálculo quando fica velha demais: anuais 36 meses após o fim
   do ano de referência, trimestrais 12 meses após o trimestre, mensais 4 meses e diárias ou semanais 3 meses.
6. **Data do índice:** cada índice mostra o mês do seu último valor. Se esse mês tem mais de 3 meses, o índice é marcado como desatualizado.

| Ótica | O que 100 significa | Estados (regra) |
|---|---|---|
| Kondratiev | expansão plena de preços, juros e produção | ≥60 Fase A; 40–60 Transição; <40 Fase B |
| Schumpeter | insumos de inovação acelerando | ≥60 Cluster em formação; 40–60 Estável; <40 Desaceleração |
| Perez | calor financeiro (valuation: capitalização/PIB, indicador Buffett, CAPE, Nasdaq; investimento: capex das grandes de tecnologia) | ≥75 Frenesi; queda de 10+ pontos após pico ≥75 nos últimos 24 meses = Inflexão; 40–75 Intermediária; <40 Implantação |
| Freeman | renováveis subindo, CO₂ e intensidade energética caindo | ≥60 Difusão em curso; 40–60 Incipiente/mista; <40 Paradigma vigente |
| Minsky | fragilidade máxima (alavancagem, spreads, condições financeiras, curva invertida) | ≥67 Alta; 33–67 Média; <33 Baixa |

Os limiares são convenções simples, não estimativas econométricas. Mudar qualquer regra exige nova versão da metodologia.

## 4. Validação histórica (backtest descritivo)
Para cada ótica dos EUA, compara-se a média do índice nos 24 meses anteriores ao início de cada recessão do NBER com a média fora de recessões.
Para Minsky (limiar 60) e Perez (limiar 70) mede-se também quantas recessões foram precedidas por um cruzamento do limiar e a taxa de alarmes falsos.
Limites: dentro da amostra, dados revisados (não são os divulgados na época) e poucas recessões. Um resultado fraco é informação válida.

## 5. Contexto de valuation
Retorno real anualizado do S&P 500 (retorno total real de Shiller) em 1, 5 e 10 anos depois dos meses em que o CAPE esteve dentro de ±10 pontos percentuais do percentil atual, contra todos os meses.
Descritivo, dentro da amostra, janelas sobrepostas (poucos episódios independentes). Não é previsão. Quando o arquivo público do Shiller está desatualizado, o site avisa.

## 6. Investimento em IA (EDGAR)
Soma de Microsoft, Alphabet, Amazon, Meta e Oracle: capex (PaymentsToAcquirePropertyPlantAndEquipment ou PaymentsToAcquireProductiveAssets, conforme a empresa e o ano)
e fluxo de caixa operacional (NetCashProvidedByUsedInOperatingActivities) em quatro trimestres móveis. Os trimestres são reconstruídos por diferença dos valores
acumulados no ano, usando só períodos que começam no início do ano fiscal; trimestres fiscais são mapeados ao trimestre-calendário mais próximo.

## 7. Alertas
A cada atualização na branch principal, compara-se com o `data.json` publicado antes. Abre-se uma Issue no GitHub quando: uma ótica dos EUA muda de estado, a curva 10 anos − 2 anos inverte ou volta a ser positiva,
o hiato de crédito do BIS cruza 10 p.p., ou alguma fonte falha na coleta. Quando a versão da metodologia muda, mudanças de estado não geram alerta (refletem regras novas, não dados).

## 8. Histórico de versões
- 0.4: subgrupos equilibrados; leitura por variação para séries com tendência; data e aviso de desatualização dos índices; extremos atuais; indicador Buffett (Fed Z.1) e Nasdaq no lugar
  da variação anual de ações do Banco Mundial (parada em 2022); leituras anuais saem do índice 36 meses após o ano de referência; prazos de frescor ajustados ao calendário de publicação.
- 0.3: validação histórica, valuation, EDGAR, alertas.
- 0.2: índices por ótica e estados.

## 9. Limites que o sistema declara
- Há poucos ciclos longos completos (2,5 a 3): qualquer inferência sobre fases tem evidência estatística limitada.
- A datação da "6ª onda" é interpretativa.
- Os indicadores do Banco Mundial têm atraso de 1 a 5 anos; o arquivo público do Shiller pode ficar meses sem atualização.
- A visão global tem menos indicadores; quando há menos de 3 por ótica, o sistema mostra "dados insuficientes".
