"""Snowflake SQL queries used by Report Nobel.

A single SELECT against the loan tape is issued; all aggregations are done
in-memory with pandas to minimize Snowflake round-trips.
"""
from .dashboard_config import DIM_FAIXAS_TABLE, FUNDO_IDS, LOAN_TAPE_TABLE


def get_loan_tape_query() -> str:
    """Single row-level pull of the Nobel open portfolio.

    Returns one row per title with the minimum set of columns needed
    to feed every chart/table in the report. The set of funds returned
    is controlled by ``FUNDO_IDS`` in ``dashboard_config``.
    """
    fundos_csv = ", ".join(str(int(f)) for f in FUNDO_IDS)
    return f"""
        SELECT
            fundo,
            nickname_fundo,
            foco,
            papel,
            status_vencimento,
            prazo,
            situacao,
            cedente_grupo,
            nome_cedente,
            sacado_grupo,
            nome_sacado,
            data_operacao,
            data_vencimento,
            data_hj,
            valor_nota,
            valor_aberto
        FROM {LOAN_TAPE_TABLE}
        WHERE fundo IN ({fundos_csv})
    """


def get_dim_faixas_query() -> str:
    """Lookup table mapping `numero` of days to the three faixa labels and
    their order ids. Loaded once and joined to the loan tape in pandas."""
    return f"""
        SELECT
            numero,
            id_faixa_inova,
            faixa_inova,
            id_faixa_micro,
            faixa_micro,
            id_faixa_macro,
            faixa_macro
        FROM {DIM_FAIXAS_TABLE}
    """
