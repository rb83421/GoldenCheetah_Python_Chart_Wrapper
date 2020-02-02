##
## Python program will run on selection.
##
from GC_Wrapper import GC_wrapper as GC
import pathlib
from datetime import datetime
import time
import collections
import tempfile
import plotly
import plotly.graph_objs as go
import numpy as np
import statistics

compares = GC.season(compare=True)
activities_list = GC.activities(filter='isRun<>0')
athlete_zones = GC.athleteZones()
hr_max = max(athlete_zones['hrmax'])

temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


# For an given subset of activities this function will return a data frame that contains all hr with corresponding speed
def get_hr_list_of_activities(activities_subset):
    start_time = time.time()
    heart_rate_speed_dict={}
    for activity in activities_subset:
        current_activity = GC.activity(activity=activity)
        for hr, speed in zip(current_activity['heart.rate'], current_activity['speed']):
            # In some cases (zwift) hr is not a round integer therefore round the hr to a integer
            # This when grouping all speed data at certain HR
            hr_rounded = int(round(hr, 0))
            if heart_rate_speed_dict.get(hr_rounded):
                heart_rate_speed_dict[hr_rounded].append(speed)
            else:
                heart_rate_speed_dict[hr_rounded] = [speed]
        #for i in heart_rate_speed_dict:
        #    print("HR: "+ str(i) + ", speed list: " + str(heart_rate_speed_dict[i]))
    print("get activities took: " + str(time.time() - start_time))
    return heart_rate_speed_dict

def create_mean_speed_by_hr(heart_rate_speed_dict):
    mean_speed_by_hr={}
    for hr in heart_rate_speed_dict:
        mean_speed_by_hr[hr] = round(statistics.mean(heart_rate_speed_dict[hr]),2)
    # Order the list on hr
    ordered_mean_speed_by_hr = collections.OrderedDict(sorted(mean_speed_by_hr.items()))
    return ordered_mean_speed_by_hr


#main function
start_time = time.time()

data=[]
for start, end, color, name in zip(compares['start'], compares['end'], compares['color'], compares['name']):
#    print("start: " + str(start) + ", end: " + str(end) + ", color: " + str(color))
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.min.time())
    activities_sub_list = []
    for i in np.arange(0,len(activities_list)):
        if activities_list[i] >= start_dt and activities_list[i] <= end_dt:
            activities_sub_list.append(activities_list[i])
#    print(activities_sub_list)
    heart_rate_speed_dict = get_hr_list_of_activities(activities_sub_list)
    mean_speed_by_hr = create_mean_speed_by_hr(heart_rate_speed_dict)
#    print(mean_speed_by_hr)

    trace = go.Scatter(
        x=list(mean_speed_by_hr.keys()),
        y=list(mean_speed_by_hr.values()),
        mode='lines+markers',
        line=dict(
            color=color,
         ),
        name=name,
        showlegend=True,
    )
    data.append(trace)
# End for

layout = go.Layout(
    title="Average speed at HR",
    paper_bgcolor=gc_bg_color,
    plot_bgcolor=gc_bg_color,
    font=dict(
        color=gc_text_color,
        size=12
    ),
    yaxis=dict(
        title="kph",
        nticks=50,
        rangemode='nonnegative',
        showgrid=True,
        zeroline=True,
        showline=True,
        gridcolor="grey",
    ),
    xaxis=dict(
        range=[90, hr_max+5],
        nticks=int(hr_max / 5),
        ticks='outside',
        showgrid=True,
        zeroline=True,
        showline=True,
        gridcolor="grey",
        title="HR",
        rangemode='nonnegative',
     ),
     margin=go.layout.Margin(
         l=100,
         r=0,
         b=100,
         t=150,
         pad=0
     ),
)

fig = go.Figure(data=data, layout=layout)

plot = plotly.offline.plot(fig, auto_open=True, filename=temp_file.name)
GC.webpage(pathlib.Path(temp_file.name).as_uri())
print("Total graph time: " + str(time.time() - start_time))



