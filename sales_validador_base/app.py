"""
CashU | Validador de Base - Main Entry Point

Single-page Streamlit app for uploading and validating BNPL datasets.
Uses the whitelabel design system for visual consistency.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from shared.styles import get_custom_css, get_table_styles, COLORS

from validator import (
    EXPECTED_SCHEMA,
    POST_PROCESS_SCHEMA,
    NULL_LIMITS,
)
from validator.engine import (
    ValidationResult,
    run_validations,
    duckdb_post_process,
    compute_statistics,
    validate_null_limits,
    validate_business_rules,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

DASHBOARD_TITLE = "CashU | Validador de Base"

st.set_page_config(page_title=DASHBOARD_TITLE, layout="wide")
st.markdown(get_custom_css(), unsafe_allow_html=True)

st.markdown(f"""
<style>
.val-card {{
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 8px;
    font-family: 'Red Hat Display', sans-serif;
    font-size: 14px;
    line-height: 1.5;
}}
.val-success {{
    background-color: #e6f9ed;
    border-left: 4px solid #2e7d32;
    color: #1b5e20;
}}
.val-warning {{
    background-color: #fff8e1;
    border-left: 4px solid {COLORS['primary']};
    color: #6d4c00;
}}
.val-error {{
    background-color: #fce4ec;
    border-left: 4px solid {COLORS['danger']};
    color: #880e4f;
}}
.val-item {{
    padding: 2px 0;
}}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Styled table helper
# ---------------------------------------------------------------------------

