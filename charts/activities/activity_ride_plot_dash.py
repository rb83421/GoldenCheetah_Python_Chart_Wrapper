# Ride plot dash V4 (Py)
# This is an python chart
# WARNING: For this chart you need to configure your own python and install an extra package called dash#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2020-01-08 - initial chart (based on ride plot V5)
# V2 - 2020-01-24 - add wait for server before loading webpage
# V3 - 2020-02-01 - make linux compatible
# V4 - 2020-08-30 - remove workaround solved with GC 3.6

from GC_Wrapper import GC_wrapper as GC

import requests
import sys
import bisect
import ctypes
import dateutil
import numpy as np
from dash.dependencies import Output, Input
from datetime import datetime
import time
from pathlib import Path
import tempfile
import threading
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import os

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

chart_title_size = 10

best_peaks_of_x_months = 12

empty_chart_dict = dict(paper_bgcolor=gc_bg_color,
                        plot_bgcolor=gc_bg_color,
                        font=dict(
                            color=gc_text_color,
                            size=chart_title_size
                        ),
                        xaxis=dict(
                            showline=False,
                            showgrid=False,
                            ticks='',
                            showticklabels=False,
                        ),
                        yaxis=dict(
                            showline=False,
                            showgrid=False,
                            ticks='',
                            showticklabels=False,
                        ),
                        height=200,
                        )


