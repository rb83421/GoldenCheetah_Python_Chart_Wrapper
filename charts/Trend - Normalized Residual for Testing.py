# Normalized Residual for Testing V2 (Py)
# This is an python chart.
# It show your Extended CP chart and determines your target power for a short/medium and long duration.
# Any remarks or questions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
# V1 - 2019-09-20 - initial chart
# V2 - 2019-10-29 - Make linux compatible
from GC_DATA import GC_wrapper as GC
import pathlib
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import numpy as np
import tempfile
import datetime
from scipy import stats
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
    dd = np.asarray(mmp["power_date"])[1:]
    xx = np.asarray(range(1, len(yy)))
    ep = np.ones(len(yy))  ##none drops thru

    print(len(yy), len(ep))

    # truncate to first 2 hours of data
    if len(yy) > 7200:
        yy = yy[0:7200]
        xx = xx[0:7200]
        ep = ep[0:7200]

    # Fit with "regress" weighting if enough data
    if len(yy) > 1200:
        x = xx[120:1200]
        y = yy[120:1200] * x
        d = dd[120:1200]
        slope, intercept, r, p, e = stats.linregress(x, y)
        print("Classic CP=", slope, "W'=", intercept)

    if weight == "regress":
        # weight the actuals vs regression
        # scale by uncertainty - big numbers = less good data
        ep = 1 / (yy / (slope + (intercept / xx)))
        # anchor on 1s power... not happy !!!!
        ep[0] = 1

    if weight == "date":
        # only keep one unique effort per day
        # use regress to determine hardest effort
        nodate = datetime.date(1900, 1, 1)
        for i in range(0, len(yy) - 1):

            # if it survived pass
            if (dd[i] != nodate):

                working = dd[i]
                keep = i
                weight = (yy[i] - slope) * xx[i]

                # whizz thru all entries to end with the
                # same date and remember which to keep
                # when keep is bettered, clear it
                for t in range(i + 1, len(yy)):

                    if (dd[t] == working):
                        thisweight = ((yy[t] * xx[t]) - weight) / xx[t]
                        if (thisweight > slope):
                            dd[keep] = nodate
                            ep[keep] = 8
                            keep = t
                        else:
                            dd[t] = nodate
                            ep[t] = 8

                ep[keep] = 1
                dd[keep] = nodate

        # anchor 1s power
        ep[0] = 1

    # initial fit
    params = Parameters()
    params.add('paa', value=811)
    params.add('paadec', value=-2)
    params.add('cp', value=280)
    params.add('tau', value=1.208)
    params.add('taudel', value=-4.8)
    params.add('cpdel', value=-0.9)
    params.add('cpdec', value=-0.583)
    params.add('cpdecdel', value=-180)

    # handy
    zero = np.zeros(len(yy))
    one = np.ones(len(yy))

    # fit
    out = minimize(excp, params, args=(xx, yy, ep))
    out.params.pretty_print()

    w1 = intercept
    w2 = out.params["cp"].value * out.params["tau"].value
    w = (w1 + w2) / 2

    print("Extended CP=", out.params["cp"].value,
          "W'=", out.params["cp"].value * out.params["tau"].value)

    # model derived values
    mod = excp(out.params, xx, zero, one) * -1

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

    # Start building charts
    fig = make_subplots(
        rows=3, cols=3,
        specs=[[{"colspan": 3}, None, None],
               [{"colspan": 3}, None, None],
               [{}, {}, {}]],
        subplot_titles=(
            "Extended CP Model", "Normalized/Residual", "Short duration test target", "Medium duration test target",
            "Long duration test target"),
        vertical_spacing=0.10,
    )

    # meanmax curve
    fig.add_trace(
        go.Scatter(
            x=xx,
            y=yy,
            mode='markers',
            name="mean maximal",
            hovertext=["Watts: " + str(watts) + "<br>Time: " + str(format_seconds(i)) for i, watts in zip(xx, yy)],
            hoverinfo="text",
        ), row=1, col=1
    )

    # model curve
    fig.add_trace(
        go.Scatter(x=xx,
                   y=mod,
                   line=dict(shape='spline'),
                   name="eCP model",
                   hovertext=["Watts: " + str(int(watts)) + "<br>Time: " + str(format_seconds(i)) for i, watts in
                              zip(xx, mod)],
                   hoverinfo="text",
                   ), row=1, col=1
    )
    # Residual
    fig.add_trace(
        go.Scatter(x=xx,
                   y=residual,
                   line=dict(shape='spline'),
                   name="Residual",
                   hovertext=["Residual Watts: " + str(int(watts)) + "<br>Time: " + str(format_seconds(i)) for i, watts in
                              zip(xx, residual)],
                   hoverinfo="text",
                   ), row=2, col=1
    )
    # Normalized
    fig.add_trace(
        go.Scatter(x=xx,
                   y=norm,
                   line=dict(shape='spline'),
                   name="Normalized",
                   hovertext=["Normalized: " + str(round(normalize, 2)) + "<br>Time: " + str(format_seconds(i)) for i, normalize in
                              zip(xx, norm)],
                   hoverinfo="text",
                   ), row=2, col=1
    )

    add_duration_target(fig,
                        mod[short_duration_index],
                        yy[short_duration_index],
                        short_duration_bracket,
                        xx[short_duration_index],
                        "Short",
                        1,
                        pmax)
    add_duration_target(fig, mod[medium_duration_index],
                        yy[medium_duration_index],
                        medium_duration_bracket,
                        xx[medium_duration_index],
                        "Medium",
                        2,
                        pmax)
    add_duration_target(fig, mod[long_duration_index],
                        yy[long_duration_index],
                        long_duration_bracket,
                        xx[long_duration_index],
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
        # cp report
        go.layout.Annotation(
            x=1,
            y=400,
            showarrow=False,
            text='CP ~%d (%d - %d)' %
                 ((slope + out.params["cp"].value) / 2,
                  slope, out.params["cp"].value),
            font=dict(family='Courier New, monospace',
                      size=20, color="#ff0000"),
            xref="x1",
            yref="y1"
        )
    )
    current_annotation_list.append(
        # w' report
        go.layout.Annotation(
            x=1,
            y=220,
            xref='x1', yref='y1',
            text="W\' ~%d (%d - %d)" %
                 (w, w1, w2),
            font=dict(family='Courier New, monospace',
                      size=20, color="#ff0000"),
            showarrow=False
        )
    )
    fig["layout"]["annotations"] += tuple(current_annotation_list)

    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


# GC Extended CP model
def excp(params, x, data, eps):
    ##x=x/60.00
    paa = params["paa"]
    paadec = params["paadec"]
    cp = params["cp"]
    tau = params["tau"]
    taudel = params["taudel"]
    cpdel = params["cpdel"]
    cpdec = params["cpdec"]
    cpdecdel = params["cpdecdel"]

    model = (paa * (1.20 - 0.20 * np.exp(-1 * x)) * np.exp(paadec * (x)) + (
            cp * (1 - np.exp(taudel * x)) * (1 - np.exp(cpdel * x)) * (1 + cpdec * np.exp(cpdecdel / x)) * (
            tau / (x))) + (cp * (1 - np.exp(taudel * x)) * (1 - np.exp(cpdel * x)) * (
            1 + cpdec * np.exp(cpdecdel / x)) * (1)))

    model = np.nan_to_num(model)
    model[model > 2000] = 0
    model[model < 1] = 0
    rt = (data - model) / eps

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
