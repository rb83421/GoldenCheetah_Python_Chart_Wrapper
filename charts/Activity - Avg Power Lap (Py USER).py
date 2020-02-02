# Average Power Lap V3 (Py)
# This python chart shows the average power per interval for the selected interval type.
# With every interval also the percentage of your CP, duration and distance are shown.
# Also HR of the ride is displayed, this can be toggled off.

# V1 - 2019-07-16 - initial chart
# V2 - 2019-10-06 - interval selection and refactor to functions.
# V3 - 2019-10-29 - Make linux compatible

from GC_DATA import GC_wrapper as GC
import pathlib
import bisect
import plotly
import plotly.graph_objs as go
import numpy as np
import tempfile
import pandas as pd

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


def main():
    # Get data
    activity_metric = GC.activityMetrics()
    activity = GC.activity(activity=None)
    zone = GC.athleteZones(date=activity_metric["date"], sport="bike")
    all_intervals = GC.activityIntervals()

    selected_type = None
    if 'power' in activity:
        if len(all_intervals['type']) > 0:
            all_intervals = pd.DataFrame(all_intervals)
            selected_type = determine_selection_type(all_intervals)
        else:
            fail_msg = "No intervals found in this activity, possible solutions: <br>" \
                       "Create manual intervals or enable interval auto-discovery via Tools->Options->Intervals"
    else:
        fail_msg = "No power data found in this activity "

    if selected_type:
        # Define chart title
        title = "Average Power per Interval " \
                "(CP:" + str(zone["cp"][0]) + ") " + \
                "Selected Interval Type=" + str(selected_type)
        intervals = all_intervals[all_intervals['type'].str.contains(selected_type)]

        # Identify for every interval the zone color
        breaks = zone["zoneslow"][0]
        zone_colors = zone["zonescolor"][0]
        interval_colors = []
        avg_power_pct = []
        for interval in intervals["Average_Power"]:
            index = bisect.bisect_left(breaks, interval)
            interval_colors.append(zone_colors[index - 1])
            avg_power_pct.append(str(round((interval / zone["cp"][0]) * 100, 1)) + "%")

        # Add percentage labels
        legend = []
        zone_index = 1
        for zone in breaks:
            legend.append("Z" + str(zone_index) + "(" + str(zone) + ")")
            zone_index += 1

        # array of lap names to printed on the x-axis
        lap_names = np.asarray(intervals["name"])
        # array of y values
        watts_y = np.asarray(intervals["Average_Power"])
        # define x-axis (start time of the intervals)
        x = np.asarray(intervals["start"])
        # arrays used for text for every interval
        distance = np.asarray(intervals["Distance"])
        stop = np.asarray(intervals["stop"])
        duration = np.asarray(intervals["Duration"])
        # duration = [stop - start for stop, start in zip(stop, x)]

        # define x-axis heart rate
        heart_rate = np.asarray(list(activity['heart.rate']))
        # define x-axis seconds
        seconds = np.asarray(list(activity['seconds']))

        # Start building charts
        fig = go.Figure()

        add_legend_data(fig, legend, zone_colors)
        add_default_layout(fig, title, watts_y)

        if selected_type == "USER" or selected_type == "ALL":
            add_annotation(fig, x, watts_y, duration, distance, avg_power_pct, lap_names)
            add_interval_shapes(fig, x, watts_y, duration, lap_names, interval_colors)
            add_heart_rate_line(fig, seconds, heart_rate)
        else:
            x = np.arange(0.5, len(lap_names), 1)
            add_annotation(fig, x, watts_y, duration, distance, avg_power_pct, lap_names, bar_chart=True)
            add_interval_bars(fig, x, watts_y, lap_names, interval_colors, selected_type)

        plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)

    else:
        create_unavailable_html(fail_msg)

    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def determine_selection_type(intervals):
    selected_type = None

    # check is type is selected if not try to do user then all.
    if not intervals[intervals['selected']].empty:
        selected_type = intervals[intervals['selected']].type.values[0]
    else:
        if intervals['type'].str.contains("USER").any():
            selected_type = 'USER'
        elif intervals['type'].str.contains("ALL").any():
            selected_type = 'ALL'

    return selected_type


