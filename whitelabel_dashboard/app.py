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

# Dashboard-specific imports (EDIT THESE for new dashboards)
from dashboard.dashboard_config import (
    DASHBOARD_TITLE,
    PAGES,
    DEFAULT_PAGE,
    DATE_MIN,
)
from dashboard.sections import render_sumario_geral, render_inadimplencia


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


# =============================================================================
# Sidebar
# =============================================================================

def _sidebar() -> date:
    """Render the sidebar with settings and navigation."""
    st.sidebar.header("Configurações")

    periodo_input = st.sidebar.date_input(
        "Período",
        min_value=DATE_MIN,
        max_value=date.today(),
        help="Selecione a data de referência.",
    )
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

def main() -> None:
    """Main application entry point."""
    _init_session_state()

    st.title(DASHBOARD_TITLE)
    _sidebar()
    
    # Page routing
    pages = {
        "Sumário Geral": render_sumario_geral,
        "Inadimplência": render_inadimplencia,
    }
    
    # Render the selected page
    render_func = pages.get(st.session_state.page, render_sumario_geral)
    render_func()


if __name__ == "__main__":
    main()
