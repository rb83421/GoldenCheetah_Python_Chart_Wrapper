# Annual progress V4 (Py)
# This is an python chart
# WARNING: For this chart you need to install an extra package called dash
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2020-01-08 - initial chart
# V2 - 2020-01-11 - Fix threading (kill threads before start multiple dash chart_not_working_yet_after_single_extract)
# V3 - 2020-01-24 - add wait for server before loading webpage
# V4 - 2020-02-01 - make linux compatible
# V5 - 2020-06-28 - WIP add selection in graph
import calendar

from GC_Wrapper import GC_wrapper as GC

import sys
import time
import requests
import ctypes
from datetime import datetime
from pathlib import Path
import tempfile
import threading
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import os
import numpy as np

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'
chart_title_size = 10

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'hidden'
    }
}

def get_cumulative_metrics():
    data = [
        ["Distance", 'km'],
        ["Duration", 'time'],
        ["TSS", 'number'],
        ["IF", 'number'],
        ["Calories", 'number'],
        ["Activities", 'number'],
        ["BikeIntensity", 'number'],
        ["BikeStress", 'number'],
        ["aBikeScore", 'number'],
        ["Work", 'number'],
        ["Elapsed_Time", 'time'],
        ["Time_Moving", 'time'],
        ["Time_Carrying", 'time'],
        ["Elevation_Gain_Carrying", 'number'],
        ["TriScore", 'number'],

        # "aIF",
        # "aBikeStress",
        # "aBikeStress_per_hour",
        # "Elevation_Gain",
        # "Elevation_Loss",
        # "Aerobic_TISS",
        # "Anaerobic_TISS",
        # "Relative_Intensity",
        # "BikeScore&#8482;",
        # "TISS_Aerobicity",
        # "BikeStress_per_hour",
        # "H1_Time_in_Zone",
        # "H2_Time_in_Zone",
        # "H3_Time_in_Zone",
        # "H4_Time_in_Zone",
        # "H5_Time_in_Zone",
        # "H6_Time_in_Zone",
        # "H7_Time_in_Zone",
        # "H8_Time_in_Zone",
        # "H9_Time_in_Zone",
        # "H10_Time_in_Zone",
        # "P1_Time_in_Pace_Zone",
        # "P3_Time_in_Pace_Zone",
        # "P4_Time_in_Pace_Zone",
        # "P5_Time_in_Pace_Zone",
        # "P6_Time_in_Pace_Zone",
        # "P7_Time_in_Pace_Zone",
        # "P8_Time_in_Pace_Zone",
        # "P9_Time_in_Pace_Zone",
        # "P10_Time_in_Pace_Zone",
        # "Distance_Swim",
        # "L1_Sustained_Time",
        # "L2_Sustained_Time",
        # "L3_Sustained_Time",
        # "L4_Sustained_Time",
        # "L5_Sustained_Time",
        # "L6_Sustained_Time",
        # "L7_Sustained_Time",
        # "L8_Sustained_Time",
        # "L9_Sustained_Time",
        # "L10_Sustained_Time",
        # "SwimScore",
        # "L1_Time_in_Zone",
        # "L2_Time_in_Zone",
        # "L3_Time_in_Zone",
        # "L4_Time_in_Zone",
        # "L5_Time_in_Zone",
        # "L6_Time_in_Zone",
        # "L7_Time_in_Zone",
        # "L8_Time_in_Zone",
        # "L9_Time_in_Zone",
        # "L10_Time_in_Zone",
        # "TRIMP_Points",
        # "TRIMP(100)_Points",
        # "TRIMP_Zonal_Points",
        # "Session_RPE",
    ]

    return pd.DataFrame(data, columns=['metric', 'type'])



