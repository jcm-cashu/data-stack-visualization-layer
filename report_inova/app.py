"""
White-Label Dashboard - Main Entry Point

This is the main Streamlit application entry point.
DO NOT MODIFY this file for new dashboards.

To customize a dashboard, edit files in the dashboard/ folder:
- dashboard/dashboard_config.py - Title, pages, filters
- dashboard/queries.py - SQL queries
- dashboard/sections.py - Section render functions (rarely needed)
"""
from datetime import date, timedelta

import streamlit as st

# Shared imports (visual identity - DO NOT MODIFY)
from shared.styles import get_custom_css
from shared.components.html_export import (
    generate_full_export_html,
    start_collection,
    stop_collection,
)

# Dashboard-specific imports (EDIT THESE for new dashboards)
from dashboard.dashboard_config import (
    DASHBOARD_TITLE,
    PAGES,
    DEFAULT_PAGE,
    DATE_MIN,
)
from dashboard.sections import (
    get_default_reference_date,
    render_carteira,
    render_inadimplencia,
    render_performance,
    render_safras,
    render_visao_geral,
)


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(page_title=DASHBOARD_TITLE, layout="wide")

# Apply custom CSS (preserves visual identity)
st.markdown(get_custom_css(), unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

def _init_session_state() -> None:
    """Initialize session state variables."""
    if "date_range" not in st.session_state:
        fim = date.today()
        inicio = fim - timedelta(days=30)
        st.session_state.date_range = (inicio, fim)
    if "page" not in st.session_state:
        st.session_state.page = DEFAULT_PAGE
    if "reference_date" not in st.session_state:
        st.session_state.reference_date = get_default_reference_date()


# =============================================================================
# Sidebar
# =============================================================================

def _sidebar() -> date:
    """Render the sidebar with settings and navigation."""
    st.sidebar.header("Configurações")

    periodo_input = st.sidebar.date_input(
        "Período",
        value=st.session_state.reference_date,
        min_value=DATE_MIN,
        max_value=date.today(),
        help="Selecione a data de referência.",
    )
    if isinstance(periodo_input, tuple):
        periodo_input = periodo_input[-1]
    if periodo_input != st.session_state.reference_date:
        st.session_state.pop("_export_html", None)
    st.session_state.reference_date = periodo_input

    st.sidebar.divider()
    
    # Navigation buttons
    for _label in PAGES:
        if st.session_state.page == _label:
            st.sidebar.markdown(f"<div class='nav-selected'>{_label}</div>", unsafe_allow_html=True)
        else:
            if st.sidebar.button(_label, key=f"nav-{_label}"):
                st.session_state.page = _label
                st.rerun()
    
    return st.session_state.reference_date


# =============================================================================
# Main Application
# =============================================================================

def _build_export(
    all_pages: dict,
    current_page: str,
    current_blocks: list,
) -> bytes:
    """Render every page off-screen and return the HTML export as bytes.

    The *current_page* was already rendered visually, so we reuse its
    pre-collected *current_blocks* to avoid duplicate Streamlit keys.
    """
    collected: dict[str, list] = {}
    for name, render_func in all_pages.items():
        if name == current_page:
            collected[name] = current_blocks
            continue
        placeholder = st.empty()
        with placeholder.container():
            start_collection()
            render_func()
            collected[name] = stop_collection()
        placeholder.empty()

    ordered = {name: collected[name] for name in all_pages if name in collected}
    ref_date = st.session_state.get("reference_date", date.today())
    html = generate_full_export_html(
        ordered,
        title=DASHBOARD_TITLE,
        reference_date=ref_date,
    )
    return html.encode("utf-8")


def main() -> None:
    """Main application entry point."""
    _init_session_state()

    st.title(DASHBOARD_TITLE)
    _sidebar()

    all_pages = {
        "Visão Geral": render_visao_geral,
        "Carteira": render_carteira,
        "Safras": render_safras,
        "Performance": render_performance,
        "Inadimplência": render_inadimplencia,
    }

    current_page = st.session_state.page

    start_collection()
    all_pages[current_page]()
    current_blocks = stop_collection()

    st.sidebar.divider()

    if st.sidebar.button("⬇ Preparar exportação HTML"):
        with st.sidebar:
            with st.spinner("Gerando exportação…"):
                st.session_state["_export_html"] = _build_export(
                    all_pages, current_page, current_blocks,
                )
                st.session_state["_export_date"] = st.session_state.get(
                    "reference_date", date.today()
                )
        st.rerun()

    if "_export_html" in st.session_state:
        ref = st.session_state["_export_date"]
        st.sidebar.download_button(
            label="Baixar HTML",
            data=st.session_state["_export_html"],
            file_name=f"dashboard_{ref.isoformat()}.html",
            mime="text/html",
        )


if __name__ == "__main__":
    main()
