"""
Activity compare laps V1 (Py)
This is an python chart.
With this chart enable to compare laps of multiple activities.
You need to use the default compare functionality of GC see https://github.com/GoldenCheetah/GoldenCheetah/wiki/UG_Compare-Pane_General

WARNING: For this chart you need to configure your own python and install an extra package called dash!!
Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users

V1 - 2020-11-12 - initial chart
"""

from GC_Wrapper import GC_wrapper as GC

import requests
import ctypes
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
import numpy as np

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

chart_title_size = 10
chart_height = 300


def main():
    start_time = datetime.now()
    assets_dir = write_css()
    print('write css duration: {}'.format(datetime.now() - start_time))

    start_time = datetime.now()
    activity_metrics = GC.activityMetrics(compare=True)
    activities = []
    for activity_metric in activity_metrics:
        activity_date = datetime.combine(activity_metric[0]['date'], activity_metric[0]['time'])
        act = GC.activity(activity=activity_date)
        act_intervals = GC.activityIntervals(type="USER", activity=activity_date)
        activities.append({
            'activity': pd.DataFrame(act, index=act['seconds']),
            'metrics': activity_metric[0],
            'intervals': act_intervals,
        })

    interval_options = []
    for activity in activities:
        time_title = "(" + str(datetime.combine(activity['metrics']['date'], activity['metrics']['time'])) + ")"
        intervals = activity['intervals']
        for i in range(len(intervals['name'])):
            name = intervals['name'][i]
            interval_options.append({"label": name + " " + time_title, "value": name + ";;" + time_title})

    print('Gathering data duration: {}'.format(datetime.now() - start_time))

    app = dash.Dash(assets_folder=assets_dir)

    app.layout = html.Div([
        html.Div([
            "Select smooth value for graph: ",
            dcc.Slider(
                id='smooth-value-ride-plot',
                min=1,
                max=200,
                step=4,
                value=20,
            )
        ], className="row",
            style={"display": "block", "margin-left": "0px", "width": "500px"}),
        html.P(dcc.Graph(id="ride-plot-graph-smooth"), className="ride_plot"),
        html.Div([html.Pre(id='zoom-data')], ),
        html.Div([dcc.Dropdown(id="interval-value", value="", multi=True,
                               options=interval_options)],
                 className="row",
                 style={"display": "block", "width": "60%", "margin-left": "auto",
                        "margin-right": "auto"}),
        html.P(dcc.Graph(id="interval-plot-graph-smooth"), className="ride_plot"),
        html.Div([html.Pre(id='zoom-data-interval')], ),

    ], className='container')

    @app.callback(Output('ride-plot-graph-smooth', 'figure'),
                  [Input('smooth-value-ride-plot', 'value')])
    def update_smooth_ride_plot(smooth_value):
        before = datetime.now()
        fig = ride_plot_smooth(activities, smooth_value=int(smooth_value))
        print('Create ride plot duration: {}'.format(datetime.now() - before))
        return fig

    @app.callback(Output('interval-plot-graph-smooth', 'figure'),
                  [Input('smooth-value-ride-plot', 'value'),
                   Input('interval-value', 'value')])
    def update_interval_plot(smooth_value, interval_selected):
        before = datetime.now()
        fig = interval_plot_smooth(activities, interval_selected, smooth_value)
        print('Create interval plot duration: {}'.format(datetime.now() - before))
        return fig

    @app.callback(Output('zoom-data', 'children'),
                  [Input('ride-plot-graph-smooth', 'relayoutData')])  # this triggers the event
    def zoom_event(relayout_data):
        header = [html.Th('metric')]
        table_rows_data = []
        tr_power = [html.Td('Avg Power')]
        tr_heartrate = [html.Td('Avg HR')]
        tr_cadence = [html.Td('Avg Cadence')]
        for activity in activities:
            act1 = activity['activity'].filter(["seconds", "power", "heart.rate", "cadence"])
            start = act1.seconds.iloc[0]
            stop = act1.seconds.iloc[-1]

            if relayout_data and 'xaxis.range[0]' in relayout_data:
                act1 = act1.loc[
                    (act1.seconds >= relayout_data['xaxis.range[0]']) & (act1.seconds <= relayout_data['xaxis.range[1]'])]
                start = relayout_data['xaxis.range[0]']
                stop = relayout_data['xaxis.range[1]']

            header.append(html.Th(" (" + str(datetime.combine(activity['metrics']['date'], activity['metrics']['time'])) + ")"))

            metric = 'power'
            if metric in act1:
                tr_power.append(html.Td(round(act1.power.mean(), 2)))

            metric = 'heart.rate'
            if metric in act1:
                tr_heartrate.append(html.Td(round(act1[metric].mean(), 2)))

            metric = 'cadence'
            if metric in act1:
                tr_cadence.append(html.Td(round(act1[metric].mean(), 2)))

        table_rows_data.append(html.Tr(tr_power))
        table_rows_data.append(html.Tr(tr_heartrate))
        table_rows_data.append(html.Tr(tr_cadence))

        return html.Div([
            html.H1("Selected Time: " + str(format_hms_seconds(start)) + " - " + str(format_hms_seconds(stop))),
            html.Table(
                [html.Tr(header)] +
                [tr for tr in table_rows_data]
            )

        ])

    @app.callback(Output('zoom-data-interval', 'children'),
                  [Input('interval-plot-graph-smooth', 'relayoutData'),  # this triggers the event
                   Input('interval-value', 'value')])
    def zoom_event_interval(relayout_data, intervals_selected):
        start = 0
        stop = 0

        header = [html.Th('metric')]
        table_rows_data = []
        tr_power = [html.Td('Avg Power')]
        tr_heartrate = [html.Td('Avg HR')]
        tr_cadence = [html.Td('Avg Cadence')]
        for process_interval in intervals_selected:
            interval_name, activity_date = process_interval.split(";;")
            for process_activity in activities:
                current_time_title = "(" + str(
                    datetime.combine(process_activity['metrics']['date'], process_activity['metrics']['time'])) + ")"
                if current_time_title == activity_date:
                    process_intervals = process_activity['intervals']
                    for index in range(len(process_intervals['name'])):
                        if process_intervals['name'][index] == interval_name:
                            act1 = process_activity['activity'].filter(["seconds", "power", "heart.rate", "cadence"])
                            act1 = act1.loc[(act1.seconds >= process_intervals['start'][index]) & (act1.seconds <= process_intervals['stop'][index])]
                            act1.seconds = np.arange(len(act1))
                            stop = max(stop, act1.seconds.iloc[-1])

                            if relayout_data and 'xaxis.range[0]' in relayout_data:
                                act1 = act1.loc[
                                    (act1.seconds >= relayout_data['xaxis.range[0]']) & (act1.seconds <= relayout_data['xaxis.range[1]'])]
                                start = relayout_data['xaxis.range[0]']
                                stop = relayout_data['xaxis.range[1]']

                            header.append(html.Th(interval_name + " (" + str(datetime.combine(activity['metrics']['date'], activity['metrics']['time'])) + ")"))
                            metric = 'power'
                            if metric in act1:
                                tr_power.append(html.Td(round(act1.power.mean(), 2)))

                            metric = 'heart.rate'
                            if metric in act1:
                                tr_heartrate.append(html.Td(round(act1[metric].mean(), 2)))

                            metric = 'cadence'
                            if metric in act1:
                                tr_cadence.append(html.Td(round(act1[metric].mean(), 2)))

        table_rows_data.append(html.Tr(tr_power))
        table_rows_data.append(html.Tr(tr_heartrate))
        table_rows_data.append(html.Tr(tr_cadence))
        return html.Div([
            html.H1("Selected Time: " + str(format_hms_seconds(start)) + " - " + str(format_hms_seconds(stop))),
            html.Table(
                [html.Tr(header)] +
                [tr for tr in table_rows_data]
            )

        ])

    return app


