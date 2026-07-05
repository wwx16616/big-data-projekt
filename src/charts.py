from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data import MIESIACE_PL

SZABLON = "plotly_white"


def wykres_liniowy(df: pd.DataFrame, okno: int) -> go.Figure:
    """Szereg czasowy średniej temperatury (średnia krocząca)."""
    d = df.sort_values("data").copy()
    d["temp_wygladzona"] = (
        d.groupby("miasto")["temp_srednia"]
        .transform(lambda s: s.rolling(okno, min_periods=1).mean())
    )
    fig = px.line(
        d,
        x="data",
        y="temp_wygladzona",
        color="miasto",
        labels={"data": "Data", "temp_wygladzona": "Temperatura [°C]", "miasto": "Miasto"},
        title=f"Średnia temperatura dobowa (średnia krocząca {okno} dni)",
        template=SZABLON,
    )
    fig.update_layout(hovermode="x unified", legend_title=None)
    return fig


def wykres_slupkowy(df: pd.DataFrame) -> go.Figure:
    """Suma opadów wg miasta."""
    agg = (
        df.groupby("miasto", as_index=False)["opady"]
        .sum()
        .sort_values("opady", ascending=False)
    )
    fig = px.bar(
        agg,
        x="miasto",
        y="opady",
        color="opady",
        color_continuous_scale="Blues",
        labels={"miasto": "Miasto", "opady": "Suma opadów [mm]"},
        title="Suma opadów w wybranym okresie",
        template=SZABLON,
    )
    fig.update_coloraxes(showscale=False)
    return fig


def wykres_scatter(df: pd.DataFrame) -> go.Figure:
    """Zależność wiatru od temperatury; rozmiar punktu = opady."""
    fig = px.scatter(
        df,
        x="temp_srednia",
        y="wiatr_max",
        color="miasto",
        size="opady",
        size_max=18,
        opacity=0.6,
        hover_data={"data": "|%d.%m.%Y"},
        labels={
            "temp_srednia": "Średnia temperatura [°C]",
            "wiatr_max": "Maks. prędkość wiatru [km/h]",
            "miasto": "Miasto",
            "opady": "Opady [mm]",
        },
        title="Wiatr vs temperatura (rozmiar punktu = opady)",
        template=SZABLON,
    )
    fig.update_layout(legend_title=None)
    return fig


def wykres_boxplot(df: pd.DataFrame) -> go.Figure:
    """Rozkład temperatur wg miasta."""
    fig = px.box(
        df,
        x="miasto",
        y="temp_srednia",
        color="miasto",
        labels={"miasto": "Miasto", "temp_srednia": "Średnia temperatura [°C]"},
        title="Rozkład średnich temperatur dobowych",
        template=SZABLON,
    )
    fig.update_layout(showlegend=False)
    return fig


def wykres_heatmapa(df: pd.DataFrame) -> go.Figure:
    """Heatmapa: średnia temperatura miasto × miesiąc."""
    pivot = (
        df.pivot_table(index="miasto", columns="miesiac", values="temp_srednia", aggfunc="mean")
        .reindex(columns=[m for m in MIESIACE_PL if m in df["miesiac"].unique()])
    )
    fig = px.imshow(
        pivot,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        labels={"x": "Miesiąc", "y": "Miasto", "color": "Temp. [°C]"},
        title="Średnia temperatura: miasto × miesiąc",
        template=SZABLON,
    )
    return fig


def wykres_mapa(df: pd.DataFrame, wspolrzedne: pd.DataFrame) -> go.Figure:
    """Mapa z miastami; kolor = śr. temperatura, rozmiar = suma opadów.

    `wspolrzedne` to ramka z kolumnami miasto/lat/lon - przekazywana z app.py,
    bo lista miast jest dynamiczna (użytkownik może dopisać własne).
    """
    agg = df.groupby("miasto", as_index=False).agg(
        temp_srednia=("temp_srednia", "mean"),
        opady=("opady", "sum"),
    )
    dane_mapa = agg.merge(wspolrzedne, on="miasto")

    # Zoom dopasowany do rozrzutu punktów (miasta zagraniczne = szersza mapa)
    rozrzut = max(
        dane_mapa["lat"].max() - dane_mapa["lat"].min(),
        dane_mapa["lon"].max() - dane_mapa["lon"].min(),
        0.0,
    )
    zoom = 5 if rozrzut <= 7 else 3 if rozrzut <= 25 else 1.5
    fig = px.scatter_map(
        dane_mapa,
        lat="lat",
        lon="lon",
        color="temp_srednia",
        size="opady",
        size_max=35,
        text="miasto",
        color_continuous_scale="RdYlBu_r",
        zoom=zoom,
        labels={"temp_srednia": "Śr. temp. [°C]", "opady": "Opady [mm]"},
        title="Mapa: średnia temperatura (kolor) i suma opadów (rozmiar)",
    )
    fig.update_layout(map_style="carto-positron", height=520, margin=dict(l=0, r=0, t=50, b=0))
    return fig
