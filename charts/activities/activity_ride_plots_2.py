# Ride Plots V4 (Py)
# This is an python chart
# My take on a ride plot
# currently only for power with a smoothness (moving average) of 20)
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 initial chart
# V2 - 2019-10-29 - Make linux compatible
# V3 - 2019-11-11 - Update Error handling
# V4 - 2019-12-03 - add altitude 3d + change xaxis time line


from GC_Wrapper import GC_wrapper as GC

import pathlib
import pandas as pd
import plotly
import plotly.graph_objs as go
import plotly.express as px
import tempfile
import math
import numpy as np
from pathlib import Path
import bisect
from itertools import compress

smooth_value = 20

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
temp_duration_selection = 360


def main():

    activity_metric = GC.activityMetrics()
    act = GC.activity()
    activity = pd.DataFrame(act, index=act['seconds'])
    zone = GC.athleteZones(date=activity_metric["date"], sport="Bike")
    activity_intervals = GC.activityIntervals()

    zones_low = zone['zoneslow'][0]
    zone_colors = zone['zonescolor'][0]

    # Possible to override colors
    # zone_colors = ["rgb(127, 127, 127)",
    #                "rgb(255, 85, 255)",
    #                "rgb(51, 140, 255)",
    #                "rgb(89, 191, 89)",
    #                "rgb(255, 204, 63)",
    #                "rgb(255, 102, 57)",
    #                "rgb(255, 51, 12)"]
    if 'latitude' in activity:
        geo_html = geo_plot_html(activity)
        fig = altitude_3d_figure(activity, activity_intervals, zone, coloring_mode, slice_distance, polygon_limit)
        altitude_html = plotly.offline.plot(fig, output_type='div', auto_open=False)

    else:
        geo_html = "<h2>Unable to draw activities ride plot no GPS data</h2>"

    if 'power' in activity:
        tiz_power_html = tiz_html(activity_metric, zone, type="L")
        if 'latitude' in activity:
            ride_html = ride_plot_html(activity, zone_colors, zones_low)
        else:
            ride_html = "<h2>Unable to draw activities ride plot no GPS data</h2>"
    else:
        ride_html = "<h2>Unable to draw activities ride plot (no power data)</h2>"
        tiz_power_html = "<h2>Unable to draw Time in Zone power (no power data)</h2>"

    if 'heart.rate' in activity:
        tiz_hr_html = tiz_html(activity_metric, zone, type="H")
    else:
        tiz_hr_html = "<h2>Unable to draw Time in Zone heart rate (no HR data)</h2>"

    create_end_html_float(activity_metric, geo_html, ride_html, tiz_power_html, tiz_hr_html, altitude_html)

    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def tiz_html(metrics, zone, type="L"):
    # type L = Power
    # type H = Heart rate

    # if heart rate assume 5 zones unalbe to get hr zones via python or R
    if type == "H":
        nr_of_zones = np.arange(0, 5)
        zone_colors = ["rgb(255, 85, 255)",
                       "rgb(51, 140, 255)",
                       "rgb(255, 204, 63)",
                       "rgb(255, 102, 57)",
                       "rgb(255, 51, 12)"]

    else:
        nr_of_zones = np.arange(0, len(zone['zoneslow'][0]))
        zone_colors = zone['zonescolor'][0]

    font_df = dict(family='Arial', size=11,
                   color=gc_text_color)

    tiz_df = {'tiz': [],
              'tiz_pct': [],
              'zone_name': [],
              'zone_color': [],
              'annotation': [],
              }
    for i in nr_of_zones:
        pct = metrics[str(type) + str(i + 1) + "_Percent_in_Zone"]
        time = metrics[str(type) + str(i + 1) + "_Time_in_Zone"]
        zone_name = "Z" + str(i + 1)

        tiz_df['tiz'].append(time)
        tiz_df['tiz_pct'].append(pct)
        tiz_df['zone_color'].append(zone_colors[i])
        tiz_df['zone_name'].append(zone_name)
        text = str(round(pct)) + "% / " + str(format_seconds(time))
        tiz_df['annotation'].append(
            dict(
                x=time + len(text)*25,
                y=zone_name,
                text=text,
                align='left',
                font=font_df,
                showarrow=False,
            )
        )

    # H2_Percent_in_Zone
    # H1_Time_in_Zone
    # L3_Time_in_Zone
    # L2_Percent_in_Zone
    fig = go.Figure(
        data=[
            go.Bar(
                x=tiz_df['tiz'],
                y=tiz_df['zone_name'],
                orientation='h',
                marker=dict(
                    color=tiz_df['zone_color'],
                ),
            )
        ]
    )
    fig.update_layout(
        title="Time in zone power" if type == "L" else "Time in zone HR",
        annotations=tiz_df['annotation'],
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        font=dict(
            color=gc_text_color,
        ),
        margin={"r": 40, "t": 30, "l": 30, "b": 5},
        height=200,
    )
    fig.update_xaxes(showticklabels=False)
    return plotly.offline.plot(fig, output_type='div')


