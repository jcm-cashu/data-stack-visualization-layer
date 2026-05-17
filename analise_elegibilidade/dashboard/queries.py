"""Consultas simples — uma tabela por query; joins e filtros em pandas."""

from .dashboard_config import (
    CLASSIFICACAO_TABLE,
    DATA_FIM,
    DATA_INICIO,
    ESTOQUE_TABLE,
    OPERACOES_TABLE,
)


def get_operacoes_query() -> str:
    return f"""
        SELECT *
        FROM {OPERACOES_TABLE}
        WHERE data_operacao >= '{DATA_INICIO.isoformat()}'
          AND data_operacao < '{DATA_FIM.isoformat()}'
          AND fundo = 2
    """


def get_classificacao_query() -> str:
    return f"""
        SELECT cnpj, rj, status, risco
        FROM {CLASSIFICACAO_TABLE}
    """


def get_estoque_query() -> str:
    return f"""
        SELECT
            ref_date,
            nr_gov_id_cedent,
            nr_gov_id_debtor,
            amt_present,
            cd_sit_recv
        FROM {ESTOQUE_TABLE}
        WHERE ref_date >= '{DATA_INICIO.isoformat()}'
          AND ref_date < '{DATA_FIM.isoformat()}'
          AND cd_sit_recv <> 'VENCIDO'
    """


def get_cedentes_periodo_query() -> str:
    """Cedentes com movimento no período (base da CTE empresas)."""
    return f"""
        SELECT DISTINCT
            ced.nr_gov_id AS cnpj_cedente
        FROM cashu.bronze.stg_netfactor__nfingressos ing
        JOIN cashu.bronze.stg_netfactor__nfcedente ced
            ON ced.cd_cedent = ing.cd_cedent
           AND ced.cd_comp = ing.cd_comp
        WHERE ing.oper_date >= '{DATA_INICIO.isoformat()}'
          AND ing.oper_date < '{DATA_FIM.isoformat()}'
          AND ing.cd_comp <> 6
    """
