"""
Relatório Metas Sales CashU - Main Entry Point

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
    MONTH_NAMES,
    MIN_YEAR,
)
from dashboard.sections import render_metas_sales

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
    today = date.today()
    
    # Default to current month/year
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = today.month
    if "selected_year" not in st.session_state:
        st.session_state.selected_year = today.year
    if "page" not in st.session_state:
        st.session_state.page = DEFAULT_PAGE


# =============================================================================
# Sidebar
# =============================================================================

def _sidebar() -> None:
    """Render the sidebar with month/year selector and navigation."""
    st.sidebar.header("Configurações")
    
    today = date.today()
    
    # Year selector
    years = list(range(MIN_YEAR, today.year + 1))
    selected_year = st.sidebar.selectbox(
        "Ano",
        options=years,
        index=years.index(st.session_state.selected_year) if st.session_state.selected_year in years else len(years) - 1,
        help="Selecione o ano.",
    )
    st.session_state.selected_year = selected_year
    
    # Month selector - if current year, only show months up to current month
    if selected_year == today.year:
        available_months = list(range(1, today.month + 1))
    else:
        available_months = list(range(1, 13))
    
    # Create month options with names
    month_options = {m: MONTH_NAMES[m - 1] for m in available_months}
    
    selected_month = st.sidebar.selectbox(
        "Mês",
        options=list(month_options.keys()),
        format_func=lambda x: month_options[x],
        index=available_months.index(st.session_state.selected_month) if st.session_state.selected_month in available_months else len(available_months) - 1,
        help="Selecione o mês.",
    )
    st.session_state.selected_month = selected_month

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
        "Metas Sales": render_metas_sales,
    }
    
    # Render the selected page
    render_func = pages.get(st.session_state.page, render_metas_sales)
    render_func()


if __name__ == "__main__":
    main()
