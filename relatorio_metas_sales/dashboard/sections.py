"""
Dashboard Sections - Relatório Metas Sales CashU

Section render functions for the Sales Goals dashboard.
"""
import streamlit as st
import pandas as pd

# Shared imports (DO NOT MODIFY these imports)
from shared.db import run_query
from shared.styles import COLORS

# Dashboard-specific imports
from . import queries
from .dashboard_config import MONTH_NAMES


# =============================================================================
# Helper Functions
# =============================================================================

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase for consistency."""
    df.columns = df.columns.str.lower()
    return df


def format_currency(value: float) -> str:
    """Format a number as Brazilian currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: int) -> str:
    """Format a number with thousand separators."""
    return f"{value:,}".replace(",", ".")


def format_percent(value: float) -> str:
    """Format a number as percentage."""
    if pd.isna(value):
        return "-"
    return f"{value:.1%}".replace(".", ",")


def _get_month_year() -> tuple[int, int]:
    """Get the selected month and year from session state."""
    month = st.session_state.get("selected_month", 1)
    year = st.session_state.get("selected_year", 2026)
    return month, year


def _get_date_range() -> tuple[str, str]:
    """Get the date range from session state."""
    date_start = st.session_state.get("date_start")
    date_end = st.session_state.get("date_end")
    return str(date_start), str(date_end)


# =============================================================================
# METAS SALES - Data Loading Functions
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def _load_goals_banker_data(month: int, year: int) -> pd.DataFrame:
    """Load goals data aggregated by banker."""
    sql = queries.get_goals_banker_monthly_query(str(month), str(year))
    return _normalize_columns(run_query(sql))


@st.cache_data(ttl=300, show_spinner=False)
def _load_goals_slug_data(month: int, year: int) -> pd.DataFrame:
    """Load goals data by corporate slug."""
    sql = queries.get_goals_slug_monthly_query(str(month), str(year))
    return _normalize_columns(run_query(sql))


# =============================================================================
# METAS SALES - Table Formatting Functions
# =============================================================================

def _format_banker_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format the banker dataframe for display."""
    if df.empty:
        return df
    
    # Select and rename columns for display
    display_cols = {
        "nm_banker": "Banker",
        "amt_cedent": "# Cedentes",
        "amt_total": "Volume Total (R$)",
        "amt_goal": "Meta (R$)",
        "gap_oport": "Gap/Oportunidade (R$)",
        "perc_goal": "% Meta",
        "amt_total_per_cedent": "Volume/Cedente (R$)",
        "amt_fee_consult_estimated": "Fee Consultoria Est. (R$)",
        "amt_fee_mdr": "Fee MDR (R$)",
    }
    
    # Filter available columns
    available_cols = [c for c in display_cols.keys() if c in df.columns]
    df_display = df[available_cols].copy()
    df_display = df_display.rename(columns={k: v for k, v in display_cols.items() if k in df_display.columns})
    
    return df_display


def _format_slug_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format the slug dataframe for display."""
    if df.empty:
        return df
    
    # Select and rename columns for display
    display_cols = {
        "nm_banker": "Banker",
        "cd_name_slug": "Corporate (Slug)",
        "amt_inst": "# Títulos",
        "amt_total": "Volume Total (R$)",
        "amt_net": "Valor Líquido (R$)",
        "amt_discount": "Desconto (R$)",
        "rate_discount": "Taxa Desconto",
        "avg_due_days": "Prazo Médio (dias)",
        "amt_goal": "Meta (R$)",
    }
    
    # Filter available columns
    available_cols = [c for c in display_cols.keys() if c in df.columns]
    df_display = df[available_cols].copy()
    df_display = df_display.rename(columns={k: v for k, v in display_cols.items() if k in df_display.columns})
    
    return df_display


