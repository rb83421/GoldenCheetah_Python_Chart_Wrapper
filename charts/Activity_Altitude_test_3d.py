# Altitude 3d V4 (Py)
# This is an python chart
# This chart shows the altitude in a 3d map and also shows the selected interval on it
# Limitation of 200 polygons for now
# It is possible to select coloring mode gradient or average power
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2019-11-23 - Initial chart
# V2 - 2019-11-24 - Add possibility to color on average power
# V3 - 2019-11-27 - Update slope calculation inline with AllPlotSlopeCurve.cpp
# V4 - 2019-12-05 - Change longitude=x latitude=y, add z range and annotations, refactor in functions


from GC_DATA import GC_wrapper as GC

import bisect
import pathlib
import tempfile
import plotly
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from itertools import compress

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)
# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

# Magic number to determine max detail level for long activities it limit the ploygon due execution time
polygon_limit = 200

coloring_mode = "G"  # P for power G for gradient

enable_annotations = True
annotations_distance = 1  # every x km a altitude annotation is given

# Create polygon per x km
slice_distance = 0.1

# This variably can be used for testing to only display the first x seconds
temp_duration_selection = None  # 360


def main():
    activity = GC.activity()
    activity_intervals = GC.activityIntervals()
    activity_metric = GC.activityMetrics()
    zones = GC.athleteZones(date=activity_metric["date"], sport="bike")
    fig = altitude_3d_figure(activity, activity_intervals, zones, coloring_mode, slice_distance, polygon_limit)
    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def altitude_3d_figure(activity, activity_intervals, zones, color_mode="G", slice_value=0.1, poly_limit=200):
    activity_df = pd.DataFrame(activity, index=activity['seconds'])
    # For testing purpose select only x number of seconds
    if temp_duration_selection:
        activity_df = activity_df.head(temp_duration_selection)
    min_altitude = activity_df.altitude.min()
    activity_df.altitude = activity_df.altitude - min_altitude

    coloring_df = determine_coloring_dict(color_mode, zones)
    paths = determine_altitude_polygons(activity_df, color_mode, coloring_df, poly_limit, slice_value)

    fig = go.Figure()
    add_altitude_polygons(fig, paths)
    add_selected_interval_trace(fig, activity_df, activity_intervals)
    add_legend_gradient(fig, coloring_df)

    # If the maximum altitude is less then 100 use a z range of 100 to add the effect of an low gradient ride
    if activity_df.altitude.max() < 100:
        z_range = [activity_df.altitude.min(), 100]
    else:
        z_range = [activity_df.altitude.min(), activity_df.altitude.max()]

    if enable_annotations:
        annotations = determine_annotations(activity_df, annotations_distance)
    else:
        annotations = []

    update_layout(fig, annotations, z_range)
    return fig


def determine_coloring_dict(color_mode, zones):
    coloring_dict = {'breaks': [],
                     'colors': [],
                     'legend_text': []}
    if color_mode == "P":
        coloring_dict['breaks'] = zones['zoneslow'][0]
        for color in zones['zonescolor'][0]:
            rgb = str(tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)))
            coloring_dict['colors'].append("rgba" + rgb.split(")")[0] + ", 0.6)")
        for i in np.arange(0, len(coloring_dict['breaks'])):
            coloring_dict['legend_text'].append("Z" + str(i + 1) + " >" + str(coloring_dict['breaks'][i]))
    else:
        coloring_dict['breaks'] = [-15, -7.5, 0, 7.5, 15, 20, 100]
        # 'colors': ['blue', 'lightblue', 'green', 'gray', 'yellow', 'orange', 'red'],
        #           <-15 darkblue,   <-7.5 mid blue,    <0 lightblue   , >0 green,        >7.5 yellow,      >15 light red,   >20 dark red
        coloring_dict['colors'] = ['rgba(0,0,133,0.6)', 'rgba(30,20,255,0.6)', 'rgba(80,235,255,0.6)',
                                   'rgba(80,255,0,0.6)', 'rgba(255,255,0,0.6)', 'rgba(235,0,0,0.6)',
                                   'rgba(122, 0,0,0.6)']
        coloring_dict['legend_text'] = ["<15%", ">-15% <-7.5%", ">-7.5% <0%", ">0% <7.5%", ">7.5% <15%", ">15% <20%",
                                        ">20%"]
    coloring_df = pd.DataFrame(coloring_dict)
    return coloring_df


def determine_altitude_polygons(activity_df, color_mode, coloring_df, poly_limit, slice_value):
    # Slice per x km
    number_slices = activity_df.distance.iloc[-1] / slice_value
    # If number of slice is to big limit traces on 200
    if number_slices > poly_limit:
        print("TO many slices limit it on poly_limit")
        number_slices = poly_limit
        slice_value = activity_df.distance.iloc[-1] / number_slices
    paths = []
    for i in range(int(number_slices)):
        start = i * slice_value
        # last slice take last sample
        if i == int(number_slices) - 1:
            stop = activity_df.distance.iloc[-1]
        else:
            stop = (i * slice_value) + slice_value

        mask = (activity_df.distance >= start) & (activity_df.distance <= stop)

        # add one extra value to close gaps
        mask[mask[::-1].idxmax() + 1] = True
        slice_df = activity_df.loc[mask]
        altitude_gain = slice_df.altitude.iloc[-1] - slice_df.altitude.iloc[0]
        distance = slice_df.distance.iloc[-1] - slice_df.distance.iloc[0]
        # slice_value is in km altitude in meter
        # distance - X-Axis is in KM, Y-Axis in m! and at the end *100 to get %value
        slope = 100 * (altitude_gain / (distance * 1000))
        # print("slope  : " + str(slope) + "(alt.: " + str(altitude_gain) + ", dist.: " + str(distance) + ")")
        avg_power = slice_df.power.mean()

        if color_mode == "P":
            index = bisect.bisect_right(coloring_df.breaks, avg_power)
            color = coloring_df.colors[index - 1]
        else:
            index = bisect.bisect_left(coloring_df.breaks, slope)
            color = coloring_df.colors[index]

        start_x = slice_df.longitude.iloc[0]
        stop_x = slice_df.longitude.iloc[-1]
        start_y = slice_df.latitude.iloc[0]
        stop_y = slice_df.latitude.iloc[-1]
        start_altitude = slice_df.altitude.iloc[0]
        stop_altitude = slice_df.altitude.iloc[-1]

        # For each slice define polygon
        new_path = {'x': [start_x, start_x, stop_x, stop_x],
                    'y': [start_y, start_y, stop_y, stop_y],
                    'z': [0, start_altitude, stop_altitude, 0],
                    'color': color,
                    'slope': [slope],
                    'altitude': [stop_altitude],
                    'average_power': [avg_power],
                    }
        paths.append(new_path)
    return paths


