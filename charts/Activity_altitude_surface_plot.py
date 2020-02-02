from GC_DATA import GC_wrapper as GC

import pathlib
import tempfile

import numpy as np
import plotly
import plotly.graph_objects as go
import pandas as pd
import math

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)


def main():
    activity = GC.activity()
    activity_df = pd.DataFrame(activity, index=activity['seconds'])

    # Set max on two hours else i get a memory problem
    activity_df = activity_df.head(30 * 60 * 2)
    # activity_df = activity_df.head(500)

    center_lat = ((activity_df.latitude.max() - activity_df.latitude.min()) / 2) + activity_df.latitude.min()
    center_lon = ((activity_df.longitude.max() - activity_df.longitude.min()) / 2) + activity_df.longitude.min()
    max_altitude = activity_df.longitude.max()
    activity_df['x'], activity_df['y'], activity_df['z'] = zip(*activity_df.apply(lambda row:
                                                                                  lla2flat([row['latitude'],
                                                                                            row['longitude'],
                                                                                            row['altitude']],
                                                                                           [center_lat, center_lon],
                                                                                           0, -max_altitude)
                                                                                  , axis=1))

    min_x = activity_df.x.min()
    max_x = activity_df.x.max()
    min_y = activity_df.y.min()
    max_y = activity_df.y.max()

    # Magic number play around to get nice result between 1 and 0.01
    precision = 0.1
    number_of_x = (max_x - min_x) * precision
    number_of_y = (max_y - min_y) * precision
    print("create array")
    values = np.zeros(int(number_of_x + 1) * int(number_of_y + 1)).reshape(int(number_of_y + 1), int(number_of_x + 1))

    for i in range(activity_df.seconds.count()):
        print("process second:" + str(i))
        index_y = int(number_of_y / 2) - (int(activity_df.y.iloc[i] * precision) * -1)
        index_x = int(number_of_x / 2) - (int(activity_df.x.iloc[i] * precision) * -1)
        print("x =" + str(activity_df.x.iloc[i]))
        print("y =" + str(activity_df.y.iloc[i]))
        print("z =" + str(activity_df.z.iloc[i]))

        values[index_y][index_x] = activity_df.z.iloc[i] * -1

    print("create data ")
    data = [go.Surface(z=values)]
    layout = go.Layout(
    )
    print("create figure ")
    fig = go.Figure(data)

    print("show ")
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
