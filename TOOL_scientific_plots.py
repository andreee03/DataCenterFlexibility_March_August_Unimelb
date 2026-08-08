"""
scientific_plots.py
====================
A reusable framework to produce publication-quality figures with Plotly,
styled like plots found in scientific journals (Nature, Science, APS, etc.).

Design goals
------------
- One function to build the figure: `scientific_figure(...)`
- One function to export it cleanly: `save_figure(...)`
- Consistent, colorblind-safe color palette
- Proper axis labels with units, e.g. "Temperature (K)"
- Support for: multiple series, markers/lines/both, error bars (x and y),
  log axes, secondary y-axis, reference lines (h/v), annotations,
  custom ranges, legend control, and high-resolution export
  (PNG / SVG / PDF / HTML).

Usage
-----
See the `if __name__ == "__main__":` block at the bottom for full examples.

Minimal example
----------------
    from scientific_plots import scientific_figure, save_figure

    data = [
        dict(x=x1, y=y1, name="Sample A"),
        dict(x=x2, y=y2, name="Sample B", mode="markers"),
    ]

    fig = scientific_figure(
        data,
        xlabel="Time", xunit="s",
        ylabel="Intensity", yunit="a.u.",
        title="Signal decay",
    )
    save_figure(fig, "my_plot")
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio


# --------------------------------------------------------------------------
# 1. COLOR PALETTE  (Okabe-Ito, colorblind-safe — standard in scientific pubs)
# --------------------------------------------------------------------------
COLORS = [
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # green
    "#E69F00",  # orange
    "#CC79A7",  # pink
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
]

MARKERS = ["circle", "square", "diamond", "triangle-up", "x", "cross", "star"]
DASHES = ["solid", "dash", "dot", "dashdot", "longdash"]


# --------------------------------------------------------------------------
# 2. JOURNAL-STYLE TEMPLATE
# --------------------------------------------------------------------------
def _register_scientific_template():
    """Register a reusable 'scientific' Plotly template (call once at import)."""
    template = go.layout.Template()

    template.layout = go.Layout(
        font=dict(family="Arial, Helvetica, sans-serif", size=16, color="black"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        colorway=COLORS,
        xaxis=dict(
            showline=True, linewidth=1.5, linecolor="black", mirror=True,
            ticks="outside", tickwidth=1.5, ticklen=6, tickcolor="black",
            showgrid=False, zeroline=False,
            title_font=dict(size=18),
            tickfont=dict(size=15),
        ),
        yaxis=dict(
            showline=True, linewidth=1.5, linecolor="black", mirror=True,
            ticks="outside", tickwidth=1.5, ticklen=6, tickcolor="black",
            showgrid=False, zeroline=False,
            title_font=dict(size=18),
            tickfont=dict(size=15),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="black",
            borderwidth=1,
            font=dict(size=14),
        ),
        margin=dict(l=90, r=40, t=70, b=80),
    )
    pio.templates["scientific"] = template


_register_scientific_template()


# --------------------------------------------------------------------------
# 3. HELPER: axis label with unit, e.g. "Temperature (K)"
# --------------------------------------------------------------------------
def _label_with_unit(label: str, unit: str = "") -> str:
    if not label:
        return ""
    return f"{label} ({unit})" if unit else label


# --------------------------------------------------------------------------
# 4. PANDAS DATAFRAME SUPPORT
# --------------------------------------------------------------------------
def series_from_dataframe(
    df,
    x,
    y,
    group=None,
    error_y=None,
    error_x=None,
    mode="lines+markers",
    name_prefix="",
    sort_by_x=True,
):
    """
    Convert a pandas DataFrame into the list-of-dict format expected by
    `scientific_figure`. Handles the common cases directly, similar to
    how `px.line`/`px.scatter` take a dataframe + column names.
 
    Parameters
    ----------
    df : pandas.DataFrame
    x, y : str
        Column names to plot.
    group : str, optional
        Column name to split the data into several series (one per unique
        value), e.g. group="condition" -> one line per condition, each
        auto-colored/labeled. Equivalent to `color=` in px.
    error_y, error_x : str, optional
        Column names holding the (symmetric) error bar values.
    mode : str
        Passed through to each series ("lines", "markers", "lines+markers").
    name_prefix : str
        Prepended to each series name (useful when combining several
        `series_from_dataframe` calls into one figure).
    sort_by_x : bool
        Sort each series by the x column (recommended for line plots so
        points connect in order).
 
    Returns
    -------
    list of dict, ready to pass as `data=` to `scientific_figure`.
 
    Example
    -------
        data = series_from_dataframe(df, x="time", y="signal", group="condition")
        fig = scientific_figure(data, xlabel="Time", xunit="s", ...)
    """
    series_list = []
 
    if group is None:
        sub = df.sort_values(x) if sort_by_x else df
        series_list.append(dict(
            x=sub[x].to_numpy(),
            y=sub[y].to_numpy(),
            name=name_prefix or y,
            mode=mode,
            error_y=sub[error_y].to_numpy() if error_y else None,
            error_x=sub[error_x].to_numpy() if error_x else None,
        ))
    else:
        for value, sub in df.groupby(group):
            sub = sub.sort_values(x) if sort_by_x else sub
            series_list.append(dict(
                x=sub[x].to_numpy(),
                y=sub[y].to_numpy(),
                name=f"{name_prefix}{value}",
                mode=mode,
                error_y=sub[error_y].to_numpy() if error_y else None,
                error_x=sub[error_x].to_numpy() if error_x else None,
            ))
 
    return series_list
 
 
# --------------------------------------------------------------------------
# 4. MAIN FIGURE BUILDER
# --------------------------------------------------------------------------
def scientific_figure(
    data,
    *,
    xlabel="", xunit="",
    ylabel="", yunit="",
    y2label="", y2unit="",      # for an optional secondary y-axis
    title="", subtitle="",
    legend_title=None,
    xtype=False, ytype=False,
    xrange=None, yrange=None,
    width=900, height=600,
    grid=False,
    hlines=None, vlines=None,   # list of dicts: {"value":..., "label":..., "color":..., "dash":...}
    annotations=None,           # list of dicts: {"x":, "y":, "text":, ...}
    template="scientific",
    show_legend=True,
):
    """
    Build a publication-style Plotly figure from a list of series.

    Parameters
    ----------
    data : list of dict
        Each dict describes one series/trace. Recognized keys:
          - x, y            : array-like (required)
          - name            : str, legend label
          - mode            : "lines", "markers", "lines+markers" (default)
          - color           : override color (else auto-cycled from palette)
          - marker_symbol   : override marker shape (else auto-cycled)
          - dash            : "solid"/"dash"/"dot"/... for lines
          - error_y         : array-like, symmetric y error bars
          - error_x         : array-like, symmetric x error bars
          - secondary_y     : bool, plot against the right-hand y-axis
          - opacity         : float 0-1
          - line_width      : float
          - marker_size     : float
    xlabel, xunit, ylabel, yunit : axis titles and units
    y2label, y2unit : secondary y-axis title/unit (only used if any
        series has secondary_y=True)
    title, subtitle : figure title (subtitle shown smaller, below title)
    legend_title : optional legend title
    xtype, ytype : bool, log-scale axes
    xrange, yrange : [min, max] to force axis ranges
    width, height : figure size in pixels (px @ scale=1; see save_figure)
    grid : show light gridlines
    hlines, vlines : reference lines, e.g.
        hlines=[{"value": 0, "label": "baseline", "color": "grey", "dash": "dash"}]
    annotations : list of annotation dicts (plotly `add_annotation` kwargs)
    template : which registered template to use (default "scientific")
    show_legend : bool

    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = go.Figure()
    has_secondary = any(d.get("secondary_y") for d in data)

    for i, series in enumerate(data):
        color = series.get("color", COLORS[i % len(COLORS)])
        mode = series.get("mode", "lines+markers")
        marker_symbol = series.get("marker_symbol", MARKERS[i % len(MARKERS)])

        error_y = None
        if series.get("error_y") is not None:
            error_y = dict(type="data", array=series["error_y"], visible=True,
                            thickness=1.3, width=4, color=color)

        error_x = None
        if series.get("error_x") is not None:
            error_x = dict(type="data", array=series["error_x"], visible=True,
                            thickness=1.3, width=4, color=color)

        fig.add_trace(
            go.Scatter(
                x=series["x"],
                y=series["y"],
                mode=mode,
                name=series.get("name", f"Series {i+1}"),
                line=dict(
                    color=color,
                    width=series.get("line_width", 2.5),
                    dash=series.get("dash", "solid"),
                ) if "lines" in mode else None,
                marker=dict(
                    color=color,
                    symbol=marker_symbol,
                    size=series.get("marker_size", 9),
                    line=dict(color="black", width=0.8),
                ) if "markers" in mode else None,
                error_y=error_y,
                error_x=error_x,
                opacity=series.get("opacity", 1.0),
                yaxis="y2" if series.get("secondary_y") else "y1",
            )
        )

    # --- Title (with optional subtitle) ---------------------------------
    if subtitle:
        title_text = f"<b>{title}</b><br><span style='font-size:14px;color:grey'>{subtitle}</span>"
    else:
        title_text = f"<b>{title}</b>" if title else None

    fig.update_layout(
        template=template,
        title=dict(text=title_text, x=0.5, xanchor="center") if title_text else None,
        width=width,
        height=height,
        legend_title_text=legend_title,
        showlegend=show_legend,
    )
    # type can be:           ['-', 'linear', 'log', 'date', 'category', 'multicategory']
    # --- Axes -------------------------------------------------------------
    fig.update_xaxes(
        title_text=_label_with_unit(xlabel, xunit),
        type= xtype if xtype else '-',
        range=xrange,
        showgrid=grid, gridcolor="rgba(0,0,0,0.12)",
    )
    fig.update_yaxes(
        title_text=_label_with_unit(ylabel, yunit),
        type= ytype if ytype else '-',
        range=yrange,
        showgrid=grid, gridcolor="rgba(0,0,0,0.12)",
    )

    if has_secondary:
        fig.update_layout(
            yaxis2=dict(
                title=_label_with_unit(y2label, y2unit),
                overlaying="y",
                side="right",
                showline=True, linewidth=1.5, linecolor="black",
                ticks="outside", tickwidth=1.5, ticklen=6,
                showgrid=False,
            )
        )

    # --- Reference lines ----------------------------------------------
    for h in (hlines or []):
        fig.add_hline(
            y=h["value"],
            line_dash=h.get("dash", "dash"),
            line_color=h.get("color", "grey"),
            annotation_text=h.get("label", ""),
            annotation_position="top left",
        )
    for v in (vlines or []):
        fig.add_vline(
            x=v["value"],
            line_dash=v.get("dash", "dash"),
            line_color=v.get("color", "grey"),
            annotation_text=v.get("label", ""),
            annotation_position="top right",
        )

    # --- Annotations -----------------------------------------------------
    for ann in (annotations or []):
        fig.add_annotation(**ann)

    return fig


