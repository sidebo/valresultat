#!/usr/bin/env python
import plotly.express as px
import pandas as pd
import folium
import pyproj
from val import VAL, VAL_GEO
from loaddata import VALRESULTAT_FILES, GEO_FILES, load_geoframe, load_dataframe
import logging

logger = logging.getLogger(__name__)

YEAR = 2018
MAKE_VALRESULTAT = True 
MAKE_VALDELTAGANDE = False #True # True

map_columns={'VALDISTRIKTSNAMN': 'VD_NAMN',
             'Vdnamn': 'VD_NAMN',
             'Lkfv': 'VD_KOD',
             'VD': 'VD_KOD',
             'VALDISTRIKTSKOD': 'VD_KOD'}
# Load valresultat

df_val = pd.concat([
    load_dataframe(*VALRESULTAT_FILES[YEAR][val]).assign(Val=val.name.title())
    for val in [VAL.RIKSDAG, VAL.REGION, VAL.KOMMUN]
])
df_val = df_val.rename(columns=map_columns)

# Reminder: 'VD' = Valdistrikt

# Load geo frame and change name of column to match above frame
df_geo = load_geoframe(YEAR).rename(columns=map_columns)
# By comparing with valdistriktskod in the 2018 xlsx files, it seems
# the last 4 digits is the actual code
df_geo["VD_KOD"] = df_geo["VD_KOD"].map(lambda x: int(x[-4:]))

# Take VD_NAMN from geo frame
df = df_geo.merge(df_val.drop(columns=["VD_NAMN"]), on='VD_KOD')
# Stockholm area
df = df[df["RVK_NAMN"] == "Stockholms kommun"].copy()


### VALRESULTAT 
if MAKE_VALRESULTAT:
    if YEAR == 2022:
        raise NotImplementedError("2022 files need to calculate percent")

    parties = ['V', 'S', 'MP'] 
    df = df.melt(value_vars=parties, 
                             value_name='Procent', 
                             id_vars=['Val','VD_NAMN', 'VD_KOD', 'KVK_NAMN', 'geometry'], 
                             var_name='Parti') 
    # NB: Seems important to create merged from GEO frame and not the other way
    #     around, to make sure the merged is of the right type.
    df = df.rename(columns={'VD_NAMN': 'Valdistrikt'}).set_index('Valdistrikt')
    
    # Select Hammarby-Skarpnack districts
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
    # fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))
    fig.update_geos(fitbounds="locations", visible=False)
    fig.write_html(f'./docs/all.html')
    
    # Make one plot per val
    for val in [VAL.RIKSDAG, VAL.REGION, VAL.KOMMUN]:
        df_val = df.query(f'Val=="{val.name.title()}"')
    
        fig = px.choropleth(
            df_val,
            geojson=df_val.geometry,
            locations=df_val.index,
            color='Procent',
            facet_col='Parti',
            # facet_row='Val',
            projection='mercator',
            title=f"Valresultat {val.name.title().replace('Region', 'Landsting')} {YEAR}"
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
        # fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))
        fig.update_geos(fitbounds="locations", visible=False)
        fig.write_html(f'./docs/{val.name.title()}.html')

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
    m.save(f"./stockholm-valdeltagande-{YEAR}.html")


"""
Where did the 'bottom' valdistrikt in Skarpnack go? 
Seems they disappeared in the 2022 data.

Also, running with 2022 data 'valresultat' track yields bananas Procent values.
"""