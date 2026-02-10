"""
Dashboard Sections - Relatório de Conciliação CashU

Section render functions for the reconciliation dashboard between
CashU Invoice Financing and Fund Administrator systems.
"""
import streamlit as st
import pandas as pd

# Shared imports (DO NOT MODIFY these imports)
from shared.db import run_query
from shared.styles import COLORS

# Dashboard-specific imports
from . import queries


# =============================================================================
# Helper Functions
# =============================================================================

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase for consistency."""
    df.columns = df.columns.str.lower()
    return df


def _first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column name that exists in df, else None."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _as_date_series(s: pd.Series) -> pd.Series:
    """Best-effort conversion to python date objects."""
    try:
        return pd.to_datetime(s, errors="coerce").dt.date
    except Exception:
        return s


def format_currency(value: float) -> str:
    """Format a number as Brazilian currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: int) -> str:
    """Format a number with thousand separators."""
    return f"{value:,}".replace(",", ".")


def _get_date_range() -> tuple[str, str]:
    """Get the date range from session state."""
    date_start = st.session_state.get("date_start")
    date_end = st.session_state.get("date_end")
    return str(date_start), str(date_end)


# =============================================================================
# Data Loading Functions
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def _load_cashu_data(date_start: str, date_end: str) -> pd.DataFrame:
    """Load CashU Invoice Financing data."""
    sql = queries.get_cashu_query(date_start, date_end)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=300, show_spinner=False)
def _load_admin_data(date_start: str, date_end: str) -> pd.DataFrame:
    """Load Fund Administrator data."""
    sql = queries.get_admin_query(date_start, date_end)
    return _normalize_columns(run_query(sql))


def _load_all_data() -> dict:
    """Load and process all data for reconciliation."""
    date_start, date_end = _get_date_range()
    
    # Load base data
    df_cashu = _load_cashu_data(date_start, date_end)
    df_admin = _load_admin_data(date_start, date_end)
    
    # Identified titles (matching between systems)
    if not df_cashu.empty and not df_admin.empty:
        titulos_identificados = pd.merge(
            df_cashu, 
            df_admin, 
            on="id_inv_fin_item", 
            how="inner",
            suffixes=("_cashu", "_admin")
        )
        
        # Mismatched values
        titulos_divergentes = titulos_identificados[
            (titulos_identificados["amt_future"] != titulos_identificados["amt_total"]) |
            (titulos_identificados["amt_acq"] != titulos_identificados["amt_net"])
        ].copy()
    else:
        titulos_identificados = pd.DataFrame()
        titulos_divergentes = pd.DataFrame()
    
    # Admin titles not in CashU
    if not df_admin.empty and not df_cashu.empty:
        df_admin_sem_cashu = df_admin[~df_admin["id_inv_fin_item"].isin(df_cashu["id_inv_fin_item"])].copy()
    elif not df_admin.empty:
        df_admin_sem_cashu = df_admin.copy()
    else:
        df_admin_sem_cashu = pd.DataFrame()
    
    # CashU titles not in Admin
    if not df_cashu.empty and not df_admin.empty:
        df_cashu_sem_admin = df_cashu[~df_cashu["id_inv_fin_item"].isin(df_admin["id_inv_fin_item"])].copy()
    elif not df_cashu.empty:
        df_cashu_sem_admin = df_cashu.copy()
    else:
        df_cashu_sem_admin = pd.DataFrame()
    
    return {
        "df_cashu": df_cashu,
        "df_admin": df_admin,
        "titulos_identificados": titulos_identificados,
        "titulos_divergentes": titulos_divergentes,
        "df_admin_sem_cashu": df_admin_sem_cashu,
        "df_cashu_sem_admin": df_cashu_sem_admin,
    }


# =============================================================================
# Section Render Functions
# =============================================================================

