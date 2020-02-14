# Ride Plots V5 (Py)
# This is an python chart
# My take on a ride plot
# currently only for power with a smoothness (moving average) of 20)
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 initial chart
# V2 - 2019-10-29 - Make linux compatible
# V3 - 2019-11-11 - Update Error handling
# V4 - 2019-12-13 - remove plotly express
#                   add intervals to map
#                   add timeline to rideplot
#                   add TSB vs IF
#                   add medals HR and power
# V5 - 2020-01-05 - remove plotly bars + default disable interval traces in legend



from GC_Wrapper import GC_wrapper as GC

import pathlib
import pandas as pd
import plotly
import plotly.graph_objs as go
import tempfile
import math
import numpy as np
from pathlib import Path
import dateutil
from datetime import datetime

smooth_value = 20

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

show_interval_type = "USER"

chart_title_size = 10

best_peaks_of_x_months = 12


def main():

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

    season_peaks = pd.DataFrame(GC.seasonMetrics(all=True, filter='Data contains "P"'))
    end_gather_time = datetime.now()
    print('Gathering data duration: {}'.format(end_gather_time - start_time))


    # Possible to override colors
    # zone_colors = ["rgb(127, 127, 127)",
    #                "rgb(255, 85, 255)",
    #                "rgb(51, 140, 255)",
    #                "rgb(89, 191, 89)",
    #                "rgb(255, 204, 63)",
    #                "rgb(255, 102, 57)",
    #                "rgb(255, 51, 12)"]
    if 'latitude' in activity:
        before = datetime.now()
        geo_html = geo_plot_html(activity, intervals, show_interval_type)
        print('Create map html duration: {}'.format(datetime.now() - before))

    else:
        geo_html = "<h2>Unable to draw activities ride plot no GPS data</h2>"

    if 'power' in activity:
        before = datetime.now()
        tiz_power_html = tiz_html(activity_metric, zone, type="L")
        print('Create time in zone power html duration: {}'.format(datetime.now() - before))
        if 'latitude' in activity:
            before = datetime.now()
            ride_html = ride_plot_html(activity, zone_colors, zones_low)
            print('Create ride html duration: {}'.format(datetime.now() - before))
        else:
            ride_html = "<h2>Unable to draw activities ride plot no GPS data</h2>"
        before = datetime.now()
        tsb_if_power_html = tsb_if_html(activity_metric, pmc)
        print('Create tsb vs if html duration: {}'.format(datetime.now() - before))
        before = datetime.now()
        medals_power_html = get_medals_html(activity_metric, season_peaks)
        print('Create medals power html duration: {}'.format(datetime.now() - before))
    else:
        ride_html = "<h2>Unable to draw activities ride plot (no power data)</h2>"
        tiz_power_html = "<h2>Unable to draw Time in Zone power (no power data)</h2>"
        tsb_if_power_html = "<h2>Unable to draw TSB vs IF (no power data)</h2>"
        medals_power_html = ""

    if 'heart.rate' in activity:
        before = datetime.now()
        tiz_hr_html = tiz_html(activity_metric, zone, type="H")
        print('Create time in zone hr html duration: {}'.format(datetime.now() - before))
        before = datetime.now()
        medals_hr_html = get_medals_html(activity_metric, season_peaks, HR=True)
        print('Create medals hr html duration: {}'.format(datetime.now() - before))
    else:
        tiz_hr_html = "<h2>Unable to draw Time in Zone heart rate (no HR data)</h2>"
        medals_hr_html = ""

    before = datetime.now()
    create_end_html_float(activity_metric, medals_power_html, medals_hr_html, geo_html, ride_html, tiz_power_html, tiz_hr_html, tsb_if_power_html)
    print('Create end html duration: {}'.format(datetime.now() - before))

    end_total_time = datetime.now()
    print('Complete duration: {}'.format(end_total_time - start_time))
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_medals_html(activity_metric, season_peaks, HR=False):
    if HR:
        metric_duration_name = ["1_min", "5_min", "10_min", "20_min", "30_min", "60_min"]
    else:
        metric_duration_name = ["1_sec", "5_sec", "10_sec", "15_sec", "20_sec", "30_sec", "1_min", "2_min", "3_min",
                                "5_min", "8_min", "10_min", "20_min", "30_min", "60_min", "90_min"]

    season_peaks = season_peaks.filter(regex="^date$|^time$|_Peak_Power$|_Peak_Power_HR$", axis=1)

    rows = ""
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

        sorted_all_time_season_peaks = all_time_season_peak.sort_values(by=[metric_name],ascending=False)[:3]
        sorted_last_x_months_season_peak_ = last_x_months_season_peak.sort_values(by=[metric_name],
                                                                                  ascending=False)[:3]

        curr_peak_activity = activity_metric[metric_name]

        sorted_all_time_season_peaks_tolist = sorted_all_time_season_peaks[metric_name].tolist()
        sorted_x_months_season_peaks_tolist = sorted_last_x_months_season_peak_[metric_name].tolist()
        row = get_html_table_row(curr_peak_activity, sorted_all_time_season_peaks_tolist, metric_prefix,
                                 "All Time", HR)
        if row:
            rows = rows + str(row)
        else:
            row = get_html_table_row(curr_peak_activity, sorted_x_months_season_peaks_tolist,
                                     metric_prefix, "Last " + str(best_peaks_of_x_months) + " Months", HR)
            if row:
                rows = rows + str(row)

    return get_html_medal_table(rows)


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


    return "<tr>" + \
           "<td><img src=" + img_location + " width=\"35\" height=\"60\" /></td>" + \
           "<td style=\"vertical-align: top;\"><strong>" + str(peak) + "</strong>" + \
           "<br />" + \
           "<br />" + \
           str(duration_name.replace("_", " ")) + suffix + \
           "</td>" + \
           "<td style=\"vertical-align: top;\">" + str(period) + "</td>" + \
           "</tr>"


