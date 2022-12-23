import threading
from datetime import datetime
import os

start = datetime.now()
store_location = 'C:/Users/r_boe/PycharmProjects/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/'
athlete = GC.athlete()
try:
    athlete_body = GC.seasonMeasures(all=True, group="Body")
    athlete_body_found = True
except SystemError:
    print("No body measurement found create empty file")
    athlete_body_found = False
activity = GC.activity()
activity_list = GC.activities( filter='Data contains "P" and Data contains "H"')
activity_intervals = GC.activityIntervals()
activity_metrics = GC.activityMetrics()
activity_xdata_names = GC.xdataNames()
zone = GC.athleteZones(date=activity_metrics["date"], sport="Bike")
season_metrics = GC.seasonMetrics(all=True)
pmc = GC.seasonPmc(all=True, metric="BikeStress")
season_mean_max = GC.seasonMeanmax(all=True)
durations = [1, 3, 5, 10, 15, 20, 30, 60, 120, 180, 300, 360, 480, 600, 900, 1200, 1800, 2400, 3600, 5400]

peaks_power = []
peaks_wpk = []
for duration in durations:
    peaks_power.append(GC.seasonPeaks(all=True, filter='Data contains "P"', series='power', duration=duration))
for duration in durations:
    peaks_wpk.append(GC.seasonPeaks(all=True, filter='Data contains "P"', series='wpk', duration=duration))

gc_series = {}
for gc_serie in dir(GC):
    if gc_serie.startswith("SERIES"):
        gc_series[gc_serie] = list(GC.series(getattr(GC, gc_serie)))

activity_xdata_series_names = {}
for name in activity_xdata_names:
    activity_xdata_series_names[name] = list(GC.xdataNames(name))

activity_xdata_series = {}
for name in activity_xdata_series_names:
    activity_xdata_series[name] = {}
    for serie in activity_xdata_series_names[name]:
        activity_xdata_series[name][serie] = list(GC.xdataSeries(name, serie))

print('Collect DATA: {}'.format(datetime.now() - start))


# TODO Create popup what is exported where

def write_athlete_data():
    f = open(os.path.join(store_location, "athlete_data.py"), "w+")
    f.writelines("import datetime\n")
    f.writelines("athlete_data = " + str(athlete))
    f.close()


def write_athlete_body(athlete_body_measurement=False):
    f = open(os.path.join(store_location, "athlete_body_data.py"), "w+")
    f.writelines("import datetime\n")
    if athlete_body_measurement:
        f.writelines("athlete_body_data = { ")
        for key in athlete_body.keys():
            f.writelines("    '" + str(key) + "': " + str(athlete_body[key]) + ", \n")
        f.writelines("\n }")
    else:
        f.writelines("athlete_body_data = None \n")
    f.close()


def write_activity_list():
    f = open(os.path.join(store_location, "activity_list.py"), "w+")
    f.writelines("import datetime\n")
    f.writelines("activity_list = " + str(activity_list))
    f.close()


def write_activity_data():
    f = open(os.path.join(store_location, "activity_single_extract_data.py"), "w+")
    f.writelines("nan=0 \n")
    f.writelines("activity_data = { \n")
    for key in activity.keys():
        f.writelines("    '" + str(key) + "': " + str(list(activity[key])) + ", \n")
    f.writelines("\n }")
    f.close()


def write_activity_intervals():
    f = open(os.path.join(store_location, "activity_single_extract_intervals.py"), "w+")
    f.writelines("activity_intervals = { \n")
    for key in activity_intervals.keys():
        f.writelines("    '" + str(key) + "': " + str(activity_intervals[key]) + ", \n")
    f.writelines("\n }")
    f.close()


