"""Series catalog. `scope`: 'usa' (main focus) or 'global'. IDs are validated against each source API
(`python -m kondratiev.validate`); a series without data shows as 'Sem dados' rather than failing the run."""

_WB_URL = "https://data.worldbank.org/indicator/{code}?locations={loc}"

# (perspective, name, World Bank code, unit, rationale, available_for_world)
# For the USA, series with a fresher official substitute (FRED, BIS) are not loaded from the World Bank.
_WB_USA_REPLACED = {"FP.CPI.TOTL.ZG", "NY.GDP.DEFL.KD.ZG", "NY.GDP.MKTP.KD.ZG", "FR.INR.RINR", "CM.MKT.LCAP.GD.ZS",
                    "CM.MKT.TRAD.GD.ZS", "FS.AST.PRVT.GD.ZS", "FS.AST.DOMS.GD.ZS", "FB.BNK.CAPA.ZS", "GB.XPD.RSDV.GD.ZS"}
_WB = [
    ("kondratiev", "Inflação ao consumidor", "FP.CPI.TOTL.ZG", "% a.a.", "Preços acelerando caracterizam a fase A; desinflação prolongada, a fase B.", True),
    ("kondratiev", "Deflator do PIB", "NY.GDP.DEFL.KD.ZG", "% a.a.", "Medida ampla de preços: sobe na expansão, cai na contração longa.", True),
    ("kondratiev", "Crescimento do PIB", "NY.GDP.MKTP.KD.ZG", "% a.a.", "Ritmo de produção: mais forte na fase A do ciclo longo.", True),
    ("kondratiev", "Taxa de juros real", "FR.INR.RINR", "% a.a.", "Custo real do capital; juros reais altos marcam fases tardias do ciclo.", False),
    ("schumpeter", "P&D como % do PIB", "GB.XPD.RSDV.GD.ZS", "% do PIB", "Esforço de inovação: base de novos clusters tecnológicos.", True),
    ("schumpeter", "Patentes depositadas (residentes)", "IP.PAT.RESD", "patentes", "Fluxo de invenções, que antecede a onda de inovações.", True),
    ("schumpeter", "Pesquisadores por milhão de habitantes", "SP.POP.SCIE.RD.P6", "por milhão", "Capacidade humana de inovar.", True),
    ("schumpeter", "Exportações de alta tecnologia", "TX.VAL.TECH.MF.ZS", "% das exportações industriais", "Difusão comercial das tecnologias novas.", True),
    ("perez", "Capitalização de mercado das ações", "CM.MKT.LCAP.GD.ZS", "% do PIB", "Indicador Buffett: capital financeiro descolado do produtivo sinaliza frenesi.", True),
    ("perez", "Valor das ações negociadas", "CM.MKT.TRAD.GD.ZS", "% do PIB", "Intensidade especulativa do mercado.", True),
    ("perez", "Exportações de bens de TIC", "TX.VAL.ICTG.ZS.UN", "% das exportações de bens", "Peso do paradigma tecnológico atual (informação).", True),
    ("freeman", "Energia renovável no consumo final", "EG.FEC.RNEW.ZS", "% do consumo", "Difusão do novo insumo-chave energético.", True),
    ("freeman", "Emissões de CO₂ per capita", "EN.GHG.CO2.PC.CE.AR5", "t por pessoa", "Queda sinaliza descarbonização da base produtiva.", True),
    ("freeman", "Intensidade energética do PIB", "EG.EGY.PRIM.PP.KD", "MJ por US$ de PIB", "Queda sinaliza eficiência do paradigma vigente.", True),
    ("minsky", "Crédito ao setor privado", "FS.AST.PRVT.GD.ZS", "% do PIB", "Alavancagem do setor privado: excesso gera fragilidade.", True),
    ("minsky", "Crédito doméstico", "FS.AST.DOMS.GD.ZS", "% do PIB", "Endividamento total da economia.", False),
    ("minsky", "Capital bancário sobre ativos", "FB.BNK.CAPA.ZS", "%", "Colchão dos bancos contra perdas.", False),
]

