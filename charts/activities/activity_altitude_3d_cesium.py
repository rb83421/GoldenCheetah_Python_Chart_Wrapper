"""
Altitude 3d Cesium V3 (Py)
This is an python chart
displays 3d altitude map with cesium
It will work without API_KEY best to register for free at https://cesium.com/

Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users

V1 - 2020-02-01 - Initial chart
V2 - 2020-02-02 - add ride time line + interval selection
V3 - 2020-02-03 - add power data with am4chart (Todo when data contains gaps power list is not correct)

"""
import matplotlib
from matplotlib import cm

from GC_Wrapper import GC_wrapper as GC

from datetime import datetime, timedelta
import bisect
import pathlib
import tempfile
import pandas as pd
import numpy as np
from itertools import compress

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)
# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

coloring_mode = "G"  # P for power G for gradient

# Create polygon per x km
slice_distance = 0.1

# This variably can be used for testing to only display the first x seconds
temp_duration_selection = None # 360

API_KEY = None


def get_zone_blocks(zones, max_watt):
    zone_blocks = []
    zones_low = zones['zoneslow'][0]
    zones_colors = zones['zonescolor'][0]

    for i in range(len(zones_low)):
        zones_low.append(max_watt)
        zone_blocks.append(
            '''
            var range''' + str(i) + ''' = axis.axisRanges.create();
            range''' + str(i) + '''.value = ''' + str(zones_low[i]) + ''';
            range''' + str(i) + '''.endValue = ''' + str(zones_low[i+1]) + ''';
            range''' + str(i) + '''.axisFill.fillOpacity = 1;
            range''' + str(i) + '''.axisFill.fill = am4core.color("''' + str(zones_colors[i]) + '''");
            range''' + str(i) + '''.axisFill.zIndex = -1;
            '''
        )
    return zone_blocks


def main():
    activity = GC.activity()
    activity_intervals = GC.activityIntervals()
    activity_metric = GC.activityMetrics()
    zones = GC.athleteZones(date=activity_metric["date"], sport="bike")
    activity_df = pd.DataFrame(activity, index=activity['seconds'])
    season_peaks = GC.seasonPeaks(all=True, filter='Data contains "P"', series='power', duration=1)
    max_watt = max(season_peaks['peak_power_1'])
    # For testing purpose select only x number of seconds
    if temp_duration_selection:
        activity_df = activity_df.head(temp_duration_selection)
    min_altitude = activity_df.altitude.min()
    activity_df.altitude = activity_df.altitude - min_altitude + 0.0001  # small offset need for cesium rendering

    coloring_df = determine_coloring_dict(coloring_mode, zones)
    entities = determine_altitude_entities(activity_df, coloring_mode, coloring_df, slice_distance)
    selected_interval_entities = get_selected_interval_entities(activity_df, activity_intervals)
    czml_block = get_czml_block_str(activity_df, activity_metric)
    zone_blocks = get_zone_blocks(zones, max_watt)

    html = write_html(activity_df, activity_metric, entities, selected_interval_entities, czml_block, zone_blocks, max_watt)
    temp_file.writelines(html)
    temp_file.close()

    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_entity_block_str(paths, color_str, zone_name):
    lat_long_str = str((paths["lon"].map(str) + "," + paths["lat"].map(str)).tolist()).replace("'", "")
    return '''
viewer.entities.add({
    name : ' ''' + zone_name + '''  ',
    wall : {
        positions : Cesium.Cartesian3.fromDegreesArray(
            ''' + lat_long_str + '''                                                        
        ),
        maximumHeights : 
            ''' + str(paths.maximumHeights.tolist()) + ''',
        minimumHeights : 
            ''' + str(np.zeros(len(paths.lat.tolist())).tolist()) + ''',
        material : Cesium.Color.fromCssColorString("''' + color_str + '''"),       
        outline : true,
        outlineColor : Cesium.Color.fromCssColorString("''' + color_str + '''"),
        zIndex: 1,       
    }
});
    '''


def get_selected_interval_entities(activity_df, activity_intervals):
    entities = []
    lap = list(activity_intervals["selected"])
    for index in list(compress(range(len(lap)), lap)):
        selected_interval_start = int(activity_intervals["start"][index]) + 1
        selected_interval_stop = int(activity_intervals["stop"][index]) + 1
        selected_interval_df = activity_df.loc[selected_interval_start:selected_interval_stop].copy()
        positions = str((selected_interval_df.longitude.map(str) + ", " + selected_interval_df.latitude.map(str) + ", " + selected_interval_df.altitude.map(str)).tolist()).replace("'", "")

        e = '''
    viewer.entities.add({
        name : 'Selected Interval',
        polyline : {
            positions : Cesium.Cartesian3.fromDegreesArrayHeights(
            ''' + positions + '''
            ),
            width : 5,
            material : Cesium.Color.BLUE,
            zIndex: 2,
        }
    });    
         '''
        entities.append(e)
    return entities