def main():
    start_time = datetime.now()
    assets_dir = write_css()
    print('write css duration: {}'.format(datetime.now() - start_time))

    start_time = datetime.now()
    activity_metric = GC.activityMetrics()
    act = GC.activity()
    activity = pd.DataFrame(act, index=act['seconds'])
    intervals = pd.DataFrame(GC.activityIntervals())

    # all pmc data
    pmc_dict = GC.seasonPmc(all=True, metric="BikeStress")
    pmc = pd.DataFrame(pmc_dict)

    zone = GC.athleteZones(date=activity_metric["date"], sport="bike")
    zones_low = zone['zoneslow'][0]
    zone_colors = zone['zonescolor'][0]
    cp = zone['cp'][0]

    season_peaks = pd.DataFrame(GC.seasonMetrics(all=True, filter='Data contains "P"'))
    print('Gathering data duration: {}'.format(datetime.now() - start_time))

    # Possible to override colors
    # zone_colors = ["rgb(127, 127, 127)",
    #                "rgb(255, 85, 255)",
    #                "rgb(51, 140, 255)",
    #                "rgb(89, 191, 89)",
    #                "rgb(255, 204, 63)",
    #                "rgb(255, 102, 57)",
    #                "rgb(255, 51, 12)"]

    interval_type_options = []
    for interval_type in intervals.type.unique().tolist():
        interval_type_options.append({"label": interval_type, "value": interval_type})

    app = dash.Dash(assets_folder=assets_dir)
    # cache = Cache(app.server, config={
    # 'CACHE_TYPE': 'simple'
    # })
    # cache.clear()

    app.layout = html.Div([
        html.Div([
            get_title_html(activity_metric),
            html.Div([
                html.P("Medals Power"),
                html.P(get_medals_html(activity, activity_metric, season_peaks, HR=False)),
            ], className="medals_power"),
            html.Div([
                html.P("Medals Heart Rate"),
                html.P(get_medals_html(activity, activity_metric, season_peaks, HR=True)),
            ], className="medals_hr")
        ], className='top'),
        html.Div([
            html.Div(["Select which intervals to show on the map: ",
                      dcc.Dropdown(id="interval-type", value=(
                          "USER" if "USER" in intervals.type.unique().tolist() else intervals.type.unique().tolist()[
                              0]),
                                   options=interval_type_options, style={'width': '200px'})],
                     className="row",
                     style={"display": "block", "margin-left": "0px"}),
            html.P(dcc.Graph(id="map-graph")),
        ], className="map"),
        html.Div([
            html.Div([
                html.P(dcc.Graph(figure=tiz_fig(activity, activity_metric, zone, metric_type="L"))),
            ], className="tiz_power"),
            html.Div([
                html.P(dcc.Graph(figure=tiz_fig(activity, activity_metric, zone, metric_type="H"))),
            ], className="tiz_hr"),
        ], className="tiz"),
        html.Div([html.P(dcc.Graph(figure=tsb_if_fig(activity, activity_metric, pmc)))], className="tsb_if"),
        html.Div([
            dcc.Tabs(id="tabs-example", value='structured', children=[
                dcc.Tab(label='Structured', value="structured", children=[
                    html.Div([
                        "Choose Interval Type for structured overview: ",
                        dcc.Dropdown(id="interval-type-ride-plot", value=(
                            "USER" if "USER" in intervals.type.unique().tolist() else
                            intervals.type.unique().tolist()[0]),
                                     options=interval_type_options, style={'width': '200px'})],
                        className="row",
                        style={"display": "block", "margin-left": "0px"}),
                    html.P(dcc.Graph(id="ride-plot-graph-structured")),
                ]),
                dcc.Tab(label='Smooth', value='smooth', children=[
                    html.Div([
                        "Choose smoothness value (lower value needs longer loading time): ",
                        dcc.Slider(
                            id='smooth-value-ride-plot',
                            min=5,
                            max=200,
                            step=5,
                            value=20,
                        )
                    ], className="row",
                        style={"display": "block", "margin-left": "0px", "width": "500px"}),
                    html.P(dcc.Graph(id="ride-plot-graph-smooth")),
                ]),
            ]),
            # html.Div([
            #     "Structured or Smooth: ",
            #     dcc.Dropdown(id="view-type", value="Structured",
            #                  options=[{"label": "Structured", "value": "Structured"},
            #                           {"label": "Smooth", "value": "Smooth"}],
            #                  style={'width': '200px'})],
            #     className="row",
            #     style={"display": "block", "margin-left": "0px"}),
            # html.P(dcc.Graph(id="ride-plot-graph")),
        ], className="ride_plot"),
    ], className='container')

    @app.callback(
        Output('map-graph', 'figure'),
        [Input('interval-type', 'value')])
    def update_map_figure(value_type):
        return geo_plot_fig(activity, intervals, value_type)

    @app.callback(
        Output('ride-plot-graph-structured', 'figure'),
        [Input('interval-type-ride-plot', 'value')])
    def update_structured_ride_plot(selected_interval_type):
        before = datetime.now()
        if 'power' in activity and 'latitude' in activity:
            fig = ride_plot_structured_fig(activity, intervals, zone_colors, zones_low, cp, selected_interval_type)
        else:
            fig = go.Figure()
            fig.update_layout(title="Unable to draw activities ride plot (no power data)")
            fig.update_layout(empty_chart_dict)
        print('Create ride plot duration: {}'.format(datetime.now() - before))
        return fig

    @app.callback(
        Output('ride-plot-graph-smooth', 'figure'),
        [Input('smooth-value-ride-plot', 'value')])
    def update_smooth_ride_plot(smooth_value):
        before = datetime.now()
        if 'power' in activity and 'latitude' in activity:
            fig = ride_plot_smooth(activity, zone_colors, zones_low, smooth_value=int(smooth_value))
        else:
            fig = go.Figure()
            fig.update_layout(title="Unable to draw activities ride plot (no power data)")
            fig.update_layout(empty_chart_dict)
        print('Create ride plot duration: {}'.format(datetime.now() - before))
        return fig

    return app


