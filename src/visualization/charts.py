import plotly.graph_objects as go

from src.config.settings import MONTHS, THRESHOLD_MM


def degradation_chart_figure(
    actual_series: list[float],
    title: str = "Tren Degradasi Ketebalan Dinding",
) -> go.Figure:
    n = len(actual_series)
    x_axis = MONTHS[:n] if n <= len(MONTHS) else list(range(n))
    threshold_line = [THRESHOLD_MM] * n
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=actual_series,
            mode="lines",
            name="Ketebalan Aktual",
            line={"color": "#3b82f6", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=threshold_line,
            mode="lines",
            name="Batas Minimum / Threshold",
            line={"color": "#ef4444", "width": 2},
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Waktu (Bulan ke-0 hingga ke-12)",
        yaxis_title="Ketebalan (mm)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
    return fig
