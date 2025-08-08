import os
import plotly.graph_objs as go
import plotly.io as pio
from pathlib import Path

def save_hr_plot_plotly(dist_data, hr_data, distance_km_total, filename="static/hr_plot.html"):
    """
    Saves a heart rate vs. distance plot with HR zones shaded in the background.
    """

    # Convert distance to km
    dist_km = [d / 1000 for d in dist_data]

    # Define HR zones
    hr_zones = {
        "Z1 (Recovery)": (0, 130, 'rgba(173,216,230,0.2)'),    # light blue
        "Z2 (Easy)": (130, 144, 'rgba(144,238,144,0.2)'),       # light green
        "Z3 (Moderate)": (145, 159, 'rgba(255,255,102,0.2)'),   # yellow
        "Z4 (Threshold)": (160, 173, 'rgba(255,165,0,0.2)'),    # orange
        "Z5 (VO2max)": (174, 189, 'rgba(255,99,71,0.2)')        # tomato red
    }

    # Heart rate trace
    hr_trace = go.Scatter(
        x=dist_km,
        y=hr_data,
        mode='lines',
        name='Heart Rate',
        line=dict(color='crimson', width=1.5, shape='spline', smoothing=1.3),
        hovertemplate='Distance: %{x:.2f} km<br>HR: %{y:.0f} bpm<extra></extra>'
    )

    # Add shaded zone backgrounds and fake traces for legends
    zone_shapes = []
    zone_legend_traces = []
    for label, (y0, y1, color) in hr_zones.items():
        zone_shapes.append({
            "type": "rect",
            "xref": "paper",
            "yref": "y",
            "x0": 0,
            "x1": 1,
            "y0": y0,
            "y1": y1,
            "fillcolor": color,
            "line": {"width": 0},
            "layer": "below"
        })
        zone_legend_traces.append(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker={"size": 10, "color": color},
                name=label
            )
        )

    # Layout
    layout = go.Layout(
        title="Heart Rate vs Distance",
        xaxis=dict(title="Distance (km)", range=[0, round(distance_km_total, 2)]),
        yaxis=dict(title="Heart Rate (bpm)", range=[min(hr_data)-5, max(hr_data)+10]),
        shapes=zone_shapes,
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
        showlegend=True,
        width=800,
        height=300,
        margin=dict(l=40, r=20, t=40, b=40)
    )

    # Build figure
    fig = go.Figure(data=[hr_trace] + zone_legend_traces, layout=layout)
   
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save plot to HTML
    pio.write_html(fig, file=filename, auto_open=False)