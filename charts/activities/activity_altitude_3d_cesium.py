"""
Altitude 3d Cesium V10 (Py)
This is an python chart
displays 3d altitude map with cesium
It will work without API_KEY best to register for free at https://cesium.com/

Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users

V1 - 2020-02-01 - Initial chart
V2 - 2020-02-02 - add ride time line + interval selection
V3 - 2020-02-03 - add power data with am4chart
V4 - 2020-02-09 - fix pause fill gaps with nan add speed gauge
V5 - 2020-02-14 - add HR and toggle buttons
V6 - 2020-02-15 - add altitude toggle + add interval selection
V7 - 2020-02-16 - make more robust for missing data + update selection layout
V8 - 2020-02-16 - fix typo + fix selection multiple intervals
V9 - 2020-02-20 - make interval name robust with special characters
V10 - 2020-06-18 - small fixes when ride without power is selected

"""

from GC_Wrapper import GC_wrapper as GC

import html
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

# HR percentage zone taken over from Options->Athlete->Zones-Heartrate Zones->Default
hr_zone_pct = [0, 68, 83, 94, 105]
zone_hr_colors = ["#ff00ff", "#00aaff", "#00ff80", "#ffd500", "#ff0000"]


def main():
    start_t = datetime.now()
    activity = GC.activity()
    activity_intervals = GC.activityIntervals()
    activity_metric = GC.activityMetrics()
    zones = GC.athleteZones(date=activity_metric["date"], sport="bike")
    activity_df = pd.DataFrame(activity, index=activity['seconds'])
    season_peaks = GC.seasonPeaks(all=True, filter='Data contains "P"', series='power', duration=1)
    print('Gathering data duration: {}'.format(datetime.now() - start_t))

    # For testing purpose select only x number of seconds
    if temp_duration_selection:
        activity_df = activity_df.head(temp_duration_selection)
    min_altitude = activity_df.altitude.min()
    activity_df.altitude = activity_df.altitude - min_altitude + 0.0001  # small offset need for cesium rendering

    # Stop if no gps data is found in the activity
    if "latitude" in activity:
        start_t = datetime.now()
        interval_entities = get_interval_entities(activity_df, activity_intervals, zones)
        print('Get interval entities duration: {}'.format(datetime.now() - start_t))

        start_t = datetime.now()
        altitude_entities = determine_altitude_entities(activity_df, zones, slice_distance)
        print('Get altitude entities duration: {}'.format(datetime.now() - start_t))

        start_t = datetime.now()
        selected_interval_entities, selected_interval_data_sources = get_selected_interval_entities(activity_df, activity_intervals)
        print('Get select intervals entities duration: {}'.format(datetime.now() - start_t))

        start_t = datetime.now()
        czml_block = get_czml_block_str(activity_df, activity_metric)
        print('Get entire ride entities + ride path duration: {}'.format(datetime.now() - start_t))

        start_t = datetime.now()
        if "power" in activity:
            max_watt = max(season_peaks['peak_power_1'])
            power_zone_ranges = get_zone_ranges(zones['zoneslow'][0], zones['zonescolor'][0], max_watt)
        else:
            max_watt = 1500
            power_zone_ranges = ""
        print('Get power ranges duration: {}'.format(datetime.now() - start_t))

        start_t = datetime.now()
        hr_lthr = zones['lthr'][0]
        hr_max = zones['hrmax'][0]
        zones_hr = []
        for i in hr_zone_pct:
            zones_hr.append(round(hr_lthr/100*i))
        if "heart.rate" in activity:
            hr_zone_ranges = get_zone_ranges(zones_hr, zone_hr_colors, hr_max, axis="axis_hr")
        else:
            hr_zone_ranges = ""
        print('Get heart rate ranges duration: {}'.format(datetime.now() - start_t))

        start_t = datetime.now()
        write_html(activity_df,
                          activity_metric,
                          activity_intervals,
                          altitude_entities,
                          interval_entities,
                          selected_interval_entities,
                          selected_interval_data_sources,
                          czml_block,
                          power_zone_ranges,
                          max_watt,
                          hr_zone_ranges,
                          hr_max)
        print('write html duration: {}'.format(datetime.now() - start_t))
    else:
        write_no_valid_data_html()

    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_interval_entities(activity_df, activity_intervals, zones):
    activity_intervals_df = pd.DataFrame(activity_intervals)
    coloring_df = determine_coloring_dict("P", zones)
    e = []
    for interval_type in activity_intervals_df.type.drop_duplicates().tolist():
        data_source_name = str(interval_type.replace(" ", "_")) + "DataSource"
        e.append("var " + data_source_name + " = new Cesium.CustomDataSource(\"" + data_source_name + "\");\n")

        selected_intervals = activity_intervals_df[activity_intervals_df.type == interval_type]
        e1 = []
        for index, row in selected_intervals.iterrows():
            index_color = bisect.bisect_right(coloring_df.breaks, row['Average_Power'])
            color = coloring_df.colors[index_color - 1]
            filtered_df = activity_df[(activity_df.seconds >= row['start']) & (activity_df.seconds <= row['stop'])]
            lat_long_str = str((filtered_df.longitude.map(str) + "," + filtered_df.latitude.map(str)).tolist()).replace("'", "")
            e1.append(data_source_name + '''.entities.add(
                {
                    name : ' ''' + str(html.escape(row['name']).encode('utf-8')).split("'")[1] + '''  ',
                    wall : {
                        positions : Cesium.Cartesian3.fromDegreesArray(
                            ''' + lat_long_str + '''                                                        
                        ),
                        maximumHeights : 
                            ''' + str(np.full(len(filtered_df.seconds.tolist()), row['Average_Power']).tolist()) + ''',
                        minimumHeights : 
                            ''' + str(np.zeros(len(filtered_df.seconds.tolist())).tolist()) + ''',
                        material : Cesium.Color.fromCssColorString("''' + str(color) + '''"),       
                        outline : false,
                        outlineColor : Cesium.Color.fromCssColorString("''' + str(color) + '''"),
                        zIndex: 1,
                    }       
                }
            );
            ''')
        e.append(str("".join(e1)))
        e.append("viewer.dataSources.add(" + data_source_name + ");\n")
        e.append(data_source_name + ".show = false;\n")
    return e


