import pandas as pd
import duckdb
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Design System Tokens
COLORS = {
    "primary": "#f5c344",       # Warm yellow - highlights, table headers
    "secondary": "#903aff",     # Purple - section headers, links
    "accent": "#ff8a00",        # Orange - KPI values, emphasis
    "danger": "#cc3366",        # Pink/red - alerts, warnings
    "bg_dark": "#1a1a1a",
    "bg_mid": "#3b3b3b",
    "bg_light": "#f7f7f7",
    "bg_white": "#FFFFFF",
    "text_primary": "#000000",
    "text_secondary": "#555555",
    "table_header": "#f5c344",
    "table_header_text": "#1a1a1a",
    "table_border": "#e0e0e0",
    "table_hover": "#fff3d6",
    "table_stripe": "#fafafa",
    "table_total": "#f0f0f0",
}


def get_css_styles() -> str:
    """Generate embedded CSS styles following the design system."""
    return f"""
    @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Red Hat Display', sans-serif;
        background-color: {COLORS['bg_light']};
        color: {COLORS['text_primary']};
        line-height: 1.5;
        padding: 32px;
    }}
    
    .container {{
        max-width: 1400px;
        margin: 0 auto;
    }}
    
    /* Header */
    .header {{
        background: linear-gradient(135deg, {COLORS['secondary']} 0%, {COLORS['primary']} 100%);
        color: {COLORS['text_primary']};
        padding: 32px 40px;
        border-radius: 12px;
        margin-bottom: 32px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    .header h1 {{
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 8px;
        color: {COLORS['bg_white']};
    }}
    
    .header .subtitle {{
        font-size: 16px;
        font-weight: 500;
        color: rgba(255,255,255,0.9);
    }}
    
    /* Sections */
    .section {{
        background-color: {COLORS['bg_white']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    
    .section-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 2px solid {COLORS['table_border']};
    }}
    
    .section-header h2 {{
        font-size: 24px;
        font-weight: 700;
        color: {COLORS['secondary']};
    }}
    
    .section-header .badge {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_primary']};
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }}
    
    /* KPI Cards Grid */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }}
    
    .kpi-card {{
        background: linear-gradient(145deg, {COLORS['bg_white']} 0%, {COLORS['bg_light']} 100%);
        border: 1px solid {COLORS['table_border']};
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }}
    
    .kpi-label {{
        font-size: 12px;
        font-weight: 500;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }}
    
    .kpi-value {{
        font-size: 28px;
        font-weight: 700;
        color: {COLORS['accent']};
    }}
    
    .kpi-value.count {{
        color: {COLORS['secondary']};
    }}
    
    .kpi-value.danger {{
        color: {COLORS['danger']};
    }}
    
    .kpi-value.success {{
        color: #2e7d32;
    }}
    
    /* Summary Box */
    .summary-box {{
        background-color: {COLORS['bg_light']};
        border-left: 4px solid {COLORS['secondary']};
        padding: 16px 20px;
        margin-bottom: 20px;
        border-radius: 0 8px 8px 0;
    }}
    
    .summary-box p {{
        margin: 4px 0;
        font-size: 14px;
    }}
    
    .summary-box strong {{
        color: {COLORS['text_primary']};
    }}
    
    /* Data Tables */
    .table-wrapper {{
        margin-bottom: 16px;
    }}
    
    .table-toolbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
        flex-wrap: wrap;
    }}
    
    .table-toolbar .filter-input {{
        flex: 1;
        max-width: 300px;
        padding: 10px 14px;
        border: 1px solid {COLORS['table_border']};
        border-radius: 6px;
        font-family: 'Red Hat Display', sans-serif;
        font-size: 13px;
        transition: border-color 0.2s, box-shadow 0.2s;
    }}
    
    .table-toolbar .filter-input:focus {{
        outline: none;
        border-color: {COLORS['secondary']};
        box-shadow: 0 0 0 3px rgba(144, 58, 255, 0.15);
    }}
    
    .table-toolbar .btn-export {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 10px 16px;
        background-color: {COLORS['secondary']};
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'Red Hat Display', sans-serif;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s, transform 0.1s;
    }}
    
    .table-toolbar .btn-export:hover {{
        background-color: #7b2ee0;
        transform: translateY(-1px);
    }}
    
    .table-toolbar .btn-export:active {{
        transform: translateY(0);
    }}
    
    .table-container {{
        overflow-x: auto;
        overflow-y: auto;
        max-height: 400px;
        border-radius: 8px;
        border: 1px solid {COLORS['table_border']};
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }}
    
    thead th {{
        background-color: {COLORS['table_header']};
        color: {COLORS['table_header_text']};
        font-weight: 600;
        padding: 14px 12px;
        text-align: left;
        white-space: nowrap;
        position: sticky;
        top: 0;
        cursor: pointer;
        user-select: none;
        transition: background-color 0.2s;
    }}
    
    thead th:hover {{
        background-color: #e0ab2d;
    }}
    
    thead th .sort-icon {{
        margin-left: 6px;
        opacity: 0.5;
        font-size: 10px;
    }}
    
    thead th.sort-asc .sort-icon,
    thead th.sort-desc .sort-icon {{
        opacity: 1;
    }}
    
    tbody tr {{
        border-bottom: 1px solid {COLORS['table_border']};
    }}
    
    tbody tr:nth-child(even) {{
        background-color: {COLORS['table_stripe']};
    }}
    
    tbody tr:hover {{
        background-color: {COLORS['table_hover']};
    }}
    
    tbody tr.hidden {{
        display: none;
    }}
    
    tbody td {{
        padding: 12px;
        vertical-align: middle;
    }}
    
    .table-info {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
        color: {COLORS['text_secondary']};
        font-size: 12px;
    }}
    
    /* Empty state */
    .empty-state {{
        text-align: center;
        padding: 40px;
        color: {COLORS['text_secondary']};
    }}
    
    .empty-state .icon {{
        font-size: 48px;
        margin-bottom: 16px;
    }}
    
    /* Alert boxes */
    .alert {{
        padding: 16px 20px;
        border-radius: 8px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .alert.success {{
        background-color: #e8f5e9;
        border: 1px solid #a5d6a7;
        color: #2e7d32;
    }}
    
    .alert.warning {{
        background-color: #fff3e0;
        border: 1px solid #ffcc80;
        color: #e65100;
    }}
    
    .alert.error {{
        background-color: #fce4ec;
        border: 1px solid #f48fb1;
        color: {COLORS['danger']};
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        padding: 24px;
        color: {COLORS['text_secondary']};
        font-size: 12px;
        margin-top: 32px;
    }}
    
    /* Print styles */
    @media print {{
        body {{
            padding: 16px;
        }}
        .section {{
            break-inside: avoid;
        }}
        .kpi-card:hover {{
            transform: none;
            box-shadow: none;
        }}
    }}
    """