def add_selected_interval_trace(fig, activity_df, activity_intervals):
    # add markers for selected intervals
    lap = list(activity_intervals["selected"])
    for index in list(compress(range(len(lap)), lap)):
        interval_name = activity_intervals["name"][index]
        selected_interval_start = int(activity_intervals["start"][index]) + 1
        selected_interval_stop = int(activity_intervals["stop"][index]) + 1
        selected_interval_df = activity_df.loc[selected_interval_start:selected_interval_stop].copy()
        marker_color = "blue"
        selected_interval_df['color'] = marker_color
        selected_interval_df['markersize'] = 5

        fig.add_trace(
            go.Scatter3d(
                x=selected_interval_df.longitude,
                y=selected_interval_df.latitude,
                z=selected_interval_df.altitude,
                mode='markers',
                marker=dict(
                    size=selected_interval_df.markersize,
                    color=selected_interval_df.color,
                ),
                hovertext=["Altitude: " + str(altitude) + "<br>" +
                           "Distance: " + str(distance) + "<br>" +
                           "Seconds: " + str(seconds)
                           for seconds, altitude, distance in
                           zip(selected_interval_df.seconds.tolist(), selected_interval_df.altitude.tolist(),
                               selected_interval_df.distance.tolist())],
                hoverinfo="text",
                name="Interval: " + str(interval_name),
                line=dict(
                    color=marker_color,
                    width=1
                )

            )
        )


def add_altitude_polygons(fig, paths):
    print("3d Altitude: number of polygons: " + str(len(paths)))
    for path in paths:
        fig.add_trace(
            go.Scatter3d(
                type='scatter3d',
                mode='lines',
                x=path['x'],
                y=path['y'],
                z=path['z'],
                surfaceaxis=1,  # add a surface axis ('1' refers to axes[1] i.e. the y-axis)
                surfacecolor=path['color'],
                hovertext="Altitude:  " + str(round(path['altitude'][-1], 1)) + "m" +
                          "<br>Slope: " + str(round(np.mean(path['slope']), 1)) + "%" +
                          "<br>Avg Power: " + str(round(np.mean(path['average_power']), 1)) + "Watt",

                hoverinfo="text",
                line=dict(
                    color=path['color'],
                    width=1
                ),
                showlegend=False,

            )
        )


def add_legend_gradient(fig, coloring_df):
    nr_legends = len(coloring_df['breaks'])
    for i in np.arange(0, nr_legends):
        legend_group = coloring_df['legend_text'][i]
        name = coloring_df['legend_text'][i]
        color = coloring_df['colors'][i]
        fig.add_trace(
            go.Scatter3d(
                x=[None],
                y=[None],
                z=[None],
                mode='markers',
                marker=dict(size=10, color=color),
                legendgroup=legend_group,
                showlegend=True,
                name=name,
            )
        )
    fig.update_layout(
        legend=go.layout.Legend(
            traceorder="normal",
            font=dict(
                color=gc_text_color,
            ),
        ),
    )


def update_layout(fig, annotations, z_range):
    fig.update_layout(
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,

        scene=dict(
            annotations=annotations,
            xaxis=dict(
                title=' ',
                showbackground=False,
                showgrid=False,
                ticks='',
                showticklabels=False,
            ),
            yaxis=dict(
                title=' ',
                showbackground=False,
                showgrid=False,
                ticks='',
                showticklabels=False,
            ),
            zaxis=dict(
                title='Altitude (m)',
                range=z_range,
                titlefont=dict(color=gc_text_color),
                showbackground=False,
                showgrid=False,
                ticks='',
                showticklabels=True,
                tickfont=dict(
                    color=gc_text_color,
                ),
            ),
        ),
    )


def determine_annotations(activity_df, distance_km):
    annotations = []
    # Slice per x km
    number_slices = activity_df.distance.iloc[-1] / distance_km

    for i in range(int(number_slices)):
        start = i * distance_km
        # last slice take last sample
        if i == int(number_slices) - 1:
            stop = activity_df.distance.iloc[-1]
        else:
            stop = (i * distance_km) + distance_km

        mask = (activity_df.distance >= start) & (activity_df.distance <= stop)
        slice_df = activity_df.loc[mask]

        annotations.append(
            dict(
                x=slice_df.longitude.iloc[-1],
                y=slice_df.latitude.iloc[-1],
                z=slice_df.altitude.iloc[-1],
                text=str(round(slice_df.altitude.iloc[-1], 1)),
                font=dict(
                    color=gc_text_color,
                    size=12
                ),
                opacity=0.7,
                yshift=10,
                showarrow=False,
            )
        )
    return annotations


if __name__ == "__main__":
    main()
