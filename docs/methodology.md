# Metodologia (versão 0.3)

Tudo é descritivo e reproduzível. Nada aqui é previsão nem recomendação de investimento.

## 1. Dados
Fontes oficiais: FRED (EUA), Tesouro dos EUA, Banco Mundial. Cada série traz data de referência, data de coleta e frescor.
Frescor: **ok** (dentro do prazo da série), **atrasado** (até 2x o prazo), **obsoleto** (acima disso).
Recessões marcadas nos gráficos vêm do NBER (série USREC do FRED).

## 2. Estatísticas de cada indicador
- **Percentil**: posição do valor atual entre todos os valores históricos da própria série. Zonas: <10 muito baixo, <33 baixo, <67 neutro, <90 alto, ≥90 muito alto.
- **Z-score**: desvios-padrão da média histórica. **Máxima/mínima**: extremos históricos com data.
- **Tendência (filtro Hodrick-Prescott)**: lambda 100 (anual), 1.600 (trimestral), 129.600 (mensal). É bilateral, portanto revisada nas pontas; serve só como contexto visual e **nunca entra em pontuações ou estados**.
- Séries diárias e semanais são reduzidas ao último valor de cada mês nos gráficos históricos.

## 3. Índice por ótica (0 a 100)
1. Cada indicador é transformado: nível, variação de 12 meses ou variação de 5 anos (conforme `SCORING` em `jobs/kondratiev/analytics.py`).
2. Calcula-se o **percentil em janela expansiva** (só dados até aquela data, sem olhar o futuro). Mínimo de 15 observações (anual) a 60 (mensal).
3. Se a polaridade é negativa, inverte-se (100 menos o percentil).
4. O índice é a **média simples** dos indicadores disponíveis no mês, exigindo pelo menos 3 (senão, "dados insuficientes").
5. Defasagem de publicação assumida: anual 12 meses, trimestral 3, mensal 1. Leituras mais velhas que 36 (anual), 9 (trimestral) ou 3 meses (demais) saem do cálculo.

| Ótica | O que 100 significa | Estados (regra) |
|---|---|---|
| Kondratiev | expansão plena de preços, juros e produção | ≥60 Fase A; 40–60 Transição; <40 Fase B |
| Schumpeter | insumos de inovação acelerando em 5 anos | ≥60 Cluster em formação; 40–60 Estável; <40 Desaceleração |
| Perez | calor financeiro (capitalização/PIB, negociação/PIB, retorno de ações) | ≥75 Frenesi; queda de 10+ pontos após pico ≥75 Inflexão; 40–75 Intermediária; <40 Implantação |
| Freeman | renováveis subindo, CO₂ e intensidade energética caindo | ≥60 Difusão em curso; 40–60 Incipiente/mista; <40 Paradigma vigente |
| Minsky | fragilidade máxima (crédito/PIB, serviço da dívida, spreads, curva invertida, condições financeiras) | ≥67 Alta; 33–67 Média; <33 Baixa |

Os limiares são convenções simples, não estimativas econométricas. Mudar qualquer regra exige nova versão da metodologia.

## 4. Validação histórica (backtest descritivo)
Para cada ótica dos EUA, compara-se a média do índice nos 24 meses anteriores ao início de cada recessão do NBER com a média fora de recessões.
Para Minsky (limiar 60) e Perez (limiar 70) mede-se também quantas recessões foram precedidas por um cruzamento do limiar e a taxa de alarmes falsos.
Limites: dentro da amostra, dados revisados (não são os divulgados na época) e poucas recessões. Um resultado fraco é informação válida.

## 5. Contexto de valuation
Retorno real anualizado do S&P 500 (retorno total real de Shiller) em 1, 5 e 10 anos depois dos meses em que o CAPE esteve dentro de ±10 pontos percentuais do percentil atual, contra todos os meses.
Descritivo, dentro da amostra, janelas sobrepostas (poucos episódios independentes). Não é previsão.

## 6. Investimento em IA (EDGAR)
Soma de Microsoft, Alphabet, Amazon, Meta e Oracle: capex (PaymentsToAcquirePropertyPlantAndEquipment) e fluxo de caixa operacional (NetCashProvidedByUsedInOperatingActivities)
em quatro trimestres móveis. Os trimestres discretos são reconstruídos por diferença dos valores acumulados no ano. Trimestres fiscais são mapeados ao trimestre-calendário mais próximo.

## 7. Alertas
A cada atualização na branch principal, compara-se com o `data.json` publicado antes. Abre-se uma Issue no GitHub quando: uma ótica dos EUA muda de estado, a curva 10 anos − 2 anos inverte ou volta a ser positiva,
o hiato de crédito do BIS cruza 10 p.p., ou alguma fonte falha na coleta.

## 8. Limites que o sistema declara
- Há poucos ciclos longos completos (2,5 a 3): qualquer inferência sobre fases tem evidência estatística limitada.
- A datação da "6ª onda" é interpretativa.
- Índices usam pesos iguais. Os indicadores do Banco Mundial têm atraso de 1 a 5 anos.
- A visão global tem menos indicadores; quando há menos de 3 por ótica, o sistema mostra "dados insuficientes".
