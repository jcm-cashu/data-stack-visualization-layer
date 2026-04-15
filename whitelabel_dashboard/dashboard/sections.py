"""
Dashboard Sections - Section render functions

This file contains all the section render functions for the dashboard.
Each section is a self-contained unit that renders a part of the page.

Storytelling structure (Cole Knaflic):
  Beginning -> KPI summary row establishes context
  Middle    -> Detailed breakdowns and charts explore the data
  End       -> Actionable insight closes the narrative

For new dashboards, you may need to:
- Adjust metric labels and names
- Add/remove sections based on your data
- Modify filter logic if your data schema differs
"""
from datetime import date, timedelta

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Shared imports (DO NOT MODIFY these imports)
from shared.db import run_query
from shared.styles import COLORS
from shared.components import (
    render_table_with_merged_headers,
    chiclet_selector,
    PLOTLY_COLORWAY,
    PLOTLY_CONFIG,
    build_vintage_line,
    get_standard_layout,
)

# Dashboard-specific imports
from . import queries
from .dashboard_config import (
    HABILITACAO_OPTIONS,
    TIER_OPTIONS,
    PERIODO_OPTIONS,
    RECENCIA_OPTIONS,
    BUCKET_LABELS,
)


# =============================================================================
# Helper Functions
# =============================================================================

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase for consistency."""
    df.columns = df.columns.str.lower()
    return df


def _ensure_cumulative_columns(
    df: pd.DataFrame,
    *,
    value_cols: list[str] | None = None,
    ratio_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Ensure cumulative delinquency column names exist; rename legacy ones when needed."""
    df.columns = df.columns.str.lower()

    rename_candidates = {
        "over_15": "over_15p",
        "over_30": "over_30p",
        "over_60": "over_60p",
        "over_90": "over_90p",
    }
    rename_map: dict[str, str] = {}
    for old, new in rename_candidates.items():
        if new not in df.columns and old in df.columns:
            rename_map[old] = new
    if rename_map:
        df = df.rename(columns=rename_map)

    value_cols = value_cols or ["over_15p", "over_30p", "over_60p", "over_90p"]
    for col in value_cols:
        if col not in df.columns:
            df[col] = 0.0

    ratio_cols = ratio_cols or [
        "delinquencia_over_15",
        "delinquencia_over_30",
        "delinquencia_over_60",
        "delinquencia_over_90",
    ]
    for col in ratio_cols:
        if col not in df.columns:
            df[col] = 0.0

    return df


def _fmt_currency(value: float) -> str:
    """Format a number as BRL currency string."""
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:,.1f}K"
    return f"R$ {value:,.0f}"


def _fmt_int(value) -> str:
    """Format a number as integer with thousands separator."""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"


def _build_tier_filter(selector_tier: str) -> str:
    """Map tier selector value to SQL filter clause."""
    if selector_tier in ("A", "B", "C", "D", "E"):
        return f"and tier_loja = '{selector_tier}'"
    if selector_tier == "Sem Tier":
        return "and tier_loja = 'Sem Tier'"
    return ""


def _build_habilitacao_filter(selector: str) -> str:
    """Map habilitacao selector value to SQL filter clause."""
    if selector == "Habilitada":
        return "and loja_habilitada_flag = true"
    if selector == "Não Habilitada":
        return "and loja_habilitada_flag = false"
    return ""