def write_activity_metrics():
    f = open(os.path.join(store_location, "activity_single_extract_metrics.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("activity_metrics = ")
    f.writelines(str(activity_metrics))
    f.close()


def write_gc_enums():
    f = open(os.path.join(store_location, "gc_series_enum.py"), "w+")
    for gc_serie in dir(GC):
        if gc_serie.startswith("SERIES"):
            f.writelines(gc_serie + " = " + str(getattr(GC, gc_serie)) + "\n")
    f.close()


def write_gc_series():
    f = open(os.path.join(store_location, "activity_single_extract_series.py"), "w+")
    for key in gc_series.keys():
        f.writelines(str(key) + " = " + str(gc_series[key]) + "\n")
    f.close()


def write_athlete_zones():
    f = open(os.path.join(store_location, "athlete_single_extract_current_zones.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("current_zones = { \n")
    for key in zone.keys():
        f.writelines("    '" + str(key) + "': " + str(zone[key]) + ", \n")
    f.writelines("\n }")
    f.close()


def write_all_season_metrics():
    f = open(os.path.join(store_location, "trend_single_extract_all_season_metrics.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("all_season_metrics = { \n")
    for key in season_metrics.keys():
        f.writelines("    '" + str(key) + "': " + str(season_metrics[key]) + ", \n")

    f.writelines("\n }")
    f.close()


def write_all_tss_pmc():
    f = open(os.path.join(store_location, "trend_single_extract_all_tss_pmc.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("all_tss_pmc = ")
    f.writelines(str(pmc))
    f.close()


def write_season_max_all():
    f = open(os.path.join(store_location, "trend_season_mean_max_all.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("season_mean_max_all = { \n")
    for key in season_mean_max.keys():
        f.writelines("    '" + str(key) + "': " + str(season_mean_max[key]) + ", \n")
    f.writelines("\n }")
    f.close()


def write_peaks_power():
    f = open(os.path.join(store_location, "trend_season_peaks_power.py"), "w+")
    f.writelines("import datetime \n")
    for i in range(len(durations)):
        f.writelines("season_peaks_power_" + str(durations[i]) + " = { \n")
        for key in peaks_power[i].keys():
            f.writelines("    '" + str(key) + "': " + str(peaks_power[i][key]) + ", \n")
        f.writelines("}\n")
    f.close()


def write_peaks_wpk():
    f = open(os.path.join(store_location, "trend_season_peaks_wpk.py"), "w+")
    f.writelines("import datetime \n")
    for i in range(len(durations)):
        f.writelines("season_peaks_wpk_" + str(durations[i]) + " = { \n")
        for key in peaks_wpk[i].keys():
            f.writelines("    '" + str(key) + "': " + str(peaks_wpk[i][key]) + ", \n")
        f.writelines("}\n")
    f.close()


def write_xdata_names():
    f = open(os.path.join(store_location, "activity_single_xdata_names.py"), "w+")
    f.writelines("xdata_names = " + str(activity_xdata_names))
    f.close()


def write_xdata_series_names():
    f = open(os.path.join(store_location, "activity_single_extract_xdata_series_names.py"), "w+")
    f.writelines("xdata_series_names = { \n")
    for key in activity_xdata_series_names.keys():
        f.writelines("    '" + str(key) + "': " + str(activity_xdata_series_names[key]) + ", \n")
    f.writelines("}\n")
    f.close()


def write_xdata_series():
    f = open(os.path.join(store_location, "activity_single_extract_xdata_series.py"), "w+")
    # No formatting done yet
    f.writelines("xdata_serie =" + str(activity_xdata_series))
    f.close()


if __name__ == "__main__":
    p = [
        threading.Thread(target=write_athlete_body, args=[athlete_body_found]),
        threading.Thread(target=write_athlete_data, args=()),
        threading.Thread(target=write_activity_list, args=()),
        threading.Thread(target=write_activity_data, args=()),
        threading.Thread(target=write_activity_intervals, args=()),
        threading.Thread(target=write_activity_metrics, args=()),
        threading.Thread(target=write_gc_enums, args=()),
        threading.Thread(target=write_gc_series, args=()),
        threading.Thread(target=write_athlete_zones, args=()),
        threading.Thread(target=write_all_season_metrics, args=()),
        threading.Thread(target=write_all_tss_pmc, args=()),
        threading.Thread(target=write_season_max_all, args=()),
        threading.Thread(target=write_peaks_power, args=()),
        threading.Thread(target=write_peaks_wpk, args=()),
        threading.Thread(target=write_xdata_names, args=()),
        threading.Thread(target=write_xdata_series_names, args=()),
        threading.Thread(target=write_xdata_series, args=()),
    ]

    start = datetime.now()
    for i in p:
        i.start()

    for i in p:
        i.join()

    print('Write data: {}'.format(datetime.now() - start))