def format_currency(value: float) -> str:
    """Format a number as Brazilian currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: int) -> str:
    """Format a number with thousand separators."""
    return f"{value:,}".replace(",", ".")


def build_kpi_card(label: str, value: str, value_class: str = "") -> str:
    """Build an HTML KPI card."""
    class_attr = f"kpi-value {value_class}" if value_class else "kpi-value"
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="{class_attr}">{value}</div>
    </div>
    """


# Global counter for unique table IDs
_table_counter = 0

def build_table(df: pd.DataFrame, table_name: str = "dados") -> str:
    """Build an HTML table from a DataFrame with sorting, filtering, and export."""
    global _table_counter
    _table_counter += 1
    table_id = f"table-{_table_counter}"
    
    if df.empty:
        return """
        <div class="empty-state">
            <div class="icon">✓</div>
            <p>Nenhum registro encontrado</p>
        </div>
        """
    
    # Build header with sort icons
    header_cells = "".join(
        f'<th onclick="sortTable(\'{table_id}\', {i})">{col}<span class="sort-icon">↕</span></th>' 
        for i, col in enumerate(df.columns)
    )
    header_html = f"<tr>{header_cells}</tr>"
    
    # Build rows
    rows_html = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td>{val}</td>" for val in row.values)
        rows_html += f"<tr>{cells}</tr>"
    
    total_rows = len(df)
    
    table_html = f"""
    <div class="table-wrapper">
        <div class="table-toolbar">
            <input type="text" class="filter-input" placeholder="Filtrar registros..." 
                   onkeyup="filterTable('{table_id}', this.value)" id="filter-{table_id}">
            <button class="btn-export" onclick="exportTableToCSV('{table_id}', '{table_name}.csv')">
                ⬇ Exportar CSV
            </button>
        </div>
        <div class="table-container">
            <table id="{table_id}">
                <thead>{header_html}</thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        <div class="table-info">
            <span id="count-{table_id}">{total_rows} registros</span>
        </div>
    </div>
    """
    
    return table_html