def _render_cashu_kpis(df_cashu: pd.DataFrame) -> None:
    """Render KPIs for CashU Invoice Financing system."""
    st.subheader("Sistema CashU Invoice Financing")
    
    if df_cashu.empty:
        st.info("Nenhum título encontrado no período selecionado.")
        return
    
    num_titulos = len(df_cashu)
    valor_face = df_cashu["amt_total"].sum()
    valor_antecipado = df_cashu["amt_net"].sum()
    valor_pos_taxas = df_cashu["amt_post_fees_pre_mdr"].sum() if "amt_post_fees_pre_mdr" in df_cashu.columns else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("# Títulos", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Antecipado", format_currency(valor_antecipado))


def _render_admin_kpis(df_admin: pd.DataFrame) -> None:
    """Render KPIs for Fund Administrator system."""
    st.subheader("Sistema Administrador do Fundo")
    
    if df_admin.empty:
        st.info("Nenhum título encontrado no período selecionado.")
        return
    
    num_titulos = len(df_admin)
    valor_face = df_admin["amt_future"].sum()
    valor_antecipado = df_admin["amt_acq"].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("# Títulos", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Antecipado", format_currency(valor_antecipado))


def _render_matched_titles(titulos_identificados: pd.DataFrame) -> None:
    """Render section for matched titles with difference KPIs."""
    st.subheader("Títulos Identificados")
    
    if titulos_identificados.empty:
        st.warning("Nenhum título foi identificado entre os dois sistemas.")
        return
    
    # Calculate differences
    diff_face = titulos_identificados["amt_future"].sum() - titulos_identificados["amt_total"].sum()
    diff_antecipado = titulos_identificados["amt_acq"].sum() - titulos_identificados["amt_net"].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("# Títulos Identificados", format_number(len(titulos_identificados)))
    with col2:
        delta_color = "off" if abs(diff_face) < 0.01 else "inverse"
        st.metric(
            "Diferença Valor Face", 
            format_currency(diff_face),
            delta="OK" if abs(diff_face) < 0.01 else "Divergência",
            delta_color=delta_color
        )
    with col3:
        delta_color = "off" if abs(diff_antecipado) < 0.01 else "inverse"
        st.metric(
            "Diferença Valor Antecipado", 
            format_currency(diff_antecipado),
            delta="OK" if abs(diff_antecipado) < 0.01 else "Divergência",
            delta_color=delta_color
        )


def _render_divergent_values(titulos_divergentes: pd.DataFrame) -> None:
    """Render table of titles with mismatched values."""
    if titulos_divergentes.empty:
        st.success("✓ Todos os títulos identificados possuem valores consistentes entre os sistemas.")
        return
    
    st.warning(f"⚠ {len(titulos_divergentes)} títulos com valores divergentes encontrados.")
    
    df_tmp = titulos_divergentes.copy()

    # Derive normalized columns (robust to merge suffixing)
    invoice_anticipated_col = _first_existing_col(df_tmp, ["anticipated_at", "anticipated_at_cashu"])
    kanastra_entry_col = _first_existing_col(df_tmp, ["anticipation_date_admin", "anticipation_date"])

    invoice_cnpj_col = _first_existing_col(df_tmp, ["nr_gov_id_seller", "nr_gov_id_seller_cashu"])
    kanastra_cnpj_col = _first_existing_col(df_tmp, ["nr_gov_id_cedent_admin", "nr_gov_id_cedent"])

    invoice_doc_col = _first_existing_col(df_tmp, ["nr_cnab_doc_cashu", "nr_cnab_doc"])
    kanastra_doc_col = _first_existing_col(df_tmp, ["nr_cnab_doc_admin"])

    invoice_ctrl_col = _first_existing_col(df_tmp, ["nr_cnab_ctrl_cashu", "nr_cnab_ctrl"])
    kanastra_ctrl_col = _first_existing_col(df_tmp, ["nr_cnab_ctrl_admin"])

    venc_invoice_col = _first_existing_col(df_tmp, ["due_date_cashu", "due_date"])
    venc_kanastra_col = _first_existing_col(df_tmp, ["due_date_admin"])

    if invoice_anticipated_col:
        df_tmp["data_antecipacao_invoice"] = _as_date_series(df_tmp[invoice_anticipated_col])
    if kanastra_entry_col:
        df_tmp["data_entrada_kanastra"] = _as_date_series(df_tmp[kanastra_entry_col])

    if invoice_cnpj_col:
        df_tmp["cnpj_emitente_invoice"] = df_tmp[invoice_cnpj_col]
    if kanastra_cnpj_col:
        df_tmp["cnpj_emitente_kanastra"] = df_tmp[kanastra_cnpj_col]
        # Same field requested as "documento do emitente"
        df_tmp["documento_emitente_kanastra"] = df_tmp[kanastra_cnpj_col]

    if invoice_doc_col:
        df_tmp["numero_documento_invoice"] = df_tmp[invoice_doc_col]
    if kanastra_doc_col:
        df_tmp["numero_documento_kanastra"] = df_tmp[kanastra_doc_col]

    if invoice_ctrl_col:
        df_tmp["seu_numero_invoice"] = df_tmp[invoice_ctrl_col]
    if kanastra_ctrl_col:
        df_tmp["seu_numero_kanastra"] = df_tmp[kanastra_ctrl_col]

    if venc_invoice_col:
        df_tmp["vencimento_invoice"] = _as_date_series(df_tmp[venc_invoice_col])
    if venc_kanastra_col:
        df_tmp["vencimento_kanastra"] = _as_date_series(df_tmp[venc_kanastra_col])

    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item",
        "cd_name_slug",
        "data_antecipacao_invoice",
        "data_entrada_kanastra",
        "cnpj_emitente_invoice",
        "cnpj_emitente_kanastra",
        "documento_emitente_kanastra",
        "numero_documento_invoice",
        "numero_documento_kanastra",
        "seu_numero_invoice",
        "seu_numero_kanastra",
        "vencimento_invoice",
        "vencimento_kanastra",
        "amt_total",
        "amt_future",
        "amt_net",
        "amt_acq",
    ]
    available_cols = [c for c in display_cols if c in df_tmp.columns]
    df_display = df_tmp[available_cols].copy()
    
    # Rename columns for better readability
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_name_slug": "Corporate",
        "data_antecipacao_invoice": "Data Antecipação (Invoice)",
        "data_entrada_kanastra": "Data Entrada (Kanastra)",
        "cnpj_emitente_invoice": "CNPJ Emitente (Invoice)",
        "cnpj_emitente_kanastra": "CNPJ Emitente (Kanastra)",
        "documento_emitente_kanastra": "Documento Emitente (Kanastra)",
        "numero_documento_invoice": "Número Documento (Invoice)",
        "numero_documento_kanastra": "Número Documento (Kanastra)",
        "seu_numero_invoice": "Seu Número (Invoice)",
        "seu_numero_kanastra": "Seu Número (Kanastra)",
        "vencimento_invoice": "Vencimento (Invoice)",
        "vencimento_kanastra": "Vencimento (Kanastra)",
        "amt_total": "Valor Face (CashU)",
        "amt_future": "Valor Face (Admin)",
        "amt_net": "Valor Líquido (CashU)",
        "amt_acq": "Valor Líquido (Admin)",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name="titulos_divergentes_aquisicoes.csv",
        mime="text/csv",
        key="download_acq_divergentes"
    )


