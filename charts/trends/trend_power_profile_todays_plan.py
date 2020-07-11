# Power Profile V7 (Py)
# This is an python chart
# Based on an power profile chart it maps your best 3s, 10s, 30s, 1m,3m, 6m,15m, 20m, 40m, 1h(FT).
# This chart helps to determine where the strengths and weaknesses are for an athlete (based on peak power)
# It shows always your best ever and overlays the selected date range. Also possible to compare multiple date ranges.
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2019-07-21: Initial Chart
# V2 - 2019-07-26: add different lengths  3s, 10s, 30s, 1m,3m, 6m,15m, 40m, 1h(FT)
# V3 - 2019-10-16: * refactor use of functions,
#                  * add activities date and names
#                  * add 20m FTP duration
#                  * use current weight of athlete
# V4 - 2019-10-22: small fix best ever hover text
# V5 - 2019-10-29: Make linux compatible
# V6 - 2019-11-13: Executable when no Workout_Title
# V7 - 2020-07-11: Update plotly syntax + workaround for 8px margin (done by Poncho)

from GC_Wrapper import GC_wrapper as GC

from pathlib import Path
import bisect
import tempfile
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import datetime

# Usage define duration and corresponding names (x-axis)
# Today's Plan Performance Index values
#    Peak: 3 second power
#    Sprint: 10 second power
#    Long sprint: 30 second power
#    Lactate: tolerance: 1 minute power
#    Maximum aerobic power: 3 minute power
#    Sustained aerobic power: 6 minute power
#    Short endurance: 15 minute power
#    Long endurance: 40 minute power

durations = [3, 10, 30, 60, 180, 360, 900, 1200, 2400, 3600, 5400]
x_labels = ['Peak (3s)',
            'Sprint (10s)',
            'Long Sprint(30s)',
            'Lactate tolorance (1m)',
            'Maximum aerobic power (3m)',
            'Sustained aerobic power (6m)',
            'Short endurance (15m)',
            'FTP Test (20m)',
            'Long endurance (40m)',
            'FT (1h)',
            'LT (1h30m)',
            ]



# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)
# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


