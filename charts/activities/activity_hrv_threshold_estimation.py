"""
HRV Threshold estimation V1 (Py)
On request created for GC from the following github
For information how to use see:
reference code: https://github.com/marcoalt/Colab/blob/main/hrv_thresholds.ipynb

Depending on the ride length is may take a while to process all RR intervals

V1 - 2021-01-23 - initial chart
"""

from GC_Wrapper import GC_wrapper as GC

import pathlib
import plotly
import plotly.graph_objs as go
import numpy as np
import tempfile
import pandas as pd
import math

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


def main():
    RRs = list(GC.xdataSeries('HRV', 'R-R'))
    if RRs:
        # transform RR form milliseconds to seconds
        df_temp = pd.DataFrame()
        df_temp['RR'] = RRs
        RRs = df_temp.RR.div(1000).tolist()

        artifact_correction_threshold = 0.05
        filtered_RRs = []
        for i in range(len(RRs)):
            if RRs[(i - 1)] * (1 - artifact_correction_threshold) < RRs[i] < RRs[(i - 1)] * (
                    1 + artifact_correction_threshold):
                filtered_RRs.append(RRs[i])

        x = np.cumsum(filtered_RRs)

        df = pd.DataFrame()
        df['timestamp'] = x
        df['RR'] = filtered_RRs

        features_df = computeFeatures(df)
        print(features_df.head())
        print("Mean Alpha 1: " + str(round(np.mean(features_df['alpha1']), 2)))

        threshold_sdnn = 10  # rather arbitrary, based on visual inspection of the data
        features_df_filtered = features_df.loc[features_df['sdnn'] < threshold_sdnn,]

        print("Mean Alpha 1, filtered based on sdnn > " + str(threshold_sdnn) + ": " + str(round(np.mean(features_df_filtered['alpha1']), 2)))

        from sklearn.linear_model import LinearRegression

        length = len(features_df['alpha1'])
        reg = LinearRegression().fit(features_df['alpha1'].values.reshape(length, 1),
                                     features_df['heartrate'].values.reshape(length, 1))
        prediction = reg.predict(np.array(0.75).reshape(1, 1))
        print("Predication: " + str(math.floor(prediction)))


        fig = go.Figure()
        fig.add_trace(go.Scatter(x=features_df.timestamp,
                        y=features_df.alpha1,
                        mode='lines+markers',))

        # This can be used when an intensity is only increasing
        # also change xasis when enabling this
        # fig.add_trace(go.Scatter(x=features_df.heartrate,
        #                 y=features_df.alpha1,
        #                 mode='lines+markers',))


        fig.update_layout(
            title='Estimated aerobic threshold heart rate (alpha 1 = 0.75): ' + (str(math.floor(prediction[0].item()))) + " bpm",
            paper_bgcolor=gc_bg_color,
            plot_bgcolor=gc_bg_color,
            font=dict(
                color=gc_text_color,
                size=12
            ),
            xaxis=dict(
                title="Window",
            ),
            yaxis=dict(
                title="alpha 1",
            ),
        )

        plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
        text = pathlib.Path(temp_file.name).read_text()
        text = text.replace('<body>', '<body style="margin: 0px;">')
        pathlib.Path(temp_file.name).write_text(text)
    else:
        create_empty_page()

    GC.webpage(pathlib.Path(temp_file.name).as_uri())


def create_empty_page():
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

        <h1>NO HRV RR intervals found unable to create chart</h1>
        </body>
    </html>
    """]
    f.writelines(lines_of_text)
    f.close()


def DFA(pp_values, lower_scale_limit, upper_scale_limit):
    scaleDensity = 30 # scales DFA is conducted between lower_scale_limit and upper_scale_limit
    m = 1 # order of polynomial fit (linear = 1, quadratic m = 2, cubic m = 3, etc...)

    # initialize, we use logarithmic scales
    start = np.log(lower_scale_limit) / np.log(10)
    stop = np.log(upper_scale_limit) / np.log(10)
    scales = np.floor(np.logspace(np.log10(math.pow(10, start)), np.log10(math.pow(10, stop)), scaleDensity))
    F = np.zeros(len(scales))
    count = 0

    for s in scales:
        rms = []
        # Step 1: Determine the "profile" (integrated signal with subtracted offset)
        x = pp_values
        y_n = np.cumsum(x - np.mean(x))
        # Step 2: Divide the profile into N non-overlapping segments of equal length s
        L = len(x)
        shape = [int(s), int(np.floor(L/s))]
        nwSize = int(shape[0]) * int(shape[1])
        # beginning to end, here we reshape so that we have a number of segments based on the scale used at this cycle
        Y_n1 = np.reshape(y_n[0:nwSize], shape, order="F")
        Y_n1 = Y_n1.T
        # end to beginning
        Y_n2 = np.reshape(y_n[len(y_n) - (nwSize):len(y_n)], shape, order="F")
        Y_n2 = Y_n2.T
        # concatenate
        Y_n = np.vstack((Y_n1, Y_n2))

        # Step 3: Calculate the local trend for each 2Ns segments by a least squares fit of the series
        for cut in np.arange(0, 2 * shape[1]):
            xcut = np.arange(0, shape[0])
            pl = np.polyfit(xcut, Y_n[cut,:], m)
            Yfit = np.polyval(pl, xcut)
            arr = Yfit - Y_n[cut,:]
            rms.append(np.sqrt(np.mean(arr * arr)))

        if (len(rms) > 0):
            F[count] = np.power((1 / (shape[1] * 2)) * np.sum(np.power(rms, 2)), 1/2)
        count = count + 1

    pl2 = np.polyfit(np.log2(scales), np.log2(F), 1)
    alpha = pl2[0]
    return alpha


def computeFeatures(df):
    features = []
    step = 120
    x = df.timestamp
    for index in range(0, int(round(np.max(x) / step))):
        array_rr = df.loc[(df['timestamp'] >= (index * step)) & (df['timestamp'] <= (index + 1) * step), 'RR'] * 1000
        # compute heart rate
        heartrate = round(60000 / np.mean(array_rr), 2)
        # compute rmssd
        NNdiff = np.abs(np.diff(array_rr))
        rmssd = round(np.sqrt(np.sum((NNdiff * NNdiff) / len(NNdiff))), 2)
        # compute sdnn
        sdnn = round(np.std(array_rr), 2)
        # dfa, alpha 1
        alpha1 = DFA(array_rr.to_list(), 4, 16)

        curr_features = {
            'timestamp': index,
            'heartrate': heartrate,
            'rmssd': rmssd,
            'sdnn': sdnn,
            'alpha1': alpha1,
        }

        features.append(curr_features)

    features_df = pd.DataFrame(features)
    return features_df


if __name__ == "__main__":
    main()
