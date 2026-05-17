"""Report Nobel single-page sections.

Each section is a small block fed by one query in `queries.py`.
All values come from the Nobel loan tape filtered by `data_pagamento IS NULL`
and `fundo = 2` (already in the SQL).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared.components import (
    GridColumnConfig,
    PLOTLY_CONFIG,
    get_standard_layout,
    render_data_grid,
)
from shared.components.html_export import (
    collect_caption,
    collect_chart,
    collect_columns_end,
    collect_columns_start,
    collect_dataframe,
    collect_divider,
    collect_metric,
    collect_pl_chart,
    collect_pl_input,
    collect_pl_metric,
    collect_subheader,
)
from shared.db import run_query
from shared.styles import COLORS

from . import queries


# =============================================================================
# Formatting helpers
# =============================================================================

def _fmt_number(value: float, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    formatted = f"{float(value):,.{decimals}f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _fmt_currency(value: float, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "R$ 0"
    return f"R$ {_fmt_number(value, decimals)}"


def _fmt_percent(value: float, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{_fmt_number(value * 100, decimals)}%"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = out.columns.str.lower()
    for col in ("val", "share"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


# =============================================================================
# Data loader (single query, cached) + aggregation helpers
# =============================================================================

_FAIXA_LEVELS = {"Macro": "macro", "Micro": "micro"}


@st.cache_data(ttl=300, show_spinner="Carregando loan tape do Nobel...")
def _load_loan_tape() -> pd.DataFrame:
    """One Snowflake round-trip; everything else is computed in pandas."""
    df = _normalize_columns(run_query(queries.get_loan_tape_query()))
    for col in ("valor_aberto", "valor_nota"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ("data_vencimento", "data_operacao", "data_hj"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "prazo" in df.columns:
        df["prazo"] = pd.to_numeric(df["prazo"], errors="coerce").astype("Int64")
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def _load_dim_faixas() -> pd.DataFrame:
    """Faixa lookup loaded once and merged in pandas. Cached for an hour."""
    df = _normalize_columns(run_query(queries.get_dim_faixas_query()))
    for col in ("numero", "id_faixa_inova", "id_faixa_micro", "id_faixa_macro"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def _agg_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Group by one column and sum `valor_aberto` into a `val` column."""
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, "val"])
    return (
        df.groupby(col, dropna=False, as_index=False)["valor_aberto"]
        .sum()
        .rename(columns={"valor_aberto": "val"})
        .sort_values("val", ascending=False)
        .reset_index(drop=True)
    )


def _agg_by_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if df.empty or not all(c in df.columns for c in cols):
        return pd.DataFrame(columns=cols + ["val"])
    return (
        df.groupby(cols, dropna=False, as_index=False)["valor_aberto"]
        .sum()
        .rename(columns={"valor_aberto": "val"})
        .sort_values("val", ascending=False)
        .reset_index(drop=True)
    )


