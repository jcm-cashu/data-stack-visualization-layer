"""
Relatório de Conciliação CashU - Main Entry Point

This is the main Streamlit application entry point.
"""
from datetime import date, timedelta

import streamlit as st

# Shared imports (visual identity - DO NOT MODIFY)
from shared.styles import get_custom_css

# Dashboard-specific imports
from dashboard.dashboard_config import (
    DASHBOARD_TITLE,
    PAGES,
    DEFAULT_PAGE,
    DATE_MIN,
    DEFAULT_DATE_START,
    DEFAULT_DATE_END,
)
from dashboard.sections import render_conciliacao_aquisicoes
from dashboard.sections import render_conciliacao_liquidações

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
        # Cap end date to today if default is in the future
        end_date = min(DEFAULT_DATE_END, date.today())
        st.session_state.date_range = (DEFAULT_DATE_START, end_date)
    if "page" not in st.session_state:
        st.session_state.page = DEFAULT_PAGE


# =============================================================================
# Sidebar
# =============================================================================

def _sidebar() -> None:
    """Render the sidebar with date range settings and navigation."""
    st.sidebar.header("Configurações")

    # Date range selector
    date_range = st.sidebar.date_input(
        "Período",
        value=st.session_state.date_range,
        min_value=DATE_MIN,
        max_value=date.today(),
        help="Selecione o período de início e fim.",
    )
    
    # Handle both single date and date range
    if isinstance(date_range, tuple) and len(date_range) == 2:
        st.session_state.date_range = date_range
        st.session_state.date_start = date_range[0]
        st.session_state.date_end = date_range[1]
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        st.session_state.date_start = date_range[0]
        st.session_state.date_end = date_range[0]
    else:
        st.session_state.date_start = date_range
        st.session_state.date_end = date_range

    st.sidebar.divider()
    
    # Navigation buttons
    for _label in PAGES:
        if st.session_state.page == _label:
            st.sidebar.markdown(f"<div class='nav-selected'>{_label}</div>", unsafe_allow_html=True)
        else:
            if st.sidebar.button(_label, key=f"nav-{_label}"):
                st.session_state.page = _label
                st.rerun()


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
        "Conciliação Aquisições": render_conciliacao_aquisicoes,
        "Conciliação Liquidações": render_conciliacao_liquidações,
    }
    
    # Render the selected page
    render_func = pages.get(st.session_state.page, render_conciliacao_aquisicoes)
    render_func()


if __name__ == "__main__":
    main()
