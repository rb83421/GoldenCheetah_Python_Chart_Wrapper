import os

store_location = 'D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/'
activity = GC.activity()
activity_intervals = GC.activityIntervals()
activity_metrics = GC.activityMetrics()
zone = GC.athleteZones(date=activity_metrics["date"], sport="bike")
season_metrics = GC.seasonMetrics(all=True)
pmc = GC.seasonPmc(all=True, metric="BikeStress")

# TODO Create popup what is exported where

f = open(os.path.join(store_location, "activity_single_extract_data.py"), "w+")
f.writelines("nan=0 \n")
f.writelines("activity_data = { \n")
for key in activity.keys():
  f.writelines("    '" + str(key) + "': " + str(list(activity[key])) + ", \n")
f.writelines("\n }")
f.close()


f = open(os.path.join(store_location, "activity_single_extract_intervals.py"), "w+")
f.writelines("activity_intervals = { \n")
for key in activity_intervals.keys():
  f.writelines("    '" + str(key) + "': " + str(activity_intervals[key]) + ", \n")
f.writelines("\n }")
f.close()

f = open(os.path.join(store_location, "activity_single_extract_metrics.py"), "w+")
f.writelines("import datetime \n")
f.writelines("activity_metrics = ")
f.writelines(str(activity_metrics))
f.close()

f = open(os.path.join(store_location, "gc_series_enum.py"), "w+")
for gc_serie in dir(GC):
    if gc_serie.startswith("SERIES"):
        f.writelines(gc_serie + " = " + str(getattr(GC, gc_serie))+ "\n")
f.close()

f = open(os.path.join(store_location, "activity_single_extract_series.py"), "w+")
for gc_serie in dir(GC):
    if gc_serie.startswith("SERIES"):
        f.writelines(gc_serie + " = " + str(list(GC.series(getattr(GC, gc_serie)))) + "\n")
f.close()


f = open(os.path.join(store_location, "athlete_single_ectract_current_zones.py"), "w+")
f.writelines("import datetime \n")
f.writelines("current_zones = { \n" )
for key in zone.keys():
    f.writelines("    '" + str(key) + "': " + str(zone[key]) + ", \n")
f.writelines("\n }")
f.close()

f = open(os.path.join(store_location, "trend_single_extract_all_season_metrics.py"), "w+")
f.writelines("import datetime \n")
f.writelines("all_season_metrics = { \n" )
for key in season_metrics.keys():
    if key != "Workout_Title":
        f.writelines("    '" + str(key) + "': " + str(season_metrics[key]) + ", \n")
    else:
        f.writelines("    '" + str(key) + "': " + str([x.encode('utf-8') for x in season_metrics[key]]) + ", \n")

f.writelines("\n }")
f.close()

f = open(os.path.join(store_location, "trend_single_extract_all_tss_pmc.py"), "w+")
f.writelines("import datetime \n")
f.writelines("all_tss_pmc = ")
f.writelines(str(pmc))
f.close()