def _pivot_faixa(
    df: pd.DataFrame,
    dim_faixas: pd.DataFrame,
    *,
    row_col: str,
    prazo_col: str = "prazo",
    level: str = "macro",
) -> tuple[pd.DataFrame, list[str]]:
    """Pivot `valor_aberto` by ``row_col`` x ``faixa_<level>``.

    Returns ``(pivot, faixa_cols)`` where ``pivot`` already has a "Total geral"
    column (sum of all faixa columns) and the rows are sorted by it desc.
    ``faixa_cols`` is the ordered list of faixa column names (without "Total").
    """
    id_col = f"id_faixa_{level}"
    name_col = f"faixa_{level}"
    if df.empty or dim_faixas.empty or row_col not in df.columns:
        return pd.DataFrame(), []

    merged = df.merge(
        dim_faixas[["numero", id_col, name_col]],
        left_on=prazo_col,
        right_on="numero",
        how="left",
    ).dropna(subset=[name_col])

    if merged.empty:
        return pd.DataFrame(), []

    faixa_cols = (
        merged[[id_col, name_col]]
        .drop_duplicates()
        .sort_values(id_col)[name_col]
        .tolist()
    )

    pivot = pd.pivot_table(
        merged,
        index=row_col,
        columns=name_col,
        values="valor_aberto",
        aggfunc="sum",
        fill_value=0,
    ).reindex(columns=faixa_cols, fill_value=0)

    pivot["Total geral"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total geral", ascending=False).reset_index()
    return pivot, faixa_cols


def _agg_faixa(
    df: pd.DataFrame,
    dim_faixas: pd.DataFrame,
    *,
    prazo_col: str = "prazo",
    level: str = "inova",
) -> pd.DataFrame:
    """Merge the slice of the loan tape with `dim_faixas` and aggregate
    `valor_aberto` by the chosen `faixa_<level>`, sorted by `id_faixa_<level>`.

    Returns a DataFrame with columns ``id_faixa_<level>``, ``faixa_<level>`` and
    ``val``. Empty if any of the inputs are missing.
    """
    id_col = f"id_faixa_{level}"
    name_col = f"faixa_{level}"
    if df.empty or dim_faixas.empty or prazo_col not in df.columns:
        return pd.DataFrame(columns=[id_col, name_col, "val"])

    keep = ["numero", id_col, name_col]
    merged = df.merge(
        dim_faixas[keep],
        left_on=prazo_col,
        right_on="numero",
        how="left",
    )
    return (
        merged.dropna(subset=[name_col])
        .groupby([id_col, name_col], dropna=False, as_index=False)["valor_aberto"]
        .sum()
        .rename(columns={"valor_aberto": "val"})
        .sort_values(id_col)
        .reset_index(drop=True)
    )


# =============================================================================
# Filters (fundo in sidebar, others inline on the page)
# =============================================================================

_PAGE_FILTER_SPECS: list[tuple[str, str]] = [
    ("foco", "Foco"),
    ("papel", "Papel"),
    ("situacao", "Situação"),
    ("status_vencimento", "Status de vencimento"),
    ("cedente_grupo", "Grupo de cedentes"),
    ("sacado_grupo", "Grupo de sacados"),
]


def _apply_fundo_filter(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Sidebar multiselect over `nickname_fundo`.

    Empty selection (``[]``) means "ALL". Returns the filtered df and the
    list of selected nicknames (empty = all).
    """
    st.sidebar.subheader("Fundo")
    if df.empty or "nickname_fundo" not in df.columns:
        st.sidebar.caption("Sem dados de fundo.")
        return df, []

    options = sorted(
        v for v in df["nickname_fundo"].dropna().unique().tolist() if str(v).strip()
    )
    chosen = st.sidebar.multiselect(
        "Selecione um ou mais fundos",
        options=options,
        default=[],
        key="flt_fundo",
        placeholder=f"ALL ({len(options)})",
    )
    if not chosen:
        return df, []
    return df[df["nickname_fundo"].isin(chosen)], chosen


def _apply_page_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Inline multiselect filters rendered above the report."""
    if df.empty:
        return df

    with st.expander("Filtros", expanded=False):
        cols = st.columns(3)
        filtered = df
        for idx, (col, label) in enumerate(_PAGE_FILTER_SPECS):
            if col not in df.columns:
                continue
            options = sorted(
                v for v in df[col].dropna().unique().tolist() if str(v).strip()
            )
            if not options:
                continue
            with cols[idx % 3]:
                chosen = st.multiselect(
                    label,
                    options=options,
                    default=[],
                    key=f"flt_{col}",
                    placeholder=f"Todos ({len(options)})",
                )
            if chosen:
                filtered = filtered[filtered[col].isin(chosen)]

        if st.button("Limpar filtros", use_container_width=False, key="flt_clear"):
            for col, _ in _PAGE_FILTER_SPECS:
                st.session_state.pop(f"flt_{col}", None)
            st.rerun()

    return filtered


def _build_dynamic_title(selected_fundos: list[str]) -> str:
    """Resolve the dashboard title from the fundo selection.

    - ALL or multiple funds  -> "Report Nobel"
    - Exactly one fund       -> "Report {nickname}"
    """
    if len(selected_fundos) == 1:
        return f"Report {selected_fundos[0]}"
    return "Report Nobel"


# =============================================================================
# Chart builders
# =============================================================================

def _wrap_label(text: str, max_chars: int) -> str:
    """Wrap a long string with ``<br>`` at word boundaries.

    Used to keep Y-axis labels narrow on horizontal bar charts placed in
    half-width columns. A single word longer than ``max_chars`` is kept on
    its own line (Plotly will still render it).
    """
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= max_chars:
        return text
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        if len(word) > max_chars and not current:
            lines.append(word)
            continue
        added = len(word) + (1 if current else 0)
        if current_len + added > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += added
    if current:
        lines.append(" ".join(current))
    return "<br>".join(lines)


def _horizontal_bar(
    df: pd.DataFrame,
    *,
    category_col: str,
    value_col: str,
    title: str,
    color: str | None = None,
    max_categories: int | None = None,
    category_label: str | None = None,
    color_map: dict[str, str] | None = None,
    category_order: list[str] | None = None,
    wrap_label_chars: int | None = None,
    total_override: float | None = None,
) -> go.Figure:
    """Horizontal bar chart with currency labels and share percentages.

    Optional ``color_map`` colors each category individually.
    Optional ``category_order`` forces the top-to-bottom order on the Y axis.
    Optional ``total_override`` replaces the denominator used to compute the
    share percentages (e.g. to express each bar as a fraction of PL).
    """
    plot_df = df.dropna(subset=[value_col]).copy()
    total = float(total_override) if total_override and total_override > 0 else plot_df[value_col].sum()
    if max_categories is not None and len(plot_df) > max_categories:
        plot_df = plot_df.head(max_categories)

    if wrap_label_chars:
        plot_df[category_col] = plot_df[category_col].astype(str).map(
            lambda t: _wrap_label(t, wrap_label_chars)
        )
        if color_map is not None:
            color_map = {
                _wrap_label(str(k), wrap_label_chars): v for k, v in color_map.items()
            }
        if category_order is not None:
            category_order = [
                _wrap_label(str(c), wrap_label_chars) for c in category_order
            ]

    plot_df = plot_df.sort_values(value_col, ascending=True)
    plot_df["share"] = np.where(total > 0, plot_df[value_col] / total, np.nan)
    plot_df["label"] = plot_df.apply(
        lambda r: f"<b>{_fmt_currency(r[value_col])}</b> ({_fmt_percent(r['share'], 1)})",
        axis=1,
    )
    plot_df["hover_value"] = plot_df.apply(
        lambda r: f"{_fmt_currency(r[value_col])} ({_fmt_percent(r['share'], 1)})",
        axis=1,
    )

    bar_color = color or COLORS["secondary"]
    cat_label = category_label or category_col.replace("_", " ").capitalize()

    px_kwargs: dict = dict(
        x=value_col,
        y=category_col,
        orientation="h",
        text="label",
        custom_data=["hover_value"],
    )
    if color_map is not None:
        px_kwargs["color"] = category_col
        px_kwargs["color_discrete_map"] = color_map
    else:
        px_kwargs["color_discrete_sequence"] = [bar_color]
    if category_order is not None:
        # Plotly draws category_orders top-to-bottom on horizontal bars,
        # which matches the user-provided ordering as-is.
        px_kwargs["category_orders"] = {category_col: list(category_order)}

    fig = px.bar(plot_df, **px_kwargs)
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=13),
        cliponaxis=False,
        hovertemplate=(
            f"<b>{cat_label}:</b> %{{y}}<br>"
            "<b>Val:</b> %{customdata[0]}<extra></extra>"
        ),
    )
    if wrap_label_chars:
        row_height = 40
        left_margin = 160
        tick_font_size = 11
    else:
        row_height = 32
        left_margin = 140
        tick_font_size = 12

    plot_height = min(720, max(280, row_height * len(plot_df) + 120))
    top_margin = 64 if title else 10
    fig.update_layout(
        **get_standard_layout(
            title=title,
            show_legend=False,
            margin=dict(l=left_margin, r=160, t=top_margin, b=40),
            height=plot_height,
        )
    )
    fig.update_xaxes(showgrid=False, visible=False)
    fig.update_yaxes(showgrid=False, title=None, tickfont=dict(size=tick_font_size))
    return fig


