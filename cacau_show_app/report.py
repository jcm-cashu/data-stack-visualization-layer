"""
HTML report generator for the Cacau Show dashboard.
Produces a self-contained HTML file with embedded Plotly charts and styled tables.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.table import render_table_with_merged_headers
from db import run_query
from styles import COLORS
import queries

PLOTLY_COLORWAY = [COLORS["secondary"], COLORS["accent"], COLORS["primary"], COLORS["danger"]]


# ---------------------------------------------------------------------------
# Shared utility functions (mirrored from app.py to avoid circular import)
# ---------------------------------------------------------------------------

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower()
    return df


def _ensure_cumulative_columns(
    df: pd.DataFrame,
    *,
    value_cols: list[str] | None = None,
    ratio_cols: list[str] | None = None,
) -> pd.DataFrame:
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


def _adjust_color(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    r = max(0, min(255, int(int(hex_color[0:2], 16) * factor)))
    g = max(0, min(255, int(int(hex_color[2:4], 16) * factor)))
    b = max(0, min(255, int(int(hex_color[4:6], 16) * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _build_vintage_line(df_vintage: pd.DataFrame, metric: str, title: str) -> go.Figure:
    df_metric = df_vintage[["vintage", "mob", metric]].copy()
    df_metric["percent"] = df_metric[metric].astype(float) * 100.0

    def vintage_to_ts(v: str) -> pd.Timestamp:
        try:
            return pd.Timestamp(f"{v}-01")
        except Exception:
            return pd.Timestamp.now()

    vintages_sorted = sorted(df_metric["vintage"].unique(), key=vintage_to_ts)
    n_vintages = len(vintages_sorted)
    base_color = COLORS["primary"]
    factors = np.linspace(0.4, 1.0, n_vintages) if n_vintages > 1 else [1.0]

    fig = go.Figure()
    for vintage, factor in zip(vintages_sorted, factors):
        subset = df_metric[df_metric["vintage"] == vintage].sort_values("mob")
        fig.add_trace(
            go.Scatter(
                x=subset["mob"],
                y=subset["percent"],
                mode="lines",
                name=vintage,
                line=dict(color=_adjust_color(base_color, factor), width=2),
                hovertemplate=f"Vintage {vintage}<br>MOB %{{x}}<br>{title}: %{{y:.1f}}%<extra></extra>",
            )
        )
    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=10, r=10, t=40, b=40),
        paper_bgcolor=COLORS["bg_light"],
        plot_bgcolor=COLORS["bg_light"],
        font=dict(family="Red Hat Display, sans-serif", color=COLORS["text_primary"]),
        legend_title_text="Vintage",
        yaxis=dict(title="Delinquência (%)", gridcolor="#e0e0e0"),
        xaxis=dict(title="MOB", gridcolor="#e0e0e0", dtick=1),
    )
    return fig


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _fig_html(fig: go.Figure) -> str:
    """Return embeddable HTML for a Plotly figure (no full page, CDN loaded separately)."""
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _section(title: str, content: str) -> str:
    return f'<section><h2>{title}</h2>\n{content}\n</section>\n'


def _row(items: list[str]) -> str:
    """Flex row with equal-width columns."""
    cols = "".join(f'<div class="col">{item}</div>' for item in items)
    return f'<div class="row">{cols}</div>\n'


def _caption(text: str) -> str:
    return f'<p class="caption">{text}</p>\n'


def _info(text: str) -> str:
    return f'<div class="info-box">{text}</div>\n'


# ---------------------------------------------------------------------------
# Report CSS
# ---------------------------------------------------------------------------

def _report_css() -> str:
    return f"""
    @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Red Hat Display', sans-serif;
        background-color: {COLORS['bg_light']};
        color: {COLORS['text_primary']};
        padding: 40px 48px;
        max-width: 1400px;
        margin: 0 auto;
    }}
    .report-header {{
        border-bottom: 3px solid {COLORS['primary']};
        padding-bottom: 16px;
        margin-bottom: 32px;
    }}
    .report-header h1 {{
        font-weight: 800; font-size: 28px; letter-spacing: -0.02em;
    }}
    .report-header p {{
        color: {COLORS['text_secondary']}; font-size: 14px; margin-top: 6px;
    }}
    section {{
        margin-bottom: 40px;
        page-break-inside: avoid;
    }}
    h2 {{
        color: {COLORS['secondary']};
        font-weight: 700; font-size: 20px;
        margin-bottom: 16px; padding-bottom: 6px;
        border-bottom: 2px solid {COLORS['table_border']};
    }}
    h3 {{
        color: {COLORS['text_primary']};
        font-weight: 600; font-size: 16px;
        margin-bottom: 10px;
    }}
    .caption {{
        color: {COLORS['text_secondary']};
        font-size: 13px; font-weight: 500;
        margin-bottom: 8px;
    }}
    .row {{
        display: flex; gap: 24px; margin-bottom: 24px;
    }}
    .col {{
        flex: 1; min-width: 0;
    }}
    .info-box {{
        background: #e8f4fd;
        border-left: 4px solid {COLORS['secondary']};
        padding: 12px 16px; border-radius: 4px;
        font-size: 14px; color: {COLORS['text_secondary']};
        margin-bottom: 16px;
    }}
    .table-scroll-container {{
        width: 100%; overflow-x: auto; margin-bottom: 16px;
    }}
    .plotly-chart {{
        margin-bottom: 20px;
    }}
    .report-footer {{
        margin-top: 48px; padding-top: 16px;
        border-top: 1px solid {COLORS['table_border']};
        color: {COLORS['text_secondary']}; font-size: 12px;
        text-align: center;
    }}
    @media print {{
        body {{ padding: 20px; }}
        section {{ page-break-inside: avoid; }}
    }}
    """


# ---------------------------------------------------------------------------
# Page: Sumário Geral
# ---------------------------------------------------------------------------

def _build_numeros_gerais(ref_date: date) -> str:
    month, year = ref_date.month, ref_date.year
    parts: list[str] = []

    # Totais
    sql_totais = queries.get_totais_query(month, year)
    df_totais = _normalize_columns(run_query(sql_totais))
    if df_totais.empty:
        totais_html = _info("Sem dados para o período.")
    else:
        r = df_totais.iloc[0]
        metric_labels = ["R$", "R$ CashU", "# Compras", "# Clientes", "# Clientes com Crédito", "Ticket Médio"]
        metric_values = [
            r.get("financeiro", 0), r.get("financeiro_cashu", 0),
            r.get("numero_compras", 0), r.get("numero_clientes", 0),
            r.get("clientes_com_credito", 0), r.get("ticket_medio", 0.0),
        ]
        df_view = pd.DataFrame({"Total": metric_values}, index=metric_labels)
        totais_html = _caption("Totais") + render_table_with_merged_headers(
            df_view, index_label="Métrica", show_percent=False, table_id="rpt-totais", return_html=True,
        )

    # Por Habilitação
    sql_hab = queries.get_habilitacao_query(month, year)
    df_hab = _normalize_columns(run_query(sql_hab))
    if df_hab.empty:
        hab_html = _info("Sem dados para o período.")
    else:
        long_hab = df_hab.melt(id_vars="status_habilitada", var_name="metric", value_name="valor")
        hab_pivot = (
            long_hab.pivot(index="metric", columns="status_habilitada", values="valor")
            .reindex(index=["financeiro", "financeiro_cashu", "numero_compras", "numero_clientes", "clientes_com_credito", "ticket_medio"])
        )
        hab_pivot.index = ["R$", "R$ CashU", "# Compras", "# Clientes", "# Clientes com Crédito", "Ticket Médio"]
        for c in ["Habilitada", "Não Habilitada"]:
            if c not in hab_pivot.columns:
                hab_pivot[c] = 0
        hab_pivot = hab_pivot[["Habilitada", "Não Habilitada"]]
        hab_html = _caption("Por Habilitação") + render_table_with_merged_headers(
            hab_pivot, index_label="Métrica", show_percent=False, table_id="rpt-hab", return_html=True,
        )

    # Por Tier
    sql_tier = queries.get_tier_query(month, year)
    df_tier = _normalize_columns(run_query(sql_tier))
    if df_tier.empty:
        tier_html = _info("Sem dados para o período.")
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
        tier_html = _caption("Por Tier") + render_table_with_merged_headers(
            tier_pivot, index_label="Métrica", show_percent=False, table_id="rpt-tier", return_html=True,
        )

    parts.append(_row([totais_html, hab_html, tier_html]))
    return _section("Números Gerais", "\n".join(parts))


def _build_breakdown_lojas(ref_date: date) -> str:
    month, year = ref_date.month, ref_date.year

    # Read current filter values from session state (defaults if not set)
    hab_sel = st.session_state.get("selector_habilitacao", "Todas")
    tier_sel = st.session_state.get("selector_tier", "Todos")

    hab_map = {"Habilitada": "and loja_habilitada_flag = true", "Não Habilitada": "and loja_habilitada_flag = false"}
    tier_map = {t: f"and tier_loja = '{t}'" for t in ["A", "B", "C", "D", "E", "Sem Tier"]}
    habilitacao_filter = hab_map.get(hab_sel, "")
    tier_filter = tier_map.get(tier_sel, "")

    sql = queries.get_breakdown_lojas_query(month, year, habilitacao_filter, tier_filter)
    df = _normalize_columns(run_query(sql))
    parts: list[str] = []

    filter_note = f"Habilitação: {hab_sel} | Tier: {tier_sel}"
    parts.append(_caption(filter_note))

    if df.empty:
        parts.append(_info("Sem dados para o período."))
    else:
        df = df.pivot(index="forma_pagamento", columns="tipo_loja",
                       values=["financeiro", "numero_compras", "numero_clientes", "ticket_medio"]).fillna(0)
        df = df.swaplevel(0, 1, axis=1)
        tipo_order = ["Franquia", "Loja Própria", "Sem Classificação"]
        metric_order = ["financeiro", "numero_clientes", "numero_compras", "ticket_medio"]
        new_columns = [(t, m) for t in tipo_order for m in metric_order]
        df = df.reindex(columns=new_columns)
        df.index.name = None
        df.columns = df.columns.set_levels(["R$", "# Clientes", "# Compras", "Ticket Médio"], level=1)
        df = df.sort_index()
        parts.append(render_table_with_merged_headers(df, table_id="rpt-breakdown-lojas", return_html=True))

    # Histogram
    sql_perc = queries.get_perc_credito_query(month, year, habilitacao_filter, tier_filter)
    df_perc = _normalize_columns(run_query(sql_perc))
    if df_perc.empty:
        parts.append(_info("Sem dados para o histograma."))
    else:
        bin_edges = np.arange(0, 101, 5)
        bin_labels = [f"{i}\u2013{i+5}%" for i in bin_edges[:-1]]
        df_perc = df_perc.copy()
        df_perc["perc_com_credito_pct"] = (
            pd.to_numeric(df_perc["perc_com_credito"], errors="coerce").fillna(0) * 100
        ).clip(lower=0, upper=100)
        df_perc["credito_bin"] = pd.cut(df_perc["perc_com_credito_pct"], bins=bin_edges, labels=bin_labels, include_lowest=True, right=False)
        bin_counts = df_perc.groupby("credito_bin", observed=True).size().reset_index(name="numero_lojas")
        bin_order_map = {label: idx for idx, label in enumerate(bin_labels)}
        bin_counts["ordering_index"] = bin_counts["credito_bin"].map(bin_order_map)
        bin_counts = bin_counts.sort_values("ordering_index")

        fig = go.Figure(data=[go.Bar(
            x=bin_counts["credito_bin"].astype(str).tolist(),
            y=bin_counts["numero_lojas"].tolist(),
            marker=dict(color=COLORS["primary"], line=dict(color="#333", width=0.6)),
        )])
        fig.update_layout(
            title="Histograma do Percentual de Cobertura de Crédito por Loja",
            template="plotly_white", height=420,
            margin=dict(l=40, r=16, t=40, b=40),
            paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
            font=dict(family="Red Hat Display, sans-serif", color=COLORS["text_primary"], size=12),
            xaxis=dict(title="% Clientes com Crédito", type="category", categoryorder="array", categoryarray=bin_labels, showgrid=False),
            yaxis=dict(title="# Lojas", gridcolor="#e0e0e0"),
        )
        parts.append(f'<div class="plotly-chart">{_fig_html(fig)}</div>')

    return _section("Breakdown Lojas", "\n".join(parts))


def _build_breakdown_revendedores(ref_date: date) -> str:
    month, year = ref_date.month, ref_date.year
    sql = queries.get_breakdown_revendedores_query(month, year)
    df = _normalize_columns(run_query(sql))
    if df.empty:
        return _section("Breakdown Revendedores", _info("Sem dados para o período."))

    df = df.pivot(index="forma_pagamento", columns=["status_habilitada", "tipo_revendedor"],
                   values=["financeiro", "numero_compras", "numero_clientes", "ticket_medio"]).fillna(0)
    df = df.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)
    status_order = ["Habilitada", "Não Habilitada"]
    tipo_order = ["Possui Crédito CashU", "Não Possui Crédito CashU"]
    metric_order = ["financeiro", "numero_compras", "numero_clientes", "ticket_medio"]
    new_columns = [(s, t, m) for s in status_order for t in tipo_order for m in metric_order]
    df = df.reindex(columns=new_columns)
    df.index.name = None
    df.columns = df.columns.set_levels(["R$", "# Compras", "# Clientes", "Ticket Médio"], level=2)
    df = df.sort_index()
    table_html = render_table_with_merged_headers(df, table_id="rpt-breakdown-rev", return_html=True)
    return _section("Breakdown Revendedores", table_html)


def _build_evolucao_faturamento(ref_date: date) -> str:
    periodo_sel = st.session_state.get("evolucao_faturamento", "Ultimos 6 Meses")
    meses_map = {
        "Ultimos 2 Meses": 2, "Ultimos 3 Meses": 3, "Ultimos 6 Meses": 6,
        "Ultimos 9 Meses": 9, "Ultimos 12 Meses": 12,
    }
    meses = meses_map.get(periodo_sel, 6)

    start_year, start_month = ref_date.year, ref_date.month - (meses - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = pd.Timestamp(start_year, start_month, 1)
    end_date = pd.Timestamp(ref_date.year, ref_date.month, 1)

    sql_fc = queries.get_faturamento_per_capta_query(str(ref_date), meses)
    df = _normalize_columns(run_query(sql_fc))
    parts: list[str] = [_caption(f"Período: {periodo_sel}")]

    if df.empty:
        parts.append(_info("Sem dados para o período."))
    else:
        items: list[str] = []
        for label, tipo in [("Possui Crédito CashU", "Possui Crédito CashU"),
                             ("Não Possui Crédito CashU", "Não Possui Crédito CashU")]:
            subset = df[df["tipo_revendedor"] == tipo]
            dfp = (
                subset.pivot(index="date", columns="forma_pagamento", values="financeiro_per_capta")
                .sort_index().fillna(0)
            )
            df_long = dfp.reset_index().melt(id_vars="date", var_name="forma_pagamento", value_name="financeiro_per_capta")
            fig = px.line(
                df_long, x="date", y="financeiro_per_capta", color="forma_pagamento",
                color_discrete_sequence=PLOTLY_COLORWAY,
                labels={"date": "Data", "financeiro_per_capta": "R$", "forma_pagamento": "Forma de Pagamento"},
                template="plotly_white",
            )
            fig.update_layout(
                title=label,
                legend_title_text="Forma de Pagamento",
                paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
            )
            items.append(f'{_caption(label)}<div class="plotly-chart">{_fig_html(fig)}</div>')
        parts.append(_row(items))

    return _section("Evolução do Faturamento Per Capta", "\n".join(parts))


def _build_distribuicao_credito(ref_date: date) -> str:
    recencia_sel = st.session_state.get("filtro_recencia", "Todos")
    recencia_map = {
        "Todos": "", "Compras Últimos 30d": "and filtro_recencia <= 30",
        "Compras Últimos 60d": "and filtro_recencia <= 60",
        "Compras Últimos 90d": "and filtro_recencia <= 90",
    }
    filtro_sql = recencia_map.get(recencia_sel, "")
    sql = queries.get_distribuicao_credito_query(str(ref_date), filtro_sql)
    df_credito = _normalize_columns(run_query(sql))
    parts: list[str] = [_caption(f"Filtro Recência: {recencia_sel}")]

    if df_credito.empty:
        parts.append(_info("Não há dados de crédito para o período selecionado."))
        return _section("Distribuição do Crédito Concedido x Utilização", "\n".join(parts))

    df_credito["credito_disponivel"] = pd.to_numeric(df_credito["credito_disponivel"], errors="coerce")
    df_credito = df_credito[df_credito["credito_disponivel"] > 0].copy()
    if "percentual_utilizado" in df_credito.columns:
        df_credito["percentual_utilizado_pct"] = (df_credito["percentual_utilizado"] * 100).clip(0, 100)
    else:
        df_credito["percentual_utilizado_pct"] = pd.NA

    # Crédito concedido histogram
    nbins = 30
    series = df_credito["credito_disponivel"].to_numpy()
    min_val, max_val = float(series.min()), float(series.max())
    if min_val == max_val:
        edges = np.array([min_val * 0.9, min_val * 1.1]) if min_val > 0 else np.array([1, 2])
    else:
        edges = np.logspace(np.floor(np.log10(min_val)), np.ceil(np.log10(max_val)), num=nbins + 1)
    counts, bins = np.histogram(series, bins=edges)
    centers = (bins[:-1] + bins[1:]) / 2.0
    widths = bins[1:] - bins[:-1]
    custom = np.stack([bins[:-1], bins[1:]], axis=1)
    fig_concedido = go.Figure(data=[go.Bar(
        x=centers, y=counts, width=widths, customdata=custom,
        marker_color=COLORS["secondary"],
        hovertemplate="Faixa: R$ %{customdata[0]:,.0f} \u2013 R$ %{customdata[1]:,.0f}<br>Clientes: %{y}<extra></extra>",
    )])
    fig_concedido.update_layout(
        title="Crédito concedido por cliente (R$)",
        template="plotly_white", margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(type="log", title="Crédito (R$)", tickprefix="R$ "),
        yaxis=dict(title="Clientes"),
        paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
    )

    # Crédito utilizado histogram
    df_credito["credito_utilizado"] = pd.to_numeric(df_credito["credito_utilizado"], errors="coerce")
    series_u = df_credito["credito_utilizado"].to_numpy()
    series_u_pos = series_u[series_u > 0]
    if series_u_pos.size == 0:
        utilizado_html = _info("Não há valores positivos de crédito utilizado.")
    else:
        min_u, max_u = float(series_u_pos.min()), float(series_u_pos.max())
        if min_u == max_u:
            edges_u = np.array([min_u * 0.9, min_u * 1.1]) if min_u > 0 else np.array([1, 2])
        else:
            edges_u = np.logspace(np.floor(np.log10(min_u)), np.ceil(np.log10(max_u)), num=nbins + 1)
        counts_u, bins_u = np.histogram(series_u_pos, bins=edges_u)
        centers_u = (bins_u[:-1] + bins_u[1:]) / 2.0
        widths_u = bins_u[1:] - bins_u[:-1]
        custom_u = np.stack([bins_u[:-1], bins_u[1:]], axis=1)
        fig_utilizado = go.Figure(data=[go.Bar(
            x=centers_u, y=counts_u, width=widths_u, customdata=custom_u,
            marker_color=COLORS["accent"],
            hovertemplate="Faixa: R$ %{customdata[0]:,.0f} \u2013 R$ %{customdata[1]:,.0f}<br>Clientes: %{y}<extra></extra>",
        )])
        fig_utilizado.update_layout(
            title="Crédito utilizado por cliente (R$)",
            template="plotly_white", margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(type="log", title="Crédito (R$)", tickprefix="R$ "),
            yaxis=dict(title="Clientes"),
            paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
        )
        utilizado_html = f'<div class="plotly-chart">{_fig_html(fig_utilizado)}</div>'

    parts.append(_row([
        f'<div class="plotly-chart">{_fig_html(fig_concedido)}</div>',
        utilizado_html,
    ]))

    # Percentual de utilização histograms
    fig_pct = px.histogram(
        df_credito, x="percentual_utilizado_pct", histnorm="percent", nbins=30,
        range_x=[0, 100], labels={"percentual_utilizado_pct": "% Utilizado"},
        template="plotly_white", log_y=True, color_discrete_sequence=[COLORS["primary"]],
    )
    fig_pct.update_layout(
        title="Percentual de utilização do crédito (%)",
        paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
    )
    fig_pct.update_yaxes(title_text="Clientes")
    parts.append(f'<div class="plotly-chart">{_fig_html(fig_pct)}</div>')

    fig_pct2 = px.histogram(
        df_credito, x="percentual_utilizado_pct", histnorm="percent", nbins=30,
        range_x=[0, 100], labels={"percentual_utilizado_pct": "% Utilizado"},
        template="plotly_white", log_y=False, color_discrete_sequence=[COLORS["accent"]],
    )
    fig_pct2.update_layout(
        title="Percentual de clientes com crédito (%)",
        paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
    )
    fig_pct2.update_yaxes(title_text="Clientes")
    parts.append(f'<div class="plotly-chart">{_fig_html(fig_pct2)}</div>')

    return _section("Distribuição do Crédito Concedido x Utilização", "\n".join(parts))


# ---------------------------------------------------------------------------
# Page: Inadimplência
# ---------------------------------------------------------------------------

def _build_evolucao_inadimplencia(ref_date: date) -> str:
    periodo_sel = st.session_state.get("inadimplencia_periodo", "Ultimos 6 Meses")
    periodo_map = {
        "Ultimos 2 Meses": 2, "Ultimos 3 Meses": 3, "Ultimos 6 Meses": 6,
        "Ultimos 9 Meses": 9, "Ultimos 12 Meses": 12,
    }
    months = periodo_map.get(periodo_sel, 6)
    start_year, start_month = ref_date.year, ref_date.month - (months - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = pd.Timestamp(start_year, start_month, 1)
    end_date = pd.Timestamp(ref_date.year, ref_date.month, 1)

    sql = queries.get_inadimplencia_evolucao_query(str(start_date.date()), str(end_date.date()))
    df = _normalize_columns(run_query(sql))
    parts: list[str] = [_caption(f"Período: {periodo_sel}")]

    if df.empty:
        parts.append(_info("Sem dados de inadimplência para o período selecionado."))
    else:
        df = _ensure_cumulative_columns(
            df,
            value_cols=["over_15p", "over_30p", "over_60p", "over_90p"],
            ratio_cols=["delinquencia_over_15", "delinquencia_over_30", "delinquencia_over_60", "delinquencia_over_90"],
        )
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df_long = df.melt(
            id_vars="date",
            value_vars=["exposicao", "total_delinquente", "atraso", "over_15p", "over_30p", "over_60p", "over_90p", "over_180"],
            var_name="bucket", value_name="valor",
        )
        bucket_labels = {
            "exposicao": "Exposição", "total_delinquente": "Total Delinquente",
            "atraso": "Atraso (>2d)", "over_15p": "15d+", "over_30p": "30d+",
            "over_60p": "60d+", "over_90p": "90d+", "over_180": "180d+",
        }
        df_long["bucket"] = df_long["bucket"].map(bucket_labels)
        fig = px.line(
            df_long, x="date", y="valor", color="bucket",
            labels={"date": "Data", "valor": "Valor (R$)", "bucket": "Faixa"},
            color_discrete_sequence=PLOTLY_COLORWAY, template="plotly_white",
        )
        fig.update_layout(
            legend_title_text="Faixa de Inadimplência", height=420,
            margin=dict(l=40, r=16, t=40, b=40),
            paper_bgcolor=COLORS["bg_light"], plot_bgcolor=COLORS["bg_light"],
            font=dict(family="Red Hat Display, sans-serif", color=COLORS["text_primary"]),
            yaxis=dict(gridcolor="#e0e0e0", title="Valor (R$)"),
            xaxis=dict(gridcolor="#e0e0e0", tickformat="%Y-%m"),
        )
        parts.append(f'<div class="plotly-chart">{_fig_html(fig)}</div>')

    return _section("Evolução da Inadimplência", "\n".join(parts))


def _build_safras_clientes() -> str:
    df_vintage_raw = _normalize_columns(run_query(queries.VINTAGE_CLIENTES_QUERY))
    if df_vintage_raw.empty:
        return _section("Análise de Safras Clientes", _info("Sem dados de safra para o período selecionado."))

    ratio_cols = [
        "delinquencia", "delinquencia_atraso", "delinquencia_over_15",
        "delinquencia_over_30", "delinquencia_over_60", "delinquencia_over_90", "delinquencia_over_180",
    ]
    df_vintage = _ensure_cumulative_columns(
        df_vintage_raw.copy(),
        value_cols=["over_15p", "over_30p", "over_60p", "over_90p"],
        ratio_cols=ratio_cols,
    )
    df_vintage["mob"] = pd.to_numeric(df_vintage["mob"], errors="coerce").astype(int)
    df_vintage["vintage"] = df_vintage["vintage"].astype(str)
    for col in ratio_cols:
        df_vintage[col] = pd.to_numeric(df_vintage[col], errors="coerce").fillna(0.0)

    metric_pairs = [
        ("delinquencia", "Delinquência Total"), ("delinquencia_atraso", "Delinquência (>2d)"),
        ("delinquencia_over_15", "Delinquência 15d+"), ("delinquencia_over_30", "Delinquência 30d+"),
        ("delinquencia_over_60", "Delinquência 60d+"), ("delinquencia_over_90", "Delinquência 90d+"),
        ("delinquencia_over_180", "Delinquência 180d+"),
    ]
    parts: list[str] = []
    for idx in range(0, len(metric_pairs), 2):
        row_items: list[str] = []
        for metric, title in metric_pairs[idx:idx + 2]:
            fig = _build_vintage_line(df_vintage, metric, title)
            row_items.append(f'<div class="plotly-chart">{_fig_html(fig)}</div>')
        parts.append(_row(row_items))

    return _section("Análise de Safras Clientes", "\n".join(parts))


def _build_safras_originacao() -> str:
    df_vintage_raw = _normalize_columns(run_query(queries.VINTAGE_ORIGINACAO_QUERY))
    if df_vintage_raw.empty:
        return _section("Análise de Safras Originação", _info("Sem dados de safra de originação para o período selecionado."))

    ratio_cols = [
        "delinquencia", "delinquencia_over_15", "delinquencia_over_30",
        "delinquencia_over_60", "delinquencia_over_90", "delinquencia_over_180",
    ]
    df_vintage = _ensure_cumulative_columns(
        df_vintage_raw.copy(),
        value_cols=["over_15p", "over_30p", "over_60p", "over_90p"],
        ratio_cols=ratio_cols,
    )
    df_vintage["mob"] = pd.to_numeric(df_vintage["mob"], errors="coerce").astype(int)
    df_vintage["vintage"] = df_vintage["vintage"].astype(str)
    for col in ratio_cols:
        df_vintage[col] = pd.to_numeric(df_vintage[col], errors="coerce").fillna(0.0)

    metric_pairs = [
        ("delinquencia", "Delinquência Total"), ("delinquencia_over_15", "Delinquência 15d+"),
        ("delinquencia_over_30", "Delinquência 30d+"), ("delinquencia_over_60", "Delinquência 60d+"),
        ("delinquencia_over_90", "Delinquência 90d+"), ("delinquencia_over_180", "Delinquência 180d+"),
    ]
    parts: list[str] = []
    for idx in range(0, len(metric_pairs), 2):
        row_items: list[str] = []
        for metric, title in metric_pairs[idx:idx + 2]:
            fig = _build_vintage_line(df_vintage, metric, title)
            row_items.append(f'<div class="plotly-chart">{_fig_html(fig)}</div>')
        parts.append(_row(row_items))

    return _section("Análise de Safras Originação", "\n".join(parts))


# ---------------------------------------------------------------------------
# Main report entry point
# ---------------------------------------------------------------------------

def generate_report(page: str, ref_date: date) -> str:
    """Generate a self-contained HTML report for the given page.

    Args:
        page: The page name (e.g. "Sumário Geral" or "Inadimplência").
        ref_date: The reference date selected in the sidebar.

    Returns:
        A complete HTML document as a string.
    """
    if page == "Sumário Geral":
        body = (
            _build_numeros_gerais(ref_date)
            + _build_breakdown_lojas(ref_date)
            + _build_breakdown_revendedores(ref_date)
            + _build_evolucao_faturamento(ref_date)
            + _build_distribuicao_credito(ref_date)
        )
    elif page == "Inadimplência":
        body = (
            _build_evolucao_inadimplencia(ref_date)
            + _build_safras_clientes()
            + _build_safras_originacao()
        )
    else:
        body = _info(f"Página '{page}' não suportada para exportação.")

    now_str = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
    ref_str = ref_date.strftime("%d/%m/%Y") if isinstance(ref_date, date) else str(ref_date)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CashU | Cacau Show - {page}</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>{_report_css()}</style>
</head>
<body>
    <div class="report-header">
        <h1>CashU | Cacau Show</h1>
        <p>Relatório: <strong>{page}</strong> &nbsp;|&nbsp; Data de referência: <strong>{ref_str}</strong> &nbsp;|&nbsp; Gerado em: {now_str}</p>
    </div>
    {body}
    <div class="report-footer">
        Relatório gerado automaticamente pelo dashboard CashU | Cacau Show
    </div>
</body>
</html>"""
    return html
