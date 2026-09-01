"""Report Inova sections built from the original R report logic."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared.components import (
    GridColumnConfig,
    PLOTLY_COLORWAY,
    PLOTLY_CONFIG,
    chiclet_selector,
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
    collect_selector_end,
    collect_selector_option,
    collect_selector_start,
    collect_subheader,
)
from shared.db import run_query
from shared.styles import COLORS

from . import queries
from .dashboard_config import (
    AGING_LEVELS,
    COHORT_BASIS_OPTIONS,
    DPD_EDGES,
    PD_HORIZON_OPTIONS,
    PDD_BY_BUCKET,
    PERIODO_OPTIONS,
    ROLLING_WINDOW_OPTIONS,
    SELLER_DRILLDOWN_DEFAULT,
)

_MESES_MAP = {"Últimos 3 Meses": 3, "Últimos 6 Meses": 6, "Últimos 12 Meses": 12}
_PD_DAYS_MAP = {"15 dias": 15, "30 dias": 30, "90 dias": 90}
_WINDOW_DAYS_MAP = {"30 dias": 30, "45 dias": 45, "60 dias": 60, "90 dias": 90}

_COHORT_COL = {"expiration": "data_vencimento", "acquisition": "data_antecipacao"}
_COHORT_BY_LABEL = {"Por vencimento": "expiration", "Por aquisição": "acquisition"}
_COHORT_TITLE = {"expiration": "safras por vencimento", "acquisition": "safras por aquisição"}

_PERF_COLUMNS = [
    "period",
    "cohort_ead",
    "eligible_ead",
    "matured_ead_share",
    "cohort_titles",
    "eligible_titles",
    "matured_titles_share",
    "defaulted_ead",
    "pd",
    "lgd",
    "pe",
]

_PERF_TABLE_LABELS = {
    "period": "Período",
    "cohort_ead": "EAD da safra",
    "eligible_ead": "EAD elegível",
    "matured_ead_share": "% maturado (EAD)",
    "cohort_titles": "Nº títulos",
    "eligible_titles": "Nº títulos elegíveis",
    "matured_titles_share": "% maturado (títulos)",
    "defaulted_ead": "EAD inadimplente",
    "pd": "PD",
    "lgd": "LGD",
    "pe": "PE",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = out.columns.str.lower()
    return out


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator is None or denominator == 0 or pd.isna(denominator):
        return float("nan")
    return float(numerator) / float(denominator)


def _weighted_average(values: pd.Series, weights: pd.Series) -> float:
    tmp = pd.DataFrame({"value": pd.to_numeric(values, errors="coerce"), "weight": pd.to_numeric(weights, errors="coerce")})
    tmp = tmp.replace([np.inf, -np.inf], np.nan).dropna()
    tmp = tmp[tmp["weight"] > 0]
    if tmp.empty:
        return float("nan")
    return float(np.average(tmp["value"], weights=tmp["weight"]))


def _hhi(shares: pd.Series) -> float:
    clean = pd.to_numeric(shares, errors="coerce").fillna(0)
    return float((clean.pow(2)).sum() * 10_000)


def _fmt_currency(value: float) -> str:
    if value is None or pd.isna(value):
        return "R$ 0,00"
    return f"R$ {_fmt_number(value, 2)}"


def _fmt_percent(value: float, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{_fmt_number(value * 100, decimals)}%"


def _fmt_number(value: float, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    formatted = f"{float(value):,.{decimals}f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _format_grid_ptbr(
    df: pd.DataFrame,
    *,
    currency_cols: list[str] | None = None,
    percent_cols: list[str] | None = None,
    integer_cols: list[str] | None = None,
    number_cols: list[str] | None = None,
    date_cols: list[str] | None = None,
    decimals: int = 2,
) -> pd.DataFrame:
    out = df.copy()
    currency_cols = currency_cols or []
    percent_cols = percent_cols or []
    integer_cols = integer_cols or []
    number_cols = number_cols or []
    date_cols = date_cols or []

    for col in currency_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").map(_fmt_currency)
    for col in percent_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").map(lambda v: _fmt_percent(v, 1))
    for col in integer_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").map(lambda v: "-" if pd.isna(v) else _fmt_number(v, 0))
    for col in number_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").map(lambda v: "-" if pd.isna(v) else _fmt_number(v, decimals))
    for col in date_cols:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("-")
    return out


def get_default_reference_date() -> date:
    """Expose Snowflake-backed default reference date for app state init."""
    return _load_reference_date()


def _period_bounds(ref: date, meses: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = (pd.Timestamp(ref) - pd.DateOffset(months=meses - 1)).replace(day=1)
    end = pd.Timestamp(ref).replace(day=1)
    return start, end


@st.cache_data(ttl=300, show_spinner=False)
def _load_reference_date() -> date:
    ref_df = _normalize_columns(run_query(queries.get_reference_date_query()))
    if ref_df.empty or pd.isna(ref_df.loc[0, "reference_date"]):
        return date.today()
    return pd.to_datetime(ref_df.loc[0, "reference_date"]).date()


@st.cache_data(ttl=300, show_spinner=False)
def _load_base_receivables() -> pd.DataFrame:
    return _normalize_columns(run_query(queries.get_base_receivables_query()))


def _prepare_base_df(ref_date: date) -> pd.DataFrame:
    df = _load_base_receivables().copy()
    if df.empty:
        return df

    date_cols = ["data_antecipacao", "data_vencimento", "data_pagamento", "year_month", "year_month_expire"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    numeric_cols = ["valor_nota", "valor_parcela", "valor_antecipado", "valor_pago", "juros_multa", "valor_recompra", "prazo"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "is_resale" in df.columns:
        resale_mask = df["is_resale"].fillna(False).astype(bool)
    else:
        resale_mask = pd.Series(False, index=df.index)

    df["ocorrencia"] = df["ocorrencia"].where(df["ocorrencia"].notna(), np.where(resale_mask, "Recompra Total", None))
    df["valor_recompra"] = df["valor_recompra"].where(df["valor_recompra"].notna(), np.where(resale_mask, df["valor_parcela"], np.nan))

    ref_ts = pd.Timestamp(ref_date)
    df = df[df["data_antecipacao"] <= ref_ts]
    if df.empty:
        return df
    expired = df["data_vencimento"] < ref_ts
    paid = df["data_pagamento"].notna()

    conditions = [
        ~expired,
        expired & paid & (df["data_pagamento"] <= df["data_vencimento"]),
        expired & paid & (df["data_pagamento"] > df["data_vencimento"]),
        expired & ~paid,
    ]
    choices = [
        0,
        0,
        (df["data_pagamento"] - df["data_vencimento"]).dt.days,
        (ref_ts - df["data_vencimento"]).dt.days,
    ]
    df["days_late"] = np.select(conditions, choices, default=np.nan)
    df["days_late"] = pd.to_numeric(df["days_late"], errors="coerce").fillna(0).clip(lower=0).astype(int)

    df["bucket"] = pd.cut(df["days_late"], bins=DPD_EDGES, labels=AGING_LEVELS, include_lowest=True, right=True)
    df["bucket"] = pd.Categorical(df["bucket"], categories=AGING_LEVELS, ordered=True)
    df["strat"] = df["bucket"].cat.codes + 1
    strat_index = df["strat"].clip(lower=1, upper=len(PDD_BY_BUCKET)).fillna(1).astype(int) - 1
    df["pdd"] = strat_index.map(lambda idx: PDD_BY_BUCKET[idx])

    valid_rate = (df["prazo"] > 0) & (df["valor_antecipado"] > 0) & (df["valor_parcela"] > 0)
    df["taxa"] = np.nan
    df.loc[valid_rate, "taxa"] = 100 * ((df.loc[valid_rate, "valor_parcela"] / df.loc[valid_rate, "valor_antecipado"]) ** (30 / df.loc[valid_rate, "prazo"]) - 1)

    df["stage"] = np.select([df["days_late"] > 90, df["days_late"] > 30], ["Stage 3", "Stage 2"], default="Stage 1")
    df["on_book"] = ((df["data_pagamento"].isna()) | (df["data_pagamento"] > ref_ts)).astype(int)

    df["cohort"] = df["data_antecipacao"].dt.to_period("M").dt.to_timestamp()
    df["year_month"] = df["data_antecipacao"].dt.to_period("M").dt.to_timestamp()
    df["year_month_expire"] = df["data_vencimento"].dt.to_period("M").dt.to_timestamp()
    return df


def _compute_highlights(df: pd.DataFrame, ref_date: date) -> dict[str, float]:
    if df.empty:
        return {}
    ref_ts = pd.Timestamp(ref_date)
    hl = df.copy()
    hl["eligible15"] = ((ref_ts - hl["data_vencimento"]).dt.days >= 15).fillna(False)
    hl["eligible30"] = ((ref_ts - hl["data_vencimento"]).dt.days >= 30).fillna(False)
    hl["eligible90"] = ((ref_ts - hl["data_vencimento"]).dt.days >= 90).fillna(False)
    hl["is15"] = hl["days_late"] >= 15
    hl["is30"] = hl["days_late"] >= 30
    hl["is90"] = hl["days_late"] >= 90
    hl["unpaid"] = hl["data_pagamento"].isna()

    den30 = hl.loc[hl["eligible30"], "valor_parcela"].sum()
    num30 = hl.loc[hl["eligible30"] & hl["is30"], "valor_parcela"].sum()
    pd30 = _safe_div(num30, den30)

    den90 = hl.loc[hl["eligible90"], "valor_parcela"].sum()
    num90 = hl.loc[hl["eligible90"] & hl["is90"], "valor_parcela"].sum()
    pd90 = _safe_div(num90, den90)

    lgd30_den = hl.loc[hl["eligible30"] & hl["is30"], "valor_parcela"].sum()
    lgd30_num = hl.loc[hl["eligible30"] & hl["is30"] & hl["unpaid"], "valor_parcela"].sum()
    lgd30 = _safe_div(lgd30_num, lgd30_den)

    return {
        "total_face": float(hl["valor_parcela"].sum()),
        "pd30": pd30,
        "pd90": pd90,
        "lgd30": lgd30,
        "elr30": pd30 * lgd30 if not pd.isna(pd30) and not pd.isna(lgd30) else np.nan,
    }


def _perf_by_period(
    df: pd.DataFrame,
    ref_date: date,
    pd_days: int,
    period: str = "quarter",
    cohort_by: str = "expiration",
) -> pd.DataFrame:
    """Value-weighted PD/LGD/PE per cohort period.

    Cohorts are grouped either by due date (``expiration``) or by anticipation
    date (``acquisition``), but eligibility always depends on the due date being
    old enough for a title to be classifiable at the report snapshot. That is
    what makes the acquisition view interpretable: recent cohorts are only
    partially observed, and the maturity shares expose how much of each cohort
    already entered the PD denominator.
    """
    cohort_col = _COHORT_COL[cohort_by]
    ref_ts = pd.Timestamp(ref_date)
    data = df.copy()
    data["cohort_dt"] = pd.to_datetime(data[cohort_col], errors="coerce")
    data = data[data["cohort_dt"].notna()]
    if data.empty:
        return pd.DataFrame(columns=_PERF_COLUMNS)

    data["eligible"] = ((ref_ts - data["data_vencimento"]).dt.days > pd_days).astype(int)
    data["is_pd"] = (data["days_late"] > pd_days).astype(int)
    data["unpaid"] = data["data_pagamento"].isna().astype(int)
    data["period_key"] = data["cohort_dt"].dt.to_period("Q" if period == "quarter" else "M")

    ead = pd.to_numeric(data["valor_parcela"], errors="coerce").fillna(0.0)
    data["_ead"] = ead
    data["_eligible_ead"] = ead * data["eligible"]
    data["_defaulted_ead"] = data["_eligible_ead"] * data["is_pd"]
    data["_defaulted_unpaid_ead"] = data["_defaulted_ead"] * data["unpaid"]

    out = (
        data.groupby("period_key", as_index=False)
        .agg(
            cohort_ead=("_ead", "sum"),
            eligible_ead=("_eligible_ead", "sum"),
            cohort_titles=("_ead", "size"),
            eligible_titles=("eligible", "sum"),
            defaulted_ead=("_defaulted_ead", "sum"),
            defaulted_unpaid_ead=("_defaulted_unpaid_ead", "sum"),
        )
        .sort_values("period_key")
    )

    out["matured_ead_share"] = out.apply(lambda r: _safe_div(r["eligible_ead"], r["cohort_ead"]), axis=1)
    out["matured_titles_share"] = out.apply(lambda r: _safe_div(r["eligible_titles"], r["cohort_titles"]), axis=1)
    out["pd"] = out.apply(lambda r: _safe_div(r["defaulted_ead"], r["eligible_ead"]), axis=1)
    out["lgd"] = out.apply(lambda r: _safe_div(r["defaulted_unpaid_ead"], r["defaulted_ead"]), axis=1)
    out["pe"] = out["pd"] * out["lgd"]

    if cohort_by == "expiration":
        out = out[out["eligible_ead"] > 0]

    if period == "quarter":
        out["period"] = out["period_key"].astype(str)
    else:
        out["period"] = out["period_key"].dt.to_timestamp()

    return out[_PERF_COLUMNS].reset_index(drop=True)


def _perf_by_rolling_window(df: pd.DataFrame, ref_date: date, pd_days: int, window_days: int, pe_days: int = 90) -> pd.DataFrame:
    data = df.copy()
    ref_ts = pd.Timestamp(ref_date)
    data["due_dt"] = pd.to_datetime(data["data_vencimento"], errors="coerce")
    data["age_days"] = (ref_ts - data["due_dt"]).dt.days
    data["eligible_pd"] = (data["age_days"] > pd_days).astype(int)
    data["is_pd"] = (data["days_late"] > pd_days).astype(int)
    data["unpaid"] = data["data_pagamento"].isna().astype(int)
    data = data[(data["eligible_pd"] == 1) & data["due_dt"].notna()]
    if data.empty:
        return pd.DataFrame(columns=["period", "gmv", "ead_pd", "pd", "lgd", "pe"])

    daily = data.groupby("due_dt", as_index=False).apply(
        lambda x: pd.Series(
            {
                "gmv": x["valor_parcela"].sum(),
                "ead_pd": (x["valor_parcela"] * x["is_pd"]).sum(),
                "ead_pd_unp": (x["valor_parcela"] * x["is_pd"] * x["unpaid"]).sum(),
            }
        )
    ).reset_index(drop=True)

    all_days = pd.DataFrame({"due_dt": pd.date_range(daily["due_dt"].min(), daily["due_dt"].max(), freq="D")})
    daily = all_days.merge(daily, on="due_dt", how="left").fillna(0).sort_values("due_dt")

    daily["gmv_r"] = daily["gmv"].rolling(window=window_days, min_periods=window_days).sum()
    daily["ead_pd_r"] = daily["ead_pd"].rolling(window=window_days, min_periods=window_days).sum()
    daily["ead_pd_unp_r"] = daily["ead_pd_unp"].rolling(window=window_days, min_periods=window_days).sum()
    daily["pd"] = daily.apply(lambda r: _safe_div(r["ead_pd_r"], r["gmv_r"]), axis=1)
    daily["lgd_raw"] = daily.apply(lambda r: _safe_div(r["ead_pd_unp_r"], r["ead_pd_r"]), axis=1)
    daily["pe_eligible"] = ((ref_ts - daily["due_dt"]).dt.days > max(pe_days, pd_days)).astype(int)
    daily["lgd"] = np.where(daily["pe_eligible"] == 1, daily["lgd_raw"], np.nan)
    daily["pe"] = daily["pd"] * daily["lgd"]
    out = daily[["due_dt", "gmv_r", "ead_pd_r", "pd", "lgd", "pe"]].copy()
    out = out.rename(columns={"due_dt": "period", "gmv_r": "gmv", "ead_pd_r": "ead_pd"})
    return out.dropna(subset=["gmv"])


def _plot_metric_lines(df: pd.DataFrame, x_col: str, y_cols: list[str], title: str, y_title: str = "%") -> go.Figure:
    melted = df[[x_col] + y_cols].melt(id_vars=x_col, value_vars=y_cols, var_name="metric", value_name="value")
    fig = px.line(melted, x=x_col, y="value", color="metric", color_discrete_sequence=PLOTLY_COLORWAY, render_mode="svg")
    fig.update_traces(mode="lines+markers")
    fig.update_layout(**get_standard_layout(title=title, legend_title="Métrica", margin=dict(l=40, r=16, t=64, b=40)))
    fig.update_yaxes(title=y_title)
    return fig


def _plot_cohort_maturity(perf: pd.DataFrame, title: str) -> go.Figure:
    data = perf[["period", "matured_ead_share"]].copy()
    data["matured_ead_share"] = data["matured_ead_share"] * 100
    fig = px.line(data, x="period", y="matured_ead_share", color_discrete_sequence=[COLORS["secondary"]], render_mode="svg")
    fig.update_traces(mode="lines+markers")
    fig.update_layout(**get_standard_layout(title=title, show_legend=False, margin=dict(l=40, r=16, t=64, b=40)))
    fig.update_yaxes(title="% do EAD da safra elegível", range=[0, 100])
    return fig


def _render_quarterly_perf(
    df: pd.DataFrame,
    ref_date: date,
    pd_days: int,
    cohort_by: str,
    *,
    render_ui: bool = True,
    collect: bool = True,
) -> None:
    """Render the quarterly PD/LGD/PE block for one cohort definition.

    When *render_ui* is True, Streamlit widgets are created.
    When *collect* is True, collector calls are made (for the HTML export).
    """
    perf = _perf_by_period(df, ref_date, pd_days=pd_days, period="quarter", cohort_by=cohort_by)
    if perf.empty:
        if render_ui:
            st.info("Sem dados elegíveis para PD/LGD/PE trimestral.")
        return

    cohort_title = _COHORT_TITLE[cohort_by]
    perf_pct = perf.copy()
    for col in ("pd", "lgd", "pe"):
        perf_pct[col] = perf_pct[col] * 100
    perf_pct = perf_pct.rename(columns={"pd": "PD", "lgd": "LGD", "pe": "PE"})
    fig = _plot_metric_lines(
        perf_pct,
        "period",
        ["PD", "LGD", "PE"],
        f"PD, LGD e PE {pd_days}+ por trimestre - {cohort_title}",
    )

    fig_maturity = (
        _plot_cohort_maturity(perf, f"Fração maturada da safra - {cohort_title}")
        if cohort_by == "acquisition"
        else None
    )

    tbl = perf.rename(columns=_PERF_TABLE_LABELS)
    tbl_grid = _format_grid_ptbr(
        tbl.set_index("Período"),
        currency_cols=["EAD da safra", "EAD elegível", "EAD inadimplente"],
        integer_cols=["Nº títulos", "Nº títulos elegíveis"],
        percent_cols=["% maturado (EAD)", "% maturado (títulos)", "PD", "LGD", "PE"],
    )

    if render_ui:
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        if fig_maturity is not None:
            st.plotly_chart(fig_maturity, use_container_width=True, config=PLOTLY_CONFIG)
        render_data_grid(
            tbl_grid,
            key=f"performance-quarterly-grid-{cohort_by}",
            table_preset="standard",
            index_label="Período",
            pagination=False,
            width="100%",
            fit_columns_on_grid_load=False,
            column_config={
                "EAD da safra": GridColumnConfig(min_width=150, sortable=False),
                "EAD elegível": GridColumnConfig(min_width=150, sortable=False),
                "% maturado (EAD)": GridColumnConfig(min_width=150, sortable=False),
                "Nº títulos": GridColumnConfig(min_width=110, sortable=False),
                "Nº títulos elegíveis": GridColumnConfig(min_width=160, sortable=False),
                "% maturado (títulos)": GridColumnConfig(min_width=170, sortable=False),
                "EAD inadimplente": GridColumnConfig(min_width=160, sortable=False),
                "PD": GridColumnConfig(min_width=100, sortable=False),
                "LGD": GridColumnConfig(min_width=100, sortable=False),
                "PE": GridColumnConfig(min_width=100, sortable=False),
            },
        )

    if collect:
        collect_chart(fig)
        if fig_maturity is not None:
            collect_chart(fig_maturity)
        collect_dataframe(tbl_grid)


def render_visao_geral() -> None:
    ref_date = st.session_state.reference_date
    df = _prepare_base_df(ref_date)
    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    st.subheader("Destaques")
    collect_subheader("Destaques")
    st.caption("Principais indicadores de risco e exposição da carteira na data de referência.")
    collect_caption("Principais indicadores de risco e exposição da carteira na data de referência.")
    hl = _compute_highlights(df, ref_date)
    c1, c2, c3, c4 = st.columns(4)
    _m = [
        ("Face Total", _fmt_currency(hl.get("total_face", 0))),
        ("PD30", _fmt_percent(hl.get("pd30"))),
        ("PD90", _fmt_percent(hl.get("pd90"))),
        ("ELR30", _fmt_percent(hl.get("elr30"))),
    ]
    c1.metric(_m[0][0], _m[0][1])
    c2.metric(_m[1][0], _m[1][1])
    c3.metric(_m[2][0], _m[2][1])
    c4.metric(_m[3][0], _m[3][1])
    collect_columns_start(4)
    for lbl, val in _m:
        collect_metric(lbl, val)
    collect_columns_end()

    st.divider()
    collect_divider()
    st.subheader("Originação")
    collect_subheader("Originação")
    st.caption("Volume originado por mês e evolução acumulada da carteira.")
    collect_caption("Volume originado por mês e evolução acumulada da carteira.")
    monthly = (
        df.groupby("year_month", as_index=False)["valor_parcela"]
        .sum()
        .sort_values("year_month")
        .rename(columns={"valor_parcela": "loan_amount"})
    )
    monthly["cum_amount"] = monthly["loan_amount"].cumsum()
    fig = go.Figure()
    fig.add_bar(x=monthly["year_month"], y=monthly["loan_amount"], name="Valor originado no mês (EAD)", marker_color=COLORS["primary"])
    fig.add_scatter(x=monthly["year_month"], y=monthly["cum_amount"], name="Valor acumulado originado", mode="lines+markers", yaxis="y2", line=dict(color=COLORS["secondary"]))
    layout = get_standard_layout(title="Valor originado mensal e acumulado", margin=dict(l=40, r=16, t=64, b=40))
    layout["yaxis"] = dict(title="R$ por mês", showgrid=True, gridcolor=COLORS["table_border"])
    layout["yaxis2"] = dict(title="R$ acumulado", overlaying="y", side="right", showgrid=False)
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    collect_chart(fig)

    st.subheader("Preço e prazo ao longo do tempo")
    collect_subheader("Preço e prazo ao longo do tempo")
    st.caption("Evolução mensal de taxa média ponderada e prazo médio da originação.")
    collect_caption("Evolução mensal de taxa média ponderada e prazo médio da originação.")
    pricing = (
        df.groupby("year_month", as_index=False)
        .apply(
            lambda x: pd.Series(
                {
                    "taxa_media": _weighted_average(x["taxa"], x["valor_parcela"]),
                    "prazo_medio": _weighted_average(x["prazo"], x["valor_parcela"]),
                    "ticket_medio": x["valor_parcela"].mean(),
                }
            )
        )
        .reset_index(drop=True)
    )
    c1, c2 = st.columns(2)
    with c1:
        fig_rate = px.line(pricing, x="year_month", y="taxa_media", color_discrete_sequence=[COLORS["secondary"]], render_mode="svg")
        fig_rate.update_traces(mode="lines+markers")
        fig_rate.update_layout(**get_standard_layout(title="Taxa média ponderada (% a.m.)", margin=dict(l=40, r=16, t=64, b=40)))
        st.plotly_chart(fig_rate, use_container_width=True, config=PLOTLY_CONFIG)
    with c2:
        fig_tenor = px.line(pricing, x="year_month", y="prazo_medio", color_discrete_sequence=[COLORS["accent"]], render_mode="svg")
        fig_tenor.update_traces(mode="lines+markers")
        fig_tenor.update_layout(**get_standard_layout(title="Prazo médio ponderado (dias)", margin=dict(l=40, r=16, t=64, b=40)))
        st.plotly_chart(fig_tenor, use_container_width=True, config=PLOTLY_CONFIG)
    collect_columns_start(2)
    collect_chart(fig_rate)
    collect_chart(fig_tenor)
    collect_columns_end()

    st.subheader(f"KPIs da Carteira (em {pd.Timestamp(ref_date).strftime('%d/%m/%Y')})")
    collect_subheader(f"KPIs da Carteira (em {pd.Timestamp(ref_date).strftime('%d/%m/%Y')})")
    st.caption("Resumo de exposição, custo, risco esperado e concentração da carteira em aberto.")
    collect_caption("Resumo de exposição, custo, risco esperado e concentração da carteira em aberto.")
    snap = df[df["on_book"] == 1].copy()
    seller_sh = snap.groupby("seller", as_index=False)["valor_parcela"].sum().rename(columns={"valor_parcela": "v"})
    seller_sh["share"] = seller_sh["v"] / seller_sh["v"].sum() if not seller_sh.empty else 0
    kpi = pd.DataFrame(
        {
            "Indicador": [
                "Face em carteira (EAD)",
                "Custo de aquisição",
                "ECL (proxy de PDD)",
                "Prazo médio ponderado (dias)",
                "Taxa média ponderada (% a.m.)",
                "Participação dos 5 maiores cedentes",
                "HHI (cedentes)",
            ],
            "Valor": [
                snap["valor_parcela"].sum(),
                snap["valor_antecipado"].sum(),
                (snap["valor_parcela"] * snap["pdd"] / 100).sum(),
                _weighted_average(snap["prazo"], snap["valor_parcela"]),
                _weighted_average(snap["taxa"], snap["valor_parcela"]),
                seller_sh.nlargest(5, "share")["share"].sum() * 100,
                _hhi(seller_sh["share"]),
            ],
        }
    )
    kpi.loc[[0, 1, 2], "Valor"] = kpi.loc[[0, 1, 2], "Valor"].map(_fmt_currency)
    kpi.loc[[3, 6], "Valor"] = kpi.loc[[3, 6], "Valor"].map(lambda v: _fmt_number(v, 2))
    kpi.loc[[4], "Valor"] = kpi.loc[[4], "Valor"].map(lambda v: f"{_fmt_number(v, 2)}%")
    kpi.loc[[5], "Valor"] = kpi.loc[[5], "Valor"].map(lambda v: f"{_fmt_number(v, 1)}%")
    render_data_grid(
        kpi,
        key="portfolio-kpis-grid",
        table_preset="compact",
        column_config={
            "Indicador": GridColumnConfig(min_width=260, wrap_text=True, auto_height=True),
            "Valor": GridColumnConfig(min_width=180),
        },
    )
    collect_dataframe(kpi)


def render_carteira() -> None:
    ref_date = st.session_state.reference_date
    df = _prepare_base_df(ref_date)
    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    st.subheader("Concentração por Cedente")
    collect_subheader("Concentração por Cedente")
    st.caption("Distribuição da carteira em aberto por cedente para avaliar concentração.")
    collect_caption("Distribuição da carteira em aberto por cedente para avaliar concentração.")
    conc = df[df["on_book"] == 1].groupby("seller", as_index=False)["valor_parcela"].sum().rename(columns={"valor_parcela": "total"})
    if conc.empty:
        st.info("Sem carteira em aberto para a data de referência.")
    else:
        conc_plot = conc.sort_values("total", ascending=True)
        total_conc = conc_plot["total"].sum()
        conc_plot["share"] = np.where(total_conc > 0, conc_plot["total"] / total_conc, np.nan)
        conc_plot["share_label"] = conc_plot["share"].map(lambda v: f"<b>{_fmt_percent(v, 1)}</b>")
        fig = px.bar(
            conc_plot,
            x="total",
            y="seller",
            orientation="h",
            text="share_label",
            color_discrete_sequence=[COLORS["secondary"]],
        )
        fig.update_traces(textposition="outside", textfont=dict(size=14), cliponaxis=False)
        plot_height = min(612, max(288, 21 * len(conc_plot)))
        fig.update_layout(
            **get_standard_layout(
                title="Concentração em carteira por cedente",
                show_legend=False,
                margin=dict(l=120, r=16, t=64, b=40),
                height=plot_height,
            )
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        collect_chart(fig)

    st.divider()
    collect_divider()
    st.subheader("Métricas por Cedente")
    collect_subheader("Métricas por Cedente")
    st.caption("Indicadores operacionais e de risco por cedente para comparação de desempenho.")
    collect_caption("Indicadores operacionais e de risco por cedente para comparação de desempenho.")
    seller_metrics = (
        df.groupby("seller", as_index=False)
        .apply(
            lambda x: pd.Series(
                {
                    "gmv_total": x["valor_parcela"].sum(),
                    "on_book_face": x.loc[x["on_book"] == 1, "valor_parcela"].sum(),
                    "n_operacoes": x["chave_nfe"].nunique(),
                    "n_pme": x["sacado_nome"].nunique(),
                    "parcela_media": x["valor_parcela"].mean(),
                    "prazo_medio_wt": _weighted_average(x["prazo"], x["valor_parcela"]),
                    "taxa_media_wt": _weighted_average(x["taxa"], x["valor_parcela"]),
                    "stage2_share": _safe_div(x.loc[x["stage"] == "Stage 2", "valor_parcela"].sum(), x.loc[x["days_late"] > 30, "valor_parcela"].sum()),
                    "stage3_share": _safe_div(x.loc[x["stage"] == "Stage 3", "valor_parcela"].sum(), x.loc[x["days_late"] > 90, "valor_parcela"].sum()),
                }
            )
        )
        .reset_index(drop=True)
        .sort_values("gmv_total", ascending=False)
    )
    seller_metrics = seller_metrics.rename(
        columns={
            "seller": "Cedente",
            "gmv_total": "GMV Total",
            "on_book_face": "Face em carteira",
            "n_operacoes": "Nº Operações",
            "n_pme": "Nº PMEs",
            "parcela_media": "Parcela Média",
            "prazo_medio_wt": "Prazo Médio (dias)",
            "taxa_media_wt": "Taxa Média (% a.m.)",
            "stage2_share": "Participação Estágio 2",
            "stage3_share": "Participação Estágio 3",
        }
    )
    seller_metrics_fmt = _format_grid_ptbr(
        seller_metrics.set_index("Cedente"),
        currency_cols=["GMV Total", "Face em carteira", "Parcela Média"],
        integer_cols=["Nº Operações", "Nº PMEs"],
        number_cols=["Prazo Médio (dias)"],
        percent_cols=["Taxa Média (% a.m.)", "Participação Estágio 2", "Participação Estágio 3"],
    )
    render_data_grid(
        seller_metrics_fmt,
        key="seller-metrics-grid",
        table_preset="standard",
        index_label="Cedente",
        page_size=10,
        enable_quick_filter=True,
        quick_filter_placeholder="Filtrar cedente...",
        column_config={
            "GMV Total": GridColumnConfig(min_width=140, sortable=False),
            "Face em carteira": GridColumnConfig(min_width=150, sortable=False),
            "Nº Operações": GridColumnConfig(min_width=120, sortable=False),
            "Nº PMEs": GridColumnConfig(min_width=100, sortable=False),
            "Parcela Média": GridColumnConfig(min_width=130, sortable=False),
            "Prazo Médio (dias)": GridColumnConfig(min_width=130, sortable=False),
            "Taxa Média (% a.m.)": GridColumnConfig(min_width=140, sortable=False),
            "Participação Estágio 2": GridColumnConfig(min_width=140, sortable=False),
            "Participação Estágio 3": GridColumnConfig(min_width=140, sortable=False),
        },
    )
    collect_dataframe(seller_metrics_fmt)

    st.subheader("Atraso e IFRS 9")
    collect_subheader("Atraso e IFRS 9")
    st.caption("Distribuição da carteira em aberto por faixa de atraso.")
    collect_caption("Distribuição da carteira em aberto por faixa de atraso.")
    aging = df[df["on_book"] == 1].groupby("bucket", as_index=False)["valor_parcela"].sum().rename(columns={"valor_parcela": "valor"})
    all_buckets = pd.DataFrame({"bucket": AGING_LEVELS})
    aging["bucket"] = aging["bucket"].astype(str)
    aging = all_buckets.merge(aging, on="bucket", how="left").fillna(0)
    aging["perc"] = aging["valor"] / aging["valor"].sum() if aging["valor"].sum() > 0 else 0
    aging["valor_fmt"] = aging["valor"].map(_fmt_currency)
    aging["perc_fmt"] = aging["perc"].map(lambda x: _fmt_percent(x, 1))
    aging_fmt = aging.rename(columns={"bucket": "Faixa", "valor": "Valor", "perc": "Participação"})
    aging_grid = _format_grid_ptbr(
        aging_fmt.set_index("Faixa")[["Valor", "Participação"]],
        currency_cols=["Valor"],
        percent_cols=["Participação"],
    )
    render_data_grid(
        aging_grid,
        key="aging-grid",
        table_preset="compact",
        index_label="Faixa",
        column_config={
            "Valor": GridColumnConfig(min_width=160, sortable=False),
            "Participação": GridColumnConfig(min_width=130, sortable=False),
        },
    )
    collect_dataframe(aging_grid)

    st.subheader("KPIs - PMEs e Estoque")
    collect_subheader("KPIs - PMEs e Estoque")
    st.caption("Evolução de base de PMEs e dinâmica mensal de estoque e deságio da carteira.")
    collect_caption("Evolução de base de PMEs e dinâmica mensal de estoque e deságio da carteira.")
    df_loan = df[df["data_antecipacao"] < pd.Timestamp(ref_date).replace(day=1)].copy()
    if df_loan.empty:
        st.info("Sem histórico suficiente para KPIs de estoque.")
        return

    months = sorted(df_loan["year_month"].dropna().unique())
    buyers_seen: set[str] = set()
    rows: list[dict] = []
    for m in months:
        month_df = df_loan[df_loan["year_month"] == m]
        month_buyers = set(month_df["sacado_cnpj"].dropna().astype(str).tolist())
        new_buyers = month_buyers - buyers_seen
        recurring = month_buyers & buyers_seen
        buyers_seen |= month_buyers
        rows.append(
            {
                "year_month": m,
                "month_companies": len(month_buyers),
                "recurrent_companies": len(recurring),
                "new_companies": len(new_buyers),
                "accum_companies": len(buyers_seen),
            }
        )
    companies = pd.DataFrame(rows)

    inv_rows = []
    for m in months:
        month_start = pd.Timestamp(m)
        month_end = month_start + pd.offsets.MonthEnd(0)
        ref_max = min(month_end, pd.Timestamp(ref_date))
        pool = df_loan[df_loan["data_antecipacao"] <= month_end].copy()
        acquisitions_within = pool[(pool["data_antecipacao"] >= month_start) & (pool["data_antecipacao"] <= month_end)]["valor_antecipado"].sum()
        paid_within = pool[(pool["data_pagamento"] >= month_start) & (pool["data_pagamento"] <= month_end)]["valor_parcela"].sum()
        on_book = pool[(pool["data_pagamento"].isna()) | (pool["data_pagamento"] > month_end)].copy()
        on_book["time_to_expire"] = (ref_max - on_book["data_antecipacao"]).dt.days
        on_book["valor_presente"] = on_book["valor_antecipado"] + (on_book["valor_parcela"] - on_book["valor_antecipado"]) * (on_book["prazo"] - on_book["time_to_expire"]) / on_book["prazo"]
        on_book["valor_pdd"] = on_book["valor_presente"] * on_book["pdd"] / 100
        inv_rows.append(
            {
                "year_month": m,
                "valor_presente": on_book["valor_presente"].sum(),
                "valor_face": on_book["valor_parcela"].sum(),
                "valor_aquisicao": on_book["valor_antecipado"].sum(),
                "valor_pdd": on_book["valor_pdd"].sum(),
                "acquisitions_within": acquisitions_within,
                "paid_within": paid_within,
            }
        )

    inventory = pd.DataFrame(inv_rows).sort_values("year_month")
    df_plot = inventory.merge(companies, on="year_month", how="left").sort_values("year_month")
    df_plot["desagio"] = (
        df_plot["valor_presente"] - df_plot["valor_presente"].shift(1).fillna(0) - df_plot["acquisitions_within"] + df_plot["paid_within"]
    )

    c1, c2 = st.columns(2)
    with c1:
        fig_sme = px.line(df_plot, x="year_month", y="accum_companies", color_discrete_sequence=[COLORS["secondary"]], render_mode="svg")
        fig_sme.update_traces(mode="lines+markers")
        fig_sme.update_layout(**get_standard_layout(title="PMEs acumuladas ao longo do tempo", margin=dict(l=40, r=16, t=64, b=40)))
        st.plotly_chart(fig_sme, use_container_width=True, config=PLOTLY_CONFIG)
    with c2:
        fig_des = px.line(df_plot, x="year_month", y="desagio", color_discrete_sequence=[COLORS["accent"]], render_mode="svg")
        fig_des.update_traces(mode="lines+markers")
        fig_des.update_layout(**get_standard_layout(title="Receita de deságio (mensal)", margin=dict(l=40, r=16, t=64, b=40)))
        st.plotly_chart(fig_des, use_container_width=True, config=PLOTLY_CONFIG)
    collect_columns_start(2)
    collect_chart(fig_sme)
    collect_chart(fig_des)
    collect_columns_end()


def render_safras() -> None:
    ref_date = st.session_state.reference_date
    ref_ts = pd.Timestamp(ref_date)
    df = _prepare_base_df(ref_date)
    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    st.subheader("Mapa de Calor")
    collect_subheader("Mapa de Calor")
    st.caption("Mapa de calor da recuperação acumulada sobre custo para coortes vencidas.")
    collect_caption("Mapa de calor da recuperação acumulada sobre custo para coortes vencidas.")
    cutoff_date = pd.Timestamp(ref_date).to_period("M").to_timestamp("M")
    cohort_exclude_month = pd.Timestamp(ref_date).to_period("M").to_timestamp()
    heat_df = df.copy()
    heat_df["cohort"] = heat_df["data_antecipacao"].dt.to_period("M").dt.to_timestamp()
    age_to_cut_raw = (cutoff_date - heat_df["data_antecipacao"]).dt.days / 30.4375
    heat_df["age_to_cut"] = np.floor(age_to_cut_raw.fillna(0)).clip(lower=0).astype(int)
    df_exp = heat_df[(heat_df["cohort"] < cohort_exclude_month) & (heat_df["data_vencimento"] <= cutoff_date)].copy()
    if df_exp.empty:
        st.info("Sem dados suficientes para o mapa de calor.")
        return

    df_exp["cash_in"] = df_exp["valor_pago"].where(df_exp["valor_pago"].notna(), np.where(df_exp["data_pagamento"].notna() & (df_exp["data_pagamento"] <= cutoff_date), df_exp["valor_parcela"], 0))
    age_m_pay_raw = (df_exp["data_pagamento"] - df_exp["data_antecipacao"]).dt.days / 30.4375
    age_m_pay = np.floor(age_m_pay_raw.replace([np.inf, -np.inf], np.nan).fillna(0)).clip(lower=0).astype(int)
    df_exp["age_m_pay"] = np.where(
        df_exp["data_pagamento"].notna() & (df_exp["data_pagamento"] <= cutoff_date),
        age_m_pay,
        np.nan,
    )
    pay_by_age = df_exp.dropna(subset=["age_m_pay"]).groupby(["cohort", "age_m_pay"], as_index=False)["cash_in"].sum().rename(columns={"age_m_pay": "age_m", "cash_in": "cash"})

    cohort_totals = (
        heat_df[heat_df["cohort"] < cohort_exclude_month].groupby("cohort", as_index=False).agg(total_cost=("valor_antecipado", "sum"), max_age_obs=("age_to_cut", "max"))
    )
    cohort_expired = df_exp.groupby("cohort", as_index=False).agg(exp_cost=("valor_antecipado", "sum"))
    coh = cohort_totals.merge(cohort_expired, on="cohort", how="left").fillna({"exp_cost": 0})
    coh["expired_share"] = np.where(coh["total_cost"] > 0, coh["exp_cost"] / coh["total_cost"], np.nan)

    grid = []
    for _, row in coh.iterrows():
        max_age_obs = int(pd.to_numeric(row["max_age_obs"], errors="coerce")) if pd.notna(row["max_age_obs"]) else 0
        for age_m in range(max(0, max_age_obs) + 1):
            grid.append({"cohort": row["cohort"], "age_m": age_m, "exp_cost": row["exp_cost"], "expired_share": row["expired_share"]})
    grid_df = pd.DataFrame(grid)
    collages = grid_df.merge(pay_by_age, on=["cohort", "age_m"], how="left").fillna({"cash": 0}).sort_values(["cohort", "age_m"])
    collages["cum_cash_exp"] = collages.groupby("cohort")["cash"].cumsum()
    collages["cum_coll_cost_exp"] = np.where(collages["exp_cost"] > 0, collages["cum_cash_exp"] / collages["exp_cost"], np.nan)
    collages["cohort_lbl"] = pd.to_datetime(collages["cohort"]).dt.strftime("%Y-%m")

    expired_col = coh.assign(age_m=-1, zval=coh["expired_share"], cohort_lbl=pd.to_datetime(coh["cohort"]).dt.strftime("%Y-%m"))[["cohort", "cohort_lbl", "age_m", "zval"]]
    heat_body = collages.assign(zval=collages["cum_coll_cost_exp"])[["cohort", "cohort_lbl", "age_m", "zval"]]
    heat_all = pd.concat([expired_col, heat_body], ignore_index=True)
    heat_pivot = heat_all.pivot(index="cohort_lbl", columns="age_m", values="zval").sort_index()
    fig_h = go.Figure(
        data=go.Heatmap(
            z=heat_pivot.values * 100,
            x=[("Vencido%" if c == -1 else str(int(c))) for c in heat_pivot.columns],
            y=heat_pivot.index.tolist(),
            colorscale="Viridis",
            colorbar=dict(title="%"),
            hoverongaps=False,
            hovertemplate=(
                "Coorte: %{y}<br>"
                "Faixa: %{x}<br>"
                "Recuperação/Custo: %{z:.1f}%<extra></extra>"
            ),
        )
    )
    fig_h.update_layout(**get_standard_layout(title="Recuperação acumulada / Custo (%) para títulos vencidos", margin=dict(l=40, r=16, t=64, b=40)))
    fig_h.update_layout(hovermode="closest")
    st.plotly_chart(fig_h, use_container_width=True, config=PLOTLY_CONFIG)
    collect_chart(fig_h)


def render_performance() -> None:
    ref_date = st.session_state.reference_date
    df = _prepare_base_df(ref_date)
    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    pd_selector = chiclet_selector(PD_HORIZON_OPTIONS, key="pd_horizon_selector", default="30 dias", variant="buttons", group_max_fraction=0.5)
    pd_days = _PD_DAYS_MAP.get(pd_selector, 30)

    st.subheader("PD, LGD e PE por trimestre")
    collect_subheader("PD, LGD e PE por trimestre")
    _cohort_caption = (
        "PD, LGD e PE trimestrais ponderados por valor para o horizonte selecionado. "
        "A visão por vencimento agrupa os títulos pela data de vencimento; a visão por aquisição "
        "agrupa pela data de antecipação, e apenas títulos com maturidade suficiente entram no "
        "denominador de PD e PE."
    )
    st.caption(_cohort_caption)
    collect_caption(_cohort_caption)

    cohort_selector = chiclet_selector(
        COHORT_BASIS_OPTIONS,
        key="cohort_basis_selector",
        default="Por vencimento",
        variant="buttons",
        group_max_fraction=0.5,
    )
    _render_quarterly_perf(
        df,
        ref_date,
        pd_days,
        _COHORT_BY_LABEL.get(cohort_selector, "expiration"),
        render_ui=True,
        collect=False,
    )

    collect_selector_start(COHORT_BASIS_OPTIONS, label="Base da safra")
    for label in COHORT_BASIS_OPTIONS:
        collect_selector_option(label)
        _render_quarterly_perf(df, ref_date, pd_days, _COHORT_BY_LABEL[label], render_ui=False, collect=True)
    collect_selector_end()

    st.divider()
    collect_divider()
    st.subheader("Média móvel de PD/PE")
    collect_subheader("Média móvel de PD/PE")
    st.caption("Séries móveis de PD e PE para suavizar volatilidade e acompanhar tendência.")
    collect_caption("Séries móveis de PD e PE para suavizar volatilidade e acompanhar tendência.")
    window_selector = chiclet_selector(
        ROLLING_WINDOW_OPTIONS,
        key="rolling_window_selector",
        default="60 dias",
        variant="buttons",
        group_max_fraction=0.5,
    )
    window_days = _WINDOW_DAYS_MAP.get(window_selector, 60)
    perf_roll = _perf_by_rolling_window(df, ref_date, pd_days=pd_days, window_days=window_days, pe_days=90)
    if perf_roll.empty:
        st.info("Sem dados para janela móvel selecionada.")
        return

    perf_roll_pct = perf_roll.dropna(subset=["period"]).copy()
    perf_roll_pct[["pd", "pe"]] = perf_roll_pct[["pd", "pe"]] * 100
    perf_roll_pct = perf_roll_pct.rename(columns={"pd": "PD", "pe": "PE"})
    fig_r = _plot_metric_lines(
        perf_roll_pct,
        "period",
        ["PD", "PE"],
        f"Janela móvel {window_days} dias - PD {pd_days}+ e PE",
    )
    st.plotly_chart(fig_r, use_container_width=True, config=PLOTLY_CONFIG)
    collect_chart(fig_r)
    tbl_r = perf_roll.copy()
    tbl_r_fmt = tbl_r.tail(24).rename(columns={"period": "Período", "gmv": "GMV", "ead_pd": "EAD PD", "pd": "PD", "lgd": "LGD", "pe": "PE"})
    tbl_r_grid = _format_grid_ptbr(
        tbl_r_fmt.set_index("Período"),
        currency_cols=["GMV", "EAD PD"],
        percent_cols=["PD", "LGD", "PE"],
    )
    render_data_grid(
        tbl_r_grid,
        key="performance-rolling-grid",
        table_preset="standard",
        index_label="Período",
        page_size=12,
        column_config={
            "GMV": GridColumnConfig(min_width=140, sortable=False),
            "EAD PD": GridColumnConfig(min_width=140, sortable=False),
            "PD": GridColumnConfig(min_width=110, sortable=False),
            "LGD": GridColumnConfig(min_width=110, sortable=False),
            "PE": GridColumnConfig(min_width=110, sortable=False),
        },
    )
    collect_dataframe(tbl_r_grid)



def _render_seller_drilldown(
    df: pd.DataFrame,
    seller_name: str,
    ref_date: date,
    *,
    render_ui: bool = True,
    collect: bool = True,
) -> None:
    """Build the 4-chart drilldown for a single seller.

    When *render_ui* is True, Streamlit widgets are created.
    When *collect* is True, collector calls are made (for the HTML export).
    """
    seller_df = df[df["seller"] == seller_name].copy()
    if seller_df.empty:
        if render_ui:
            st.info("Sem dados para o cedente selecionado.")
        return

    orig = seller_df.groupby("year_month", as_index=False).apply(
        lambda x: pd.Series({"origination": x["valor_parcela"].sum(), "taxa_media": _weighted_average(x["taxa"], x["valor_parcela"])})
    ).reset_index(drop=True)

    risk = seller_df.copy()
    due_age_days = (pd.Timestamp(ref_date) - risk["data_vencimento"]).dt.days
    risk["eligible30"] = (due_age_days > 30).astype(int)
    risk["is30"] = (risk["days_late"] > 30).astype(int)
    risk["unpaid"] = risk["data_pagamento"].isna().astype(int)
    risk["eligible_lgd"] = (due_age_days >= 90).astype(int)
    risk = risk[(risk["eligible30"] == 1) | ((risk["is30"] == 1) & (risk["eligible_lgd"] == 1))]
    if risk.empty:
        risk_month = pd.DataFrame(columns=["year_month_expire", "pd30", "lgd", "pe_proxy"])
    else:
        risk_month = risk.groupby("year_month_expire", as_index=False).apply(
            lambda x: pd.Series(
                {
                    "base_30": x.loc[x["eligible30"] == 1, "valor_parcela"].sum(),
                    "ead_30": (x.loc[x["eligible30"] == 1, "valor_parcela"] * x.loc[x["eligible30"] == 1, "is30"]).sum(),
                    "ead_30_unpaid_proxy": (
                        x.loc[x["eligible30"] == 1, "valor_parcela"]
                        * x.loc[x["eligible30"] == 1, "is30"]
                        * x.loc[x["eligible30"] == 1, "unpaid"]
                    ).sum(),
                    "lgd_base": x.loc[(x["is30"] == 1) & (x["eligible_lgd"] == 1), "valor_parcela"].sum(),
                    "ead_30_unpaid": (x.loc[(x["is30"] == 1) & (x["eligible_lgd"] == 1), "valor_parcela"] * x.loc[(x["is30"] == 1) & (x["eligible_lgd"] == 1), "unpaid"]).sum(),
                }
            )
        ).reset_index(drop=True)
        risk_month["pd30"] = risk_month.apply(lambda r: _safe_div(r["ead_30"], r["base_30"]), axis=1)
        risk_month["lgd"] = risk_month.apply(lambda r: _safe_div(r["ead_30_unpaid"], r["lgd_base"]), axis=1)
        risk_month["pe_proxy"] = risk_month.apply(lambda r: _safe_div(r["ead_30_unpaid_proxy"], r["base_30"]), axis=1)

    seller_book = seller_df[seller_df["on_book"] == 1].copy()
    book_status = pd.DataFrame(
        {
            "bucket": ["Vencidos em carteira", "Em carteira a vencer"],
            "amount": [
                seller_book[seller_book["data_vencimento"] < pd.Timestamp(ref_date)]["valor_parcela"].sum(),
                seller_book[seller_book["data_vencimento"] >= pd.Timestamp(ref_date)]["valor_parcela"].sum(),
            ],
        }
    )

    fig_book = px.bar(book_status, x="bucket", y="amount", color="bucket", color_discrete_sequence=[COLORS["danger"], COLORS["secondary"]])
    fig_book.update_layout(**get_standard_layout(title=f"Abertura da exposição em carteira - {seller_name}", show_legend=False, margin=dict(l=40, r=16, t=64, b=40)))

    fig_orig = px.bar(orig, x="year_month", y="origination", color_discrete_sequence=[COLORS["primary"]])
    fig_orig.update_layout(**get_standard_layout(title=f"Originação por mês de originação - {seller_name}", show_legend=False, margin=dict(l=40, r=16, t=64, b=40)))

    fig_rate = px.line(orig, x="year_month", y="taxa_media", color_discrete_sequence=[COLORS["accent"]], render_mode="svg")
    fig_rate.update_traces(mode="lines+markers")
    fig_rate.update_layout(**get_standard_layout(title=f"Taxa média ponderada - {seller_name}", show_legend=False, margin=dict(l=40, r=16, t=64, b=40)))

    risk_long = risk_month.melt(id_vars="year_month_expire", value_vars=["pd30", "lgd", "pe_proxy"], var_name="metric", value_name="value")
    fig_risk = px.line(risk_long, x="year_month_expire", y="value", color="metric", color_discrete_sequence=PLOTLY_COLORWAY, render_mode="svg")
    fig_risk.update_traces(mode="lines+markers")
    fig_risk.update_layout(**get_standard_layout(title=f"PD30, LGD e PE por mês de vencimento - {seller_name}", margin=dict(l=40, r=16, t=64, b=40)))

    if render_ui:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fig_book, use_container_width=True, config=PLOTLY_CONFIG)
        with c2:
            st.plotly_chart(fig_orig, use_container_width=True, config=PLOTLY_CONFIG)
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(fig_rate, use_container_width=True, config=PLOTLY_CONFIG)
        with c4:
            st.plotly_chart(fig_risk, use_container_width=True, config=PLOTLY_CONFIG)

    if collect:
        collect_columns_start(2)
        collect_chart(fig_book)
        collect_chart(fig_orig)
        collect_columns_end()
        collect_columns_start(2)
        collect_chart(fig_rate)
        collect_chart(fig_risk)
        collect_columns_end()


def render_inadimplencia() -> None:
    ref_date = st.session_state.reference_date
    df = _prepare_base_df(ref_date)
    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    st.subheader("Inadimplência por cedente")
    collect_subheader("Inadimplência por cedente")
    st.caption("Montante em atraso (30+ dias) por cedente na carteira em aberto.")
    collect_caption("Montante em atraso (30+ dias) por cedente na carteira em aberto.")
    inad_titles = df[(df["on_book"] == 1) & (df["days_late"] >= 30)].copy()
    by_seller = inad_titles.groupby("seller", as_index=False)["valor_parcela"].sum().rename(columns={"valor_parcela": "valor"}).sort_values("valor", ascending=False)
    by_seller_fmt = by_seller.rename(columns={"seller": "Slug", "valor": "Valor em atraso"})
    by_seller_grid = _format_grid_ptbr(
        by_seller_fmt.set_index("Slug"),
        currency_cols=["Valor em atraso"],
    )
    render_data_grid(
        by_seller_grid,
        key="inad-seller-grid",
        table_preset="standard",
        index_label="Slug",
        page_size=12,
        column_config={
            "Valor em atraso": GridColumnConfig(min_width=160, sortable=False),
        },
    )
    collect_dataframe(by_seller_grid)

    st.subheader("Inadimplência por Faixa de Atraso")
    collect_subheader("Inadimplência por Faixa de Atraso")
    st.caption("Valor em carteira (on-book) por cedente e faixa de atraso.")
    collect_caption("Valor em carteira (on-book) por cedente e faixa de atraso.")
    _DPD_BUCKET_LABELS = ["3-30", "31-90", "91-180", "180+"]
    inad_dpd = df[(df["on_book"] == 1) & (df["days_late"] >= 3)].copy()
    inad_dpd["dpd_bucket"] = pd.cut(
        inad_dpd["days_late"],
        bins=[2, 30, 90, 180, float("inf")],
        labels=_DPD_BUCKET_LABELS,
    )
    dpd_grouped = (
        inad_dpd.groupby(["seller", "dpd_bucket"], observed=True)["valor_parcela"]
        .sum()
        .reset_index()
    )
    dpd_pivot = dpd_grouped.pivot_table(
        index="seller",
        columns="dpd_bucket",
        values="valor_parcela",
        fill_value=0,
    )
    dpd_pivot = dpd_pivot.reindex(columns=_DPD_BUCKET_LABELS, fill_value=0)
    dpd_pivot.columns.name = None
    dpd_pivot["Total"] = dpd_pivot[_DPD_BUCKET_LABELS].sum(axis=1)
    dpd_pivot = dpd_pivot.sort_values("Total", ascending=False)
    dpd_pivot.index.name = "Slug"
    _DPD_ALL_COLS = _DPD_BUCKET_LABELS + ["Total"]
    dpd_pivot_fmt = _format_grid_ptbr(dpd_pivot.copy(), currency_cols=_DPD_ALL_COLS)
    dpd_totals = dpd_pivot[_DPD_ALL_COLS].sum(axis=0)
    dpd_total_df = pd.DataFrame([dpd_totals], index=["Total"])
    dpd_total_df.index.name = "Slug"
    dpd_total_fmt = _format_grid_ptbr(dpd_total_df.copy(), currency_cols=_DPD_ALL_COLS)
    dpd_total_row = dpd_total_fmt.reset_index().to_dict(orient="records")
    render_data_grid(
        dpd_pivot_fmt,
        key="inad-dpd-grid",
        table_preset="standard",
        index_label="Slug",
        pagination=False,
        pinned_bottom_rows=dpd_total_row,
        column_config={lbl: GridColumnConfig(min_width=130, sortable=False) for lbl in _DPD_ALL_COLS},
    )
    collect_dataframe(pd.concat([dpd_pivot_fmt, dpd_total_fmt]))

    st.subheader("Inadimplência de títulos")
    collect_subheader("Inadimplência de títulos")
    st.caption("Detalhamento dos principais títulos inadimplentes por vencimento e severidade.")
    collect_caption("Detalhamento dos principais títulos inadimplentes por vencimento e severidade.")
    cols = ["seller", "sacado_nome", "valor_parcela", "valor_nota", "data_antecipacao", "data_vencimento", "on_book", "days_late", "valor_recompra"]
    detail = inad_titles[cols].sort_values(["data_vencimento", "days_late", "valor_parcela"], ascending=[True, False, False]).copy()
    detail_tbl = detail[["seller", "sacado_nome", "data_vencimento", "valor_parcela", "valor_nota", "on_book", "days_late", "valor_recompra"]].rename(
        columns={
            "seller": "Slug",
            "sacado_nome": "Sacado",
            "data_vencimento": "Vencimento",
            "valor_parcela": "Valor parcela",
            "valor_nota": "Valor nota",
            "on_book": "Em carteira",
            "days_late": "Dias em atraso",
            "valor_recompra": "Valor recompra",
        }
    )
    detail_tbl["Vencimento"] = pd.to_datetime(detail_tbl["Vencimento"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("-")
    detail_grid = _format_grid_ptbr(
        detail_tbl,
        currency_cols=["Valor parcela", "Valor nota", "Valor recompra"],
        integer_cols=["Dias em atraso"],
    )
    detail_grid["Em carteira"] = detail_grid["Em carteira"].map(
        lambda v: "Sim" if pd.to_numeric(v, errors="coerce") == 1 else ("Não" if pd.notna(v) else "-")
    )
    render_data_grid(
        detail_grid,
        key="inad-titles-grid",
        table_preset="large",
        page_size=12,
        quick_filter_placeholder="Filtrar títulos...",
        fit_columns_on_grid_load=True,
        column_config={
            "Slug": GridColumnConfig(min_width=120),
            "Sacado": GridColumnConfig(min_width=260, wrap_text=True, auto_height=True),
            "Vencimento": GridColumnConfig(min_width=120),
            "Valor parcela": GridColumnConfig(min_width=140, sortable=False),
            "Valor nota": GridColumnConfig(min_width=120, sortable=False),
            "Em carteira": GridColumnConfig(min_width=110),
            "Dias em atraso": GridColumnConfig(min_width=120, sortable=False),
            "Valor recompra": GridColumnConfig(min_width=140, sortable=False),
        },
    )
    collect_dataframe(detail_grid)

    st.divider()
    collect_divider()
    st.subheader("Detalhamento por Cedente")
    collect_subheader("Detalhamento por Cedente")
    st.caption(
        "Originação e taxa média ponderada por mês de originação; PD30/LGD/PE por mês de vencimento."
    )
    collect_caption("Originação e taxa média ponderada por mês de originação; PD30/LGD/PE por mês de vencimento.")
    sellers = sorted(df["seller"].dropna().astype(str).unique().tolist())
    if not sellers:
        st.info("Sem cedentes disponíveis.")
        return
    default_seller = SELLER_DRILLDOWN_DEFAULT if SELLER_DRILLDOWN_DEFAULT in sellers else sellers[0]
    col_sel, _ = st.columns([3, 7])
    with col_sel:
        selector = st.selectbox(
            "Selecione o cedente",
            options=sellers,
            index=sellers.index(default_seller),
            key="seller_drilldown_selector",
        )

    _render_seller_drilldown(df, selector, ref_date, render_ui=True, collect=False)

    collect_selector_start(sellers, label="Selecione o cedente")
    for s in sellers:
        collect_selector_option(s)
        _render_seller_drilldown(df, s, ref_date, render_ui=False, collect=True)
    collect_selector_end()
