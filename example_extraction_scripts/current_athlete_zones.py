activity_metric = GC.activityMetrics()
zone = GC.athleteZones(date=activity_metric["date"], sport="bike")
f = open('D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/athlete_current_zones.py', "w+")
f.writelines("import datetime \n")
f.writelines("current_zones = { \n" )
for key in zone.keys():
  f.writelines("    '" + str(key) + "': " + str(zone[key]) + ", \n")
f.writelines("\n }")
f.close()