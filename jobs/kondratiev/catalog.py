"""Series catalog. `scope`: 'usa' (main focus) or 'global'. IDs are validated against each source API
(`python -m kondratiev.validate`); a series without data shows as 'Sem dados' rather than failing the run."""

_WB_URL = "https://data.worldbank.org/indicator/{code}?locations={loc}"

# (perspective, name, World Bank code, unit, rationale, available_for_world)
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
    ("perez", "Variação do índice de ações", "CM.MKT.INDX.ZG", "% a.a.", "Ritmo de valorização do capital financeiro.", False),
    ("freeman", "Energia renovável no consumo final", "EG.FEC.RNEW.ZS", "% do consumo", "Difusão do novo insumo-chave energético.", True),
    ("freeman", "Emissões de CO₂ per capita", "EN.GHG.CO2.PC.CE.AR5", "t por pessoa", "Queda sinaliza descarbonização da base produtiva.", True),
    ("freeman", "Intensidade energética do PIB", "EG.EGY.PRIM.PP.KD", "MJ por US$ de PIB", "Queda sinaliza eficiência do paradigma vigente.", True),
    ("minsky", "Crédito ao setor privado", "FS.AST.PRVT.GD.ZS", "% do PIB", "Alavancagem do setor privado: excesso gera fragilidade.", True),
    ("minsky", "Crédito doméstico", "FS.AST.DOMS.GD.ZS", "% do PIB", "Endividamento total da economia.", False),
    ("minsky", "Capital bancário sobre ativos", "FB.BNK.CAPA.ZS", "%", "Colchão dos bancos contra perdas.", False),
]

# (id, perspective, layer, FRED code, name, unit, frequency, stale_after_days, rationale)
_FRED = [
    ("fred_fedfunds", "kondratiev", "regime", "FEDFUNDS", "Taxa de juros básica (Fed Funds)", "% a.a.", "monthly", 60, "Preço do dinheiro definido pelo banco central: referência de todo o sistema de crédito."),
    ("fred_dfii10", "kondratiev", "timing", "DFII10", "Juros reais do Tesouro 10 anos (TIPS)", "% a.a.", "daily", 7, "Custo real do capital de longo prazo, sem a distorção da inflação."),
    ("fred_cpiaucsl", "kondratiev", "regime", "CPIAUCSL", "Índice de preços ao consumidor", "índice 1982-84=100", "monthly", 60, "Preços acelerando caracterizam a fase A; deflação ou desinflação prolongada, a fase B."),
    ("fred_ppiaco", "kondratiev", "regime", "PPIACO", "Índice de preços ao produtor (commodities)", "índice 1982=100", "monthly", 60, "Preços de matérias-primas lideram a inflação ao consumidor nas ondas longas."),
    ("fred_dcoilwtico", "kondratiev", "timing", "DCOILWTICO", "Petróleo WTI", "US$ por barril", "daily", 7, "Preço do principal insumo energético: choques marcam viradas de fase."),
    ("fred_indpro", "kondratiev", "regime", "INDPRO", "Produção industrial", "índice 2017=100", "monthly", 60, "Ritmo da produção física da economia."),
    ("fred_unrate", "kondratiev", "regime", "UNRATE", "Taxa de desemprego", "%", "monthly", 60, "Folga do mercado de trabalho ao longo do ciclo."),
    ("fred_t10y2y", "minsky", "timing", "T10Y2Y", "Curva de juros (10 anos menos 2 anos)", "p.p.", "daily", 7, "Inversão (valor negativo) antecede recessões e crises de crédito."),
    ("fred_t10y3m", "minsky", "timing", "T10Y3M", "Curva de juros (10 anos menos 3 meses)", "p.p.", "daily", 7, "Versão da curva mais usada para prever recessões."),
    ("fred_baa10y", "minsky", "timing", "BAA10Y", "Spread de crédito corporativo (Baa menos Tesouro 10 anos)", "p.p.", "daily", 7, "Prêmio de risco do crédito: dispara quando a fragilidade se revela."),
    ("fred_hy", "minsky", "timing", "BAMLH0A0HYM2", "Spread de títulos high yield", "p.p.", "daily", 7, "Termômetro do apetite por risco no crédito especulativo."),
    ("fred_nfci", "minsky", "timing", "NFCI", "Condições financeiras (Chicago Fed)", "índice", "weekly", 14, "Acima de zero: condições mais apertadas que a média histórica."),
    ("fred_tdsp", "minsky", "regime", "TDSP", "Serviço da dívida das famílias", "% da renda disponível", "quarterly", 120, "Peso da dívida sobre a renda: base da fragilidade financeira de Minsky."),
    ("fred_m2sl", "minsky", "regime", "M2SL", "Oferta de moeda M2", "US$ bilhões", "monthly", 60, "Liquidez disponível para alimentar ativos e crédito."),
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
            if scope == "global" and not world_ok:
                continue
            out.append(dict(id=f"wb_{country.lower()}_{code.lower().replace('.', '_')}", scope=scope, perspective=persp,
                            layer="structure", source="worldbank", code=code, name=f"{name} ({label})", country=country,
                            unit=unit, frequency="annual", role="procyclical", rationale=why,
                            source_url=_WB_URL.format(code=code, loc=loc), stale_after_days=900))
    for id_, persp, layer, code, name, unit, freq, stale, why in _FRED:
        out.append(dict(id=id_, scope="usa", perspective=persp, layer=layer, source="fred", code=code,
                        name=f"{name} (EUA)", country="USA", unit=unit, frequency=freq, role="procyclical", rationale=why,
                        source_url=f"https://fred.stlouisfed.org/series/{code}", stale_after_days=stale))
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