def get_title_html(activity_metric):
    if 'Workout_Title' in activity_metric:
        title = activity_metric['Workout_Title']
        print("Processing data " + str(title))
    else:
        title = str(activity_metric['date']) + " - " + str(activity_metric['time'])
    return html.Div([
        html.H1(title),
        html.Table([
            html.Tr([
                html.Td("Workout Code"),
                html.Td(str(activity_metric['Workout_Code'])),
            ]),
            html.Tr([
                html.Td("TSS/BikeStress"),
                html.Td(str(round(activity_metric['BikeStress']))),
            ]),
            html.Tr([

                html.Td("Time"),
                html.Td(str(format_hms_seconds(activity_metric['Duration']))),
            ]),
            html.Tr([

                html.Td("Distance"),
                html.Td(str(round(activity_metric['Distance'], 2)) + " Km"),
            ]),
            html.Tr([

                html.Td("Elevation gain"),
                html.Td(str(round(activity_metric['Elevation_Gain'], 2)) + " m"),
            ]),
            html.Tr([

                html.Td("Normalized Power/Iso Power"),
                html.Td(str(round(activity_metric['IsoPower'])) + " Watts"),
            ]),
            html.Tr([

                html.Td("Average speed"),
                html.Td(str(round(activity_metric['Average_Speed'], 1)) + " km/h"),
            ]),
            html.Tr([

                html.Td("Average power"),
                html.Td(str(round(activity_metric['Average_Power'])) + " Watts"),
            ]),
            html.Tr([

                html.Td("Average cadence"),
                html.Td(str(round(activity_metric['Average_Cadence'])) + " rpm"),
            ]),

        ]),
    ], className="title")


def format_hms_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    return '%02d:%02d:%02d' % (hours, minutes, secs)


def write_css():
    temp_dir = tempfile.gettempdir()
    asset_dir = os.path.join(temp_dir, "assets")
    if not os.path.exists(asset_dir):
        os.mkdir(asset_dir)
    css_file = os.path.join(asset_dir, "GC_dash.css")

    template = '''
.Select-control {
    background-color: ''' + gc_bg_color + ''';
}
.is-open>.Select-control {  
    background-color: ''' + gc_bg_color + '''; 
    color: ''' + gc_text_color + ''';
}

.has-value.Select--single>.Select-control .Select-value .Select-value-label,
.has-value.is-pseudo-focused.Select--single>.Select-control .Select-value .Select-value-label {
  color: ''' + gc_text_color + ''';
  font-size: 13px;
}

.Select-menu-outer {
  background-color: ''' + gc_bg_color + ''';
  font-size: 13px;
  
}

.tab ,
.tab--selected{
  background-color: #343434 !important;
  color: #ffffff !important;
}

* {
    margin: 0;
    padding: 0;
    color: ''' + gc_text_color + ''';
}

html{
    background-color:  ''' + gc_bg_color + ''';
}

/* Disable ploty bars*/ 
.modebar {
    display: none !important;
}    

.container {
  background-color:  ''' + str(gc_bg_color) + ''';
}

.top {
   background-color:  #343434;
    display: -webkit-box;
    -webkit-box-orient: horizontal;
    -webkit-box-pack: justify;
    -webkit-box-align: top;

    display: -moz-box;
    -moz-box-orient: horizontal;
    -moz-box-pack: justify;
    -moz-box-align: top;

    display: box;
    box-orient: horizontal;
    box-pack: justify;
    box-align: left;

}
.title {
    padding:10px;
    margin-left: 50px;
}

.medals_power {
    height: 275px;
    overflow:auto;
    overflow-x:hidden;    
}
.medals_hr {
    margin-right: 100px;
    height: 275px;
    overflow:auto;   
    overflow-x:hidden;    
}
.medal_td{
    vertical-align: top;
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
.tsb_if {
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
    height: 500px;
}

    '''
    Path(css_file).write_text(template)
    return asset_dir


