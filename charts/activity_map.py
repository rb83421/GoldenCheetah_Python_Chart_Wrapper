# xxxxx V1 (Py)
# This is an python chart
# My take on a ride plot
# currently only for power with a smoothness (moving average) of 20)
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2019-12-13 - Initial chart

from GC_Wrapper import GC_wrapper as GC

import pathlib
import pandas as pd
import plotly
import plotly.graph_objs as go
import tempfile

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

map_interval_type = "USER"


def main():
    act = GC.activity()
    activity = pd.DataFrame(act, index=act['seconds'])
    activity = remove_incorrect_lat_long_values(activity)

    all_intervals = pd.DataFrame(GC.activityIntervals())
    filtered_intervals = all_intervals[all_intervals.type == map_interval_type].filter(
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
    fig = go.Figure(go.Scattermapbox(
                            lat=activity.latitude,
                            lon=activity.longitude,
                            hoverinfo="skip",
                            name="Entire Ride"
                            )
    )

    fig.update(
        layout=dict(
            mapbox_style="open-street-map",
            margin=go.layout.Margin(
                l=0,
                r=0,
                b=0,
                t=25,
                pad=0
            ),
            mapbox=dict(
                center=dict(
                    lat=activity.latitude.mean(),
                    lon=activity.longitude.mean(),
                ),
                zoom=9,
            )
        )
    )


    for index, row in filtered_intervals.iterrows():
        interval = activity[(activity.seconds >= row.start) & (activity.seconds < row.stop)]
        hovertext=[]
        for i, value in interval.iterrows():
            hovertext.append(row["name"] + "<br>" + str(round(value.distance, 2)) + "Km")

        fig.add_trace(
            go.Scattermapbox(
                lon=interval.longitude, lat=interval.latitude,
                marker={'size': 10, 'symbol': "circle"},
                hoverinfo="text",
                hovertext=hovertext,
                name=row["name"]
            )
        )

    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


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


if __name__ == "__main__":
    main()