def get_czml_block_str(activity, activity_metric):
    act_datetime = datetime.combine(activity_metric['date'], activity_metric['time'])
    start_time_str = act_datetime.isoformat() + "Z"
    end_time_str = (act_datetime + timedelta(seconds=activity_metric['Duration'])).isoformat() + "Z"
    positions = str((activity.seconds.map(str) + ", " + activity.longitude.map(str) + ", " + activity.latitude.map(str) + ", " + activity.altitude.map(str)).tolist()).replace("'", "")
    return '''
var czml = [{
    "id" : "document",
    "name" : "CZML Path",
    "version" : "1.0",
    "clock": {
        "interval": "''' + start_time_str + '''/''' + end_time_str + '''",
        "currentTime": "''' + start_time_str + '''",
        "multiplier": 10
    }
}, {
    "id" : "path",
    "name" : "path with GPS ride data",
    "description" : "<p>Test Ride</p>",
    "availability" : "''' + start_time_str + '''/''' + end_time_str + '''",
    "path" : {
        "material" : {
            "polylineOutline" : {
                "color" : {
                    "rgba" : [255, 200, 0, 0]
                },
                "outlineColor" : {
                    "rgba" : [255, 200, 0, 0]
                },
                "outlineWidth" : 1
            }
        },
        "width" : 2,
    },
    "billboard" : {
        "image" : "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/cycle-pointer.png",
        "scale" : 0.1,
        "eyeOffset": {
            "cartesian": [ 0.0, 0.0, -10.0 ]
        }
    },
    "position" : {
        "epoch" : "''' + start_time_str + '''",
        "cartographicDegrees" :
        ''' + positions + '''
    }
}];
    
    '''

def determine_coloring_dict(color_mode, zones):
    coloring_dict = {'breaks': [],
                     'colors': [],
                     'legend_text': []}
    if color_mode == "P":
        coloring_dict['breaks'] = zones['zoneslow'][0]
        for color in zones['zonescolor'][0]:
            rgb = str(tuple(int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)))
            coloring_dict['colors'].append("rgba" + rgb.split(")")[0] + ", 0.6)")
        for i in np.arange(0, len(coloring_dict['breaks'])):
            coloring_dict['legend_text'].append("Z" + str(i + 1) + " >" + str(coloring_dict['breaks'][i]))
    else:
        coloring_dict['breaks'] = [-15, -7.5, 0, 7.5, 15, 20, 100]
        # 'colors': ['blue', 'lightblue', 'green', 'gray', 'yellow', 'orange', 'red'],
        #           <-15 darkblue,   <-7.5 mid blue,    <0 lightblue   , >0 green,        >7.5 yellow,      >15 light red,   >20 dark red
        coloring_dict['colors'] = ['rgba(0,0,133,0.6)', 'rgba(30,20,255,0.6)', 'rgba(80,235,255,0.6)',
                                   'rgba(80,255,0,0.6)', 'rgba(255,255,0,0.6)', 'rgba(235,0,0,0.6)',
                                   'rgba(122, 0,0,0.6)']
        coloring_dict['legend_text'] = ["<15%", ">-15% <-7.5%", ">-7.5% <0%", ">0% <7.5%", ">7.5% <15%", ">15% <20%",
                                        ">20%"]
    coloring_df = pd.DataFrame(coloring_dict)
    return coloring_df


def determine_altitude_entities(activity_df, color_mode, coloring_df, slice_value):
    # Slice per x km
    number_slices = activity_df.distance.iloc[-1] / slice_value
    e = []
    for i in range(int(number_slices)):
        start = i * slice_value
        # last slice take last sample
        if i == int(number_slices) - 1:
            stop = activity_df.distance.iloc[-1]
        else:
            stop = (i * slice_value) + slice_value

        mask = (activity_df.distance >= start) & (activity_df.distance <= stop)

        # add one extra value to close gaps
        mask[mask[::-1].idxmax() + 1] = True
        slice_df = activity_df.loc[mask]
        altitude_gain = slice_df.altitude.iloc[-1] - slice_df.altitude.iloc[0]
        distance = slice_df.distance.iloc[-1] - slice_df.distance.iloc[0]
        # slice_value is in km altitude in meter
        # distance - X-Axis is in KM, Y-Axis in m! and at the end *100 to get %value
        slope = 100 * (altitude_gain / (distance * 1000))
        # print("slope  : " + str(slope) + "(alt.: " + str(altitude_gain) + ", dist.: " + str(distance) + ")")
        avg_power = slice_df.power.mean()

        if color_mode == "P":
            index = bisect.bisect_right(coloring_df.breaks, avg_power)
            color = coloring_df.colors[index - 1]
            legend_text = coloring_df.legend_text[index-1]
        else:
            index = bisect.bisect_left(coloring_df.breaks, slope)
            color = coloring_df.colors[index]
            # legend_text = coloring_df.legend_text[index]
            legend_text = str(round(slope,2)) + "%"
            # normalize item number values to colormap
            # norm = matplotlib.colors.Normalize(vmin=-25, vmax=25)
            # rgba_color = list(cm.jet(norm(slope), bytes=True))
            # color = 'rgba(' + str(rgba_color[0]) + ', ' + str(rgba_color[1]) + ', ' + str(rgba_color[2]) + ', 0.6)'


        start_seconds = slice_df.seconds.iloc[0]
        stop_seconds = slice_df.seconds.iloc[-1]
        start_lon = slice_df.longitude.iloc[0]
        stop_lon = slice_df.longitude.iloc[-1]
        start_lat = slice_df.latitude.iloc[0]
        stop_lat = slice_df.latitude.iloc[-1]
        start_altitude = slice_df.altitude.iloc[0]
        stop_altitude = slice_df.altitude.iloc[-1]

        # For each slice define polygon
        df = pd.DataFrame({ 'seconds': [start_seconds, stop_seconds],
                        'lat': [start_lat, stop_lat],
                      'lon': [start_lon, stop_lon],
                      'maximumHeights': [start_altitude, stop_altitude],
                      'color': [color, color],
                      'slope': [slope, slope],
                      'average_power': [avg_power, avg_power]})
        e.append(get_entity_block_str(df, color, legend_text))
    return e