def get_medals_html(activity, activity_metric, season_peaks, HR=False):
    if (HR and 'heart.rate' in activity) or (not HR and 'power' in activity):
        if HR:
            metric_duration_name = ["1_min", "5_min", "10_min", "20_min", "30_min", "60_min"]
        else:
            metric_duration_name = ["1_sec", "5_sec", "10_sec", "15_sec", "20_sec", "30_sec", "1_min", "2_min", "3_min",
                                    "5_min", "8_min", "10_min", "20_min", "30_min", "60_min", "90_min"]

        season_peaks = season_peaks.filter(regex="^date$|^time$|_Peak_Power$|_Peak_Power_HR$", axis=1)

        rows = []
        for metric_prefix in metric_duration_name:
            metric_name = metric_prefix + "_Peak_Power"
            if HR:
                metric_name = metric_name + "_HR"

            # remove peaks after activities date
            all_time_season_peak = season_peaks.loc[
                (season_peaks.date < activity_metric['date'])]
            last_x_months_date = activity_metric['date'] - dateutil.relativedelta.relativedelta(
                months=best_peaks_of_x_months)

            last_x_months_season_peak = season_peaks.loc[
                (season_peaks.date < activity_metric['date']) &
                (season_peaks.date > last_x_months_date)]

            sorted_all_time_season_peaks = all_time_season_peak.sort_values(by=[metric_name], ascending=False)[:3]
            sorted_last_x_months_season_peak_ = last_x_months_season_peak.sort_values(by=[metric_name],
                                                                                      ascending=False)[:3]

            curr_peak_activity = activity_metric[metric_name]

            sorted_all_time_season_peaks_tolist = sorted_all_time_season_peaks[metric_name].tolist()
            sorted_x_months_season_peaks_tolist = sorted_last_x_months_season_peak_[metric_name].tolist()
            row = get_html_table_row(curr_peak_activity, sorted_all_time_season_peaks_tolist, metric_prefix, "All Time",
                                     HR)
            if row:
                rows.append(row)
            else:
                row = get_html_table_row(curr_peak_activity, sorted_x_months_season_peaks_tolist, metric_prefix,
                                         "Last " + str(best_peaks_of_x_months) + " Months", HR)
                if row:
                    rows.append(row)
        return get_html_medal_table(rows)
    else:
        return ""


def get_html_table_row(curr_peak_activity, sorted_season_peaks, duration_name, period, HR=False):
    gold_img_location = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Gold_Medal_PNG_Clip_Art.png?m=1507172109"
    silver_img_location = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Silver_Medal_PNG_Clip_Art.png?m=1507172109"
    bronze_img_location = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Bronze_Medal_PNG_Clip_Art.png?m=1507172109"

    if curr_peak_activity > sorted_season_peaks[0]:
        img_location = gold_img_location
        # print("GOLD MEDAL for duration " + str(duration_name) + ", Peak:" + str(curr_peak_activity))
    elif curr_peak_activity > sorted_season_peaks[1]:
        img_location = silver_img_location
        # print("SILVER  MEDAL for duration " + str(duration_name) + ", Peak:" + str(curr_peak_activity))
    elif curr_peak_activity > sorted_season_peaks[2]:
        img_location = bronze_img_location
        # print("BRONZE  MEDAL for duration " + str(duration_name) + ", Peak:" + str(curr_peak_activity))
    else:
        return None

    if HR:
        suffix = " heart rate"
        peak = str(round(curr_peak_activity)) + " bpm"
    else:
        suffix = " power"
        peak = str(round(curr_peak_activity)) + " W"

    return html.Tr([
        html.Td(html.Img(src=img_location, width="35", height="60")),
        html.Td([
            html.Strong(str(peak)),
            html.Br(),
            html.Br(),
            html.P(str(duration_name.replace("_", " ")) + str(suffix))
        ], className="medal_td"),
        html.Td([html.P(str(period))], className="medal_td")
    ])


def get_html_medal_table(rows):
    return html.Table([
        html.Tbody(rows)
    ])


