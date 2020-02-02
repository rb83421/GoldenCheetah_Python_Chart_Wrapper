# Types from GoldenCheetah
from GC_DATA import gc_series_enum as GC_E

SERIES_SECS = GC_E.SERIES_SECS
SERIES_CAD = GC_E.SERIES_CAD
SERIES_CADD = GC_E.SERIES_CADD
SERIES_HR = GC_E.SERIES_HR
SERIES_HRD = GC_E.SERIES_HRD
SERIES_KM = GC_E.SERIES_KM
SERIES_KPH = GC_E.SERIES_KPH
SERIES_KPHD = GC_E.SERIES_KPHD
SERIES_NM = GC_E.SERIES_NM
SERIES_NMD = GC_E.SERIES_NMD
SERIES_WATTS = GC_E.SERIES_WATTS
SERIES_WATTSD = GC_E.SERIES_WATTSD
SERIES_ALT = GC_E.SERIES_ALT
SERIES_LON = GC_E.SERIES_LON
SERIES_LAT = GC_E.SERIES_LAT
SERIES_HEADWIND = GC_E.SERIES_HEADWIND
SERIES_SLOPE = GC_E.SERIES_SLOPE
SERIES_TEMP = GC_E.SERIES_TEMP
SERIES_INTERVAL = GC_E.SERIES_INTERVAL
SERIES_NP = GC_E.SERIES_NP
SERIES_XPOWER = GC_E.SERIES_XPOWER
SERIES_VAM = GC_E.SERIES_VAM
SERIES_WATTSKG = GC_E.SERIES_WATTSKG
SERIES_LRBALANCE = GC_E.SERIES_LRBALANCE
SERIES_LTE = GC_E.SERIES_LTE
SERIES_RTE = GC_E.SERIES_RTE
SERIES_LPS = GC_E.SERIES_LPS
SERIES_RPS = GC_E.SERIES_RPS
SERIES_APOWER = GC_E.SERIES_APOWER
SERIES_WPRIME = GC_E.SERIES_WPRIME
SERIES_ATISS = GC_E.SERIES_ATISS
SERIES_ANTISS = GC_E.SERIES_ANTISS
SERIES_SMO2 = GC_E.SERIES_SMO2
SERIES_THB = GC_E.SERIES_THB
SERIES_RVERT = GC_E.SERIES_RVERT
SERIES_RCAD = GC_E.SERIES_RCAD
SERIES_RCONTACT = GC_E.SERIES_RCONTACT
SERIES_GEAR = GC_E.SERIES_GEAR
SERIES_O2HB = GC_E.SERIES_O2HB
SERIES_HHB = GC_E.SERIES_HHB
SERIES_RPCO = GC_E.SERIES_RPCO
SERIES_LPPB = GC_E.SERIES_LPPB
SERIES_RPPB = GC_E.SERIES_RPPB
SERIES_LPPE = GC_E.SERIES_LPPE
SERIES_RPPE = GC_E.SERIES_RPPE
SERIES_LPPPB = GC_E.SERIES_LPPPB
SERIES_RPPPB = GC_E.SERIES_RPPPB
SERIES_LPPPE = GC_E.SERIES_LPPPE
SERIES_RPPPE = GC_E.SERIES_RPPPE
SERIES_WBAL = GC_E.SERIES_WBAL
SERIES_TCORE = GC_E.SERIES_TCORE
SERIES_CLENGTH = GC_E.SERIES_CLENGTH
SERIES_APOWERKG = GC_E.SERIES_APOWERKG
SERIES_INDEX = GC_E.SERIES_INDEX
SERIES_HRV = GC_E.SERIES_HRV

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
    from GC_DATA import athlete_single_ectract_current_zones
    return athlete_single_ectract_current_zones.current_zones


# Activity
def activities(filter=""):  # to get a list of activities (as dates): #
    # Not implemented yet
    return None

def activity(activity=None):  # to get the activity data
    from GC_DATA import activity_single_extract_data
    return activity_single_extract_data.activity_data


def series(type, activity=None):  # to get an individual series data
    from GC_DATA import activity_single_extract_series
    if type == SERIES_HR:
        return activity_single_extract_series.HR
    elif type == SERIES_WATTS:
        return activity_single_extract_series.WATTS
    elif type == SERIES_SECS:
        return activity_single_extract_series.SECS
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
    from GC_DATA import activity_single_extract_metrics
    return activity_single_extract_metrics.activity_metrics

def activityMeanmax(compare=False):  # to get mean maximals for all activity data
    # Not implemented yet
    return None


def activityIntervals(type="", activity=None):  # to get information about activity intervals
    from GC_DATA import activity_single_extract_intervals
    return activity_single_extract_intervals.activity_intervals


# Trends
def season(all=False, compare=False):  # to get season details
    # Not implemented yet
    return None


def seasonMetrics(all=False, filter="", compare=False):  # to get season metrics
    from GC_DATA import trend_single_extract_all_season_metrics
    return trend_single_extract_all_season_metrics.all_season_metrics


def seasonMeanmax(all=False, filter="", compare=False):  # to get best mean maximals for a season
    # Not implemented yet
    return None


def seasonPeaks(all=False, filter="", compare=False, series="wpk",
                duration=5):  # to get activity peaks for a given series and duration
    # Not implemented yet
    return None


def seasonPmc(all=False, metric="TSS"):  # to get PMC data for any given metric
    from GC_DATA import trend_single_extract_all_tss_pmc
    if metric == "TSS" or metric == "BikeStress":
        return trend_single_extract_all_tss_pmc.all_tss_pmc

    # Rest Not implemented yet
    return None


def seasonIntervals(type="", compare=False):  # to get metrics for all intervals
    # Not implemented yet
    return None


def seasonMeasures(all=False, group="Body"):  # to get Daily measures (Body and Hrv available for v3.5): #
    # Not implemented yet
    return None