def main():
    assets_dir = write_css()
    app = dash.Dash(assets_folder=assets_dir)

    season_metrics = pd.DataFrame(GC.seasonMetrics(all=True))
    season_metrics['year'] = pd.to_datetime(season_metrics.date).dt.year

    years = sorted(season_metrics.year.unique().tolist(), reverse=True)
    year_options = []
    for year in years:
        year_options.append({"label": year, "value": year})

    metrics_options = []
    cumulative_metrics = get_cumulative_metrics()
    for column in cumulative_metrics.metric.tolist():
        metrics_options.append({"label": column, "value": column})

    app.layout = html.Div([html.Div([html.H1("Annual Progress Year")], style={'textAlign': "center"}),
                           html.Div([dcc.Dropdown(id="year-value", multi=True, value=[years[0]],
                                                  options=year_options)],
                                    className="row",
                                    style={"display": "block", "width": "60%", "margin-left": "auto",
                                           "margin-right": "auto"}),
                           html.Div([dcc.Dropdown(id="type-value", value="Distance",
                                                  options=metrics_options)],
                                    className="row",
                                    style={"display": "block", "width": "60%", "margin-left": "auto",
                                           "margin-right": "auto"}),
                           html.Div([dcc.Graph(id="my-graph")]),
                           html.Div([html.Pre(id='click-data', style=styles['pre']),
                           ], className='three columns'),
                           ], className="container")

    @app.callback(
        Output('my-graph', 'figure'),
        [Input('year-value', 'value'),
         Input('type-value', 'value'), ])
    def update_figure(selected, metric):
        print("update figure")
        metric_type = cumulative_metrics[cumulative_metrics.metric == metric].type.tolist()[0]
        trace = []
        max_cumsum = pd.Series(0)
        for selected_year in selected:
            # filter year and selected metric
            dff = season_metrics[season_metrics.year == selected_year][['date', 'year', metric]].copy()

            # summarize metric when multiple entries on one day
            dff[metric] = dff.groupby(['date'])[metric].transform('sum')
            # delete duplicate dates
            dff = dff.drop_duplicates(subset=['date'])

            # add days when no entry with (needed later for selection)
            processing_year = dff.year.iloc[0]
            current_year = datetime.now().year
            if processing_year == current_year:
                idx = pd.date_range('01-01-' + str(processing_year), dff.date.iloc[-1])
            else:
                idx = pd.date_range('01-01-' + str(processing_year), '31-12-' + str(dff.year.iloc[-1]))
            dff = dff.set_index('date')
            dff.index = pd.DatetimeIndex(dff.index)
            dff = dff.reindex(idx, fill_value=0)

            # transform month number to readable month
            dff['month'] = pd.to_datetime(dff.index).month
            dff.month = dff.month.apply(lambda x: calendar.month_abbr[x])
            dff["period"] = pd.to_datetime(dff.index).day.astype(str) + '-' + dff.month


            # add column with the summurized values and interpolate in between values
            dff['cumsum_'+str(metric)] = dff[metric].cumsum()
            # dff['cumsum_'+str(metric)] = dff['cumsum_' + str(metric)].interpolate()

            # create an opacity value for the days entries are found an marker can be placed
            dff['opacity'] = np.where(dff[metric] == 0.0, 0, 0.6)

            if metric_type == 'time':
                hover_text = [
                    str(metric) + ": " + str(format_hms_seconds(duration)) + "<br>Date: " + date.strftime("%d-%m-%Y")
                    for duration, date in zip(dff[metric].cumsum().tolist(), dff.index)]
            else:
                hover_text = [str(metric) + ": " + str(cumsum) + "<br>Date: " + date.strftime("%d-%m-%Y") for
                              cumsum, date in zip(dff[metric].cumsum().tolist(), dff.index)]

            trace.append(go.Scatter(x=dff.period,
                                    y=dff['cumsum_'+str(metric)],
                                    name=selected_year,
                                    mode='lines+markers',
                                    hoverinfo="text",
                                    hovertext=hover_text,
                                    marker={'size': 8, "opacity": dff.opacity, "line": {'width': 0.5}}, ))

        if metric_type == 'time':
            cumsum = max_cumsum.tolist()
            tickvals = [cumsum[i * 20] for i in range(int(len(cumsum) / 20) + 1)]
            tickvals.append(cumsum[-1])
            ticktext = [format_hms_seconds(tickval) for tickval in tickvals]
            yaxis = {"title": metric,
                     "gridcolor": 'gray',
                     "tickvals": tickvals,
                     "ticktext": ticktext,
                     }
        else:
            yaxis = {"title": metric,
                     "gridcolor": 'gray',
                     }

        tickvals_x = [i for i in range(1, 365, 10)]
        tickvals_x.append(365)
        ticktext_x = [datetime.strptime(str(tickval), "%j").strftime("%d-%b") for tickval in tickvals_x]

        return {
            "data": trace,
            "layout": go.Layout(title="Aggregated '" + str(metric) + "'",
                                xaxis={"title": "Day of Year",
                                       "gridcolor": 'gray',
                                       "tickangle": 45,
                                       "tickvals": tickvals_x,
                                       "ticktext": ticktext_x,
                                       },
                                yaxis=yaxis,
                                paper_bgcolor=gc_bg_color,
                                plot_bgcolor=gc_bg_color,
                                clickmode='event',
                                font=dict(
                                    color=gc_text_color,
                                    size=chart_title_size,
                                ),

                                )
        }

    @app.callback(
        Output('click-data', 'children'),
        [Input('my-graph', 'clickData'),
         Input('year-value', 'value'),
         Input('type-value', 'value'), ]
    )
    def display_click_data(click_data, selected_years, metric):
        if click_data:
            df = pd.DataFrame()

            for point in click_data['points']:
                new_row = {'year': point['hovertext'].split('-')[-1], 'metric': round(point['y'], 2)}
                # append row to the dataframe
                df = df.append(new_row, ignore_index=True)

            selected_x = click_data['points'][0]['x']
            selected_y = click_data['points'][0]['y']

            print("date selected: " + str(selected_x))
            print("Cumulative value" + str(selected_y))

            return html.Div([
                html.H1("Selected Date: " + str(selected_x)),

                html.Table(
                    # Header
                    [html.Tr([html.Th(col) for col in df.columns])] +

                    # Body
                    [html.Tr([
                        html.Td(
                            df.iloc[i][col]) for col in df.columns
                    ]) for i in range(min(len(df), 10))]
                )
            ])
            # return """
            # Date Selected:  """ + str(selected_x) + """
            # First Value:  """ + str(selected_y) + """
            # Raw data : """ + json.dumps(click_data, indent=2) + """
            #
            # """
        return html.Div([html.H1("Selected a date")])

    return app


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
}

.Select-menu-outer {
 background-color: ''' + gc_bg_color + ''';
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
    '''
    Path(css_file).write_text(template)
    return asset_dir


def kill_previous_dash_server():
    for thread in threading.enumerate():
        # print("Thread Running: " + str(thread.name) + ", deamon: " + str(thread.daemon))
        if thread.name == "dash":
            print("terminating thread:  " + str(thread.getName()))
            print("terminating thread_id :  " + str(thread.ident))
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), ctypes.py_object(SystemExit))


def run_server(dash_app):
    dash_app.run_server(debug=False)


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
    # Redirect stdout when running in GC else you get and CatchOutErr on file.flush of flask app
    # Temp till the following issue is fixed: https://github.com/GoldenCheetah/GoldenCheetah/issues/3293
    sys.stdout = open(os.path.join(tempfile.gettempdir(), "GC_server_annual_progress_year.log"), 'a')
    kill_previous_dash_server()
    threading.Thread(target=run_server, args=(main(),), name="dash").start()
    wait_for_server()
    # run_server(main())
    GC.webpage("http://127.0.0.1:8050/")