def tsb_if_fig(activity, activity_metric, pmc):
    before = datetime.now()
    if 'power' in activity:
        # select current stress level
        pmc_at_activity_date = pmc.loc[pmc.date == activity_metric['date']]
        current_sb = pmc_at_activity_date.sb.values[0]

        # Determine hovertext
        hovertext = "Date: " + activity_metric['date'].strftime('%d-%m-%Y') + "<br>" + \
                    "TSS: " + str(round(activity_metric['BikeStress'], 2)) + "<br>" + \
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
                    size=40,
                    color="Blue"
                ),
                # name=trace_name,
                showlegend=False,
                hoverinfo="text",
                hovertext=hovertext,
                text=round(activity_metric['BikeStress'], 2),
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
            get_tss_if_annotation(min_stress_balance / 2, min_intensity_factor * 1.03, "Maintain"),
            get_tss_if_annotation(max_stress_balance / 2, max_intensity_factor * 0.98, "Race"),
            get_tss_if_annotation(min_stress_balance / 2, max_intensity_factor * 0.98, "Overload"),
            get_tss_if_annotation(max_stress_balance / 2, min_intensity_factor * 1.03, "Junk")
        ]

        fig.update_layout(
            title="TSB vs IF (based on current stress balance) ",
            paper_bgcolor=gc_bg_color,
            plot_bgcolor=gc_bg_color,
            font=dict(
                color=gc_text_color,
                size=chart_title_size,
            ),
            annotations=annotation,
            margin={"r": 40, "t": 30, "l": 30, "b": 5},
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
    else:
        fig = go.Figure()
        fig.update_layout(title="Unable to tsb vs if in zone (no power data)")
        fig.update_layout(empty_chart_dict)

    print('Create tsb vs if html duration: {}'.format(datetime.now() - before))
    return fig


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
            size=12
        ),
    )