# (id, perspective, layer, FRED code, name, unit, frequency, stale_after_days, rationale)
_FRED = [
    ("fred_fedfunds", "kondratiev", "regime", "FEDFUNDS", "Taxa de juros básica (Fed Funds)", "% a.a.", "monthly", 90, "Preço do dinheiro definido pelo banco central: referência de todo o sistema de crédito."),
    ("fred_dfii10", "kondratiev", "timing", "DFII10", "Juros reais do Tesouro 10 anos (TIPS)", "% a.a.", "daily", 7, "Custo real do capital de longo prazo, sem a distorção da inflação."),
    ("fred_cpiaucsl", "kondratiev", "regime", "CPIAUCSL", "Índice de preços ao consumidor", "índice 1982-84=100", "monthly", 90, "Preços acelerando caracterizam a fase A; deflação ou desinflação prolongada, a fase B."),
    ("fred_ppiaco", "kondratiev", "regime", "PPIACO", "Índice de preços ao produtor (commodities)", "índice 1982=100", "monthly", 90, "Preços de matérias-primas lideram a inflação ao consumidor nas ondas longas."),
    ("fred_dcoilwtico", "kondratiev", "timing", "DCOILWTICO", "Petróleo WTI", "US$ por barril", "daily", 7, "Preço do principal insumo energético: choques marcam viradas de fase."),
    ("fred_indpro", "kondratiev", "regime", "INDPRO", "Produção industrial", "índice 2017=100", "monthly", 90, "Ritmo da produção física da economia."),
    ("fred_unrate", "kondratiev", "regime", "UNRATE", "Taxa de desemprego", "%", "monthly", 90, "Folga do mercado de trabalho ao longo do ciclo."),
    ("fred_t10y2y", "minsky", "timing", "T10Y2Y", "Curva de juros (10 anos menos 2 anos)", "p.p.", "daily", 7, "Inversão (valor negativo) antecede recessões e crises de crédito."),
    ("fred_t10y3m", "minsky", "timing", "T10Y3M", "Curva de juros (10 anos menos 3 meses)", "p.p.", "daily", 7, "Versão da curva mais usada para prever recessões."),
    ("fred_baa10y", "minsky", "timing", "BAA10Y", "Spread de crédito corporativo (Baa menos Tesouro 10 anos)", "p.p.", "daily", 7, "Prêmio de risco do crédito: dispara quando a fragilidade se revela."),
    ("fred_hy", "minsky", "timing", "BAMLH0A0HYM2", "Spread de títulos high yield", "p.p.", "daily", 7, "Termômetro do apetite por risco no crédito especulativo. O FRED só disponibiliza os últimos 3 anos desta série, curto demais para pontuar no índice."),
    ("fred_nasdaq", "perez", "timing", "NASDAQCOM", "Índice Nasdaq Composite", "pontos", "daily", 7, "Preço das ações de tecnologia desde 1971; a variação de 12 meses mede o ritmo de valorização do capital financeiro no paradigma da informação."),
    ("fred_buffett", "perez", "regime", "NCBEILQ027S/GDP*0.1", "Valor de mercado das ações sobre o PIB (indicador Buffett, Fed Z.1)", "% do PIB", "quarterly", 270, "Ações das empresas não financeiras a valor de mercado divididas pelo PIB: o descolamento entre capital financeiro e produção, atualizado a cada trimestre."),
    ("fred_gdpc1", "kondratiev", "regime", "GDPC1", "PIB real", "US$ bilhões de 2017", "quarterly", 200, "Produção total da economia; o crescimento em 12 meses mede o ritmo da expansão."),
    ("fred_gdpdef", "kondratiev", "regime", "GDPDEF", "Deflator do PIB", "índice 2017=100", "quarterly", 200, "Medida ampla de preços: sobe na expansão, desacelera na contração longa."),
    ("fred_bfs", "schumpeter", "regime", "BABATOTALSAUS", "Pedidos de abertura de empresas", "pedidos por mês", "monthly", 90, "Novos negócios são o canal da destruição criadora de Schumpeter: ondas de abertura acompanham clusters de inovação."),
    ("fred_rnd", "schumpeter", "structure", "Y694RC1Q027SBEA/GDP*100", "Investimento privado em P&D sobre o PIB", "% do PIB", "quarterly", 200, "Esforço privado de inovação medido pelas contas nacionais (BEA), atualizado a cada trimestre."),
    ("fred_sp500", "perez", "timing", "SP500", "S&P 500", "pontos", "daily", 7, "Índice de ações das 500 maiores empresas americanas; também atualiza o CAPE quando o arquivo de Shiller atrasa."),
    ("fred_nfci", "minsky", "timing", "NFCI", "Condições financeiras (Chicago Fed)", "índice", "weekly", 14, "Acima de zero: condições mais apertadas que a média histórica."),
    ("fred_tdsp", "minsky", "regime", "TDSP", "Serviço da dívida das famílias", "% da renda disponível", "quarterly", 280, "Peso da dívida sobre a renda: base da fragilidade financeira de Minsky."),
    ("fred_m2sl", "minsky", "regime", "M2SL", "Oferta de moeda M2", "US$ bilhões", "monthly", 90, "Liquidez disponível para alimentar ativos e crédito."),
    ("fred_mortgage30us", "minsky", "timing", "MORTGAGE30US", "Juros do financiamento imobiliário 30 anos", "% a.a.", "weekly", 14, "Custo do crédito imobiliário, setor central em ciclos de crédito."),
]