def build_section(title: str, badge: str = None, content: str = "") -> str:
    """Build an HTML section."""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    return f"""
    <div class="section">
        <div class="section-header">
            <h2>{title}</h2>
            {badge_html}
        </div>
        {content}
    </div>
    """


def build_alert(message: str, alert_type: str = "success") -> str:
    """Build an alert box."""
    icons = {"success": "✓", "warning": "⚠", "error": "✗"}
    icon = icons.get(alert_type, "ℹ")
    return f"""
    <div class="alert {alert_type}">
        <span>{icon}</span>
        <span>{message}</span>
    </div>
    """


def generate_report(report_date_start: str = None, report_date_end: str = None) -> str:
    """Generate the HTML report for the specified date."""
    
    if report_date_start is None:
        report_date_start = '2026-01-01'
    if report_date_end is None:
        report_date_end = '2026-01-31'
    
    # Connect to database
    con = duckdb.connect(database=os.getenv("DUCKDB_PATH"))
    
    # Query 1: CashU Invoice Financing
    df_cashu = con.query(f"""
       SELECT
    	anticipated_at::date anticipated_at,
    	c.name_slug,
    	p2.nm_legal nm_seller,
    	p1.nm_legal nm_buyer,
    	f.id_inv_fin_item,
    	f.id_recv,
    	f.id_inv_fin,
    	f.id_ord_inst,
    	f.id_bnk_resale,
    	f.nr_cnab_ctrl,
    	f.nr_cnab_doc,
    	f.due_date::date due_date,
    	f.issue_date::Date issue_date,
    	f.amt_total,
    	f.amt_net,
        f.amt_post_fees_pre_mdr,
    	f.qty_credit_days,
    	f.tp_rate,
    	f.is_antcp,
    	f.is_resale
       from bronze.stg_cashu_app__invoice_financing_items f
       left join bronze.stg_cashu_app__order_installments oi on f.id_ord_inst = oi.id_ord_inst 
       left join bronze.stg_cashu_app__orders o on o.id_ord = oi.id_ord 
       left join master_data.dim_parties p1 on p1.nr_gov_id = o.nr_doc_buyer 
       left join master_data.dim_parties p2 on p2.nr_gov_id = o.nr_doc_seller 
       left join bronze.raw_cashu_app__corporates c on c.id = o.id_corp 
       where is_antcp and anticipated_at::date BETWEEN '{report_date_start}' and '{report_date_end}'
       order by anticipated_at, name_slug, nm_seller 
    """).df()
    
    # Query 2: Fund Administrator
    df_admin = con.query(f"""
        SELECT 
            id_billet,
            id_ord_inst,
            nr_cnab_ctrl,
            nr_cnab_doc,
            ref_date::date anticipation_date,
            due_date::date due_date,
            cd_slug_oper slug_fund,
            nm_debtor nm_seller,
            nm_cedent nm_buyer,
            tp_recv tp_recv,
            amt_acq,
            amt_future,
            has_coobl
        FROM fact_data.fact_fund_acquisitions
        WHERE ref_date::date between '{report_date_start}' and '{report_date_end}'
    """).df()
    
    # Query 3: Identified titles (matching between systems)
    titulos_identificados = con.query(f"""
        SELECT
            *
        FROM df_cashu t1
        INNER JOIN df_admin t2 ON t1.id_ord_inst = t2.id_ord_inst
    """).df()
    
    # Query 4: Mismatched values
    titulos_divergentes = con.query(f"""
        SELECT
            *
        FROM titulos_identificados
        WHERE amt_future != amt_total OR amt_acq != amt_net
    """).df()
    
    # Query 5: Admin titles not in CashU
    df_admin_sem_cashu = df_admin.loc[~df_admin.id_ord_inst.isin(df_cashu.id_ord_inst)]

    # Query 6: CashU titles not in Admin
    df_cashu_sem_admin = df_cashu.loc[~df_cashu.id_ord_inst.isin(df_admin.id_ord_inst)]
    
    # Calculate differences
    diff_face = titulos_identificados['amt_future'].sum() - titulos_identificados['amt_total'].sum()
    diff_antecipado = titulos_identificados['amt_acq'].sum() - titulos_identificados['amt_net'].sum()
    
    # Build HTML content
    html_parts = []
    
    # Section 1: Sistema CashU Invoice Financing
    cashu_kpis = f"""
    <div class="kpi-grid">
        {build_kpi_card("# Títulos", format_number(len(df_cashu)), "count")}
        {build_kpi_card("Valor Face", format_currency(df_cashu['amt_total'].sum()))}
        {build_kpi_card("Valor Antecipado", format_currency(df_cashu['amt_net'].sum()))}
        {build_kpi_card("Valor Após Taxa sem MDR", format_currency(df_cashu['amt_post_fees_pre_mdr'].sum()))}
    </div>
    """
    html_parts.append(build_section("Sistema CashU Invoice Financing", f"{len(df_cashu)} títulos", cashu_kpis))
    
    # Section 2: Sistema Administrador do Fundo
    admin_kpis = f"""
    <div class="kpi-grid">
        {build_kpi_card("# Títulos", format_number(len(df_admin)), "count")}
        {build_kpi_card("Valor Face", format_currency(df_admin['amt_future'].sum()))}
        {build_kpi_card("Valor Antecipado", format_currency(df_admin['amt_acq'].sum()))}
    </div>
    """
    html_parts.append(build_section("Sistema Administrador do Fundo", f"{len(df_admin)} títulos", admin_kpis))
    
    # Section 3: Títulos Identificados
    identificados_content = f"""
    <div class="kpi-grid">
        {build_kpi_card("# Títulos Identificados", format_number(len(titulos_identificados)), "count")}
        {build_kpi_card("Diferença Valor Face", format_currency(diff_face), "danger" if abs(diff_face) > 0.01 else "success")}
        {build_kpi_card("Diferença Valor Antecipado", format_currency(diff_antecipado), "danger" if abs(diff_antecipado) > 0.01 else "success")}
    </div>
    """
    
    if len(titulos_divergentes) > 0:
        identificados_content += f"""
        <h3 style="font-size: 16px; font-weight: 600; margin: 20px 0 12px; color: {COLORS['text_primary']};">
            Títulos com Valores Divergentes ({len(titulos_divergentes)} registros)
        </h3>
        {build_table(titulos_divergentes, "titulos_divergentes")}
        """
    else:
        identificados_content += build_alert("Todos os títulos identificados possuem valores consistentes entre os sistemas.", "success")
    
    html_parts.append(build_section("Títulos Identificados", f"{len(titulos_identificados)} encontrados", identificados_content))
    
    # Section 4: Títulos no CashU sem Administrador
    sem_admin_content = f"""
    <div class="kpi-grid">
        {build_kpi_card("# Títulos", format_number(len(df_cashu_sem_admin)), "danger" if len(df_cashu_sem_admin) > 0 else "success")}
        {build_kpi_card("Valor Face", format_currency(df_cashu_sem_admin['amt_total'].sum() if len(df_cashu_sem_admin) > 0 else 0))}
    </div>
    """
    
    if len(df_cashu_sem_admin) > 0:
        sem_admin_content += build_alert(f"{len(df_cashu_sem_admin)} títulos da CashU não encontrados no Sistema do Administrador.", "error")
        sem_admin_content += build_table(df_cashu_sem_admin, "cashu_sem_administrador")
    else:
        sem_admin_content += build_alert("Todos os títulos da CashU foram identificados no Sistema Administrador.", "success")
    
    html_parts.append(build_section("Títulos CashU sem Match no Administrador", None, sem_admin_content))
    
    # Section 5: Títulos no Administrador sem CashU
    sem_cashu_content = f"""
    <div class="kpi-grid">
        {build_kpi_card("# Títulos", format_number(len(df_admin_sem_cashu)), "danger" if len(df_admin_sem_cashu) > 0 else "success")}
        {build_kpi_card("Valor Face", format_currency(df_admin_sem_cashu['amt_future'].sum() if len(df_admin_sem_cashu) > 0 else 0))}
    </div>
    """
    
    if len(df_admin_sem_cashu) > 0:
        sem_cashu_content += build_alert(f"{len(df_admin_sem_cashu)} títulos do Administrador não encontrados no Sistema CashU.", "error")
        sem_cashu_content += build_table(df_admin_sem_cashu, "administrador_sem_cashu")
    else:
        sem_cashu_content += build_alert("Todos os títulos do Administrador foram identificados no Sistema CashU.", "success")
    
    html_parts.append(build_section("Títulos Administrador sem Match na CashU", None, sem_cashu_content))
    
    # Build full HTML document
    sections_html = "\n".join(html_parts)
    generated_at = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório CashU - {report_date_start} a {report_date_end}</title>
    <style>
        {get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Relatório de Conciliação CashU</h1>
            <div class="subtitle">Data do Relatório: {report_date_start} a {report_date_end} | Gerado em: {generated_at}</div>
        </header>
        
        {sections_html}
        
        <footer class="footer">
            <p>CashU | Cacau Show - Relatório de Conciliação de Invoice Financing</p>
            <p>Gerado automaticamente em {generated_at}</p>
        </footer>
    </div>
    
    <script>
        // Sort state for each table
        const sortState = {{}};
        
        function sortTable(tableId, columnIndex) {{
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headers = table.querySelectorAll('thead th');
            
            // Determine sort direction
            const key = `${{tableId}}-${{columnIndex}}`;
            sortState[key] = sortState[key] === 'asc' ? 'desc' : 'asc';
            const isAsc = sortState[key] === 'asc';
            
            // Update header classes
            headers.forEach((th, i) => {{
                th.classList.remove('sort-asc', 'sort-desc');
                if (i === columnIndex) {{
                    th.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
                    th.querySelector('.sort-icon').textContent = isAsc ? '↑' : '↓';
                }} else {{
                    th.querySelector('.sort-icon').textContent = '↕';
                }}
            }});
            
            // Sort rows
            rows.sort((a, b) => {{
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();
                
                // Try numeric comparison
                const aNum = parseFloat(aVal.replace(/[R$\\s.,]/g, '').replace(',', '.'));
                const bNum = parseFloat(bVal.replace(/[R$\\s.,]/g, '').replace(',', '.'));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return isAsc ? aNum - bNum : bNum - aNum;
                }}
                
                // String comparison
                return isAsc ? aVal.localeCompare(bVal, 'pt-BR') : bVal.localeCompare(aVal, 'pt-BR');
            }});
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }}
        
        function filterTable(tableId, searchTerm) {{
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tbody tr');
            const term = searchTerm.toLowerCase();
            let visibleCount = 0;
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                const isVisible = text.includes(term);
                row.classList.toggle('hidden', !isVisible);
                if (isVisible) visibleCount++;
            }});
            
            // Update count
            const countEl = document.getElementById(`count-${{tableId}}`);
            if (countEl) {{
                const total = rows.length;
                countEl.textContent = searchTerm ? `${{visibleCount}} de ${{total}} registros` : `${{total}} registros`;
            }}
        }}
        
        function exportTableToCSV(tableId, filename) {{
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tr:not(.hidden)');
            const csv = [];
            
            rows.forEach(row => {{
                const cols = row.querySelectorAll('th, td');
                const rowData = [];
                cols.forEach(col => {{
                    // Clean the text and handle the sort icon in headers
                    let text = col.textContent.replace(/[↕↑↓]/g, '').trim();
                    // Escape quotes and wrap in quotes if contains separator
                    if (text.includes(';') || text.includes('"') || text.includes('\\n')) {{
                        text = '"' + text.replace(/"/g, '""') + '"';
                    }}
                    rowData.push(text);
                }});
                csv.push(rowData.join(';'));
            }});
            
            // Add BOM for Excel compatibility with UTF-8
            const BOM = '\\uFEFF';
            const csvContent = BOM + csv.join('\\n');
            
            // Create download link
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Main function to generate and save the report."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerar relatório HTML de conciliação CashU')
    parser.add_argument('--date_start', '-ds', type=str, default='2026-01-01',
                        help='Data de início do relatório no formato YYYY-MM-DD (default: 2026-01-01)')
    parser.add_argument('--date_end', '-de', type=str, default='2026-01-31',
                        help='Data de fim do relatório no formato YYYY-MM-DD (default: 2026-01-31)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Caminho do arquivo de saída (default: report_YYYY-MM-DD_YYYY-MM-DD.html)')
    
    args = parser.parse_args()
    
    report_date_start = args.date_start
    report_date_end = args.date_end
    output_file = args.output or f"report_{report_date_start}_{report_date_end}.html"
    
    print(f"Gerando relatório para {report_date_start} a {report_date_end}...")
    
    html_content = generate_report(report_date_start, report_date_end)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Relatório salvo em: {output_file}")
    print(f"Abra o arquivo em um navegador para visualizar.")


if __name__ == "__main__":
    main()