def tiz_fig(activity, metrics, zone, metric_type="L"):
    before = datetime.now()
    if (metric_type == "H" and 'heart.rate' in activity) or (metric_type == "L" and 'power' in activity):
        # type L = Power
        # type H = Heart rate

        # if heart rate assume 5 zones unable to get hr zones via python or R
        if metric_type == "H":
            nr_of_zones = np.arange(0, 5)
            zone_colors = ["rgb(255, 85, 255)",
                           "rgb(51, 140, 255)",
                           "rgb(255, 204, 63)",
                           "rgb(255, 102, 57)",
                           "rgb(255, 51, 12)"]

        else:
            nr_of_zones = np.arange(0, len(zone['zoneslow'][0]))
            zone_colors = zone['zonescolor'][0]

        font_df = dict(family='Arial', size=10,
                       color=gc_text_color)

        tiz_df = {'tiz': [],
                  'tiz_pct': [],
                  'zone_name': [],
                  'zone_color': [],
                  'annotation': [],
                  }
        for i in nr_of_zones:
            pct = metrics[str(metric_type) + str(i + 1) + "_Percent_in_Zone"]
            time = metrics[str(metric_type) + str(i + 1) + "_Time_in_Zone"]
            zone_name = "Z" + str(i + 1)
            text = str(round(pct)) + "% / " + str(format_seconds(time))

            # per charter add 20px to move the hover text to the correct place
            # TODO Calculate movement of the text
            #  power has more levels,
            #  so time more divided so less move needed for the text could be calculated i.s.o fixed values
            if metric_type == "L":
                x = time + (len(text) * 15)
            else:
                x = time + (len(text) * 30)

            tiz_df['tiz'].append(time)
            tiz_df['tiz_pct'].append(pct)
            tiz_df['zone_color'].append(zone_colors[i])
            tiz_df['zone_name'].append(zone_name)
            tiz_df['annotation'].append(
                dict(
                    x=x,
                    y=zone_name,
                    text=text,
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
            title="Time in zone power" if metric_type == "L" else "Time in zone HR",
            annotations=tiz_df['annotation'],
            paper_bgcolor=gc_bg_color,
            plot_bgcolor=gc_bg_color,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            font=dict(
                color=gc_text_color,
                size=chart_title_size,
            ),
            margin={"r": 40, "t": 30, "l": 30, "b": 5},
            height=200,
        )
        fig.update_xaxes(showticklabels=False)
    else:
        fig = go.Figure()
        if metric_type == "H" and not 'heart.rate' in activity:
            title = "Unable to draw time in zone (no heart rate data)"
        elif metric_type == "L" and not 'power' in activity:
            title = "Unable to draw time in zone (no power data)"
        else:
            title = "Unable to draw time in zone (???)"
        fig.update_layout(
            title=title,
            height=200,
        )
        fig.update_layout(empty_chart_dict)

    print('Create time in zone figure duration: {}'.format(datetime.now() - before))
    return fig


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


def geo_plot_fig(activity, intervals, map_interval_type):
    before = datetime.now()
    if 'latitude' in activity:
        filtered_intervals = intervals[intervals.type == map_interval_type].filter(
            ["start", "stop", "color", "name"])

        # TODO Find way to always give a correct zoom
        # long_diff = max(filter_act.longitude) - min(filter_act.longitude)
        # lat_diff = max(filter_act.latitude) - min(filter_act.latitude)
        # biggest_diff = max(long_diff, lat_diff)
        #
        # diff = np.arange(0.016, 0.8, 0.01).tolist()
        # zoom_values = np.linspace(12.5, 9, num=len(diff))
        # index = min(enumerate(diff), key=lambda x: abs(x[1] - biggest_diff))
        # print("lat/long diff: " + str(biggest_diff) + "zoom: " + str(zoom_values[index[0]]))
        fig = go.Figure(
            go.Scattermapbox(
                lat=activity.latitude,
                lon=activity.longitude,
                hoverinfo="skip",
                name="Entire Ride"
            )
        )

        for index, row in filtered_intervals.iterrows():
            interval = activity[(activity.seconds >= row.start) & (activity.seconds < row.stop)]
            hovertext = []
            for i, value in interval.iterrows():
                hovertext.append(row["name"] + "<br>" + str(round(value.distance, 2)) + "Km")

            fig.add_trace(
                go.Scattermapbox(
                    lon=interval.longitude, lat=interval.latitude,
                    marker={'size': 10, 'symbol': "circle"},
                    hoverinfo="text",
                    hovertext=hovertext,
                    name=row["name"],
                    visible="legendonly",
                    # legend=True,
                )
            )

        fig.update(
            layout=dict(
                paper_bgcolor=gc_bg_color,
                plot_bgcolor=gc_bg_color,
                mapbox_style="open-street-map",
                mapbox=dict(
                    center=dict(
                        lat=activity.latitude.mean(),
                        lon=activity.longitude.mean(),
                    ),
                    zoom=9,
                ),
                margin=go.layout.Margin(
                    l=0,
                    r=0,
                    b=0,
                    t=25,
                    pad=0
                ),

                legend=go.layout.Legend(
                    traceorder="normal",
                    font=dict(
                        color=gc_text_color,
                    ),
                ),
            ),

        )
    else:
        fig = go.Figure()
        fig.update_layout(title="Unable to draw map plot (no power data)")
        fig.update_layout(empty_chart_dict)
    print('Create map html duration: {}'.format(datetime.now() - before))
    return fig


def remove_incorrect_lat_long_values(activity):
    # Filter out invalid values
    false_rows = (activity.longitude == 0.0) | (activity.latitude == 0.0)
    if false_rows.any():
        invalid_rows = activity[false_rows][['seconds', 'latitude', "longitude"]]
        print("Invalid lat/long values found on row(s): ")
        print(str(invalid_rows))
        print("These row will be removed for display")
        activity = activity[~false_rows]
    return activity


def ride_plot_smooth(activity_filtered, zone_colors, zones_low, smooth_value=20):
    activity_filtered = activity_filtered.filter(["seconds", "power"])
    fig = go.Figure()

    activity_filtered['smooth_power'] = activity_filtered.power.rolling(smooth_value).mean()
    # TODO for now will first value with the first average (investigate to improve)
    activity_filtered.smooth_power.iloc[0: (smooth_value - 1)] = activity_filtered.smooth_power.iloc[smooth_value - 1]
    # data.value.expanding(1).sum()

    before = datetime.now()
    temp_list_of_dict = []
    for i in range(len(zones_low)):
        # Zone lines:
        fig.add_trace(
            go.Scatter(
                x=[min(activity_filtered.seconds), max(activity_filtered.seconds)],
                y=[zones_low[i], zones_low[i]],
                mode='lines',
                showlegend=False,
                line=dict(
                    color=zone_colors[i],
                ),
            )
        )

        # Copy power into new power column and set all power values for this zone
        selector = 'smooth_zone_power' + str(i)
        activity_filtered[selector] = activity_filtered.smooth_power
        # Only for the last zone all watt above
        if i == len(zones_low) - 1:
            activity_filtered.loc[activity_filtered.smooth_power <= zones_low[i], 'smooth_zone_power' + str(i)] = None
        else:
            activity_filtered.loc[(activity_filtered.smooth_power <= zones_low[i]) | (
                    activity_filtered.smooth_power > zones_low[i + 1]), 'smooth_zone_power' + str(i)] = None

        before1 = datetime.now()
        # Select every transition from current zone
        df = activity_filtered[selector].notnull()
        df1 = activity_filtered[selector].isnull()
        start = ((df != df.shift(1)) & df)
        start_seconds = start.index[start == True].tolist()
        stop = ((df1 != df1.shift(1)) & df1)
        stop[0] = False
        stop_seconds = stop.index[stop == True].tolist()

        for seconds in start_seconds:
            if seconds != 0:
                temp_list_of_dict.append(
                    {'seconds': activity_filtered.seconds[(activity_filtered.seconds == seconds)].values[0] - 0.00001,
                     selector: 0})
        for seconds in stop_seconds:
            temp_list_of_dict.append(
                {'seconds': activity_filtered.seconds[(activity_filtered.seconds == seconds)].values[0] + 0.00001,
                 selector: 0})
            temp_list_of_dict.append(
                {'seconds': activity_filtered.seconds[(activity_filtered.seconds == seconds)].values[0],
                 selector: activity_filtered[activity_filtered.seconds == seconds].smooth_power.values[0]})
        print("Determine " + str(selector) + " sections duration: " + str(datetime.now() - before1))

    activity_filtered = activity_filtered.append(pd.DataFrame(temp_list_of_dict), ignore_index=True, sort=False)
    activity_filtered = activity_filtered.sort_values(by=['seconds'])
    print('Determine smooth sections duration: {}'.format(datetime.now() - before))

    # Add power zone values
    for i in range(len(zones_low)):
        selector = 'smooth_zone_power' + str(i)
        fig.add_trace(
            go.Scatter(
                x=activity_filtered['seconds'],
                y=activity_filtered[selector],
                mode='none',
                showlegend=True,
                name="Z" + str(i + 1),
                fill='tozeroy',
                fillcolor=zone_colors[i],
                connectgaps=False,  # override default to connect the gaps
            )
        )
    # # Print Raw Data
    fig.add_trace(
        go.Scatter(
            x=activity_filtered['seconds'],
            y=activity_filtered['power'],
            mode='lines',
            visible="legendonly",
            showlegend=True,
            name="power",
            line=dict(
                color='red',
                width=1,
            ),
            connectgaps=True  # override default to connect the gaps
        )
    )

    fig.add_trace(
        go.Scatter(
            x=activity_filtered.seconds,
            y=activity_filtered.smooth_power,
            mode='lines',
            showlegend=True,
            name="smooth power",
            visible="legendonly",
            line=dict(
                color='yellow',
                width=1,
            ),
            connectgaps=True,  # override default to connect the gaps
        )
    )

    tick_values = activity_filtered.iloc[::360, :].seconds.tolist()
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
            size=chart_title_size,
        ),
        margin={"r": 5, "t": 50, "l": 5, "b": 20},
    )
    return fig