def main():
    athlete = GC.athlete()
    athlete_name = athlete['name']
    athlete_gender = athlete['gender']

    # TODO investigate if/how FTP/CP and weight is needed from specific time i.s.o. latest.
    try:
        body_measurements = GC.seasonMeasures(all=True, group="Body")
        athlete_kg = body_measurements['Weight'][-1]
        # when athlete weight incorrect fall back on athlete default weight
        if athlete_kg <= 0:
            athlete_kg = athlete['weight']
    except (SystemError, TypeError):
        # when an exception might be thrown when no body measures are used fall back on athlete default weight
        athlete_kg = athlete['weight']
    azz = GC.athleteZones(date=0, sport='bike')
    inckg = 1  # real value = 1
    lcp = azz['cp'][-1] * inckg
    lftp = azz['ftp'][-1] * inckg

    # Fetch meanmax power for current selected season Bike activities
    selected_date_ranges = GC.season(compare=True)

    # Fetch all season metrics (used to determine workout title)
    all_season_metrics = GC.seasonMetrics(all=True)

    best_peaks = {}
    for duration in durations:
        best_peaks['best_peaks' + str(duration)] = GC.seasonPeaks(all=True,
                                                                  filter='Data contains "P"',
                                                                  series="wpk",
                                                                  duration=duration)

    date_ranges_peaks = {}
    for duration in durations:
        date_ranges_peaks['date_ranges_peaks' + str(duration)] = GC.seasonPeaks(filter='Data contains "P"',
                                                                                series="wpk",
                                                                                duration=duration,
                                                                                compare=True)

    # Power profile chart Allen Hunter 2019
    power_profile_category = [
        ' ',
        'Novice1',
        'Novice2',
        'Fair',
        'Moderate',
        'Good',
        'Very good',
        'Excellent',
        'Exceptional',
        'World class',
    ]

    ipv5s = 1.05  # (var estimate...)
    ipv1h = 0.01667  # (var estimate...)

    tm = np.arange(0, durations[len(durations) - 1] + 1)
    pvm = len(tm) / 3600
    # Power profile chart values
    world_class = pd.Series([23.06 * ipv5s, 23.06, 10.68, 6.86, 5.93, 5.93 * (1 - (ipv1h * pvm))])
    exceptional = pd.Series([21.25 * ipv5s, 21.25, 9.97, 6.23, 5.36, 5.36 * (1 - (ipv1h * pvm))])
    excellent = pd.Series([19.43 * ipv5s, 19.43, 9.27, 5.59, 4.79, 4.79 * (1 - (ipv1h * pvm))])
    very_good = pd.Series([17.61 * ipv5s, 17.61, 8.57, 4.96, 4.22, 4.22 * (1 - (ipv1h * pvm))])
    good = pd.Series([15.80 * ipv5s, 15.80, 7.86, 4.32, 3.65, 3.65 * (1 - (ipv1h * pvm))])
    moderate = pd.Series([13.98 * ipv5s, 13.98, 7.16, 3.69, 3.08, 3.08 * (1 - (ipv1h * pvm))])
    fair = pd.Series([12.17 * ipv5s, 12.17, 6.45, 3.06, 2.51, 2.51 * (1 - (ipv1h * pvm))])
    novice2 = pd.Series([10.35 * ipv5s, 10.35, 5.75, 2.42, 1.93, 1.93 * (1 - (ipv1h * pvm))])
    novice1 = pd.Series([8.23 * ipv5s, 8.23, 4.93, 1.68, 1.27, 1.27 * (1 - (ipv1h * pvm))])
    untrained = pd.Series([0, 0, 0, 0, 0, 0])

    # world_class
    # exceptional Domestic_pro
    # excellent   Cat1
    # very_good   Cat2
    # good        Cat3
    # moderate    Cat4
    # fair        Cat5
    # novice2     Untrained2
    # novice1     Untrained1
    # Untrained1

    # Default power profile chart durations
    if durations[len(durations) - 1] >= 3600:
        pp_durations = [1, 5, 60, 300, 3600, len(tm) - 1]
    if durations[len(durations) - 1] < 3600:
        pp_durations = [1, 5, 60, 300, len(tm) - 1, 3600]

    pan = [untrained, novice1, novice2, fair, moderate, good, very_good, excellent, exceptional, world_class]

    mmpsdf = pd.DataFrame()
    # fill in the for every category the W/Kg values determined by power profile chart
    for i in range(len(power_profile_category)):
        mmpsdf[power_profile_category[i]] = np.where(tm == pp_durations[0], pan[i][0],
                                                     np.where(tm == pp_durations[1], pan[i][1],
                                                              np.where(tm == pp_durations[2], pan[i][2],
                                                                       np.where(tm == pp_durations[3], pan[i][3],
                                                                                np.where(tm == pp_durations[4],
                                                                                         pan[i][4],
                                                                                         np.where(tm == pp_durations[5],
                                                                                                  pan[i][5],
                                                                                                  np.nan))))))

    # Interpolate values between de default durations
    mmpsdf[power_profile_category] = mmpsdf[power_profile_category].interpolate(method='pchip')

    best_peaks_y_values = determine_best_peak(best_peaks, all_season_metrics, durations, mmpsdf, power_profile_category)

    selected_date_ranges_y = determine_season_peaks(date_ranges_peaks, selected_date_ranges, all_season_metrics,
                                                    durations, mmpsdf, power_profile_category)

    print("Season Y values" + str(selected_date_ranges_y))

    y_scale = np.arange(0, len(power_profile_category))

    # Create the plot
    fig = go.Figure()

    # Add annotations used for the y-axis labels
    for i in y_scale:
        fig.add_annotation(
            x=-0.9,
            y=i + 0.5,
            xref='x',
            yref='y',
            text=power_profile_category[i],
            showarrow=False,
        )

    # Add annotation for athlete information
    fig.add_annotation(
        x=len(x_labels) / 2,
        y=9.8,
        # x=-0.01,
        # y=1.1,
        text="Athlete: " + str(athlete_name)
             + '<br>Gender: ' + str(athlete_gender)
             + '<br>Weight:' + str(round(athlete_kg, 1)) + "kg  "
             + '<br>FTP: ' + str(round(lftp / athlete_kg, 1)) + "W/kg, "
             + str(round(lftp)) + "W"
             + '<br>CP: ' + str(round(lcp / athlete_kg, 1)) + "W/kg, "
             + str(round(lcp)) + "W",
        showarrow=False,
        font=dict(
            size=11,
            color='rgb(210,210,210)'),
        align='left',
    )

    # Add bars for the best ever peaks mapped on category
    fig.add_trace(go.Bar(
        x=x_labels,
        y=best_peaks_y_values['peaks_weighted'],
        name='Best Ever',
        hovertext=[determine_hover_text(peak, date, name, athlete_kg)
                   for peak, date, name in
                   zip(best_peaks_y_values['peaks'],
                       best_peaks_y_values['activity_dates'],
                       best_peaks_y_values['activity_names'])],

        hoverinfo="text",
        marker=dict(
            color='orange',
        )
    ))

    # Per date range add a smooth line (spline) to compare to your best
    for season_dict in selected_date_ranges_y:
        print(season_dict)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=season_dict['peaks_weighted'],
            hovertext=[determine_hover_text(peak, date, name, athlete_kg)
                       for peak, date, name
                       in zip(season_dict['peaks'], season_dict['activity_dates'], season_dict['activity_name'])],

            hoverinfo="text",
            mode='lines+markers',
            showlegend=True,
            line_shape='spline',
            name=season_dict['name'],
            line=dict(color=season_dict['color']),
        ))

    # 11.26 W/Kg for 5s is stated as untrained values
    date_ranges_peaks5 = {'peak_wpk_5': [11.26]}
    average_untrained_weighted = get_category_index_value(5, date_ranges_peaks5, mmpsdf, power_profile_category)
    fig.add_annotation(
        x=len(x_labels) - 0.1,
        y=average_untrained_weighted - 0.2,
        text='Average <br>Untrained',
        align='left',
        showarrow=False,
    )

    fig.update_layout(
        margin=dict(
            l=20,
            r=50,
            b=150,
            t=100,
            pad=4
        ),

        title='Power Profile ' + str(athlete['name']),
        paper_bgcolor=gc_bg_color,
        plot_bgcolor=gc_bg_color,
        font=dict(
            color=gc_text_color,
            size=12
        ),
    )

    # Add horizontal average untrained line
    fig.add_shape(
        type="line",
        x0=-1,
        y0=average_untrained_weighted,
        x1=len(x_labels),
        y1=average_untrained_weighted,
        line=dict(
            color="Red",
            dash="dashdot",
        ),
    )

    fig.update_xaxes(
        showline=False,
        showgrid=False,
    )

    fig.update_yaxes(
        showticklabels=False,
        tickvals=y_scale,
        range=[0, max(y_scale) + 1],
        gridwidth=2,
        gridcolor='DarkGray',
    )

    fig.write_html(temp_file.name, auto_open=False)
    text = Path(temp_file.name).read_text()
    text = text.replace('<body>', '<body style="margin: 0px;">')
    Path(temp_file.name).write_text(text)
    GC.webpage(Path(temp_file.name).as_uri())