def format_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return_value = '%dh%dm%ds' % (hours, minutes, secs)
    elif minutes > 0:
        return_value = '%dm%ds' % (minutes, secs)
    else:
        return_value = '%ds' % (secs)

    # return '%02d:%02d:%02d' % (hours, minutes, secs)
    return return_value


def format_hms_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    return '%02d:%02d:%02d' % (hours, minutes, secs)


def geo_plot_html(activity):
    filter_act = activity.loc[activity['longitude'] != 0.0]
    filter_act = filter_act.loc[filter_act['latitude'] != 0.0]

    # TODO Find way to always give a correct zoom
    # long_diff = max(filter_act.longitude) - min(filter_act.longitude)
    # lat_diff = max(filter_act.latitude) - min(filter_act.latitude)
    # biggest_diff = max(long_diff, lat_diff)
    #
    # diff = np.arange(0.016, 0.8, 0.01).tolist()
    # zoom_values = np.linspace(12.5, 9, num=len(diff))
    # index = min(enumerate(diff), key=lambda x: abs(x[1] - biggest_diff))
    # print("lat/long diff: " + str(biggest_diff) + "zoom: " + str(zoom_values[index[0]]))

    fig = px.scatter_mapbox(filter_act,
                            lat="latitude",
                            lon="longitude",
                            zoom=9,
                            height=400,
                            )
    fig.update_layout(mapbox_style="open-street-map",
                      paper_bgcolor=gc_bg_color,
                      plot_bgcolor=gc_bg_color,
                      margin={"r": 0, "t": 0, "l": 0, "b": 0}
                      )
    return plotly.offline.plot(fig, output_type='div', auto_open=False)


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


def ride_plot_html(activity, zone_colors, zones_low):
    fig = go.Figure()
    # Zone lines:
    for i in range(len(zones_low)):
        fig.add_trace(
            go.Scatter(
                x=[min(activity['seconds']), max(activity['seconds'])],
                y=[zones_low[i], zones_low[i]],
                mode='lines',
                showlegend=False,
                line=dict(
                    color=zone_colors[i],
                ),
            )
        )
    activity['smooth_power'] = activity.power.rolling(smooth_value).mean()
    # TODO for now will first value with the first average (investigate to improve)
    activity.smooth_power.iloc[0: (smooth_value - 1)] = activity.smooth_power.iloc[smooth_value - 1]
    # data.value.expanding(1).sum()

    for i in range(len(zones_low)):
        activity['smooth_zone_power' + str(i)] = activity['smooth_power']

        # Last zone all above
        if i == len(zones_low) - 1:
            activity.loc[activity.smooth_power <= zones_low[i], 'smooth_zone_power' + str(i)] = None
        else:
            activity.loc[(activity.smooth_power <= zones_low[i]) | (
                    activity.smooth_power > zones_low[i + 1]), 'smooth_zone_power' + str(i)] = None
    for i in range(len(zones_low)):
        selector = 'smooth_zone_power' + str(i)
        power_value_found = False
        for index in range(len(activity['seconds'])):
            if not math.isnan(activity[selector][index]) and not power_value_found:
                power_value_found = True
                tmp = {'seconds': activity.seconds[index] - 0.00001, selector: 0}
                activity = activity.append(tmp, ignore_index=True)
            elif math.isnan(activity[selector][index]) and power_value_found:
                tmp = {'seconds': activity.seconds[index] + 0.00001, selector: 0}
                activity[selector].iloc[index] = activity.smooth_power.iloc[index]
                activity = activity.append(tmp, ignore_index=True)
                power_value_found = False
    activity = activity.sort_values(by=['seconds'])
    for i in range(len(zones_low)):
        selector = 'smooth_zone_power' + str(i)
        fig.add_trace(
            go.Scatter(
                x=activity['seconds'],
                y=activity[selector],
                mode='none',
                showlegend=True,
                name="Z" + str(i + 1),
                fill='tozeroy',
                fillcolor=zone_colors[i],
                connectgaps=False,  # override default to connect the gaps
            )
        )
    # # Print Raw Data
    # fig.add_trace(
    #     go.Scatter(
    #         x=activities['seconds'],
    #         y=activities['power'],
    #         mode='lines',
    #         showlegend=True,
    #         line=dict(
    #             color='yellow',
    #         ),
    #         connectgaps=False  # override default to connect the gaps
    #     )
    # )


    fig.add_trace(
        go.Scatter(
            x=activity.seconds,
            y=activity.smooth_power,
            mode='lines',
            showlegend=True,
            name="power",
            line=dict(
                color='black',
                width=1,
            ),
            connectgaps=False,  # override default to connect the gaps
        )
    )

    tick_values = activity.iloc[::360, :].seconds.tolist()
    fig.update_layout(
        title="Ride Plot (smooth value:" + str(smooth_value) + ")",
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        xaxis=dict(
            showgrid=False,
            tickvals=tick_values,
            ticktext=[format_seconds(i) for i in tick_values],

        ),
        yaxis=dict(
            showgrid=False
            ),
        font=dict(
            color=gc_text_color,
            size=12
        ),
        margin={"r": 5, "t": 50, "l": 5, "b": 20},
    )
    return plotly.offline.plot(fig, output_type='div', auto_open=False)