# --------------------------------------------------------------------------
# 5. EXPORT HELPER
# --------------------------------------------------------------------------
def save_figure(fig, filepath, formats=("png", "svg", "html"), scale=3):
    """
    Export a figure to one or several formats, at publication resolution.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
    filepath : str
        Path WITHOUT extension, e.g. "outputs/figure1"
    formats : tuple of str
        Any of "png", "svg", "pdf", "html". PNG/SVG/PDF require `kaleido`.
    scale : float
        Multiplier for raster resolution (scale=3 at width=900 → ~2700 px wide,
        good for print).
    """
    for fmt in formats:
        out = f"{filepath}.{fmt}"
        if fmt == "html":
            fig.write_html(out, include_plotlyjs="cdn")
        else:
            fig.write_image(out, scale=scale)
        print(f"Saved: {out}")


# --------------------------------------------------------------------------
# 6. DEMO / EXAMPLES
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import numpy as np

    rng = np.random.default_rng(0)

    # --- Example 1: two series with error bars, log y-axis ---------------
    x = np.linspace(0, 10, 12)
    y1 = 5 * np.exp(-0.3 * x) + rng.normal(0, 0.05, size=x.size)
    y1_err = np.full_like(x, 0.15)
    y2 = 3 * np.exp(-0.15 * x) + rng.normal(0, 0.05, size=x.size)
    y2_err = np.full_like(x, 0.12)

    data1 = [
        dict(x=x, y=y1, name="Sample A (25 °C)", error_y=y1_err, mode="markers+lines"),
        dict(x=x, y=y2, name="Sample B (50 °C)", error_y=y2_err, mode="markers+lines"),
    ]

    fig1 = scientific_figure(
        data1,
        xlabel="Time", xunit="s",
        ylabel="Signal intensity", yunit="a.u.",
        title="Decay of the fluorescence signal",
        subtitle="Averaged over 3 replicates, error bars = 1 s.d.",
        ytype=True,
        legend_title="Condition",
        hlines=[{"value": 0.5, "label": "Detection limit", "color": "red", "dash": "dot"}],
    )

    # --- Example 2: dual y-axis -------------------------------------------
    t = np.linspace(0, 24, 100)
    temperature = 20 + 5 * np.sin(2 * np.pi * t / 24)
    pressure = 101.3 + 0.4 * np.cos(2 * np.pi * t / 24 + 0.5)

    data2 = [
        dict(x=t, y=temperature, name="Temperature", mode="lines"),
        dict(x=t, y=pressure, name="Pressure", mode="lines",
             dash="dash", secondary_y=True),
    ]

    fig2 = scientific_figure(
        data2,
        xlabel="Time", xunit="h",
        ylabel="Temperature", yunit="°C",
        y2label="Pressure", y2unit="kPa",
        title="Diurnal variation of temperature and pressure",
    )

    import os
    os.makedirs("/mnt/user-data/outputs", exist_ok=True)
    save_figure(fig1, "/mnt/user-data/outputs/example_decay", formats=("png", "svg", "html"))
    save_figure(fig2, "/mnt/user-data/outputs/example_dual_axis", formats=("png", "html"))
