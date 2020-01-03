season_metrics = GC.seasonMetrics(all=True)
f = open('D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/trend_all_season_metrics.py', "w+")
f.writelines("import datetime \n")
f.writelines("all_season_metrics = { \n" )
for key in season_metrics.keys():
  f.writelines("    '" + str(key) + "': " + str(season_metrics[key]) + ", \n")
f.writelines("\n }")

f.close()
