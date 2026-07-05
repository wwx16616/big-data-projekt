from __future__ import annotations

import datetime as dt

import pandas as pd
import requests
import streamlit as st

# Miasta z współrzędnymi (do zapytań API i mapy)
MIASTA: dict[str, tuple[float, float]] = {
    "Warszawa": (52.2297, 21.0122),
    "Kraków": (50.0647, 19.9450),
    "Gdańsk": (54.3520, 18.6466),
    "Wrocław": (51.1079, 17.0385),
    "Poznań": (52.4064, 16.9252),
    "Katowice": (50.2649, 19.0238),
    "Białystok": (53.1325, 23.1688),
    "Rzeszów": (50.0412, 21.9991),
}

API_URL = "https://archive-api.open-meteo.com/v1/archive"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

ZMIENNE_DZIENNE = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "windspeed_10m_max",
]

SEZONY = {
    12: "Zima", 1: "Zima", 2: "Zima",
    3: "Wiosna", 4: "Wiosna", 5: "Wiosna",
    6: "Lato", 7: "Lato", 8: "Lato",
    9: "Jesień", 10: "Jesień", 11: "Jesień",
}

MIESIACE_PL = [
    "Sty", "Lut", "Mar", "Kwi", "Maj", "Cze",
    "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru",
]


def _pobierz_miasto(miasto: str, lat: float, lon: float, start: dt.date, koniec: dt.date) -> pd.DataFrame:
    """Pobiera surowe dane dzienne dla jednego miasta."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": koniec.isoformat(),
        "daily": ",".join(ZMIENNE_DZIENNE),
        "timezone": "Europe/Warsaw",
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    dane = resp.json()["daily"]
    df = pd.DataFrame(dane)
    df["miasto"] = miasto
    return df


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def pobierz_dane(
    miasta: tuple[tuple[str, float, float], ...], start: dt.date, koniec: dt.date
) -> pd.DataFrame:
    """Pobiera i łączy dane dla wielu miast (nazwa, lat, lon). Cache na 24h."""
    ramki = [_pobierz_miasto(m, lat, lon, start, koniec) for m, lat, lon in miasta]
    return pd.concat(ramki, ignore_index=True)


@st.cache_data(ttl=7 * 24 * 3600, show_spinner=False)
def szukaj_miasta(nazwa: str) -> tuple[str, float, float] | None:
    """Szuka miasta w Geocoding API Open-Meteo.

    Zwraca (etykieta, lat, lon) dla najlepszego trafienia albo None,
    gdy nic nie znaleziono. Miasta spoza Polski dostają dopisek z kodem kraju.
    """
    resp = requests.get(
        GEO_URL,
        params={"name": nazwa, "count": 1, "language": "pl"},
        timeout=15,
    )
    resp.raise_for_status()
    wyniki = resp.json().get("results")
    if not wyniki:
        return None
    r = wyniki[0]
    etykieta = r["name"]
    if r.get("country_code") and r["country_code"] != "PL":
        etykieta = f"{etykieta} ({r['country_code']})"
    return etykieta, float(r["latitude"]), float(r["longitude"])


def wyczysc_dane(df_surowe: pd.DataFrame) -> pd.DataFrame:
    df = df_surowe.rename(
        columns={
            "time": "data",
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "temperature_2m_mean": "temp_srednia",
            "precipitation_sum": "opady",
            "windspeed_10m_max": "wiatr_max",
        }
    ).copy()

    # Konwersje typów
    df["data"] = pd.to_datetime(df["data"])
    kolumny_num = ["temp_max", "temp_min", "temp_srednia", "opady", "wiatr_max"]
    df[kolumny_num] = df[kolumny_num].astype("float64")

    # Braki: interpolacja w obrębie każdego miasta (sortując po dacie)
    df = df.sort_values(["miasto", "data"])
    df[kolumny_num] = (
        df.groupby("miasto")[kolumny_num]
        .transform(lambda s: s.interpolate(limit=3, limit_direction="both"))
    )
    df = df.dropna(subset=kolumny_num)

    # Kolumny pochodne
    df["amplituda"] = df["temp_max"] - df["temp_min"]
    df["rok"] = df["data"].dt.year
    df["nr_miesiaca"] = df["data"].dt.month
    df["miesiac"] = df["nr_miesiaca"].map(lambda m: MIESIACE_PL[m - 1])
    df["sezon"] = df["nr_miesiaca"].map(SEZONY)
    df["dzien_deszczowy"] = df["opady"] >= 1.0  # próg 1 mm/dobę

    return df.reset_index(drop=True)

