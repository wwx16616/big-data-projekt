# Pogoda w polskich miastach

Interaktywny dashboard analityczny w **Streamlit** do eksploracji historycznych danych
pogodowych dla największych polskich miast: temperatura, opady i wiatr w dowolnym
zakresie dat od 2000 roku.

**Działająca aplikacja:** https://big-data-projekt-wwx16616.streamlit.app/

## Co robi aplikacja

- Pobiera dzienne dane meteo (temp. min/max/średnia, suma opadów, maks. wiatr)
  dla 8 wbudowanych polskich miast - a przez wyszukiwarkę w panelu bocznym można
  dodać **dowolną miejscowość na świecie** (Geocoding API Open-Meteo zamienia
  nazwę na współrzędne).
- Czyści i przygotowuje dane: konwersje typów, interpolacja braków w szeregach,
  kolumny pochodne (amplituda dobowa, sezon, miesiąc, flaga dnia deszczowego).
- Prezentuje wyniki w 4 zakładkach z **6 typami wykresów**: liniowy (średnia
  krocząca), heatmapa (miasto × miesiąc), słupkowy, boxplot, scatter i mapa Polski.
- Reaguje na **5 widgetów**: text_input wyszukiwarki miast, multiselect miast,
  zakres dat, selectbox sezonu i slider wygładzania - wszystkie wykresy, KPI
  i tabela przeliczają się na bieżąco.
- Pozwala pobrać przefiltrowane dane jako CSV.

## Źródło danych

[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- darmowe, otwarte API bez klucza. Dane pobierane są na żywo per miasto i cachowane
przez 24 h (`@st.cache_data`), żeby nie odpytywać API przy każdej zmianie filtra.

## Uruchomienie lokalne

```bash
git clone https://github.com/wwx16616/big-data-projekt.git
cd big-data-projekt
pip install -r requirements.txt
streamlit run app.py
```

Aplikacja otworzy się pod adresem `http://localhost:8501`.

## Struktura projektu

```
├── app.py            # orkiestrator: layout, filtry, KPI, zakładki
├── src/
│   ├── data.py       # pobieranie z API, czyszczenie, kolumny pochodne
│   └── charts.py     # funkcje budujące wykresy Plotly
├── requirements.txt
```

## Technologie

Python · Streamlit · pandas · Plotly · requests
