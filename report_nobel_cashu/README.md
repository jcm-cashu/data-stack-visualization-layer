# Report Nobel

Dashboard Streamlit de **single-page** para a carteira em aberto do Fundo Nobel
(`fundo = 2` na loan tape `CASHU_DEV.RPT_DATA.LOAN_TAPE_NOBEL_TEST`).

Baseado no template `report_inova` (mesma identidade visual e componentes).

## Visões da página `Carteira`

1. **Carteira Total** – soma de `valor_aberto` (single metric).
2. **Concentração por Foco** – barras horizontais por `foco`.
3. **Concentração por Papel** – barras horizontais por `papel`.
4. **Status de Vencimento** – barras horizontais por `status_vencimento`.
5. **Faixa a Vencer** – barras horizontais por `faixa_a_vencer`
   (exclui registros `Vencido`).
6. **Situação** – barras horizontais por `situacao`.
7. **Concentração por Grupo de Cedentes** – barras horizontais por
   `cedente_grupo` (top 20).
8. **Detalhe por Grupo / Cedente** – grid `cedente_grupo × nome_cedente`
   com filtro rápido e linha de total fixa.
9. **Concentração por Grupo de Sacados** – barras horizontais por
   `sacado_grupo` (top 20).
10. **Grupo de Sacados por Vencimento** – heatmap dos top 15 grupos
    de sacados por mês de vencimento + tabela detalhada filtrável.

Todas as consultas filtram `data_pagamento IS NULL AND fundo = 2`.

## Estrutura

```
report_nobel/
├── app.py                       # Entry point (single page)
├── config.py                    # Snowflake credentials (.env)
├── shared/                      # LOCKED - identidade visual
└── dashboard/
    ├── __init__.py
    ├── dashboard_config.py      # título + tabela alvo + fundo_id
    ├── queries.py               # 10 consultas SQL
    └── sections.py              # render_carteira()
```

## Executar localmente

1. Configurar o `.env` (ou variáveis de ambiente) com credenciais Snowflake:

   ```env
   SNOWFLAKE_USER=...
   SNOWFLAKE_PASSWORD=...
   SNOWFLAKE_ACCOUNT=...
   SNOWFLAKE_WAREHOUSE=...
   SNOWFLAKE_DATABASE=CASHU_DEV
   SNOWFLAKE_SCHEMA=RPT_DATA
   ```

2. Rodar:

   ```bash
   cd report_nobel
   streamlit run app.py
   ```

## Trocar a tabela ou o fundo

Edite apenas `dashboard/dashboard_config.py`:

```python
FUNDO_ID = 2
LOAN_TAPE_TABLE = "cashu_dev.rpt_data.loan_tape_nobel_test"
```

Para apontar para a versão de produção da loan tape, basta atualizar
`LOAN_TAPE_TABLE`. As 10 consultas em `queries.py` derivam dali.