def _render_cashu_sem_admin(df_cashu_sem_admin: pd.DataFrame) -> None:
    """Render section for CashU titles not found in Admin."""
    st.subheader("Títulos CashU sem Match no Administrador")
    
    num_titulos = len(df_cashu_sem_admin)
    valor_face = df_cashu_sem_admin["amt_total"].sum() if not df_cashu_sem_admin.empty else 0
    valor_liquido = df_cashu_sem_admin["amt_net"].sum() if not df_cashu_sem_admin.empty else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("# Títulos", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Líquido", format_currency(valor_liquido))
    
    if df_cashu_sem_admin.empty:
        st.success("✓ Todos os títulos da CashU foram identificados no Sistema Administrador.")
        return
    
    st.error(f"✗ {num_titulos} títulos da CashU não encontrados no Sistema do Administrador.")
    
    df_tmp = df_cashu_sem_admin.copy()

    invoice_anticipated_col = _first_existing_col(df_tmp, ["anticipated_at"])
    if invoice_anticipated_col:
        df_tmp["data_antecipacao_invoice"] = _as_date_series(df_tmp[invoice_anticipated_col])

    if "nr_gov_id_seller" in df_tmp.columns:
        df_tmp["cnpj_emitente_invoice"] = df_tmp["nr_gov_id_seller"]
    if "nr_cnab_doc" in df_tmp.columns:
        df_tmp["numero_documento_invoice"] = df_tmp["nr_cnab_doc"]
    if "nr_cnab_ctrl" in df_tmp.columns:
        df_tmp["seu_numero_invoice"] = df_tmp["nr_cnab_ctrl"]
    # Keep column parity across acquisition tables (no Admin/Kanastra match here)
    df_tmp["documento_emitente_kanastra"] = pd.NA

    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item",
        "data_antecipacao_invoice",
        "cd_name_slug",
        "cnpj_emitente_invoice",
        "numero_documento_invoice",
        "seu_numero_invoice",
        "due_date",
        "amt_total",
        "amt_net",
    ]
    available_cols = [c for c in display_cols if c in df_tmp.columns]
    df_display = df_tmp[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "data_antecipacao_invoice": "Data Antecipação (Invoice)",
        "cd_name_slug": "Corporate",
        "cnpj_emitente_invoice": "CNPJ Emitente (Invoice)",
        "numero_documento_invoice": "Número Documento (Invoice)",
        "seu_numero_invoice": "Seu Número (Invoice)",
        "documento_emitente_kanastra": "Documento Emitente (Kanastra)",
        "due_date": "Vencimento",
        "amt_total": "Valor Face",
        "amt_net": "Valor Líquido",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name="aquisicoes_cashu_sem_administrador.csv",
        mime="text/csv",
        key="download_acq_cashu_sem_admin"
    )


