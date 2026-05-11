# White-Label Dashboard Template

A reusable Streamlit dashboard template for Snowflake-hosted applications.

## Overview

This template allows rapid creation of new dashboards while preserving:
- Visual identity (colors, fonts, layouts)
- Chart styles and interactions
- Component behavior
- Snowflake integration

## Folder Structure

```
whitelabel_dashboard/
├── app.py                    # Main entry point (DO NOT MODIFY)
├── config.py                 # Snowflake connection config
├── shared/                   # LOCKED - Do not modify for new dashboards
│   ├── __init__.py
│   ├── styles.py             # Colors, CSS, table styles
│   ├── db.py                 # Snowflake connection layer
│   └── components/
│       ├── __init__.py
│       ├── table.py          # Merged-header table component
│       ├── chiclet.py        # Filter button selector
│       └── charts.py         # Chart builders and colorway
├── dashboard/                # EDIT THESE for each new dashboard
│   ├── __init__.py
│   ├── dashboard_config.py   # Dashboard title, pages, filters
│   ├── queries.py            # SQL queries (main customization point)
│   └── sections.py           # Section render functions
└── README.md
```

## Quick Start: Creating a New Dashboard

### Step 1: Copy the Template

```bash
cp -r whitelabel_dashboard/ my_new_dashboard/
```

### Step 2: Edit Dashboard Configuration

Edit `dashboard/dashboard_config.py`:

```python
# Change these values
DASHBOARD_TITLE = "My New Dashboard"
PAGES = ["Summary", "Details"]
DEFAULT_PAGE = "Summary"
DATE_MIN = date(2024, 1, 1)
```

### Step 3: Update SQL Queries

Edit `dashboard/queries.py`:

```python
# Update table references
MAIN_TABLE = "MY_SCHEMA.MY_TABLE"
RECEIVABLES_TABLE = "MY_SCHEMA.MY_RECEIVABLES"

# Modify queries as needed for your data schema
```

### Step 4: Configure Snowflake (Local Development)

Create a `.env` file in the dashboard folder:

```env
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

### Step 5: Run the Dashboard

```bash
cd my_new_dashboard
streamlit run app.py
```

## File Edit Rules

| File | Safe to Edit? | Purpose |
|------|---------------|---------|
| `shared/*` | **NO** | Visual identity, components |
| `dashboard/dashboard_config.py` | **YES** | Titles, pages, filters |
| `dashboard/queries.py` | **YES** | SQL queries, table refs |
| `dashboard/sections.py` | **CAREFUL** | Section logic (rarely needed) |
| `app.py` | **NO** | Entry point orchestration |
| `config.py` | **YES** | Snowflake credentials |

## What to Change for New Dashboards

### Always Change

1. **`dashboard/dashboard_config.py`**
   - `DASHBOARD_TITLE` - Browser tab and header title
   - `PAGES` - List of available pages
   - `DATE_MIN` - Minimum date for date picker

2. **`dashboard/queries.py`**
   - `MAIN_TABLE` - Your main data table
   - `RECEIVABLES_TABLE` - Your receivables table (if applicable)
   - SQL query functions - Adapt to your schema

### Sometimes Change

3. **`dashboard/sections.py`** (only if needed)
   - Metric labels and names
   - Filter options
   - Add/remove sections

### Never Change

4. **`shared/` folder** - Contains visual identity
5. **`app.py`** - Entry point structure

## Guardrails

### Must NOT Change (Visual Consistency)

- `COLORS` dict in `shared/styles.py`
- `get_custom_css()` output
- `PLOTLY_COLORWAY` in `shared/components/charts.py`
- Chart layout configs (margins, fonts, backgrounds)
- Table component styling

### Safe to Change Per Dashboard

- Dashboard title and pages
- SQL queries and table references
- Metric labels and filter options
- Section visibility (which sections to render)

## Common Customizations

### Adding a New Page

1. Add page name to `PAGES` in `dashboard/dashboard_config.py`
2. Create render function in `dashboard/sections.py`:
   ```python
   def render_my_new_page() -> None:
       st.subheader("My New Section")
       # ... your code
   ```
3. Add to page routing in `app.py`:
   ```python
   pages = {
       "Sumário Geral": render_sumario_geral,
       "Inadimplência": render_inadimplencia,
       "My New Page": render_my_new_page,  # Add this
   }
   ```

### Changing Metric Labels

Edit `METRIC_LABELS` in `dashboard/dashboard_config.py`:

```python
METRIC_LABELS = {
    "financeiro": "Revenue",
    "numero_compras": "# Purchases",
    # ...
}
```

### Adding a New Filter

1. Add options to `dashboard/dashboard_config.py`:
   ```python
   MY_FILTER_OPTIONS = ["All", "Option A", "Option B"]
   ```

2. Use in `dashboard/sections.py`:
   ```python
   from .dashboard_config import MY_FILTER_OPTIONS
   
   selector = chiclet_selector(
       options=MY_FILTER_OPTIONS,
       key="my_filter",
       default="All",
       variant="buttons",
   )
   ```

## Snowflake Deployment

When deploying to Snowflake Streamlit:

1. The `shared/db.py` automatically detects the Snowflake environment
2. No `.env` file needed - uses Snowpark Session
3. Upload all files maintaining the folder structure
4. Set `app.py` as the main file

## Troubleshooting

### Import Errors

Ensure you're running from the dashboard root folder:
```bash
cd whitelabel_dashboard  # or your dashboard folder
streamlit run app.py
```

### Missing Data

1. Check `MAIN_TABLE` and `RECEIVABLES_TABLE` in `queries.py`
2. Verify Snowflake credentials in `.env` (local) or Snowpark session (hosted)
3. Check date range - data may not exist for selected period

### Visual Inconsistencies

If visuals don't match the original:
1. Verify you haven't modified files in `shared/`
2. Check browser cache - try hard refresh (Ctrl+Shift+R)
3. Ensure `get_custom_css()` is called in `app.py`