def add_legend_data(fig, legend, zone_colors):
    # workaround to get a custom legend
    for i in np.arange(0, len(legend)):
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(size=10, color=zone_colors[i]),
                legendgroup=legend[i],
                showlegend=True,
                name=legend[i],
            )
        )


def add_default_layout(fig, title, watts_y):
    fig.update_layout(
        title=title,
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        font=dict(
            color=gc_text_color,
            size=12
        ),
        yaxis=dict(
            range=[0, max(watts_y) + 100],
            nticks=int(max(watts_y) / 10),
            ticks='outside',
            showgrid=True,
            zeroline=True,
            showline=True,
            gridcolor="grey",
            title="Watts",
        ),
        margin=go.layout.Margin(
            l=100,
            r=0,
            b=100,
            t=150,
            pad=0
        ),
    )


def add_annotation(fig, x, watts_y, duration, distance, avg_power_pct, lap_names, bar_chart=False):
    annotations = []
    x_label_pos = []

    for i in np.arange(0, len(lap_names)):

        if bar_chart:
            current_x_pos = x[i]
            x_label_pos.append(current_x_pos)
        else:
            current_x_pos = x[i] + (duration[i] / 2)
            x_label_pos.append(current_x_pos)

        m, s = divmod(duration[i], 60)
        h, m = divmod(m, 60)
        if h > 0:
            duration_formatted = str(int(h)) + "h" + str(int(m)) + "m" + str(int(s)) + "s"
        elif m > 0:
            duration_formatted = str(int(m)) + "m" + str(int(s)) + "s"
        else:
            duration_formatted = str(int(s)) + "s"
        annotations.append(
            dict(
                x=current_x_pos,
                y=watts_y[i],
                xref='x',
                yref='y',
                text=str(avg_power_pct[i]) + "<br>" + duration_formatted + "<br>" + str(round(distance[i], 2)) + "km",
                showarrow=True,
                arrowhead=7,
                arrowcolor=gc_text_color,
                ax=0,
                ay=-40,
                font=dict(
                    color=gc_text_color,
                    size=12
                ),
            )
        )
    # end for

    fig.update_layout(
        xaxis=dict(
            tickvals=x_label_pos,
            ticktext=lap_names,
            tickangle=45,
            showgrid=False,
            rangemode='nonnegative',
        ),
        annotations=annotations,
    )


def add_interval_shapes(fig, x, watts_y, duration, lap_names, interval_colors):
    # Create rectangles per interval
    shapes = []
    x_label_pos = []

    for i in np.arange(0, len(lap_names)):
        x_label_pos.append(x[i] + (duration[i] / 2))

        shapes.append(
            {
                'type': 'rect',
                'x0': x[i],
                'y0': 0,
                'x1': x[i] + duration[i] - 1,
                'y1': watts_y[i],
                'fillcolor': interval_colors[i],
            }
        )
    # end for

    fig.update_layout(
        shapes=shapes,
    )


def add_interval_bars(fig, x, watts_y, lap_names, interval_colors, selected_type):
    fig.add_trace(
        go.Bar(
            x=x,
            y=watts_y,
            text=lap_names,
            marker_color=interval_colors,
            showlegend=False,
            name=selected_type
        )
    ),


def add_heart_rate_line(fig, seconds, heart_rate):
    fig.add_trace(
        go.Scatter(
            x=seconds,
            y=heart_rate,
            mode='lines',
            showlegend=True,
            name="HR",
            line=dict(
                color='Red',
            ),
            yaxis='y2'
        )
    )

    fig.update_layout(
        yaxis2=dict(
            range=[0, max(heart_rate) + 10],
            nticks=int(max(heart_rate) / 5),
            overlaying='y',
            anchor='x',
            side='right',
            showgrid=False,
            title='HR',
            rangemode='nonnegative',

        ),
    )


def create_unavailable_html(fail_msg):
    f = open(temp_file.name, "w+")
    lines_of_text = ["""
    <!DOCTYPE html>
    <html>
        <head>
            <style>
                body {
                  background-color: #343434;
                  text-align: center;
                  color: white;
                  font-family: Arial, Helvetica, sans-serif;
                }
            </style>
        </head>
        <body>
        
        <h1>Unable to draw chart</h1>
        """,
                     str(fail_msg),
                     """
        </body>
    </html>
    """]
    f.writelines(lines_of_text)
    f.close()


if __name__ == "__main__":
    main()
