# TSB vs IF V6 (Py)
# This is an python chart
# TSB vs IF with BikeStress
#
# A scatter plot visualisation of a PMC where the TSB v IF for a ride is compared as a bubble plot,
# where the size of the bubble is related to the TSS accumulated in the ride.
# The colors reflect the color configuration for the ride,
# unless you are comparing seasons or date ranges in which case the compare colors are applied instead.
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2019-10-24 - Initial chart based on Scatter PMC (2016-09-30 of Creator: Livers)
# V2 - 2019-10-25 - Add date to bubbles + add season to title
# V3 - 2019-10-27 - Update temporary file definition and file uri (linux compatibility)
# V4 - 2019-11-12 - Executable when no Workout_Title
# V5 - 2019-12-08 - Take over auto center from Manuel
# V6 - 2019-12-08 - Make more robust when only one value in a season

from GC_Wrapper import GC_wrapper as GC

import pandas as pd
import plotly
import plotly.graph_objects as go
import tempfile
import pathlib

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


def main():
    # get data
    selected_seasons = GC.season(compare=True)
    compares = GC.seasonMetrics(compare=True, filter='Data contains "P"')

    # all pmc data
    pmc_dict = GC.seasonPmc(all=True, metric="BikeStress")
    pmc = pd.DataFrame(pmc_dict, index=pmc_dict['date'])

    fig = go.Figure()

    intensity_factor = []
    stress_balance = []
    for compare, season_name in zip(compares, selected_seasons['name']):
        if 'Workout_Title' in compare[0]:
            metrics = pd.DataFrame(compare[0], index=compare[0]['date']).filter(
                ['date', 'IF', 'color', 'Workout_Code', 'BikeStress', 'Workout_Title'])
        else:
            metrics = pd.DataFrame(compare[0], index=compare[0]['date']).filter(
                ['date', 'IF', 'color', 'Workout_Code', 'BikeStress'])

        # Filter out IF = 0 (probably rides without power)
        metrics = metrics.loc[metrics.IF > 0]

        # combine pmc and metric data
        merged_metrics = pd.merge(metrics, pmc)
        stress_balance.extend(merged_metrics.sb.tolist())
        intensity_factor.extend(merged_metrics.IF.tolist())

        # Determine the radius of the circles based on BikeStress (on a scale of 30-100)
        # merged_metrics['radius'] = np.sqrt((merged_metrics.BikeStress / 3.1415927))
        a = 30
        b = 100
        minimal = merged_metrics.BikeStress.min()
        maximal = merged_metrics.BikeStress.max()
        div = maximal - minimal
        if div == 0:
            div = 1
        # norm = [(number - a) / (b - a) for number in residual]
        merged_metrics['radius'] = a + ((merged_metrics.BikeStress - minimal) * (b - a) / div)
        # norm = [a + ((number - minimal) * (b - a) / (maximal - minimal)) for number in residual]

        # Determine hovertext
        titles = "Title: " + merged_metrics.Workout_Title if 'Workout_Title' in merged_metrics else ""
        merged_metrics['date'] = pd.to_datetime(merged_metrics.date)
        merged_metrics['hovertext'] = "Date: " + merged_metrics.date.dt.strftime('%d-%m-%Y').map(str) + "<br>" + \
                                      "TSS: " + merged_metrics.BikeStress.astype(int).map(str) + "<br>" + \
                                      "TSB: " + round(merged_metrics.sb, 1).map(str) + "<br>" + \
                                      titles

        # make transparent for overlapping
        # colors <- adjustcolor(merged_metrics.color, 0.6)

        if not len(compares) == 1:
            color = compare[1]
            merged_metrics['color'] = color
            merged_metrics['legend'] = season_name
        else:
            merged_metrics['legend'] = merged_metrics['Workout_Code']

        for i in merged_metrics.color.unique():
            cur_metrics = merged_metrics.loc[merged_metrics.color == i]
            trace_name = cur_metrics.iloc[0]['legend']
            if not trace_name:
                trace_name = "None"

            # Add scatter traces
            fig.add_traces(
                go.Scatter(
                    x=cur_metrics.sb,
                    y=cur_metrics.IF,
                    mode='markers+text',
                    marker=dict(
                        size=cur_metrics.radius,
                        color=cur_metrics.color
                    ),
                    name=trace_name,
                    showlegend=True,
                    hoverinfo="text",
                    hovertext=cur_metrics.hovertext,
                    text=cur_metrics['date'].dt.strftime('%d-%m-<br>%Y'),
                    textfont=dict(
                        size=8,
                        color='darkgray',
                    )

                )
            )
        # print(merged_metrics[['date', 'sb', 'BikeStress', 'radius', 'Workout_Code', 'color', 'legend']].head())

    # Add Quadrant text
    min_intensity_factor = min(min(intensity_factor) * 0.9, 0.7)
    max_intensity_factor = max(max(intensity_factor) * 1.1, 0.9)
    min_stress_balance = min(min(stress_balance) * 1.2, -5)
    max_stress_balance = max(max(stress_balance) * 1.2, 5)

    annotation = [
        get_annotation(min_stress_balance / 2, min_intensity_factor * 1.03, "Maintain"),
        get_annotation(max_stress_balance / 2, max_intensity_factor * 0.98, "Race"),
        get_annotation(min_stress_balance / 2, max_intensity_factor * 0.98, "Overload"),
        get_annotation(max_stress_balance / 2, min_intensity_factor * 1.03, "Junk")
    ]


    fig.update_layout(
        title="TSB vs IF (" + ",".join(selected_seasons['name']) + ")",
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

    # fig.show()
    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_annotation(x, y, text):
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
