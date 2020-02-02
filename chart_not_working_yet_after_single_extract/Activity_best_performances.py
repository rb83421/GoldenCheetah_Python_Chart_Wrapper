# xxxxx V1 (Py)
# This is an python chart
# <Description>
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 20xx-xx-xx - Initial chart
from datetime import timedelta

import dateutil

from GC_Wrapper import GC_wrapper as GC

import pathlib
import plotly
import plotly.graph_objs as go
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

best_peaks_of_x_months = 12


def main():
    activity_metric = GC.activityMetrics()
    act = GC.activity()
    activity = pd.DataFrame(act, index=act['seconds'])

    peak_duration = [1, 5, 10, 15, 20, 30, 60, 120, 180, 300, 480, 600, 1200, 1800, 3600, 5400]
    metric_duration_name = ["1_sec", "5_sec", "10_sec", "15_sec", "20_sec", "30_sec", "1_min", "2_min", "3_min",
                            "5_min", "8_min", "10_min", "20_min", "30_min", "60_min", "90_min"]
    season_peaks = pd.DataFrame(GC.seasonMetrics(all=True, filter='Data contains "P"'))
    season_peaks = season_peaks.filter(regex="^date$|^time$|_Peak_Power$", axis=1)

    rows = ""
    for i in range(len(peak_duration)):
        metric_name = metric_duration_name[i] + "_Peak_Power"
        # remove peaks after activity date
        all_time_season_peak = season_peaks.loc[
            (season_peaks.date <= activity_metric['date'])]
        last_x_months_date = activity_metric['date'] - dateutil.relativedelta.relativedelta(
            months=best_peaks_of_x_months)

        last_x_months_season_peak = season_peaks.loc[
            (season_peaks.date <= activity_metric['date']) &
            (season_peaks.date > last_x_months_date)]

        sorted_all_time_season_peaks = all_time_season_peak.sort_values(by=[metric_name],ascending=False)[:3]
        sorted_last_x_months_season_peak_ = last_x_months_season_peak.sort_values(by=[metric_name],
                                                                                  ascending=False)[:3]

        peak_power_curr_activity = activity_metric[metric_name]

        sorted_all_time_season_peaks_tolist = sorted_all_time_season_peaks[metric_name].tolist()
        sorted_x_months_season_peaks_tolist = sorted_last_x_months_season_peak_[metric_name].tolist()
        row = get_html_table_row(peak_power_curr_activity, sorted_all_time_season_peaks_tolist, metric_name,
                                 "All Time")
        if row:
            rows = rows + str(row)
        else:
            row = get_html_table_row(peak_power_curr_activity, sorted_x_months_season_peaks_tolist,
                                     metric_duration_name[i], "Last " + str(best_peaks_of_x_months) + " Months")
            if row:
                rows = rows + str(row)

    create_end_html_float(rows)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_html_table_row(peak_power_curr_activity, sorted_season_peaks, duration_name, period):
    gold_img_location = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Gold_Medal_PNG_Clip_Art.png?m=1507172109"
    silver_img_location = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Silver_Medal_PNG_Clip_Art.png?m=1507172109"
    bronze_img_location = "https://gallery.yopriceville.com/var/resizes/Free-Clipart-Pictures/Trophy-and-Medals-PNG/Bronze_Medal_PNG_Clip_Art.png?m=1507172109"

    if peak_power_curr_activity > sorted_season_peaks[0]:
        img_location = gold_img_location
        print("GOLD MEDAL for duration " + str(duration_name) +
              ", Peak:" + str(peak_power_curr_activity))
    elif peak_power_curr_activity > sorted_season_peaks[1]:
        img_location = silver_img_location
        print("SILVER  MEDAL for duration " + str(duration_name) +
              ", Peak:" + str(peak_power_curr_activity))
    elif peak_power_curr_activity > sorted_season_peaks[2]:
        img_location = bronze_img_location
        print("BRONZE  MEDAL for duration " + str(duration_name) +
              ", Peak:" + str(peak_power_curr_activity))
    else:
        return None

    return "<tr>" + \
           "<td><img src=" + img_location + " width=\"35\" height=\"60\" /></td>" + \
           "<td style=\"vertical-align: top;\"><strong>" + str(peak_power_curr_activity) + " W</strong>" + \
           "<br />" + \
           "<br />" + \
           str(duration_name.replace("_", " ")) + " Power" + \
           "</td>" + \
           "<td style=\"vertical-align: top;\">" + str(period) + "</td>" + \
           "</tr>"


def create_end_html_float(rows):
    template = '''
    <!DOCTYPE html>

    <html>
        <head>
        </head>
        <body>
            <table>
            <tbody>
            ''' + str(rows) + '''
            </tbody>
            </table>        
        </body>
    </html>'''
    Path(temp_file.name).write_text(template)


if __name__ == "__main__":
    main()