def get_layout(title):
    return dict(title=title,
                height=chart_height,
                paper_bgcolor=gc_bg_color,
                plot_bgcolor=gc_bg_color,
                hovermode='x',
                xaxis=dict(
                    zeroline=True,
                    showline=True,
                    showgrid=False,
                    tickformat='%H:%M:%S',
                    nticks=25,
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=True,
                    showline=True,
                    rangemode='tozero',
                    fixedrange=True,
                    autorange=True,
                ),
                font=dict(
                    color=gc_text_color,
                    size=chart_title_size,
                ),
                margin={"r": 5, "t": 50, "l": 5, "b": 20},
                )


def format_hms_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    return '%02d:%02d:%02d' % (hours, minutes, secs)


def format_hms_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    return '%02d:%02d:%02d' % (hours, minutes, secs)


def ride_plot_smooth(activities, smooth_value=20):
    fig = go.Figure()
    for activity in activities:
        act = activity['activity'].filter(["seconds", "power", "heart.rate", "cadence"])
        intervals = activity['intervals']
        act['seconds_fmt'] = act.apply(lambda row: format_hms_seconds(row.seconds), axis=1)
        time_title = " (" + str(datetime.combine(activity['metrics']['date'], activity['metrics']['time'])) + ")"
        field = 'power'
        if field in act:
            fig.add_trace(
                add_line(act, field, field + time_title, field, smooth_value)
            )
        field = 'heart.rate'
        if field in act:
            group = 'HR'
            fig.add_trace(
                add_line(act, field, group + time_title, group, smooth_value)
            )
        field = 'cadence'
        if field in act:
            fig.add_trace(
                add_line(act, field, field + time_title, field, smooth_value)
            )

        act['hovertext'] = ""
        for i in range(len(intervals['name'])):
            x = format_hms_seconds(intervals['start'][i])
            fig.add_shape(go.layout.Shape(type="line",
                                          yref="paper",
                                          xref="x",
                                          x0=x,
                                          y0=0,
                                          x1=x,
                                          y1=1,
                                          line=dict(color="RoyalBlue", width=1),
                                          # line=dict(color=colors[counter], width=3), ),
                                          ))
            start = intervals['start'][i]
            stop = intervals['stop'][i]
            hover_text = intervals['name'][i] + time_title
            act['hovertext'] = np.where((act['seconds'] >= start) & (act['seconds'] <= stop),
                                        np.where(act['hovertext'] == "", hover_text,
                                                 act['hovertext'] + ", " + hover_text),
                                        act['hovertext'])
        fig.add_trace(go.Scatter(name="",
                                 mode='lines',
                                 x=act.seconds_fmt,
                                 y=np.zeros(len(act.seconds_fmt)),
                                 hovertext=act.hovertext,
                                 showlegend=False,
                                 opacity=0
                                 ))

    fig.update_layout(get_layout("Ride Plot (smooth value:" + str(smooth_value) + ")"))
    return fig


