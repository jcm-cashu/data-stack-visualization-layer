"""AG Grid wrapper component for configurable table rendering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import streamlit as st
from ..styles import COLORS

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

    _HAS_AGGRID = True
except ImportError:
    _HAS_AGGRID = False
    JsCode = None  # type: ignore[assignment]


@dataclass
class GridColumnConfig:
    """Per-column AG Grid configuration."""

    header_name: str | None = None
    width: int | None = None
    min_width: int | None = None
    max_width: int | None = None
    pinned: str | None = None
    hide: bool | None = None
    sortable: bool | None = None
    filterable: bool | None = None
    resizable: bool | None = None
    wrap_text: bool | None = None
    auto_height: bool | None = None
    type: list[str] = field(default_factory=list)
    value_formatter: str | None = None


@dataclass
class GridTheme:
    """Design-system aware theme configuration for AG Grid."""

    header_bg: str = COLORS["table_header"]
    header_fg: str = COLORS["table_header_text"]
    text_color: str = COLORS["text_primary"]
    border_color: str = COLORS["table_border"]
    row_even_bg: str = COLORS["table_stripe"]
    row_odd_bg: str = COLORS["bg_white"]
    hover_bg: str = COLORS["table_hover"]
    selected_bg: str = "#f5c34433"
    input_bg: str = COLORS["bg_white"]
    input_fg: str = COLORS["text_primary"]
    input_border: str = COLORS["table_border"]
    font_family: str = "Red Hat Display, sans-serif"
    row_height: int = 28
    header_height: int = 34
    pagination_height: int = 34


def get_design_system_grid_theme() -> GridTheme:
    """Return the default Report Inova design-system grid theme."""
    return GridTheme()


def _build_custom_css(theme: GridTheme) -> dict[str, dict[str, str]]:
    """Build AG Grid custom CSS from a theme object."""
    return {
        ".ag-root-wrapper": {
            "border": f"1px solid {theme.border_color}",
            "border-radius": "8px",
            "overflow": "hidden",
            "font-family": theme.font_family,
            "color": theme.text_color,
        },
        ".ag-header": {
            "background-color": theme.header_bg,
            "border-bottom": f"1px solid {theme.border_color}",
        },
        ".ag-header-cell": {
            "background-color": theme.header_bg,
            "color": theme.header_fg,
            "font-weight": "700",
            "border-right": f"1px solid {theme.border_color}",
        },
        ".ag-header-cell-label": {
            "font-weight": "700",
            "color": theme.header_fg,
        },
        ".ag-row": {
            "border-bottom": f"1px solid {theme.border_color}",
            "color": theme.text_color,
        },
        ".ag-row-even": {
            "background-color": theme.row_even_bg,
        },
        ".ag-row-odd": {
            "background-color": theme.row_odd_bg,
        },
        ".ag-row-hover": {
            "background-color": f"{theme.hover_bg} !important",
        },
        ".ag-row-selected": {
            "background-color": f"{theme.selected_bg} !important",
        },
        ".ag-cell": {
            "color": theme.text_color,
            "font-family": theme.font_family,
        },
        ".ag-paging-panel": {
            "border-top": f"1px solid {theme.border_color}",
            "color": theme.text_color,
            "font-family": theme.font_family,
        },
        ".ag-input-field-input": {
            "background-color": theme.input_bg,
            "color": theme.input_fg,
            "border": f"1px solid {theme.input_border}",
        },
        ".ag-filter-toolpanel-header, .ag-side-buttons": {
            "background-color": theme.row_even_bg,
            "color": theme.text_color,
            "border-bottom": f"1px solid {theme.border_color}",
        },
    }


def _coerce_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d")
    return out


def _apply_column_config(
    gb: "GridOptionsBuilder",
    config: dict[str, GridColumnConfig | dict[str, Any]] | None,
) -> None:
    if not config:
        return

    for col_name, col_cfg in config.items():
        if isinstance(col_cfg, GridColumnConfig):
            cfg = col_cfg
        else:
            cfg = GridColumnConfig(
                header_name=col_cfg.get("header_name"),
                width=col_cfg.get("width"),
                min_width=col_cfg.get("min_width"),
                max_width=col_cfg.get("max_width"),
                pinned=col_cfg.get("pinned"),
                hide=col_cfg.get("hide"),
                sortable=col_cfg.get("sortable"),
                filterable=col_cfg.get("filterable"),
                resizable=col_cfg.get("resizable"),
                wrap_text=col_cfg.get("wrap_text"),
                auto_height=col_cfg.get("auto_height"),
                type=list(col_cfg.get("type", [])),
                value_formatter=col_cfg.get("value_formatter"),
            )

        col_kwargs: dict[str, Any] = {k: v for k, v in {
            "header_name": cfg.header_name,
            "width": cfg.width,
            "minWidth": cfg.min_width,
            "maxWidth": cfg.max_width,
            "pinned": cfg.pinned,
            "hide": cfg.hide,
            "sortable": cfg.sortable,
            "filter": cfg.filterable,
            "resizable": cfg.resizable,
            "wrapText": cfg.wrap_text,
            "autoHeight": cfg.auto_height,
            "type": cfg.type if cfg.type else None,
        }.items() if v is not None}
        if cfg.value_formatter and JsCode is not None:
            col_kwargs["valueFormatter"] = JsCode(cfg.value_formatter)
        gb.configure_column(col_name, **col_kwargs)


def render_data_grid(
    df: pd.DataFrame,
    key: str,
    *,
    table_preset: str = "standard",
    index_label: str | None = None,
    height: int | None = None,
    width: str | None = None,
    center: bool | None = None,
    fit_columns_on_grid_load: bool | None = None,
    pagination: bool | None = None,
    page_size: int | None = None,
    enable_sidebar: bool = False,
    enable_quick_filter: bool = False,
    quick_filter_placeholder: str = "Filtrar...",
    sortable: bool = True,
    filterable: bool = True,
    resizable: bool = True,
    editable: bool = False,
    column_config: dict[str, GridColumnConfig | dict[str, Any]] | None = None,
    pinned_bottom_rows: list[dict[str, Any]] | None = None,
    selection_mode: str | None = None,
    ag_theme: str = "streamlit",
    grid_theme: GridTheme | None = None,
) -> dict[str, Any] | None:
    """
    Render a configurable AG Grid table.

    Falls back to st.dataframe if streamlit-aggrid is unavailable.
    """
    if df.empty:
        st.info("Sem dados para exibir.")
        return None

    table_df = _coerce_columns(df)
    if index_label and not isinstance(table_df.index, pd.RangeIndex):
        table_df = table_df.reset_index().rename(columns={"index": index_label})

    if not _HAS_AGGRID:
        st.warning("Dependência opcional `streamlit-aggrid` não instalada; usando tabela padrão.")
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        return None

    preset_defaults = {
        "compact": {
            "min_height": 180,
            "max_height": 300,
            "width": "72%",
            "center": True,
            "fit_columns_on_grid_load": True,
            "pagination": False,
            "page_size": 10,
            "enable_quick_filter": False,
        },
        "standard": {
            "min_height": 210,
            "max_height": 440,
            "width": "90%",
            "center": True,
            "fit_columns_on_grid_load": True,
            "pagination": True,
            "page_size": 12,
            "enable_quick_filter": False,
        },
        "large": {
            "min_height": 320,
            "max_height": 680,
            "width": "100%",
            "center": False,
            "fit_columns_on_grid_load": True,
            "pagination": True,
            "page_size": 20,
            "enable_quick_filter": True,
        },
    }
    preset = preset_defaults.get(table_preset, preset_defaults["standard"])
    width = preset["width"] if width is None else width
    center = preset["center"] if center is None else center
    fit_columns_on_grid_load = preset["fit_columns_on_grid_load"] if fit_columns_on_grid_load is None else fit_columns_on_grid_load
    pagination = preset["pagination"] if pagination is None else pagination
    page_size = preset["page_size"] if page_size is None else page_size
    if not enable_quick_filter:
        enable_quick_filter = preset["enable_quick_filter"]

    effective_theme = grid_theme or get_design_system_grid_theme()
    custom_css = _build_custom_css(effective_theme)

    if height is None:
        visible_rows = min(len(table_df), page_size) if pagination else len(table_df)
        row_height = effective_theme.row_height
        header_height = effective_theme.header_height
        pager_height = effective_theme.pagination_height if pagination else 0
        padding = 8
        auto_height = header_height + (visible_rows * row_height) + pager_height + padding
        height = int(max(preset["min_height"], min(auto_height, preset["max_height"])))

    if enable_quick_filter:
        # Keep quick filter left-aligned with a constrained width.
        col_filter, _ = st.columns([3, 9])
        with col_filter:
            quick_value = st.text_input(
                "Filtro rápido",
                value="",
                placeholder=quick_filter_placeholder,
                key=f"{key}-quick-filter",
                label_visibility="collapsed",
            )
    else:
        quick_value = ""

    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_default_column(
        sortable=sortable,
        filter=filterable,
        resizable=resizable,
        editable=editable,
    )

    if pagination:
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)

    if selection_mode:
        gb.configure_selection(selection_mode)

    if enable_sidebar:
        gb.configure_side_bar()

    _apply_column_config(gb, column_config)

    grid_options = gb.build()
    grid_options["rowHeight"] = effective_theme.row_height
    grid_options["headerHeight"] = effective_theme.header_height
    if quick_value:
        grid_options["quickFilterText"] = quick_value
    if pinned_bottom_rows:
        grid_options["pinnedBottomRowData"] = pinned_bottom_rows

    if center:
        col_l, col_mid, col_r = st.columns([1, 10, 1])
        with col_mid:
            response = AgGrid(
                table_df,
                gridOptions=grid_options,
                height=height,
                width=width,
                fit_columns_on_grid_load=fit_columns_on_grid_load,
                update_mode=GridUpdateMode.NO_UPDATE,
                theme=ag_theme,
                custom_css=custom_css,
                allow_unsafe_jscode=True,
                key=key,
            )
    else:
        response = AgGrid(
            table_df,
            gridOptions=grid_options,
            height=height,
            width=width,
            fit_columns_on_grid_load=fit_columns_on_grid_load,
            update_mode=GridUpdateMode.NO_UPDATE,
            theme=ag_theme,
            custom_css=custom_css,
            allow_unsafe_jscode=True,
            key=key,
        )
    return response

