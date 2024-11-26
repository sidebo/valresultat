#!/usr/bin/env python
import plotly.express as px
import pandas as pd
import folium
import pyproj
from val import VAL 
from loaddata import load_geoframe, load_dataframe
import logging

logger = logging.getLogger(__name__)

YEAR = 2022
MAKE_VALRESULTAT = False #True 
MAKE_VALDELTAGANDE = True #True # True

map_columns={'VALDISTRIKTSNAMN': 'VD_NAMN',
             'Vdnamn': 'VD_NAMN'}

# Load valresultat
df_val = pd.concat([
    load_dataframe(YEAR, val).assign(Val=val.name.title())
    for val in [VAL.RIKSDAG, VAL.REGION, VAL.KOMMUN]
])
df_val = df_val.rename(columns=map_columns)

# Reminder: 'VD' = Valdistrikt

# Load geo frame and change name of column to match above frame
df_geo = load_geoframe(YEAR)
df_geo=df_geo.rename(columns=map_columns)

# Take VD_NAMN from geo frame
# NB: Seems important to create merged from GEO frame and not the other way
#     around, to make sure the merged is of the right type.
df = df_geo.merge(df_val.drop(columns=["VD_NAMN"]), on=["LAN_KOD", "KOMMUN_KOD", "VD_KOD"])
# Stockholm area
KOMMUN_KOD_STOCKHOLM = 80
KOMMUN_KOD = KOMMUN_KOD_STOCKHOLM
df = df[df["KOMMUN_KOD"] == KOMMUN_KOD].copy()

### VALRESULTAT 
if MAKE_VALRESULTAT:
    if YEAR == 2022:
        raise NotImplementedError("2022 files need to calculate percent")

    parties = ['V', 'S', 'MP'] 
    df = df.melt(value_vars=parties, 
                             value_name='Procent', 
                             id_vars=['Val','VD_NAMN', 'VD_KOD', 'KVK_NAMN', 'geometry'], 
                             var_name='Parti') 
    df = df.rename(columns={'VD_NAMN': 'Valdistrikt'}).set_index('Valdistrikt')
    
    ## Select Hammarby-Skarpnack districts
    df = df[(df.KVK_NAMN == "4 Östra Söderort") & (df.index.str.startswith('Skarpn'))]
    
    # Make one big plot with all elections
    fig = px.choropleth(
        df,
        geojson=df.geometry,
        locations=df.index,
        color='Procent',
        facet_col='Parti',
        facet_row='Val',
        projection='mercator',
        title=f"Valresultat {YEAR}",
        height=1600,
        width=1400
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    fig.update_geos(fitbounds="locations", visible=False)
    fig.write_html(f'./docs/{YEAR}-resultat-alla.html')
    
    # Make one plot per val
    for val in [VAL.RIKSDAG, VAL.REGION, VAL.KOMMUN]:
        df_val = df.query(f'Val=="{val.name.title()}"')
    
        fig = px.choropleth(
            df_val,
            geojson=df_val.geometry,
            locations=df_val.index,
            color='Procent',
            facet_col='Parti',
            projection='mercator',
            title=f"Valresultat {val.name.title().replace('Region', 'Landsting' if YEAR <= 2018 else 'Region')} {YEAR}"
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
        fig.update_geos(fitbounds="locations", visible=False)
        fig.write_html(f'./docs/{YEAR}-resultat-{val.name.lower()}.html')

### VALDELTAGANDE
if MAKE_VALDELTAGANDE:
    df = df[df["Val"] == "Riksdag"]
    bins = (0., 70., 75., 80., 85., 100)
    labels = ('<70%', '70-75%', '75-80%', '80-85%', '>85%')
    # Color-blind friendly heatmap palette gradient sequence
    colors = ['#ffffcc', '#ffeda0', '#feb24c', '#fd8d3c', '#e31a1c']

    df["bin"] = pd.cut(df["VALDELTAGANDE"], bins, labels=labels).astype(str)
    df["color"] = pd.cut(df["VALDELTAGANDE"], bins, labels=colors).astype(str)
    df["Valdeltagande"] = df["VALDELTAGANDE"].map(lambda v: f"{v*1e-2:.1%}")
    
    lat, lon = 59.314391, 18.066062 # Stockholm
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles='CartoDB Positron')
    folium.GeoJson(df, style_function=lambda feature: {"fillColor": feature["properties"]["color"]},
                   tooltip=folium.GeoJsonTooltip(
                       fields=['VD_NAMN', 'Valdeltagande'], 
                       aliases=['', ''])).add_to(m)
    m.save(f"./docs/stockholm-deltagande-riksdagsval-{YEAR}.html")


"""
TODO: calculate percent for 2022 valresultat data
"""