_CURRENCY_VALUE_FORMATTER = (
    "function(params) {"
    " if (params.value == null || params.value === '') return '';"
    " var v = Math.round(Number(params.value));"
    " if (isNaN(v)) return params.value;"
    " return 'R$ ' + v.toLocaleString('pt-BR');"
    " }"
)

_DATE_BR_VALUE_FORMATTER = (
    "function(params) {"
    " if (params.value == null || params.value === '') return '';"
    " var s = String(params.value);"
    " var iso = s.length >= 10 ? s.substring(0, 10) : s;"
    " var parts = iso.split('-');"
    " if (parts.length !== 3) return s;"
    " return parts[2] + '/' + parts[1] + '/' + parts[0];"
    " }"
)


def _render_cedente_faixa_section(
    df: pd.DataFrame,
    dim_faixas: pd.DataFrame,
    *,
    title: str,
    caption: str,
    prazo_col: str,
    radio_key: str,
    grid_key_prefix: str,
    empty_message: str = "Sem dados para grupo de cedentes.",
) -> None:
    """Subheader + radio (Macro/Micro) + pivot grid for Cedentes x Faixa.

    Used twice on the page: once for "A Vencer" (prazo positivo) and once
    para "Vencidos" (prazo invertido em dias de atraso).
    """
    header_col, level_col = st.columns([3, 2], vertical_alignment="bottom")
    with header_col:
        st.subheader(title)
        collect_subheader(title)
    with level_col:
        level_label = st.radio(
            "Detalhe das faixas",
            options=list(_FAIXA_LEVELS.keys()),
            index=0,
            horizontal=True,
            key=radio_key,
            label_visibility="collapsed",
        )
    level = _FAIXA_LEVELS[level_label]

    st.caption(caption)
    collect_caption(caption)

    pivot, faixa_cols = _pivot_faixa(
        df,
        dim_faixas,
        row_col="cedente_grupo",
        prazo_col=prazo_col,
        level=level,
    )
    if pivot.empty:
        st.info(empty_message)
        return

    numeric_df = pivot.rename(columns={"cedente_grupo": "Grupo Cedente"}).copy()
    ordered_cols = ["Grupo Cedente"] + faixa_cols + ["Total geral"]
    numeric_df = numeric_df[ordered_cols]

    totals_row = {"Grupo Cedente": "Total geral"}
    for col in faixa_cols:
        totals_row[col] = float(pivot[col].sum())
    totals_row["Total geral"] = float(pivot["Total geral"].sum())

    column_config = {
        "Grupo Cedente": GridColumnConfig(min_width=220, wrap_text=True, auto_height=True),
        "Total geral": GridColumnConfig(
            min_width=140, sortable=True, value_formatter=_CURRENCY_VALUE_FORMATTER
        ),
    }
    for col in faixa_cols:
        column_config[col] = GridColumnConfig(
            min_width=130, sortable=True, value_formatter=_CURRENCY_VALUE_FORMATTER
        )

    render_data_grid(
        numeric_df,
        key=f"{grid_key_prefix}-{level}",
        table_preset="standard",
        page_size=15,
        enable_quick_filter=True,
        quick_filter_placeholder="Filtrar grupo...",
        pinned_bottom_rows=[totals_row],
        column_config=column_config,
        width="100%",
        center=False,
    )

    export_df = numeric_df.copy()
    for col in faixa_cols + ["Total geral"]:
        export_df[col] = export_df[col].map(_fmt_currency)
    collect_dataframe(export_df)


def _balanco_chart_height(n_rows: int) -> int:
    """Shared height (px) so the 100%-vencido grid matches the bar chart."""
    return int(min(820, max(360, 42 * n_rows + 160)))


