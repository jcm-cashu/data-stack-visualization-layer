"""
White-Label Dashboard Styles - DO NOT MODIFY
Visual identity: Colors, CSS, table styles.
Typography: Red Hat Display
"""

# Paleta de cores
COLORS = {
    # Cores principais
    "primary": "#f5c344",        # Warm yellow - highlights, buttons, active states
    "secondary": "#903aff",      # Accent purple - charts, highlights
    "accent": "#ff8a00",         # Orange - call-to-action, warnings, KPIs
    "danger": "#cc3366",         # Warm pink/red - alerts, warnings
    
    # Backgrounds
    "bg_dark": "#1a1a1a",        # Off-black background
    "bg_mid": "#3b3b3b",         # Medium gray for containers/cards
    "bg_light": "#f7f7f7",       # Light surface background
    "bg_white": "#FFFFFF",
    
    # Texto
    "text_primary": "#000000",   # Main text
    "text_secondary": "#555555", # Muted text
    
    # Tabela
    "table_header": "#f5c344",   # Light yellow for headers
    "table_header_text": "#1a1a1a",  # Dark text on yellow background
    "table_border": "#e0e0e0",
    "table_hover": "#fff3d6",    # Light yellow hover
    "table_stripe": "#fafafa",
    "table_total": "#f0f0f0",    # Very light gray for totals
    "table_total_text": "#1a1a1a",  # Dark text on light background
}


def get_custom_css() -> str:
    """Retorna CSS customizado para o dashboard."""
    return f"""
    <style>
    /* ===== Configurações Globais ===== */
    @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap');
    
    /* Apply Red Hat Display to text elements only, not icons/buttons */
    body, .main, [data-testid="stMarkdownContainer"], 
    [data-testid="stText"], p, div:not([data-testid*="collapse"]):not([role="button"]) {{
        font-family: 'Red Hat Display', sans-serif !important;
    }}
    
    :root {{
        --primary-color: {COLORS['primary']};
        --secondary-color: {COLORS['secondary']};
        --accent-color: {COLORS['accent']};
    }}
    
    /* ===== Main Container ===== */
    /* Multiple selectors for Snowflake-hosted Streamlit compatibility */
    .main {{
        background-color: {COLORS['bg_light']} !important;
    }}
    
    .stApp {{
        background-color: {COLORS['bg_light']} !important;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: {COLORS['bg_light']} !important;
    }}
    
    [data-testid="stAppViewBlockContainer"] {{
        background-color: {COLORS['bg_light']} !important;
    }}
    
    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['bg_light']};
    }}
    
    [data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        border: 0 !important;
        padding: 0.5rem 0 !important;
        color: {COLORS['text_primary']} !important;
        text-align: left !important;
        box-shadow: none !important;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        text-decoration: underline;
        color: {COLORS['secondary']} !important;
        background: transparent !important;
    }}
    
    [data-testid="stSidebar"] .nav-selected {{
        font-weight: 700;
        text-decoration: underline;
        padding: 0.5rem 0;
        cursor: default;
        color: {COLORS['secondary']};
    }}
    
    /* ===== Headers ===== */
    h1 {{
        color: {COLORS['text_primary']} !important;
        font-weight: 800 !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
        background-color: {COLORS['bg_light']} !important;
        padding: 0.5rem 0 !important;
    }}
    
    h2 {{
        color: {COLORS['secondary']} !important;
        font-weight: 700 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        background-color: {COLORS['bg_light']} !important;
        padding: 0.5rem 0 !important;
    }}

    
    
    /* Reduce gap between consecutive h2 (subheaders) */
    h2 + h2 {{
        margin-top: 0rem !important;
        margin-bottom: 0.5rem !important;
    }}
    
    /* (No global overrides for stComponent/iframe) */
    
    h3 {{
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    /* ===== Inputs e Controles ===== */
    .stDateInput > div > div > input {{
        border-color: {COLORS['table_border']} !important;
    }}
    
    .stDateInput > div > div > input:focus {{
        border-color: {COLORS['secondary']} !important;
        box-shadow: 0 0 0 2px {COLORS['secondary']}33 !important;
    }}
    
    /* ===== Métricas ===== */
    [data-testid="stMetricValue"] {{
        color: {COLORS['accent']} !important;
        font-weight: 700 !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
        font-weight: 500 !important;
    }}
    
    /* ===== Divisor ===== */
    hr {{
        border-color: {COLORS['table_border']} !important;
    }}
    
    /* ===== DataFrames ===== */
    .dataframe {{
        font-size: 13px !important;
    }}
    
    /* ===== Links ===== */
    a {{
        color: {COLORS['secondary']} !important;
        text-decoration: none !important;
    }}
    
    a:hover {{
        color: {COLORS['accent']} !important;
        text-decoration: underline !important;
    }}
    
    /* ===== Chiclet/Filter Button Group ===== */
    /* Styling for filter buttons in main area */
    
    /* Base button styling - readable size */
    .stButton > button {{
        font-size: 12px !important;
        padding: 0.4rem 0.8rem !important;
        min-height: 32px !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    
    /* Selected chiclet (primary button) - Yellow background */
    [data-testid="baseButton-primary"],
    button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: {COLORS['primary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['primary']} !important;
    }}
    
    /* Unselected chiclet (secondary button) - White background */
    [data-testid="baseButton-secondary"],
    button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
        background-color: {COLORS['bg_white']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['table_border']} !important;
    }}
    
    /* Hover states */
    [data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {{
        background-color: {COLORS['accent']} !important;
        border-color: {COLORS['accent']} !important;
    }}
    
    [data-testid="baseButton-secondary"]:hover,
    button[kind="secondary"]:hover {{
        background-color: {COLORS['table_hover']} !important;
        border-color: {COLORS['primary']} !important;
    }}

    </style>
    """


def get_table_styles() -> dict:
    """Retorna estilos para componentes de tabela customizados."""
    return {
        "header_bg": COLORS["table_header"],
        "header_text": COLORS["table_header_text"],
        "border": COLORS["table_border"],
        "hover": COLORS["table_hover"],
        "stripe": COLORS["table_stripe"],
        "total_bg": COLORS["table_total"],
        "total_text": COLORS["table_header_text"],
    }