def _render_admin_sem_cashu(df_admin_sem_cashu: pd.DataFrame) -> None:
    """Render section for Admin titles not found in CashU."""
    st.subheader("Títulos Administrador sem Match na CashU")
    
    num_titulos = len(df_admin_sem_cashu)
    valor_face = df_admin_sem_cashu["amt_future"].sum() if not df_admin_sem_cashu.empty else 0
    valor_liquido = df_admin_sem_cashu["amt_acq"].sum() if not df_admin_sem_cashu.empty else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("# Títulos", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Líquido", format_currency(valor_liquido))
    
    if df_admin_sem_cashu.empty:
        st.success("✓ Todos os títulos do Administrador foram identificados no Sistema CashU.")
        return
    
    st.error(f"✗ {num_titulos} títulos do Administrador não encontrados no Sistema CashU.")
    
    df_tmp = df_admin_sem_cashu.copy()
    print(df_tmp.columns)

    kanastra_entry_col = _first_existing_col(df_tmp, ["anticipation_date", "ref_date"])
    if kanastra_entry_col:
        df_tmp["data_entrada_kanastra"] = _as_date_series(df_tmp[kanastra_entry_col])

    if "nr_gov_id_cedent" in df_tmp.columns:
        df_tmp["cnpj_emitente_kanastra"] = df_tmp["nr_gov_id_cedent"]
        df_tmp["documento_emitente_kanastra"] = df_tmp["nr_gov_id_cedent"]
    if "nr_cnab_doc" in df_tmp.columns:
        df_tmp["numero_documento_kanastra"] = df_tmp["nr_cnab_doc"]
    if "nr_cnab_ctrl" in df_tmp.columns:
        df_tmp["seu_numero_kanastra"] = df_tmp["nr_cnab_ctrl"]

    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item",
        "data_entrada_kanastra",
        "cd_slug_oper",
        "cnpj_emitente_kanastra",
        "numero_documento_kanastra",
        "seu_numero_kanastra",
        "nm_cedent",
        "due_date",
        "amt_future",
        "amt_acq",
    ]
    available_cols = [c for c in display_cols if c in df_tmp.columns]
    df_display = df_tmp[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "data_entrada_kanastra": "Data Entrada (Kanastra)",
        "cd_slug_oper": "Operação",
        "cnpj_emitente_kanastra": "CNPJ Emitente (Kanastra)",
        "documento_emitente_kanastra": "Documento Emitente (Kanastra)",
        "numero_documento_kanastra": "Número Documento (Kanastra)",
        "seu_numero_kanastra": "Seu Número (Kanastra)",
        "nm_debtor": "Devedor",
        "nm_cedent": "Cedente",
        "due_date": "Vencimento",
        "amt_future": "Valor Face",
        "amt_acq": "Valor Líquido",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name="aquisicoes_administrador_sem_cashu.csv",
        mime="text/csv",
        key="download_acq_admin_sem_cashu"
    )