def write_html(activity_df, activity_metric, entities, selected_interval_entities, czml, zone_blocks, max_watt):
    act_datetime = datetime.combine(activity_metric['date'], activity_metric['time'])
    start_time_str = act_datetime.isoformat() + "Z"

    temp_df = activity_df.filter(['seconds', 'power', 'heart.rate'])
    new_index = pd.Index(np.arange(0, activity_df.seconds.tolist()[-1]), name="seconds")
    temp_df = temp_df.set_index("seconds").reindex(new_index).reset_index()

    provided_api_key = ""
    if API_KEY:
        provided_api_key = "Cesium.Ion.defaultAccessToken = '" + API_KEY + "';"

    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
    * {
        margin: 0;
        padding: 0;
        color: ''' + gc_text_color + ''';
    }
    
    html{
          background-color:  ''' + str(gc_bg_color) + ''';
    }  
    </style>
  <meta charset="utf-8">
  <link href="https://cesium.com/downloads/cesiumjs/releases/1.65/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
</head>
<body>
    <script src="https://www.amcharts.com/lib/4/core.js"></script>
    <script src="https://www.amcharts.com/lib/4/charts.js"></script>
    <script src="https://www.amcharts.com/lib/4/maps.js"></script>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.65/Build/Cesium/Cesium.js"></script>
    <div id="cesiumContainer" ></div>
    <div id="chartdiv"></div>
    
    <script type="text/javascript">
    ''' + provided_api_key + ''' 
    ''' + czml + '''
    var viewer = new Cesium.Viewer('cesiumContainer', {
        shouldAnimate : true
    });
    ''' + str("".join(entities)) + '''
    
    ''' + str("".join(selected_interval_entities)) + '''
    
    
    viewer.dataSources.add(Cesium.CzmlDataSource.load(czml)).then(function(ds) {
        viewer.trackedEntity = ds.entities.getById('path');
    });
    
    viewer.zoomTo(viewer.entities);
    
    
    // Create chart instance
    var chart = am4core.create(document.getElementById("chartdiv"), am4charts.GaugeChart);
    var axis = chart.xAxes.push(new am4charts.ValueAxis());
    axis.min = 0;
    axis.max = ''' + str(max_watt) + ''';
    axis.strictMinMax = true;
    
    chart.innerRadius = -15;
    
    ''' + str("".join(zone_blocks)) + '''
    
    
    var hand = chart.hands.push(new am4charts.ClockHand());
    hand.value = 0;
    hand.fill = am4core.color("#FFFFFF");
    hand.stroke = am4core.color("#FFFFFF");
    
    var label = chart.radarContainer.createChild(am4core.Label);
    label.fontSize = 20;
    label.horizontalCenter = "middle";
    label.text = "";
    
    var nan = NaN;    
    var power = ''' + str(temp_df.power.tolist()) + ''';
    var lastTime = viewer.clockViewModel.startTime;
    start_date = new Date("''' + str(start_time_str) + '''")
    Cesium.knockout.getObservable(viewer.clockViewModel, 'currentTime').subscribe(
    function(currentTime) {
          var current_date = new Date(Cesium.JulianDate.toIso8601(currentTime, 0));
          var dif = current_date.getTime() - start_date.getTime();
          var seconds_from_dif = dif / 1000;
          label.text = power[seconds_from_dif]         
          var animation = new am4core.Animation(hand, {
            property: "value",
            to: power[seconds_from_dif]
          }, 1000, am4core.ease.cubicOut).start();
    });

</script>

</body>
</html>

    '''



if __name__ == "__main__":
    main()
