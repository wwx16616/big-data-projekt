import datetime as dt

import pandas as pd
import streamlit as st

from src import charts
from src.data import MIASTA, pobierz_dane, szukaj_miasta, wyczysc_dane

st.set_page_config(
    page_title="Pogoda w polskich miastach",
    page_icon="🌤️",
    layout="wide",
)

# ----------------------------- Sidebar: filtry -----------------------------
DZIS = dt.date.today()
DOMYSLNY_START = DZIS - dt.timedelta(days=365)
MIN_DATA = dt.date(2000, 1, 1)
MAX_DATA = DZIS - dt.timedelta(days=6)  # archiwum ma kilka dni opóźnienia

# Stan sesji: miasta dopisane przez użytkownika + aktualny wybór na liście
if "miasta_dodane" not in st.session_state:
    st.session_state.miasta_dodane = {}  # {nazwa: (lat, lon)}
if "wybor_miast" not in st.session_state:
    st.session_state.wybor_miast = ["Warszawa", "Kraków", "Gdańsk", "Wrocław"]

with st.sidebar:
    st.title("Filtry")

    # Wyszukiwarka miast spoza listy (Geocoding API Open-Meteo)
    nowe_miasto = st.text_input(  # widget 5
        "Dodaj miasto spoza listy",
        placeholder="np. Zakopane, Berlin, Lizbona…",
    )
    if st.button("Znajdź i dodaj", use_container_width=True) and nowe_miasto.strip():
        try:
            trafienie = szukaj_miasta(nowe_miasto.strip())
        except Exception:
            trafienie = None
            st.error("Wyszukiwarka chwilowo nie odpowiada - spróbuj ponownie.")
        else:
            if trafienie is None:
                st.error(f"Nie znaleziono miejscowości „{nowe_miasto.strip()}”.")
            else:
                nazwa, lat, lon = trafienie
                st.session_state.miasta_dodane[nazwa] = (lat, lon)
                if nazwa not in st.session_state.wybor_miast:
                    st.session_state.wybor_miast.append(nazwa)
                st.success(f"Dodano: {nazwa}")

    # Pełna pula: miasta wbudowane + dopisane w tej sesji
    wszystkie_miasta = {**MIASTA, **st.session_state.miasta_dodane}

    wybrane_miasta = st.multiselect(  # widget 1
        "Miasta",
        options=list(wszystkie_miasta),
        key="wybor_miast",
    )

    zakres = st.date_input(  # widget 2
        "Zakres dat",
        value=(DOMYSLNY_START, MAX_DATA),
        min_value=MIN_DATA,
        max_value=MAX_DATA,
        format="DD.MM.YYYY",
    )

    sezon = st.selectbox(  # widget 3
        "Sezon",
        options=["Wszystkie", "Wiosna", "Lato", "Jesień", "Zima"],
    )

    okno = st.slider(  # widget 4
        "Wygładzenie wykresu liniowego (dni)",
        min_value=1,
        max_value=30,
        value=7,
        help="Okno średniej kroczącej dla szeregu czasowego temperatury.",
    )

    st.caption("Dane: [Open-Meteo](https://open-meteo.com).")

# ------------------------------- Walidacja ---------------------------------
st.title("Pogoda w polskich miastach")
st.markdown(
    "Analiza historycznych danych meteo z **Open-Meteo** - temperatura, opady i wiatr "
    "dla największych polskich miast. Ustaw filtry w panelu bocznym."
)

if not wybrane_miasta:
    st.warning("Wybierz co najmniej jedno miasto w panelu bocznym.")
    st.stop()

if not (isinstance(zakres, tuple) and len(zakres) == 2):
    st.info("Wybierz pełny zakres dat (początek i koniec).")
    st.stop()

start, koniec = zakres

# --------------------------- Pobranie i czyszczenie ------------------------
zapytanie = tuple(sorted((m, *wszystkie_miasta[m]) for m in wybrane_miasta))
try:
    with st.spinner("Pobieram dane z Open-Meteo…"):
        df_surowe = pobierz_dane(zapytanie, start, koniec)
except Exception as blad:
    st.error(
        "Nie udało się pobrać danych z Open-Meteo. Spróbuj ponownie za chwilę "
        f"albo zawęź zakres dat. Szczegóły: `{blad}`"
    )
    st.stop()

df = wyczysc_dane(df_surowe)
if sezon != "Wszystkie":
    df = df[df["sezon"] == sezon]

if df.empty:
    st.warning("Brak danych dla wybranych filtrów - zmień sezon albo zakres dat.")
    st.stop()

# ---------------------------------- KPI ------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Śr. temperatura", f"{df['temp_srednia'].mean():.1f} °C")
k2.metric("Rekord ciepła", f"{df['temp_max'].max():.1f} °C")
k3.metric("Rekord zimna", f"{df['temp_min'].min():.1f} °C")
k4.metric("Dni deszczowe", f"{df['dzien_deszczowy'].mean():.0%}")

st.divider()

# --------------------------------- Zakładki --------------------------------
tab_czas, tab_porownanie, tab_mapa, tab_dane = st.tabs(
    ["W czasie", "Porównanie miast", "Mapa", "Dane"]
)

with tab_czas:
    st.plotly_chart(charts.wykres_liniowy(df, okno), use_container_width=True)
    st.caption(
        "Średnia krocząca wygładza dobowe wahania i uwydatnia sezonowość - "
        "różnice między miastami są zwykle największe zimą."
    )
    st.plotly_chart(charts.wykres_heatmapa(df), use_container_width=True)
    st.caption(
        "Heatmapa pokazuje profil roczny każdego miasta. Miasta nadmorskie (Gdańsk) "
        "mają łagodniejsze zimy i chłodniejsze lata niż kontynentalny wschód (Białystok)."
    )

with tab_porownanie:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.wykres_slupkowy(df), use_container_width=True)
    with c2:
        st.plotly_chart(charts.wykres_boxplot(df), use_container_width=True)
    st.plotly_chart(charts.wykres_scatter(df), use_container_width=True)
    st.caption(
        "Scatter pozwala wychwycić dni skrajne: silny wiatr przy niskiej temperaturze "
        "to zwykle zimowe fronty, a duże opady latem - burze."
    )

with tab_mapa:
    wspolrzedne = pd.DataFrame(
        [
            {"miasto": m, "lat": lat, "lon": lon}
            for m, (lat, lon) in wszystkie_miasta.items()
            if m in wybrane_miasta
        ]
    )
    st.plotly_chart(charts.wykres_mapa(df, wspolrzedne), use_container_width=True)
    st.caption("Kolor punktu = średnia temperatura w okresie, rozmiar = suma opadów.")

with tab_dane:
    st.markdown(
        f"Po czyszczeniu: **{len(df):,}** wierszy, "
        f"**{df['miasto'].nunique()}** miast, "
        f"zakres **{df['data'].min():%d.%m.%Y} – {df['data'].max():%d.%m.%Y}**."
    )
    st.dataframe(
        df.drop(columns=["nr_miesiaca"]).sort_values(["miasto", "data"]),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Pobierz przefiltrowane dane (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="pogoda_filtrowane.csv",
        mime="text/csv",
    )
