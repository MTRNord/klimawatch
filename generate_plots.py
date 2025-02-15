# plots
import plotly.graph_objects as go
# make it easier with numeric values
import pandas
import numpy as np
# for computing the trend
from scipy.stats import linregress
# reading command line arguments
import sys
# writing json
import json

# read data
if(len(sys.argv) == 1):
  print("No city given, plotting data for Münster ('data/muenster.csv')")
  city = "muenster"
  df = pandas.read_csv("data/muenster.csv")
else:
  print("Plotting data for", sys.argv[1])
  city = sys.argv[1]
  try:
    df = pandas.read_csv("data/" + city + ".csv")
  except:
    print("File not found. Does the file", city + ".csv",  "exist?")
    exit();

# create plot
fig = go.Figure()

# set() only lists unique values
# this loop plots all categories present in the csv, if type is either "real" or "geplant"
for cat in set(df.category):
  subdf = df[df.category == cat]
  subdf_real = subdf[subdf.type == "real"]
  fig.add_trace(go.Scatter(x = subdf_real.year, y = subdf_real.value, name = cat + ", real",
                          mode = "lines+markers"))

  subdf_planned = subdf[subdf.type == "geplant"]
  fig.add_trace(go.Scatter(x = subdf_planned.year, y = subdf_planned.value, name = cat + ", geplant",
                          mode = "lines+markers", line = dict(dash = "dash")))

# compute trend based on current data
subdf = df[df.category == "Gesamt"]
subdf_real = subdf[subdf.type == "real"]

# variables to write to JSON later on
years_past_total_real = list(subdf_real.year)
values_past_total_real = list(subdf_real.value)

slope, intercept, r, p, stderr = linregress(subdf_real.year, subdf_real.value)
# print info about trend
print("linearer Trend: Steigung: ", slope, "Y-Achsenabschnitt: ",  intercept, "R^2: ", r)

# plot trend
fig.add_trace(go.Scatter(x = subdf.year, y = slope * subdf.year + intercept, name = "Trend",
                          mode = "lines", line = dict(dash = "dot")))


# compute remaining paris budget
last_emissions = np.array(df[df.note == "last_emissions"].value)
# see https://scilogs.spektrum.de/klimalounge/wie-viel-co2-kann-deutschland-noch-ausstossen/
paris_budget_germany_2019 = 7300000
inhabitants_germany = 83019213
paris_budget_per_capita_2019 = paris_budget_germany_2019 / inhabitants_germany
paris_budget_full_city_2019 = paris_budget_per_capita_2019 * np.array(df[df.type == "Einwohner"].value)
# substract individual CO2 use; roughly 40%, see https://uba.co2-rechner.de/
paris_budget_wo_individual_city_2019 = paris_budget_full_city_2019 * 0.6
# substract already emitted CO2 from 2019 onwards; assume last measured budget is 2019 emission
paris_budget_wo_individual_city_2020 = paris_budget_wo_individual_city_2019 - last_emissions

# compute slope for linear reduction of paris budget
paris_slope = (-pow(last_emissions, 2)) / (2 * paris_budget_wo_individual_city_2020)
years_to_climate_neutral = - last_emissions / paris_slope
full_years_to_climate_neutral = int(np.round(years_to_climate_neutral))

# plot paris line
future = list(range(0, full_years_to_climate_neutral, 1)) # from 2020 to 2050
future.append(float(years_to_climate_neutral))
fig.add_trace(go.Scatter(x = np.array(future) + 2020, y = paris_slope * np.array(future) + last_emissions, name = "Paris berechnet",
                          mode = "lines+markers", line = dict(dash = "dash")))

total_emission_1990 = float(df[(df.type == "real") & (df.category == "Gesamt") & (df.year == 1990)].value)

# horizontal legend; vertical line at 2020
fig.update_layout(
  title="Realität und Ziele",
  yaxis_title="CO2 in tausend Tonnen",
  xaxis_title="Jahr",
  legend_orientation="h",
  # vertical "today" line
  shapes=[
    go.layout.Shape(
      type="line",
      x0=2020,
      y0=0,
      x1=2020,
      y1=total_emission_1990,
    )]
  )