def _build_balanco_figure(
    pivot: pd.DataFrame,
    *,
    wrap_label_chars: int = 20,
    grand_total: float | None = None,
) -> go.Figure:
    """Build a 100%-stacked horizontal bar chart from a pre-sorted pivot
    containing ``cedente_grupo``, ``A Vencer``, ``Vencido``, ``Total``,
    ``pct_av`` and ``pct_vc`` columns.

    When ``grand_total`` is provided, each bar gets an outside label on the
    right with ``R$ Total (% da carteira)``.
    """
    pivot = pivot.copy()
    pivot["label"] = pivot["cedente_grupo"].astype(str).map(
        lambda t: _wrap_label(t, wrap_label_chars)
    )
    pivot["av_hover"] = pivot.apply(
        lambda r: f"{_fmt_currency(r['A Vencer'])} ({_fmt_percent(r['pct_av'], 1)})",
        axis=1,
    )
    pivot["vc_hover"] = pivot.apply(
        lambda r: f"{_fmt_currency(r['Vencido'])} ({_fmt_percent(r['pct_vc'], 1)})",
        axis=1,
    )
    pivot["av_pct"] = pivot["pct_av"] * 100
    pivot["vc_pct"] = pivot["pct_vc"] * 100
    pivot["av_label"] = pivot["pct_av"].map(
        lambda v: _fmt_percent(v, 1) if v >= 0.08 else ""
    )
    pivot["vc_label"] = pivot["pct_vc"].map(
        lambda v: _fmt_percent(v, 1) if v >= 0.08 else ""
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=pivot["label"],
            x=pivot["av_pct"],
            orientation="h",
            name="A Vencer",
            marker=dict(color=COLORS["accent"]),
            text=pivot["av_label"],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="white", size=11),
            customdata=pivot[["av_hover"]].values,
            hovertemplate=(
                "<b>Grupo Cedente:</b> %{y}<br>"
                "<b>A Vencer:</b> %{customdata[0]}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Bar(
            y=pivot["label"],
            x=pivot["vc_pct"],
            orientation="h",
            name="Vencido",
            marker=dict(color=COLORS["secondary"]),
            text=pivot["vc_label"],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="white", size=11),
            customdata=pivot[["vc_hover"]].values,
            hovertemplate=(
                "<b>Grupo Cedente:</b> %{y}<br>"
                "<b>Vencido:</b> %{customdata[0]}<extra></extra>"
            ),
        )
    )

    show_outside = grand_total is not None and grand_total > 0
    right_margin = 170 if show_outside else 30

    plot_height = _balanco_chart_height(len(pivot))
    fig.update_layout(
        **get_standard_layout(
            title="",
            show_legend=True,
            margin=dict(l=160, r=right_margin, t=10, b=40),
            height=plot_height,
        )
    )
    fig.update_layout(
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, title=None, range=[0, 100], ticksuffix="%")
    fig.update_yaxes(showgrid=False, title=None, tickfont=dict(size=11))

    if show_outside:
        for _, row in pivot.iterrows():
            share = float(row["Total"]) / float(grand_total) if grand_total else 0.0
            fig.add_annotation(
                xref="paper",
                x=1.01,
                yref="y",
                y=row["label"],
                text=(
                    f"<b>{_fmt_currency(row['Total'])}</b> "
                    f"({_fmt_percent(share, 1)})"
                ),
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=11),
                align="left",
            )

    return fig


def _render_cedente_balanco(
    df: pd.DataFrame,
    *,
    max_categories: int = 20,
    wrap_label_chars: int = 20,
) -> list[go.Figure]:
    """Two side-by-side 100%-stacked bar charts for cedente carteira balance.

    - Left:  cedentes parcialmente em atraso (% Vencido < 100%), ordenados
      por % Vencido desc; empate -> maior valor total primeiro.
    - Right: cedentes com 100% da carteira vencida, ordenados por valor desc.
    """
    needed = {"status_vencimento", "cedente_grupo", "valor_aberto"}
    if df.empty or not needed.issubset(df.columns):
        st.info("Sem dados para balanço por grupo de cedentes.")
        return []

    base = df.dropna(subset=["valor_aberto"]).copy()
    pivot = pd.pivot_table(
        base,
        index="cedente_grupo",
        columns="status_vencimento",
        values="valor_aberto",
        aggfunc="sum",
        fill_value=0,
    )
    for col in ("A Vencer", "Vencido"):
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot["Total"] = pivot["A Vencer"] + pivot["Vencido"]
    pivot = pivot[pivot["Total"] > 0].copy()
    if pivot.empty:
        st.info("Sem dados para balanço por grupo de cedentes.")
        return []

    pivot["pct_av"] = pivot["A Vencer"] / pivot["Total"]
    pivot["pct_vc"] = pivot["Vencido"] / pivot["Total"]
    grand_total = float(pivot["Total"].sum())

    full_vc_mask = pivot["pct_vc"] >= 1.0
    pivot_mix = pivot[~full_vc_mask].copy()
    pivot_full = pivot[full_vc_mask].copy()

    pivot_mix = (
        pivot_mix.sort_values(["pct_vc", "Total"], ascending=[False, False])
        .head(max_categories)
        .iloc[::-1]
        .reset_index()
    )
    pivot_full = (
        pivot_full.sort_values("Total", ascending=False).reset_index()
    )

    shared_height = _balanco_chart_height(len(pivot_mix))

    figs: list[go.Figure] = []
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Parcialmente em atraso")
        st.caption("Ordenado por % Vencido (empate = maior valor total).")
        if pivot_mix.empty:
            st.info("Sem grupos parcialmente em atraso.")
        else:
            fig_mix = _build_balanco_figure(
                pivot_mix,
                wrap_label_chars=wrap_label_chars,
                grand_total=grand_total,
            )
            st.plotly_chart(fig_mix, use_container_width=True, config=PLOTLY_CONFIG)
            figs.append(fig_mix)

    with col_r:
        st.markdown("#### 100% Vencido")
        st.caption("Lista completa de grupos com toda a carteira em aberto vencida.")
        if pivot_full.empty:
            st.info("Sem grupos com carteira 100% vencida.")
        else:
            full_list = pivot_full[["cedente_grupo", "Vencido"]].rename(
                columns={"cedente_grupo": "Grupo Cedente", "Vencido": "Valor Vencido"}
            )
            total_vencido = float(full_list["Valor Vencido"].sum())
            totals_row = {
                "Grupo Cedente": f"Total ({len(full_list)} grupos)",
                "Valor Vencido": total_vencido,
            }
            render_data_grid(
                full_list,
                key="cedente-100-vencido-grid",
                table_preset="standard",
                page_size=max(15, min(40, len(full_list))),
                height=shared_height,
                enable_quick_filter=True,
                quick_filter_placeholder="Filtrar grupo...",
                pinned_bottom_rows=[totals_row],
                column_config={
                    "Grupo Cedente": GridColumnConfig(
                        min_width=220, wrap_text=True, auto_height=True
                    ),
                    "Valor Vencido": GridColumnConfig(
                        min_width=160,
                        sortable=True,
                        value_formatter=_CURRENCY_VALUE_FORMATTER,
                    ),
                },
                width="100%",
                center=False,
            )
            export_full = full_list.copy()
            export_full["Valor Vencido"] = export_full["Valor Vencido"].map(_fmt_currency)
            collect_dataframe(export_full)

    return figs