def get_zone_ranges(zones, zones_colors, max_range, axis="axis_pwr"):
    zone_blocks = []
    for i in range(len(zones)):
        zones.append(max_range)
        zone_blocks.append(
            '''
            var range''' + str(i) + ''' = ''' + axis + '''.axisRanges.create();
            range''' + str(i) + '''.value = ''' + str(zones[i]) + ''';
            range''' + str(i) + '''.endValue = ''' + str(zones[i+1]) + ''';
            range''' + str(i) + '''.axisFill.fillOpacity = 1;
            range''' + str(i) + '''.axisFill.fill = am4core.color("''' + str(zones_colors[i]) + '''");
            range''' + str(i) + '''.axisFill.zIndex = -1;
            '''
        )
    return zone_blocks


def get_selected_interval_entities(activity_df, activity_intervals):
    if not pd.DataFrame(activity_intervals).selected.any():
        return "", ""
    else:
        lap = list(activity_intervals["selected"])
        selected_interval_names = []
        e = []
        data_source_names = []

        for index in list(compress(range(len(lap)), lap)):
            selected_interval_name = str(html.escape(activity_intervals['name'][index]).encode('utf-8')).split("'")[1]
            selected_interval_start = int(activity_intervals["start"][index]) + 1
            selected_interval_stop = int(activity_intervals["stop"][index]) + 1
            selected_interval_df = activity_df.loc[selected_interval_start:selected_interval_stop].copy()
            positions = str((selected_interval_df.longitude.map(str) + ", " + selected_interval_df.latitude.map(
                str) + ", " + selected_interval_df.altitude.map(str)).tolist()).replace("'", "")
            data_source_name = "selectedIntervalsDataSource" + str(index)
            data_source_names.append(data_source_name)
            e.append('''
            var ''' + data_source_name + ''' = new Cesium.CustomDataSource(\"''' + data_source_name + '''\");    
            ''' + data_source_name + '''.entities.add(
                        {
                            name : ' ''' + str(selected_interval_name) + '''  ',
                            polyline : {
                                positions : Cesium.Cartesian3.fromDegreesArrayHeights(
                                    ''' + str(positions) + '''                                                        
                                ),
                            width : 5,
                            material : Cesium.Color.BLUE,
                            }       
                        }
                    );
            viewer.dataSources.add(''' + data_source_name + ''');
            ''' + data_source_name + '''.show = true;                        
            ''')
    return e, data_source_names


