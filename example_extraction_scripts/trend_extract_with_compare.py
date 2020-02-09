import threading
from datetime import datetime
import os

start = datetime.now()
store_location = 'D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/'

selected_seasons = GC.season(compare=True)
all_seasons = GC.season(all=True)
one_selected_seasons_metrics = GC.seasonMetrics()

compares_season_metrics = GC.seasonMetrics(compare=True)
durations = [1, 3, 5, 10, 15, 20, 30, 60, 120, 180, 300, 360, 480, 600, 900, 1200, 1800, 2400, 3600, 5400]
compare_peaks_power = []
compare_peaks_wpk = []
for duration in durations:
    compare_peaks_power.append(GC.seasonPeaks(filter='Data contains "P"', series='power', duration=duration, compare=True))
for duration in durations:
    compare_peaks_wpk.append(GC.seasonPeaks(filter='Data contains "P"', series='wpk', duration=duration, compare=True))

print('Collect DATA: {}'.format(datetime.now() - start))


# TODO Create popup what is exported where

def write_selected_seasons():
    f = open(os.path.join(store_location, "trend_compare_seasons.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("selected_seasons = { \n")
    for key in selected_seasons.keys():
        f.writelines("    '" + str(key) + "': " + str(selected_seasons[key]) + ", \n")
    f.writelines("\n }")
    f.close()


def write_all_seasons():
    f = open(os.path.join(store_location, "trend_all_seasons.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("all_seasons = { \n")
    for key in all_seasons.keys():
        f.writelines("    '" + str(key) + "': " + str(all_seasons[key]) + ", \n")
    f.writelines("\n }")
    f.close()


def write_compare_season_metrics():
    f = open(os.path.join(store_location, "trend_compare_seasons_metrics.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("compare_seasons_metrics = [ \n")
    for i in range(len(compares_season_metrics)):
        f.writelines("    (\n")
        for var in compares_season_metrics[i]:
            if isinstance(var, dict):
                f.writelines("        {\n")
                for key in var.keys():
                    f.writelines("            '" + str(key) + "': " + str(var[key]) + ", \n")
                f.writelines("        },\n")
            else:
                f.writelines("        '" + str(var) + "',\n")
        f.writelines("    ),\n")
    f.writelines("]\n")
    f.close()


def write_compare_peaks_power():
    f = open(os.path.join(store_location, "trend_season_compare_peaks_power.py"), "w+")
    f.writelines("import datetime \n")
    for i in range(len(durations)):
        f.writelines("season_peaks_power_" + str(durations[i]) + " = [ \n")
        for serie in compare_peaks_power[i]:
            f.writelines("    (\n")
            for var in serie:
                if isinstance(var, dict):
                   f.writelines("        {\n")
                   for key in var.keys():
                       f.writelines("            '" + str(key) + "': " + str(var[key]) + ", \n")
                   f.writelines("        },\n")
                else:
                    f.writelines("        '" + str(var) + "',\n")
            f.writelines("    ),\n")
        f.writelines("] \n")
    f.close()


def write_compare_peaks_wpk():
    f = open(os.path.join(store_location, "trend_season_compare_peaks_wpk.py"), "w+")
    f.writelines("import datetime \n")
    for i in range(len(durations)):
        f.writelines("season_peaks_wpk_" + str(durations[i]) + " = [ \n")
        for serie in compare_peaks_wpk[i]:
            f.writelines("    (\n")
            for var in serie:
                if isinstance(var, dict):
                   f.writelines("        {\n")
                   for key in var.keys():
                       f.writelines("            '" + str(key) + "': " + str(var[key]) + ", \n")
                   f.writelines("        },\n")
                else:
                    f.writelines("        '" + str(var) + "',\n")
            f.writelines("    ),\n")
        f.writelines("] \n")
    f.close()


def write_one_selected_season_metrics():
    f = open(os.path.join(store_location, "trend_extract_one_selected_season_metrics.py"), "w+")
    f.writelines("import datetime \n")
    f.writelines("one_selected_season_metrics = { \n")
    for key in one_selected_seasons_metrics.keys():
        f.writelines("    '" + str(key) + "': " + str(one_selected_seasons_metrics[key]) + ", \n")

    f.writelines("\n }")
    f.close()


if __name__ == "__main__":
    p = [
        threading.Thread(target=write_selected_seasons, args=()),
        threading.Thread(target=write_all_seasons, args=()),
        threading.Thread(target=write_compare_season_metrics, args=()),
        threading.Thread(target=write_compare_peaks_power, args=()),
        threading.Thread(target=write_compare_peaks_wpk, args=()),
        threading.Thread(target=write_one_selected_season_metrics, args=()),
    ]

    start = datetime.now()
    for i in p:
        i.start()

    for i in p:
        i.join()
    print('Write data: {}'.format(datetime.now() - start))

