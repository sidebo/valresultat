#!/usr/bin/env python
import geopandas as gpd
from functools import cache
from typing import Union
import pandas as pd
from val import VAL, VAL_GEO
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = "data"
VALRESULTAT_DIR = Path(DATA_DIR) / "valresultat"
VALGEO_DIR = Path(DATA_DIR) / "valgeografi"

SHAPE_FILES = {
    2018: {
      VAL_GEO.RIKSDAGSVALKRETS: VALGEO_DIR / "2018_valgeografi_riksdagsvalkretsar/alla_riksdagsvalkretsar.shp",
      VAL_GEO.KOMMUNVALKRETS:   VALGEO_DIR / "2018_valgeografi_kommunvalkretsar/alla_kommunvalkretsar.shp",
      VAL_GEO.VALDISTRIKT:      VALGEO_DIR / "2018_valgeografi_valdistrikt/alla_valdistrikt.shp"
    },
    2022: {
      # TODO: get new geo files
      VAL_GEO.RIKSDAGSVALKRETS: VALGEO_DIR / "2018_valgeografi_riksdagsvalkretsar/alla_riksdagsvalkretsar.shp",
      VAL_GEO.KOMMUNVALKRETS:   VALGEO_DIR / "2018_valgeografi_kommunvalkretsar/alla_kommunvalkretsar.shp",
      VAL_GEO.VALDISTRIKT:      VALGEO_DIR / "2018_valgeografi_valdistrikt/alla_valdistrikt.shp"
    }
}

# Election result (filename, sheet name) tuples
VALRESULTAT_FILES = {
    2018: {
        VAL.RIKSDAG: (VALRESULTAT_DIR / "2018_R_per_valdistrikt.xlsx", "R procent"),
        VAL.REGION:  (VALRESULTAT_DIR / "2018_L_per_valdistrikt.xlsx", "L procent"),
        VAL.KOMMUN:  (VALRESULTAT_DIR / "2018_K_per_valdistrikt.xlsx", "K procent")
    },
    2022: {
        VAL.RIKSDAG: (VALRESULTAT_DIR / "riksdag_2022.csv", None),
        VAL.REGION: (VALRESULTAT_DIR / "region_2022.csv", None),
        VAL.KOMMUN: (VALRESULTAT_DIR / "kommun_2022.csv", None),
    }
}

def load_geoframe(fname: str = SHAPE_FILES[2018][VAL_GEO.VALDISTRIKT]) -> gpd.geodataframe.GeoDataFrame:
    """Load geo data frame"""
    logger.info(f"Loading geo data from {fname}")
    return gpd.read_file(fname)

@cache
def load_dataframe(fname: Union[str, Path], sheet_name: str = None) -> pd.DataFrame:
    fname = str(fname)
    parties = ["V", "S", "MP", "M", "C", "KD", "SD"]
    usecols = parties + ["VALDELTAGANDE", "VALDISTRIKTSNAMN"]
    logger.info(f"Loading data frame {fname}")
    if fname.endswith(".xlsx") and sheet_name is not None:
        return pd.read_excel(fname, sheet_name=sheet_name, usecols=usecols)
    elif fname.endswith(".csv") and sheet_name is None:
        return pd.read_csv(fname, usecols=usecols)
    raise ValueError((fname, sheet_name))

if __name__ == "__main__":
  # Geoframe
  # df = load_geoframe()

  df = load_dataframe(*VALRESULTAT_FILES[2022][VAL.KOMMUN])

  # Valresultat frame
  df = load_dataframe(*VALRESULTAT_FILES[2018][VAL.RIKSDAG])

  print(f'Loaded dataframe into variable "df"')
