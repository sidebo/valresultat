#!/usr/bin/env python
import plotly.express as px
import pandas as pd
import pyproj
from val import VAL, VAL_GEO
from loaddata import VALRESULTAT_FILES, SHAPE_FILES, load_geoframe, load_dataframe

if __name__ == "__main__":

  # Load valresultat
  parties = ['V', 'S', 'MP'] # , 'FI']
  # Map party columns to a single column and add columns for riksdag/region/kommun
  df_valresultat = pd.concat([
      load_dataframe(*VALRESULTAT_FILES[2018][val]).rename(columns={party: 'Procent'}).assign(Parti=party).assign(Val=val.name.title()) for party in parties for val in [VAL.RIKSDAG, VAL.REGION, VAL.KOMMUN]
  ])

  # Load geo frame and change name of column to match above frame
  df_geo = load_geoframe(SHAPE_FILES[2018][VAL_GEO.VALDISTRIKT]).rename(columns={'VD_NAMN': 'VALDISTRIKTSNAMN'})
  # Change to the right CRS
  df_geo.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)

  # NB: Seems important to create merged from GEO frame and not the other way
  #     around, to make sure the merged is of the right type.
  df = df_geo.merge(df_valresultat, on='VALDISTRIKTSNAMN').rename(columns={'VALDISTRIKTSNAMN': 'Valdistrikt'}).set_index('Valdistrikt')

  # Select Hammarby-Skarpnack districts
  df = df[(df.KVK_NAMN == "4 Östra Söderort") & (df.index.str.startswith('Skarpn'))]

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
          projection='mercator'
      )
      fig.update_geos(fitbounds="locations", visible=False)
      fig.write_html(f'./docs/{val.name.title()}.html')