# =============================================================================
# Main Page Render Function
# =============================================================================

def render_conciliacao_aquisicoes() -> None:
    """Render the 'Conciliação' page."""
    # Load all data
    with st.spinner("Carregando dados..."):
        data = _load_all_data()
    
    # Render sections
    _render_cashu_kpis(data["df_cashu"])
    st.divider()
    
    _render_admin_kpis(data["df_admin"])
    st.divider()
    
    _render_matched_titles(data["titulos_identificados"])
    _render_divergent_values(data["titulos_divergentes"])
    st.divider()
    
    _render_cashu_sem_admin(data["df_cashu_sem_admin"])
    st.divider()
    
    _render_admin_sem_cashu(data["df_admin_sem_cashu"])

# =============================================================================
# LIQUIDATIONS - Data Loading Functions
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def _load_cashu_liquidations(date_start: str, date_end: str) -> pd.DataFrame:
    """Load CashU liquidations data."""
    sql = queries.get_cashu_liquidations_query(date_start, date_end)
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=300, show_spinner=False)
def _load_admin_liquidations(date_start: str, date_end: str) -> pd.DataFrame:
    """Load Fund Administrator liquidations data."""
    sql = queries.get_admin_liquidations_query(date_start, date_end)
    return _normalize_columns(run_query(sql))


def _load_all_liquidations_data() -> dict:
    """Load and process all data for liquidations reconciliation."""
    date_start, date_end = _get_date_range()
    
    # Load base data
    df_cashu = _load_cashu_liquidations(date_start, date_end)
    df_admin = _load_admin_liquidations(date_start, date_end)
    
    # Identified titles (matching between systems)
    if not df_cashu.empty and not df_admin.empty:
        titulos_identificados = pd.merge(
            df_cashu, 
            df_admin, 
            on="id_inv_fin_item", 
            how="inner",
            suffixes=("_cashu", "_admin")
        )
        
        # Mismatched values - compare AMT_PAID vs AMT_PYMT and AMT_TOTAL vs AMT_FUTURE
        titulos_divergentes = titulos_identificados[
            (abs(titulos_identificados["amt_future"] - titulos_identificados["amt_total"]) > 0.01) |
            (abs(titulos_identificados["amt_pymt"] - titulos_identificados["amt_paid"]) > 0.01)
        ].copy()
    else:
        titulos_identificados = pd.DataFrame()
        titulos_divergentes = pd.DataFrame()
    
    # Admin titles not in CashU
    if not df_admin.empty and not df_cashu.empty:
        df_admin_sem_cashu = df_admin[~df_admin["id_inv_fin_item"].isin(df_cashu["id_inv_fin_item"])].copy()
    elif not df_admin.empty:
        df_admin_sem_cashu = df_admin.copy()
    else:
        df_admin_sem_cashu = pd.DataFrame()
    
    # CashU titles not in Admin
    if not df_cashu.empty and not df_admin.empty:
        df_cashu_sem_admin = df_cashu[~df_cashu["id_inv_fin_item"].isin(df_admin["id_inv_fin_item"])].copy()
    elif not df_cashu.empty:
        df_cashu_sem_admin = df_cashu.copy()
    else:
        df_cashu_sem_admin = pd.DataFrame()
    
    return {
        "df_cashu": df_cashu,
        "df_admin": df_admin,
        "titulos_identificados": titulos_identificados,
        "titulos_divergentes": titulos_divergentes,
        "df_admin_sem_cashu": df_admin_sem_cashu,
        "df_cashu_sem_admin": df_cashu_sem_admin,
    }