_TREASURY = [("ust_3m", "3 Mo", "3 meses", "regime", "minsky"), ("ust_2y", "2 Yr", "2 anos", "timing", "minsky"),
             ("ust_5y", "5 Yr", "5 anos", "timing", "kondratiev"), ("ust_10y", "10 Yr", "10 anos", "timing", "kondratiev"),
             ("ust_30y", "30 Yr", "30 anos", "timing", "kondratiev")]
_TURL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates"


def _build():
    out = []
    for scope, country, loc, label in (("usa", "USA", "US", "EUA"), ("global", "WLD", "1W", "Mundo")):
        for persp, name, code, unit, why, world_ok in _WB:
            if (scope == "global" and not world_ok) or (scope == "usa" and code in _WB_USA_REPLACED):
                continue
            out.append(dict(id=f"wb_{country.lower()}_{code.lower().replace('.', '_')}", scope=scope, perspective=persp,
                            layer="structure", source="worldbank", code=code, name=f"{name} ({label})", country=country,
                            unit=unit, frequency="annual", role="procyclical", rationale=why,
                            source_url=_WB_URL.format(code=code, loc=loc), stale_after_days=900))
    for id_, persp, layer, code, name, unit, freq, stale, why in _FRED:
        out.append(dict(id=id_, scope="usa", perspective=persp, layer=layer, source="fred", code=code,
                        name=f"{name} (EUA)", country="USA", unit=unit, frequency=freq, role="procyclical", rationale=why,
                        source_url=f"https://fred.stlouisfed.org/series/{code}", stale_after_days=stale))
    out.append(dict(id="bis_us_credit_gap", scope="usa", perspective="minsky", layer="regime", source="bis",
                    code="WS_CREDIT_GAP/Q.US.P.A.C", name="Hiato de crédito sobre o PIB (EUA)", country="USA", unit="p.p. do PIB",
                    frequency="quarterly", role="fragility",
                    rationale="Desvio do crédito privado/PIB em relação à sua tendência (filtro HP, método do BIS): o indicador clássico de fragilidade de Minsky; acima de 10 p.p. historicamente precede crises.",
                    source_url="https://data.bis.org/topics/CREDIT_GAPS", stale_after_days=280))
    out.append(dict(id="bis_us_dsr", scope="usa", perspective="minsky", layer="regime", source="bis",
                    code="WS_DSR/Q.US.P", name="Serviço da dívida do setor privado (EUA)", country="USA", unit="% da renda",
                    frequency="quarterly", role="fragility",
                    rationale="Parcela da renda do setor privado comprometida com juros e amortizações: pressão direta sobre a capacidade de pagamento.",
                    source_url="https://data.bis.org/topics/DSR", stale_after_days=280))
    out.append(dict(id="bis_us_total_credit", scope="usa", perspective="minsky", layer="regime", source="bis",
                    code="WS_TC/Q.US.P.A.M.770.A", name="Crédito total ao setor privado não financeiro sobre o PIB (EUA)", country="USA",
                    unit="% do PIB", frequency="quarterly", role="fragility",
                    rationale="Toda a dívida de famílias e empresas (bancos e mercado) sobre o PIB: o estoque de alavancagem que sustenta o ciclo de Minsky.",
                    source_url="https://data.bis.org/topics/TOTAL_CREDIT", stale_after_days=280))
    for scope, area, label in (("usa", "USA", "EUA"), ("global", "World", "Mundo")):
        for key, variable, unit, name, why in (
                ("renew", "Electricity generation|Renewables|%", "% da geração", "Renováveis na geração de eletricidade",
                 "Difusão do novo insumo-chave energético, medida todo mês."),
                ("windsolar", "Electricity generation|Wind and Solar|%", "% da geração", "Eólica e solar na geração de eletricidade",
                 "As tecnologias de custo marginal quase zero que definem o novo paradigma energético."),
                ("co2int", "Power sector emissions|CO2 intensity|gCO2/kWh", "gCO₂/kWh", "Intensidade de carbono da eletricidade",
                 "Emissões por unidade de energia elétrica: a queda mede a substituição do paradigma fóssil.")):
            out.append(dict(id=f"ember_{area.lower()}_{key}", scope=scope, perspective="freeman", layer="regime", source="ember",
                            code=f"{area}|{variable}", name=f"{name} ({label})", country=area, unit=unit, frequency="monthly",
                            role="procyclical", rationale=why, source_url="https://ember-energy.org/data/", stale_after_days=120))
    out.append(dict(id="x_real_fedfunds", scope="usa", perspective="minsky", layer="regime", source="derivado",
                    code="FEDFUNDS − CPI 12m", name="Juro real do Fed (Fed Funds menos inflação de 12 meses) (EUA)", country="USA",
                    unit="p.p.", frequency="monthly", role="fragility",
                    rationale="Calculado cruzando FEDFUNDS e CPI (FRED): juro real alto aperta o crédito e expõe a fragilidade acumulada.",
                    source_url="https://fred.stlouisfed.org/series/FEDFUNDS", stale_after_days=90))
    out.append(dict(id="x_erp", scope="usa", perspective="perez", layer="regime", source="derivado",
                    code="100/CAPE − TIPS 10a", name="Prêmio de risco das ações (rendimento do CAPE menos juro real de 10 anos) (EUA)",
                    country="USA", unit="p.p.", frequency="monthly", role="valuation_excess",
                    rationale="Calculado cruzando o CAPE (Shiller, estendido com S&P 500 e CPI do FRED) e o juro real dos TIPS: quanto menor, menos as ações compensam o risco frente aos títulos — sinal de euforia.",
                    source_url="https://fred.stlouisfed.org/series/DFII10", stale_after_days=90))
    out.append(dict(id="shiller_cape", scope="usa", perspective="perez", layer="regime", source="shiller", code="CAPE",
                    name="CAPE de Shiller — S&P 500 (EUA)", country="USA", unit="múltiplo", frequency="monthly",
                    role="valuation_excess",
                    rationale="Preço sobre lucros reais médios de 10 anos, desde 1871: mede o descolamento entre o capital financeiro e a produção (frenesi de Perez). Quando o arquivo de Shiller atrasa, os meses seguintes são estimados com o S&P 500 e o CPI do FRED, mantendo os lucros de 10 anos do último mês publicado.",
                    source_url="https://shillerdata.com/", stale_after_days=75))
    out.append(dict(id="shiller_real_tr", scope="context", perspective="perez", layer="regime", source="shiller",
                    code="Return Price", name="S&P 500 — retorno total real (Shiller)", country="USA", unit="índice",
                    frequency="monthly", role="context", rationale="Base dos retornos históricos por nível de CAPE.",
                    source_url="https://shillerdata.com/", stale_after_days=75))
    out.append(dict(id="sec_ai_capex_ocf", scope="usa", perspective="perez", layer="regime", source="edgar", code="capex_ocf",
                    name="Capex sobre fluxo de caixa operacional — 5 grandes de tecnologia (EUA)", country="USA", unit="%",
                    frequency="quarterly", role="valuation_excess",
                    rationale="Quanto do caixa operacional de Microsoft, Alphabet, Amazon, Meta e Oracle vira investimento em ativos (data centers, chips): mede a intensidade do ciclo de investimento em IA, a fase de instalação de Perez.",
                    source_url="https://www.sec.gov/edgar/sec-api-documentation", stale_after_days=150))
    out.append(dict(id="sec_ai_capex", scope="usa", perspective="perez", layer="regime", source="edgar", code="capex",
                    name="Capex de 12 meses — 5 grandes de tecnologia (EUA)", country="USA", unit="US$ bilhões",
                    frequency="quarterly", role="valuation_excess",
                    rationale="Investimento total em ativos fixos de Microsoft, Alphabet, Amazon, Meta e Oracle nos últimos quatro trimestres.",
                    source_url="https://www.sec.gov/edgar/sec-api-documentation", stale_after_days=150))
    out.append(dict(id="fred_usrec", scope="context", perspective="minsky", layer="regime", source="fred", code="USREC",
                    name="Recessões dos EUA (NBER)", country="USA", unit="0/1", frequency="monthly", role="context",
                    rationale="Datação oficial das recessões americanas, usada apenas para marcar os gráficos.",
                    source_url="https://fred.stlouisfed.org/series/USREC", stale_after_days=90))
    for id_, col, label, layer, persp in _TREASURY:
        out.append(dict(id=id_, scope="usa", perspective=persp, layer=layer, source="treasury", code=col,
                        name=f"Juros do Tesouro {label} (EUA)", country="USA", unit="% a.a.", frequency="daily",
                        role="procyclical", rationale="Curva de juros oficial do Tesouro dos EUA: preço do capital em cada prazo.",
                        source_url=_TURL, stale_after_days=7))
    return out


CATALOG = _build()
