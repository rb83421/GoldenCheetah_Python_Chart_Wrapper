import bisect
import pathlib
import tempfile

import plotly

from GC_DATA import GC_wrapper as GC

import plotly.graph_objects as go
import math
import pandas as pd

smooth_value = 20

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)


def main():
    activity = GC.activity()
    activity_df = pd.DataFrame(activity, index=activity['seconds'])
    # activity_df = activity_df.head(30 * 60)
    # activity_df = activity_df.head(365)
    reference_location = [((activity_df.latitude.max() - activity_df.latitude.min()) / 2) + activity_df.latitude.min(),
                          ((activity_df.longitude.max() - activity_df.longitude.min()) / 2) + activity_df.longitude.min()]
    max_altitude = activity_df.altitude.max()

    activity_df['x'], activity_df['y'], activity_df['z'] = zip(*activity_df.apply(lambda row:
                                                                                  lla2flat([row['latitude'],
                                                                                            row['longitude'],
                                                                                            row['altitude']],
                                                                                           reference_location,
                                                                                           0,
                                                                                           -max_altitude)
                                                                                  , axis=1))
    # activity_df['x'], activity_df['y'], activity_df['z'] = zip(*activity_df.apply(lambda row:
    #                                                                               geodetic_to_ecef(row['latitude'],
    #                                                                                         row['longitude'],
    #                                                                                         row['altitude'])
    #
    #
    #                                                                               , axis=1))

    gradiant_dict = {
        'breaks': [-15, -7.5, 0, 7.5, 15, 20, 100],
        # 'colors': ['blue', 'lightblue', 'green', 'gray', 'yellow', 'orange', 'red'],
        #           <-15 darkblue,   <-7.5 mid blue,    <0 lightblue   , >0 green,        >7.5 yellow,      >15 light red,   >20 dark red
        'colors': ['rgba(0,0,133,0.6)',  'rgba(30,20,255,0.6)', 'rgba(80,235,255,0.6)', 'rgba(80,255,0,0.6)', 'rgba(255,255,0,0.6)', 'rgba(235,0,0,0.6)', 'rgba(122, 0,0,0.6)']
    }
    gradiant_df = pd.DataFrame(gradiant_dict)

    data=[]
    data.append(
        go.Scatter(
            mode='lines+markers',
            x=activity_df.seconds,
            y=activity_df.z,
            name="Altitude",
            showlegend=True,
        )
    )

    data.append(
        go.Scatter(
            mode='lines+markers',
            x=activity_df.seconds,
            y=activity_df.slope,
            name="Slope",
            showlegend=True,
        )
    )

    activity_df['smooth_slope'] = activity_df.slope.rolling(20).mean()
    data.append(
        go.Scatter(
            mode='lines+markers',
            x=activity_df.seconds,
            y=activity_df.smooth_slope,
            name="Sooth Slope",
            showlegend=True,
        )
    )


    # Slice per x  seconds
    slice_value = 10
    number_slices = len(activity_df.index) / slice_value
    shapes = []
    cumulative_gain = 0
    paths = []
    for i in range(int(number_slices)):
        start = i * slice_value
        # last slice take last sample
        if i == int(number_slices) - 1:
            stop = -1
        else:
            stop = (i * slice_value) + slice_value

        tmp = ""
        # # new_df = activity_df.iloc[i*slice_value:(i*slice_value)+slice_value][['x', 'z', 'altitude']]
        #
        # new_df = activity_df.iloc[[(i * slice_value), ((i * slice_value) + slice_value)]][['x', 'y', 'altitude', 'seconds']]
        #
        # # determine bucket
        altitude_gain = activity_df.z.iloc[stop] - activity_df.z.iloc[start]
        index = bisect.bisect_left(gradiant_df.breaks, altitude_gain)
        color = gradiant_df.colors[index]
        start_x = activity_df.x.iloc[start]
        stop_x = activity_df.x.iloc[stop]
        start_y = activity_df.y.iloc[start]
        stop_y = activity_df.y.iloc[stop]
        start_altitude = activity_df.z.iloc[start]
        stop_altitude = activity_df.z.iloc[stop]

        if i == 0 or paths[-1]['color'] != color:
            # create new path (polygon)
            path_new = ("M " + str(activity_df.seconds.iloc[start]) + "," + "0" +
                        " L" + str(activity_df.seconds.iloc[start]) + "," + str(start_altitude) +
                        " L" + str(activity_df.seconds.iloc[stop]) + "," + str(stop_altitude) +
                        " L" + str(activity_df.seconds.iloc[stop]) + "," + "0Z")
            paths.append({'path': path_new,
                        'color': color,
                        })
        else:
            # extend previous polygon
            last = len(paths)-1
            prev_path = paths[last]
            new_path = prev_path['path'].rsplit('L', 1)[0] + \
                       " L" + str(activity_df.seconds.iloc[stop]) + "," + str(stop_altitude) + \
                       " L" + str(activity_df.seconds.iloc[stop]) + "," + "0Z"
            paths[last]['path'] = new_path


        # path_new = ("M " + str(activity_df.seconds.iloc[start]) + "," + "0" +
        #             " L" + str(activity_df.seconds.iloc[start]) + "," + str(start_altitude) +
        #        " L" + str(activity_df.seconds.iloc[stop]) + "," + str(stop_altitude) +
        #        " L" + str(activity_df.seconds.iloc[stop]) + "," + "0 Z")
        # paths.append({'path': path_new,
        #               'color': color,
        #               })
    print("Number of polygons: " + str(len(paths)))
    for path in paths:
        shapes.append(go.layout.Shape(
            type="path",
            path=path['path'],
            fillcolor=path['color'],
            line=dict(
                color=path['color'],
                width=1
            )
            # line_color="Red",
        ))

    fig = go.Figure(data=data)
    fig.update_layout(
        shapes=shapes,
    )
    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())