def get_html_medal_table(rows):
    return '''
                <table>
                <tbody>
                ''' + str(rows) + '''
                </tbody>
                </table>        
             '''


def tsb_if_html(activity_metric, pmc):
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

    return plotly.offline.plot(fig, output_type='div')


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


def tiz_html(metrics, zone, type="L"):
    # type L = Power
    # type H = Heart rate

    # if heart rate assume 5 zones unable to get hr zones via python or R
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

    font_df = dict(family='Arial', size=10,
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
        text = str(round(pct)) + "% / " + str(format_seconds(time))

        # per charter add 20px to move the hover text to the correct place
        # TODO Calculate movement of the text
        #  power has more levels,
        #  so time more divided so less move needed for the text could be calculated i.s.o fixed values
        if type == "L":
            x = time + (len(text)*15)
        else:
            x = time + (len(text)*30)

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
        title="Time in zone power" if type == "L" else "Time in zone HR",
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


def geo_plot_html(activity, intervals, map_interval_type):
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
                visible="legendonly",
                name=row["name"]
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
    # fig.update_layout(legend_orientation="h")
    return plotly.offline.plot(fig, output_type='div', auto_open=False)


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
            size=chart_title_size,
        ),
        margin={"r": 5, "t": 50, "l": 5, "b": 20},
    )
    return plotly.offline.plot(fig, output_type='div', auto_open=False)


def create_end_html_float(activity_metric, medals_power_html, medals_hr_html, map_html, ride_html, tiz_power_html, tiz_hr_html, tsb_if_power_html):
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

            /* Disable ploty bars*/ 
             .modebar {
                display: none !important;
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
            }
            .medals_hr {
                margin-right: 100px;
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
            }
            </style>        
        </head>
        <body>
          <div class=top>
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
              <div class="medals_power">
              MEDALS Power
              ''' + str(medals_power_html) + ''' 
              </div>
              <div class="medals_hr">
              MEDALS Heart rate
              ''' + str(medals_hr_html) + ''' 
              </div>
          </div>
            <div class="container">
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
                  <div class="tsb_if">
                  ''' + str(tsb_if_power_html) + '''
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