def _period_bounds(ref: date, meses: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Compute (start_date, end_date) going *meses* months back from *ref*."""
    start_year = ref.year
    start_month = ref.month - (meses - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    return pd.Timestamp(start_year, start_month, 1), pd.Timestamp(ref.year, ref.month, 1)


_MESES_MAP: dict[str, int] = {
    "Ultimos 2 Meses": 2,
    "Ultimos 3 Meses": 3,
    "Ultimos 6 Meses": 6,
    "Ultimos 9 Meses": 9,
    "Ultimos 12 Meses": 12,
}


# =============================================================================
# Cached data-loading helpers
# =============================================================================

@st.cache_data(ttl=3600)
def _load_totais(month: int, year: int) -> pd.DataFrame:
    return _normalize_columns(run_query(queries.get_totais_query(month, year)))


@st.cache_data(ttl=3600)
def _load_habilitacao(month: int, year: int) -> pd.DataFrame:
    return _normalize_columns(run_query(queries.get_habilitacao_query(month, year)))


@st.cache_data(ttl=3600)
def _load_tier(month: int, year: int) -> pd.DataFrame:
    return _normalize_columns(run_query(queries.get_tier_query(month, year)))


@st.cache_data(ttl=3600)
def _load_breakdown_lojas(month: int, year: int, hab_filter: str, tier_filter: str) -> pd.DataFrame:
    sql = queries.get_breakdown_lojas_query(month, year, hab_filter, tier_filter)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=3600)
def _load_perc_credito(month: int, year: int, hab_filter: str, tier_filter: str) -> pd.DataFrame:
    sql = queries.get_perc_credito_query(month, year, hab_filter, tier_filter)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=3600)
def _load_breakdown_revendedores(month: int, year: int) -> pd.DataFrame:
    sql = queries.get_breakdown_revendedores_query(month, year)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=3600)
def _load_faturamento_per_capta(ref_date: str, meses: int) -> pd.DataFrame:
    sql = queries.get_faturamento_per_capta_query(ref_date, meses)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=3600)
def _load_distribuicao_credito(ref_date: str, filtro_sql: str) -> pd.DataFrame:
    sql = queries.get_distribuicao_credito_query(ref_date, filtro_sql)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=3600)
def _load_inadimplencia_evolucao(start_date: str, end_date: str) -> pd.DataFrame:
    sql = queries.get_inadimplencia_evolucao_query(start_date, end_date)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=3600)
def _load_vintage_clientes() -> pd.DataFrame:
    return _normalize_columns(run_query(queries.VINTAGE_CLIENTES_QUERY))


@st.cache_data(ttl=3600)
def _load_vintage_originacao() -> pd.DataFrame:
    return _normalize_columns(run_query(queries.VINTAGE_ORIGINACAO_QUERY))


@st.cache_data(ttl=3600)
def _load_timeseries_receita(start: str, end: str, flag: bool) -> pd.DataFrame:
    sql_ts = queries.get_timeseries_receita_query()
    return _normalize_columns(run_query(sql_ts, params=(start, end, flag)))


# =============================================================================
# SUMÁRIO GERAL - Section Functions
# =============================================================================


def _render_kpi_sumario(df_totais: pd.DataFrame) -> None:
    """Beginning: KPI summary row establishing context for the general summary."""
    if df_totais.empty:
        return
    r = df_totais.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Receita Total", _fmt_currency(r.get("financeiro", 0)))
    with col2:
        st.metric("Receita CashU", _fmt_currency(r.get("financeiro_cashu", 0)))
    with col3:
        st.metric("Clientes", _fmt_int(r.get("numero_clientes", 0)))
    with col4:
        st.metric("Ticket Médio", _fmt_currency(r.get("ticket_medio", 0)))


def _render_numeros_gerais(df_totais: pd.DataFrame) -> None:
    """Render the 'Números Gerais' section with Totais, Por Habilitação, Por Tier tables."""
    inicio = st.session_state.reference_date
    st.subheader("Números Gerais")
    st.caption("Visão consolidada das métricas do período por habilitação e tier de loja.")
    col_totais, col_hab, col_tier = st.columns([0.45, 0.55, 1.0])

    # Totais
    with col_totais:
        st.caption("Totais")
        if df_totais.empty:
            st.info("Sem dados para o período.")
        else:
            r = df_totais.iloc[0]
            metric_labels = ["R$", "R$ CashU", "# Compras", "# Clientes", "# Clientes com Crédito", "Ticket Médio"]
            metric_values = [
                r.get("financeiro", 0),
                r.get("financeiro_cashu", 0),
                r.get("numero_compras", 0),
                r.get("numero_clientes", 0),
                r.get("clientes_com_credito", 0),
                r.get("ticket_medio", 0.0),
            ]
            df_totais_view = pd.DataFrame({"Total": metric_values}, index=metric_labels)
            render_table_with_merged_headers(
                df_totais_view,
                index_label="Métrica",
                show_percent=False,
                table_id="totais-table",
                column_width_overrides={1: "120px", 2: "120px"},
                frame_width=240,
                container_css_width="240px",
            )

    # Por habilitação
    with col_hab:
        st.caption("Por Habilitação")
        df_hab = _load_habilitacao(inicio.month, inicio.year)
        if df_hab.empty:
            st.info("Sem dados para o período.")
        else:
            long_hab = df_hab.melt(id_vars="status_habilitada", var_name="metric", value_name="valor")
            hab_pivot = (
                long_hab.pivot(index="metric", columns="status_habilitada", values="valor")
                    .reindex(index=["financeiro", "financeiro_cashu", "numero_compras", "numero_clientes", "clientes_com_credito", "ticket_medio"])
            )
            hab_pivot.index = ["R$", "R$ CashU", "# Compras", "# Clientes", "# Clientes com Crédito", "Ticket Médio"]
            status_order = ["Habilitada", "Não Habilitada"]
            for c in status_order:
                if c not in hab_pivot.columns:
                    hab_pivot[c] = 0
            hab_pivot = hab_pivot[status_order]
            render_table_with_merged_headers(hab_pivot, index_label="Métrica", show_percent=False)

    # Por tier
    with col_tier:
        st.caption("Por Tier")
        df_tier = _load_tier(inicio.month, inicio.year)
        if df_tier.empty:
            st.info("Sem dados para o período.")
        else:
            long_tier = df_tier.melt(id_vars="tier_loja", var_name="metric", value_name="valor")
            tier_pivot = (
                long_tier.pivot(index="metric", columns="tier_loja", values="valor")
                    .reindex(index=["financeiro", "financeiro_cashu", "numero_compras", "numero_clientes", "clientes_com_credito", "ticket_medio"])
            )
            tier_pivot.index = ["R$", "R$ CashU", "# Compras", "# Clientes", "# Clientes com Crédito", "Ticket Médio"]
            tier_order = ["A", "B", "C", "D", "E", "Sem Tier"]
            for c in tier_order:
                if c not in tier_pivot.columns:
                    tier_pivot[c] = 0
            tier_pivot = tier_pivot[tier_order]
            render_table_with_merged_headers(tier_pivot, index_label="Métrica", show_percent=False)


def _render_breakdown_lojas() -> None:
    """Render the 'Breakdown Lojas' section with filters and histogram."""
    inicio = st.session_state.reference_date
    st.subheader("Breakdown Lojas")
    st.caption("Comparação de métricas por tipo de loja. Use os filtros para segmentar por habilitação e tier.")

    selector_habilitacao = chiclet_selector(
        options=HABILITACAO_OPTIONS,
        key="selector_habilitacao",
        default="Todas",
        variant="buttons",
        group_max_fraction=0.5,
    )
    selector_tier = chiclet_selector(
        options=TIER_OPTIONS,
        key="selector_tier",
        default="Todos",
        variant="buttons",
        group_max_fraction=0.5,
    )

    habilitacao_filter = _build_habilitacao_filter(selector_habilitacao)
    tier_filter = _build_tier_filter(selector_tier)

    df = _load_breakdown_lojas(inicio.month, inicio.year, habilitacao_filter, tier_filter)
    df = df.pivot(index='forma_pagamento', columns='tipo_loja', values=['financeiro', 'numero_compras', 'numero_clientes', 'ticket_medio']).fillna(0)

    df = df.swaplevel(0, 1, axis=1)

    tipo_order = ['Franquia', 'Loja Própria', 'Sem Classificação']
    metric_order = ['financeiro', 'numero_clientes', 'numero_compras', 'ticket_medio']

    new_columns = [
        (tipo, metric)
        for tipo in tipo_order
        for metric in metric_order
    ]

    df = df.reindex(columns=new_columns)
    df.index.name = None

    metric_display_names = ['R$', '# Clientes', '# Compras', 'Ticket Médio']
    df.columns = df.columns.set_levels(metric_display_names, level=1)

    df = df.sort_index()

    render_table_with_merged_headers(df)

    # Histogram: Distribuição de Clientes com Crédito
    df_perc_credito = _load_perc_credito(inicio.month, inicio.year, habilitacao_filter, tier_filter)
    st.caption("Proporção de clientes com crédito por loja. Concentração à esquerda indica baixa penetração de crédito.")
    if df_perc_credito.empty:
        st.info("Sem dados para o período.")
    else:
        bin_edges = np.arange(0, 101, 5)
        bin_labels = [f"{i}–{i+5}%" for i in bin_edges[:-1]]
        df_perc_credito = df_perc_credito.copy()

        df_perc_credito["perc_com_credito_pct"] = (
            pd.to_numeric(df_perc_credito["perc_com_credito"], errors="coerce")
            .fillna(0)
            * 100
        ).clip(lower=0, upper=100)

        df_perc_credito["credito_bin"] = pd.cut(
            df_perc_credito["perc_com_credito_pct"],
            bins=bin_edges,
            labels=bin_labels,
            include_lowest=True,
            right=False,
        )

        bin_counts = (
            df_perc_credito.groupby("credito_bin", observed=True)
            .size()
            .reset_index(name="numero_lojas")
        )
        bin_order_map = {label: idx for idx, label in enumerate(bin_labels)}
        bin_counts["ordering_index"] = bin_counts["credito_bin"].map(bin_order_map)
        bin_counts = bin_counts.sort_values("ordering_index")

        x_vals = bin_counts["credito_bin"].astype(str).tolist()
        y_vals = bin_counts["numero_lojas"].tolist()
        fig = go.Figure(
            data=[
                go.Bar(
                    x=x_vals,
                    y=y_vals,
                    orientation='v',
                    marker=dict(
                        color=COLORS["primary"],
                        line=dict(color="#333", width=0.6),
                    ),
                )
            ]
        )

        fig.update_layout(
            **get_standard_layout(
                show_legend=False,
                xaxis=dict(
                    title="% Clientes com Crédito",
                    type="category",
                    categoryorder="array",
                    categoryarray=bin_labels,
                    showgrid=False,
                    showline=False,
                    zeroline=False,
                ),
                yaxis=dict(
                    title="# Lojas",
                    showgrid=True,
                    gridcolor=COLORS["table_border"],
                    gridwidth=0.5,
                    showline=False,
                    zeroline=False,
                ),
            )
        )

        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def _render_breakdown_revendedores() -> None:
    """Render the 'Breakdown Revendedores' section."""
    inicio = st.session_state.reference_date
    st.subheader("Breakdown Revendedores")
    st.caption("Desempenho por forma de pagamento, segmentado por habilitação e posse de crédito CashU.")

    df = _load_breakdown_revendedores(inicio.month, inicio.year)
    df = df.pivot(index='forma_pagamento', columns=['status_habilitada', 'tipo_revendedor'], values=['financeiro', 'numero_compras', 'numero_clientes', 'ticket_medio']).fillna(0)

    df = df.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)

    status_order = ['Habilitada', 'Não Habilitada']
    tipo_order = ['Possui Crédito CashU', 'Não Possui Crédito CashU']
    metric_order = ['financeiro', 'numero_compras', 'numero_clientes', 'ticket_medio']

    new_columns = [
        (status, tipo, metric)
        for status in status_order
        for tipo in tipo_order
        for metric in metric_order
    ]
    df = df.reindex(columns=new_columns)

    df.index.name = None

    metric_display_names = ['R$', '# Compras', '# Clientes', 'Ticket Médio']
    df.columns = df.columns.set_levels(metric_display_names, level=2)

    df = df.sort_index()

    render_table_with_merged_headers(df)


def _render_evolucao_faturamento() -> None:
    """Render the 'Evolução do Faturamento Per Capta' section."""
    inicio = st.session_state.reference_date
    st.subheader("Evolução do Faturamento Per Capta")
    st.caption("Tendência de receita por cliente ao longo do tempo, comparando clientes com e sem crédito CashU.")

    periodo_grafico = chiclet_selector(
        options=PERIODO_OPTIONS,
        key="evolucao_faturamento",
        default="Ultimos 2 Meses",
        variant="buttons",
        group_max_fraction=0.5,
    )

    meses = _MESES_MAP.get(periodo_grafico, 2)

    df = _load_faturamento_per_capta(str(inicio), meses)

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Possui Crédito CashU")
        df1 = (
            df[df["tipo_revendedor"] == "Possui Crédito CashU"]
            .pivot(index="date", columns="forma_pagamento", values="financeiro_per_capta")
            .sort_index()
            .fillna(0)
        )
        df1_long = (
            df1.reset_index()
               .melt(id_vars="date", var_name="forma_pagamento", value_name="financeiro_per_capta")
        )
        fig1 = px.line(
            df1_long,
            x="date",
            y="financeiro_per_capta",
            color="forma_pagamento",
            color_discrete_sequence=PLOTLY_COLORWAY,
            labels={"date": "Data", "financeiro_per_capta": "R$", "forma_pagamento": "Forma de Pagamento"},
            template="plotly_white",
        )
        fig1.update_traces(mode="lines")
        fig1.update_layout(
            **get_standard_layout(legend_title="Forma de Pagamento")
        )
        st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)

    with col2:
        st.caption("Não Possui Crédito CashU")
        df2 = (
            df[df["tipo_revendedor"] == "Não Possui Crédito CashU"]
            .pivot(index="date", columns="forma_pagamento", values="financeiro_per_capta")
            .sort_index()
            .fillna(0)
        )
        df2_long = (
            df2.reset_index()
               .melt(id_vars="date", var_name="forma_pagamento", value_name="financeiro_per_capta")
        )
        fig2 = px.line(
            df2_long,
            x="date",
            y="financeiro_per_capta",
            color="forma_pagamento",
            color_discrete_sequence=PLOTLY_COLORWAY,
            labels={"date": "Data", "financeiro_per_capta": "R$", "forma_pagamento": "Forma de Pagamento"},
            template="plotly_white",
        )
        fig2.update_traces(mode="lines")
        fig2.update_layout(
            **get_standard_layout(legend_title="Forma de Pagamento")
        )
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)


def _render_distribuicao_credito() -> None:
    """Render the 'Distribuição do Crédito Concedido x Utilização' section."""
    inicio = st.session_state.reference_date
    st.subheader("Distribuição do Crédito Concedido x Utilização")
    st.caption("Análise da distribuição de limites e uso do crédito. Concentração à esquerda indica limites conservadores.")

    filtro_recencia = chiclet_selector(
        options=RECENCIA_OPTIONS,
        key="filtro_recencia",
        default="Todos",
        variant="buttons",
        group_max_fraction=0.5,
    )
    filtro_recencia_map = {
        "Todos": "",
        "Compras Últimos 30d": "and filtro_recencia <= 30",
        "Compras Últimos 60d": "and filtro_recencia <= 60",
        "Compras Últimos 90d": "and filtro_recencia <= 90",
    }
    filtro_recencia_sql = filtro_recencia_map.get(filtro_recencia, "")

    df_credito = _load_distribuicao_credito(str(inicio), filtro_recencia_sql)

    if df_credito.empty:
        st.info("Não há dados de crédito para o período selecionado.")
    else:
        df_credito["credito_disponivel"] = pd.to_numeric(df_credito["credito_disponivel"], errors="coerce")
        df_credito = df_credito[df_credito["credito_disponivel"] > 0].copy()
        if "percentual_utilizado" in df_credito.columns:
            df_credito["percentual_utilizado_pct"] = (
                (df_credito["percentual_utilizado"] * 100).clip(lower=0, upper=100)
            )
        else:
            df_credito["percentual_utilizado_pct"] = pd.NA

        _hist_layout = get_standard_layout(
            show_legend=False,
            margin=dict(l=0, r=0, t=10, b=0),
        )

        col_1, col_2 = st.columns(2)
        with col_1:
            st.caption("Crédito concedido por cliente (R$)")
            nbins = 30
            min_val = float(df_credito["credito_disponivel"].min())
            max_val = float(df_credito["credito_disponivel"].max())
            if min_val == max_val:
                edges = np.array([min_val * 0.9, min_val * 1.1]) if min_val > 0 else np.array([1, 2])
            else:
                start_exp = np.floor(np.log10(min_val))
                end_exp = np.ceil(np.log10(max_val))
                edges = np.logspace(start_exp, end_exp, num=nbins + 1)
            counts, bins = np.histogram(df_credito["credito_disponivel"].to_numpy(), bins=edges)
            centers = (bins[:-1] + bins[1:]) / 2.0
            widths = (bins[1:] - bins[:-1])
            custom = np.stack([bins[:-1], bins[1:]], axis=1)

            fig_concedido = go.Figure(
                data=[
                    go.Bar(
                        x=centers,
                        y=counts,
                        width=widths,
                        customdata=custom,
                        marker_color=COLORS["secondary"],
                        hovertemplate="Faixa: R$ %{customdata[0]:,.0f} – R$ %{customdata[1]:,.0f}<br>Clientes: %{y}<extra></extra>",
                    )
                ]
            )
            fig_concedido.update_layout(
                **_hist_layout,
                xaxis=dict(type="log", title="Crédito (R$)", tickprefix="R$ ", showgrid=False, showline=False, zeroline=False),
                yaxis=dict(title="Clientes", showgrid=True, gridcolor=COLORS["table_border"], gridwidth=0.5, showline=False, zeroline=False),
            )
            st.plotly_chart(fig_concedido, use_container_width=True, config=PLOTLY_CONFIG)

        with col_2:
            st.caption("Crédito utilizado por cliente (R$)")
            df_credito["credito_utilizado"] = pd.to_numeric(df_credito["credito_utilizado"], errors="coerce")
            series_u = df_credito["credito_utilizado"].to_numpy()
            series_u_pos = series_u[series_u > 0]
            if series_u_pos.size == 0:
                st.info("Não há valores positivos de crédito utilizado para o período selecionado.")
            else:
                nbins_u = 30
                min_val_u = float(series_u_pos.min())
                max_val_u = float(series_u_pos.max())
                if min_val_u == max_val_u:
                    edges_u = np.array([min_val_u * 0.9, min_val_u * 1.1]) if min_val_u > 0 else np.array([1, 2])
                else:
                    start_exp_u = np.floor(np.log10(min_val_u))
                    end_exp_u = np.ceil(np.log10(max_val_u))
                    edges_u = np.logspace(start_exp_u, end_exp_u, num=nbins_u + 1)
                counts_u, bins_u = np.histogram(series_u_pos, bins=edges_u)
                centers_u = (bins_u[:-1] + bins_u[1:]) / 2.0
                widths_u = (bins_u[1:] - bins_u[:-1])
                custom_u = np.stack([bins_u[:-1], bins_u[1:]], axis=1)

                fig_utilizado = go.Figure(
                    data=[
                        go.Bar(
                            x=centers_u,
                            y=counts_u,
                            width=widths_u,
                            customdata=custom_u,
                            marker_color=COLORS["accent"],
                            hovertemplate="Faixa: R$ %{customdata[0]:,.0f} – R$ %{customdata[1]:,.0f}<br>Clientes: %{y}<extra></extra>",
                        )
                    ]
                )
                fig_utilizado.update_layout(
                    **_hist_layout,
                    xaxis=dict(type="log", title="Crédito (R$)", tickprefix="R$ ", showgrid=False, showline=False, zeroline=False),
                    yaxis=dict(title="Clientes", showgrid=True, gridcolor=COLORS["table_border"], gridwidth=0.5, showline=False, zeroline=False),
                )
                st.plotly_chart(fig_utilizado, use_container_width=True, config=PLOTLY_CONFIG)

        st.caption("Percentual de utilização do crédito — escala logarítmica para evidenciar faixas com poucos clientes.")
        fig_pct = px.histogram(
            df_credito,
            x="percentual_utilizado_pct",
            nbins=30,
            range_x=[0, 100],
            labels={"percentual_utilizado_pct": "% Utilizado"},
            template="plotly_white",
            log_y=True,
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig_pct.update_layout(**get_standard_layout(show_legend=False))
        fig_pct.update_yaxes(title_text="Clientes")
        st.plotly_chart(fig_pct, use_container_width=True, config=PLOTLY_CONFIG)

        st.caption("Percentual de utilização do crédito — escala linear para visualizar a distribuição geral.")
        fig_pct2 = px.histogram(
            df_credito,
            x="percentual_utilizado_pct",
            nbins=30,
            range_x=[0, 100],
            labels={"percentual_utilizado_pct": "% Utilizado"},
            template="plotly_white",
            log_y=False,
            color_discrete_sequence=[COLORS["accent"]],
        )
        fig_pct2.update_layout(**get_standard_layout(show_legend=False))
        fig_pct2.update_yaxes(title_text="Clientes")
        st.plotly_chart(fig_pct2, use_container_width=True, config=PLOTLY_CONFIG)


def render_sumario_geral() -> None:
    """Render the 'Sumário Geral' page with narrative structure."""
    inicio = st.session_state.reference_date

    # Beginning: KPI context row
    df_totais = _load_totais(inicio.month, inicio.year)
    _render_kpi_sumario(df_totais)
    st.divider()

    # Middle: detailed breakdowns
    _render_numeros_gerais(df_totais)
    _render_breakdown_lojas()
    _render_breakdown_revendedores()
    _render_evolucao_faturamento()
    _render_distribuicao_credito()


# =============================================================================
# INADIMPLÊNCIA - Section Functions
# =============================================================================


def _render_kpi_inadimplencia(df: pd.DataFrame) -> None:
    """Beginning: KPI summary row for the delinquency page."""
    if df.empty:
        return
    latest = df.sort_values("date").iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Exposição", _fmt_currency(latest.get("exposicao", 0)))
    with col2:
        st.metric("Total Delinquente", _fmt_currency(latest.get("total_delinquente", 0)))
    with col3:
        exp = latest.get("exposicao", 0)
        delinq = latest.get("total_delinquente", 0)
        rate = (delinq / exp * 100) if exp else 0
        st.metric("Taxa de Inadimplência", f"{rate:.1f}%")
    with col4:
        st.metric("Atraso (>2d)", _fmt_currency(latest.get("atraso", 0)))


def _render_evolucao_inadimplencia() -> None:
    """Render the 'Evolução da Inadimplência' section."""
    ref = st.session_state.reference_date
    st.subheader("Evolução da Inadimplência")
    st.caption("Acompanhamento mensal dos valores em atraso por faixa. Tendência crescente requer atenção.")

    periodo = chiclet_selector(
        options=PERIODO_OPTIONS,
        key="inadimplencia_periodo",
        default="Ultimos 6 Meses",
        variant="buttons",
        group_max_fraction=0.5,
    )
    months = _MESES_MAP.get(periodo, 6)
    start_date, end_date = _period_bounds(ref, months)

    df = _load_inadimplencia_evolucao(str(start_date.date()), str(end_date.date()))
    if df.empty:
        st.info("Sem dados de inadimplência para o período selecionado.")
        return

    df = _ensure_cumulative_columns(
        df,
        value_cols=["over_15p", "over_30p", "over_60p", "over_90p"],
        ratio_cols=[
            "delinquencia_over_15",
            "delinquencia_over_30",
            "delinquencia_over_60",
            "delinquencia_over_90",
        ],
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df_long = df.melt(
        id_vars="date",
        value_vars=["exposicao", "total_delinquente", "atraso", "over_15p", "over_30p", "over_60p", "over_90p", "over_180"],
        var_name="bucket",
        value_name="valor",
    )
    df_long["bucket"] = df_long["bucket"].map(BUCKET_LABELS)

    fig = px.line(
        df_long,
        x="date",
        y="valor",
        color="bucket",
        labels={"date": "Data", "valor": "Valor (R$)", "bucket": "Faixa"},
        color_discrete_sequence=PLOTLY_COLORWAY,
        template="plotly_white",
    )
    fig.update_traces(mode="lines")
    fig.update_layout(
        **get_standard_layout(
            legend_title="Faixa de Inadimplência",
            yaxis=dict(
                title="Valor (R$)",
                showgrid=True,
                gridcolor=COLORS["table_border"],
                gridwidth=0.5,
                showline=False,
                zeroline=False,
            ),
            xaxis=dict(
                tickformat="%Y-%m",
                showgrid=False,
                showline=False,
                zeroline=False,
            ),
        )
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def _render_safras_clientes() -> None:
    """Render the 'Análise de Safras Clientes' section."""
    st.subheader("Análise de Safras Clientes")
    st.caption("Curvas de delinquência por safra de relacionamento. Safras mais recentes devem convergir para níveis menores.")

    df_vintage_clientes = _load_vintage_clientes()
    if df_vintage_clientes.empty:
        st.info("Sem dados de safra para o período selecionado.")
        return

    ratio_cols_clientes = [
        "delinquencia",
        "delinquencia_atraso",
        "delinquencia_over_15",
        "delinquencia_over_30",
        "delinquencia_over_60",
        "delinquencia_over_90",
        "delinquencia_over_180",
    ]
    df_vintage = _ensure_cumulative_columns(
        df_vintage_clientes.copy(),
        value_cols=["over_15p", "over_30p", "over_60p", "over_90p"],
        ratio_cols=ratio_cols_clientes,
    )
    df_vintage["mob"] = pd.to_numeric(df_vintage["mob"], errors="coerce").astype(int)
    df_vintage["vintage"] = df_vintage["vintage"].astype(str)
    for col in ratio_cols_clientes:
        df_vintage[col] = pd.to_numeric(df_vintage[col], errors="coerce").fillna(0.0)

    metric_pairs_clientes = [
        ("delinquencia", "Delinquência Total"),
        ("delinquencia_atraso", "Delinquência (>2d)"),
        ("delinquencia_over_15", "Delinquência 15d+"),
        ("delinquencia_over_30", "Delinquência 30d+"),
        ("delinquencia_over_60", "Delinquência 60d+"),
        ("delinquencia_over_90", "Delinquência 90d+"),
        ("delinquencia_over_180", "Delinquência 180d+"),
    ]

    for idx in range(0, len(metric_pairs_clientes), 2):
        cols = st.columns(2)
        for col_placeholder, pair in zip(cols, metric_pairs_clientes[idx:idx + 2]):
            metric, title = pair
            with col_placeholder:
                fig_line = build_vintage_line(df_vintage, metric, title)
                st.plotly_chart(fig_line, use_container_width=True, config=PLOTLY_CONFIG)
        if len(metric_pairs_clientes[idx:idx + 2]) == 1:
            cols[1].empty()


def _render_safras_originacao() -> None:
    """Render the 'Análise de Safras Originação' section."""
    st.subheader("Análise de Safras Originação")
    st.caption("Curvas de delinquência por safra de originação do crédito.")

    df_vintage_origin = _load_vintage_originacao()
    if df_vintage_origin.empty:
        st.info("Sem dados de safra de originação para o período selecionado.")
        return

    ratio_cols_origin = [
        "delinquencia",
        "delinquencia_over_15",
        "delinquencia_over_30",
        "delinquencia_over_60",
        "delinquencia_over_90",
        "delinquencia_over_180",
    ]
    df_vintage = _ensure_cumulative_columns(
        df_vintage_origin.copy(),
        value_cols=["over_15p", "over_30p", "over_60p", "over_90p"],
        ratio_cols=ratio_cols_origin,
    )
    df_vintage["mob"] = pd.to_numeric(df_vintage["mob"], errors="coerce").astype(int)
    df_vintage["vintage"] = df_vintage["vintage"].astype(str)
    for col in ratio_cols_origin:
        df_vintage[col] = pd.to_numeric(df_vintage[col], errors="coerce").fillna(0.0)

    metric_pairs_origin = [
        ("delinquencia", "Delinquência Total"),
        ("delinquencia_over_15", "Delinquência 15d+"),
        ("delinquencia_over_30", "Delinquência 30d+"),
        ("delinquencia_over_60", "Delinquência 60d+"),
        ("delinquencia_over_90", "Delinquência 90d+"),
        ("delinquencia_over_180", "Delinquência 180d+"),
    ]

    for idx in range(0, len(metric_pairs_origin), 2):
        cols = st.columns(2)
        for col_placeholder, pair in zip(cols, metric_pairs_origin[idx:idx + 2]):
            metric, title = pair
            with col_placeholder:
                fig_line = build_vintage_line(df_vintage, metric, title)
                st.plotly_chart(fig_line, use_container_width=True, config=PLOTLY_CONFIG)
        if len(metric_pairs_origin[idx:idx + 2]) == 1:
            cols[1].empty()


def render_inadimplencia() -> None:
    """Render the 'Inadimplência' page with narrative structure."""
    ref = st.session_state.reference_date

    # Beginning: KPI context row (reuses default 6-month window)
    start_date, end_date = _period_bounds(ref, 6)
    df_kpi = _load_inadimplencia_evolucao(str(start_date.date()), str(end_date.date()))
    if not df_kpi.empty:
        df_kpi = _ensure_cumulative_columns(df_kpi)
        df_kpi["date"] = pd.to_datetime(df_kpi["date"])
    _render_kpi_inadimplencia(df_kpi)
    st.divider()

    # Middle: detailed analysis
    _render_evolucao_inadimplencia()
    _render_safras_clientes()
    _render_safras_originacao()
