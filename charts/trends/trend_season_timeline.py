# TimeLine V1 (Py)
# This is an python chart
# This chart plot for an season the activities in an timeline (test for upload)
#
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - 2020-02-09 - Initial chart

from GC_Wrapper import GC_wrapper as GC

import pathlib
import plotly
import plotly.graph_objs as go
import tempfile
import pandas as pd

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = "#343434"  # 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = "#ffffff"  # 'rgb(255,255,255)'

def main():
    season_metrics = GC.seasonMetrics()

    chart_data = get_time_line_data(season_metrics)

    start_formatted = season_metrics['date'][0].strftime("%Y, %m, %d,") + season_metrics['time'][0].strftime("%H,%M")
    stop_formatted = season_metrics['date'][-1].strftime("%Y, %m, %d,") + season_metrics['time'][-1].strftime("%H,%M")
    season_metrics['date'][-1]
    start_time = "new Date(" + str(start_formatted) + ").getTime();"
    stop_time = "new Date(" + str(stop_formatted) + ").getTime();"
    html = get_complete_html(chart_data, start_time, stop_time)
    temp_file.writelines(html)
    temp_file.close()
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def get_color_for_sport(sport):
    if sport == 'Bike':
        return "#098542"
    elif sport == 'Run':
        return "#1728a8"
    elif sport == "Fitness":
        return "#a81717"
    elif sport == "Walking":
        return "#a3a4a6"
    else:
        return ""


def get_sport_icon(sport):
    if sport == 'Bike' or sport == 'Fitness' or sport == 'Walking' or sport == 'Run':
        return sport
    else:
        return 'Default'


def get_time_line_data(season_metrics):
    items = []
    for i in range(len(season_metrics['date'])):
        date = season_metrics['date'][i]
        time = season_metrics['time'][i]
        color = get_color_for_sport(season_metrics['Sport'][i])
        sport = season_metrics['Sport'][i]

        text = ""
        if 'Workout_Title' in season_metrics:
            text = text + "Title: " + str(season_metrics['Workout_Title'][i]) + "\\n"
        if not season_metrics['Notes'][i] == '':
            text = text + "Notes: \\n " + str(season_metrics['Notes'][i].encode('utf-8')) + "\\n"

        items.append('''{
            "category": "",
            "start": "''' + str(date) + ''' ''' + str(time) + '''",
            "end": "''' + str(date) + ''' ''' + str(time) + '''",
            "color":         am4core.color("''' + str(color) + '''"),
            "icon": ''' + str(get_sport_icon(sport)) + ''',
            "text": " ''' + str(text) + '''"
            },''')

    return '''chart.data = [''' + str("".join(items)) + ''' ] '''


def get_complete_html(chart_data, start_time, stop_time):
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Styles -->    
    <style>
        #chartdiv {
          width: 100%;
          height: 600px;
    }
        
    html{
          background-color:  ''' + str(gc_bg_color) + ''';
    }          
    </style>
  <meta charset="utf-8">
