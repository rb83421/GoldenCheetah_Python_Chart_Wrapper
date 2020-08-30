from GC_DATA import athlete_data
from GC_DATA import trend_season_mean_max_all
from GC_DATA import athlete_single_extract_current_zones
from GC_DATA import activity_single_extract_metrics
from GC_DATA import activity_single_extract_series
from GC_DATA import activity_single_extract_data
from GC_DATA import activity_single_extract_intervals
from GC_DATA import activity_list
from GC_DATA import activity_single_xdata_names
from GC_DATA import activity_single_extract_xdata_series_names
from GC_DATA import activity_single_extract_xdata_series
from GC_DATA import trend_single_extract_all_season_metrics
from GC_DATA import trend_single_extract_all_tss_pmc
from GC_DATA import trend_season_peaks_power
from GC_DATA import trend_season_peaks_wpk

from GC_DATA import trend_season_compare_peaks_power
from GC_DATA import trend_season_compare_peaks_wpk

from GC_DATA import trend_compare_seasons
from GC_DATA import trend_all_seasons
from GC_DATA import trend_compare_seasons_metrics
from GC_DATA import trend_extract_one_selected_season_metrics

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
    return athlete_data.athlete_data


def athleteZones(date=0, sport=""):  # to get zone config
    return athlete_single_extract_current_zones.current_zones


# Activity
def activities(filter=""):  # to get a list of activities (as dates): #
    return activity_list.activity_list


def activity(activity=None):  # to get the activities data
    if activity:
        print("Currently only giving back one activities")
    return activity_single_extract_data.activity_data


def series(type, activity=None):  # to get an individual series data
    if type == SERIES_HR:
        return activity_single_extract_series.SERIES_HR
    elif type == SERIES_WATTS:
        return activity_single_extract_series.SERIES_WATTS
    elif type == SERIES_SECS:
        return activity_single_extract_series.SERIES_SECS
    elif type == SERIES_LAT:
        return activity_single_extract_series.SERIES_LAT
    elif type == SERIES_LON:
        return activity_single_extract_series.SERIES_LON

    else:
        raise Exception('NOT YET Implemented in GC wrapper' + str(type))
    # Not implemented yet
    return None


def activityWbal(activity=None):  # to get wbal series data    #Not implemented yet
    # Not implemented yet
    return None


def xdataNames(name="", activity=None):  # to get activities xdata series names
    if name:
        return activity_single_extract_xdata_series_names.xdata_series_names[name]
    else:
        return activity_single_xdata_names.xdata_names


def xdataSeries(name, series, activity=None):  # to get activities xdata series in its own sampling interval
    return activity_single_extract_xdata_series.xdata_serie[name][series]


def xdata(name, series, join="repeat", activity=None):  # to get interpolated activities xdata series
    # Not implemented yet
    return None


def activityMetrics(compare=False):  # to get the activities metrics and metadata
    return activity_single_extract_metrics.activity_metrics


def activityMeanmax(compare=False):  # to get mean maximals for all activities data
    # Not implemented yet
    return None


def activityIntervals(type="", activity=None):  # to get information about activities intervals
    return activity_single_extract_intervals.activity_intervals


# Trends
def season(all=False, compare=False):  # to get season details
    if all and not compare:
        return trend_all_seasons.all_seasons
    if compare:
        return trend_compare_seasons.selected_seasons


def seasonMetrics(all=False, filter="", compare=False):  # to get season metrics
    if not compare and all:
        return trend_single_extract_all_season_metrics.all_season_metrics
    elif not compare and not all:
        return trend_extract_one_selected_season_metrics.one_selected_season_metrics
    else:
        return trend_compare_seasons_metrics.compare_seasons_metrics


def seasonMeanmax(all=False, filter="", compare=False):  # to get best mean maximals for a season
    return trend_season_mean_max_all.season_mean_max_all


