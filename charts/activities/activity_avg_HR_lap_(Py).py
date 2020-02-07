# Average HR Lap V3 (Py)
# This python chart shows the average heart rate per interval for the selected interval type.
# With every interval also the percentage of your LTHR, duration and distance are shown.
# Also HR of the ride is displayed, this can be toggled off.

# V1 - 2019-07-16 - initial chart
# V2 - 2019-10-06 - interval selection and refactor to functions.
# V3 - 2019-10-29 - Make linux compatible
from GC_Wrapper import GC_wrapper as GC
import bisect
import pathlib
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

# HR percentage zone taken over from Options->Athlete->Zones-Heartrate Zones->Default
hr_zone_pct = [0, 68, 83, 94, 105]
zone_colors = ["#ff00ff", "#00aaff", "#00ff80", "#ffd500", "#ff0000"]



def main():
    # Get data
    activity_metric = GC.activityMetrics()
    activity = GC.activity(activity=None)
    zone = GC.athleteZones(date=activity_metric["date"], sport="bike")
    all_intervals = GC.activityIntervals()
    lthr = zone["lthr"][0]
    hrmax = zone["hrmax"][0]

    selected_type = None
    if 'power' in activity:
        if len(all_intervals['type']) > 0:
            all_intervals = pd.DataFrame(all_intervals)
            selected_type = determine_selection_type(all_intervals)
        else:
            fail_msg = "No intervals found in this activities, possible solutions: <br>" \
                       "Create manual intervals or enable interval auto-discovery via Tools->Options->Intervals"
    else:
        fail_msg = "No power data found in this activities "

    if selected_type:
        # Define chart title
        title = "Average Heart Rate per Interval " \
                "(LTHR:" + str(lthr) + ") " + \
                "Selected Interval Type=" + str(selected_type)

        intervals = all_intervals[all_intervals['type'].str.contains(selected_type)]

        # Identify for every interval the zone color
        breaks = [round(zone["lthr"][0] * hr / 100, 0) for hr in hr_zone_pct]
        interval_colors = []
        avg_hr_pct = []
        for interval in intervals["Average_Heart_Rate"]:
            index = bisect.bisect_left(breaks, interval)
            interval_colors.append(zone_colors[index - 1])
            avg_hr_pct.append(str(round((interval / lthr) * 100, 1)) + "%")

        # Add percentage labels
        legend = []
        zone_index = 1
        for zone in breaks:
            legend.append("Z" + str(zone_index) + "(" + str(zone) + ")")
            zone_index += 1

        # array of lap names to printed on the x-axis
        lap_names = np.asarray(intervals["name"])
        # array of y values
        avg_hr_y = np.asarray(intervals["Average_Heart_Rate"])
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

        # Start building chart_not_working_yet_after_single_extract
        fig = go.Figure()

        add_legend_data(fig, legend, zone_colors)
        add_default_layout(fig, title, hrmax)

        if selected_type == "USER" or selected_type == "ALL":
            add_annotation(fig, x, avg_hr_y, duration, distance, avg_hr_pct, lap_names)
            add_interval_shapes(fig, x, avg_hr_y, duration, lap_names, interval_colors)
            add_horizontal_line(fig, x, stop, lthr, 'Blue', 'LTHR')
            add_horizontal_line(fig, x, stop, hrmax, 'Red', 'MAX')
            add_heart_rate_line(fig, seconds, heart_rate)
        else:
            x = np.arange(0.5, len(lap_names), 1)
            add_horizontal_line(fig, x, x, lthr, 'Blue', 'LTHR')
            add_horizontal_line(fig, x, x, hrmax, 'Red', 'MAX')
            add_annotation(fig, x, avg_hr_y, duration, distance, avg_hr_pct, lap_names, bar_chart=True)
            add_interval_bars(fig, x, avg_hr_y, lap_names, interval_colors, selected_type)

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


def add_default_layout(fig, title, hr_max):
    fig.update_layout(
        title=title,
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        font=dict(
            color=gc_text_color,
            size=12
        ),
        yaxis=dict(
            range=[0, hr_max + 10],
            nticks=int(hr_max / 4),
            ticks='outside',
            showgrid=True,
            zeroline=True,
            showline=True,
            gridcolor="grey",
            title="BPM",
        ),
        margin=go.layout.Margin(
            l=100,
            r=0,
            b=100,
            t=150,
            pad=0
        ),
    )


def add_horizontal_line(fig, start, stop, value, color, name):
    fig.add_trace(
        go.Scatter(
            x=[min(start), max(stop)],
            y=[value, value],
            mode='lines',
            showlegend=True,
            name=name,
            line=dict(
                color=color,
            )
        )
    )


def add_annotation(fig, x, avg_hr_y, duration, distance, avg_power_pct, lap_names, bar_chart=False):
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
                y=avg_hr_y[i],
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


def add_interval_shapes(fig, x, avg_hr_y, duration, lap_names, interval_colors):
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
                'y1': avg_hr_y[i],
                'layer': 'below',
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
        )
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