</head>
</body>

    <!-- Resources -->
    <script src="https://www.amcharts.com/lib/4/core.js"></script>
    <script src="https://www.amcharts.com/lib/4/charts.js"></script>
    <script src="https://www.amcharts.com/lib/4/plugins/timeline.js"></script>
    <script src="https://www.amcharts.com/lib/4/plugins/bullets.js"></script>
    <script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>

   <!-- Chart code -->
    <script>
    am4core.ready(function() {
    
    var Walking =  "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/0_Walking_Pin.png";
    var Run =  "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/1_Running_Pin.png";
    var Fitness =  "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/3_Exercise_Pin.png";
    var Bike = "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/4_Road_Cycling_Pin.png";   
    var Default = "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/5_Default_Pin.png";   

    // Themes begin
    am4core.useTheme(am4themes_animated);
    // Themes end
    
    var chart = am4core.create("chartdiv", am4plugins_timeline.SerpentineChart);
    chart.curveContainer.padding(20,20,20,20);
    chart.levelCount = 8;
    chart.orientation = "horizontal";
    chart.fontSize = 11;
    chart.maskBullets = false;

    ''' + chart_data + ''' 
    
    var colorSet = new am4core.ColorSet();
    colorSet.saturation = 0.6;
    
    chart.dateFormatter.dateFormat = "yyyy-MM-dd";
    chart.dateFormatter.inputDateFormat = "yyyy-MM-dd";
    
    var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
    categoryAxis.dataFields.category = "category";
    categoryAxis.renderer.grid.template.disabled = true;
    categoryAxis.renderer.labels.template.paddingRight = 25;
    categoryAxis.renderer.minGridDistance = 10;
    categoryAxis.renderer.innerRadius = -60;
    categoryAxis.renderer.radius = 60;
    
    var dateAxis = chart.xAxes.push(new am4charts.DateAxis());
    dateAxis.renderer.minGridDistance = 70;
    dateAxis.baseInterval = { count: 1, timeUnit: "day" };
    
    dateAxis.renderer.tooltipLocation = 0;
    dateAxis.startLocation = -0.5;
    dateAxis.renderer.line.strokeDasharray = "1,4";
    dateAxis.renderer.line.strokeOpacity = 0.7;
    dateAxis.tooltip.background.fillOpacity = 0.2;
    dateAxis.tooltip.background.cornerRadius = 5;
    dateAxis.tooltip.label.fill = new am4core.InterfaceColorSet().getFor("alternativeBackground");
    dateAxis.tooltip.label.paddingTop = 7;
    
    var labelTemplate = dateAxis.renderer.labels.template;
    labelTemplate.verticalCenter = "middle";
    labelTemplate.fillOpacity = 0.7;
    labelTemplate.background.fill =  am4core.color("''' + gc_bg_color + '''");
    labelTemplate.fill = am4core.color("''' + gc_text_color + '''");
    labelTemplate.background.fillOpacity = 1;
    labelTemplate.padding(7,7,7,7);
    
    var categoryAxisLabelTemplate = categoryAxis.renderer.labels.template;
    categoryAxisLabelTemplate.horizontalCenter = "left";
    categoryAxisLabelTemplate.adapter.add("rotation", function (rotation, target) {
      var position = dateAxis.valueToPosition(dateAxis.min);
      return dateAxis.renderer.positionToAngle(position) + 90;
    })
    
    var series1 = chart.series.push(new am4plugins_timeline.CurveColumnSeries());
    series1.columns.template.height = am4core.percent(20);
    
    series1.dataFields.openDateX = "start";
    series1.dataFields.dateX = "end";
    series1.dataFields.categoryY = "category";
    series1.columns.template.propertyFields.fill = "color"; // get color from data
    series1.columns.template.propertyFields.stroke = "color";
    series1.columns.template.strokeOpacity = 0;
    

    var imageBullet1 = series1.bullets.push(new am4plugins_bullets.PinBullet());
        imageBullet1.background.radius = 18;
        imageBullet1.locationX = 1;
        imageBullet1.propertyFields.stroke = "color";
        imageBullet1.background.propertyFields.fill = "color";
        imageBullet1.image = new am4core.Image();
        imageBullet1.image.propertyFields.href = "icon";
        imageBullet1.image.scale = 0.7;
        imageBullet1.circle.radius = am4core.percent(100);
        imageBullet1.background.fillOpacity = 0.8;
        imageBullet1.background.strokeOpacity = 0;
        imageBullet1.dy = -2;
        imageBullet1.background.pointerBaseWidth = 10;
        imageBullet1.background.pointerLength = 10
        imageBullet1.tooltipText = "[bold]{start}[/]: \\n {text}";

   
    chart.scrollbarX = new am4core.Scrollbar();
    chart.scrollbarX.align = "center"
    chart.scrollbarX.width = am4core.percent(90);
    
    var cursor = new am4plugins_timeline.CurveCursor();
    chart.cursor = cursor;
    cursor.xAxis = dateAxis;
    cursor.yAxis = categoryAxis;
    cursor.lineY.disabled = true;
    cursor.lineX.strokeDasharray = "1,4";
    cursor.lineX.strokeOpacity = 1;
    
    dateAxis.renderer.tooltipLocation2 = 0;
    categoryAxis.cursorTooltipEnabled = false;
    
    }); // end am4core.ready()
    </script>    
    <!-- HTML -->
    <div id="chartdiv"></div>
</body>    
</html>    
    '''


if __name__ == "__main__":
    main()