def determine_season_peaks(date_ranges_peaks, selected_date_ranges, all_season_metrics, durations, mmpsdf,
                           power_profile_category):
    # Determine y values peaks for every selected season
    selected_date_ranges_y = []
    for color, name in zip(selected_date_ranges['color'], selected_date_ranges['name']):
        print("name: " + str(name) + ", color: " + str(color))
        current_date_range_y_values_weighted = []
        current_date_range_y_values = []
        current_date_range_activity_dates = []
        current_date_range_activity_names = []

        for current_duration in durations:
            # print("Season peaks current Duration: " + str(current_duration))
            selected_date_range_peaks_of_duration = date_ranges_peaks['date_ranges_peaks' + str(current_duration)]

            # When multiple date ranges (compares) are selected iterate
            if len(selected_date_range_peaks_of_duration) > 1:
                # find corresponding peak done by color matching
                for peak in selected_date_range_peaks_of_duration:
                    # print('compare color:' + str(color) + ', peaks color: ' + str(peak[1]))
                    if peak[1] == color:
                        current_date_range_y_values_weighted.append(
                            get_category_index_value(current_duration, peak[0], mmpsdf, power_profile_category))
                        current_date_range_y_values.append(max(peak[0]['peak_wpk_' + str(current_duration)]))

                        # get activities dates
                        index = peak[0]['peak_wpk_' + str(current_duration)].index(
                            max(peak[0]['peak_wpk_' + str(current_duration)]))
                        current_date = peak[0]['datetime'][index]
                        current_date_range_activity_dates.append(current_date)
                        current_date_range_activity_names.append(get_activity_title(all_season_metrics, current_date))

            else:
                current_date_range_y_values_weighted.append(
                    get_category_index_value(current_duration, selected_date_range_peaks_of_duration[0][0],
                                             mmpsdf, power_profile_category))
                current_date_range_y_values.append(
                    max(selected_date_range_peaks_of_duration[0][0]['peak_wpk_' + str(current_duration)]))

                # get activities dates
                index = selected_date_range_peaks_of_duration[0][0]['peak_wpk_' + str(current_duration)].index(
                    max(selected_date_range_peaks_of_duration[0][0]['peak_wpk_' + str(current_duration)]))
                current_date = selected_date_range_peaks_of_duration[0][0]['datetime'][index]
                current_date_range_activity_dates.append(current_date)
                current_date_range_activity_names.append(get_activity_title(all_season_metrics, current_date))

        selected_date_ranges_y.append({'name': name,
                                       'peaks_weighted': current_date_range_y_values_weighted,
                                       'peaks': current_date_range_y_values,
                                       'activity_dates': current_date_range_activity_dates,
                                       'activity_name': current_date_range_activity_names,
                                       'color': color,
                                       })
    return selected_date_ranges_y


