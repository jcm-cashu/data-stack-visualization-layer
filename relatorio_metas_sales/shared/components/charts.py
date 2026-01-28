"""
Chart components - DO NOT MODIFY
Provides consistent chart styling and builders for Plotly charts.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..styles import COLORS


# Plot color palette derived from app theme
PLOTLY_COLORWAY = [COLORS["secondary"], COLORS["accent"], COLORS["primary"], COLORS["danger"]]


def adjust_color(hex_color: str, factor: float) -> str:
    """Adjust color brightness by factor.
    
    Args:
        hex_color: Hex color string (e.g., "#f5c344")
        factor: Brightness multiplier (< 1 = darker, > 1 = lighter)
    
    Returns:
        Adjusted hex color string
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_standard_layout(
    title: str = "",
    height: int = 420,
    show_legend: bool = True,
    legend_title: str = "",
) -> dict:
    """Get standard Plotly layout configuration matching the visual identity.
    
    Args:
        title: Chart title
        height: Chart height in pixels
        show_legend: Whether to show legend
        legend_title: Legend title text
    
    Returns:
        Dict with Plotly layout configuration
    """
    layout = dict(
        title=title,
        height=height,
        margin=dict(l=40, r=16, t=40 if title else 10, b=40),
        paper_bgcolor=COLORS["bg_light"],
        plot_bgcolor=COLORS["bg_light"],
        font=dict(
            family="Red Hat Display, sans-serif",
            color=COLORS["text_primary"],
            size=12,
        ),
        showlegend=show_legend,
        yaxis=dict(gridcolor="#e0e0e0"),
        xaxis=dict(gridcolor="#e0e0e0"),
    )
    if legend_title:
        layout["legend_title_text"] = legend_title
    return layout


def build_vintage_line(df_vintage: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """Build a vintage line chart for the given metric.
    
    Creates a line chart with multiple vintages, each with progressively 
    lighter colors based on chronological order.
    
    Args:
        df_vintage: DataFrame with columns ['vintage', 'mob', metric]
        metric: Column name of the metric to plot
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    df_metric = df_vintage[["vintage", "mob", metric]].copy()
    df_metric["percent"] = df_metric[metric].astype(float) * 100.0

    def vintage_to_ts(v: str) -> pd.Timestamp:
        try:
            return pd.Timestamp(f"{v}-01")
        except Exception:
            return pd.Timestamp.now()

    vintages_sorted = sorted(df_metric["vintage"].unique(), key=vintage_to_ts)
    n_vintages = len(vintages_sorted)
    base_color = COLORS["primary"]
    factors = np.linspace(0.4, 1.0, n_vintages) if n_vintages > 1 else [1.0]

    fig_line = go.Figure()
    for vintage, factor in zip(vintages_sorted, factors):
        subset = df_metric[df_metric["vintage"] == vintage].sort_values("mob")
        fig_line.add_trace(
            go.Scatter(
                x=subset["mob"],
                y=subset["percent"],
                mode="lines",
                name=vintage,
                line=dict(color=adjust_color(base_color, factor), width=2),
                hovertemplate=f"Vintage {vintage}<br>MOB %{{x}}<br>{title}: %{{y:.1f}}%<extra></extra>",
            )
        )

    fig_line.update_layout(
        title=title,
        height=360,
        margin=dict(l=10, r=10, t=40, b=40),
        paper_bgcolor=COLORS["bg_light"],
        plot_bgcolor=COLORS["bg_light"],
        font=dict(family="Red Hat Display, sans-serif", color=COLORS["text_primary"]),
        legend_title_text="Vintage",
        yaxis=dict(title="Delinquência (%)", gridcolor="#e0e0e0"),
        xaxis=dict(title="MOB", gridcolor="#e0e0e0", dtick=1),
    )
    return fig_line