def _render_operacao_detalhe(df: pd.DataFrame) -> None:
    """Operation-level grid showing the active portfolio (one row per title)."""
    if df.empty:
        st.info("Sem operações para detalhamento.")
        return

    cols_order = [
        ("codigo_operacao", "Operação"),
        ("nickname_fundo", "Fundo"),
        ("cedente_grupo", "Grupo Cedente"),
        ("nome_cedente", "Cedente"),
        ("sacado_grupo", "Grupo Sacado"),
        ("nome_sacado", "Sacado"),
        ("foco", "Foco"),
        ("papel", "Papel"),
        ("situacao", "Situação"),
        ("data_operacao", "Data Operação"),
        ("data_vencimento", "Vencimento"),
        ("prazo", "Prazo"),
        ("status_vencimento", "Status"),
        ("valor_nota", "Valor Nota"),
    ]
    available = [(c, lbl) for c, lbl in cols_order if c in df.columns]
    if not available:
        st.info("Sem colunas suficientes para o detalhamento.")
        return

    base = df[[c for c, _ in available]].copy()

    for date_col in ("data_operacao", "data_vencimento"):
        if date_col in base.columns:
            base[date_col] = pd.to_datetime(base[date_col], errors="coerce")

    sort_keys: list[tuple[str, bool]] = []
    if "data_operacao" in base.columns:
        sort_keys.append(("data_operacao", False))
    if "nome_cedente" in base.columns:
        sort_keys.append(("nome_cedente", True))
    if "data_vencimento" in base.columns:
        sort_keys.append(("data_vencimento", True))
    if sort_keys:
        base = base.sort_values(
            [k for k, _ in sort_keys],
            ascending=[asc for _, asc in sort_keys],
        )

    detalhe = base.rename(columns=dict(available))

    if "Prazo" in detalhe.columns:
        detalhe["Prazo"] = pd.to_numeric(detalhe["Prazo"], errors="coerce").astype("Int64")

    column_config: dict[str, GridColumnConfig] = {
        "Operação": GridColumnConfig(min_width=110),
        "Fundo": GridColumnConfig(min_width=110),
        "Grupo Cedente": GridColumnConfig(min_width=180, wrap_text=True, auto_height=True),
        "Cedente": GridColumnConfig(min_width=220, wrap_text=True, auto_height=True),
        "Grupo Sacado": GridColumnConfig(min_width=180, wrap_text=True, auto_height=True),
        "Sacado": GridColumnConfig(min_width=220, wrap_text=True, auto_height=True),
        "Foco": GridColumnConfig(min_width=110),
        "Papel": GridColumnConfig(min_width=110),
        "Situação": GridColumnConfig(min_width=120),
        "Data Operação": GridColumnConfig(
            min_width=120, sortable=True, value_formatter=_DATE_BR_VALUE_FORMATTER
        ),
        "Vencimento": GridColumnConfig(
            min_width=120, sortable=True, value_formatter=_DATE_BR_VALUE_FORMATTER
        ),
        "Prazo": GridColumnConfig(min_width=80, sortable=True),
        "Status": GridColumnConfig(min_width=110),
        "Valor Nota": GridColumnConfig(
            min_width=140, sortable=True, value_formatter=_CURRENCY_VALUE_FORMATTER
        ),
    }
    column_config = {k: v for k, v in column_config.items() if k in detalhe.columns}

    render_data_grid(
        detalhe,
        key="operacao-detalhe-grid",
        table_preset="large",
        page_size=20,
        enable_quick_filter=True,
        quick_filter_placeholder="Filtrar operação / cedente / sacado...",
        column_config=column_config,
        width="100%",
        center=False,
    )

    export_df = detalhe.copy()
    for date_col in ("Data Operação", "Vencimento"):
        if date_col in export_df.columns:
            export_df[date_col] = pd.to_datetime(
                export_df[date_col], errors="coerce"
            ).dt.strftime("%d/%m/%Y").fillna("-")
    if "Valor Nota" in export_df.columns:
        export_df["Valor Nota"] = export_df["Valor Nota"].map(_fmt_currency)
    collect_dataframe(export_df)


