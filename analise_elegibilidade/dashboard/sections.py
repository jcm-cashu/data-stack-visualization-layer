"""Layout do relatório Análise de Elegibilidade."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from shared.components import render_data_grid
from shared.styles import COLORS

from . import data_logic as dl
from .dashboard_config import DASHBOARD_TITLE, DATA_FIM, DATA_INICIO, VALOR_COL

_PREVIEW_COLS = {
    "codigo_operacao": "CODIGO_OPE",
    "doc": "DOCUMENTO",
    "fundo": "EMPRESA",
    "data_operacao": "DATA_OPE",
    "data_vencimento": "DT_VENCIMENTO",
    "mes_vencimento": "MES_VENCIMENTO",
}

_DETAIL_EXTRA = {
    VALOR_COL: "VALOR_NOTA",
    "foco": "FOCO",
    "papel": "PAPEL",
    "situacao": "SITUACAO",
    "papel_gerencial": "PAPEL_GERENCIAL",
    "papel_tratado_foco": "PAPEL_TRATADO_FOCO",
    "gov_cedente": "CNPJ_CED",
    "nome_cedente": "NOME_CED",
    "gov_sacado": "CNPJ_SAC",
    "nome_sacado": "NOME_SAC",
    "cedente_grupo": "GRUPO_CEDENTE_TRATADO",
    "sacado_grupo": "GRUPO_SACADO_TRATADO",
}


def _fmt_br(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _rename_display(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    cols = [c for c in mapping if c in df.columns]
    out = df[cols].copy()
    return out.rename(columns={c: mapping[c] for c in cols})


def _section_title(text: str) -> None:
    st.markdown(
        f"""
        <div style="
            border-top: 1px solid {COLORS['table_border']};
            border-bottom: 1px solid {COLORS['table_border']};
            padding: 0.65rem 0;
            margin: 1.25rem 0 1rem 0;
            text-align: center;
            font-weight: 600;
            font-size: 1.05rem;
        ">{text}</div>
        """,
        unsafe_allow_html=True,
    )


def _metric_and_table(
    title: str, df: pd.DataFrame, *, grid_key: str, preview_only: bool = False
) -> None:
    total = dl.sum_valor(df)
    left, right = st.columns([1, 2.2], gap="medium")
    with left:
        st.markdown(
            f"""
            <div style="
                border: 1px solid {COLORS['table_border']};
                border-radius: 8px;
                padding: 1.5rem 1rem;
                text-align: center;
                min-height: 140px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="font-size: 0.9rem; color: {COLORS['text_secondary']}; margin-bottom: 0.5rem;">
                    {title}
                </div>
                <div style="font-size: 1.75rem; font-weight: 700;">{_fmt_br(total)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.caption(f"{title} — {len(df):,} linhas".replace(",", "."))
        if df.empty:
            st.info("Query produced no results")
        else:
            mapping = dict(_PREVIEW_COLS)
            if not preview_only:
                mapping.update(_DETAIL_EXTRA)
            render_data_grid(_rename_display(df, mapping), grid_key, height=320)


def _kpi_card(title: str, df: pd.DataFrame) -> None:
    total = dl.sum_valor(df)
    if df.empty:
        st.markdown(
            f"""
            <div style="
                border: 1px solid {COLORS['table_border']};
                border-radius: 8px;
                padding: 1rem;
                min-height: 100px;
                color: {COLORS['text_secondary']};
                font-size: 0.85rem;
            ">
                <strong>{title}</strong><br/>
                <span style="margin-top: 0.75rem; display: inline-block;">Query produced no results</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="
                border: 1px solid {COLORS['table_border']};
                border-radius: 8px;
                padding: 1rem;
                min-height: 100px;
            ">
                <div style="font-size: 0.85rem; color: {COLORS['text_secondary']};">{title}</div>
                <div style="font-size: 1.35rem; font-weight: 700; margin-top: 0.5rem;">{_fmt_br(total)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_dashboard() -> None:
    st.title(DASHBOARD_TITLE)
    st.caption(f"Período: {DATA_INICIO.isoformat()} a {DATA_FIM.isoformat()} (exclusive) · Fundo {2}")

    bundle = dl.load_data()
    ops = dl._base_ops(bundle.operacoes)
    ops_inova = dl.filter_inova_disponiveis(ops, bundle.empresas)

    _section_title("Operações")
    _metric_and_table("Operações", ops, grid_key="grid_operacoes", preview_only=True)

    rows = []
    no_emp = {"Operações de Fomento", "Operações de Intercompany"}
    for title, fn in dl.CATEGORY_FILTERS:
        subset = fn(ops) if title in no_emp else fn(ops, bundle.empresas)
        rows.append((title, subset))

    for i in range(0, len(rows), 4):
        cols = st.columns(4)
        for col, (title, subset) in zip(cols, rows[i : i + 4]):
            with col:
                _kpi_card(title, subset)

    _section_title("Operações disponíveis para o Inova")
    _metric_and_table(
        "Operações disponíveis para o Inova",
        ops_inova,
        grid_key="grid_inova",
        preview_only=True,
    )

    analise_cedente = dl.build_analise_cedente(ops_inova, bundle.estoque, ops)
    _section_title("Análise Cedente")
    st.caption(f"Análise Cedente — {len(analise_cedente)} linhas")
    if analise_cedente.empty:
        st.info("Query produced no results")
    else:
        render_data_grid(analise_cedente, "grid_analise_cedente", height=360)

    analise_sacado = dl.build_analise_sacado(ops_inova, bundle.estoque, ops)
    _section_title("Análise Sacado")
    st.caption(f"Análise Sacado — {len(analise_sacado)} linhas")
    if analise_sacado.empty:
        st.info("Query produced no results")
    else:
        render_data_grid(analise_sacado, "grid_analise_sacado", height=400)

    ops_selecionadas = dl.build_operacoes_selecionadas(ops_inova, analise_sacado)
    _section_title("Operações Selecionadas")
    _metric_and_table(
        "Operações Selecionadas",
        ops_selecionadas,
        grid_key="grid_selecionadas_preview",
        preview_only=True,
    )

    st.caption(f"Detalhe — {len(ops_selecionadas)} linhas")
    if ops_selecionadas.empty:
        st.info("Query produced no results")
    else:
        render_data_grid(
            _rename_display(ops_selecionadas, {**_PREVIEW_COLS, **_DETAIL_EXTRA}),
            "grid_selecionadas_detalhe",
            height=420,
        )