def get_czml_block_str(activity, activity_metric):
    act_datetime = datetime.combine(activity_metric['date'], activity_metric['time'])
    start_time_str = act_datetime.isoformat() + "Z"
    end_time_str = (act_datetime + timedelta(seconds=activity_metric['Duration'])).isoformat() + "Z"
    positions_w_time = str((activity.seconds.map(str) + ", " + activity.longitude.map(str) + ", " + activity.latitude.map(str) + ", " + activity.altitude.map(str)).tolist()).replace("'", "")
    positions = str((activity.longitude.map(str) + ", " + activity.latitude.map(str) + ", " + activity.altitude.map(str)).tolist()).replace("'", "")
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
        ''' + positions_w_time + '''
    }
}];

        var completeRideDataSource = new Cesium.CustomDataSource(\"completeRideDataSource\");    
        completeRideDataSource.entities.add(
                    {
                        name : 'Entire ride',
                        polyline : {
                            positions : Cesium.Cartesian3.fromDegreesArrayHeights(
                                ''' + str("".join(positions)) + '''                                                        
                            ),
                        width : 2,
                        material : Cesium.Color.YELLOW,
                        }       
                    }
                );
        viewer.dataSources.add(completeRideDataSource);
        completeRideDataSource.show = false;                        

    
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


def determine_altitude_entities(activity_df, zones, slice_value):
    coloring_df = determine_coloring_dict(coloring_mode, zones)

    # Slice per x km
    number_slices = activity_df.distance.iloc[-1] / slice_value
    e = []
    altitude_entity_name = "altitudeDataSource"
    e.append("var " + altitude_entity_name + " = new Cesium.CustomDataSource(\"" + altitude_entity_name + "\");\n")
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

        if coloring_mode == "P":
            avg_power = slice_df.power.mean()
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
                      # 'slope': [slope, slope],
                      # 'average_power': [avg_power, avg_power]
                    })

        lat_long_str = str((df["lon"].map(str) + "," + df["lat"].map(str)).tolist()).replace("'", "")
        e.append(altitude_entity_name + '''.entities.add(
            {
                name : ' ''' + legend_text + '''  ',
                wall : {
                    positions : Cesium.Cartesian3.fromDegreesArray(
                        ''' + lat_long_str + '''                                                        
                    ),
                    maximumHeights : 
                        ''' + str(df.maximumHeights.tolist()) + ''',
                    minimumHeights : 
                        ''' + str(np.zeros(len(df.lat.tolist())).tolist()) + ''',
                    material : Cesium.Color.fromCssColorString("''' + color + '''"),       
                    outline : true,
                    outlineColor : Cesium.Color.fromCssColorString("''' + color + '''"),
                    zIndex: 1,       
                }
            }
        );
            ''')

    e.append("viewer.dataSources.add(" + altitude_entity_name + ");\n")
    return e


def get_power_gauge(power_zone_ranges, max_watt):
    return '''
        var axis_pwr = chart.xAxes.push(new am4charts.ValueAxis());
        axis_pwr.min = 0;
        axis_pwr.max = ''' + str(max_watt) + ''';
        axis_pwr.strictMinMax = true;
        axis_pwr.renderer.grid.template.disabled = true;
        axis_pwr.renderer.labels.template.fill = am4core.color("''' + gc_text_color + '''");
        axis_pwr.renderer.labels.template.radius = am4core.percent(1);    
        axis_pwr.renderer.ticks.template.stroke = am4core.color("''' + gc_text_color + '''");
    
        
        
        ''' + str("".join(power_zone_ranges)) + '''
        
        var hand_pwr = chart.hands.push(new am4charts.ClockHand());
        hand_pwr.innerRadius = am4core.percent(85);
        hand_pwr.startWidth = 5;
        hand_pwr.pin.disabled = true;
        hand_pwr.value = 0;
        hand_pwr.fill = am4core.color("''' + gc_text_color + '''");
        hand_pwr.stroke = am4core.color("''' + gc_text_color + '''");
        
        
        var label_pwr = chart.radarContainer.createChild(am4core.Label);
        label_pwr.fontSize = 20;
        label_pwr.innerRadius = 80;
        label_pwr.y = -265;
        label_pwr.textAlign = "middle";;
        label_pwr.fill = am4core.color("''' + gc_text_color + '''");
        label_pwr.horizontalCenter = "middle";
        label_pwr.text = "";
    '''


