#!/usr/bin/env python
import geopandas as gpd
import pandas as pd
from val import VAL, VAL_GEO
import logging

logger = logging.getLogger(__name__)

SHAPE_FILES = {
    2018: {
      VAL_GEO.RIKSDAGSVALKRETS: "2018_valgeografi_riksdagsvalkretsar/alla_riksdagsvalkretsar.shp",
      VAL_GEO.KOMMUNVALKRETS: "2018_valgeografi_kommunvalkretsar/alla_kommunvalkretsar.shp",
      VAL_GEO.VALDISTRIKT: "2018_valgeografi_valdistrikt/alla_valdistrikt.shp"
    }
}

# Election result (filename, sheet name) tuples
VALRESULTAT_FILES = {
    2018: {
        VAL.RIKSDAG: ("2018_R_per_valdistrikt.xlsx", "R procent")
    }
}

def load_geoframe(fname: str = SHAPE_FILES[2018][VAL_GEO.VALDISTRIKT]) -> gpd.geodataframe.GeoDataFrame:
    """Load geo data frame"""
    logger.info(f"Loading geo data from {fname}")
    return gpd.read_file(fname)

def load_dataframe(fname: str, sheet_name: str = None) -> pd.DataFrame:
    logger.info(f"Loading data frame {fname}")
    if fname.endswith(".xlsx") and sheet_name is not None:
        return pd.read_excel(fname, sheet_name=sheet_name)
    elif fname.endswith(".csv") and sheet_name is None:
        return pd.csv(fname)
    logger.error(f"Invalid arguments {fname} and {sheet_name}!")

if __name__ == "__main__":
  df = load_geoframe()
  print(f'Loaded geo dataframe into variable "df"')
