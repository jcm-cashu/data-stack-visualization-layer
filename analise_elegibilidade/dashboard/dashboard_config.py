"""Configuração do relatório Análise de Elegibilidade."""

from datetime import date

DASHBOARD_TITLE = "Análise de Elegibilidade"

OPERACOES_TABLE = "cashu_dev.rpt_data.loan_tape_operacoes_compat_test"
CLASSIFICACAO_TABLE = "cashu.master_data.dim_classificacao_temporaria"
ESTOQUE_TABLE = "cashu.silver.int_fromtis__estoque_recent"

FUNDO_ID = 2
PL_FUNDO = 120_000_000.0
LIMITE_CEDENTE_PCT = 0.20
LIMITE_SACADO_PCT = 0.0125

DATA_INICIO = date(2026, 2, 1)
DATA_FIM = date(2026, 4, 1)
MES_OPERADO_02_FIM = date(2026, 3, 1)
ESTOQUE_REF_CEDENTE = date(2026, 2, 2)
ESTOQUE_REF_SACADO = (date(2026, 2, 2), date(2026, 3, 3))

VALOR_COL = "valor_nota"
