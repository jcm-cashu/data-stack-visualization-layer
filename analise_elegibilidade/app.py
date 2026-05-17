"""
Análise de Elegibilidade — dashboard Streamlit.

Dados: cashu_dev.rpt_data.loan_tape_operacoes_compat_test + dimensões auxiliares.
Agregações e filtros equivalentes ao Selects.txt, em pandas.
"""
import streamlit as st

from shared.styles import get_custom_css
from dashboard.dashboard_config import DASHBOARD_TITLE
from dashboard.sections import render_dashboard


st.set_page_config(page_title=DASHBOARD_TITLE, layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)


def _sidebar() -> None:
    st.sidebar.header("Configurações")
    st.sidebar.caption(
        "Fonte: loan_tape_operacoes_compat_test. "
        "Somas sempre em valor_nota."
    )
    if st.sidebar.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()


def main() -> None:
    _sidebar()
    render_dashboard()


if __name__ == "__main__":
    main()
