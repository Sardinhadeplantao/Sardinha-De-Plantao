"""Initial catalog (Phase 0). IDs must be validated against each source API: run `python -m kondratiev.validate`."""
CATALOG = [
    dict(id="fred_dgs10", perspective="kondratiev", layer="timing", source="fred", code="DGS10",
         name="Juros do Tesouro EUA 10 anos", country="USA", unit="% a.a.", frequency="daily", role="procyclical",
         rationale="Juros longos sobem na expansão (fase A) e são o preço de referência do capital no ciclo de Kondratiev.",
         source_url="https://fred.stlouisfed.org/series/DGS10", stale_after_days=7),
    dict(id="fred_cpiaucsl", perspective="kondratiev", layer="regime", source="fred", code="CPIAUCSL",
         name="Índice de preços ao consumidor (EUA)", country="USA", unit="índice 1982-84=100", frequency="monthly",
         role="procyclical",
         rationale="Preços acelerando caracterizam a fase A; deflação ou desinflação prolongada, a fase B.",
         source_url="https://fred.stlouisfed.org/series/CPIAUCSL", stale_after_days=60),
    dict(id="wb_wld_cpi_inflation", perspective="kondratiev", layer="structure", source="worldbank",
         code="FP.CPI.TOTL.ZG", name="Inflação ao consumidor (Mundo)", country="WLD", unit="% a.a.", frequency="annual",
         role="procyclical", rationale="Camada estrutural: inflação global anual, publicada com defasagem de 1-2 anos.",
         source_url="https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=1W", stale_after_days=730),
]
