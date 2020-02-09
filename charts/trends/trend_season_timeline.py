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


def get_time_line_data(season_metrics):
    items = []
    for i in range(len(season_metrics['date'])):
        date = season_metrics['date'][i]
        time = season_metrics['time'][i]
        color = get_color_for_sport(season_metrics['Sport'][i])
        sport = season_metrics['Sport'][i]
        if sport == "Fitness":
            text = season_metrics['Notes'][i].encode('utf-8')
        else:
            text = season_metrics['Workout_Title'][i]

        items.append('''{
            "category": "",
            "start": "''' + str(date) + ''' ''' + str(time) + '''",
            "end": "''' + str(date) + ''' ''' + str(time) + '''",
            "color":         am4core.color("''' + str(color) + '''"),
            "icon": ''' + str(sport) + ''',
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
        max-width: 100%;
        height: 500px;
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

    // Themes begin
    am4core.useTheme(am4themes_animated);
    // Themes end

    var Walking =  "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/0_Walking_Pin.png";
    var Run =  "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/1_Running_Pin.png";
    var Fitness =  "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/3_Exercise_Pin.png";
    var Bike = "https://raw.githubusercontent.com/rb83421/GoldenCheetah_Python_Chart_Wrapper/master/chart_images/4_Road_Cycling_Pin.png";   


    am4core.ready(function() {
        var chart = am4core.create("chartdiv", am4plugins_timeline.CurveChart);
        chart.curveContainer.padding(100, 20, 50, 20);
        chart.maskBullets = false;


    ''' + str(chart_data) + '''    


        var colorSet = new am4core.ColorSet();

        chart.dateFormatter.inputDateFormat = "yyyy-MM-dd HH:mm:ss";
        chart.dateFormatter.dateFormat = "dd";


        chart.fontSize = 10;
        chart.tooltipContainer.fontSize = 10;

        var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
        categoryAxis.dataFields.category = "category";
        categoryAxis.renderer.grid.template.disabled = true;
        categoryAxis.renderer.labels.template.paddingRight = 25;
        categoryAxis.renderer.minGridDistance = 10;
        categoryAxis.renderer.innerRadius = 10;
        categoryAxis.renderer.radius = 30;

        var dateAxis = chart.xAxes.push(new am4charts.DateAxis());


        dateAxis.renderer.points = getPoints();


        dateAxis.renderer.autoScale = false;
        dateAxis.renderer.autoCenter = false;
        dateAxis.renderer.minGridDistance = 70;
        dateAxis.baseInterval = { count: 30, timeUnit: "minutes" };
        dateAxis.renderer.tooltipLocation = 0;
        dateAxis.renderer.line.strokeDasharray = "1,4";
        dateAxis.renderer.line.strokeOpacity = 0.5;
        dateAxis.tooltip.background.fillOpacity = 0.2;
        dateAxis.tooltip.background.cornerRadius = 5;
        dateAxis.tooltip.label.fill = new am4core.InterfaceColorSet().getFor("alternativeBackground");
        dateAxis.tooltip.label.paddingTop = 7;
        dateAxis.endLocation = 0;
        dateAxis.startLocation = -0.5;
        dateAxis.min = ''' + start_time + '''
        dateAxis.max = ''' + stop_time + '''    

        var labelTemplate = dateAxis.renderer.labels.template;
        labelTemplate.verticalCenter = "middle";
        labelTemplate.fillOpacity = 0.6;
        labelTemplate.background.fill = new am4core.InterfaceColorSet().getFor("background");
        labelTemplate.background.fillOpacity = 1;
        labelTemplate.fill = new am4core.InterfaceColorSet().getFor("text");
        labelTemplate.padding(7, 7, 7, 7);

        var series = chart.series.push(new am4plugins_timeline.CurveColumnSeries());
        series.columns.template.height = am4core.percent(30);

        series.dataFields.openDateX = "start";
        series.dataFields.dateX = "end";
        series.dataFields.categoryY = "category";
        series.baseAxis = categoryAxis;
        series.columns.template.propertyFields.fill = "color"; // get color from data
        series.columns.template.propertyFields.stroke = "color";
        series.columns.template.strokeOpacity = 0;
        series.columns.template.fillOpacity = 0.6;

        var imageBullet1 = series.bullets.push(new am4plugins_bullets.PinBullet());
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
        imageBullet1.tooltipText = "{text}";

        series.tooltip.pointerOrientation = "up";

        imageBullet1.background.adapter.add("pointerAngle", (value, target) => {
            if (target.dataItem) {
                var position = dateAxis.valueToPosition(target.dataItem.openDateX.getTime());
                return dateAxis.renderer.positionToAngle(position);
            }
            return value;
        });

        var hs = imageBullet1.states.create("hover")
        hs.properties.scale = 1.3;
        hs.properties.opacity = 1;

        var textBullet = series.bullets.push(new am4charts.LabelBullet());
        textBullet.label.propertyFields.text = "text";
        textBullet.disabled = true;
        textBullet.propertyFields.disabled = "textDisabled";
        textBullet.label.strokeOpacity = 0;
        textBullet.locationX = 1;
        textBullet.dy = - 100;
        textBullet.label.textAlign = "middle";

        chart.scrollbarX = new am4core.Scrollbar();
        chart.scrollbarX.align = "center"
        chart.scrollbarX.width = am4core.percent(75);
        chart.scrollbarX.parent = chart.curveContainer;
        chart.scrollbarX.height = 300;
        chart.scrollbarX.orientation = "vertical";
        chart.scrollbarX.x = 128;
        chart.scrollbarX.y = -140;
        chart.scrollbarX.isMeasured = false;
        chart.scrollbarX.opacity = 0.5;

        var cursor = new am4plugins_timeline.CurveCursor();
        chart.cursor = cursor;
        cursor.xAxis = dateAxis;
        cursor.yAxis = categoryAxis;
        cursor.lineY.disabled = true;
        cursor.lineX.disabled = true;

        dateAxis.renderer.tooltipLocation2 = 0;
        categoryAxis.cursorTooltipEnabled = false;

        chart.zoomOutButton.disabled = true;

        var previousBullet;


        function hoverItem(dataItem) {
            var bullet = dataItem.bullets.getKey(imageBullet1.uid);
            var index = dataItem.index;

            if (index >= series.dataItems.length - 1) {
                index = -1;
            }

            if (bullet) {

                if (previousBullet) {
                    previousBullet.isHover = false;
                }

                bullet.isHover = true;

                previousBullet = bullet;
            }
            setTimeout(
                function() {
                    hoverItem(series.dataItems.getIndex(index + 1))
                }, 1000);
        }

    });


    function getPoints() {

        var points = [{ x: -1300, y: 200 }, { x: 0, y: 200 }];

        var w = 400;
        var h = 400;
        var levelCount = 4;

        var radius = am4core.math.min(w / (levelCount - 1) / 2, h / 2);
        var startX = radius;

        for (var i = 0; i < 25; i++) {
            var angle = 0 + i / 25 * 90;
            var centerPoint = { y: 200 - radius, x: 0 }
            points.push({ y: centerPoint.y + radius * am4core.math.cos(angle), x: centerPoint.x + radius * am4core.math.sin(angle) });
        }


        for (var i = 0; i < levelCount; i++) {

            if (i % 2 != 0) {
                points.push({ y: -h / 2 + radius, x: startX + w / (levelCount - 1) * i })
                points.push({ y: h / 2 - radius, x: startX + w / (levelCount - 1) * i })

                var centerPoint = { y: h / 2 - radius, x: startX + w / (levelCount - 1) * (i + 0.5) }
                if (i < levelCount - 1) {
                    for (var k = 0; k < 50; k++) {
                        var angle = -90 + k / 50 * 180;
                        points.push({ y: centerPoint.y + radius * am4core.math.cos(angle), x: centerPoint.x + radius * am4core.math.sin(angle) });
                    }
                }

                if (i == levelCount - 1) {
                    points.pop();
                    points.push({ y: -radius, x: startX + w / (levelCount - 1) * i })
                    var centerPoint = { y: -radius, x: startX + w / (levelCount - 1) * (i + 0.5) }
                    for (var k = 0; k < 25; k++) {
                        var angle = -90 + k / 25 * 90;
                        points.push({ y: centerPoint.y + radius * am4core.math.cos(angle), x: centerPoint.x + radius * am4core.math.sin(angle) });
                    }
                    points.push({ y: 0, x: 1300 });
                }

            }
            else {
                points.push({ y: h / 2 - radius, x: startX + w / (levelCount - 1) * i })
                points.push({ y: -h / 2 + radius, x: startX + w / (levelCount - 1) * i })
                var centerPoint = { y: -h / 2 + radius, x: startX + w / (levelCount - 1) * (i + 0.5) }
                if (i < levelCount - 1) {
                    for (var k = 0; k < 50; k++) {
                        var angle = -90 - k / 50 * 180;
                        points.push({ y: centerPoint.y + radius * am4core.math.cos(angle), x: centerPoint.x + radius * am4core.math.sin(angle) });
                    }
                }
            }
        }

        return points;
    }


    }); // end am4core.ready()
    </script>

    <!-- HTML -->
    <div id="chartdiv"></div>
</body>    
</html>    
    '''


if __name__ == "__main__":
    main()

