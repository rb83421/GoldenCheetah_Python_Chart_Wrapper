"""
MMP compare V1 (Py)
This is an python chart.
This chart will show your all time and the selected season:
 * Max power peak
 * Average power of the top 5
 * Percentage top5 against the max

Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
V1 - 2021-02-24 - initial chart
"""

from GC_Wrapper import GC_wrapper as GC

import pathlib
import tempfile
import pandas as pd

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'

durations = [5,10,600]

def main():
    season_info = GC.season()
    html = []
    for duration in durations:
        html.append("<h1>MMP: " + str(format_seconds(duration)) + "</h1>")
        html.append(get_table_for_duration(duration, str(season_info['name'][0])))
        html.append("</br>")
    write_html(html)


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


def get_table_for_duration(duration, season_name):
    all = pd.DataFrame(GC.seasonPeaks(all=True, series='power', duration=duration))
    season = pd.DataFrame(GC.seasonPeaks(series='power', duration=duration))
    field = 'peak_power_' + str(duration)
    df = pd.DataFrame({
        'Max': [all[field].max(), season[field].max()],
        'Avg top 5': [all.nlargest(5, field).mean().values[0], season.nlargest(5, field).mean().values[0]],
    })
    df['Percentage of Max (%)'] = (df['Avg top 5'] / df['Max']) * 100
    df = df.round(2)
    df.index = ['All', season_name]
    return df.to_html()


def write_html(html):
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

    table {
      border-collapse: collapse;
    }
    
    th, td {
      padding: 8px;
      text-align: left;
      border-top: 1px solid #343434;
      border-left: 1px solid #343434;
      border-right: 1px solid #343434;

      border-bottom: 1px solid #ddd;
    }


    </style>
  <meta charset="utf-8">

</head>
<body class="black_back">
''' + ' '.join([str(line) for line in html]) + '''
</body>
</html>        
        '''
    temp_file.writelines(html)
    temp_file.close()


if __name__ == "__main__":
    main()
    GC.webpage(pathlib.Path(temp_file.name).as_uri())

