# Normalized Residual for Testing Peronnet Thibault V1 (Py)
# This is an python chart.
# It show your MMP  chart and determines your target power for a short/medium and long duration.
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
# V1 - 2019-09-20 - initial chart model based on WKO4 chart

from GC_Wrapper import GC_wrapper as GC

import pathlib
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import numpy as np
import tempfile
from lmfit import minimize, Parameters
import bisect

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


# weight = "regress"  # one of "none", "regress" or "date" or "logistic"

def main():
    weight = "regress"  # one of "none", "regress" or "date" or "logistic"

    # Get data
    mmp = GC.seasonMeanmax()
    pmax = max(mmp['power'])

    # get meanmax power data as whole watts
    yy = np.rint(np.asarray(mmp["power"])[1:])
    secs = np.asarray(range(1, len(yy)))

    # truncate to first 2 hours of data
    if len(yy) > 7200:
        yy = yy[0:7200]
        secs = secs[0:7200]


    # initial fit
    params = Parameters()
    params.add('ftp', value=200)
    params.add('frc', value=11000)
    params.add('pmax', value=1000)
    params.add('a', value=40)
    params.add('tau2', value=50)
    params.add('tte', value=1800)

    out = minimize(peronnet_thibault, params, args=(secs, yy))
    #out.params.pretty_print()

    print("FTP=", out.params["ftp"].value,
          "PMax=", out.params["pmax"].value,
          "FRC=", out.params["frc"].value,
          "TTE=", out.params["tte"].value)

    # model derived values
    zero = np.zeros(len(yy))
    mod = peronnet_thibault(out.params, secs, zero) * -1

    # substract predicted (mod) and measured (yy)
    residual = np.subtract(yy, mod)

    # Normalize
    a = -10
    b = 10
    minimal = min(residual)
    maximal = max(residual)
    # norm = [(number - a) / (b - a) for number in residual]
    norm = [a + ((number - minimal) * (b - a) / (maximal - minimal)) for number in residual]

    # Find short medium long duration test targets
    short_duration_bracket = [15, 40]  # 15 - 40 seconds
    medium_duration_bracket = [60, 900]  # 1 - 15 minutes
    long_duration_bracket = [1200, 2400]  # 20 - 40 minutes

    short_duration_index = norm.index(min(norm[short_duration_bracket[0]:short_duration_bracket[1]]))
    medium_duration_index = norm.index(min(norm[medium_duration_bracket[0]:medium_duration_bracket[1]]))
    long_duration_index = norm.index(min(norm[long_duration_bracket[0]:long_duration_bracket[1]]))

    # Start building chart_not_working_yet_after_single_extract
    fig = make_subplots(
        rows=3, cols=3,
        specs=[[{"colspan": 3}, None, None],
               [{"colspan": 3}, None, None],
               [{}, {}, {}]],
        subplot_titles=(
            "Peronnet Thibault Model", "Normalized/Residual", "Short duration test target", "Medium duration test target",
            "Long duration test target"),
        vertical_spacing=0.10,
    )

    # meanmax curve
    fig.add_trace(
        go.Scatter(
            x=secs,
            y=yy,
            mode='lines',
            line=dict(color='orange',
                      width=1,
                      dash='dash'
                      ),
            name="mean maximal",
            hovertext=["Watts: " + str(watts) + "<br>Time: " + str(format_seconds(i)) for i, watts in zip(secs, yy)],
            hoverinfo="text",
        ), row=1, col=1
    )

    # model curve
    fig.add_trace(
        go.Scatter(x=secs,
                   y=mod,
                   line=dict(shape='spline'),
                   name="Peronnet Thibault model",
                   hovertext=["Watts: " + str(int(watts)) + "<br>Time: " + str(format_seconds(i)) for i, watts in
                              zip(secs, mod)],
                   hoverinfo="text",
                   ), row=1, col=1
    )
    # Residual
    fig.add_trace(
        go.Scatter(x=secs,
                   y=residual,
                   line=dict(shape='spline'),
                   name="Residual",
                   hovertext=["Residual Watts: " + str(int(watts)) + "<br>Time: " + str(format_seconds(i)) for i, watts in
                              zip(secs, residual)],
                   hoverinfo="text",
                   ), row=2, col=1
    )
    # Normalized
    fig.add_trace(
        go.Scatter(x=secs,
                   y=norm,
                   line=dict(shape='spline'),
                   name="Normalized",
                   hovertext=["Normalized: " + str(round(normalize, 2)) + "<br>Time: " + str(format_seconds(i)) for i, normalize in
                              zip(secs, norm)],
                   hoverinfo="text",
                   ), row=2, col=1
    )

    add_duration_target(fig,
                        mod[short_duration_index],
                        yy[short_duration_index],
                        short_duration_bracket,
                        secs[short_duration_index],
                        "Short",
                        1,
                        pmax)
    add_duration_target(fig, mod[medium_duration_index],
                        yy[medium_duration_index],
                        medium_duration_bracket,
                        secs[medium_duration_index],
                        "Medium",
                        2,
                        pmax)
    add_duration_target(fig, mod[long_duration_index],
                        yy[long_duration_index],
                        long_duration_bracket,
                        secs[long_duration_index],
                        "Long",
                        3,
                        pmax)

  #  tick_values = np.logspace(0.01, math.log10(max(xx)), 50, base=10, endpoint=True)
    tick_values = [1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 40, 60, 120, 180, 240, 360, 480, 600, 900, 1200, 1800, 2400, 3600, 7200]

    fig.update_layout(
        go.Layout(
            paper_bgcolor=gc_bg_color,
            plot_bgcolor=gc_bg_color,
            font=dict(
                color=gc_text_color,
                size=12
            ),
            showlegend=True,
            xaxis1=dict(
                type='log',
                tickangle=45,
                tickvals=tick_values,
                ticktext=[format_seconds(i) for i in tick_values],
            ),
            xaxis2=dict(
                type='log',
                tickangle=45,
                tickvals=tick_values,
                ticktext=[format_seconds(i) for i in tick_values],
            ),
            margin={'t': 10},
        )
    )
    current_annotation_list = list(fig["layout"]["annotations"])
    current_annotation_list.append(
        # FTP report
        go.layout.Annotation(
            x=1,
            y=400,
            showarrow=False,
            text='FTP: %d Pmax: %d FRC: %d TTE: %d' %
                 (out.params["ftp"].value, out.params["pmax"].value, out.params["frc"].value, out.params["tte"].value),
            font=dict(family='Courier New, monospace',
                      size=20, color="#ff0000"),
            xref="x1",
            yref="y1"
        )
    )

    fig["layout"]["annotations"] += tuple(current_annotation_list)

    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    # Workaround for fixing margin
    text = pathlib.Path(temp_file.name).read_text()
    text = text.replace('<body>', '<body style="margin: 0px;">')
    pathlib.Path(temp_file.name).write_text(text)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def f(x):
    return np.int(x)


