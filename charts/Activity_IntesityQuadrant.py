# xxxxx V1 (Py)
# This is an python chart
# <Description>
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 20xx-xx-xx - Initial chart

from GC_DATA import GC_wrapper as GC

import pathlib
import plotly
import plotly.graph_objs as go
import tempfile
import pandas as pd

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'


def main():
    activity_metric = GC.activityMetrics()
    act = GC.activity()
    activity = pd.DataFrame(act, index=act['seconds'])

    # all pmc data
    pmc_dict = GC.seasonPmc(all=True, metric="BikeStress")
    pmc = pd.DataFrame(pmc_dict)

    # select current stress level
    pmc_at_activity_date = pmc.loc[pmc.date == activity_metric['date']]
    current_sb = pmc_at_activity_date.sb.values[0]

    # Determine hovertext
    hovertext = "Date: " + activity_metric['date'].strftime('%d-%m-%Y') + "<br>" + \
                                  "TSS: " + str(activity_metric['BikeStress']) + "<br>" + \
                                  "IF: " + str(round(activity_metric['IF'], 2)) + "<br>" + \
                                  "TSB: " + str(round(current_sb, 1)) + "<br>"

    fig = go.Figure()

    # Add scatter traces
    fig.add_traces(
        go.Scatter(
            x=[current_sb],
            y=[activity_metric['IF']],
            mode='markers+text',
            marker=dict(
                size=60,
                color="Blue"
            ),
            # name=trace_name,
            showlegend=False,
            hoverinfo="text",
            hovertext=hovertext,
            text=activity_metric['BikeStress'],
            textfont=dict(
                size=8,
                color='darkgray',
            )

        )
    )

    # Add Quadrant text
    min_intensity_factor = min((activity_metric['IF'] * 0.9), 0.7)
    max_intensity_factor = max((activity_metric['IF'] * 1.1), 0.9)
    min_stress_balance = min((current_sb * 1.2), -5)
    max_stress_balance = max((current_sb * 1.2), 5)

    annotation = [
        get_tss_if_annotation(min_stress_balance / 2, min_intensity_factor * 1.08, "Maintain"),
        get_tss_if_annotation(max_stress_balance / 2, max_intensity_factor * 0.98, "Race"),
        get_tss_if_annotation(min_stress_balance / 2, max_intensity_factor * 0.98, "Overload"),
        get_tss_if_annotation(max_stress_balance / 2, min_intensity_factor * 1.08, "Junk")
    ]

    fig.update_layout(
        title="TSB vs IF (Based on current stress level) ",
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        font=dict(
            color=gc_text_color,
            size=12
        ),
        annotations=annotation,
    )


    # Add horizontal IF 0.85 line
    fig.add_trace(
        go.Scatter(
            x=[min_stress_balance, max_stress_balance],
            y=[0.85, 0.85],
            mode='lines',
            showlegend=False,
            line=dict(
                color="White",
                dash='dash'
            )
        )
    )

    # Add vertical TSB 0 line
    fig.add_trace(
        go.Scatter(
            x=[0, 0],
            y=[min_intensity_factor, max_intensity_factor],
            mode='lines',
            showlegend=False,
            line=dict(
                color="White",
                dash='dash'
            )
        )
    )


    # Set axes properties
    fig.update_xaxes(range=[min_stress_balance, max_stress_balance],
                     zeroline=False,
                     gridcolor='gray',
                     mirror=True,
                     ticks='outside',
                     showline=True,
                     )
    fig.update_yaxes(range=[min_intensity_factor, max_intensity_factor],
                     gridcolor='gray',
                     mirror=True,
                     ticks='outside',
                     showline=True,
                     )

    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_tss_if_annotation(x, y, text):
    return go.layout.Annotation(
        x=x,
        y=y,
        xref="x",
        yref="y",
        text=text,
        showarrow=False,
        font=dict(
            color="darkgray",
            size=18
        ),
    )


if __name__ == "__main__":
    main()