def create_end_html_float(activity_metric, map_html, ride_html, tiz_power_html, tiz_hr_html, altitude_3d_html):
    if 'Workout_Title' in activity_metric:
        title = activity_metric['Workout_Title']
    else:
        title = str(activity_metric['date']) + " - " + str(activity_metric['time'])

    template = '''
    <!DOCTYPE html>

    <html>
        <head>
            <title>Ride plot</title>
            <meta charset="utf-8">        
            <style>
            * {
                margin: 0;
                padding: 0;
                color: ''' + gc_text_color + ''';
            }
        
            html{
                  background-color:  ''' + str(gc_bg_color) + ''';
            }  
            .container {
              background-color:  ''' + str(gc_bg_color) + ''';
            }
            
            .title {
                padding:10px;
                margin-left: 100px;
            }
            table { 
                padding:10px;
                margin-left: 10px;              
            }
            
            .map {
                width: 40%;
                float: left;
            }
            .tiz{
                width: 30%;
                float: left;
            }
            .altitude_3d {
                width: 30%;
                float: left;
            }           
            .tiz_power {
                width: 100%;
                height: 50%;
                float: left;
            }
            .tiz_hr {
                width: 100%;
                height: 50%;
                float: left;
            }

            .ride_plot {
                clear:both;
            }
            </style>        
        </head>
        <body>
            <div class="container">
              <div class="title">
                <h1>''' + str(title) + '''</h1>
                <table>
                    <tr>
                        <td>Workout Code</td>
                        <td>''' + str(activity_metric['Workout_Code']) + '''</td>
                    </tr>
                    <tr>
                        <td>TSS/BikeStress</td>
                        <td>''' + str(round(activity_metric['BikeStress'])) + '''</td>
                    </tr>
                    <tr>
                        <td>Time</td>
                        <td>''' + str(format_hms_seconds(activity_metric['Duration'])) + '''</td>
                    </tr>
                    <tr>
                        <td>Distance</td>
                        <td>''' + str(round(activity_metric['Distance'], 2)) + ''' Km</td>
                    </tr>
                    <tr>
                        <td>Elevation gain</td>
                        <td>''' + str(round(activity_metric['Elevation_Gain'], 2)) + ''' m</td>
                    </tr>
                    <tr>
                        <td>Normalized Power/Iso Power</td>
                        <td>''' + str(round(activity_metric['IsoPower'])) + ''' Watts</td>
                    </tr>
                    <tr>
                        <td>Average speed</td>
                        <td>''' + str(round(activity_metric['Average_Speed'], 1)) + ''' km/h</td>
                    </tr>
                    <tr>
                        <td>Average power</td>
                        <td>''' + str(round(activity_metric['Average_Power'])) + ''' Watts</td>
                    </tr>
                    <tr>
                        <td>Average cadence</td>
                        <td>''' + str(round(activity_metric['Average_Cadence'])) + ''' rpm</td>
                    </tr>
                </table>
              </div>
              <div>
                  <div class="map">
                  ''' + str(map_html) + '''
                  </div>
                  <div class="tiz">
                      <div class="tiz_power">
                      ''' + str(tiz_power_html) + '''
                      </div>
                      <div class="tiz_hr">
                      ''' + str(tiz_hr_html) + '''
                      </div>
                  </div>
                  <div class="altitude_3d">
                  ''' + str(altitude_3d_html) + '''
                  </div>
              </div>
              
              <div class="ride_plot">
              ''' + str(ride_html) + '''            
              </div>
            </div>        
        </body>
    </html>'''
    Path(temp_file.name).write_text(template)


if __name__ == "__main__":
    main()
