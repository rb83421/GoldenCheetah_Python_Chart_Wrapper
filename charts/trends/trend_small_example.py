# xxxxx V1 (Py)
# This is Python chart
# <Description>
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 20xx-xx-xx - Initial chart

from GC_Wrapper import GC_wrapper as GC

import pathlib
import plotly
import plotly.graph_objs as go
import tempfile

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'


def main():
    season_metrics = GC.seasonMetrics()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=season_metrics['date'],
            y=season_metrics['Distance'],
            name="Distance",
        )
    )
    fig.update_layout(
        title="Small trend distance example",
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        showlegend=True,
        font=dict(
            color=gc_text_color,
            size=12
        ),
        xaxis_title='Date',
        yaxis_title='Distance (km)',
    )
    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


if __name__ == "__main__":
    main()

