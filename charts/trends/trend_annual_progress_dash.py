# Annual progress V6 (Py)
# This is an python chart for GC 3.6
# WARNING: For this chart you need to configure your own python and install an extra package called dash
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2020-01-08 - initial chart
# V2 - 2020-01-11 - Fix threading (kill threads before start multiple dash chart_not_working_yet_after_single_extract)
# V3 - 2020-01-24 - add wait for server before loading webpage
# V4 - 2020-02-01 - make linux compatible
# V5 - 2020-06-28 - Add selection in graph
# V6 - 2020-08-23 - Add subplots (multiple metrics) + add selection line

from GC_Wrapper import GC_wrapper as GC

import calendar
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
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
import os
import numpy as np
import plotly
from decimal import Decimal, ROUND_HALF_UP

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'
chart_title_size = 10

styles = {
    'red': {
        'color': 'red',
    },
    'green': {
        'color': 'green',
    }
}

colors = plotly.colors.DEFAULT_PLOTLY_COLORS

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

##
# This function creates cumulative columns for every metric and also fill in empty days later for selection
##
def get_season_metrics_for_metrics_per_year(season_metrics):
    start_time = time.time()
    season_metrics['year'] = pd.to_datetime(season_metrics.date).dt.year
    years = sorted(season_metrics.year.unique().tolist(), reverse=True)

    filtered_season_metrics = pd.DataFrame()
    first = True
    for metric in get_cumulative_metrics().metric.tolist():
        metric_for_years = pd.DataFrame()
        for year in years:
            # filter year and selected metric
            dff = season_metrics[season_metrics.year == year][['date', 'year', metric]].copy()

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
            dff.insert(0, 'date', dff.index)

            # transform month number to readable month
            dff['year'] = year
            dff['month'] = pd.to_datetime(dff.index).month
            dff.month = dff.month.apply(lambda x: calendar.month_abbr[x])
            dff["period"] = pd.to_datetime(dff.index).day.astype(str) + '-' + dff.month

            # add column with the summarized values and interpolate in between values
            dff['cumsum_' + str(metric)] = dff[metric].cumsum()

            # create an opacity value for the days entries are found an marker can be placed
            dff['opacity'] = np.where(dff[metric] == 0.0, 0, 0.6)
            metric_for_years = pd.concat([metric_for_years, dff])

        if first:
            filtered_season_metrics = metric_for_years.copy()
            first = False
        else:
            filtered_season_metrics = pd.merge(filtered_season_metrics, metric_for_years[['date', str(metric), 'cumsum_'+str(metric)]], on='date')
    print("Processing data cost: " + str(time.time() - start_time))
    return filtered_season_metrics


def add_legend_data(fig, years):
    # workaround to get a custom legend
    for i in np.arange(0, len(years)):
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='lines+markers',
                marker=dict(size=8, color=colors[i]),
                legendgroup=years[i],
                showlegend=True,
                name=years[i],
            )
        )