def _render_concentration_block(
    df: pd.DataFrame,
    *,
    category_col: str,
    category_label: str,
    block_title: str,
    bar_color: str,
    max_categories: int = 20,
    total_override: float | None = None,
) -> tuple[
    list[tuple[str, str]],
    go.Figure | None,
    list[tuple[str, float]],
    list[float],
    list[str],
]:
    """Top-N concentration block: 4 compact KPI cards (Top 1/5/10/20) + bar chart.

    Percentages are computed against the full ``df`` universe (after the
    caller has already applied any business filter, e.g. "A Vencer").

    If ``total_override`` is provided (e.g. PL of the fund), it replaces the
    denominator used for both the Top-N KPIs and the bar share labels.

    Returns a 5-tuple:
      * ``metric_pairs``: list of ``(label, formatted_percent)``
      * ``figure``: Plotly figure (or ``None`` when empty)
      * ``raw_metrics``: list of ``(label, raw_top_n_value)`` for the HTML
        export to recompute shares interactively
      * ``raw_bar_values``: per-bar absolute values in the same order Plotly
        rendered the bars
      * ``raw_bar_currencies``: pre-formatted currency strings for each bar
    """
    st.markdown(f"#### {block_title}")

    agg = _agg_by(df, category_col)
    if agg.empty:
        st.info(f"Sem dados para {category_label.lower()}.")
        return [], None, [], [], []

    use_override = bool(total_override and total_override > 0)
    total = float(total_override) if use_override else float(agg["val"].sum())
    top_specs = [1, 5, 10, 20]
    kpi_cols = st.columns(len(top_specs))
    metrics: list[tuple[str, str]] = []
    raw_metrics: list[tuple[str, float]] = []
    for col, n in zip(kpi_cols, top_specs):
        top_n_val = float(agg["val"].head(n).sum())
        pct = top_n_val / total if total > 0 else 0.0
        label = f"Top {n}"
        value = _fmt_percent(pct, 1)
        with col:
            st.markdown(
                f"""
                <div style="line-height:1.15;margin:4px 0 8px 0;">
                  <div style="color:#6b6b6b;font-size:12px;font-weight:600;letter-spacing:0.02em;">{label}</div>
                  <div style="color:{bar_color};font-size:22px;font-weight:700;margin-top:2px;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        metrics.append((label, value))
        raw_metrics.append((label, top_n_val))

    fig = _horizontal_bar(
        agg,
        category_col=category_col,
        category_label=category_label,
        value_col="val",
        title="",
        color=bar_color,
        max_categories=max_categories,
        wrap_label_chars=24,
        total_override=total if use_override else None,
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    bar_agg = agg.head(max_categories).copy() if max_categories else agg.copy()
    bar_agg = bar_agg.sort_values("val", ascending=True)
    raw_bar_values = [float(v) for v in bar_agg["val"].tolist()]
    raw_bar_currencies = [_fmt_currency(v) for v in raw_bar_values]
    return metrics, fig, raw_metrics, raw_bar_values, raw_bar_currencies


def _table_with_total(
    df: pd.DataFrame,
    *,
    category_cols: list[str],
    value_col: str,
    column_labels: dict[str, str],
    key: str,
    page_size: int | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """Return a formatted DataFrame + a 'Total' pinned row for the data grid."""
    tbl = df.copy()
    total_value = tbl[value_col].sum()
    tbl["share"] = np.where(total_value > 0, tbl[value_col] / total_value, np.nan)
    tbl[value_col] = tbl[value_col].map(_fmt_currency)
    tbl["share"] = tbl["share"].map(lambda v: _fmt_percent(v, 1))

    rename_map = {**column_labels, value_col: column_labels.get(value_col, "Valor"), "share": "Participação"}
    tbl = tbl.rename(columns=rename_map)

    cat_labels = [column_labels[c] for c in category_cols]
    val_label = column_labels.get(value_col, "Valor")
    ordered_cols = cat_labels + [val_label, "Participação"]
    tbl = tbl[ordered_cols]

    total_row_data: dict = {col: "" for col in ordered_cols}
    total_row_data[cat_labels[0]] = "Total"
    total_row_data[val_label] = _fmt_currency(total_value)
    total_row_data["Participação"] = "100,0%"

    return tbl, [total_row_data]


# =============================================================================
# Main page renderer
# =============================================================================

def render_carteira() -> None:  # noqa: C901 - layout-heavy renderer
    loan_tape = _load_loan_tape()
    df, selected_fundos = _apply_fundo_filter(loan_tape)

    page_title = _build_dynamic_title(selected_fundos)
    st.title(page_title)

    if "data_hj" in df.columns and not df.empty:
        ref_dt = pd.to_datetime(df["data_hj"], errors="coerce").max()
        if pd.notna(ref_dt):
            ref_str = ref_dt.strftime("%d/%m/%Y")
            st.caption(f"Data de referência: **{ref_str}**")
            collect_caption(f"Data de referência: {ref_str}")

    df = _apply_page_filters(df)

    # -------------------------------------------------------------------------
    # 1. Carteira Total (single big metric)
    # -------------------------------------------------------------------------
    st.subheader("Carteira")
    collect_subheader("Carteira A")
    #st.caption("Valor em aberto da carteira do Fundo Nobel (data_pagamento nula).")
    #collect_caption("Valor em aberto da carteira do Fundo Nobel (data_pagamento nula).")

    total_val = float(df["valor_aberto"].sum()) if not df.empty else 0.0

    st.metric("Carteira em aberto", _fmt_currency(total_val))
    collect_columns_start(1)
    collect_metric("Carteira em aberto", _fmt_currency(total_val))
    collect_columns_end()

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 2. Concentração por Foco + Papel (side by side)
    # -------------------------------------------------------------------------
    st.subheader("Concentração")
    collect_subheader("Concentração")

    foco_df = _agg_by(df, "foco")
    papel_df = _agg_by(df, "papel")
    sit_df = _agg_by(df, "situacao")

    c1, c2, c3 = st.columns(3)
    if foco_df.empty:
        with c1:
            st.info("Sem dados para concentração por foco.")
        fig_foco = None
    else:
        fig_foco = _horizontal_bar(
            foco_df,
            category_col="foco",
            category_label="Foco",
            value_col="val",
            title="Foco",
            color=COLORS["secondary"],
        )
        with c1:
            st.plotly_chart(fig_foco, use_container_width=True, config=PLOTLY_CONFIG)

    if papel_df.empty:
        with c2:
            st.info("Sem dados para concentração por papel.")
        fig_papel = None
    else:
        fig_papel = _horizontal_bar(
            papel_df,
            category_col="papel",
            category_label="Papel",
            value_col="val",
            title="Papel",
            color=COLORS["accent"],
        )
        with c2:
            st.plotly_chart(fig_papel, use_container_width=True, config=PLOTLY_CONFIG)

    if sit_df.empty:
        with c3:
            st.info("Sem dados para situação.")
        fig_sit = None
    else:
        fig_sit = _horizontal_bar(
            sit_df,
            category_col="situacao",
            category_label="Situação",
            value_col="val",
            title="Situação",
            color=COLORS["primary"],
        )
        with c3:
            st.plotly_chart(fig_sit, use_container_width=True, config=PLOTLY_CONFIG)

    collect_columns_start(3)
    if fig_foco is not None:
        collect_chart(fig_foco)
    if fig_papel is not None:
        collect_chart(fig_papel)
    if fig_sit is not None:
        collect_chart(fig_sit)
    collect_columns_end()

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 3. Vencimentos da Carteira (Status + Faixa a Vencer + Faixa dos Vencidos)
    # -------------------------------------------------------------------------
    st.subheader("Vencimentos da Carteira")
    collect_subheader("Vencimentos da Carteira")

    status_color_map = {
        "A Vencer": COLORS["accent"],       # laranja
        "Vencido": COLORS["secondary"],     # roxo
    }
    status_df = _agg_by(df, "status_vencimento")

    dim_faixas = _load_dim_faixas()

    # A Vencer: usa prazo positivo direto.
    df_a_vencer = (
        df[df["status_vencimento"] == "A Vencer"]
        if "status_vencimento" in df.columns
        else df.iloc[0:0]
    )

    # Vencido: inverte o sinal do prazo e descarta o 0 (somente atraso > 0).
    if "status_vencimento" in df.columns and "prazo" in df.columns:
        df_vencido = df[df["status_vencimento"] == "Vencido"].copy()
        df_vencido["prazo_atraso"] = -df_vencido["prazo"]
        df_vencido = df_vencido[df_vencido["prazo_atraso"] > 0]
    else:
        df_vencido = df.iloc[0:0].assign(prazo_atraso=pd.Series(dtype="Int64"))

    c1, c2, c3 = st.columns(3)
    fig_status = None
    fig_faixa_av = None
    fig_faixa_vc = None

    with c1:
        title_col, level_col = st.columns([2, 3], vertical_alignment="bottom")
        with title_col:
            st.markdown("**Status de Vencimento**")
        with level_col:
            # Espaço reservado para alinhar com os radios dos outros 2 gráficos.
            st.markdown("&nbsp;", unsafe_allow_html=True)
    if status_df.empty:
        with c1:
            st.info("Sem dados para status de vencimento.")
    else:
        fig_status = _horizontal_bar(
            status_df,
            category_col="status_vencimento",
            category_label="Status de vencimento",
            value_col="val",
            title="",
            color_map=status_color_map,
            category_order=["A Vencer", "Vencido"],
        )
        with c1:
            st.plotly_chart(fig_status, use_container_width=True, config=PLOTLY_CONFIG)

    with c2:
        title_col, level_col = st.columns([2, 3], vertical_alignment="bottom")
        with title_col:
            st.markdown("**Faixa a Vencer**")
        with level_col:
            level_av_label = st.radio(
                "Detalhe",
                options=list(_FAIXA_LEVELS.keys()),
                index=0,
                horizontal=True,
                key="faixa_level_av",
                label_visibility="collapsed",
            )
    level_av = _FAIXA_LEVELS[level_av_label]
    col_av = f"faixa_{level_av}"
    faixa_a_vencer_df = _agg_faixa(
        df_a_vencer, dim_faixas, prazo_col="prazo", level=level_av
    )
    if faixa_a_vencer_df.empty:
        with c2:
            st.info("Sem dados para faixa a vencer.")
        fig_faixa_av = None
    else:
        fig_faixa_av = _horizontal_bar(
            faixa_a_vencer_df,
            category_col=col_av,
            category_label="Faixa a vencer",
            value_col="val",
            title="",
            color=COLORS["accent"],
            category_order=faixa_a_vencer_df[col_av].tolist(),
        )
        with c2:
            st.plotly_chart(fig_faixa_av, use_container_width=True, config=PLOTLY_CONFIG)

    with c3:
        title_col, level_col = st.columns([2, 3], vertical_alignment="bottom")
        with title_col:
            st.markdown("**Faixa dos Vencidos**")
        with level_col:
            level_vc_label = st.radio(
                "Detalhe",
                options=list(_FAIXA_LEVELS.keys()),
                index=0,
                horizontal=True,
                key="faixa_level_vc",
                label_visibility="collapsed",
            )
    level_vc = _FAIXA_LEVELS[level_vc_label]
    col_vc = f"faixa_{level_vc}"
    faixa_vencidos_df = _agg_faixa(
        df_vencido, dim_faixas, prazo_col="prazo_atraso", level=level_vc
    )
    if faixa_vencidos_df.empty:
        with c3:
            st.info("Sem dados para faixa dos vencidos.")
        fig_faixa_vc = None
    else:
        fig_faixa_vc = _horizontal_bar(
            faixa_vencidos_df,
            category_col=col_vc,
            category_label="Faixa dos vencidos",
            value_col="val",
            title="",
            color=COLORS["secondary"],
            category_order=faixa_vencidos_df[col_vc].tolist(),
        )
        with c3:
            st.plotly_chart(fig_faixa_vc, use_container_width=True, config=PLOTLY_CONFIG)

    collect_columns_start(3)
    if fig_status is not None:
        collect_chart(fig_status)
    if fig_faixa_av is not None:
        collect_chart(fig_faixa_av)
    if fig_faixa_vc is not None:
        collect_chart(fig_faixa_vc)
    collect_columns_end()

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 3.5 Concentração por Cedentes e Sacados (Top-N + bar chart)
    # -------------------------------------------------------------------------
    st.subheader("Concentração por Cedentes e Sacados")
    collect_subheader("Concentração por Cedentes e Sacados")
    st.caption("Participação dos maiores grupos na carteira a vencer (Top 1, 5, 10 e 20).")
    collect_caption("Participação dos maiores grupos na carteira a vencer (Top 1, 5, 10 e 20).")

    df_a_vencer_conc = (
        df[df["status_vencimento"] == "A Vencer"]
        if "status_vencimento" in df.columns
        else df
    )

    pl_col, _ = st.columns([1, 3])
    with pl_col:
        pl_input = st.number_input(
            "Patrimônio Líquido (R$)",
            min_value=0.0,
            value=None,
            step=100_000.0,
            format="%.2f",
            help=(
                "Opcional. Se informado, os percentuais Top 1/5/10/20 e do "
                "gráfico são calculados sobre o PL em vez do total da "
                "carteira a vencer."
            ),
            key="conc_pl_input",
            placeholder="Deixe vazio para usar o total da carteira",
        )
    pl_override = float(pl_input) if pl_input and pl_input > 0 else None
    if pl_override is not None:
        pl_msg = f"Percentuais calculados sobre PL informado: {_fmt_currency(pl_override)}"
        st.caption(pl_msg)
        collect_caption(pl_msg)

    conc_left, conc_right = st.columns(2)
    with conc_left:
        (
            ced_metrics,
            fig_ced_conc,
            ced_raw_metrics,
            ced_raw_bars,
            ced_raw_cur,
        ) = _render_concentration_block(
            df_a_vencer_conc,
            category_col="cedente_grupo",
            category_label="Grupo Cedente",
            block_title="Grupo de Cedentes",
            bar_color=COLORS["secondary"],
            total_override=pl_override,
        )
    with conc_right:
        (
            sac_metrics,
            fig_sac_conc,
            sac_raw_metrics,
            sac_raw_bars,
            sac_raw_cur,
        ) = _render_concentration_block(
            df_a_vencer_conc,
            category_col="sacado_grupo",
            category_label="Grupo Sacado",
            block_title="Grupo de Sacados",
            bar_color=COLORS["accent"],
            total_override=pl_override,
        )

    conc_default_total = (
        float(df_a_vencer_conc["valor_aberto"].sum())
        if "valor_aberto" in df_a_vencer_conc.columns and not df_a_vencer_conc.empty
        else 0.0
    )
    pl_scope = "conc_main"
    collect_pl_input(
        pl_scope,
        default_total=conc_default_total,
        label="Patrimônio Líquido (R$)",
        help_text="Vazio = % sobre o total da carteira a vencer.",
    )

    collect_columns_start(2)
    for label, raw_val in ced_raw_metrics:
        collect_pl_metric(label, raw_val, scope_id=pl_scope, color=COLORS["secondary"])
    if fig_ced_conc is not None:
        collect_pl_chart(
            fig_ced_conc,
            scope_id=pl_scope,
            raw_values=ced_raw_bars,
            currencies=ced_raw_cur,
        )
    for label, raw_val in sac_raw_metrics:
        collect_pl_metric(label, raw_val, scope_id=pl_scope, color=COLORS["accent"])
    if fig_sac_conc is not None:
        collect_pl_chart(
            fig_sac_conc,
            scope_id=pl_scope,
            raw_values=sac_raw_bars,
            currencies=sac_raw_cur,
        )
    collect_columns_end()

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 4. Grupo de Cedentes (pivot por faixa) - A Vencer
    # -------------------------------------------------------------------------
    if "status_vencimento" in df.columns and "prazo" in df.columns:
        df_ced_av = df[df["status_vencimento"] == "A Vencer"]
    elif "prazo" in df.columns:
        df_ced_av = df[df["prazo"] >= 0]
    else:
        df_ced_av = df.iloc[0:0]

    _render_cedente_faixa_section(
        df_ced_av,
        dim_faixas,
        title="Concentração por Grupo de Cedentes",
        caption="Carteira a vencer por grupo de cedentes, distribuída em faixas de prazo.",
        prazo_col="prazo",
        radio_key="faixa_level_ced_av",
        grid_key_prefix="ced-faixa-grid-av",
    )

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 5. Grupo de Cedentes (pivot por faixa) - Vencidos
    # -------------------------------------------------------------------------
    if "status_vencimento" in df.columns and "prazo" in df.columns:
        df_ced_vc = df[df["status_vencimento"] == "Vencido"].copy()
        df_ced_vc["prazo_atraso"] = (-df_ced_vc["prazo"]).astype("Int64")
        df_ced_vc = df_ced_vc[df_ced_vc["prazo_atraso"] > 0]
    else:
        df_ced_vc = df.iloc[0:0].assign(prazo_atraso=pd.Series(dtype="Int64"))

    _render_cedente_faixa_section(
        df_ced_vc,
        dim_faixas,
        title="Concentração por Grupo de Cedentes (Vencidos)",
        caption="Carteira vencida por grupo de cedentes, distribuída em faixas de dias de atraso.",
        prazo_col="prazo_atraso",
        radio_key="faixa_level_ced_vc",
        grid_key_prefix="ced-faixa-grid-vc",
        empty_message="Sem dados de vencidos para grupo de cedentes.",
    )

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 6. Balanço por Grupo de Cedentes (A Vencer x Vencido empilhado)
    # -------------------------------------------------------------------------
    st.subheader("Balanço por Grupo de Cedentes")
    collect_subheader("Balanço por Grupo de Cedentes")
    st.caption(
        "Distribuição da carteira em aberto entre A Vencer e Vencido por grupo de "
        "cedentes (top 20 por valor total)."
    )
    collect_caption(
        "Distribuição da carteira em aberto entre A Vencer e Vencido por grupo de "
        "cedentes (top 20 por valor total)."
    )

    collect_columns_start(2)
    for fig in _render_cedente_balanco(df):
        collect_chart(fig)
    collect_columns_end()

    st.divider()
    collect_divider()

    # -------------------------------------------------------------------------
    # 7. Detalhamento por Operação
    # -------------------------------------------------------------------------
    st.subheader("Detalhamento por Operação")
    collect_subheader("Detalhamento por Operação")
    st.caption("Detalhamento ativo da carteira por operação (uma linha por título em aberto).")
    collect_caption("Detalhamento ativo da carteira por operação (uma linha por título em aberto).")

    _render_operacao_detalhe(df)
