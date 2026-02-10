from datetime import date, timedelta

import streamlit as st
from components.chiclet import chiclet_selector
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from db import run_query
from components import render_table_with_merged_headers
from styles import get_custom_css, COLORS
import queries

# Plot color palette derived from app theme
PLOTLY_COLORWAY = [COLORS["secondary"], COLORS["accent"], COLORS["primary"], COLORS["danger"]]


def _ensure_cumulative_columns(
    df: pd.DataFrame,
    *,
    value_cols: list[str] | None = None,
    ratio_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Ensure cumulative delinquency column names exist; rename legacy ones when needed."""
    # Snowflake returns uppercase column names, normalize to lowercase
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


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase for consistency."""
    df.columns = df.columns.str.lower()
    return df


def adjust_color(hex_color: str, factor: float) -> str:
    """Adjust color brightness by factor."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def build_vintage_line(df_vintage: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """Build a vintage line chart for the given metric."""
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

    fig_line = go.Figure()
    for vintage, factor in zip(vintages_sorted, factors):
        subset = df_metric[df_metric["vintage"] == vintage].sort_values("mob")
        fig_line.add_trace(
            go.Scatter(
                x=subset["mob"],
                y=subset["percent"],
                mode="lines",
                name=vintage,
                line=dict(color=adjust_color(base_color, factor), width=2),
                hovertemplate=f"Vintage {vintage}<br>MOB %{{x}}<br>{title}: %{{y:.1f}}%<extra></extra>",
            )
        )

    fig_line.update_layout(
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
    return fig_line


# Configuração da página (deve vir antes de qualquer outro comando Streamlit)
st.set_page_config(page_title="CashU | Relatório de Clientes", layout="wide")

# Aplicar estilos customizados
st.markdown(get_custom_css(), unsafe_allow_html=True)


def _init_session_state() -> None:
    if "date_range" not in st.session_state:
        fim = date.today()
        inicio = fim - timedelta(days=30)
        st.session_state.date_range = (inicio, fim)
    if "page" not in st.session_state:
        st.session_state.page = "Sumário Geral"
    if "selected_slug" not in st.session_state:
        st.session_state.selected_slug = None




def _sidebar() -> date:
    st.sidebar.header("Configurações")

    # Slug selector
    sql_slugs = queries.get_available_slugs_query()
    df_slugs = _normalize_columns(run_query(sql_slugs))
    if not df_slugs.empty:
        slugs_list = df_slugs["cd_name_slug"].tolist()
        # Set default to first slug if not already set
        if st.session_state.selected_slug is None or st.session_state.selected_slug not in slugs_list:
            st.session_state.selected_slug = slugs_list[0]
        selected_slug = st.sidebar.selectbox(
            "Marca",
            options=slugs_list,
            index=slugs_list.index(st.session_state.selected_slug),
            key="slug_selector",
        )
        st.session_state.selected_slug = selected_slug
    else:
        st.sidebar.warning("Nenhuma marca encontrada.")
        st.session_state.selected_slug = None

    st.sidebar.divider()

    periodo_input = st.sidebar.date_input(
        "Período",
        min_value=date(2024, 12, 1),
        max_value=date.today(),
        help="Selecione a data de referência.",
    )
    st.session_state.reference_date = periodo_input

    st.sidebar.divider()
    for _label in ["Sumário Geral", "Inadimplência"]:
        if st.session_state.page == _label:
            st.sidebar.markdown(f"<div class='nav-selected'>{_label}</div>", unsafe_allow_html=True)
        else:
            if st.sidebar.button(_label, key=f"nav-{_label}"):
                st.session_state.page = _label
                st.rerun()
    return st.session_state.reference_date


# =============================================================================
# SUMÁRIO GERAL - Section Functions
# =============================================================================


def _render_numeros_gerais() -> None:
    """Render the 'Números Gerais' section with Totais table."""
    inicio = st.session_state.reference_date
    slug = st.session_state.selected_slug
    
    if not slug:
        st.warning("Selecione uma marca para visualizar os dados.")
        return
    
    st.subheader("Números Gerais")

    # Totais
    st.caption("Totais")
    sql_totais = queries.get_totais_query(inicio.month, inicio.year, slug)
    print(sql_totais)
    df_totais = _normalize_columns(run_query(sql_totais))
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


def _render_breakdown_revendedores() -> None:
    """Render the 'Breakdown Revendedores' section by credit status."""
    inicio = st.session_state.reference_date
    slug = st.session_state.selected_slug
    
    if not slug:
        return
    
    st.subheader("Breakdown Revendedores")

    sql = queries.get_breakdown_revendedores_query(inicio.month, inicio.year, slug)
    df = _normalize_columns(run_query(sql))
    
    if df.empty:
        st.info("Sem dados para o período.")
        return
    
    df = df.pivot(index='forma_pagamento', columns='tipo_revendedor', values=['financeiro', 'numero_compras', 'numero_clientes', 'ticket_medio']).fillna(0)

    df = df.swaplevel(0, 1, axis=1)

    tipo_order = ['Possui Crédito CashU', 'Não Possui Crédito CashU']
    metric_order = ['financeiro', 'numero_compras', 'numero_clientes', 'ticket_medio']

    new_columns = [
        (tipo, metric)
        for tipo in tipo_order
        for metric in metric_order
    ]
    df = df.reindex(columns=new_columns)

    df.index.name = None

    metric_display_names = ['R$', '# Compras', '# Clientes', 'Ticket Médio']
    df.columns = df.columns.set_levels(metric_display_names, level=1)

    df = df.sort_index()

    render_table_with_merged_headers(df)


def _render_evolucao_faturamento() -> None:
    """Render the 'Evolução do Faturamento Per Capta' section."""
    inicio = st.session_state.reference_date
    slug = st.session_state.selected_slug
    
    if not slug:
        return
    
    st.subheader("Evolução do Faturamento Per Capta")

    periodo_grafico = chiclet_selector(
        options=["Ultimos 2 Meses", "Ultimos 3 Meses", "Ultimos 6 Meses", "Ultimos 9 Meses", "Ultimos 12 Meses"],
        key="evolucao_faturamento",
        default="Ultimos 2 Meses",
        variant="buttons",
        group_max_fraction=0.5,
    )

    meses_map = {
        "Ultimos 2 Meses": 2,
        "Ultimos 3 Meses": 3,
        "Ultimos 6 Meses": 6,
        "Ultimos 9 Meses": 9,
        "Ultimos 12 Meses": 12,
    }
    meses = meses_map.get(periodo_grafico, 2)

    ref = st.session_state.reference_date
    start_year = ref.year
    start_month = ref.month - (meses - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = pd.Timestamp(start_year, start_month, 1)
    end_date = pd.Timestamp(ref.year, ref.month, 1)

    month_selector = {
        "Ultimos 2 Meses": 2,
        "Ultimos 3 Meses": 3,
        "Ultimos 6 Meses": 6,
        "Ultimos 9 Meses": 9,
        "Ultimos 12 Meses": 12,
    }

    sql = queries.get_faturamento_per_capta_query(str(inicio), month_selector[periodo_grafico], slug)
    df = _normalize_columns(run_query(sql))

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
        fig1.update_layout(
            legend_title_text="Forma de Pagamento",
            paper_bgcolor=COLORS["bg_light"],
            plot_bgcolor=COLORS["bg_light"],
        )
        st.plotly_chart(fig1, width="stretch", config={"displayModeBar": False})

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
        fig2.update_layout(
            legend_title_text="Forma de Pagamento",
            paper_bgcolor=COLORS["bg_light"],
            plot_bgcolor=COLORS["bg_light"],
        )
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})


def _render_distribuicao_credito() -> None:
    """Render the 'Distribuição do Crédito Concedido x Utilização' section."""
    inicio = st.session_state.reference_date
    slug = st.session_state.selected_slug
    
    if not slug:
        return
    
    st.subheader("Distribuição do Crédito Concedido x Utilização")

    filtro_recencia = chiclet_selector(
        options=["Todos", "Compras Últimos 30d", "Compras Últimos 60d", "Compras Últimos 90d"],
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

    sql = queries.get_distribuicao_credito_query(str(inicio), filtro_recencia_sql, slug)
    df_credito = _normalize_columns(run_query(sql))

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
                template="plotly_white",
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(type="log", title="Crédito (R$)", tickprefix="R$ "),
                yaxis=dict(title="Clientes"),
                paper_bgcolor=COLORS["bg_light"],
                plot_bgcolor=COLORS["bg_light"],
            )
            st.plotly_chart(fig_concedido, width="stretch", config={"displayModeBar": False})

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
                    template="plotly_white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(type="log", title="Crédito (R$)", tickprefix="R$ "),
                    yaxis=dict(title="Clientes"),
                    paper_bgcolor=COLORS["bg_light"],
                    plot_bgcolor=COLORS["bg_light"],
                )
                st.plotly_chart(fig_utilizado, width="stretch", config={"displayModeBar": False})

        st.caption("Percentual de utilização do crédito (%)")
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
        fig_pct.update_layout(
            paper_bgcolor=COLORS["bg_light"],
            plot_bgcolor=COLORS["bg_light"],
        )
        fig_pct.update_yaxes(title_text="Clientes")
        st.plotly_chart(fig_pct, width="stretch", config={"displayModeBar": False})

        st.caption("Percentual de clientes com crédito (%)")
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
        fig_pct2.update_layout(
            paper_bgcolor=COLORS["bg_light"],
            plot_bgcolor=COLORS["bg_light"],
        )
        fig_pct2.update_yaxes(title_text="Clientes")
        st.plotly_chart(fig_pct2, width="stretch", config={"displayModeBar": False})


def render_sumario_geral() -> None:
    """Render the 'Sumário Geral' page."""
    _render_numeros_gerais()
    _render_breakdown_revendedores()
    _render_evolucao_faturamento()
    _render_distribuicao_credito()


# =============================================================================
# INADIMPLÊNCIA - Section Functions
# =============================================================================


def _render_evolucao_inadimplencia() -> None:
    """Render the 'Evolução da Inadimplência' section."""
    ref = st.session_state.reference_date
    slug = st.session_state.selected_slug
    
    if not slug:
        st.warning("Selecione uma marca para visualizar os dados.")
        return
    
    st.subheader("Evolução da Inadimplência")

    periodo = chiclet_selector(
        options=["Ultimos 2 Meses", "Ultimos 3 Meses", "Ultimos 6 Meses", "Ultimos 9 Meses", "Ultimos 12 Meses"],
        key="inadimplencia_periodo",
        default="Ultimos 6 Meses",
        variant="buttons",
        group_max_fraction=0.5,
    )
    periodo_map = {
        "Ultimos 2 Meses": 2,
        "Ultimos 3 Meses": 3,
        "Ultimos 6 Meses": 6,
        "Ultimos 9 Meses": 9,
        "Ultimos 12 Meses": 12,
    }
    months = periodo_map.get(periodo, 6)

    start_year = ref.year
    start_month = ref.month - (months - 1)
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = pd.Timestamp(start_year, start_month, 1)
    end_date = pd.Timestamp(ref.year, ref.month, 1)

    sql = queries.get_inadimplencia_evolucao_query(str(start_date.date()), str(end_date.date()), slug)
    df = _normalize_columns(run_query(sql))
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
    bucket_labels = {
        "exposicao": "Exposição",
        "total_delinquente": "Total Delinquente",
        "atraso": "Atraso (>2d)",
        "over_15p": "15d+",
        "over_30p": "30d+",
        "over_60p": "60d+",
        "over_90p": "90d+",
        "over_180": "180d+",
    }
    df_long["bucket"] = df_long["bucket"].map(bucket_labels)

    fig = px.line(
        df_long,
        x="date",
        y="valor",
        color="bucket",
        labels={"date": "Data", "valor": "Valor (R$)", "bucket": "Faixa"},
        color_discrete_sequence=PLOTLY_COLORWAY,
        template="plotly_white",
    )
    fig.update_layout(
        legend_title_text="Faixa de Inadimplência",
        height=420,
        margin=dict(l=40, r=16, t=40, b=40),
        paper_bgcolor=COLORS["bg_light"],
        plot_bgcolor=COLORS["bg_light"],
        font=dict(family="Red Hat Display, sans-serif", color=COLORS["text_primary"]),
        yaxis=dict(gridcolor="#e0e0e0", title="Valor (R$)"),
        xaxis=dict(gridcolor="#e0e0e0", tickformat="%Y-%m"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_safras_clientes() -> None:
    """Render the 'Análise de Safras Clientes' section."""
    slug = st.session_state.selected_slug
    
    if not slug:
        return
    
    st.subheader("Análise de Safras Clientes")

    df_vintage_clientes = _normalize_columns(run_query(queries.get_vintage_clientes_query(slug)))
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
                st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
        if len(metric_pairs_clientes[idx:idx + 2]) == 1:
            cols[1].empty()


def _render_safras_originacao() -> None:
    """Render the 'Análise de Safras Originação' section."""
    slug = st.session_state.selected_slug
    
    if not slug:
        return
    
    st.subheader("Análise de Safras Originação")

    df_vintage_origin = _normalize_columns(run_query(queries.get_vintage_originacao_query(slug)))
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
                st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
        if len(metric_pairs_origin[idx:idx + 2]) == 1:
            cols[1].empty()


def render_inadimplencia() -> None:
    """Render the 'Inadimplência' page."""
    _render_evolucao_inadimplencia()
    _render_safras_clientes()
    _render_safras_originacao()


def main() -> None:
    _init_session_state()

    st.title("CashU | Relatório de Clientes")
    _sidebar()
    pages = {
        "Sumário Geral": render_sumario_geral,
        "Inadimplência": render_inadimplencia,
    }
    pages.get(st.session_state.page, render_sumario_geral)()


if __name__ == "__main__":
    main()
