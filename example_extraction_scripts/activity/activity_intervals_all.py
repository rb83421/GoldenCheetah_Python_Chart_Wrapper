activity_intervals = GC.activityIntervals()
f = open('D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/activity_xxx_intervals.py', "w+")
f.writelines("activity_intervals = { \n" )
for key in activity_intervals.keys():
  f.writelines("    '" + str(key) + "': " + str(activity_intervals[key]) + ", \n")
f.writelines("\n }")

f.close()
