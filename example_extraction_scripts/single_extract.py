import multiprocessing
import threading
from datetime import datetime
import os

start = datetime.now()
store_location = 'D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/'
activity = GC.activity()
activity_intervals = GC.activityIntervals()
activity_metrics = GC.activityMetrics()
zone = GC.athleteZones(date=activity_metrics["date"], sport="bike")
season_metrics = GC.seasonMetrics(all=True)
pmc = GC.seasonPmc(all=True, metric="BikeStress")
season_mean_max = GC.seasonMeanmax(all=True)
durations = [1, 5, 10, 15, 20, 30, 60, 120, 180, 300, 480, 600, 1200, 1800, 3600, 5400]
peaks_power = []
peaks_wpk = []
for duration in durations:
    peaks_power.append(GC.seasonPeaks(all=True, filter='Data contains "P"', series='power', duration=duration))
for duration in durations:
    peaks_wpk.append(GC.seasonPeaks(all=True, filter='Data contains "P"', series='wpk', duration=duration))

print('Collect DATA: {}'.format(datetime.now() - start))


# TODO Create popup what is exported where

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
    for gc_serie in dir(GC):
        if gc_serie.startswith("SERIES"):
            f.writelines(gc_serie + " = " + str(list(GC.series(getattr(GC, gc_serie)))) + "\n")
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
        if key != "Workout_Title":
            f.writelines("    '" + str(key) + "': " + str(season_metrics[key]) + ", \n")
        else:
            f.writelines("    '" + str(key) + "': " + str([x.encode('utf-8') for x in season_metrics[key]]) + ", \n")

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


if __name__ == "__main__":
    p = [
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
    ]

    start = datetime.now()
    for i in p:
        i.start()

    for i in p:
        i.join()
    print('Write data: {}'.format(datetime.now() - start))