def seasonPeaks(all=False, filter="", compare=False, series="wpk", duration=5):  # to get activities peaks for a given series and duration
    if not compare and series == "wpk":
        peak_duration = {1: trend_season_peaks_wpk.season_peaks_wpk_1,
                         3: trend_season_peaks_wpk.season_peaks_wpk_3,
                         5: trend_season_peaks_wpk.season_peaks_wpk_5,
                         10: trend_season_peaks_wpk.season_peaks_wpk_10,
                         15: trend_season_peaks_wpk.season_peaks_wpk_15,
                         20: trend_season_peaks_wpk.season_peaks_wpk_20,
                         30: trend_season_peaks_wpk.season_peaks_wpk_30,
                         60: trend_season_peaks_wpk.season_peaks_wpk_60,
                         120: trend_season_peaks_wpk.season_peaks_wpk_120,
                         180: trend_season_peaks_wpk.season_peaks_wpk_180,
                         300: trend_season_peaks_wpk.season_peaks_wpk_300,
                         360: trend_season_peaks_wpk.season_peaks_wpk_360,
                         480: trend_season_peaks_wpk.season_peaks_wpk_480,
                         600: trend_season_peaks_wpk.season_peaks_wpk_600,
                         900: trend_season_peaks_wpk.season_peaks_wpk_900,
                         1200: trend_season_peaks_wpk.season_peaks_wpk_1200,
                         1800: trend_season_peaks_wpk.season_peaks_wpk_1800,
                         2400: trend_season_peaks_wpk.season_peaks_wpk_2400,
                         3600: trend_season_peaks_wpk.season_peaks_wpk_3600,
                         5400: trend_season_peaks_wpk.season_peaks_wpk_5400
                         }
        return peak_duration.get(duration, "Invalid duration (wpk)")
    elif not compare and series == "power":
        peak_duration = {1: trend_season_peaks_power.season_peaks_power_1,
                         3: trend_season_peaks_power.season_peaks_power_3,
                         5: trend_season_peaks_power.season_peaks_power_5,
                         10: trend_season_peaks_power.season_peaks_power_10,
                         15: trend_season_peaks_power.season_peaks_power_15,
                         20: trend_season_peaks_power.season_peaks_power_20,
                         30: trend_season_peaks_power.season_peaks_power_30,
                         60: trend_season_peaks_power.season_peaks_power_60,
                         120: trend_season_peaks_power.season_peaks_power_120,
                         180: trend_season_peaks_power.season_peaks_power_180,
                         300: trend_season_peaks_power.season_peaks_power_300,
                         360: trend_season_peaks_power.season_peaks_power_360,
                         480: trend_season_peaks_power.season_peaks_power_480,
                         600: trend_season_peaks_power.season_peaks_power_600,
                         900: trend_season_peaks_power.season_peaks_power_900,
                         1200: trend_season_peaks_power.season_peaks_power_1200,
                         1800: trend_season_peaks_power.season_peaks_power_1800,
                         2400: trend_season_peaks_power.season_peaks_power_2400,
                         3600: trend_season_peaks_power.season_peaks_power_3600,
                         5400: trend_season_peaks_power.season_peaks_power_5400
                         }
        return peak_duration.get(duration, "Invalid duration (power)")
    elif compare and series == "wpk":
            peak_duration = {1: trend_season_compare_peaks_wpk.season_peaks_wpk_1,
                             3: trend_season_compare_peaks_wpk.season_peaks_wpk_3,
                             5: trend_season_compare_peaks_wpk.season_peaks_wpk_5,
                             10: trend_season_compare_peaks_wpk.season_peaks_wpk_10,
                             15: trend_season_compare_peaks_wpk.season_peaks_wpk_15,
                             20: trend_season_compare_peaks_wpk.season_peaks_wpk_20,
                             30: trend_season_compare_peaks_wpk.season_peaks_wpk_30,
                             60: trend_season_compare_peaks_wpk.season_peaks_wpk_60,
                             120: trend_season_compare_peaks_wpk.season_peaks_wpk_120,
                             180: trend_season_compare_peaks_wpk.season_peaks_wpk_180,
                             300: trend_season_compare_peaks_wpk.season_peaks_wpk_300,
                             360: trend_season_compare_peaks_wpk.season_peaks_wpk_360,
                             480: trend_season_compare_peaks_wpk.season_peaks_wpk_480,
                             600: trend_season_compare_peaks_wpk.season_peaks_wpk_600,
                             900: trend_season_compare_peaks_wpk.season_peaks_wpk_900,
                             1200: trend_season_compare_peaks_wpk.season_peaks_wpk_1200,
                             1800: trend_season_compare_peaks_wpk.season_peaks_wpk_1800,
                             2400: trend_season_compare_peaks_wpk.season_peaks_wpk_2400,
                             3600: trend_season_compare_peaks_wpk.season_peaks_wpk_3600,
                             5400: trend_season_compare_peaks_wpk.season_peaks_wpk_5400
                             }
            return peak_duration.get(duration, "Invalid duration (wpk)")
    elif compare and series == "power":
        peak_duration = {1: trend_season_compare_peaks_power.season_peaks_power_1,
                         3: trend_season_compare_peaks_power.season_peaks_power_3,
                         5: trend_season_compare_peaks_power.season_peaks_power_5,
                         10: trend_season_compare_peaks_power.season_peaks_power_10,
                         15: trend_season_compare_peaks_power.season_peaks_power_15,
                         20: trend_season_compare_peaks_power.season_peaks_power_20,
                         30: trend_season_compare_peaks_power.season_peaks_power_30,
                         60: trend_season_compare_peaks_power.season_peaks_power_60,
                         120: trend_season_compare_peaks_power.season_peaks_power_120,
                         180: trend_season_compare_peaks_power.season_peaks_power_180,
                         300: trend_season_compare_peaks_power.season_peaks_power_300,
                         360: trend_season_compare_peaks_power.season_peaks_power_360,
                         480: trend_season_compare_peaks_power.season_peaks_power_480,
                         600: trend_season_compare_peaks_power.season_peaks_power_600,
                         900: trend_season_compare_peaks_power.season_peaks_power_900,
                         1200: trend_season_compare_peaks_power.season_peaks_power_1200,
                         1800: trend_season_compare_peaks_power.season_peaks_power_1800,
                         2400: trend_season_compare_peaks_power.season_peaks_power_2400,
                         3600: trend_season_compare_peaks_power.season_peaks_power_3600,
                         5400: trend_season_compare_peaks_power.season_peaks_power_5400
                         }
        return peak_duration.get(duration, "Invalid duration (power)")
    else:
        raise Exception('NOT YET Implemented in GC wrapper' + str(type))


def seasonPmc(all=False, metric="TSS"):  # to get PMC data for any given metric
    if metric == "TSS" or metric == "BikeStress":
        return trend_single_extract_all_tss_pmc.all_tss_pmc

    # Rest Not implemented yet
    return None


def seasonIntervals(type="", compare=False):  # to get metrics for all intervals
    # Not implemented yet
    return None


def seasonMeasures(all=False, group="Body"):  # to get Daily measures (Body and Hrv available for v3.5): #
    # this can only be turned on when the extract also contains body measurement file: athlete body data

    # import GC_DATA.athlete_body_data
    # if all and group == "Body":
    #     return athlete_data.athlete_data

    return None