def main():
    assets_dir = write_css()
    app = dash.Dash(assets_folder=assets_dir)

    season_metrics_raw = pd.DataFrame(GC.seasonMetrics(all=True))
    season_metrics = get_season_metrics_for_metrics_per_year(season_metrics_raw)

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
                           html.Div([dcc.Dropdown(id="type-value", value="Distance", multi=True,
                                                  options=metrics_options)],
                                    className="row",
                                    style={"display": "block", "width": "60%", "margin-left": "auto",
                                           "margin-right": "auto"}),
                           html.Div([dcc.Graph(id="my-graph")], ),
                           html.Div([html.Pre(id='click-data')],),
                           ], className="container")


    @app.callback(
        Output('my-graph', 'figure'),
        [Input('year-value', 'value'),
         Input('type-value', 'value'),
         Input('my-graph', 'clickData')
         ])
    def update_figure(selected, metrics, click_data):
        # if only one metric is selected it is not an list transform to list
        if not isinstance(metrics, list):
            metrics = [metrics]

        cols = 1
        if len(metrics) > 1:
            cols = 2
        rows = int(Decimal(len(metrics)/2).to_integral_value(rounding=ROUND_HALF_UP))
        row_height = 500
        fig = make_subplots(rows=rows,
                            cols=cols,
                            subplot_titles=metrics,
                            row_heights=np.full(rows, row_height).tolist())
        fig.update_layout(title="Aggregated '" + ','.join(metrics) + "'",
                          paper_bgcolor=gc_bg_color,
                          plot_bgcolor=gc_bg_color,
                          clickmode='event',
                          autosize=False,
                          height=row_height*rows,
                          font=dict(
                              color=gc_text_color,
                              size=chart_title_size,
                          ),
                          )

        row = 1
        col = 1
        chart_counter = 1
        vlines=[]
        for metric in metrics:
            metric_type = cumulative_metrics[cumulative_metrics.metric == metric].type.tolist()[0]
            if selected:
                # Workaround if there is an leap year you need to process that first
                # This because with x-axis not being a sequence number!!!
                # So change order of selected years
                reorder = False
                for selected_year in selected:
                    if calendar.isleap(selected_year):
                        reorder = True
                        first = selected_year
                if reorder and len(selected) > 1 and selected[0] != first:
                    selected.remove(first)
                    selected.insert(0, first)

                color_index = 0
                for selected_year in selected:
                    dff = season_metrics[season_metrics.year == selected_year].copy()
                    if metric_type == 'time':
                        hover_text = [
                            str(metric) + ": " + str(format_hms_seconds(duration)) + "<br>Date: " + date.strftime("%d-%m-%Y")
                            for duration, date in zip(dff[metric].cumsum().tolist(), dff.date)]
                    else:
                        hover_text = [str(metric) + ": " + str(cumsum) + "<br>Date: " + date.strftime("%d-%m-%Y") for
                                      cumsum, date in zip(dff[metric].cumsum().tolist(), dff.date)]

                    fig.append_trace(
                        go.Scatter(x=dff.period,
                                   y=dff['cumsum_'+str(metric)],
                                   # name=selected_year,
                                   mode='lines+markers',
                                   hoverinfo="text",
                                   hovertext=hover_text,
                                   showlegend=False,
                                   line={'color': colors[color_index]},
                                   marker={'size': 8,
                                           "opacity": dff.opacity,
                                           "line": {'width': 0.5,}
                                           },
                                   ),
                        row=row,
                        col=col
                    )
                    color_index = color_index + 1

            yaxis = {"title": metric,
                     "gridcolor": 'gray',
                     }
            max_y = season_metrics[season_metrics.year.isin(selected)].groupby(["year"])["cumsum_" + str(metric)].max().max()
            if metric_type == 'time':
                # season_metrics[season_metrics.year.isin()]
                season_metrics[season_metrics.year == selected_year].copy()
                number_of_ticks = 20
                # 5% large y axis for the visibility
                tickvals = range(0, int(max_y*1.05), int(max_y/number_of_ticks))
                ticktext = [format_hms_seconds(tickval) for tickval in tickvals]

                yaxis = {"title": metric,
                         "gridcolor": 'gray',
                         "tickvals": [tickval for tickval in tickvals],
                         "ticktext": ticktext,
                         }

            fig.update_yaxes(yaxis, row=row, col=col,)
            fig.update_xaxes(
                {"title": "Day of Year",
                 "gridcolor": 'gray',
                 "tickangle": 45,
                 },
                row=row,
                col=col,
            )
            if click_data:
                vlines.append(
                    dict(
                        type='line',
                        yref='y' + str(chart_counter), y0=0, y1=max_y*1.1,
                        xref='x' + str(chart_counter), x0=click_data['points'][0]['pointIndex'], x1=click_data['points'][0]['pointIndex'],
                        line=dict(
                            color="Red",
                            width=1
                        )
                    )
                )

            fig.update_layout(shapes=vlines)
            chart_counter = chart_counter + 1
            # set the next row and column
            if col == 2:
                col = 1
                row = row + 1
            else:
                col = 2
        add_legend_data(fig, selected)
        return fig

    @app.callback(
        Output('click-data', 'children'),
        [Input('my-graph', 'clickData'),
         Input('year-value', 'value'),
         Input('type-value', 'value')]
    )
    def display_click_data(click_data, selected_years, selected_metrics):
        if not click_data:
            return html.Div([html.H1("Selected a date")])
        else:
            selected_date = click_data['points'][0]['x']

            if not isinstance(selected_years, list):
                selected_years = [selected_years]

            if not isinstance(selected_metrics, list):
                selected_metrics = [selected_metrics]

            dff = season_metrics[(season_metrics.period == selected_date) & (season_metrics.year.isin(selected_years))].copy()
            dff = dff.sort_values('year')

            # Create header for table and
            header = [html.Th('Year')]
            for metric in selected_metrics:
                dff['delta_'+str(metric)] = round(dff['cumsum_' + str(metric)].diff(+1), 2)
                header.append(html.Th(metric))
                header.append(html.Th('Δ ' + str(metric)))

            # For every year create and new row in the table
            table_rows_data = []
            for i in range(len(dff)):
                tr = [html.Td(dff.iloc[i].year)]
                for metric in selected_metrics:
                    metric_type = cumulative_metrics[cumulative_metrics.metric == metric].type.tolist()[0]
                    cumsum = round(dff.iloc[i]['cumsum_' + str(metric)], 2)
                    delta = round(dff.iloc[i]['delta_' + str(metric)], 2)
                    if metric_type == 'time':
                        cumsum = format_hms_seconds(cumsum)
                        delta = format_hms_seconds(delta)

                    if dff.iloc[i]['delta_' + str(metric)] >= 0:
                        style = styles['green']
                    else:
                        style = styles['red']

                    tr.append(html.Td(cumsum))
                    tr.append(html.Td(delta, style=style))
                table_rows_data.append(html.Tr(tr))

            return html.Div([
                html.H1("Selected Date: " + str(click_data['points'][0]['x'])),

                html.Table(
                    [html.Tr(header)] +
                    [tr for tr in table_rows_data]
                )
            ])

    return app


def format_hms_seconds(secs):
    if not np.isnan(secs):
        minutes, secs = divmod(secs, 60)
        hours, minutes = divmod(minutes, 60)
        return '%02d:%02d:%02d' % (hours, minutes, secs)
    else:
        return ""


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

table, th, td {
  border: 1px solid white;
  border-collapse: collapse;
  padding: 8px;
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
    # kill_previous_dash_server()
    threading.Thread(target=run_server, args=(main(),), name="dash").start()
    wait_for_server()
    # run_server(main())
    GC.webpage("http://127.0.0.1:8050/")