def _render_styled_dataframe(
    df: pd.DataFrame,
    table_id: str = "styled-table",
) -> None:
    """Render a flat DataFrame as an HTML table styled with the design system."""
    styles = get_table_styles()

    css = f"""
    <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    html, body {{ margin: 0; padding: 0 12px 0 0; background: transparent; }}
    .ds-table-wrap {{
        width: 100%; overflow-x: auto; scrollbar-width: thin; margin-bottom: 16px;
    }}
    .ds-table-wrap::-webkit-scrollbar {{ height: 6px; }}
    .ds-table-wrap::-webkit-scrollbar-thumb {{ background-color: rgba(0,0,0,.25); border-radius: 999px; }}
    table.ds-table {{
        border-collapse: collapse; width: 100%; table-layout: auto;
        font-family: 'Red Hat Display', sans-serif; font-size: 12px; margin: 0;
    }}
    table.ds-table th {{
        background-color: {styles['header_bg']}; color: {styles['header_text']};
        font-weight: 600; text-align: center; padding: 8px 12px;
        border: none; white-space: nowrap;
        border-bottom: 3px solid #000 !important;
    }}
    table.ds-table td {{
        padding: 8px 12px; border: none; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;
    }}
    table.ds-table tbody tr:nth-child(even) {{
        background-color: {styles['stripe']};
    }}
    table.ds-table tbody tr:hover {{
        background-color: {styles['hover']}; transition: background-color .2s ease;
    }}
    table.ds-table td:first-child {{ font-weight: 600; text-align: left; }}
    table.ds-table td:not(:first-child) {{ text-align: right; }}
    </style>
    """

    header = "".join(f'<th title="{c}">{c}</th>' for c in df.columns)
    rows_html = ""
    for _, row in df.iterrows():
        cells = ""
        for val in row:
            display = str(val) if val is not None and pd.notna(val) else "-"
            cells += f'<td title="{display}">{display}</td>'
        rows_html += f"<tr>{cells}</tr>"

    html = (
        f'{css}<div class="ds-table-wrap">'
        f'<table class="ds-table" id="{table_id}">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{rows_html}</tbody></table></div>"
    )

    row_count = len(df)
    header_height = 44
    row_height = 40
    padding = 24
    iframe_h = header_height + row_count * row_height + padding
    components.html(html, height=int(iframe_h), scrolling=False)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _render_result(result: ValidationResult) -> None:
    """Render a ValidationResult as a styled card."""
    if result.passed and not result.warnings:
        st.markdown(
            f'<div class="val-card val-success">&#10003; {result.stage}: '
            f"validação passou com sucesso.</div>",
            unsafe_allow_html=True,
        )
        return

    if result.errors:
        items = "".join(
            f'<div class="val-item">&#10007; {e}</div>' for e in result.errors
        )
        st.markdown(
            f'<div class="val-card val-error">'
            f"<strong>{result.stage} &mdash; Erros</strong>{items}</div>",
            unsafe_allow_html=True,
        )

    if result.warnings:
        items = "".join(
            f'<div class="val-item">&#9888; {w}</div>' for w in result.warnings
        )
        st.markdown(
            f'<div class="val-card val-warning">'
            f"<strong>{result.stage} &mdash; Avisos</strong>{items}</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

SEPARATOR_LABELS = {
    "Vírgula ( , )": ",",
    "Ponto e vírgula ( ; )": ";",
    "Tab": "\t",
    "Pipe ( | )": "|",
}


def _sidebar():
    """Render sidebar controls and return (file_type, sheet_name, separator, uploaded_file)."""
    st.sidebar.header("Configurações")

    file_type = st.sidebar.selectbox(
        "Tipo de Arquivo",
        options=["Excel", "CSV"],
        index=0,
    )

    st.sidebar.divider()

    sheet_name = ""
    separator = ","

    if file_type == "Excel":
        sheet_name = st.sidebar.text_input(
            "Nome da Aba",
            value="Preencher",
            help="Nome da aba (sheet) a ser lida do arquivo Excel.",
        )
        accepted = ["xlsx", "xls"]
    else:
        sep_label = st.sidebar.selectbox(
            "Separador",
            options=list(SEPARATOR_LABELS.keys()),
            index=0,
        )
        separator = SEPARATOR_LABELS[sep_label]
        accepted = ["csv", "txt"]

    st.sidebar.divider()

    uploaded = st.sidebar.file_uploader(
        "Upload do Arquivo",
        type=accepted,
        help="Arraste ou clique para enviar o arquivo.",
    )

    return file_type, sheet_name, separator, uploaded


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def _load_file(
    uploaded_file,
    file_type: str,
    sheet_name: str,
    separator: str,
) -> pd.DataFrame:
    """Read an uploaded file into a DataFrame."""
    if file_type == "Excel":
        return pd.read_excel(uploaded_file, sheet_name=sheet_name or 0)
    return pd.read_csv(uploaded_file, sep=separator)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.title(DASHBOARD_TITLE)

    file_type, sheet_name, separator, uploaded = _sidebar()

    if uploaded is None:
        st.markdown(
            f'<div style="text-align:center; padding:80px 0; '
            f'color:{COLORS["text_secondary"]}; font-size:16px;">'
            f"Envie um arquivo pela barra lateral para iniciar a validação."
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    # --- Load file ---
    try:
        df_raw = _load_file(uploaded, file_type, sheet_name, separator)
    except Exception as exc:
        st.error(f"Erro ao ler o arquivo: {exc}")
        return

    st.caption(
        f"Arquivo: **{uploaded.name}** &nbsp;|&nbsp; "
        f"Linhas: **{len(df_raw):,}** &nbsp;|&nbsp; "
        f"Colunas: **{len(df_raw.columns)}**"
    )

    all_passed = True

    # --- Step 1: Pre-processing validation ---
    st.subheader("1. Validação Pré-processamento")
    pre_result = run_validations(
        df_raw, EXPECTED_SCHEMA, stage="Pré-processamento", strict=False
    )
    _render_result(pre_result)

    if pre_result.errors:
        st.warning("Pipeline interrompido devido a erros no pré-processamento.")
        return

    # --- Step 2: Data normalisation ---
    st.subheader("2. Normalização dos Dados")
    try:
        df_processed = duckdb_post_process(df_raw)
        st.markdown(
            '<div class="val-card val-success">&#10003; Dados normalizados com '
            "sucesso via DuckDB (CNPJs, datas e valores numéricos).</div>",
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.markdown(
            f'<div class="val-card val-error">&#10007; Erro na normalização: '
            f"{exc}</div>",
            unsafe_allow_html=True,
        )
        return

    # --- Step 3: Post-processing validation ---
    st.subheader("3. Validação Pós-processamento")
    post_result = run_validations(
        df_processed, POST_PROCESS_SCHEMA, stage="Pós-processamento", strict=True
    )
    _render_result(post_result)

    if post_result.errors:
        all_passed = False

    # --- Step 4: Statistics ---
    st.subheader("4. Estatísticas dos Dados")
    stats_df = compute_statistics(df_processed, POST_PROCESS_SCHEMA)
    stats_display = stats_df.copy()
    stats_display.columns = [
        "Coluna", "Tipo", "Total Linhas", "Únicos",
        "Nulos", "Nulos %", "Mín", "Máx", "Média",
    ]
    _render_styled_dataframe(stats_display, table_id="stats-table")

    # --- Step 5: Null limits ---
    st.subheader("5. Limites de Nulos")
    null_result = validate_null_limits(df_processed, NULL_LIMITS)
    _render_result(null_result)

    if not null_result.passed:
        all_passed = False

    # --- Step 6: Business rules ---
    st.subheader("6. Regras de Negócio")
    biz_result = validate_business_rules(df_processed)
    _render_result(biz_result)

    if not biz_result.passed:
        all_passed = False

    # --- Data preview ---
    st.subheader("Prévia dos Dados Processados")
    preview_df = df_processed.head(20).copy()
    for col in preview_df.columns:
        preview_df[col] = preview_df[col].astype(str).replace("NaT", "-").replace("nan", "-")
    _render_styled_dataframe(preview_df, table_id="preview-table")

    # --- Download ---
    st.sidebar.divider()
    if all_passed:
        csv_bytes = df_processed.to_csv(index=False).encode("utf-8")
        base_name = uploaded.name.rsplit(".", 1)[0] if "." in uploaded.name else uploaded.name
        st.sidebar.download_button(
            label="Baixar CSV Validado",
            data=csv_bytes,
            file_name=f"{base_name}_validado.csv",
            mime="text/csv",
            type="primary",
        )
    else:
        st.sidebar.warning("Corrija os erros de validação para habilitar o download.")


if __name__ == "__main__":
    main()