# Peronnet-Thibault Model
def peronnet_thibault(params, x, data):
    ftp = params['ftp']
    frc = params['frc']
    pmax = params['pmax']
    a = params['a']
    tau2 = params['tau2']
    tte = params['tte']

    f2 = np.vectorize(f)
    model = (frc / x * (1 - np.exp(-x / (frc / pmax)))) + \
            ((ftp * (1 - np.exp(-x / tau2))) - (f2(x > tte) * (a * np.log(x / tte))))
#    model = np.nan_to_num(model)
#    model[model > 2000] = 0
    model[model < 1] = 0
    rt = (data - model)
    return rt


def format_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return_value = '%dh%dm%ds' % (hours, minutes, secs)
    elif minutes > 0:
        return_value = '%dm%ds' % (minutes, secs)
    else:
        return_value = '%ds' % (secs)

    #return '%02d:%02d:%02d' % (hours, minutes, secs)
    return return_value


def format_hms_seconds(secs):
    minutes, secs = divmod(secs, 60)
    hours, minutes = divmod(minutes, 60)
    return '%02d:%02d:%02d' % (hours, minutes, secs)


def add_duration_target(fig, target_watts, current_watts, duration_bracket, duration, legend_name, column, pmax):
    # divide fairly within an array of 7
    x = np.linspace(min(duration_bracket), max(duration_bracket), num=7)
    y = np.zeros(len(x))
    # Find the index of close enough to duration
    index = bisect.bisect_left(x, duration)
    # insert the target test for the target duration
    y[index] = target_watts
    # modify the x to exact duration value
    x[index] = duration
    fig.add_trace(
        go.Bar(x=[format_hms_seconds(i)for i in x],
               y=y,
               text=[int(watts) for watts in y],
               hovertext=["Target Watts: " + str(int(watts)) + "<br>Time: " + str(format_seconds(i)) for
                          i, watts in
                          zip(x, y)],
               hoverinfo="text",
               textposition='auto',
               name=legend_name + " - Target",
               ), row=3, col=column
    )
    y[index] = current_watts
    fig.add_trace(
        go.Bar(x=[format_hms_seconds(i)for i in x],
               y=y,
               text=[int(watts) for watts in y],
               hovertext=["Current Watts: " + str(int(watts)) + "<br>Time: " + str(format_seconds(i)) for
                          i, watts in
                          zip(x, y)],
               hoverinfo="text",
               textposition='auto',
               name=legend_name + " - Current",
               ), row=3, col=column
    )
    fig.update_xaxes(tickangle=45, row=3, col=column)
    fig.update_yaxes(range=[0, pmax], row=3, col=column)


if __name__ == "__main__":
    main()