def ride_plot_structured_fig(activity, all_intervals, zone_colors, zones_low, cp, selected_type):
    if len(all_intervals['type']) > 0:
        all_intervals = pd.DataFrame(all_intervals)
    else:
        return "No intervals found in this activities, possible solutions: <br>" \
               "Create manual intervals or enable interval auto-discovery via Tools->Options->Intervals"

    if selected_type:
        # Define chart title
        title = "Average Power per Interval " \
                "(CP:" + str(cp) + ") " + \
                "Selected Interval Type=" + str(selected_type)
        intervals = all_intervals[all_intervals['type'].str.contains(selected_type)]

        # Identify for every interval the zone color
        breaks = zones_low
        zone_colors = zone_colors
        interval_colors = []
        avg_power_pct = []
        for interval in intervals["Average_Power"]:
            index = bisect.bisect_left(breaks, interval)
            interval_colors.append(zone_colors[index - 1])
            avg_power_pct.append(str(round((interval / cp) * 100, 1)) + "%")

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

        # define x-axis seconds
        seconds = np.asarray(list(activity['seconds']))

        # Start building chart_not_working_yet_after_single_extract
        fig = go.Figure()

        add_ride_plot_legend_data(fig, legend, zone_colors)
        add_ride_plot_default_layout(fig, title, watts_y)

        if selected_type == "USER" or selected_type == "ALL":
            add_ride_plot_annotation(fig, x, watts_y, duration, distance, avg_power_pct, lap_names)
            add_ride_plot_interval_shapes(fig, x, watts_y, duration, lap_names, interval_colors)
            if 'heart.rate' in activity:
                # define x-axis heart rate
                heart_rate = np.asarray(list(activity['heart.rate']))
                add_ride_plot_heart_rate_line(fig, seconds, heart_rate)
        else:
            x = np.arange(0.5, len(lap_names), 1)
            add_ride_plot_annotation(fig, x, watts_y, duration, distance, avg_power_pct, lap_names, bar_chart=True)
            add_ride_plot_interval_bars(fig, x, watts_y, lap_names, interval_colors, selected_type)

    return fig