def get_power_gauge_animation():
    return ''' 
      label_pwr.text = power[seconds_from_dif] + " watt"
      var animation = new am4core.Animation(hand_pwr, {
        property: "value",
        to: power[seconds_from_dif]
      }, 1000, am4core.ease.cubicOut).start();
    '''


def get_heartrate_gauge(heartrate_zone_ranges, max_hr):
    return '''
        var axis_hr = chart.xAxes.push(new am4charts.ValueAxis());
    axis_hr.min = 40;
    axis_hr.max = ''' + str(max_hr) + ''';
    axis_hr.renderer.radius = am4core.percent(70);
    axis_hr.strictMinMax = true;
    axis_hr.renderer.grid.template.disabled = true;
    axis_hr.renderer.labels.template.fill = am4core.color("#ffffff");
    axis_hr.renderer.labels.template.radius = am4core.percent(1);    
    axis_hr.renderer.ticks.template.stroke = am4core.color("#ffffff");
    
    
    ''' + str("".join(heartrate_zone_ranges)) + '''
    
    var hand_hr = chart.hands.push(new am4charts.ClockHand());
    hand_hr.axis = axis_hr;
    hand_hr.innerRadius = am4core.percent(80);
    hand_hr.startWidth = 5;
    hand_hr.pin.disabled = true;
    hand_hr.value = 50;
    hand_hr.fill = am4core.color("#ffffff");
    hand_hr.stroke = am4core.color("#ffffff");
    
    
    var label_hr = chart.radarContainer.createChild(am4core.Label);
    label_hr.fontSize = 20;
    label_hr.innerRadius = 40;
    label_hr.y = -185;
    label_hr.textAlign = "middle";;
    label_hr.fill = am4core.color("#ffffff");
    label_hr.horizontalCenter = "middle";
    label_hr.text = "";

    '''


def get_heartrate_gauge_animation():
    return '''
          label_hr.text = hr[seconds_from_dif] + " bpm"         
          var animation2 = new am4core.Animation(hand_hr, {
            property: "value",
            to: hr[seconds_from_dif]
          }, 1000, am4core.ease.cubicOut).start();    
    '''