# =============================================================================
# LIQUIDATIONS - Section Render Functions
# =============================================================================

def _render_cashu_liquidations_kpis(df_cashu: pd.DataFrame) -> None:
    """Render KPIs for CashU liquidations system."""
    st.subheader("Sistema CashU - Liquidações")
    
    if df_cashu.empty:
        st.info("Nenhuma liquidação encontrada no período selecionado.")
        return
    
    num_titulos = len(df_cashu)
    valor_face = df_cashu["amt_total"].sum()
    valor_pago = df_cashu["amt_paid"].sum()
    valor_juros = df_cashu["amt_int"].sum() if "amt_int" in df_cashu.columns else 0
    valor_multa = df_cashu["amt_pnlt"].sum() if "amt_pnlt" in df_cashu.columns else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("# Títulos", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Pago", format_currency(valor_pago))
    with col4:
        st.metric("Juros", format_currency(valor_juros))
    with col5:
        st.metric("Multa", format_currency(valor_multa))


def _render_admin_liquidations_kpis(df_admin: pd.DataFrame) -> None:
    """Render KPIs for Fund Administrator liquidations system."""
    st.subheader("Sistema Administrador do Fundo - Liquidações")
    
    if df_admin.empty:
        st.info("Nenhuma liquidação encontrada no período selecionado.")
        return
    
    num_titulos = len(df_admin)
    valor_face = df_admin["amt_future"].sum()
    valor_pago = df_admin["amt_pymt"].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("# Títulos", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Pago", format_currency(valor_pago))


def _render_matched_liquidations(titulos_identificados: pd.DataFrame) -> None:
    """Render section for matched liquidations with difference KPIs."""
    st.subheader("Liquidações Identificadas")
    
    if titulos_identificados.empty:
        st.warning("Nenhuma liquidação foi identificada entre os dois sistemas.")
        return
    
    # Calculate differences
    diff_face = titulos_identificados["amt_future"].sum() - titulos_identificados["amt_total"].sum()
    diff_pago = titulos_identificados["amt_pymt"].sum() - titulos_identificados["amt_paid"].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("# Liquidações Identificadas", format_number(len(titulos_identificados)))
    with col2:
        delta_color = "off" if abs(diff_face) < 0.01 else "inverse"
        st.metric(
            "Diferença Valor Face", 
            format_currency(diff_face),
            delta="OK" if abs(diff_face) < 0.01 else "Divergência",
            delta_color=delta_color
        )
    with col3:
        delta_color = "off" if abs(diff_pago) < 0.01 else "inverse"
        st.metric(
            "Diferença Valor Pago", 
            format_currency(diff_pago),
            delta="OK" if abs(diff_pago) < 0.01 else "Divergência",
            delta_color=delta_color
        )


def _render_divergent_liquidations(titulos_divergentes: pd.DataFrame) -> None:
    """Render table of liquidations with mismatched values."""
    if titulos_divergentes.empty:
        st.success("✓ Todas as liquidações identificadas possuem valores consistentes entre os sistemas.")
        return
    
    st.warning(f"⚠ {len(titulos_divergentes)} liquidações com valores divergentes encontradas.")
    
    df_tmp = titulos_divergentes.copy()

    if "nr_gov_id_seller" in df_tmp.columns:
        df_tmp["cnpj_emitente_invoice"] = df_tmp["nr_gov_id_seller"]

    # CNAB identifiers (both sides, when available)
    if "nr_cnab_doc_cashu" in df_tmp.columns:
        df_tmp["numero_documento_cashu"] = df_tmp["nr_cnab_doc_cashu"]
    elif "nr_cnab_doc" in df_tmp.columns:
        df_tmp["numero_documento_cashu"] = df_tmp["nr_cnab_doc"]
    if "nr_cnab_doc_admin" in df_tmp.columns:
        df_tmp["numero_documento_admin"] = df_tmp["nr_cnab_doc_admin"]

    if "nr_cnab_ctrl_cashu" in df_tmp.columns:
        df_tmp["seu_numero_cashu"] = df_tmp["nr_cnab_ctrl_cashu"]
    elif "nr_cnab_ctrl" in df_tmp.columns:
        df_tmp["seu_numero_cashu"] = df_tmp["nr_cnab_ctrl"]
    if "nr_cnab_ctrl_admin" in df_tmp.columns:
        df_tmp["seu_numero_admin"] = df_tmp["nr_cnab_ctrl_admin"]

    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item",
        "cd_name_slug",
        "cnpj_emitente_invoice",
        "numero_documento_cashu",
        "numero_documento_admin",
        "seu_numero_cashu",
        "seu_numero_admin",
        "pymt_date",
        "pymt_date_cedent",
        "amt_total",
        "amt_future",
        "amt_paid",
        "amt_pymt",
        "st_billet",
        "tp_liquidation",
    ]
    available_cols = [c for c in display_cols if c in df_tmp.columns]
    df_display = df_tmp[available_cols].copy()
    
    # Rename columns for better readability
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_name_slug": "Corporate",
        "cnpj_emitente_invoice": "CNPJ Emitente (Invoice)",
        "numero_documento_cashu": "Número Documento (CashU)",
        "numero_documento_admin": "Número Documento (Admin)",
        "seu_numero_cashu": "Seu Número (CashU)",
        "seu_numero_admin": "Seu Número (Admin)",
        "pymt_date": "Data Pgto (CashU)",
        "pymt_date_cedent": "Data Pgto (Admin)",
        "amt_total": "Valor Face (CashU)",
        "amt_future": "Valor Face (Admin)",
        "amt_paid": "Valor Pago (CashU)",
        "amt_pymt": "Valor Pago (Admin)",
        "st_billet": "Status (CashU)",
        "tp_liquidation": "Tipo Liquidação",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name="liquidacoes_divergentes.csv",
        mime="text/csv",
        key="download_liq_divergentes"
    )


