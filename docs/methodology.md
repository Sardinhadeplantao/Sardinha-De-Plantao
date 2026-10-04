# Metodologia (versão 0.2)

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

## 4. Limites que o sistema declara
- Há poucos ciclos longos completos (2,5 a 3): qualquer inferência sobre fases tem evidência estatística limitada.
- A datação da "6ª onda" é interpretativa.
- Índices usam pesos iguais. Os indicadores do Banco Mundial têm atraso de 1 a 5 anos.
- A visão global tem menos indicadores; quando há menos de 3 por ótica, o sistema mostra "dados insuficientes".