def write_html(activity_df,
               activity_metric,
               activity_intervals,
               altitude_entities,
               interval_entities,
               selected_interval_entities,
               selected_interval_data_sources,
               czml,
               power_zone_ranges,
               max_watt,
               heartrate_zone_ranges,
               max_hr):
    act_datetime = datetime.combine(activity_metric['date'], activity_metric['time'])
    start_time_str = act_datetime.isoformat() + "Z"

    temp_df = activity_df.filter(['seconds', 'power', 'heart.rate', 'speed'])
    new_index = pd.Index(np.arange(0, activity_df.seconds.tolist()[-1]), name="seconds")
    temp_df = temp_df.set_index("seconds").reindex(new_index).reset_index()
    temp_df.speed = temp_df.speed.round(1)
    provided_api_key = ""
    if API_KEY:
        provided_api_key = "Cesium.Ion.defaultAccessToken = '" + API_KEY + "';"

    activity_intervals_df = pd.DataFrame(activity_intervals)
    interval_list = [str("<a class=\"dropdown-item\" href=\"#\">" + interval_type + "</a>") for interval_type in activity_intervals_df.type.drop_duplicates().tolist()]

    hide_interval = [str(interval_type.replace(" ", "_") + "DataSource.show = false;\n") for interval_type in activity_intervals_df.type.drop_duplicates().tolist()]
    enable_interval = []
    for interval_type in activity_intervals_df.type.drop_duplicates().tolist():
        enable_interval.append(
            '''
            if ($('.selected_interval').text() == "''' + interval_type + '''"){
            ''' + interval_type.replace(" ", "_") + '''DataSource.show = true;
            } '''
        )

    status_selected_interval = "unchecked disabled data-onstyle=\"danger\" data-offstyle=\"danger\"" if selected_interval_entities == "" else "checked data-onstyle=\"success\" data-offstyle=\"warning\""

    status_power = "unchecked disabled data-onstyle=\"danger\" data-offstyle=\"danger\"" if power_zone_ranges == "" else "checked data-onstyle=\"success\" data-offstyle=\"warning\""
    power_values = str(temp_df.power.tolist()) if "power" in temp_df else "[]"
    power_gauge_axis = "" if power_zone_ranges == "" else get_power_gauge(power_zone_ranges, max_watt)
    power_gauge_animation = "" if power_zone_ranges == "" else get_power_gauge_animation()

    status_heartrate = "unchecked disabled data-onstyle=\"danger\" data-offstyle=\"danger\"" if heartrate_zone_ranges == "" else "checked data-onstyle=\"success\" data-offstyle=\"warning\""
    heartrate_values = str(temp_df['heart.rate'].tolist()) if "heart.rate" in temp_df else "[]"
    heartrate_gauge_axis = "" if heartrate_zone_ranges == "" else get_heartrate_gauge(heartrate_zone_ranges, max_hr)
    heartrate_gauge_animation = "" if heartrate_zone_ranges == "" else get_heartrate_gauge_animation()
    speed_overwrite = '''
        axis3_speed.renderer.innerRadius = 40
        axis2_speed.renderer.radius = am4core.percent(80);
        axis_speed.renderer.radius = am4core.percent(80);
        hand_speed.innerRadius = am4core.percent(25);
        ''' if heartrate_zone_ranges == "" else ""

    selected_interval_data_sources_show = []
    selected_interval_data_sources_hide = []
    selected_interval_data_sources_show_check = "true"
    for i in selected_interval_data_sources:
        selected_interval_data_sources_show_check = str(i + ".show == false")
        selected_interval_data_sources_show.append(str(i + ".show = true;\n"))
        selected_interval_data_sources_hide.append(str(i + ".show = false;\n"))

    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
    * {
        margin: 0;
        padding: 0;
        color: ''' + gc_text_color + ''';
    }
    
    #cesiumContainer {
      height: 450px;
      margin: 1em auto;
    }

    
    #container {
      height: 400px;
      margin: 1em auto;
      background-color:  #343434;      
    }
        
    .black_back{
        background-color:  #343434;
    }

    .toggle.ios, .toggle-on.ios, .toggle-off.ios { border-radius: 20px; }
    .toggle.ios .toggle-handle { border-radius: 20px; }

    .box {border:2px solid #0094ff;}
    .box h2 {background:#0094ff;color:white;padding:10px;}
    .box p {color:#333;padding:10px;}
        
    </style>
  <meta charset="utf-8">
  <link href="https://cesium.com/downloads/cesiumjs/releases/1.65/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
  <link href="https://gitcdn.github.io/bootstrap-toggle/2.2.2/css/bootstrap-toggle.min.css" rel="stylesheet">
  
</head>
<body class="black_back">

    <script src="https://www.amcharts.com/lib/4/core.js"></script>
    <script src="https://www.amcharts.com/lib/4/charts.js"></script>
    <script src="https://www.amcharts.com/lib/4/maps.js"></script>

    <script src="https://cesium.com/downloads/cesiumjs/releases/1.65/Build/Cesium/Cesium.js"></script>


    <script src="https://code.jquery.com/jquery-3.4.1.slim.min.js" integrity="sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js" integrity="sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6" crossorigin="anonymous"></script>    
    <script src="https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js"></script>
    
    <div id="cesiumContainer" ></div>
    
    
    <div class="row" align="center">
        <div class="col-xs-6 col-md-7">
            <div class="card bg-dark" >
                <h5 class="card-header text-white  bg-info ">Map settings</h5>
                <div class="card-body " style="padding-top: 5px; padding-bottom: 5px;">
                    <input type="checkbox" id="toggle-altitude" checked data-on="Altitude" data-off="Altitude" data-toggle="toggle" data-size="small" data-onstyle="success" data-offstyle="warning" data-style="ios" data-width="100" data-height="40px">
                    <input type="checkbox" id="toggle-interval" checked data-on="Interval" data-off="Interval" data-toggle="toggle" data-size="small" data-onstyle="success" data-offstyle="warning" data-style="ios" data-width="100" data-height="40px">
                    <class="dropdown" style="padding-top: 5px;padding-bottom: 5px;">
                    <button class="btn btn-secondary dropdown-toggle selected_interval" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="border-radius: 20px;height:40px;">
                      Select interval type
                    </button>
                    <div class="dropdown-menu dropdown-selected_interval" aria-labelledby="dropdownMenuButton">
                      ''' + str("".join(interval_list)) + '''
                    </div>
                    <input type="checkbox" id="toggle-gc-selected-interval" ''' + status_selected_interval + ''' data-on="Selected intervals" data-off="Selected intervals" data-toggle="toggle" data-size="small" data-style="ios" data-width="150" data-height="40px">
                    <input type="checkbox" id="toggle-entire-ride" unchecked data-on="Entire ride" data-off="Entire ride" data-toggle="toggle" data-size="small" data-onstyle="success" data-offstyle="warning" data-style="ios" data-width="100" data-height="40px">                                     
                </div>
            </div> 
        </div>
        <div class="col-xs-6 col-md-5">
            <div class="card bg-dark" data-width="100px">
                <h5 class="card-header text-white bg-info">Graph settings</h5>
                <div class="card-body" style="padding-top: 5px; padding-bottom: 5px;">
                    <input type="checkbox" id="toggle-hr" ''' + status_heartrate + ''' data-on="HR" data-off="HR" data-toggle="toggle" data-size="small" data-style="ios" data-width="100" data-height="40px">
                    <input type="checkbox" id="toggle-pwr" ''' + status_power + ''' data-on="Power" data-off="Power" data-toggle="toggle" data-size="small" data-style="ios" data-width="100" data-height="40px">
                    <input type="checkbox" id="toggle-speed" checked data-on="Speed" data-off="Speed" data-toggle="toggle" data-size="small" data-onstyle="success" data-offstyle="warning" data-style="ios" data-width="100" data-height="40px">
                </div>       
            </div>
        </div>
    </div> 
          
   
    <div id="container"></div> 
    <script>
    ''' + provided_api_key + '''
    var nan = NaN;    
    var power = ''' + power_values + ''';
    var speed = ''' + str(temp_df.speed.tolist()) + ''';
    var hr = ''' + heartrate_values + ''';

    var viewer = new Cesium.Viewer('cesiumContainer', {
        shouldAnimate : true
    });
    
    ''' + czml + '''
    ''' + str("".join(altitude_entities)) + '''
    
    ''' + str("".join(interval_entities)) + '''
    
    
    viewer.dataSources.add(Cesium.CzmlDataSource.load(czml)).then(function(ds) {
        viewer.trackedEntity = ds.entities.getById('path');
    });
    
    ''' + str("".join(selected_interval_entities)) + '''
        
    viewer.flyTo(altitudeDataSource);

    
    

    // Create a container
    var container = am4core.create(document.getElementById("container"), am4core.Container);
    container.width = am4core.percent(100);
    container.height = am4core.percent(100);
    container.layout = "horizontal";

    // Create sub-containers
    // var buttonContainer = container.createChild(am4core.Container);
    // buttonContainer.layout = "vertical";
    // buttonContainer.width = 200;
    // buttonContainer.height = am4core.percent(100);
    // buttonContainer.background.fill = am4core.color("#D2AB99");
    // buttonContainer.background.fillOpacity = 0.3;

    var chartContainer = container.createChild(am4core.Container);
    chartContainer.layout = "vertical";
    chartContainer.width = am4core.percent(100);
    chartContainer.height = am4core.percent(100);




    // Create chart instance
    var chart = chartContainer.createChild(am4charts.GaugeChart);
    chart.innerRadius = -15;
    
    ''' + power_gauge_axis + '''
    
    var axis_speed = chart.xAxes.push(new am4charts.ValueAxis);
    axis_speed.min = 0;
    axis_speed.max = 60;
    axis_speed.renderer.minGridDistance = 100;
    axis_speed.strictMinMax = true;
    axis_speed.renderer.radius = am4core.percent(50);
    axis_speed.renderer.inside = true;
    axis_speed.renderer.line.strokeOpacity = 1;
    axis_speed.renderer.line.stroke = am4core.color("''' + gc_text_color + '''");
    axis_speed.renderer.ticks.template.disabled = false;  
    axis_speed.renderer.ticks.template.strokeOpacity = 1;
    axis_speed.renderer.ticks.template.length = 15;
    axis_speed.renderer.ticks.template.stroke = am4core.color("''' + gc_text_color + '''");
    axis_speed.renderer.grid.template.disabled = true;
    axis_speed.renderer.labels.template.radius = 40;
    axis_speed.renderer.labels.template.fill = am4core.color("''' + gc_text_color + '''");


    var axis2_speed = chart.xAxes.push(new am4charts.ValueAxis);
    axis2_speed.min = 0;
    axis2_speed.max = 60;
    axis2_speed.renderer.minGridDistance = 1;
    axis2_speed.strictMinMax = true;
    axis2_speed.renderer.radius = am4core.percent(50);
    axis2_speed.renderer.inside = true;
    axis2_speed.renderer.ticks.template.disabled = false;  
    axis2_speed.renderer.ticks.template.strokeOpacity = 0.8;
    axis2_speed.renderer.ticks.template.length = 5;
    axis2_speed.renderer.ticks.template.stroke = am4core.color("''' + gc_text_color + '''");
    axis2_speed.renderer.grid.template.disabled = true;
    axis2_speed.renderer.labels.template.adapter.add("text", function(text) {
    return "" ;
    })

    /**
     * Axis for ranges
     */
    var colorSet = new am4core.ColorSet();

    var axis3_speed = chart.xAxes.push(new am4charts.ValueAxis());
    axis3_speed.min = 0;
    axis3_speed.max = 60;
    axis3_speed.renderer.innerRadius = 10
    axis3_speed.strictMinMax = true;
    axis3_speed.renderer.labels.template.disabled = true;
    axis3_speed.renderer.ticks.template.disabled = true;
    axis3_speed.renderer.grid.template.disabled = true;

    var range0 = axis2_speed.axisRanges.create();
    range0.value = 0;
    range0.endValue = 60;
    range0.axisFill.fillOpacity = 0.6;
    range0.axisFill.fill = colorSet.getIndex(0);

    /**
     * Label
     */

    var label_speed = chart.radarContainer.createChild(am4core.Label);
    label_speed.isMeasured = false;
    label_speed.fontSize = 20;
    label_speed.horizontalCenter = "middle";
    label_speed.verticalCenter = "bottom";
    label_speed.textAlign = "middle";;
    label_speed.fill = am4core.color("''' + gc_text_color + '''");
    label_speed.text = "";


    /**
     * Hand
     */
    var hand_speed = chart.hands.push(new am4charts.ClockHand());
    hand_speed.axis = axis2_speed;
    hand_speed.innerRadius = am4core.percent(40);
    hand_speed.startWidth = 5;
    hand_speed.pin.disabled = true;
    hand_speed.value = 0;
    hand_speed.fill = am4core.color("''' + gc_text_color + '''");
    hand_speed.stroke = am4core.color("''' + gc_text_color + '''");    

    /** 
    * Overwrite value when no heart rate data is found
    **/
    ''' + speed_overwrite + '''

    ''' + heartrate_gauge_axis + '''

    $(function() {
        $('#toggle-hr').change(function() {
            if(label_hr.visible==false){
            label_hr.visible=true;
            hand_hr.visible=true;
            axis_hr.visible=true;

            axis3_speed.renderer.innerRadius = 10
            axis2_speed.renderer.radius = am4core.percent(50);
            axis_speed.renderer.radius = am4core.percent(50);
            hand_speed.innerRadius = am4core.percent(40);
           
        }else{
            label_hr.visible=false;
            hand_hr.visible=false;
            axis_hr.visible=false;

            axis3_speed.renderer.innerRadius = 40
            axis2_speed.renderer.radius = am4core.percent(80);
            axis_speed.renderer.radius = am4core.percent(80);
            hand_speed.innerRadius = am4core.percent(25);

        }
    })
    })


  $(function() {
        $('#toggle-pwr').change(function() {
            if(label_pwr.visible==false){
                label_pwr.visible=true;
                hand_pwr.visible=true;
                axis_pwr.visible=true;
            }else{
                label_pwr.visible=false;
                hand_pwr.visible=false;
                axis_pwr.visible=false;
            }
    })
  })  


  $(function() {
        $('#toggle-speed').change(function() {
            if(label_speed.visible==false){
                label_speed.visible=true;
                hand_speed.visible=true;
                axis_speed.visible=true;
                axis2_speed.visible=true;
                axis3_speed.visible=true;
            }else{
                label_speed.visible=false;
                hand_speed.visible=false;
                axis_speed.visible=false;
                axis2_speed.visible=false;
                axis3_speed.visible=false;
            }
    })
  })    

    $(function() {
            $('#toggle-gc-selected-interval').change(function() {
                if(''' + selected_interval_data_sources_show_check + '''){
                    ''' + str("".join(selected_interval_data_sources_show)) + '''
                }else{
                    ''' + str("".join(selected_interval_data_sources_hide)) + '''
                }
        })
      })    


  $(function() {
        $('#toggle-altitude').change(function() {
            if(altitudeDataSource.show == false){
                altitudeDataSource.show = true;
            }else{
                altitudeDataSource.show = false;
            }
    })
  })    

  $(function() {
        $('#toggle-entire-ride').change(function() {
            if(completeRideDataSource.show == false){
                completeRideDataSource.show = true;
            }else{
                completeRideDataSource.show = false;
            }
    })
  })    



    $('.dropdown-selected_interval a').click(function(e){
        $('.selected_interval').text(this.innerHTML);
        ''' + str("".join(hide_interval)) + '''
        ''' + str("".join(enable_interval)) + '''
    });


  $(function() {
        $('#toggle-interval').change(function() {
            ''' + str("".join(hide_interval)) + '''
            if ($('#toggle-interval:checked').val() == "on"){
                $('.selected_interval').prop('disabled', false);
                ''' + str("".join(enable_interval)) + '''            
            }else{
                $('.selected_interval').prop('disabled', true);
            }

    })
  })    


    var lastTime = viewer.clockViewModel.startTime;
    start_date = new Date("''' + str(start_time_str) + '''")
    Cesium.knockout.getObservable(viewer.clockViewModel, 'currentTime').subscribe(
    function(currentTime) {
          var current_date = new Date(Cesium.JulianDate.toIso8601(currentTime, 0));
          var dif = current_date.getTime() - start_date.getTime();
          var seconds_from_dif = dif / 1000;
          
          ''' + str(power_gauge_animation) + '''
          ''' + str(heartrate_gauge_animation) + '''
    
          label_speed.text = speed[seconds_from_dif] + " km/h"
          var animation3 = new am4core.Animation(hand_speed, {
            property: "value",
            to: speed[seconds_from_dif]
          }, 1000, am4core.ease.cubicOut).start();
    });



</script>

</body>
</html>
'''
    temp_file.writelines(html)
    temp_file.close()



def write_no_valid_data_html():
    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <style>
    * {
        margin: 0;
        padding: 0;
        color: ''' + gc_text_color + ''';
    }
        
    .black_back{
        background-color:  #343434;
    }

        
    </style>
  <meta charset="utf-8">
  
</head>
<body class="black_back">
    <h1 align="center"> NO GPS DATA FOUND<h1>
</body>
</html>        
        '''
    temp_file.writelines(html)
    temp_file.close()


if __name__ == "__main__":
    start_time = datetime.now()
    main()
    print('Total duration: {}'.format(datetime.now() - start_time))