def determine_best_peak(best_peaks, all_season_metrics, durations, mmpsdf, power_profile_category):
    ret_val = {}
    # Determine y values for best ever peaks
    best_peaks_y_values_weighted = []
    best_peaks_y_values = []
    best_activity_dates = []
    best_activity_names = []
    for current_duration in durations:
        # print('Best peak current Duration: ' + str(current_duration))
        current_best_peaks = best_peaks['best_peaks' + str(current_duration)]
        max_current_best_peak = max(current_best_peaks['peak_wpk_' + str(current_duration)])

        # get weighted
        best_peaks_y_values_weighted.append(get_category_index_value(current_duration, current_best_peaks,
                                                                     mmpsdf, power_profile_category))
        best_peaks_y_values.append(max_current_best_peak)

        # get activities dates
        index = current_best_peaks['peak_wpk_' + str(current_duration)].index(max_current_best_peak)
        current_date = current_best_peaks['datetime'][index]
        best_activity_dates.append(current_date)
        best_activity_names.append(get_activity_title(all_season_metrics, current_date))
    print('Best Peaks Y values weighted: ' + str(best_peaks_y_values_weighted))
    print('Best Peaks Y values: ' + str(best_peaks_y_values))

    ret_val["peaks_weighted"] = best_peaks_y_values_weighted
    ret_val["peaks"] = best_peaks_y_values
    ret_val["activity_dates"] = best_activity_dates
    ret_val["activity_names"] = best_activity_names
    return ret_val


def get_activity_title(metrics, find_date):
    ret_val = "No workout title found"
    for metric_index in np.arange(0, len(metrics['date'])):
        cur_date = metrics['date'][metric_index]
        if datetime.datetime(cur_date.year, cur_date.month, cur_date.day) == datetime.datetime(find_date.date().year,
                                                                                               find_date.date().month,
                                                                                               find_date.date().day):
            cur_time = metrics['time'][metric_index]
            if datetime.time(cur_time.hour, cur_time.minute, cur_time.second) == find_date.time():
                if 'Workout_Title' in metrics:
                    ret_val = metrics['Workout_Title'][metric_index]
                else:
                    ret_val = ""
                break;
    return ret_val


def get_category_index_value(duration, peaks, mmpsdf, power_profile_category):
    """
     Based on Andrew Coggan and Allen Hunter cycling profile chart
     Determine in which category you belong for a certain duration
    """
    limits = [mmpsdf[category][duration] for category in power_profile_category]

    peak_wpk = max(peaks['peak_wpk_' + str(duration)])

    # print('season: Best ever, duration: ' + str(current_duration) + ', wpk max: ' + str(peak_wpk))
    index = bisect.bisect_left(limits, peak_wpk) - 1

    print(str(peak_wpk) + " W/Kg, index of limits: " + str(limits[index]) +
          ", Power profile category: " + str(power_profile_category[index]))

    # calculate percentage between category
    pct = (peak_wpk - limits[index]) / (limits[index + 1] - limits[index])
    return index + pct


def determine_hover_text(peak, date, name, athlete_kg):
    linefeed = "<br>"
    return_value = 'W/Kg  : ' + str(round(peak, 2)) + linefeed
    return_value += 'Watts : ' + str(round(peak * athlete_kg, 2)) + linefeed
    return_value += 'Activity date : ' + str(date) + linefeed
    if name != "":
        return_value += 'Activity Name : ' + str(name) + linefeed
    return return_value


if __name__ == "__main__":
    main()
