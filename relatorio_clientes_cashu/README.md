# CashU | Cacau Show Dashboard

A Streamlit-based analytics dashboard for CashU's Cacau Show partnership. This application visualizes sales metrics, credit utilization, and delinquency analysis for franchise stores and resellers.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Data Flow](#data-flow)
- [Pages and Sections](#pages-and-sections)
- [Database Schema](#database-schema)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
- [Extending the Application](#extending-the-application)

---

## Architecture Overview

The application follows a **three-layer architecture** that separates concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│                         (app.py)                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ render_sumario_ │  │ render_         │  │ Streamlit       │ │
│  │ geral()         │  │ inadimplencia() │  │ Components      │ │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘ │
│           │                    │                                │
│           ▼                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Section Functions (_render_*)                  ││
│  │  • _render_numeros_gerais()    • _render_evolucao_inad...() ││
│  │  • _render_breakdown_lojas()   • _render_safras_clientes()  ││
│  │  • _render_breakdown_revend..()• _render_safras_originacao()││
│  │  • _render_evolucao_fatur...()                              ││
│  │  • _render_distribuicao_cred()                              ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   queries.py    │  │     db.py       │  │   config.py     │ │
│  │  SQL templates  │  │  run_query()    │  │  Environment    │ │
│  │  & constants    │  │  get_connection │  │  variables      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                              │
│                                                                 │
│                    DuckDB Database                              │
│           ┌─────────────────────────────────┐                   │
│           │  gold.movimentacoes_cacau_show_ │                   │
│           │       analytics (main view)     │                   │
│           ├─────────────────────────────────┤                   │
│           │  silver.movimentacao_boletos_   │                   │
│           │       cashu (payment details)   │                   │
│           └─────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle**: Streamlit is purely a visualization layer. All heavy data processing happens in DuckDB through pre-built views and SQL aggregations.

---

## Project Structure

```
cacau_show_app/
├── app.py                 # Main Streamlit application
├── queries.py             # SQL query templates and constants
├── db.py                  # Database connection and query execution
├── config.py              # Environment configuration loader
├── styles.py              # CSS styles and color palette
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
└── components/
    ├── __init__.py        # Component exports
    ├── chiclet.py         # Button selector component
    └── table.py           # Merged-header table component
```

### File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main entry point. Contains page routing, section render functions, and Plotly chart configurations. |
| `queries.py` | All SQL queries separated from visualization logic. Functions return parameterized SQL strings. |
| `db.py` | Database abstraction with Streamlit caching. Provides `run_query()` for all data access. |
| `config.py` | Loads `.env` file and exposes configuration constants. |
| `styles.py` | Theme configuration: color palette (`COLORS` dict) and CSS generation (`get_custom_css()`). |
| `components/chiclet.py` | Reusable button-group selector widget. |
| `components/table.py` | Complex HTML table renderer with multi-level headers and DataTables integration. |

---

## Data Flow

```
User Interaction          Application Logic                Database
─────────────────         ─────────────────                ────────

[Date Selector] ──────▶  _sidebar() stores
                         reference_date in
                         st.session_state
                              │
                              ▼
[Page Navigation] ────▶  main() routes to
                         render_*() function
                              │
                              ▼
                         Section function calls
                         queries.get_*_query()
                              │
                              ▼
                         run_query(sql, params)  ────────▶  DuckDB
                              │                             executes
                              │                             SQL
                              ◀────────────────────────────
                         Returns pd.DataFrame
                              │
                              ▼
                         DataFrame pivot/transform
                         (minimal processing)
                              │
                              ▼
                         render_table_*() or
                         st.plotly_chart()
                              │
                              ▼
                         [User sees results]
```

### Caching Strategy

- **`@st.cache_resource`**: Used for database connections (persistent across reruns)
- **`@st.cache_data(ttl=60)`**: Used for query results (cached for 60 seconds)

---

## Pages and Sections

### Page 1: Sumário Geral (General Summary)

| Section | Function | Description |
|---------|----------|-------------|
| Números Gerais | `_render_numeros_gerais()` | Three tables showing totals, by enablement status, and by store tier |
| Breakdown Lojas | `_render_breakdown_lojas()` | Store breakdown with filters (tier, enablement) + credit distribution histogram |
| Breakdown Revendedores | `_render_breakdown_revendedores()` | Reseller breakdown by credit status and store enablement |
| Evolução Faturamento | `_render_evolucao_faturamento()` | Per-capita revenue time series (2-12 months) |
| Distribuição Crédito | `_render_distribuicao_credito()` | Credit granted vs utilized histograms |

### Page 2: Inadimplência (Delinquency)

| Section | Function | Description |
|---------|----------|-------------|
| Evolução Inadimplência | `_render_evolucao_inadimplencia()` | Delinquency evolution line chart by aging bucket |
| Safras Clientes | `_render_safras_clientes()` | Vintage analysis by customer relationship start date |
| Safras Originação | `_render_safras_originacao()` | Vintage analysis by document origination date |

---

## Database Schema

The application primarily queries two tables/views:

### `gold.movimentacoes_cacau_show_analytics`

Main analytics view with pre-calculated flags and metrics.

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE | Reference date |
| `mes`, `ano` | INT | Month and year |
| `customer_id` | STRING | Customer identifier |
| `venda_flag` | BOOLEAN | Whether this is a valid sale |
| `valor_venda` | DECIMAL | Sale amount |
| `valor_bruto` | DECIMAL | Gross value |
| `forma_pagamento` | STRING | Payment method (BOL=boleto/CashU) |
| `loja_habilitada_flag` | BOOLEAN | Store enabled for CashU |
| `tier_loja` | STRING | Store tier (A-E) |
| `tipo_loja` | STRING | Store type (Franquia/Loja Própria) |
| `possui_credito_flag` | BOOLEAN | Customer has CashU credit |
| `credit_limit` | DECIMAL | Customer credit limit |
| `compra_ativa_flag` | BOOLEAN | Active purchase |
| `em_atraso_flag` | BOOLEAN | In arrears |
| `over_30_flag`, `over_60_flag`, `over_90_flag`, `over_180_flag` | BOOLEAN | Aging bucket flags |
| `dias_relacionamento_cashu` | INT | Days since first CashU interaction |
| `dias_ultima_compra` | INT | Days since last purchase |

### `silver.movimentacao_boletos_cashu`

Payment-level detail for vintage analysis.

| Column | Type | Description |
|--------|------|-------------|
| `data_pedido` | DATE | Order date |
| `data_vencimento` | DATE | Due date |
| `data_pagamento` | DATE | Payment date (null if unpaid) |
| `valor_parcela` | DECIMAL | Installment value |
| `valor_pago` | DECIMAL | Amount paid |
| `name_slug` | STRING | Partner identifier |

---

## Setup and Installation

### Prerequisites

- Python 3.11+
- DuckDB database with the required views

### Installation

```bash
# Clone and enter directory
cd cacau_show_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
# Path to the DuckDB database file
DUCKDB_PATH=/path/to/your/cashu.duckdb
```

### Running

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DUCKDB_PATH` | Yes | Absolute path to the DuckDB database file |

### Theme Customization

Edit `styles.py` to modify:

- **Colors**: `COLORS` dictionary with primary, secondary, accent, and background colors
- **CSS**: `get_custom_css()` returns the full Streamlit CSS override
- **Typography**: Uses "Red Hat Display" font family

---

## Extending the Application

### Adding a New Section

1. **Create the SQL query** in `queries.py`:
   ```python
   def get_new_metric_query(month: int, year: int) -> str:
       return f"""
           SELECT ...
           FROM gold.movimentacoes_cacau_show_analytics
           WHERE mes = {month} AND ano = {year}
       """
   ```

2. **Create the render function** in `app.py`:
   ```python
   def _render_new_section() -> None:
       inicio = st.session_state.reference_date
       st.subheader("New Section Title")
       
       sql = queries.get_new_metric_query(inicio.month, inicio.year)
       df = run_query(sql, db_path=st.session_state.db_path)
       
       if df.empty:
           st.info("Sem dados para o período.")
           return
       
       # Transform and display...
       st.plotly_chart(fig)
   ```

3. **Add to page orchestrator**:
   ```python
   def render_sumario_geral() -> None:
       _render_numeros_gerais()
       _render_new_section()  # Add here
       # ...
   ```

### Adding a New Page

1. **Create page render function**:
   ```python
   def render_new_page() -> None:
       _render_section_a()
       _render_section_b()
   ```

2. **Add to navigation** in `_sidebar()`:
   ```python
   for _label in ["Sumário Geral", "Inadimplência", "New Page"]:
       # ...
   ```

3. **Add to page routing** in `main()`:
   ```python
   pages = {
       "Sumário Geral": render_sumario_geral,
       "Inadimplência": render_inadimplencia,
       "New Page": render_new_page,
   }
   ```

### Adding New Filters

1. Add filter widget using `chiclet_selector()` or Streamlit native widgets
2. Build SQL filter string based on selection
3. Pass filter to query function

Example pattern from `_render_breakdown_lojas()`:
```python
selector = chiclet_selector(options=["All", "A", "B"], key="my_filter")
filter_sql = f"AND column = '{selector}'" if selector != "All" else ""
sql = queries.get_query(month, year, filter_sql)
```

---

## Key Patterns

### DataFrame Transformations

The app uses pandas for minimal post-query transformations:

- **`melt()`**: Convert wide format to long format for pivoting
- **`pivot()`**: Reshape data for multi-level column headers
- **`swaplevel()`**: Reorder MultiIndex column levels
- **`reindex()`**: Ensure consistent column ordering

### Vintage Analysis (MOB Charts)

MOB = "Months on Books" - measures cohort performance over time.

The vintage charts use:
1. SQL CTEs to calculate vintage (cohort month) and MOB
2. `build_vintage_line()` helper to create Plotly figures
3. Color gradient based on vintage age (older = lighter)

### Table Rendering

`render_table_with_merged_headers()` creates HTML tables with:
- Multi-level headers (2 or 3 levels)
- DataTables.js for sorting
- Custom styling matching the app theme
- "Total" row pinned to footer

---

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web framework |
| duckdb | Database engine |
| pandas | Data manipulation |
| plotly | Interactive charts |
| streamlit-plotly-events | Click events on Plotly charts |
| python-dotenv | Environment configuration |

---

## Troubleshooting

### Common Issues

1. **"No data for period"**: Check if the selected date has data in the database
2. **Slow queries**: The database views should be pre-materialized; check DuckDB query plans
3. **Style issues**: Clear Streamlit cache with `st.cache_data.clear()`

### Debug Mode

Add to see raw DataFrames:
```python
st.dataframe(df)  # Before any transformation
```