def interval_plot_smooth(activities, interval_selected, smooth_value):
        fig = go.Figure()
        for process_interval in interval_selected:
            interval_name, activity_date = process_interval.split(";;")
            for process_activity in activities:
                time_title = "(" + str(
                    datetime.combine(process_activity['metrics']['date'], process_activity['metrics']['time'])) + ")"
                if time_title == activity_date:
                    process_intervals = process_activity['intervals']
                    for index in range(len(process_intervals['name'])):
                        if process_intervals['name'][index] == interval_name:
                            act1 = process_activity['activity'].filter(["seconds", "power", "heart.rate", "cadence"])
                            interval_name = process_intervals['name'][index]
                            start = process_intervals['start'][index]
                            stop = process_intervals['stop'][index]
                            act1 = act1.loc[(act1.seconds >= start) & (act1.seconds <= stop)]
                            act1.seconds = np.arange(len(act1))
                            act1['seconds_fmt'] = act1.apply(lambda row: format_hms_seconds(row.seconds), axis=1)
                            field = 'power'
                            if field in act1:
                                group = 'power'
                                fig.add_trace(
                                    add_line(act1, field, group + interval_name + time_title, group, smooth_value)
                                )
                            field = 'heart.rate'
                            if field in act1:
                                group = 'HR'
                                fig.add_trace(
                                    add_line(act1, field, group + interval_name + time_title, group, smooth_value)
                                )
                            field = 'cadence'
                            if field in act1:
                                group = 'cadence'
                                fig.add_trace(
                                    add_line(act1, field, group + interval_name + time_title, group, smooth_value)
                                )
        fig.update_layout(get_layout("Interval Plot (smooth value:" + str(smooth_value) + ")"))
        return fig


def add_line(act, field, name, group, smooth_value):
    return go.Scatter(
        x=act.seconds_fmt.values,
        y=act[field].rolling(smooth_value, min_periods=1).mean().values,
        mode='lines',
        name=name,
        legendgroup=group,
        line=dict(
            width=1,
        ),
    )


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
    '''
    Path(css_file).write_text(template)
    return asset_dir


def run_server(app):
    app.run_server(debug=False)


def kill_previous_dash_server():
    for thread in threading.enumerate():
        if thread.name == "dash":
            print("terminating thread:  " + str(thread.getName()))
            print("terminating thread_id :  " + str(thread.ident))
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), ctypes.py_object(SystemExit))


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
    # Use for development
    #run_server(main())
    GC.webpage("http://127.0.0.1:8050/")
