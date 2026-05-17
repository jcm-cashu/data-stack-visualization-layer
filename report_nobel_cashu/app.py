"""
Report Nobel - Single-page Streamlit dashboard.

Entry point. Edit content via dashboard/queries.py and dashboard/sections.py.
"""
from datetime import date

import streamlit as st

from shared.styles import get_custom_css
from shared.components.html_export import (
    generate_full_export_html,
    start_collection,
    stop_collection,
)

from dashboard.dashboard_config import DASHBOARD_TITLE, DEFAULT_PAGE
from dashboard.sections import render_carteira


st.set_page_config(page_title=DASHBOARD_TITLE, layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)


def _sidebar() -> None:
    """Sidebar: simple title + cache refresh, since this report is point-in-time."""
    st.sidebar.header("Configurações")
    st.sidebar.caption(
        "Os dados refletem a carteira em aberto do Fundo Nobel "
        "(snapshot mais recente da loan tape)."
    )

    if st.sidebar.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.session_state.pop("_export_html", None)
        st.rerun()


def _build_export(render_func, page_label: str, current_blocks: list) -> bytes:
    """Render the single page off-screen for HTML export reuse."""
    ordered = {page_label: current_blocks}
    html = generate_full_export_html(
        ordered,
        title=DASHBOARD_TITLE,
        reference_date=date.today(),
    )
    return html.encode("utf-8")


def main() -> None:
    _sidebar()

    start_collection()
    render_carteira()
    current_blocks = stop_collection()

    st.sidebar.divider()
    if st.sidebar.button("⬇ Preparar exportação HTML"):
        with st.sidebar:
            with st.spinner("Gerando exportação…"):
                st.session_state["_export_html"] = _build_export(
                    render_carteira, DEFAULT_PAGE, current_blocks
                )
                st.session_state["_export_date"] = date.today()
        st.rerun()

    if "_export_html" in st.session_state:
        ref = st.session_state["_export_date"]
        st.sidebar.download_button(
            label="Baixar HTML",
            data=st.session_state["_export_html"],
            file_name=f"report_nobel_{ref.isoformat()}.html",
            mime="text/html",
        )


if __name__ == "__main__":
    main()
