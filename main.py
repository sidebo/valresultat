#!/usr/bin/env python
import plotly.express as px
import pandas as pd
import folium
import pyproj
from val import VAL, VAL_GEO
from loaddata import VALRESULTAT_FILES, GEO_FILES, load_geoframe, load_dataframe
import logging

logger = logging.getLogger(__name__)

YEAR = 2022
MAKE_VALRESULTAT = False
MAKE_VALDELTAGANDE = True # True

# Load valresultat
parties = ['V', 'S', 'MP'] 

df_val = pd.concat([
    load_dataframe(*VALRESULTAT_FILES[YEAR][val]).assign(Val=val.name.title())
    for val in [VAL.RIKSDAG, VAL.REGION, VAL.KOMMUN]
])


# Load geo frame and change name of column to match above frame
df_geo = load_geoframe(YEAR).rename(
    columns={'VD_NAMN': 'VALDISTRIKTSNAMN',
             'Vdnamn': 'VALDISTRIKTSNAMN',
             'Lkfv': 'VALDISTRIKTSKOD'})
df_geo["VALDISTRIKTSKOD"] = df_geo["VALDISTRIKTSKOD"].astype(int)
# Change to the right CRS


# Take VALDISTRIKTSNAMN from geo frame
df = df_geo.merge(df_val.drop(columns=["VALDISTRIKTSNAMN"]), on='VALDISTRIKTSKOD')
# Stockholm area
df = df[df["VALKRETSNAMN"] == "Stockholms kommun"].copy()


### VALRESULTAT 
if MAKE_VALRESULTAT:
    if YEAR == 2022:
        raise NotImplementedError("2022 files need to calculate percent")
    df_valresultat = df_val.melt(value_vars=parties, 
                             value_name='Procent', 
                             id_vars=['Val','VALDISTRIKTSNAMN', 'VALDISTRIKTSKOD'], 
                             var_name='Parti') 
    # NB: Seems important to create merged from GEO frame and not the other way
    #     around, to make sure the merged is of the right type.
    df = df.rename(columns={'VALDISTRIKTSNAMN': 'Valdistrikt'}).set_index('Valdistrikt')
    
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
    # Color-blind friendly red palette gradient sequence
    colors = ['#fcae91', '#fb6a4a', '#de2d26', '#a50f15', '#67000d']
    df["bin"] = pd.cut(df["VALDELTAGANDE"], bins, labels=labels).astype(str)
    df["color"] = pd.cut(df["VALDELTAGANDE"], bins, labels=colors).astype(str)
    print(df["color"].value_counts())
    df["Valdeltagande"] = df["VALDELTAGANDE"].map(lambda v: f"{v*1e-2:.1%}")
    
    lat, lon = 59.314391, 18.066062
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles='CartoDB Positron')
    folium.GeoJson(df, style_function=lambda feature: {"fillColor": feature["properties"]["color"]},
                   tooltip=folium.GeoJsonTooltip(
                       fields=['VALDISTRIKTSNAMN', 'Valdeltagande'], 
                       aliases=['', ''])).add_to(m)
    m.save(f"./stockholm-valdeltagande-{YEAR}.html")


"""
Where did the 'bottom' valdistrikt in Skarpnack go? 
Seems they disappeared in the 2022 data.

Also, running with 2022 data 'valresultat' track yields bananas Procent values.
"""