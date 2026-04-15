# White-Label Dashboard Design System

## Industry-Standard Documentation for Streamlit Dashboard Development

**Version:** 2.0.0
**Last Updated:** April 2026
**Status:** Production-Ready | Agent-Compatible | Figma-Integrated

---

## Document Purpose

This design system serves as the **single source of truth** for all visual, interaction, and data visualization decisions for the white-label Streamlit dashboard template. The dashboard title and branding are configurable via `dashboard/dashboard_config.py`. This document is structured to:

1. **Enable agent-based code generation** through machine-readable token formats (W3C DTCG compliant)
2. **Support Figma integration** via design token synchronization
3. **Follow validated principles** from "Storytelling with Data" by Cole Nussbaumer Knaflic
4. **Maintain industry standards** for enterprise dashboard design

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Design Tokens](#2-design-tokens)
3. [Data Visualization Principles](#3-data-visualization-principles)
4. [Component Library](#4-component-library)
5. [Chart Guidelines](#5-chart-guidelines)
6. [Layout & Composition](#6-layout--composition)
7. [Accessibility Standards](#7-accessibility-standards)
8. [Performance & Optimization](#8-performance--optimization)
9. [Figma Integration](#9-figma-integration)
10. [Agent Implementation Guide](#10-agent-implementation-guide)
11. [Versioning & Governance](#11-versioning--governance)

---

## 1. Design Philosophy

### Core Principles

The design system is built on validated data visualization principles from Cole Nussbaumer Knaflic's "Storytelling with Data":

#### 1.1 Context-Driven Design

- **Understand the audience:** Business analysts need actionable insights, not raw data
- **Define the message:** Every dashboard section must answer a specific business question
- **Focus on explanatory data:** Remove exploratory elements that don't support decision-making

#### 1.2 Maximize Data-Ink Ratio

Following Edward Tufte's principle: maximize the proportion of ink devoted to data representation.

**Implementation:**

- Remove unnecessary chart borders
- Minimize gridlines (use light gray, horizontal only when necessary)
- Eliminate redundant data markers
- Direct label data points instead of using separate legends where possible
- Use whitespace strategically

#### 1.3 Eliminate Clutter

Apply Gestalt principles to reduce cognitive load:

- **Proximity:** Group related elements
- **Similarity:** Use consistent styling for related data
- **Enclosure:** Use subtle backgrounds to define sections
- **Continuity:** Create natural reading flow from top-left to bottom-right

#### 1.4 Guide Attention with Preattentive Attributes

Use visual properties that are processed instantly:

- **Color:** Reserve brand colors for emphasis (primary yellow for active states, orange for KPIs)
- **Size:** Larger elements indicate importance (KPI values > supporting text)
- **Position:** Top-left placement for critical metrics
- **Contrast:** Bold weights for emphasis, regular for body text

#### 1.5 Tell a Story

Structure dashboards with narrative flow:

- **Beginning:** Overview KPIs establish context
- **Middle:** Detailed breakdowns explore the problem
- **End:** Actionable insights and recommendations

---

## 2. Design Tokens

### 2.1 Token Architecture

The design token system follows the **W3C Design Tokens Community Group (DTCG)** specification with three tiers:

```
Primitive Tokens → Semantic Tokens → Component Tokens
(Base values)      (Purpose-driven)   (Component-specific)
```

The canonical token file lives at `design_tokens.json` in the project root. The Python runtime reads from `shared/styles.py`, where the `COLORS` dict is kept **flat** for composability — the three-tier hierarchy lives exclusively in `design_tokens.json`.

### 2.2 Token Format (Agent-Compatible)

All tokens use the standard DTCG format with `$type`, `$value`, and `$description` properties:

```json
{
  "color-background-primary": {
    "$type": "color",
    "$value": "#f7f7f7",
    "$description": "Main application background surface"
  }
}
```

**Token Naming Convention:**

```
{category}-{purpose}-{variant}-{state}

Examples:
- color-background-primary
- color-interactive-primary-hover
- spacing-component-card-padding
- typography-heading-level1-size
```

### 2.3 Color Tokens

#### Primitive Colors

```json
{
  "color.primitive.brand.warmYellow":  {"$value": "#f5c344", "$type": "color"},
  "color.primitive.brand.violet":      {"$value": "#903aff", "$type": "color"},
  "color.primitive.brand.orange":      {"$value": "#ff8a00", "$type": "color"},
  "color.primitive.feedback.danger":   {"$value": "#cc3366", "$type": "color"},
  "color.primitive.neutral.gray100":   {"$value": "#f7f7f7", "$type": "color"},
  "color.primitive.neutral.gray200":   {"$value": "#e0e0e0", "$type": "color"},
  "color.primitive.neutral.gray600":   {"$value": "#555555", "$type": "color"},
  "color.primitive.neutral.black":     {"$value": "#000000", "$type": "color"},
  "color.primitive.neutral.white":     {"$value": "#FFFFFF", "$type": "color"},
  "color.primitive.neutral.gray950":   {"$value": "#1a1a1a", "$type": "color"},
  "color.primitive.neutral.gray700":   {"$value": "#3b3b3b", "$type": "color"},
  "color.primitive.neutral.gray150":   {"$value": "#f0f0f0", "$type": "color"},
  "color.primitive.neutral.gray50":    {"$value": "#fafafa", "$type": "color"},
  "color.primitive.surface.creamHover":{"$value": "#fff3d6", "$type": "color"}
}
```

#### Semantic Color Tokens

Semantic aliases map 1:1 with the `COLORS` dict in `shared/styles.py`:

```json
{
  "color.semantic.primary":          {"$value": "{color.primitive.brand.warmYellow}"},
  "color.semantic.secondary":        {"$value": "{color.primitive.brand.violet}"},
  "color.semantic.accent":           {"$value": "{color.primitive.brand.orange}"},
  "color.semantic.danger":           {"$value": "{color.primitive.feedback.danger}"},
  "color.semantic.bg_light":         {"$value": "{color.primitive.neutral.gray100}"},
  "color.semantic.bg_white":         {"$value": "{color.primitive.neutral.white}"},
  "color.semantic.text_primary":     {"$value": "{color.primitive.neutral.black}"},
  "color.semantic.text_secondary":   {"$value": "{color.primitive.neutral.gray600}"},
  "color.semantic.table_header":     {"$value": "{color.primitive.brand.warmYellow}"},
  "color.semantic.table_header_text":{"$value": "{color.primitive.neutral.gray950}"},
  "color.semantic.table_border":     {"$value": "{color.primitive.neutral.gray200}"},
  "color.semantic.table_hover":      {"$value": "{color.primitive.surface.creamHover}"},
  "color.semantic.table_stripe":     {"$value": "{color.primitive.neutral.gray50}"},
  "color.semantic.table_total":      {"$value": "{color.primitive.neutral.gray150}"},
  "color.semantic.table_total_text": {"$value": "{color.primitive.neutral.gray950}"}
}
```

#### Python Runtime — `COLORS` dict (`shared/styles.py`)

```python
COLORS = {
    "primary": "#f5c344",
    "secondary": "#903aff",
    "accent": "#ff8a00",
    "danger": "#cc3366",
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
    "table_total_text": "#1a1a1a",
}
```

#### Chart Color Sequence

Defined in `shared/components/charts.py`:

```python
PLOTLY_COLORWAY = [COLORS["secondary"], COLORS["accent"], COLORS["primary"], COLORS["danger"]]
# Resolves to: ["#903aff", "#ff8a00", "#f5c344", "#cc3366"]
```

**Usage Guidelines:**

- Use sequential shades for time-series with multiple cohorts
- Apply diverging colors for positive/negative comparisons
- Maintain 4.5:1 contrast ratio with backgrounds (WCAG AA)

#### Accessibility-First Color Validation

All color combinations must pass WCAG 2.1 AA standards:

| Foreground | Background | Ratio | Status | Use Case |
|------------|------------|-------|--------|----------|
| #000000 | #FFFFFF | 21:1 | ✅ AAA | Body text |
| #000000 | #f5c344 | 13.8:1 | ✅ AAA | Button text on primary |
| #903aff | #FFFFFF | 4.8:1 | ✅ AA | Links, interactive text |
| #ff8a00 | #FFFFFF | 3.1:1 | ⚠️ Large text only | KPI values (≥18px) |
| #555555 | #FFFFFF | 7.5:1 | ✅ AAA | Secondary body text |
| #1a1a1a | #f5c344 | 12.5:1 | ✅ AAA | Table header text |

### 2.4 Spacing Tokens

Based on 4px base unit for consistent rhythm. Defined in both `design_tokens.json` and `shared/styles.py`:

```json
{
  "spacing-xs":  {"$value": "4px",  "$type": "dimension"},
  "spacing-sm":  {"$value": "8px",  "$type": "dimension"},
  "spacing-md":  {"$value": "16px", "$type": "dimension"},
  "spacing-lg":  {"$value": "24px", "$type": "dimension"},
  "spacing-xl":  {"$value": "32px", "$type": "dimension"},
  "spacing-2xl": {"$value": "48px", "$type": "dimension"}
}
```

```python
# shared/styles.py
SPACING = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "2xl": 48}
```

**Component-Specific Spacing:**

```json
{
  "spacing-component-button-padding-x": {"$value": "{spacing-md}"},
  "spacing-component-button-padding-y": {"$value": "{spacing-sm}"},
  "spacing-component-card-padding":     {"$value": "{spacing-md}"},
  "spacing-layout-section-margin":      {"$value": "{spacing-xl}"},
  "spacing-chart-margin-left":          {"$value": "40px"},
  "spacing-chart-margin-right":         {"$value": "16px"}
}
```

### 2.5 Typography Tokens

**Font Family:**

```json
{
  "typography-fontFamily-primary": {
    "$value": ["Red Hat Display", "sans-serif"],
    "$type": "fontFamily",
    "$description": "Primary typeface for all UI elements"
  }
}
```

**Type Scale:**

```json
{
  "typography-fontSize-display":    {"$value": "32px", "$type": "dimension"},
  "typography-fontSize-title":      {"$value": "24px", "$type": "dimension"},
  "typography-fontSize-subtitle":   {"$value": "18px", "$type": "dimension"},
  "typography-fontSize-body":       {"$value": "14px", "$type": "dimension"},
  "typography-fontSize-caption":    {"$value": "12px", "$type": "dimension"},
  "typography-fontSize-micro":      {"$value": "11px", "$type": "dimension"}
}
```

**Font Weights:**

```json
{
  "typography-fontWeight-regular":   {"$value": 400, "$type": "fontWeight"},
  "typography-fontWeight-medium":    {"$value": 500, "$type": "fontWeight"},
  "typography-fontWeight-semibold":  {"$value": 600, "$type": "fontWeight"},
  "typography-fontWeight-bold":      {"$value": 700, "$type": "fontWeight"},
  "typography-fontWeight-extrabold": {"$value": 800, "$type": "fontWeight"}
}
```

**Line Heights:**

```json
{
  "typography-lineHeight-tight":   {"$value": 1.2,  "$type": "lineHeight"},
  "typography-lineHeight-snug":    {"$value": 1.25, "$type": "lineHeight"},
  "typography-lineHeight-normal":  {"$value": 1.35, "$type": "lineHeight"},
  "typography-lineHeight-relaxed": {"$value": 1.5,  "$type": "lineHeight"}
}
```

---

## 3. Data Visualization Principles

### 3.1 The Six-Step Storytelling Framework

Based on Cole Nussbaumer Knaflic's methodology:

#### Step 1: Understand the Context

**Before creating any visualization:**

- Define WHO will use the dashboard (analysts, managers, executives)
- Determine WHAT action they need to take
- Identify HOW data supports decision-making

**Implementation Checklist:**

- [ ] Audience role documented
- [ ] Key business question identified
- [ ] Success metric defined
- [ ] Update frequency established

#### Step 2: Choose Appropriate Visuals

**Visual Selection Matrix:**

| Data Type | Comparison Type | Recommended Chart | Avoid |
|-----------|----------------|-------------------|-------|
| Single value | None | KPI card with trend indicator | Gauge, speedometer |
| Categorical | Comparison | Horizontal bar chart | Pie chart (>5 categories) |
| Time series | Trend over time | Line chart | Bar chart |
| Time series | Period comparison | Grouped bar chart | Multiple line charts |
| Distribution | Frequency | Histogram | Scatter plot |
| Relationship | Correlation | Scatter plot | Pie chart |
| Part-to-whole | Composition | Stacked bar / table | Donut chart |
| Geographic | Location | Choropleth map | Table |

**Streamlit Implementation:**

```python
import plotly.express as px

# ✅ Line chart for time series
fig = px.line(df, x='date', y='revenue',
              title='Revenue Evolution',
              color_discrete_sequence=['#903aff'])

# ✅ Bar chart for categorical comparison
fig = px.bar(df, x='category', y='sales',
             title='Sales by Category',
             color_discrete_sequence=['#f5c344'])

# ❌ Avoid pie chart for many categories — use horizontal bar instead
```

#### Step 3: Eliminate Clutter

**Decluttering Checklist:**

- [ ] Remove chart border
- [ ] Remove or minimize gridlines (keep horizontal only if necessary)
- [ ] Remove data markers from line charts (unless <10 points)
- [ ] Clean up axis labels (remove redundant units)
- [ ] Label data directly (remove legend if possible)
- [ ] Use consistent color (avoid rainbow charts)

**Plotly Implementation:**

```python
fig.update_layout(
    paper_bgcolor='#f7f7f7',
    plot_bgcolor='#f7f7f7',
    xaxis=dict(
        showgrid=False,
        showline=False,
        zeroline=False
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#e0e0e0',
        gridwidth=0.5,
        showline=False,
        zeroline=False
    ),
    margin=dict(l=40, r=16, t=40, b=40),
    showlegend=False
)
```

#### Step 4: Focus Attention

**Preattentive Attributes for Emphasis:**

1. **Color Emphasis:**

```python
colors = ['#e0e0e0'] * len(df)
colors[important_index] = '#ff8a00'

fig = go.Figure(go.Bar(x=df['category'], y=df['value'],
                       marker=dict(color=colors)))
```

2. **Size Emphasis:**

```python
st.metric(
    label="Total Revenue",
    value="R$ 1.2M",
    delta="+15.3%"
)
```

3. **Position Emphasis:**

- Place most important KPIs in top-left
- Use F-pattern or Z-pattern layout
- Critical insights above-the-fold

#### Step 5: Think Like a Designer

- **Affordances:** Buttons look clickable, active filters use primary color, hover states provide feedback
- **Accessibility:** WCAG 2.1 AA compliance mandatory (4.5:1 for text, 3:1 for large text ≥18px)
- **Aesthetics:** Consistent alignment, adequate whitespace, harmonious color palette
- **Acceptance:** Standard chart types, conventional interaction patterns, familiar terminology

#### Step 6: Tell a Story

**Narrative Structure:**

**Beginning (Overview):**

```python
st.title("Dashboard Overview")
st.caption(f"Last updated: {last_update}")

col1, col2, col3 = st.columns(3)
col1.metric("Delinquency Rate", "12.3%", "-2.1%")
col2.metric("Outstanding Amount", "R$ 450K", "+5.2%")
col3.metric("Affected Clients", "1,234", "-8")
```

**Middle (Detailed Analysis):**

```python
st.subheader("Delinquency Evolution")
st.caption("Monthly comparison over the last 12 months")
st.plotly_chart(line_chart, use_container_width=True, config=PLOTLY_CONFIG)

st.subheader("Delinquency by Segment")
st.caption("Outstanding amount distribution by client tier")
st.plotly_chart(bar_chart, use_container_width=True, config=PLOTLY_CONFIG)
```

**End (Call to Action):**

```python
st.info("💡 **Recommendation:** Tier C shows the highest delinquency growth "
        "(+18% MoM). Consider reviewing credit policies for this segment.")
```

### 3.2 Chart-Specific Guidelines

#### 3.2.1 KPI Metric Cards

**Purpose:** Display single value with context

**Anatomy:**

- Large numeric value (24–32px)
- Clear label (12–14px, gray)
- Trend indicator (delta with color: green = positive, red = negative)
- Optional: Sparkline showing recent history

**Implementation:**

```python
st.metric(
    label="Total Active Clients",
    value="12,345",
    delta="+234 (+1.9%)",
    delta_color="normal"
)
```

**Best Practices:**

- Limit to 3–5 KPIs per row
- Use consistent units across related metrics
- Include comparison context (vs. last period, vs. target)
- Avoid decimals unless precision is critical

#### 3.2.2 Line Charts (Time Series)

**Purpose:** Show trends and patterns over time

**Best Practices:**

- X-axis: Date/time (continuous)
- Y-axis: Quantitative measure
- Maximum 5 lines per chart (avoid spaghetti charts)
- Use direct labels at line endpoints (not legends)
- Show data points only if ≤20 points

**Implementation:**

```python
from shared.components import get_standard_layout, PLOTLY_CONFIG, PLOTLY_COLORWAY

fig = px.line(
    df_time_series, x='date', y='value', color='category',
    color_discrete_sequence=PLOTLY_COLORWAY
)
fig.update_layout(**get_standard_layout(title="Monthly Revenue"))
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
```

**Common Mistakes to Avoid:**

- ❌ Dual Y-axes (confusing, use separate charts)
- ❌ 3D effects (distort data)
- ❌ Non-zero baseline (misleading for trends)
- ❌ Too many lines (>5 makes comparison difficult)

#### 3.2.3 Bar Charts (Categorical Comparison)

**Purpose:** Compare discrete categories

**Orientation Decision:**

- **Vertical bars:** ≤10 categories with short labels
- **Horizontal bars:** >10 categories OR long category labels

**Best Practices:**

- Sort bars by value (descending) unless natural order exists
- Start Y-axis at zero (never truncate bar charts)
- Use single color (gray) with accent color for emphasis
- Include data labels if space permits

**Implementation:**

```python
import plotly.graph_objects as go

df_sorted = df.sort_values('value', ascending=True)

fig = go.Figure(go.Bar(
    y=df_sorted['category'], x=df_sorted['value'],
    orientation='h',
    marker=dict(color='#f5c344', line=dict(color='#333', width=0.5)),
    text=df_sorted['value'],
    texttemplate='%{text:,.0f}',
    textposition='outside'
))
fig.update_layout(**get_standard_layout(
    title="Sales by Category",
    height=max(300, len(df_sorted) * 30)
))
```

#### 3.2.4 Tables (Detailed Data)

**Purpose:** Display precise values, enable comparisons

**Best Practices:**

- Limit columns to ≤8 (horizontal scrolling is bad UX)
- Right-align numeric values
- Left-align text values
- Use alternating row colors (subtle: `#fafafa`)
- Bold total rows
- Include sort functionality

**Implementation:**

```python
from shared.components import render_table_with_merged_headers

render_table_with_merged_headers(
    df_pivot,
    index_label='Payment Method',
    show_percent=True,
    table_id='payment-analysis-table'
)
```

**Styling Requirements:**

- Header background: `#f5c344` (primary yellow)
- Header text: `#1a1a1a` (dark, semibold)
- Row hover: `#fff3d6` (light yellow)
- Borders: `#e0e0e0` (light gray, 1px)
- Total row: `#f0f0f0` (medium gray, bold text)

#### 3.2.5 Histograms (Distribution)

**Purpose:** Show frequency distribution of continuous data

**Best Practices:**

- Use 10–30 bins (adjust based on data)
- Include descriptive statistics (mean, median)
- Consider log scale for skewed distributions

**Implementation:**

```python
fig = px.histogram(
    df, x='credit_utilization_pct', nbins=25,
    range_x=[0, 100],
    color_discrete_sequence=['#f5c344'],
    labels={'credit_utilization_pct': 'Credit Utilization (%)'}
)

mean_val = df['credit_utilization_pct'].mean()
fig.add_vline(x=mean_val, line_dash='dash', line_color='#903aff',
              annotation_text=f'Mean: {mean_val:.1f}%')
fig.update_layout(**get_standard_layout(title="Credit Utilization Distribution"))
```

### 3.3 Color in Data Visualization

#### 3.3.1 Color Usage Strategy

**Sequential Color Scales (Single Hue):**

```python
sequential_scale = ['#fff9e6', '#f5e5a8', '#f5c344', '#d4a935', '#b38e29']
```

**Diverging Color Scales (Two Hues):**

```python
diverging_scale = ['#2166ac', '#92c5de', '#e0e0e0', '#fdb863', '#ff8a00']
```

**Categorical Colors:**

```python
from shared.components import PLOTLY_COLORWAY
# ['#903aff', '#ff8a00', '#f5c344', '#cc3366']
```

#### 3.3.2 Colorblind-Safe Palettes

Ensure accessibility for ~8% of male population:

**Tested Color Combinations:**

- Purple (#903aff) + Orange (#ff8a00) → ✅ Deuteranopia-safe
- Yellow (#f5c344) + Purple (#903aff) → ✅ Protanopia-safe
- Avoid: Red + Green, Blue + Purple (problematic for colorblind users)

**Validation:**
Test all charts at: https://www.color-blindness.com/coblis-color-blindness-simulator/

#### 3.3.3 Semantic Color Meanings

| Color | Meaning | Usage |
|-------|---------|-------|
| Purple (#903aff) | Primary category, main data series | First line in multi-line chart |
| Orange (#ff8a00) | Secondary category, emphasis | KPI values, second series |
| Yellow (#f5c344) | Interactive, active, selected | Active button, table header |
| Pink (#cc3366) | Warning, negative, danger | Error states, negative trends |
| Gray (#555555) | Supporting, inactive, context | Non-selected items, secondary text |
| Green (outside palette) | Only for positive delta indicators | `st.metric` delta values |

---

## 4. Component Library

### 4.1 Chiclet Selector (Filter Component)

**Source:** `shared/components/chiclet.py`

**Purpose:** Toggle between mutually exclusive options

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `options` | `List[str]` | (required) | Available options |
| `key` | `str` | (required) | Unique session state key |
| `default` | `Optional[str]` | `None` (first option) | Pre-selected value |
| `label` | `str` | `""` | Visible label (radio only) |
| `variant` | `str` | `"radio"` | `"radio"` or `"buttons"` |
| `group_max_fraction` | `float` | `0.25` | Max page width for button group |
| `buttons_per_row` | `int` | `999` | Buttons per row |

#### Radio Variant

Use for: 2–4 options, keyboard navigation priority

```python
from shared.components import chiclet_selector

selected = chiclet_selector(
    options=['All', 'Active', 'Inactive'],
    key='status_filter',
    variant='radio',
    label='Client Status'
)
```

#### Buttons Variant

Use for: 5+ options, visual prominence

```python
selected = chiclet_selector(
    options=['All', 'A', 'B', 'C', 'D', 'E'],
    key='tier_filter',
    variant='buttons',
    group_max_fraction=0.5,
    buttons_per_row=6
)
```

**States:**

| State | Background | Border | Text |
|-------|-----------|--------|------|
| Default | transparent | #e0e0e0 | #000000 |
| Hover (unselected) | #fff3d6 | #f5c344 | #000000 |
| Selected | #f5c344 | #f5c344 | #000000 |
| Hover (selected) | #ff8a00 | #ff8a00 | #000000 |
| Disabled | #f7f7f7 | #e0e0e0 | #999999 |

### 4.2 Data Table Component

**Source:** `shared/components/table.py`

**Purpose:** Display tabular data with advanced features

**Features:**

- Multi-level column headers (2–3 levels supported)
- Sortable columns (click header)
- Hover highlighting
- Percentage calculations
- Fixed total row (in `<tfoot>`)
- No external CDN dependencies (Snowflake-compatible)

**Signature:**

```python
def render_table_with_merged_headers(
    df_pivot: pd.DataFrame,
    index_label: str = "Forma de Pagamento",
    show_percent: bool = True,
    table_id: str = "data-table",
    column_width_overrides: dict | None = None,
    frame_width: int | None = None,
    container_css_width: str | None = None,
) -> None:
```

**Implementation:**

```python
from shared.components import render_table_with_merged_headers

df_pivot = df.pivot_table(
    index='payment_method',
    columns=['month', 'status'],
    values='amount',
    aggfunc='sum'
)

render_table_with_merged_headers(
    df_pivot=df_pivot,
    index_label='Payment Method',
    show_percent=True,
    table_id='financial-table',
    column_width_overrides={1: '200px'}
)
```

**Styling (CSS):**

```css
thead {
    background-color: #f5c344;
    color: #1a1a1a;
    font-weight: 600;
    text-align: center;
}

tbody tr {
    border-bottom: 1px solid #e0e0e0;
}

tbody tr:nth-child(even) {
    background-color: #fafafa;
}

tbody tr:hover {
    background-color: #fff3d6;
}

tfoot {
    background-color: #f0f0f0;
    font-weight: 700;
    border-top: 2px solid #e0e0e0;
}

td, th {
    padding: 12px 16px;
    text-align: right;
}

td:first-child, th:first-child {
    text-align: left;
    font-weight: 600;
}
```

**Accessibility:**

- Proper `<thead>`, `<tbody>`, `<tfoot>` structure
- `title` attribute on cells with percentage
- Keyboard-sortable (Enter/Space on headers)
- High contrast (21:1 on white background)

### 4.3 KPI Metric Card

**Purpose:** Highlight single important value

**Anatomy:**

```
┌─────────────────────────┐
│ Label (12px, gray)      │
│ 12,345                  │ ← Value (28px, orange)
│ +234 (+1.9%) ↑          │ ← Delta (14px, semantic color)
└─────────────────────────┘
```

**Implementation:**

```python
st.metric(
    label='Total Clients',
    value='12,345',
    delta='+234',
    delta_color='normal',
    help='Active clients in selected period'
)
```

**Styling Override (from `shared/styles.py` CSS):**

```python
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 28px;
    font-weight: 700;
    color: #ff8a00;
}

[data-testid="stMetricLabel"] {
    font-size: 12px;
    font-weight: 500;
    color: #555555;
}

[data-testid="stMetricDelta"] {
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)
```

**Layout Patterns:**

```python
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Total Revenue', 'R$ 1.2M', '+15.3%')
with col2:
    st.metric('Average Ticket', 'R$ 450', '-2.1%', delta_color='inverse')
with col3:
    st.metric('Conversion', '12.8%', '+0.5pp')
```

### 4.4 Sidebar Navigation

**Purpose:** Page navigation and global filters

**Structure:**

```python
with st.sidebar:
    st.image('logo.png', width=200)
    st.divider()

    st.subheader('Filters')
    start_date = st.date_input('Start Date')
    end_date = st.date_input('End Date')

    st.divider()

    st.subheader('Navigation')
    for page in PAGES:
        if st.session_state.page == page:
            st.markdown(f'**{page}**')
        else:
            if st.button(page, key=f'nav-{page}'):
                st.session_state.page = page
                st.rerun()
```

**Styling (from `shared/styles.py`):**

```css
[data-testid="stSidebar"] {
    background-color: #f7f7f7;
    padding: 2rem 1rem;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    color: #000000;
    font-weight: 500;
}

[data-testid="stSidebar"] .stButton > button:hover {
    color: #903aff;
    text-decoration: underline;
}

[data-testid="stSidebar"] .nav-selected {
    color: #903aff;
    font-weight: 700;
    text-decoration: underline;
}
```

### 4.5 Loading States

**Purpose:** Indicate data is being fetched (>200ms operations)

**Implementation:**

```python
with st.spinner('Loading data...'):
    df = run_query(sql, db_path)

if data_loading:
    st.empty()
    st.info('📊 Generating visualization...')
else:
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
```

**Best Practices:**

- Show loading state only if operation takes >200ms
- Use skeleton screens for predictable layouts
- Provide progress indicators for long operations (>5s)
- Avoid "flash of loading content" (add 200ms delay before showing spinner)

### 4.6 Empty States

**Purpose:** Inform user when no data is available

**Implementation:**

```python
if df.empty:
    st.info('🔭 No data available for the selected period.')
    st.caption('Adjust the filters or select a different date range.')
    return
```

**Tone Guidelines:**

- Be helpful, not technical
- Explain what's missing in user terms
- Suggest action to resolve
- Use emoji sparingly for visual interest

**Examples:**

- ✅ "No data available for the selected period"
- ❌ "Query returned empty result set"

---

## 5. Chart Guidelines

### 5.1 Plotly Configuration

All charts in the white-label template share a consistent configuration defined in `shared/styles.py`:

**PLOTLY_CONFIG:**

```python
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}
```

**PLOTLY_LAYOUT:**

```python
PLOTLY_LAYOUT = {
    "height": 420,
    "margin": dict(l=40, r=16, t=40, b=40),
    "paper_bgcolor": COLORS["bg_light"],   # #f7f7f7
    "plot_bgcolor": COLORS["bg_light"],    # #f7f7f7
    "font": dict(
        family="Red Hat Display, sans-serif",
        color=COLORS["text_primary"],      # #000000
        size=12,
    ),
    "xaxis": dict(
        showgrid=False,
        showline=False,
        zeroline=False,
        tickfont=dict(size=12),
    ),
    "yaxis": dict(
        showgrid=True,
        gridcolor=COLORS["table_border"],  # #e0e0e0
        gridwidth=0.5,
        showline=False,
        zeroline=False,
        tickfont=dict(size=12),
    ),
    "showlegend": True,
    "legend": dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),
}
```

### 5.2 `get_standard_layout()` Usage

The `get_standard_layout()` function in `shared/components/charts.py` deep-copies `PLOTLY_LAYOUT` and applies common overrides:

```python
from shared.components import get_standard_layout, PLOTLY_CONFIG

fig = px.line(df, x='date', y='value')
fig.update_layout(**get_standard_layout(
    title="Monthly Revenue Trend",
    height=420,
    show_legend=True,
    legend_title="Category"
))
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
```

When `title` is empty, the function automatically shrinks the top margin to 10px.

### 5.3 Chart Titles and Labels

**Title Requirements:**

- Clear, descriptive (not vague like "Chart 1")
- Left-aligned, 18px, semibold
- Avoid abbreviations unless universally understood
- Include time period if relevant

**Examples:**

- ✅ "Monthly Revenue Evolution — Last 12 Months"
- ❌ "Revenue Chart"

**Axis Labels:**

- Include units (R$, %, un.)
- Avoid redundancy with title
- Use abbreviations for large numbers (K, M, B)
- Format consistently across the dashboard

### 5.4 Legends vs. Direct Labels

**Prefer direct labels when:**

- ≤5 categories
- Labels fit without overlap
- End-of-line labels for time series

**Use legends when:**

- >5 categories
- Interactive filtering is enabled
- Direct labels would clutter

**Implementation:**

```python
# Direct labels (preferred)
for i, row in df.iterrows():
    fig.add_annotation(
        x=row['x'], y=row['y'],
        text=row['category'],
        showarrow=False, xanchor='left', xshift=5
    )
fig.update_layout(showlegend=False)

# Legend (when necessary)
fig.update_layout(
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=-0.2)
)
```

### 5.5 Interactive Features

**Enable when:**

- Dataset is large (>100 points)
- User needs to explore subsets
- Drill-down provides value

**Disable when:**

- Clarity is paramount
- Printed/exported reports
- Simple, focused message

**Hover Templates:**

```python
fig.update_traces(
    hovertemplate='<b>%{x}</b><br>Value: R$ %{y:,.0f}<br>'
                  'Growth: %{customdata}%<extra></extra>'
)
```

---

## 6. Layout & Composition

### 6.1 Page Structure

**Standard Dashboard Layout:**

```
┌─────────────────────────────────────────────────────────┐
│ SIDEBAR              │ MAIN CONTENT                     │
│ ┌──────────────────┐ │ ┌──────────────────────────────┐ │
│ │ Logo             │ │ │ Page Title (h1)              │ │
│ │ Global Filters   │ │ │ Caption/Context              │ │
│ │                  │ │ └──────────────────────────────┘ │
│ │ Date Range       │ │                                  │
│ │ Segment Filter   │ │ ┌────────┬────────┬────────┐    │
│ │                  │ │ │  KPI   │  KPI   │  KPI   │    │
│ │ ────────────────── │ └────────┴────────┴────────┘    │
│ │                  │ │                                  │
│ │ Navigation       │ │ ┌──────────────────────────────┐ │
│ │ • Overview       │ │ │ Section Header (h2)          │ │
│ │ • Analysis       │ │ │ Filter / Context             │ │
│ │ • Reports        │ │ │                              │ │
│ │                  │ │ │ [Chart]                      │ │
│ └──────────────────┘ │ │                              │ │
│                      │ └──────────────────────────────┘ │
│                      │                                  │
│                      │ ┌──────────┬───────────────────┐ │
│                      │ │          │                   │ │
│                      │ │ [Chart]  │    [Chart]        │ │
│                      │ │          │                   │ │
│                      │ └──────────┴───────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
from dashboard.dashboard_config import DASHBOARD_TITLE

st.set_page_config(
    page_title=DASHBOARD_TITLE,
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('Overview')
st.caption(f'Data updated on {last_update.strftime("%Y-%m-%d %H:%M")}')

col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Metric 1', 'Value 1', 'Delta 1')

st.divider()
st.subheader('Time Series')
st.plotly_chart(chart1, use_container_width=True, config=PLOTLY_CONFIG)

st.divider()
col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(chart2, use_container_width=True, config=PLOTLY_CONFIG)
with col_right:
    st.dataframe(table, use_container_width=True)
```

### 6.2 Grid System

**Column Proportions:**

```python
# Equal columns
col1, col2, col3 = st.columns(3)

# Weighted columns (30%–40%–30%)
col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

# Two-thirds + one-third
col_main, col_sidebar = st.columns([2, 1])
```

**Responsive Considerations:**

- Streamlit automatically stacks columns on mobile (<768px)
- Test layouts at 1920px (desktop), 768px (tablet), 375px (mobile)
- Limit to 3 columns maximum for readability

### 6.3 Visual Hierarchy

**Size Hierarchy:**

1. Page title (32px, extrabold) → `st.title()`
2. Section headers (24px, bold) → `st.subheader()`
3. Subsection headers (18px, semibold) → `st.markdown('### ...')`
4. Body text (14px, regular) → Default
5. Captions (12px, regular) → `st.caption()`

**Position Hierarchy:**

1. Top-left: Most important content (KPIs, key insights)
2. Center: Primary visualizations
3. Bottom: Supporting details, tables
4. Right sidebar: Filters, secondary information

**Color Hierarchy:**

1. Primary yellow (#f5c344): Interactive elements, emphasis
2. Secondary purple (#903aff): Headings, main data series
3. Accent orange (#ff8a00): KPI values, call-outs
4. Gray (#555555): Supporting text, context

### 6.4 Whitespace

**Principles:**

- More whitespace → more premium feel
- Group related elements (reduce spacing within groups)
- Separate unrelated elements (increase spacing between groups)
- Minimum 16px between elements

**Implementation:**

```python
st.divider()
# OR
st.markdown('<div style="margin-top:32px;"></div>', unsafe_allow_html=True)

with st.container():
    st.markdown(
        '<div style="padding:24px; background:#FFFFFF; border-radius:8px;">',
        unsafe_allow_html=True
    )
    # Content
    st.markdown('</div>', unsafe_allow_html=True)
```

### 6.5 Responsive Design

**Breakpoints:**

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Mobile | <768px | Single column, stacked |
| Tablet | 768px–1024px | 2 columns |
| Desktop | >1024px | 3+ columns |

**Streamlit Responsive Behavior:**

- Columns stack vertically on mobile
- Charts resize with `use_container_width=True`
- Sidebar collapses to hamburger menu

**Mobile-Specific Considerations:**

- Increase touch targets to minimum 44×44px
- Simplify filters (use dropdowns instead of multi-select)
- Show fewer KPIs (3 max instead of 5)
- Hide non-essential charts/tables

---

## 7. Accessibility Standards

### 7.1 WCAG 2.1 Compliance

**Target:** Level AA (mandatory for all components)

**Color Contrast Requirements:**

| Content Type | Minimum Ratio | Target Ratio |
|--------------|---------------|--------------|
| Normal text (<18px) | 4.5:1 | 7:1 (AAA) |
| Large text (≥18px) | 3:1 | 4.5:1 (AAA) |
| UI components | 3:1 | 4.5:1 |
| Graphical objects | 3:1 | — |

**Validated Color Pairs:**

| Foreground | Background | Ratio | Result |
|------------|------------|-------|--------|
| #000000 | #FFFFFF | 21:1 | ✅ AAA |
| #000000 | #f5c344 | 13.8:1 | ✅ AAA |
| #903aff | #FFFFFF | 4.8:1 | ✅ AA |
| #ff8a00 | #FFFFFF | 3.1:1 | ⚠️ Large text only |

**Testing Tools:**

- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Browser DevTools (Chrome / Firefox)

### 7.2 Keyboard Navigation

**Requirements:**

- All interactive elements must be keyboard-accessible
- Logical tab order (top-to-bottom, left-to-right)
- Visible focus indicators
- Skip-to-content links for long pages

**Streamlit Default Behavior:**

- Native components (buttons, inputs) are keyboard-accessible
- Custom HTML requires manual ARIA labels

**Custom Component Example:**

```python
st.markdown("""
<button
    tabindex="0"
    role="button"
    aria-label="Filter by Tier A"
    onkeydown="if(event.key==='Enter'||event.key===' '){this.click()}"
>
    Tier A
</button>
""", unsafe_allow_html=True)
```

### 7.3 Screen Reader Support

**Best Practices:**

- Use semantic HTML (`<header>`, `<nav>`, `<main>`, `<section>`)
- Provide alt text for images/icons
- Label form inputs clearly
- Use ARIA labels for custom components
- Include descriptive chart titles

**Implementation:**

```python
st.image('logo.png', caption='Dashboard Logo')

st.markdown(
    '<p class="sr-only">This chart shows delinquency trends over the last '
    '12 months, with a 15% increase in the period.</p>',
    unsafe_allow_html=True
)
```

### 7.4 Alternative Text for Data Visualizations

**Requirements:**

- Every chart must have a text description
- Describe trend, not every data point
- Include key takeaways
- Position before or after chart

**Example:**

```python
st.subheader('Revenue by Segment')
st.caption(
    'Horizontal bar chart showing total revenue per client segment. '
    'Tier A leads with R$ 2.5M (45%), followed by Tier B with R$ 1.8M (32%). '
    'Trend: +12% growth in Tier A vs. prior quarter.'
)
st.plotly_chart(bar_chart, use_container_width=True, config=PLOTLY_CONFIG)
```

### 7.5 Motion and Animation

**Guidelines:**

- Avoid auto-playing animations
- Provide pause/stop controls
- Use `prefers-reduced-motion` media query
- Keep animations subtle (≤300ms)

**Implementation:**

```python
st.markdown("""
<style>
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
""", unsafe_allow_html=True)
```

---

## 8. Performance & Optimization

### 8.1 Streamlit Caching Strategy

**Cache Data (for data transformations):**

```python
@st.cache_data(ttl=3600)
def load_data(start_date, end_date):
    df = run_query(sql, start_date=start_date, end_date=end_date)
    return df

@st.cache_data
def process_data(df):
    return df.groupby('category').agg({'value': 'sum'})
```

**Cache Resources (for database connections, models):**

```python
@st.cache_resource
def get_database_connection():
    return create_engine(DATABASE_URL)
```

**When to Invalidate Cache:**

- User changes filters → Don't cache (parameters change)
- Data updates daily → Use `ttl=86400` (24 hours)
- Data is static → No `ttl` (cache forever)

### 8.2 Plotly Performance

**Optimization Techniques:**

1. **Reduce Data Points:**

```python
if len(df) > 1000:
    df = df.resample('D', on='date').mean()
```

2. **Simplify Hover Templates:**

```python
fig.update_traces(hovertemplate='%{x}: %{y}<extra></extra>')
```

3. **Use WebGL for Large Datasets:**

```python
fig = go.Figure(go.Scattergl(x=df['x'], y=df['y'], mode='markers'))
```

4. **Disable Animations:**

```python
fig.update_layout(transition_duration=0)
```

### 8.3 Query Optimization

**Best Practices:**

- Pre-aggregate data in SQL (don't bring raw data to Python)
- Use indexes on filtered/joined columns
- Limit date ranges (default to last 90 days)
- Avoid `SELECT *` (specify columns)

**Example:**

```python
# ❌ Bad: Bring all data, filter in Python
df = pd.read_sql('SELECT * FROM transactions', conn)
df_filtered = df[df['date'] >= start_date]

# ✅ Good: Filter in SQL
sql = '''
    SELECT date, category, SUM(amount) as total
    FROM transactions
    WHERE date >= %(start_date)s
    GROUP BY date, category
'''
df = pd.read_sql(sql, conn, params={'start_date': start_date})
```

### 8.4 Loading State Management

**Progressive Loading:**

```python
with st.spinner('Loading key metrics...'):
    kpis = load_kpis()
    display_kpis(kpis)

with st.spinner('Generating charts...'):
    df_charts = load_chart_data()
    display_charts(df_charts)

with st.spinner('Loading detailed tables...'):
    df_tables = load_table_data()
    display_tables(df_tables)
```

**Lazy Loading (on user interaction):**

```python
if st.button('Load Detailed Analysis'):
    with st.spinner('Processing...'):
        df_detailed = load_detailed_analysis()
        st.dataframe(df_detailed)
```

---

## 9. Figma Integration

### 9.1 Design Token Synchronization

**Workflow:**

```
Figma Variables → Tokens Studio Plugin → JSON Export → Style Dictionary → CSS / Python
```

**Step-by-Step:**

1. **Define Variables in Figma:**
   - Create color variables (e.g., `color/primary/500`)
   - Create spacing variables (e.g., `spacing/md`)
   - Organize into collections

2. **Install Tokens Studio Plugin:**
   - Install from Figma Community
   - Connect to GitHub repository

3. **Export to JSON** (`design_tokens.json`):

```json
{
  "color": {
    "primitive": {
      "brand": {
        "warmYellow": {
          "$value": "#f5c344",
          "$type": "color"
        }
      }
    }
  }
}
```

4. **Transform with Style Dictionary** (`tokens/build.js`):

```javascript
const StyleDictionary = require("style-dictionary");

const sd = new StyleDictionary({
  source: ["../design_tokens.json"],
  platforms: {
    css: {
      transformGroup: "css",
      buildPath: "dist/css/",
      files: [{
        destination: "variables.css",
        format: "css/variables",
        options: { outputReferences: true }
      }]
    },
    python: {
      transformGroup: "js",
      buildPath: "dist/python/",
      files: [{
        destination: "tokens.json",
        format: "json/flat"
      }]
    }
  }
});

sd.buildAllPlatforms();
```

Run with:

```bash
cd tokens && npm install && npm run build
```

See `tokens/package.json` for project config (uses `style-dictionary@^4.0.0`).

5. **Import in Streamlit:**

```python
# shared/styles.py already defines COLORS, SPACING, PLOTLY_LAYOUT
from shared.styles import COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT, SPACING
```

### 9.2 Component Handoff

**Figma → Code Mapping:**

| Figma Layer | Streamlit Component | Properties |
|-------------|---------------------|------------|
| Frame: Button | `st.button()` | background, border, padding, text |
| Text: Label | `st.caption()` | fontSize, fontWeight, color |
| Frame: Card | `st.container()` | padding, backgroundColor, borderRadius |
| Chart | `st.plotly_chart()` | colors, fonts, layout |
| Filter Group | `chiclet_selector()` | variant, options, states |
| Data Table | `render_table_with_merged_headers()` | headers, styling, sorting |

**Documentation Requirements:**

- Component anatomy diagram
- All states (default, hover, active, disabled)
- Spacing measurements (using design tokens)
- Typography specifications
- Color specifications
- Interaction behavior

### 9.3 Design Sync Process

**Cadence:** Weekly sync between design and development

**Checklist:**

- [ ] New components designed in Figma
- [ ] Design tokens exported to `design_tokens.json`
- [ ] Developer reviews component specs
- [ ] Implementation in Streamlit
- [ ] Visual QA against Figma designs
- [ ] Update design system documentation

**Tools:**

- Figma Inspector for pixel-perfect measurements
- Figma API for programmatic access to design data
- GitHub for version control of token JSON files
- Style Dictionary for cross-platform token transformation

---

## 10. Agent Implementation Guide

### 10.1 Machine-Readable Format

All tokens follow W3C DTCG specification for agent parsing. See `design_tokens.json` for the complete token reference:

```json
{
  "$schema": "https://tr.designtokens.org/format/",
  "$description": "W3C DTCG design tokens for the white-label Streamlit dashboard template.",
  "token-name": {
    "$type": "color|dimension|fontFamily|fontWeight|lineHeight",
    "$value": "actual-value",
    "$description": "Human-readable description",
    "$extensions": {
      "figma": {
        "variableId": "uuid",
        "collection": "collection-name"
      }
    }
  }
}
```

### 10.2 Agent Prompt Template

**For Code Generation Agents:**

```markdown
# Context
You are generating Streamlit dashboard code using the white-label dashboard template.
The dashboard title is configured in `dashboard/dashboard_config.py`.

# Design System Reference
- **Colors:** Use COLORS dict from `shared/styles.py`
- **Spacing:** Use SPACING dict (xs=4px, sm=8px, md=16px, lg=24px, xl=32px)
- **Typography:** Red Hat Display font, scale: 32/24/18/14/12/11px
- **Components:** Import from `shared.components`
- **Charts:** Use `get_standard_layout()` and `PLOTLY_CONFIG`

# Imports
from shared.components import (
    get_standard_layout, PLOTLY_CONFIG, PLOTLY_COLORWAY,
    render_table_with_merged_headers, chiclet_selector,
    build_vintage_line
)
from shared.styles import COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT, SPACING

# Requirements
1. Follow Storytelling with Data principles
2. Use COLORS dict keys (not hardcoded hex values)
3. Include accessibility features (ARIA labels, alt text)
4. Implement caching (@st.cache_data with ttl=3600)
5. Add loading states for operations >200ms
6. Handle empty states gracefully
```

### 10.3 Component Generation Rules

**Button Component:**

```json
{
  "component": "button",
  "streamlit_method": "st.button()",
  "variants": {
    "primary": {
      "background": "{color.semantic.primary}",
      "text": "{color.semantic.text_primary}",
      "border": "none"
    },
    "secondary": {
      "background": "transparent",
      "text": "{color.semantic.text_primary}",
      "border": "1px solid {color.semantic.table_border}"
    }
  }
}
```

**Metric Card Component:**

```json
{
  "component": "metric",
  "streamlit_method": "st.metric()",
  "properties": {
    "label": {
      "fontSize": "{typography.fontSize.caption}",
      "fontWeight": "{typography.fontWeight.medium}",
      "color": "{color.semantic.text_secondary}"
    },
    "value": {
      "fontSize": "28px",
      "fontWeight": "{typography.fontWeight.bold}",
      "color": "{color.semantic.accent}"
    },
    "delta": {
      "fontSize": "{typography.fontSize.body}",
      "semanticColor": true
    }
  }
}
```

**Dashboard Section Template:**

```python
def render_{section_name}():
    st.subheader('{Section Title}')
    st.caption('{Context description}')

    selected = chiclet_selector(
        options=[...], key='{section}_filter', variant='buttons'
    )

    @st.cache_data(ttl=3600)
    def load_data(filter_value):
        return run_query(sql, params={'filter': filter_value})

    df = load_data(selected)

    if df.empty:
        st.info('No data available.')
        return

    fig = create_chart(df)
    fig.update_layout(**get_standard_layout(title='{Chart Title}'))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
```

### 10.4 Validation Checklist

**Agent-Generated Code Must:**

- [ ] Import required modules from `shared.components` and `shared.styles`
- [ ] Use `COLORS` dict keys (not hardcoded hex values)
- [ ] Include type hints for functions
- [ ] Implement error handling
- [ ] Add docstrings for functions
- [ ] Use caching decorators (`@st.cache_data`)
- [ ] Include accessibility attributes
- [ ] Follow PEP 8 style guide
- [ ] Handle empty states
- [ ] Apply consistent formatting

**Visual QA:**

- [ ] Colors match design system
- [ ] Spacing uses token values
- [ ] Typography follows scale
- [ ] Components render correctly
- [ ] Responsive on mobile/tablet
- [ ] No console errors
- [ ] Charts use `get_standard_layout()` defaults
- [ ] Tables use `render_table_with_merged_headers()`

---

## 11. Versioning & Governance

### 11.1 Semantic Versioning

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (token name changes, component API changes)
- **MINOR:** New features (new components, new token additions)
- **PATCH:** Bug fixes, documentation updates

**Current Version:** 2.0.0

**Changelog:**

```
## [2.0.0] - 2026-04-12

### Added
- W3C DTCG-compliant token format (design_tokens.json)
- Agent implementation guide
- Figma integration workflow with Style Dictionary
- White-label template architecture

### Changed
- Token naming convention (primitive → semantic → component)
- Chart color sequence order (PLOTLY_COLORWAY)

### Deprecated
- Direct color hex usage (use COLORS dict instead)
```

### 11.2 Release Process

1. **Proposal:** Team member proposes change via GitHub issue/PR
2. **Review:** Design system team reviews (design + dev)
3. **Documentation:** Update design system docs
4. **Token Update:** Export new tokens from Figma
5. **Code Update:** Implement changes in `shared/styles.py` and `design_tokens.json`
6. **Testing:** Visual regression testing, accessibility audit
7. **Release:** Publish new version with changelog
8. **Communication:** Notify stakeholders

**Release Schedule:** Bi-weekly (every 2 weeks)

### 11.3 Governance Model

**Roles:**

- **Design System Owner:** Final decision authority (1 person)
- **Design System Team:** Core contributors (2–3 people)
- **Contributors:** Anyone can propose changes via PR
- **Consumers:** All developers using the template

**Decision Framework:**

| Change Type | Approval Required |
|-------------|------------------|
| Patch (bug fix) | Design System Team |
| Minor (new component) | Design System Owner |
| Major (breaking change) | Design System Owner + Stakeholder vote |

### 11.4 Component Lifecycle

```
Proposed → In Review → Approved → In Development → Published → Stable → Deprecated → Removed
```

**Timeframes:**

- **In Review:** 1 week
- **In Development:** 2 weeks
- **Stable:** Minimum 6 months before deprecation
- **Deprecated:** 3 months warning before removal

**Deprecation Notice:**

```python
import warnings

def old_component():
    warnings.warn(
        "old_component is deprecated and will be removed in v3.0.0. "
        "Use new_component instead.",
        DeprecationWarning,
        stacklevel=2
    )
```

### 11.5 Adoption Tracking

**Metrics:**

- % of pages using design system components
- Token usage vs. hardcoded values
- Accessibility compliance score (Lighthouse)
- Design/dev handoff time
- Bug reports related to design inconsistency

**Tools:**

- GitHub Insights for code usage
- Figma Analytics for design file access
- Custom script to audit token usage in `shared/styles.py` and `dashboard/sections.py`

---

## Appendices

### A.1 Quick Reference

**Import Statements:**

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from shared.components import (
    get_standard_layout,
    PLOTLY_CONFIG,
    PLOTLY_COLORWAY,
    render_table_with_merged_headers,
    chiclet_selector,
    build_vintage_line,
)
from shared.styles import COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT, SPACING
```

**Common Patterns:**

```python
# Page setup
from dashboard.dashboard_config import DASHBOARD_TITLE
st.set_page_config(layout='wide', page_title=DASHBOARD_TITLE)

# KPI row
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Label', 'Value', 'Delta')

# Chart with standard layout
fig = px.line(df, x='date', y='value')
fig.update_layout(**get_standard_layout(title='Chart Title'))
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

# Table with merged headers
render_table_with_merged_headers(df_pivot, index_label='Category')

# Filter
selected = chiclet_selector(options=['A', 'B', 'C'], key='filter')

# Vintage line chart
fig = build_vintage_line(df_vintage, metric='delinquency_rate', title='Vintage Analysis')
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
```

### A.2 File Structure Reference

```
whitelabel_dashboard/
├── dashboard/
│   ├── dashboard_config.py    # ← EDIT: title, pages, filter options
│   ├── sections.py            # ← EDIT: dashboard section renderers
│   └── queries.py             # ← EDIT: SQL queries
├── shared/
│   ├── styles.py              # DO NOT MODIFY: COLORS, SPACING, PLOTLY_*
│   └── components/
│       ├── __init__.py        # Re-exports all shared components
│       ├── charts.py          # get_standard_layout, build_vintage_line, PLOTLY_COLORWAY
│       ├── chiclet.py         # chiclet_selector
│       └── table.py           # render_table_with_merged_headers
├── design_tokens.json         # W3C DTCG token source of truth
├── design-system.md           # This document
└── tokens/
    ├── package.json           # npm project for Style Dictionary
    └── build.js               # Figma → CSS/Python token transform
```

### A.3 Resources

**Books & Articles:**

- *Storytelling with Data* by Cole Nussbaumer Knaflic
- *The Visual Display of Quantitative Information* by Edward Tufte
- W3C Design Tokens Spec: https://tr.designtokens.org/format/

**Tools:**

- Figma: Design and prototyping
- Tokens Studio: Token management plugin for Figma
- Style Dictionary: Token transformation pipeline
- Streamlit: Dashboard framework
- Plotly: Data visualization

**Communities:**

- Streamlit Forum: https://discuss.streamlit.io/
- Storytelling with Data Community: https://www.storytellingwithdata.com/

### A.4 Glossary

| Term | Definition |
|------|-----------|
| **Design Token** | Named entity storing a design decision (color, spacing, etc.) |
| **Semantic Token** | Purpose-driven token referencing primitive tokens |
| **Component Token** | UI-role token referencing semantic tokens |
| **Data-Ink Ratio** | Proportion of ink devoted to data vs. non-data elements |
| **Preattentive Attribute** | Visual property processed instantly (color, size, position) |
| **Gestalt Principle** | Psychological principle of visual perception (proximity, similarity) |
| **WCAG** | Web Content Accessibility Guidelines |
| **DTCG** | Design Tokens Community Group (W3C) |
| **Chiclet** | Pill-shaped filter button component |
| **White-label** | Template designed for rebranding via configuration |

---

## Document Maintenance

**Last Review:** April 12, 2026
**Next Review:** July 12, 2026 (Quarterly)
**Maintained By:** Design System Team

**Change Log:**

- v2.0.0 (2026-04-12): White-label template rewrite, W3C DTCG tokens, agent compatibility, Figma integration
- v1.0.0 (2026-01-15): Initial design system documentation
