# CashU | Cacau Show Design System

This document defines the visual language and interaction patterns for the CashU | Cacau Show dashboard. It serves as the source of truth for all UI decisions.

---

## Table of Contents

1. [Foundation Tokens](#1-foundation-tokens)
   - [Colors](#colors)
   - [Typography](#typography)
   - [Spacing](#spacing)
2. [Components](#2-components)
   - [Chiclet Selector](#chiclet-selector)
   - [Data Tables](#data-tables)
   - [Sidebar Navigation](#sidebar-navigation)
   - [KPI Metrics](#kpi-metrics)
3. [Charts](#3-charts)
   - [Color Palette](#chart-color-palette)
   - [Layout Defaults](#chart-layout-defaults)
   - [Chart Types](#chart-types)
4. [States and Feedback](#4-states-and-feedback)
   - [Empty States](#empty-states)
   - [Loading States](#loading-states)
   - [Error States](#error-states)
   - [Interactive States](#interactive-states)
5. [Layout Patterns](#5-layout-patterns)
   - [Page Structure](#page-structure)
   - [Column Layouts](#column-layouts)
   - [Section Organization](#section-organization)
6. [Accessibility](#6-accessibility)
   - [Color Contrast](#color-contrast)
   - [Keyboard Navigation](#keyboard-navigation)
   - [Screen Reader Support](#screen-reader-support)

---

## 1. Foundation Tokens

### Colors

The color palette is defined in `styles.py` and uses warm, energetic tones aligned with the Cacau Show brand.

#### Primary Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#f5c344` | Warm yellow - highlights, active states, primary buttons, table headers |
| `secondary` | `#903aff` | Purple - charts, links, section headers, secondary highlights |
| `accent` | `#ff8a00` | Orange - call-to-action, KPI values, emphasis |
| `danger` | `#cc3366` | Pink/red - alerts, warnings, negative indicators |

#### Background Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `bg_dark` | `#1a1a1a` | Off-black - reserved for dark mode or contrast elements |
| `bg_mid` | `#3b3b3b` | Medium gray - cards, containers (dark contexts) |
| `bg_light` | `#f7f7f7` | Light surface - main background, chart backgrounds |
| `bg_white` | `#FFFFFF` | Pure white - cards, modals, secondary background |

#### Text Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `text_primary` | `#000000` | Main text, headings, labels |
| `text_secondary` | `#555555` | Muted text, captions, hints |

#### Table Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `table_header` | `#f5c344` | Table header background |
| `table_header_text` | `#1a1a1a` | Table header text |
| `table_border` | `#e0e0e0` | Cell borders, dividers |
| `table_hover` | `#fff3d6` | Row hover state |
| `table_stripe` | `#fafafa` | Alternating row background |
| `table_total` | `#f0f0f0` | Total row background |

#### Semantic Usage Guidelines

- **Primary (Yellow)**: Use for interactive elements that need attention - selected buttons, active navigation, table headers
- **Secondary (Purple)**: Use for branding elements and visual hierarchy - section titles, links, chart accents
- **Accent (Orange)**: Use sparingly for maximum impact - KPI values, important metrics, CTAs
- **Danger (Red/Pink)**: Reserve for negative states only - errors, delinquency warnings, critical alerts

### Typography

The dashboard uses **Red Hat Display** as the primary typeface, imported via Google Fonts.

```css
@import url('https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800&display=swap');
```

#### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | 32px | 800 | 1.2 | Page title (`h1`) |
| Heading | 24px | 700 | 1.3 | Section headers (`h2`) |
| Subheading | 18px | 600 | 1.4 | Subsection headers (`h3`) |
| Body | 14px | 400 | 1.5 | Default paragraph text |
| Caption | 12px | 400 | 1.4 | Labels, hints, `st.caption()` |
| Small | 11px | 400 | 1.3 | Compact tables, dense data |

#### Font Weight Reference

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text, captions |
| Medium | 500 | Sidebar buttons, form labels |
| Semibold | 600 | Subheadings, table headers |
| Bold | 700 | Section headers, emphasis |
| Extrabold | 800 | Page titles, hero text |

### Spacing

The spacing system uses a 4px base unit for consistent rhythm.

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Minimal gaps, icon padding |
| `sm` | 8px | Tight spacing, button padding |
| `md` | 16px | Default spacing, card padding |
| `lg` | 24px | Section margins, larger gaps |
| `xl` | 32px | Page margins, major sections |
| `2xl` | 48px | Large section breaks |

#### Application Examples

```css
/* Button padding */
padding: 8px 16px;  /* sm horizontal, md vertical */

/* Card padding */
padding: 16px;  /* md all around */

/* Section margin */
margin-top: 32px;  /* xl before new section */

/* Chart margins */
margin: dict(l=40, r=16, t=40, b=40)  /* Plotly format */
```

---

## 2. Components

### Chiclet Selector

A toggle button group for filtering data. Defined in `components/chiclet.py`.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `options` | `List[str]` | Required | List of selectable options |
| `key` | `str` | Required | Unique Streamlit session key |
| `default` | `str` | First option | Initially selected value |
| `label` | `str` | `""` | Optional label (radio variant) |
| `variant` | `str` | `"radio"` | `"radio"` or `"buttons"` |
| `group_max_fraction` | `float` | `0.25` | Max width fraction (buttons) |
| `buttons_per_row` | `int` | `999` | Buttons per row (buttons) |

#### Variants

**Radio Variant**: Compact, keyboard-accessible horizontal radio buttons.

```python
chiclet_selector(
    options=["Option A", "Option B", "Option C"],
    key="my_filter",
    variant="radio"
)
```

**Buttons Variant**: Styled button group with primary/secondary states.

```python
chiclet_selector(
    options=["Todos", "A", "B", "C", "D", "E"],
    key="tier_filter",
    variant="buttons",
    group_max_fraction=0.5  # Takes up half the page width
)
```

#### Styling

Selected buttons use `primary` color with dark text. Unselected buttons are transparent with border.

```css
/* Selected */
background-color: #f5c344;
color: #000000;
border: 1px solid #f5c344;

/* Unselected */
background-color: transparent;
color: #000000;
border: 1px solid #e0e0e0;
```

### Data Tables

Rich data tables with merged headers, sorting, and theming. Defined in `components/table.py`.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `df_pivot` | `pd.DataFrame` | Required | DataFrame with MultiIndex columns |
| `index_label` | `str` | `"Forma de Pagamento"` | Label for index column |
| `show_percent` | `bool` | `True` | Show percentage of column total |
| `table_id` | `str` | `"data-table"` | HTML table ID |
| `column_width_overrides` | `dict` | `None` | Custom column widths |
| `frame_width` | `int` | `None` | Fixed iframe width (px) |
| `container_css_width` | `str` | `None` | CSS width for container |

#### Features

- **Merged Headers**: Supports 2-level and 3-level MultiIndex columns
- **Sorting**: Click column headers to sort (DataTables integration)
- **Total Row**: Pinned to bottom in `<tfoot>`, unaffected by sorting
- **Percentage Display**: Shows value + percentage of column total
- **Hover States**: Row highlighting on hover

#### Usage Example

```python
from components import render_table_with_merged_headers

# Create pivot table with MultiIndex
df_pivot = df.pivot(
    index='forma_pagamento',
    columns=['status', 'tipo'],
    values=['financeiro', 'numero_compras']
)

render_table_with_merged_headers(
    df_pivot,
    index_label="Forma de Pagamento",
    show_percent=True
)
```

#### Visual Structure

```
+------------------+---------------+---------------+
| Forma de         |    Status A   |    Status B   |  <- Level 0 (merged)
| Pagamento        +-------+-------+-------+-------+
|                  | R$    | #     | R$    | #     |  <- Level 1
+------------------+-------+-------+-------+-------+
| Cartao           | 1,000 | 50    | 2,000 | 100   |
| Boleto           | 500   | 25    | 800   | 40    |
+------------------+-------+-------+-------+-------+
| Total            | 1,500 | 75    | 2,800 | 140   |  <- tfoot (pinned)
+------------------+-------+-------+-------+-------+
```

### Sidebar Navigation

Custom navigation using styled buttons in the sidebar.

#### Pattern

```python
# In sidebar
st.sidebar.divider()
for _label in ["Sumário Geral", "Inadimplência"]:
    if st.session_state.page == _label:
        # Selected state - styled text
        st.sidebar.markdown(
            f"<div class='nav-selected'>{_label}</div>",
            unsafe_allow_html=True
        )
    else:
        # Unselected state - clickable button
        if st.sidebar.button(_label, key=f"nav-{_label}"):
            st.session_state.page = _label
            st.rerun()
```

#### Styling

```css
/* Unselected navigation button */
[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    border: 0;
    color: #000000;
    font-weight: 500;
}

/* Hover state */
[data-testid="stSidebar"] .stButton > button:hover {
    text-decoration: underline;
    color: #903aff;
}

/* Selected state */
.nav-selected {
    font-weight: 700;
    text-decoration: underline;
    color: #903aff;
}
```

### KPI Metrics

Use Streamlit's native `st.metric()` with custom styling.

#### Usage

```python
st.metric(
    label="Total Clientes",
    value="12,345",
    delta="+5.2%"
)
```

#### Styling

```css
[data-testid="stMetricValue"] {
    color: #ff8a00;  /* accent color */
    font-weight: 700;
}

[data-testid="stMetricLabel"] {
    color: #555555;  /* text_secondary */
    font-weight: 500;
}
```

---

## 3. Charts

All charts use Plotly with consistent theming defined in `app.py`.

### Chart Color Palette

The chart color sequence is derived from the main color palette:

```python
PLOTLY_COLORWAY = [
    "#903aff",  # secondary (purple) - primary series
    "#ff8a00",  # accent (orange) - secondary series
    "#f5c344",  # primary (yellow) - tertiary series
    "#cc3366",  # danger (pink/red) - quaternary series
]
```

For vintage/line charts with multiple series, colors are generated by adjusting brightness:

```python
def adjust_color(hex_color: str, factor: float) -> str:
    # factor < 1.0 = darker, factor > 1.0 = lighter
    # Used to create gradient of shades for vintage analysis
```

### Chart Layout Defaults

Apply these settings to all Plotly figures:

```python
fig.update_layout(
    # Dimensions
    height=420,
    margin=dict(l=40, r=16, t=40, b=40),
    
    # Colors
    paper_bgcolor="#f7f7f7",  # bg_light
    plot_bgcolor="#f7f7f7",   # bg_light
    
    # Typography
    font=dict(
        family="Red Hat Display, sans-serif",
        color="#000000",  # text_primary
        size=12
    ),
    
    # Axis styling
    xaxis=dict(
        showgrid=False,
        tickfont=dict(family="Red Hat Display, sans-serif", size=12)
    ),
    yaxis=dict(
        gridcolor="#e0e0e0",  # table_border
        tickfont=dict(family="Red Hat Display, sans-serif", size=12)
    ),
    
    # Legend
    legend_title_text="Legenda",
    
    # Template
    template="plotly_white"
)
```

### Chart Types

#### Line Charts (Time Series)

Used for evolution and vintage analysis.

```python
fig = px.line(
    df_long,
    x="date",
    y="valor",
    color="categoria",
    color_discrete_sequence=PLOTLY_COLORWAY,
    template="plotly_white"
)
```

#### Bar Charts (Distributions)

Used for histograms and categorical comparisons.

```python
fig = go.Figure(
    data=[go.Bar(
        x=x_vals,
        y=y_vals,
        marker=dict(
            color="#f5c344",  # primary
            line=dict(color="#333", width=0.6)
        )
    )]
)
```

#### Histogram (Credit Distribution)

```python
fig = px.histogram(
    df,
    x="percentual_utilizado_pct",
    nbins=30,
    range_x=[0, 100],
    template="plotly_white",
    log_y=True,
    color_discrete_sequence=["#f5c344"]
)
```

### Rendering Charts

Always use `st.plotly_chart()` with consistent options:

```python
st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)
```

---

## 4. States and Feedback

### Empty States

When no data is available for a query, use `st.info()` with a clear Portuguese message:

```python
if df.empty:
    st.info("Sem dados para o período selecionado.")
    return
```

#### Guidelines

- Keep messages concise and in Portuguese
- Explain what's missing, not technical details
- Use `st.info()` for neutral empty states
- Place early in the function to avoid rendering partial content

### Loading States

Streamlit handles loading states automatically. For long-running queries, consider:

```python
with st.spinner("Carregando dados..."):
    df = run_query(sql, db_path=db_path)
```

### Error States

For error conditions, use `st.error()` or `st.warning()`:

```python
# Critical error
st.error("Erro ao conectar com o banco de dados.")

# Warning (recoverable)
st.warning("Alguns dados podem estar incompletos.")
```

### Interactive States

#### Chiclet Buttons

| State | Background | Border | Text Color |
|-------|-----------|--------|------------|
| Default | transparent | `#e0e0e0` | `#000000` |
| Hover | transparent | `#e0e0e0` | `#000000` |
| Selected | `#f5c344` | `#f5c344` | `#000000` |

#### Navigation Items

| State | Style |
|-------|-------|
| Default | Regular weight, no decoration |
| Hover | Underline, purple text |
| Selected | Bold, underline, purple text |

#### Table Rows

| State | Background |
|-------|-----------|
| Default (odd) | `#FFFFFF` |
| Default (even) | `#fafafa` |
| Hover | `#fff3d6` |
| Total row | `#f0f0f0` |

#### General Buttons

| State | Effect |
|-------|--------|
| Hover | `translateY(-1px)`, shadow |
| Active | `background-color: #ff8a00` |

---

## 5. Layout Patterns

### Page Structure

```
+------------------------------------------+
|  SIDEBAR          |  MAIN CONTENT        |
|                   |                      |
|  [Logo/Title]     |  [Page Title]        |
|  [Date Picker]    |                      |
|  [Divider]        |  [Section 1]         |
|  [Nav Item 1]     |    - Filters         |
|  [Nav Item 2]     |    - Content         |
|                   |                      |
|                   |  [Section 2]         |
|                   |    - Charts/Tables   |
+------------------------------------------+
```

### Column Layouts

#### Three-Column Metrics

```python
col_totais, col_hab, col_tier = st.columns([0.45, 0.55, 1.0])
```

Use for displaying related metrics with different widths.

#### Two-Column Charts

```python
col1, col2 = st.columns(2)
with col1:
    st.caption("Chart A")
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.caption("Chart B")
    st.plotly_chart(fig2, use_container_width=True)
```

Equal-width columns for side-by-side comparisons.

#### Filter Row (Chiclet with Constrained Width)

```python
chiclet_selector(
    options=["A", "B", "C"],
    key="filter",
    variant="buttons",
    group_max_fraction=0.5  # Takes 50% of page width
)
```

### Section Organization

Each page section follows this pattern:

```python
def _render_section_name() -> None:
    """Render the 'Section Name' section."""
    
    # 1. Section header
    st.subheader("Section Name")
    
    # 2. Filters (if any)
    filter_value = chiclet_selector(...)
    
    # 3. Data query
    sql = queries.get_section_query(...)
    df = run_query(sql, db_path=st.session_state.db_path)
    
    # 4. Empty state check
    if df.empty:
        st.info("Sem dados para o período.")
        return
    
    # 5. Data transformation
    df_pivot = df.pivot(...)
    
    # 6. Render content
    render_table_with_merged_headers(df_pivot)
    # or st.plotly_chart(fig, ...)
```

---

## 6. Accessibility

### Color Contrast

Ensure text meets WCAG 2.1 AA standards (4.5:1 for normal text, 3:1 for large text).

| Combination | Ratio | Status |
|-------------|-------|--------|
| Black on White | 21:1 | Pass |
| Black on Yellow (#f5c344) | 13.8:1 | Pass |
| Black on Light Gray (#f7f7f7) | 18.5:1 | Pass |
| Purple (#903aff) on White | 4.8:1 | Pass |
| Orange (#ff8a00) on White | 3.1:1 | Pass (large text only) |

#### Recommendations

- Use `text_primary` (#000000) for all body text
- Avoid orange text on light backgrounds for small text
- Ensure chart legends use sufficient contrast

### Keyboard Navigation

#### Chiclet Selector

- **Radio variant**: Native keyboard support (arrow keys)
- **Buttons variant**: Tab to navigate, Enter/Space to select

#### Tables

- DataTables provides keyboard navigation for sorting
- Tab order follows visual order

#### Sidebar Navigation

- Buttons are focusable and activatable via Enter

### Screen Reader Support

#### Best Practices

1. **Use semantic HTML**: Tables use proper `<thead>`, `<tbody>`, `<tfoot>`
2. **Add title attributes**: All table cells include `title` for tooltips
3. **Descriptive captions**: Use `st.caption()` before charts/tables
4. **Meaningful labels**: Form inputs have associated labels

#### Chart Accessibility

Since Plotly charts are SVG-based, provide text alternatives:

```python
st.caption("Distribuição de Clientes com Crédito que Compraram no Período")
# Chart follows with visual representation of the described data
```

### Focus Indicators

Ensure visible focus states for all interactive elements:

```css
/* Input focus */
.stDateInput > div > div > input:focus {
    border-color: #903aff;
    box-shadow: 0 0 0 2px rgba(144, 58, 255, 0.2);
}

/* Button focus */
.stButton > button:focus {
    outline: 2px solid #903aff;
    outline-offset: 2px;
}
```

---

## Quick Reference

### Color Variables (CSS)

```css
:root {
    --primary-color: #f5c344;
    --secondary-color: #903aff;
    --accent-color: #ff8a00;
}
```

### Python Imports

```python
from styles import get_custom_css, COLORS, get_table_styles
from components import render_table_with_merged_headers
from components.chiclet import chiclet_selector
```

### Plotly Theme Setup

```python
PLOTLY_COLORWAY = [COLORS["secondary"], COLORS["accent"], COLORS["primary"], COLORS["danger"]]

fig.update_layout(
    paper_bgcolor=COLORS["bg_light"],
    plot_bgcolor=COLORS["bg_light"],
    font=dict(family="Red Hat Display, sans-serif", color=COLORS["text_primary"])
)
```

---

*Last updated: January 2026*
