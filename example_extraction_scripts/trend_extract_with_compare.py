import threading
from datetime import datetime
import os

start = datetime.now()
store_location = 'D:/git-repos/GoldenCheetah_Python_Chart_Wrapper/GC_DATA/'

selected_seasons = GC.season(compare=True)
all_seasons = GC.season(all=True)
compares_season_metrics = GC.seasonMetrics(compare=True)

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
                    if key != "Workout_Title":
                        f.writelines("            '" + str(key) + "': " + str(var[key]) + ", \n")
                    else:
                        f.writelines(
                            "            '" + str(key) + "': " + str([x.encode('utf-8') for x in var[key]]) + ", \n")
                f.writelines("        },\n")
            else:
                f.writelines("        '" + str(var) + "',\n")
        f.writelines("    ),\n")
    f.close()


if __name__ == "__main__":
    p = [
        threading.Thread(target=write_selected_seasons, args=()),
        threading.Thread(target=write_all_seasons(), args=()),
    ]

    start = datetime.now()
    for i in p:
        i.start()

    for i in p:
        i.join()
    print('Write data: {}'.format(datetime.now() - start))