def _render_styled_table(
    df: pd.DataFrame,
    table_id: str = "styled-table",
    column_formats: dict | None = None,
) -> None:
    """
    Render a styled HTML table following the design system.
    
    Args:
        df: DataFrame to render
        table_id: Unique ID for the table
        column_formats: Dict mapping column names to format types: 
                        'currency', 'number', 'percent', 'days', 'text'
    """
    import streamlit.components.v1 as components
    from shared.styles import get_table_styles
    
    if df.empty:
        st.info("Nenhum dado encontrado.")
        return
    
    styles = get_table_styles()
    
    # Default column formats
    if column_formats is None:
        column_formats = {}
    
    # Build HTML table
    html = f'''
    <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    html, body {{ margin: 0; padding: 0; background: transparent; }}
    
    .table-container {{
        width: 100%;
        overflow-x: auto;
        scrollbar-width: thin;
        margin-bottom: 16px;
    }}
    .table-container::-webkit-scrollbar {{
        height: 6px;
    }}
    .table-container::-webkit-scrollbar-thumb {{
        background-color: rgba(0, 0, 0, 0.25);
        border-radius: 999px;
    }}
    
    table.styled-table {{
        border-collapse: collapse;
        width: 100%;
        font-family: 'Red Hat Display', sans-serif;
        font-size: 12px;
        margin: 0;
    }}
    
    table.styled-table th {{
        background-color: {styles['header_bg']};
        color: {styles['header_text']};
        font-weight: 600;
        text-align: center;
        padding: 10px 12px;
        border: none;
        border-bottom: 3px solid #000000;
        white-space: nowrap;
        cursor: pointer;
        user-select: none;
        position: relative;
    }}
    
    table.styled-table th:hover {{
        background-color: #e6b03a;
    }}
    
    table.styled-table th::after {{
        content: '⇅';
        position: absolute;
        right: 4px;
        top: 50%;
        transform: translateY(-50%);
        opacity: 0.4;
        font-size: 10px;
    }}
    
    table.styled-table th.asc::after {{ content: '▲'; opacity: 1; }}
    table.styled-table th.desc::after {{ content: '▼'; opacity: 1; }}
    
    table.styled-table td {{
        padding: 8px 12px;
        border: none;
        white-space: nowrap;
    }}
    
    table.styled-table td.text-col {{
        text-align: left;
        font-weight: 500;
    }}
    
    table.styled-table td.number-col {{
        text-align: right;
    }}
    
    table.styled-table tbody tr:nth-child(even) {{
        background-color: {styles['stripe']};
    }}
    
    table.styled-table tbody tr:hover {{
        background-color: {styles['hover']};
        transition: background-color 0.2s ease;
    }}
    
    /* Total row styling */
    table.styled-table tfoot td {{
        background-color: {styles['total_bg']} !important;
        color: {styles['total_text']} !important;
        font-weight: 700;
        border-top: 3px solid #000000;
        padding: 10px 12px;
    }}
    </style>
    '''
    
    html += f'<div class="table-container"><table class="styled-table" id="{table_id}">'
    
    # Header row
    html += '<thead><tr>'
    for i, col in enumerate(df.columns):
        html += f'<th data-col="{i}">{col}</th>'
    html += '</tr></thead>'
    
    # Body rows
    html += '<tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            fmt = column_formats.get(col, 'text')
            
            # Format value based on type
            if pd.isna(val):
                display_val = "-"
                sort_val = ""
            elif fmt == 'currency':
                try:
                    num_val = float(val)
                    # Format with thousands and decimal separators for pt-BR
                    display_val = f"R$ {num_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    sort_val = str(num_val)
                except:
                    display_val = str(val)
                    sort_val = display_val
            elif fmt == 'number':
                try:
                    num_val = float(val)
                    # Format integer with thousands separator for pt-BR
                    display_val = f"{num_val:,.0f}".replace(",", ".")
                    sort_val = str(num_val)
                except:
                    display_val = str(val)
                    sort_val = display_val
            elif fmt == 'percent':
                try:
                    num_val = float(val)
                    # Convert ratio to percentage (0.85 -> 85%)
                    # Multiply by 100 and format with pt-BR separators
                    pct_val = num_val * 100
                    # Format with thousands separator and 1 decimal, then convert to pt-BR
                    display_val = f"{pct_val:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
                    sort_val = str(num_val)
                except:
                    display_val = str(val)
                    sort_val = display_val
            elif fmt == 'days':
                try:
                    num_val = float(val)
                    # Format with 1 decimal and pt-BR separator
                    display_val = f"{num_val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    sort_val = str(num_val)
                except:
                    display_val = str(val)
                    sort_val = display_val
            else:
                display_val = str(val) if val else "-"
                sort_val = display_val
            
            # Determine cell class
            cell_class = "text-col" if fmt == 'text' else "number-col"
            
            html += f'<td class="{cell_class}" data-sort="{sort_val}">{display_val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    
    # Add sorting JavaScript
    html += f'''
    <script>
    (function() {{
        var table = document.getElementById('{table_id}');
        if (!table) return;
        
        var headers = table.querySelectorAll('th');
        var tbody = table.querySelector('tbody');
        
        headers.forEach(function(header) {{
            header.addEventListener('click', function() {{
                var colIndex = parseInt(this.getAttribute('data-col'));
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var isAsc = this.classList.contains('asc');
                
                headers.forEach(function(h) {{ h.classList.remove('asc', 'desc'); }});
                
                if (isAsc) {{
                    this.classList.add('desc');
                }} else {{
                    this.classList.add('asc');
                }}
                var ascending = this.classList.contains('asc');
                
                rows.sort(function(a, b) {{
                    var aCell = a.cells[colIndex];
                    var bCell = b.cells[colIndex];
                    var aVal = aCell ? (aCell.getAttribute('data-sort') || aCell.textContent) : '';
                    var bVal = bCell ? (bCell.getAttribute('data-sort') || bCell.textContent) : '';
                    
                    var aNum = parseFloat(aVal.replace(/,/g, '.'));
                    var bNum = parseFloat(bVal.replace(/,/g, '.'));
                    
                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return ascending ? aNum - bNum : bNum - aNum;
                    }}
                    return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }});
                
                rows.forEach(function(row) {{ tbody.appendChild(row); }});
            }});
        }});
    }})();
    </script>'''
    
    # Calculate iframe height
    row_height = 36
    header_height = 44
    padding = 24
    iframe_height = header_height + (len(df) * row_height) + padding
    
    components.html(html, height=int(iframe_height), scrolling=False)