def _render_cashu_liquidations_sem_admin(df_cashu_sem_admin: pd.DataFrame) -> None:
    """Render section for CashU liquidations not found in Admin."""
    st.subheader("Liquidações CashU sem Match no Administrador")
    
    num_titulos = len(df_cashu_sem_admin)
    valor_face = df_cashu_sem_admin["amt_total"].sum() if not df_cashu_sem_admin.empty else 0
    valor_pago = df_cashu_sem_admin["amt_paid"].sum() if not df_cashu_sem_admin.empty else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("# Liquidações", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Pago", format_currency(valor_pago))
    
    if df_cashu_sem_admin.empty:
        st.success("✓ Todas as liquidações da CashU foram identificadas no Sistema Administrador.")
        return
    
    st.error(f"✗ {num_titulos} liquidações da CashU não encontradas no Sistema do Administrador.")
    
    df_tmp = df_cashu_sem_admin.copy()

    if "nr_gov_id_seller" in df_tmp.columns:
        df_tmp["cnpj_emitente_invoice"] = df_tmp["nr_gov_id_seller"]
    if "nr_cnab_doc" in df_tmp.columns:
        df_tmp["numero_documento_cashu"] = df_tmp["nr_cnab_doc"]
    if "nr_cnab_ctrl" in df_tmp.columns:
        df_tmp["seu_numero_cashu"] = df_tmp["nr_cnab_ctrl"]

    # Select relevant columns for display (no Vencimento / Valor Líquido requested for this page)
    display_cols = [
        "id_inv_fin_item",
        "cd_name_slug",
        "cnpj_emitente_invoice",
        "numero_documento_cashu",
        "seu_numero_cashu",
        "pymt_date",
        "amt_total",
        "amt_paid",
        "st_billet",
    ]
    available_cols = [c for c in display_cols if c in df_tmp.columns]
    df_display = df_tmp[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_name_slug": "Corporate",
        "cnpj_emitente_invoice": "CNPJ Emitente (Invoice)",
        "numero_documento_cashu": "Número Documento (CashU)",
        "seu_numero_cashu": "Seu Número (CashU)",
        "pymt_date": "Data Pagamento",
        "amt_total": "Valor Face",
        "amt_paid": "Valor Pago",
        "st_billet": "Status",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name="liquidacoes_cashu_sem_administrador.csv",
        mime="text/csv",
        key="download_liq_cashu_sem_admin"
    )


def _render_admin_liquidations_sem_cashu(df_admin_sem_cashu: pd.DataFrame) -> None:
    """Render section for Admin liquidations not found in CashU."""
    st.subheader("Liquidações Administrador sem Match na CashU")
    
    num_titulos = len(df_admin_sem_cashu)
    valor_face = df_admin_sem_cashu["amt_future"].sum() if not df_admin_sem_cashu.empty else 0
    valor_pago = df_admin_sem_cashu["amt_pymt"].sum() if not df_admin_sem_cashu.empty else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("# Liquidações", format_number(num_titulos))
    with col2:
        st.metric("Valor Face", format_currency(valor_face))
    with col3:
        st.metric("Valor Pago", format_currency(valor_pago))
    
    if df_admin_sem_cashu.empty:
        st.success("✓ Todas as liquidações do Administrador foram identificadas no Sistema CashU.")
        return
    
    st.error(f"✗ {num_titulos} liquidações do Administrador não encontradas no Sistema CashU.")
    
    df_tmp = df_admin_sem_cashu.copy()

    if "nr_cnab_doc" in df_tmp.columns:
        df_tmp["numero_documento_admin"] = df_tmp["nr_cnab_doc"]
    if "nr_cnab_ctrl" in df_tmp.columns:
        df_tmp["seu_numero_admin"] = df_tmp["nr_cnab_ctrl"]

    # Select relevant columns for display (no Vencimento / Valor Líquido requested for this page)
    display_cols = [
        "id_inv_fin_item",
        "cd_slug_corp",
        "numero_documento_admin",
        "seu_numero_admin",
        "pymt_date_cedent",
        "pymt_info_date",
        "amt_future",
        "amt_pymt",
        "st_inst",
        "tp_liquidation",
    ]
    available_cols = [c for c in display_cols if c in df_tmp.columns]
    df_display = df_tmp[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_slug_corp": "Corporate",
        "numero_documento_admin": "Número Documento (Admin)",
        "seu_numero_admin": "Seu Número (Admin)",
        "pymt_date_cedent": "Data Pgto Cedente",
        "pymt_info_date": "Data Info Pgto",
        "amt_future": "Valor Face",
        "amt_pymt": "Valor Pago",
        "st_inst": "Status",
        "tp_liquidation": "Tipo Liquidação",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="⬇ Exportar CSV",
        data=csv,
        file_name="liquidacoes_administrador_sem_cashu.csv",
        mime="text/csv",
        key="download_liq_admin_sem_cashu"
    )


# =============================================================================
# LIQUIDATIONS - Main Page Render Function
# =============================================================================

def render_conciliacao_liquidações() -> None:
    """Render the 'Conciliação Liquidações' page."""
    # Load all data
    with st.spinner("Carregando dados de liquidações..."):
        data = _load_all_liquidations_data()
    
    # Render sections
    _render_cashu_liquidations_kpis(data["df_cashu"])
    st.divider()
    
    _render_admin_liquidations_kpis(data["df_admin"])
    st.divider()
    
    _render_matched_liquidations(data["titulos_identificados"])
    _render_divergent_liquidations(data["titulos_divergentes"])
    st.divider()
    
    _render_cashu_liquidations_sem_admin(data["df_cashu_sem_admin"])
    st.divider()
    
    _render_admin_liquidations_sem_cashu(data["df_admin_sem_cashu"])