def lla2flat(lla, llo, psio, href):
    R = 6378137.0  # Equator radius in meters
    f = 0.00335281066474748071  # 1/298.257223563, inverse flattening

    '''
    lla  -- array of geodetic coordinates 
            (latitude, longitude, and altitude), 
            in [degrees, degrees, meters]. 
            Latitude and longitude values can be any value. 
            However, latitude values of +90 and -90 may return 
            unexpected values because of singularity at the poles.
    llo  -- Reference location, in degrees, of latitude and 
            longitude, for the origin of the estimation and 
            the origin of the flat Earth coordinate system.
    psio -- Angular direction of flat Earth x-axis 
            (degrees clockwise from north), which is the angle 
            in degrees used for converting flat Earth x and y 
            coordinates to the North and East coordinates.
    href -- Reference height from the surface of the Earth to 
            the flat Earth frame with regard to the flat Earth 
            frame, in meters.
    usage: print(lla2flat((0.1, 44.95, 1000.0), (0.0, 45.0), 5.0, -100.0))
    '''

    Lat_p = lla[0] * math.pi / 180.0  # from degrees to radians
    Lon_p = lla[1] * math.pi / 180.0  # from degrees to radians
    Alt_p = lla[2]  # meters

    # Reference location (lat, lon), from degrees to radians
    Lat_o = llo[0] * math.pi / 180.0
    Lon_o = llo[1] * math.pi / 180.0

    psio = psio * math.pi / 180.0  # from degrees to radians

    dLat = Lat_p - Lat_o
    dLon = Lon_p - Lon_o

    ff = (2.0 * f) - (f ** 2)  # Can be precomputed

    sinLat = math.sin(Lat_o)

    # Radius of curvature in the prime vertical
    Rn = R / math.sqrt(1 - (ff * (sinLat ** 2)))

    # Radius of curvature in the meridian
    Rm = Rn * ((1 - ff) / (1 - (ff * (sinLat ** 2))))

    dNorth = (dLat) / math.atan2(1, Rm)
    dEast = (dLon) / math.atan2(1, (Rn * math.cos(Lat_o)))

    # Rotate matrice clockwise
    Xp = (dNorth * math.cos(psio)) + (dEast * math.sin(psio))
    Yp = (-dNorth * math.sin(psio)) + (dEast * math.cos(psio))
    Zp = -Alt_p - href

    return Xp, -Yp, Zp


if __name__ == "__main__":
    main()