def add_ride_plot_legend_data(fig, legend, zone_colors):
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


def add_ride_plot_default_layout(fig, title, watts_y):
    fig.update_layout(
        title=title,
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        font=dict(
            color=gc_text_color,
            size=chart_title_size
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
        margin={"r": 50, "t": 50, "l": 50, "b": 5, "pad": 0},
        legend=dict(
            orientation="v",
            x=1.05,
            xanchor='left',
            y=1,
        )

    )


def add_ride_plot_annotation(fig, x, watts_y, duration, distance, avg_power_pct, lap_names, bar_chart=False):
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


def add_ride_plot_interval_shapes(fig, x, watts_y, duration, lap_names, interval_colors):
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


def add_ride_plot_interval_bars(fig, x, watts_y, lap_names, interval_colors, selected_type):
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


def add_ride_plot_heart_rate_line(fig, seconds, heart_rate):
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


def run_server(app):
    app.run_server(debug=False)


def kill_previous_dash_server():
    for thread in threading.enumerate():
        if thread.name == "dash":
            print("terminating thread:  " + str(thread.getName()))
            print("terminating thread_id :  " + str(thread.ident))
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), ctypes.py_object(SystemExit))


if __name__ == '__main__':
    # Redirect stdout when running in GC else you get and CatchOutErr on file.flush of flask app
    # Temp till the following issue is fixed: https://github.com/GoldenCheetah/GoldenCheetah/issues/3293
    sys.stdout = open(os.path.join(tempfile.gettempdir(), "GC_server_ride_plot.log"), 'a')
    kill_previous_dash_server()
    threading.Thread(target=run_server, args=(main(),), name="dash").start()
    GC.webpage("http://127.0.0.1:8050/")


def wait_for_server():
    timeout = time.time() + 30  # seconds from now
    while True:
        try:
            resp = requests.get("http://127.0.0.1:8050/ ")
            if resp.status_code == 200:
                print("Server (Re)started go load webpage")
                break
        except requests.exceptions.ConnectionError:
            print("No Connection YET")

        if time.time() > timeout:
            print("STOP retry web server connection (timed out)")
            break


if __name__ == '__main__':
    kill_previous_dash_server()
    threading.Thread(target=run_server, args=(main(),), name="dash").start()
    wait_for_server()

    GC.webpage("http://127.0.0.1:8050/")