# write plot to file
fig.write_html("hugo/layouts/shortcodes/paris_" + city + ".html", include_plotlyjs = False,
                config={'displayModeBar': False}, full_html = False, auto_open=True)

# write computed Paris budget to JSON file for you-draw-it

paris_data = {}
paris_data["values"] = []

# past data

for index in range(len(years_past_total_real)):
  paris_data["values"].append({
      "year": years_past_total_real[index],
      "value": values_past_total_real[index]
  })

# years with remaining budget
paris_years = list(np.array(future) + 2020)
budget_per_year = list(paris_slope * np.array(future) + last_emissions)

for index in range(len(paris_years)):
  paris_data["values"].append({
      "year": paris_years[index],
      "value": budget_per_year[index]
  })

# fill up zeros to let people draw until 2050
# ~ years_until_2050 =

climate_neutral_by = int(np.round(max(paris_years)))
years_after_budget = range(climate_neutral_by, 2051, 1)

for y in years_after_budget:
  paris_data["values"].append({
      "year": y,
      "value": 0
  })

with open("hugo/data/you_draw_it_" + city + "_paris_data.json", "w") as outfile:
    json.dump(paris_data, outfile)

# ~ print(np.array(future) + 2020)
# ~ print(paris_slope * np.array(future) + last_emissions)

# TODO add percentage to plotly tooltips
# ~ percentage_real = [x / data_real.data["CO2"][0] for x in data_real.data["CO2"]]
# ~ data_real.add(name = "percentage", data = percentage_real)

# ~ percentage_warmth_real = [x / data_warmth_real.data["CO2"][0] for x in data_warmth_real.data["CO2"]]
# ~ data_warmth_real.add(name = "percentage", data = percentage_warmth_real)

# ~ percentage_electricity_real = [x / data_electricity_real.data["CO2"][0] for x in data_electricity_real.data["CO2"]]
# ~ data_electricity_real.add(name = "percentage", data = percentage_electricity_real)

# ~ percentage_traffic_real = [x / data_traffic_real.data["CO2"][0] for x in data_traffic_real.data["CO2"]]
# ~ data_traffic_real.add(name = "percentage", data = percentage_traffic_real)

# ~ percentage_planned = [x / data_real.data["CO2"][0] for x in data_planned.data["CO2"]]
# ~ data_planned.add(name = "percentage", data = percentage_planned)

# ~ percentage_trend = [x / data_real.data["CO2"][0] for x in data_trend.data["CO2"]]
# ~ data_trend.add(name = "percentage", data = percentage_trend)

# ~ percentage_paris = [x / data_real.data["CO2"][0] for x in data_paris.data["CO2"]]
# ~ data_paris.add(name = "percentage", data = percentage_paris)

# ~ TOOLTIPS = [
    # ~ ("Jahr", "@year"),
    # ~ ("CO2 (tausend Tonnen)", "@CO2{0.00}"),
    # ~ ("Prozent von 1990", "@percentage{0.0%}"),
    # ~ ("Typ", "@type"),
# ~ ]


# TODO visualise modules

fig_modules = go.Figure(go.Treemap(
    branchvalues = "total",
    labels = ["Wärme", "Strom", "Verkehr",  "W1", "W2", "S1", "S2", "V1", "V2"],
    parents = ["", "", "", "Wärme", "Wärme", "Strom", "Strom", "Verkehr", "Verkehr"],
    values = [780, 690, 484, 700, 80, 600, 90, 400, 84],
    marker_colors = ["green", "yellow", "red", "green", "green", "red", "green", "red", "red"],
    textinfo = "label+value+percent parent+percent entry+percent root",
))

# ~ fig_modules.write_html('hugo/layouts/shortcodes/modules_' + city + '.html', include_plotlyjs = False,
                        # ~ config={'displayModeBar': False}, full_html = False, auto_open=True)

