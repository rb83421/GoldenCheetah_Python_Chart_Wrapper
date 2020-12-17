"""

Custom heatmap with folium V1 (Py)
This is an python chart which displays an heatmap (density map) with the selected daterange
WARNING: For this chart you need to install an custom python with an extra package called folium,tkinter and mttkinter

See for custom python install wiki:
https://github.com/GoldenCheetah/GoldenCheetah/wiki/UG_Special-Topics_Working-with-Python
For problems/question/suggestions post on https://groups.google.com/forum/#!forum/golden-cheetah-users

V1 - 2020-12-17 - Initial Chart

"""

from GC_Wrapper import GC_wrapper as GC

import pathlib
import tempfile
import pandas as pd
from datetime import datetime
from datetime import timedelta
import numpy as np
import folium
from folium.plugins import HeatMap
from tkinter import messagebox as mb
from mttkinter import *

root = mtTkinter.Tk(baseName="").withdraw()

# Light or dark map
light_map = False
# Radius
radius = 2
# Blur
blur = 2

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'

heatmap_grad = {'dark': {0.0: '#000004',
                         0.1: '#160b39',
                         0.2: '#420a68',
                         0.3: '#6a176e',
                         0.4: '#932667',
                         0.5: '#bc3754',
                         0.6: '#dd513a',
                         0.7: '#f37819',
                         0.8: '#fca50a',
                         0.9: '#f6d746',
                         1.0: '#fcffa4'},
                'light': {0.0: '#3b4cc0',
                          0.1: '#5977e3',
                          0.2: '#7b9ff9',
                          0.3: '#9ebeff',
                          0.4: '#c0d4f5',
                          0.5: '#dddcdc',
                          0.6: '#f2cbb7',
                          0.7: '#f7ac8e',
                          0.8: '#ee8468',
                          0.9: '#d65244',
                          1.0: '#b40426'}}


def main():
    start_time = datetime.now()
    season = GC.season(compare=True)
    all_lat_long_df = pd.DataFrame()
    activities_list = GC.activities(filter='Data contains "G"')

    start_dt = datetime.combine(season['start'][0], datetime.min.time())
    end_dt = datetime.combine(season['end'][0], datetime.min.time())
    activities_sub_list = []

    for i in np.arange(0, len(activities_list)):
        if start_dt <= activities_list[i] <= end_dt:
            activities_sub_list.append(activities_list[i])

    activity_time_calculation = round(len(activities_sub_list) * 0.5)
    map_time_calculation = round(len(activities_sub_list) * 0.05)
    html_write_time_calculation = round(len(activities_sub_list) * 0.2)
    duration = activity_time_calculation + map_time_calculation + html_write_time_calculation
    msg = """You are about to process: """ + str(len(activities_sub_list)) + """ (activities)

Based on your selection an rough estimation on how long the script will run: """ +\
          str(timedelta(seconds=duration)) + """

Do you want to continue?
"""
    if mb.askyesno("Expected run time", msg):
        for activity in activities_sub_list:
            current_activity = GC.activity(activity=activity)
            current_activity_df = pd.DataFrame(current_activity,
                                               index=current_activity['seconds']).filter(["longitude", "latitude"])
            all_lat_long_df = all_lat_long_df.append(current_activity_df)
        heat_data = all_lat_long_df[['latitude', 'longitude']].to_numpy()

        print('Gathering data est:{} act:{} '.format(activity_time_calculation, round(
            (datetime.now() - start_time).total_seconds(), 2)))

        before = datetime.now()
        fmap = folium.Map(tiles='CartoDB positron' if light_map else 'CartoDB dark_matter',
                          prefer_canvas=True)

        HeatMap(heat_data,
                radius=radius,
                blur=blur,
                gradient=heatmap_grad['light' if light_map else 'dark'],
                min_opacity=0.3,
                max_val=1).add_to(fmap)
        fmap.fit_bounds(fmap.get_bounds())
        print('Create map est:{} act:{}'.format(map_time_calculation,
                                                round((datetime.now() - before).total_seconds(), 2)))

        before = datetime.now()
        html = fmap.get_root().render()
        temp_file.writelines(html)
        temp_file.close()
        print('Write HTML est:{} act:{}'.format(html_write_time_calculation,
                                                round((datetime.now() - before).total_seconds()), 2))

        print('Total time est:{} act:{}'.format(timedelta(seconds=duration),
                                                str(datetime.now() - start_time).split('.')[0]))
    else:
        create_cancel_html()

    GC.webpage(pathlib.Path(temp_file.name).as_uri())



def create_cancel_html():
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

        <h1>Canceled</h1>
        </body>
    </html>
    """]
    f.writelines(lines_of_text)
    f.close()


if __name__ == "__main__":
    main()
