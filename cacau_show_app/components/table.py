from collections import OrderedDict
import pandas as pd
import streamlit.components.v1 as components
import sys
import os

# Add parent directory to path to import styles
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import get_table_styles


def render_table_with_merged_headers(
    df_pivot: pd.DataFrame,
    index_label: str = "Forma de Pagamento",
    show_percent: bool = True,
    table_id: str = "data-table",
    column_width_overrides: dict | None = None,
    frame_width: int | None = None,  # pixel width of the iframe; None = auto
    container_css_width: str | None = None,  # CSS width for inner container, e.g. '280px' or '60%'
) -> None:
    """Render a DataFrame with 2 or 3-level MultiIndex columns with merged headers and interactive sorting."""
    # Separate "Total" row if it exists (will be rendered in tfoot)
    total_row = None
    if 'Total' in df_pivot.index:
        total_row = df_pivot.loc['Total']
        df_pivot = df_pivot.drop('Total')
    
    # Detect number of levels
    num_levels = df_pivot.columns.nlevels
    
    if num_levels == 2:
        level_0 = [col[0] for col in df_pivot.columns]
        level_1 = [col[1] for col in df_pivot.columns]
        level_2 = None
    elif num_levels == 3:
        level_0 = [col[0] for col in df_pivot.columns]
        level_1 = [col[1] for col in df_pivot.columns]
        level_2 = [col[2] for col in df_pivot.columns]
    else:
        # Fallback for single level
        level_0 = list(df_pivot.columns)
        level_1 = None
        level_2 = None
    
    # Get theme colors
    styles = get_table_styles()
    container_class = "table-scroll-container"
    
    # Build HTML table with inline sorting (no external CDN dependencies for Snowflake compatibility)
    html = f'''
    <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    html, body {{ margin: 0; padding: 0 12px 0 0; background: transparent; }}
    /* Sorting indicators */
    th.sortable {{ cursor: pointer; user-select: none; position: relative; padding-right: 20px !important; }}
    th.sortable:hover {{ background-color: #e6b03a !important; }}
    th.sortable::after {{ 
        content: '⇅'; 
        position: absolute; 
        right: 4px; 
        top: 50%; 
        transform: translateY(-50%); 
        opacity: 0.4; 
        font-size: 10px;
    }}
    th.sortable.asc::after {{ content: '▲'; opacity: 1; }}
    th.sortable.desc::after {{ content: '▼'; opacity: 1; }}
    .table-scroll-container {{
        width: 100%;
        overflow-x: hidden;
        scrollbar-width: thin;
        margin-bottom: 16px;
    }}
    .table-scroll-container::-webkit-scrollbar {{
        height: 6px;
    }}
    .table-scroll-container::-webkit-scrollbar-thumb {{
        background-color: rgba(0, 0, 0, 0.25);
        border-radius: 999px;
    }}
    table.merged-header {{
        border-collapse: collapse;
        width: 100%;
        min-width: 0;
        table-layout: fixed;
        font-family: 'Red Hat Display', sans-serif;
        font-size: 12px; /* compact font size */
        margin: 0;
    }}
    table.merged-header, table.merged-header th, table.merged-header td {{ box-sizing: border-box; }}
    table.merged-header th {{
        border: none !important; /* remove all cell lines */
        padding: 8px; /* compact cell padding */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    table.merged-header td {{
        border: none !important; /* remove all cell lines */
        padding: 8px 12px 8px 8px; /* extra right padding to avoid clipping */
        text-align: right; /* right-align numeric values */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    table.merged-header th:first-child,
    table.merged-header td:first-child {{
        width: 180px;
        white-space: normal;
        overflow: visible;
        text-overflow: unset;
        word-break: break-word;
    }}
    @media (max-width: 1200px) {{
        table.merged-header th:first-child,
        table.merged-header td:first-child {{
            width: 140px;
        }}
    }}
    @media (max-width: 1200px) {{
        table.merged-header th,
        table.merged-header td {{
            font-size: 11px;
            padding: 6px 8px;
        }}
    }}
    /* bold separator under header */
    table.merged-header thead tr:last-child th {{
        border-bottom: 3px solid #000000 !important;
    }}
    /* ensure the left-most header with rowspan gets bottom separator and vertical line */
    table.merged-header thead th[rowspan] {{
        border-bottom: 3px solid #000000 !important;
        border-right: 2px solid #000000 !important;
    }}
    /* remove any horizontal line between header levels */
    table.merged-header thead tr:not(:last-child) th {{
        border-bottom: none !important;
    }}
    table.merged-header thead tr:first-child th + th {{
        border-left: 2px solid #000000 !important;
    }}
    /* avoid double-thick line next to the rowspan header */
    table.merged-header thead tr:first-child th[rowspan] + th {{
        border-left: none !important;
    }}
    /* remove any right-edge vertical line on the last topmost header cell */
    table.merged-header thead tr:first-child th:last-child {{
        border-right: none !important;
    }}
    /* extend leftmost vertical line through second header row */
    table.merged-header thead tr:nth-child(2) th:first-child {{
        border-left: 2px solid #000000 !important;
    }}
    /* extend leftmost vertical line through third header row (if present) */
    table.merged-header thead tr:nth-child(3) th:first-child {{
        border-left: 2px solid #000000 !important;
    }}
    /* vertical separators continue for lower header rows at group boundaries */
    table.merged-header thead th.group-start {{
        border-left: 2px solid #000000 !important;
    }}
    /* enforce continuity explicitly on 2nd and 3rd header rows */
    table.merged-header thead tr:nth-child(2) th.group-start,
    table.merged-header thead tr:nth-child(3) th.group-start {{
        border-left: 2px solid #000000 !important;
    }}
    /* second header row: remove all verticals, then re-add only at topmost boundaries and far left */
    table.merged-header thead tr:nth-child(2) th {{
        border-left: none !important;
        border-right: none !important;
    }}
    table.merged-header thead tr:nth-child(2) th.group-start,
    table.merged-header thead tr:nth-child(2) th:first-child {{
        border-left: 2px solid #000000 !important;
    }}
    /* no vertical separators on the bottom-most header row */
    table.merged-header thead tr:last-child th {{
        border-left: none !important;
        border-right: none !important;
    }}
    /* bold separator above Total row */
    table.merged-header tfoot tr:first-child td {{
        border-top: 3px solid #000000 !important;
    }}
    /* remove DataTables default bottom border */
    table.merged-header.dataTable.no-footer {{
        border-bottom: none !important;
    }}
    table.merged-header th {{
        background-color: {styles['header_bg']};
        color: {styles['header_text']};
        font-weight: 600;
        text-align: center;
    }}
    
    table.merged-header th:first-child, table.merged-header td:first-child {{
        padding-left: 12px; /* keep inner spacing for first column */
    }}
    table.merged-header tbody tr:nth-child(even) {{
        background-color: {styles['stripe']};
    }}
    /* ensure the header separator runs across full table width */
    table.merged-header tbody tr:first-child td {{
        border-top: 3px solid #000000 !important;
    }}
    table.merged-header tbody tr:hover {{
        background-color: {styles['hover']};
        transition: background-color 0.2s ease;
    }}
    table.merged-header tfoot td {{
        background-color: {styles['total_bg']} !important;
        color: {styles['total_text']} !important;
        font-weight: 700;
    }}
    </style>
    '''
    # Optional per-table column width overrides (1-based column indices)
    if column_width_overrides:
        html += "<style>"
        for idx, width in column_width_overrides.items():
            try:
                idx_int = int(idx)
            except Exception:
                continue
            html += f'#{table_id} th:nth-child({idx_int}), #{table_id} td:nth-child({idx_int}) {{ width: {width}; }}'
        html += "</style>"
    # Optional container width styling
    container_style_attr = f' style="width: {container_css_width};"' if container_css_width else ''
    html += f'<div class="{container_class}"{container_style_attr}>' 
    
    # Precompute column sums for percent-of-column totals (exclude Total row)
    numeric_df = df_pivot.apply(pd.to_numeric, errors='coerce')
    col_sums = numeric_df.sum(axis=0, numeric_only=True)

    # Build header based on number of levels
    if num_levels == 3:
        # Calculate colspan for level 0 (topmost)
        groups_l0 = OrderedDict()
        for i, val in enumerate(level_0):
            if val not in groups_l0:
                groups_l0[val] = []
            groups_l0[val].append(i)
        
        # Calculate colspan for level 1 within each level 0 group
        groups_l1 = OrderedDict()
        for i, (l0, l1) in enumerate(zip(level_0, level_1)):
            key = (l0, l1)
            if key not in groups_l1:
                groups_l1[key] = []
            groups_l1[key].append(i)
        
        # Start table with 3 header rows
        html += f'<table class="merged-header" id="{table_id}"><thead><tr><th rowspan="{num_levels}" style="text-align: center;" title="Forma de Pagamento">Forma de Pagamento</th>'
        
        # Row 1: Level 0 (status_habilitacao)
        for group_val, indices in groups_l0.items():
            html += f'<th colspan="{len(indices)}" style="text-align: center;" title="{group_val}">{group_val}</th>'
        html += '</tr><tr>'
        
        # Row 2: Level 1 (status_cliente) with group-start markers for vertical separators
        last_l0 = None
        for (l0, l1), indices in groups_l1.items():
            is_group_start = last_l0 is not None and l0 != last_l0
            cls_attr = ' class="group-start"' if is_group_start else ''
            html += f'<th colspan="{len(indices)}"{cls_attr} style="text-align: center;" title="{l1}">{l1}</th>'
            last_l0 = l0
        html += '</tr><tr>'
        
        # Row 3: Level 2 (R$ / # de Compras) with group-start markers to carry top-level separators
        for i, val in enumerate(level_2):
            is_group_start = i > 0 and level_0[i] != level_0[i - 1]
            cls_list = ['sortable']
            if is_group_start:
                cls_list.append('group-start')
            cls_attr = f' class="{" ".join(cls_list)}"'
            html += f'<th{cls_attr} style="text-align: center;" data-col="{i+1}" title="{val}">{val}</th>'
        html += '</tr></thead><tbody>'
        
    elif num_levels == 2:
        # Calculate colspan for level 0
        groups = OrderedDict()
        for i, val in enumerate(level_0):
            if val not in groups:
                groups[val] = []
            groups[val].append(i)
        
        html += f'<table class="merged-header" id="{table_id}"><thead><tr><th rowspan="2" style="text-align: center;" title="Forma de Pagamento">Forma de Pagamento</th>'
        
        # Top header row with merged cells
        for group_val, indices in groups.items():
            html += f'<th colspan="{len(indices)}" style="text-align: center;" title="{group_val}">{group_val}</th>'
        html += '</tr><tr>'
        
        # Second header row with group-start markers for vertical separators
        for i, val in enumerate(level_1):
            is_group_start = i > 0 and level_0[i] != level_0[i - 1]
            cls_list = ['sortable']
            if is_group_start:
                cls_list.append('group-start')
            cls_attr = f' class="{" ".join(cls_list)}"'
            html += f'<th{cls_attr} style="text-align: center;" data-col="{i+1}" title="{val}">{val}</th>'
        html += '</tr></thead><tbody>'
    else:
        # Single-level columns: simple header
        html += f'<table class="merged-header" id="{table_id}"><thead><tr>'
        html += f'<th style="text-align: center;" title="{index_label}">{index_label}</th>'
        for i, val in enumerate(level_0):
            html += f'<th class="sortable" style="text-align: center;" data-col="{i+1}" title="{val}">{val}</th>'
        html += '</tr></thead><tbody>'
    
    # Data rows (without Total) with inline percent of column total
    for idx, row in numeric_df.iterrows():
        first_col_value = str(idx)
        html += f'<tr><td style="text-align: left; font-weight: 600;" title="{first_col_value}">{first_col_value}</td>'
        for col, val in zip(df_pivot.columns, row):
            try:
                v = float(val)
            except Exception:
                v = float('nan')
            if pd.isna(v):
                display_text = "-"
                order_value = "nan"
                percent_text = ""
            else:
                denom = float(col_sums.get(col, 0.0) or 0.0)
                percent_text = f" ({(v/denom):.0%})" if (show_percent and denom) else ""
                display_text = f"{v:,.0f}{percent_text}"
                order_value = f"{v}"
            title_text = display_text if display_text != "-" else "Sem dado"
            html += (
                f'<td style="text-align: right;" data-order="{order_value}" '
                f'data-sort="{order_value}" title="{title_text}">{display_text}</td>'
            )
        html += '</tr>'
    
    html += '</tbody>'
    
    # Add Total row in tfoot (pinned at bottom, unaffected by sorting)
    if total_row is not None:
        html += '<tfoot><tr><td style="text-align: left;" title="Total">Total</td>'
        for val in total_row:
            if pd.isna(val):
                total_value = "-"
                title_text = "Sem dado"
            else:
                total_value = f"{val:,.0f}"
                title_text = total_value
            html += f'<td style="text-align: right;" title="{title_text}">{total_value}</td>'
        html += '</tr></tfoot>'
    
    html += '</table>'
    html += '</div>'
    
    # Inline JavaScript for sorting (no external dependencies - Snowflake compatible)
    html += f'''
    <script>
    (function() {{
        var table = document.getElementById('{table_id}');
        if (!table) return;
        
        var headers = table.querySelectorAll('th.sortable');
        var tbody = table.querySelector('tbody');
        
        headers.forEach(function(header) {{
            header.addEventListener('click', function() {{
                var colIndex = parseInt(this.getAttribute('data-col'));
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var isAsc = this.classList.contains('asc');
                
                // Reset all headers
                headers.forEach(function(h) {{ h.classList.remove('asc', 'desc'); }});
                
                // Set new sort direction
                if (isAsc) {{
                    this.classList.add('desc');
                }} else {{
                    this.classList.add('asc');
                }}
                var ascending = this.classList.contains('asc');
                
                rows.sort(function(a, b) {{
                    var aCell = a.cells[colIndex];
                    var bCell = b.cells[colIndex];
                    var aVal = aCell ? (aCell.getAttribute('data-order') || aCell.textContent) : '';
                    var bVal = bCell ? (bCell.getAttribute('data-order') || bCell.textContent) : '';
                    
                    // Try numeric comparison
                    var aNum = parseFloat(aVal.replace(/,/g, ''));
                    var bNum = parseFloat(bVal.replace(/,/g, ''));
                    
                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return ascending ? aNum - bNum : bNum - aNum;
                    }}
                    
                    // Fall back to string comparison
                    return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }});
                
                // Re-append sorted rows
                rows.forEach(function(row) {{ tbody.appendChild(row); }});
            }});
        }});
    }})();
    </script>'''
    
    # Dynamically size iframe height to avoid large blank gaps below the table
    header_rows = num_levels if num_levels in (2, 3) else 1
    body_rows = len(df_pivot.index)
    footer_rows = 1 if total_row is not None else 0
    header_row_height = 56
    body_row_height = 44
    footer_row_height = 52
    extra_padding = 24
    iframe_height = (
        header_rows * header_row_height
        + body_rows * body_row_height
        + footer_rows * footer_row_height
        + extra_padding
    )
    # Apply optional iframe width for finer layout control
    if frame_width is not None:
        components.html(html, height=int(iframe_height), width=frame_width, scrolling=False)
    else:
        components.html(html, height=int(iframe_height), scrolling=False)

