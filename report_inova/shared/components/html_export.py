"""
HTML export engine for dashboard pages.

Serializes collected content blocks (Plotly figures, metrics, tables,
headings) into a single self-contained interactive HTML file.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from ..styles import COLORS

_EXPORT_STATE_KEY = "_html_export_blocks"


def _is_collecting() -> bool:
    return st.session_state.get(_EXPORT_STATE_KEY) is not None


def _collect(block: dict[str, Any]) -> None:
    buf = st.session_state.get(_EXPORT_STATE_KEY)
    if buf is not None:
        buf.append(block)


def start_collection() -> None:
    st.session_state[_EXPORT_STATE_KEY] = []


def stop_collection() -> list[dict[str, Any]]:
    blocks = st.session_state.pop(_EXPORT_STATE_KEY, [])
    return blocks


# ------------------------------------------------------------------
# Collector helpers -- call these instead of raw st.* calls
# ------------------------------------------------------------------

def collect_chart(fig: go.Figure) -> None:
    """Append a Plotly figure to the export buffer (if active)."""
    if _is_collecting():
        _collect({"type": "chart", "figure": fig})


def collect_metric(label: str, value: str) -> None:
    if _is_collecting():
        _collect({"type": "metric", "label": label, "value": value})


def collect_subheader(text: str) -> None:
    if _is_collecting():
        _collect({"type": "subheader", "text": text})


def collect_caption(text: str) -> None:
    if _is_collecting():
        _collect({"type": "caption", "text": text})


def collect_divider() -> None:
    if _is_collecting():
        _collect({"type": "divider"})


def collect_dataframe(df: pd.DataFrame, title: str = "") -> None:
    if _is_collecting():
        _collect({"type": "dataframe", "df": df.copy(), "title": title})


def collect_columns_start(n: int) -> None:
    if _is_collecting():
        _collect({"type": "row_start", "n": n})


def collect_columns_end() -> None:
    if _is_collecting():
        _collect({"type": "row_end"})


def collect_selector_start(options: list[str], label: str = "Selecione") -> None:
    """Begin a filterable section with a dropdown selector in the export."""
    if _is_collecting():
        _collect({"type": "selector_start", "options": options, "label": label})


def collect_selector_option(option: str) -> None:
    """Mark the beginning of content for one selector option."""
    if _is_collecting():
        _collect({"type": "selector_option", "option": option})


def collect_selector_end() -> None:
    if _is_collecting():
        _collect({"type": "selector_end"})


# ------------------------------------------------------------------
# HTML generation
# ------------------------------------------------------------------

def _render_chart_div(fig: go.Figure, idx: int) -> str:
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=False,
        div_id=f"chart-{idx}",
        config={"responsive": True, "displaylogo": False},
    )


def _render_metric_card(label: str, value: str) -> str:
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'</div>'
    )


_table_counter = 0
_selector_counter = 0


def _next_table_id() -> str:
    global _table_counter
    _table_counter += 1
    return f"grid-{_table_counter}"


def _next_selector_id() -> str:
    global _selector_counter
    _selector_counter += 1
    return f"sel-{_selector_counter}"


def _render_dataframe_html(df: pd.DataFrame) -> str:
    table_id = _next_table_id()
    has_index = not isinstance(df.index, pd.RangeIndex)
    page_size = 12

    header_cells = ""
    if has_index:
        header_cells += f'<th class="sortable" data-col="0">{df.index.name or ""}</th>'
    for i, col in enumerate(df.columns):
        col_idx = i + 1 if has_index else i
        header_cells += f'<th class="sortable" data-col="{col_idx}">{col}</th>'

    body_rows = ""
    for row_idx, (idx_val, row) in enumerate(df.iterrows()):
        cells = ""
        if has_index:
            cells += f'<td class="idx-cell">{idx_val}</td>'
        for val in row:
            display = "-" if pd.isna(val) else str(val)
            try:
                sort_val = str(float(val))
            except (ValueError, TypeError):
                sort_val = display
            cells += f'<td data-order="{sort_val}">{display}</td>'
        body_rows += f'<tr>{cells}</tr>'

    total_rows = len(df)
    needs_paging = total_rows > page_size

    return f"""
    <div class="ag-wrapper" id="{table_id}-wrap">
    <table class="ag-table" id="{table_id}">
    <thead><tr>{header_cells}</tr></thead>
    <tbody>{body_rows}</tbody>
    </table>
    {f'<div class="ag-pager" id="{table_id}-pager"></div>' if needs_paging else ''}
    </div>
    <script>
    (function(){{
      var tid='{table_id}', ps={page_size}, total={total_rows};
      var t=document.getElementById(tid);
      if(!t)return;
      var ths=t.querySelectorAll('th.sortable'),tb=t.querySelector('tbody');
      var allRows=Array.from(tb.querySelectorAll('tr'));
      var curPage=0, totalPages=Math.ceil(total/ps);
      var needsPaging=total>ps;

      function showPage(p){{
        curPage=Math.max(0,Math.min(p,totalPages-1));
        allRows.forEach(function(r,i){{
          r.style.display=(i>=curPage*ps&&i<(curPage+1)*ps)?'':'none';
        }});
        allRows.forEach(function(r,i){{
          if(r.style.display!=='none'){{
            var vi=Array.from(tb.querySelectorAll('tr')).filter(function(x){{return x.style.display!=='none'}}).indexOf(r);
            r.className=vi%2===0?'even':'odd';
          }}
        }});
        if(needsPaging)updatePager();
      }}

      function updatePager(){{
        var pg=document.getElementById(tid+'-pager');
        if(!pg)return;
        pg.innerHTML='<span>Página '+(curPage+1)+' de '+totalPages+'</span>'
          +'<button '+(curPage===0?'disabled':'')+' onclick="document._pagers[\\''+tid+'\\'].prev()">&#9664;</button>'
          +'<button '+(curPage>=totalPages-1?'disabled':'')+' onclick="document._pagers[\\''+tid+'\\'].next()">&#9654;</button>';
      }}

      if(!document._pagers)document._pagers={{}};
      document._pagers[tid]={{
        prev:function(){{showPage(curPage-1)}},
        next:function(){{showPage(curPage+1)}}
      }};

      ths.forEach(function(h){{
        h.addEventListener('click',function(){{
          var ci=parseInt(this.dataset.col),asc=this.classList.contains('asc');
          ths.forEach(function(x){{x.classList.remove('asc','desc')}});
          this.classList.add(asc?'desc':'asc');
          var asc2=this.classList.contains('asc');
          allRows.sort(function(a,b){{
            var av=(a.cells[ci]||{{}}).getAttribute('data-order')||(a.cells[ci]||{{}}).textContent||'';
            var bv=(b.cells[ci]||{{}}).getAttribute('data-order')||(b.cells[ci]||{{}}).textContent||'';
            var an=parseFloat(av.replace(/,/g,'')),bn=parseFloat(bv.replace(/,/g,''));
            if(!isNaN(an)&&!isNaN(bn))return asc2?an-bn:bn-an;
            return asc2?av.localeCompare(bv):bv.localeCompare(av);
          }});
          allRows.forEach(function(r){{tb.appendChild(r)}});
          showPage(0);
        }});
      }});

      showPage(0);
    }})();
    </script>"""


def _render_blocks_html(blocks: list[dict[str, Any]], chart_offset: int = 0) -> tuple[str, int]:
    """Render a list of blocks to HTML fragments. Returns (html, next_chart_idx)."""
    parts: list[str] = []
    chart_idx = chart_offset
    in_row = False
    row_col_count = 0
    cur_selector_id: str | None = None
    in_selector_option = False

    for block in blocks:
        btype = block["type"]

        if btype == "row_start":
            row_col_count = block["n"]
            parts.append('<div class="flex-row">')
            in_row = True
            continue

        if btype == "row_end":
            if in_row:
                parts.append('</div>')
            in_row = False
            continue

        if btype == "selector_start":
            sid = _next_selector_id()
            cur_selector_id = sid
            options = block["options"]
            label = block["label"]
            opts_html = "".join(
                f'<option value="{opt}">{opt}</option>' for opt in options
            )
            parts.append(
                f'<div class="selector-wrapper">'
                f'<label class="selector-label" for="{sid}">{label}</label>'
                f'<select id="{sid}" class="selector-dropdown" '
                f'onchange="switchOption(\'{sid}\', this.value)">'
                f'{opts_html}</select>'
                f'</div>'
            )
            continue

        if btype == "selector_option":
            opt = block["option"]
            if in_selector_option:
                parts.append('</div>')
            in_selector_option = True
            parts.append(
                f'<div class="selector-section" data-selector="{cur_selector_id}" '
                f'data-option="{opt}" style="display:none">'
            )
            continue

        if btype == "selector_end":
            if in_selector_option:
                parts.append('</div>')
            in_selector_option = False
            if cur_selector_id:
                parts.append(
                    f'<script>(function(){{'
                    f'switchOption("{cur_selector_id}",document.getElementById("{cur_selector_id}").value);'
                    f'}})();</script>'
                )
            cur_selector_id = None
            continue

        if in_row and btype in ("chart", "metric", "dataframe"):
            pct = int(100 / row_col_count)
            parts.append(f'<div class="flex-col" style="width:{pct}%">')

        if btype == "chart":
            parts.append(_render_chart_div(block["figure"], chart_idx))
            chart_idx += 1
        elif btype == "metric":
            parts.append(_render_metric_card(block["label"], block["value"]))
        elif btype == "subheader":
            parts.append(f'<h2>{block["text"]}</h2>')
        elif btype == "caption":
            parts.append(f'<p class="caption">{block["text"]}</p>')
        elif btype == "divider":
            parts.append("<hr>")
        elif btype == "dataframe":
            parts.append(_render_dataframe_html(block["df"]))

        if in_row and btype in ("chart", "metric", "dataframe"):
            parts.append('</div>')

    return "\n".join(parts), chart_idx


def generate_full_export_html(
    pages: dict[str, list[dict[str, Any]]],
    title: str = "Dashboard",
    reference_date: date | None = None,
) -> str:
    """Build a single HTML file containing all dashboard pages with tab navigation."""
    global _table_counter, _selector_counter
    _table_counter = 0
    _selector_counter = 0
    ref_str = reference_date.strftime("%d/%m/%Y") if reference_date else ""
    page_names = list(pages.keys())

    tab_buttons = ""
    for i, name in enumerate(page_names):
        active = " active" if i == 0 else ""
        tab_buttons += f'<button class="tab-btn{active}" onclick="showPage(\'page-{i}\', this)">{name}</button>\n'

    page_divs = ""
    chart_offset = 0
    for i, (name, blocks) in enumerate(pages.items()):
        display = "block" if i == 0 else "none"
        body_html, chart_offset = _render_blocks_html(blocks, chart_offset)
        page_divs += f'<div id="page-{i}" class="page-content" style="display:{display}">\n{body_html}\n</div>\n'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0;
    font-family: 'Red Hat Display', sans-serif;
    background: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
  }}
  header {{
    padding: 24px 40px 0;
  }}
  h1 {{
    font-weight: 800; letter-spacing: -0.02em;
    margin: 0 0 4px; font-size: 2rem;
  }}
  .subtitle {{ color: {COLORS['text_secondary']}; margin: 0 0 16px; font-size: 1rem; }}
  h2 {{
    color: {COLORS['secondary']}; font-weight: 700;
    margin: 2rem 0 0.5rem; font-size: 1.25rem;
  }}
  .caption {{ color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0 0 12px; }}
  hr {{ border: none; border-top: 1px solid {COLORS['table_border']}; margin: 24px 0; }}

  /* Tab navigation */
  .tab-bar {{
    display: flex; gap: 0; padding: 0 40px;
    border-bottom: 2px solid {COLORS['table_border']};
    background: {COLORS['bg_light']};
    position: sticky; top: 0; z-index: 100;
  }}
  .tab-btn {{
    font-family: 'Red Hat Display', sans-serif;
    font-size: 14px; font-weight: 600;
    padding: 12px 24px;
    border: none; background: transparent;
    color: {COLORS['text_secondary']};
    cursor: pointer; transition: all 0.2s;
    border-bottom: 3px solid transparent;
    margin-bottom: -2px;
  }}
  .tab-btn:hover {{ color: {COLORS['text_primary']}; }}
  .tab-btn.active {{
    color: {COLORS['secondary']};
    border-bottom-color: {COLORS['secondary']};
  }}
  .page-content {{ padding: 24px 40px; }}

  /* Metric cards */
  .metrics-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; }}
  .metric-card {{
    flex: 1 1 180px; padding: 16px 20px;
    background: {COLORS['bg_white']}; border-radius: 8px;
    border: 1px solid {COLORS['table_border']};
  }}
  .metric-label {{ color: {COLORS['text_secondary']}; font-weight: 500; font-size: 0.85rem; }}
  .metric-value {{ color: {COLORS['accent']}; font-weight: 700; font-size: 1.5rem; margin-top: 4px; }}

  /* Flex grid for side-by-side charts */
  .flex-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }}
  .flex-col {{ min-width: 0; }}

  /* AG Grid-style tables */
  .ag-wrapper {{
    border: 1px solid {COLORS['table_border']};
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 16px;
    background: {COLORS['bg_white']};
  }}
  .ag-table {{
    border-collapse: collapse; width: 100%;
    font-family: 'Red Hat Display', sans-serif; font-size: 13px;
  }}
  .ag-table th {{
    background: {COLORS['table_header']}; color: {COLORS['table_header_text']};
    font-weight: 600; text-align: center; padding: 10px 14px;
    border-bottom: 2px solid {COLORS['table_border']};
    cursor: pointer; user-select: none;
    position: relative; white-space: nowrap;
  }}
  .ag-table th::after {{ content: '⇅'; position: absolute; right: 6px; top: 50%; transform: translateY(-50%); opacity: .35; font-size: 10px; }}
  .ag-table th.asc::after {{ content: '▲'; opacity: 1; color: {COLORS['secondary']}; }}
  .ag-table th.desc::after {{ content: '▼'; opacity: 1; color: {COLORS['secondary']}; }}
  .ag-table td {{
    padding: 8px 14px; text-align: right; white-space: nowrap;
    border-bottom: 1px solid {COLORS['table_border']};
  }}
  .ag-table td.idx-cell {{ text-align: left; font-weight: 600; }}
  .ag-table tr.even {{ background: {COLORS['bg_white']}; }}
  .ag-table tr.odd {{ background: {COLORS['table_stripe']}; }}
  .ag-table tr:hover {{ background: {COLORS['table_hover']}; }}

  /* Pagination bar */
  .ag-pager {{
    display: flex; align-items: center; justify-content: flex-end; gap: 10px;
    padding: 8px 14px;
    font-size: 12px; color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['table_border']};
    background: {COLORS['bg_light']};
  }}
  .ag-pager button {{
    font-family: 'Red Hat Display', sans-serif;
    background: transparent; border: 1px solid {COLORS['table_border']};
    border-radius: 4px; padding: 4px 10px; cursor: pointer;
    color: {COLORS['text_primary']}; font-size: 12px;
    transition: background 0.15s;
  }}
  .ag-pager button:hover:not(:disabled) {{ background: {COLORS['table_hover']}; }}
  .ag-pager button:disabled {{ opacity: 0.35; cursor: default; }}

  /* Selector dropdown */
  .selector-wrapper {{
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 16px;
  }}
  .selector-label {{
    font-weight: 600; font-size: 14px;
    color: {COLORS['text_secondary']};
  }}
  .selector-dropdown {{
    font-family: 'Red Hat Display', sans-serif;
    font-size: 14px; font-weight: 500;
    padding: 8px 14px; border-radius: 6px;
    border: 1px solid {COLORS['table_border']};
    background: {COLORS['bg_white']};
    color: {COLORS['text_primary']};
    cursor: pointer; min-width: 220px;
    outline: none; transition: border-color 0.15s;
  }}
  .selector-dropdown:focus {{
    border-color: {COLORS['secondary']};
  }}

  /* Plotly responsive overrides */
  .js-plotly-plot {{ width: 100% !important; }}

  @media print {{
    body {{ padding: 12px; }}
    .tab-bar {{ display: none; }}
    .page-content {{ display: block !important; page-break-before: always; }}
    .page-content:first-of-type {{ page-break-before: auto; }}
    .js-plotly-plot .plotly {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <p class="subtitle">{ref_str}</p>
</header>
<nav class="tab-bar">
{tab_buttons}
</nav>
{page_divs}
<script>
function showPage(id, btn) {{
  document.querySelectorAll('.page-content').forEach(function(el) {{ el.style.display = 'none'; }});
  document.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
  document.getElementById(id).style.display = 'block';
  btn.classList.add('active');
  window.dispatchEvent(new Event('resize'));
}}
function switchOption(selectorId, value) {{
  document.querySelectorAll('.selector-section[data-selector="'+selectorId+'"]').forEach(function(el) {{
    el.style.display = el.getAttribute('data-option') === value ? 'block' : 'none';
  }});
  window.dispatchEvent(new Event('resize'));
}}
</script>
</body>
</html>"""
