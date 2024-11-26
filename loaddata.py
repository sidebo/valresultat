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

GEO_FILES = {
    2018: {
      VAL_GEO.RIKSDAGSVALKRETS: VALGEO_DIR / "2018_valgeografi_riksdagsvalkretsar/alla_riksdagsvalkretsar.shp",
      VAL_GEO.KOMMUNVALKRETS:   VALGEO_DIR / "2018_valgeografi_kommunvalkretsar/alla_kommunvalkretsar.shp",
      VAL_GEO.VALDISTRIKT:      VALGEO_DIR / "2018_valgeografi_valdistrikt/alla_valdistrikt.shp"
    },
    2022: {
      # Below is Stockholm only, from https://www.val.se/valresultat/riksdag-region-och-kommun/2022/radata-och-statistik.html#slutligtvalresultat
      VAL_GEO.VALDISTRIKT: VALGEO_DIR / "2022_valdistrikt/VD_01_20220910_Val_20220911.json",
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

def load_geoframe(year: int, geo=VAL_GEO.VALDISTRIKT) -> gpd.geodataframe.GeoDataFrame:
    """Load geo data frame"""
    fname = GEO_FILES[year][geo]
    logger.info(f"Loading geo data from {fname}")
    df_geo = gpd.read_file(fname)
    if year == 2022:
        df_geo = df_geo.set_crs("EPSG:32633", allow_override=True)
        df_geo = extract_codes(df_geo, "Lkfv")
    return df_geo.to_crs("EPSG:4326")

def extract_codes(df, col_vd_code: str) -> pd.DataFrame:
    df = df.copy()
    df["VD_KOD_STR"] = df[col_vd_code].astype(str)
    df["VD_KOD"] = df["VD_KOD_STR"].map(lambda x: int(x[-4:]))
    df["KOMMUN_KOD"] = df["VD_KOD_STR"].map(lambda x: int(x[-6:-4]))
    df["LAN_KOD"] = df["VD_KOD_STR"].map(lambda x: int(x[:-6]))
    df = df.drop(columns=["VD_KOD_STR", col_vd_code])
    return df

@cache
def load_dataframe(year: int, val: VAL, sheet_name: str = None) -> pd.DataFrame:
    fname, sheet_name = VALRESULTAT_FILES[year][val]
    fname = str(fname)
    parties = ["V", "S", "MP", "M", "C", "KD", "SD"]
    idx_cols = ["LÄNSKOD", "KOMMUNKOD", "VALDISTRIKTSKOD"] if year == 2018 else ["VALDISTRIKTSKOD"]
    usecols = idx_cols + parties + ["VALDELTAGANDE", "VALDISTRIKTSNAMN", "VALKRETSNAMN"]
    logger.info(f"Loading data frame {fname}")
    df = None
    if fname.endswith(".xlsx") and sheet_name is not None:
        df = pd.read_excel(fname, sheet_name=sheet_name, usecols=usecols)
    elif fname.endswith(".csv") and sheet_name is None:
        df = pd.read_csv(fname, usecols=usecols)
    else:
        raise ValueError(fname)
    if year == 2022:
        df = extract_codes(df, "VALDISTRIKTSKOD")
    return df
    

if __name__ == "__main__":
  # Geoframe
  # df = load_geoframe()

  df = load_dataframe(*VALRESULTAT_FILES[2022][VAL.KOMMUN])

  # Valresultat frame
  df = load_dataframe(*VALRESULTAT_FILES[2018][VAL.RIKSDAG])

  print(f'Loaded dataframe into variable "df"')
