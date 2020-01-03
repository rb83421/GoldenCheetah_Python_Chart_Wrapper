# Types from GoldenCheetah
SERIES_SECS = 0
SERIES_CAD = 1
SERIES_CADD = 2
SERIES_HR = 3
SERIES_HRD = 4
SERIES_KM = 5
SERIES_KPH = 6
SERIES_KPHD = 7
SERIES_NM = 8
SERIES_NMD = 9
SERIES_WATTS = 10
SERIES_WATTSD = 11
SERIES_ALT = 12
SERIES_LON = 13
SERIES_LAT = 14
SERIES_HEADWIND = 15
SERIES_SLOPE = 16
SERIES_TEMP = 17
SERIES_INTERVAL = 18
SERIES_NP = 19
SERIES_XPOWER = 20
SERIES_VAM = 21
SERIES_WATTSKG = 22
SERIES_LRBALANCE = 23
SERIES_LTE = 24
SERIES_RTE = 25
SERIES_LPS = 26
SERIES_RPS = 27
SERIES_APOWER = 28
SERIES_WPRIME = 29
SERIES_ATISS = 30
SERIES_ANTISS = 31
SERIES_SMO2 = 32
SERIES_THB = 33
SERIES_RVERT = 34
SERIES_RCAD = 35
SERIES_RCONTACT = 36
SERIES_GEAR = 37
SERIES_O2HB = 38
SERIES_HHB = 39
SERIES_RPCO = 40
SERIES_LPPB = 41
SERIES_RPPB = 42
SERIES_LPPE = 43
SERIES_RPPE = 44
SERIES_LPPPB = 45
SERIES_RPPPB = 46
SERIES_LPPPE = 47
SERIES_RPPPE = 48
SERIES_WBAL = 49
SERIES_TCORE = 50
SERIES_CLENGTH = 51
SERIES_APOWERKG = 52
SERIES_INDEX = 53
SERIES_HRV = 54

def version():  # to get a version string
    # Not implemented yet
    return None


def build():  # to get a build number
    # Not implemented yet
    return None


def webpage(filename):  # to set the webpage
    import webbrowser
    new = 2  # open in a new tab, if possible
    webbrowser.open(filename, new=new)


# Athlete
def athlete():  # to get the athlete details
    # Not implemented yet
    return None


def athleteZones(date=0, sport=""):  # to get zone config
    from GC_DATA import athlete_current_zones
    return athlete_current_zones.current_zones


# Activity
def activities(filter=""):  # to get a list of activities (as dates): #
    # Not implemented yet
    return None

def activity(activity=None):  # to get the activity data
    from GC_DATA import activity_xxx_data
    return activity_xxx_data.activity_xxx


def series(type, activity=None):  # to get an individual series data
    from GC_DATA import activity_xxx_series
    if type == SERIES_HR:
        return activity_xxx_series.HR
    elif type == SERIES_WATTS:
        return activity_xxx_series.WATTS
    elif type == SERIES_SECS:
        return activity_xxx_series.SECS
    else:
        raise Exception('NOT YET Implemented in GC wrapper' + str(type))
    # Not implemented yet
    return None

def activityWbal(activity=None):  # to get wbal series data    #Not implemented yet
    # Not implemented yet
    return None


def xdataNames(name="", activity=None):  # to get activity xdata series names
    # Not implemented yet
    return None


def xdataSeries(name, series, activity=None):  # to get activity xdata series in its own sampling interval
    # Not implemented yet
    return None


def xdata(name, series, join="repeat", activity=None):  # to get interpolated activity xdata series
    # Not implemented yet
    return None


def activityMetrics(compare=False):  # to get the activity metrics and metadata
    from GC_DATA import activity_xxx_metrics
    return activity_xxx_metrics.activityMetrics

def activityMeanmax(compare=False):  # to get mean maximals for all activity data
    # Not implemented yet
    return None


def activityIntervals(type="", activity=None):  # to get information about activity intervals
    from GC_DATA import activity_xxx_intervals
    return activity_xxx_intervals.activity_intervals


# Trends
def season(all=False, compare=False):  # to get season details
    # Not implemented yet
    return None


def seasonMetrics(all=False, filter="", compare=False):  # to get season metrics
    from GC_DATA import trend_all_season_metrics
    return trend_all_season_metrics.all_season_metrics


def seasonMeanmax(all=False, filter="", compare=False):  # to get best mean maximals for a season
    # Not implemented yet
    return None


def seasonPeaks(all=False, filter="", compare=False, series="wpk",
                duration=5):  # to get activity peaks for a given series and duration
    # Not implemented yet
    return None


def seasonPmc(all=False, metric="TSS"):  # to get PMC data for any given metric
    from GC_DATA import trend_all_tss_pmc
    if metric == "TSS" or metric == "BikeStress":
        return trend_all_tss_pmc.all_tss_pmc

    # Rest Not implemented yet
    return None


def seasonIntervals(type="", compare=False):  # to get metrics for all intervals
    # Not implemented yet
    return None


def seasonMeasures(all=False, group="Body"):  # to get Daily measures (Body and Hrv available for v3.5): #
    # Not implemented yet
    return None
