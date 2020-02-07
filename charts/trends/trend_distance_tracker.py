# Tracking Custom field within a period V2 (Py)
#
# For Tracking custom fields within a certain period.
# I use it to monitor how many km i have ridden on a tyre or how many hours the battery of my equipment last.
#
# NOTE:
# Before using this chart update it for your filters and items:
# Update the filters (e.g. create a filter for Bike 1 or Bike 2)
# Update tracking items (e.g. Tyre 1 within period january to august for bike 1)
# For problems/question/suggestions post on https://groups.google.com/forum/#!forum/golden-cheetah-users
#
# V1 - Initial Chart
# V2 - 2019-10-29 - Make linux compatible
from GC_Wrapper import GC_wrapper as GC
import pathlib
import numpy as np
from datetime import datetime
import tempfile
# from _plotly_future_ import v4_subplots
from plotly.subplots import make_subplots
import plotly
import plotly.graph_objs as go
import pandas as pd

# Globals
filters = {}
tracked_items = {}
# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Define GC background color
gc_bg_color = 'rgb(52,52,52)'
# Define GC Text color
gc_text_color = 'rgb(255,255,255)'


def main():
    define_filter(name="Bike 1",
                  gc_filter='Sport = "Bike" and SubSport <> "VirtualRide" and Bike_Rental = 0',
                  color='Blue')
    define_filter(name="Bike 2",
                  gc_filter='Sport = "Bike" and Bike_Rental = 1',
                  color='Red')

    # Add season metrics for defined filters
    get_filtered_rides()

    # Define what to track (distance and duration)
    add_tracking_item(name="Dummy Tyre Bike 1",
                      filter_name="Bike 1",
                      tracking_start_date="2018-05-16",
                      tracking_stop_date="2019-02-22",
                      tracking_field='Distance',
                      notes="Replaced after large puncture")

    # Minimum field mandatory
    add_tracking_item(name="Dummy Tyre 2 Bike 1",
                      filter_name="Bike 1",
                      tracking_start_date="2019-02-22",
                      )

    add_tracking_item(name="Dummy Test ",
                      filter_name="Bike 2",
                      tracking_start_date="2019-02-15",
                      tracking_field='Duration')

    add_tracking_item(name="Dummy Test 1",
                      filter_name="Bike 2",
                      tracking_start_date="2019-02-15",
                      tracking_field='Calories')

    panda_dict = processData()
    plot(panda_dict)


def define_filter(name, gc_filter, color):
    filters[name] = {'filter': gc_filter,
                     'color': color,
                     }


def add_tracking_item(name, filter_name, tracking_start_date, tracking_stop_date=None, notes="",
                      tracking_field='Distance'):
    start_dt = datetime.strptime(tracking_start_date, '%Y-%m-%d')
    if tracking_stop_date:
        end_dt = datetime.strptime(tracking_stop_date, '%Y-%m-%d')
    else:
        end_dt = None

    tracked_items[name] = {
        'filter_name': filter_name,
        'tracking_start_date': start_dt,
        'tracking_stop_date': end_dt,
        'tracking_field': tracking_field,
        'notes': notes,
    }


def get_filtered_rides():
    for gc_filter in filters:
        filters[gc_filter]['season_metrics'] = GC.seasonMetrics(all=True, filter=filters[gc_filter]['filter'], compare=False)

def processData():
    # Collect process data
    field = []
    colors = []
    filter_names = []
    names = []
    aggregated = []
    notes = []
    units = []
    for item_name in tracked_items:
        # Add given name to chart (x axis)
        names.append(item_name)

        tracked_item = tracked_items[item_name]
        field.append(tracked_item['tracking_field'])
        filter_names.append(tracked_item['filter_name'])

        gc_filter = filters[tracked_item['filter_name']]
        colors.append(gc_filter['color'])
        rides = gc_filter["season_metrics"]

        filtered_result = []
        for i in np.arange(0, len(rides['date'])):
            if rides['date'][i] >= tracked_item["tracking_start_date"].date() and \
                    (tracked_item["tracking_stop_date"] is None or rides['date'][i] <= tracked_item["tracking_stop_date"].date()):
                filtered_result.append(rides[tracked_item['tracking_field']][i])

        # Add the sum of the tracked field (y-axis)
        result = sum(filtered_result)

        # For specific fields add your formatter and units
        unit = ""
        if tracked_item['tracking_field'] == 'Duration':
            result = round(result / 3600, 2)  # Transform to hours
            unit = 'hours'
        elif tracked_item['tracking_field'] == 'Distance':
            result = round(result, 2)
            unit = 'km'

        # default round 2
        result = round(result, 2)

        aggregated.append(result)
        units.append(unit)

        # Add notes to chart  (hover)
        # If no stop date is provided replace end date note by Now
        if tracked_item["tracking_stop_date"]:
            note_end_date = str(tracked_item["tracking_stop_date"].strftime('%Y-%m-%d'))
        else:
            note_end_date = "Now"
        edited_notes = str(result) + " " + unit + "<br>" \
                       + "(" + str(tracked_item["tracking_start_date"].strftime('%Y-%m-%d')) \
                       + " - " + note_end_date + ")" + "<br>" \
                       + str(tracked_item['notes'])
        notes.append(edited_notes)

    # Transform list in to panda data frame
    return pd.DataFrame(list(zip(field, names, colors, filter_names, aggregated, units, notes)),
                        columns=['field', 'names', 'colors', 'filter_names', 'aggregated', 'units', 'notes'])


def plot(panda_dict):
    # Go plot
    fig = make_subplots(rows=len(panda_dict['field'].unique()), cols=1,
                        subplot_titles=list(panda_dict['field'].unique()))
    count = 1
    for tracking_field in panda_dict['field'].unique():
        chart = panda_dict[panda_dict['field'] == tracking_field]
        for color in chart['colors'].unique():
            trace = chart[chart['colors'] == color]
            fig.append_trace(
                go.Bar(
                    x=trace['names'],
                    y=trace['aggregated'],
                    marker_color=color,
                    showlegend=True,
                    text=trace['aggregated'],
                    textposition='auto',
                    hoverinfo='text',
                    hovertext=trace['notes'],
                    name=tracking_field + "-" + str(trace['filter_names'].iloc[0])
                ),
                row=count,
                col=1
            )
        fig.update_yaxes(title_text=str(trace['units'].iloc[0]), showgrid=True, ticks="inside", color='white',
                         row=count,
                         col=1,
                         tickformat='d',
                         )
        count = count + 1

    fig['layout'].update(title_text="Tracking Custom fields (aggregated) by dates",
                         paper_bgcolor=gc_bg_color,
                         plot_bgcolor=gc_bg_color,
                         font=dict(
                             color=gc_text_color,
                             size=12
                         ),
                         yaxis=dict(showgrid=True),
                         )

    plotly.offline.plot(fig, auto_open=False, filename=temp_file.name)
    GC.webpage(pathlib.Path(temp_file.name).as_uri())


if __name__ == "__main__":
    main()