# =============================================================================
# METAS SALES - Main Page Render Function
# =============================================================================

def render_metas_sales() -> None:
    """Render the 'Metas Sales' page with tables in a grid layout."""
    month, year = _get_month_year()
    month_name = MONTH_NAMES[month - 1]
    
    st.subheader(f"Período: {month_name} / {year}")
    
    # Load all data
    with st.spinner("Carregando dados de metas..."):
        df_banker = _load_goals_banker_data(month, year)
        df_slug = _load_goals_slug_data(month, year)
    
    # ==========================================================================
    # ROW 1: Goals by Banker (Summary Table)
    # ==========================================================================
    st.markdown("### Metas por Banker")
    
    if df_banker.empty:
        st.info("Nenhum dado encontrado para o período selecionado.")
    else:
        df_banker_display = _format_banker_dataframe(df_banker)
        
        # Column format mapping for styled table
        banker_formats = {
            "Banker": "text",
            "# Cedentes": "number",
            "Volume Total (R$)": "currency",
            "Meta (R$)": "currency",
            "Gap/Oportunidade (R$)": "currency",
            "% Meta": "percent",
            "Volume/Cedente (R$)": "currency",
            "Fee Consultoria Est. (R$)": "currency",
            "Fee MDR (R$)": "currency",
        }
        
        _render_styled_table(
            df_banker_display,
            table_id="banker-table",
            column_formats=banker_formats,
        )
        
        # Download button for banker data
        csv_banker = df_banker_display.to_csv(index=False, sep=";", decimal=",")
        st.download_button(
            label="⬇ Exportar Banker CSV",
            data=csv_banker,
            file_name=f"metas_banker_{year}_{month:02d}.csv",
            mime="text/csv",
            key="download_banker"
        )
    
    st.divider()
    
    # ==========================================================================
    # ROW 2: Goals by Corporate Slug (Detailed Table)
    # ==========================================================================
    st.markdown("### Metas por Corporate (Slug)")
    
    if df_slug.empty:
        st.info("Nenhum dado encontrado para o período selecionado.")
    else:
        df_slug_display = _format_slug_dataframe(df_slug)
        
        # Column format mapping for styled table
        slug_formats = {
            "Banker": "text",
            "Corporate (Slug)": "text",
            "# Títulos": "number",
            "Volume Total (R$)": "currency",
            "Valor Líquido (R$)": "currency",
            "Desconto (R$)": "currency",
            "Taxa Desconto": "percent",
            "Prazo Médio (dias)": "days",
            "Meta (R$)": "currency",
        }
        
        _render_styled_table(
            df_slug_display,
            table_id="slug-table",
            column_formats=slug_formats,
        )
        
        # Download button for slug data
        csv_slug = df_slug_display.to_csv(index=False, sep=";", decimal=",")
        st.download_button(
            label="⬇ Exportar Corporate CSV",
            data=csv_slug,
            file_name=f"metas_corporate_{year}_{month:02d}.csv",
            mime="text/csv",
            key="download_slug"
        )


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
    
    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item", "cd_name_slug", "due_date",
        "amt_total", "amt_future", "amt_net", "amt_acq"
    ]
    available_cols = [c for c in display_cols if c in titulos_divergentes.columns]
    df_display = titulos_divergentes[available_cols].copy()
    
    # Rename columns for better readability
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_name_slug": "Corporate",
        "due_date": "Vencimento",
        "amt_total": "Valor Face (CashU)",
        "amt_future": "Valor Face (Admin)",
        "amt_net": "Valor Líquido (CashU)",
        "amt_acq": "Valor Líquido (Admin)",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",")
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
    
    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item", "anticipated_at", "cd_name_slug",
        "due_date", "amt_total", "amt_net"
    ]
    available_cols = [c for c in display_cols if c in df_cashu_sem_admin.columns]
    df_display = df_cashu_sem_admin[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "anticipated_at": "Data Antecipação",
        "cd_name_slug": "Corporate",
        "due_date": "Vencimento",
        "amt_total": "Valor Face",
        "amt_net": "Valor Líquido",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",")
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
    
    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item", "ref_date", "cd_slug_oper", "nm_debtor", "nm_cedent",
        "due_date", "amt_future", "amt_acq"
    ]
    available_cols = [c for c in display_cols if c in df_admin_sem_cashu.columns]
    df_display = df_admin_sem_cashu[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "ref_date": "Data Aquisição",
        "cd_slug_oper": "Operação",
        "nm_debtor": "Devedor",
        "nm_cedent": "Cedente",
        "due_date": "Vencimento",
        "amt_future": "Valor Face",
        "amt_acq": "Valor Líquido",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",")
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
    
    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item", "cd_name_slug", "pymt_date", "pymt_date_cedent",
        "amt_total", "amt_future", "amt_paid", "amt_pymt", "st_billet", "tp_liquidation"
    ]
    available_cols = [c for c in display_cols if c in titulos_divergentes.columns]
    df_display = titulos_divergentes[available_cols].copy()
    
    # Rename columns for better readability
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_name_slug": "Corporate",
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
    csv = df_display.to_csv(index=False, sep=";", decimal=",")
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
    
    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item", "cd_name_slug", "pymt_date", "due_date",
        "amt_total", "amt_paid", "st_billet"
    ]
    available_cols = [c for c in display_cols if c in df_cashu_sem_admin.columns]
    df_display = df_cashu_sem_admin[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_name_slug": "Corporate",
        "pymt_date": "Data Pagamento",
        "due_date": "Vencimento",
        "amt_total": "Valor Face",
        "amt_paid": "Valor Pago",
        "st_billet": "Status",
    }
    df_display = df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns})
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # CSV download
    csv = df_display.to_csv(index=False, sep=";", decimal=",")
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
    
    # Select relevant columns for display
    display_cols = [
        "id_inv_fin_item", "cd_slug_corp", "pymt_date_cedent", "pymt_info_date",
        "amt_future", "amt_pymt", "st_inst", "tp_liquidation"
    ]
    available_cols = [c for c in display_cols if c in df_admin_sem_cashu.columns]
    df_display = df_admin_sem_cashu[available_cols].copy()
    
    # Rename columns
    rename_map = {
        "id_inv_fin_item": "ID Invoice Financing Item",
        "cd_slug_corp": "Corporate",
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
    csv = df_display.to_csv(index=False, sep=";", decimal=",")
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
