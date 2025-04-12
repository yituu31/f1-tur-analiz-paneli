
import streamlit as st
import fastf1
import fastf1.plotting
from fastf1 import plotting
from fastf1.core import Laps
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("🏁 Formula 1 Tur Analiz Paneli")

# FastF1 cache klasörü
fastf1.Cache.enable_cache('./cache')

# Pist ve yıl seçimi
year = st.selectbox("Yıl Seç", options=[2023, 2022, 2021], index=0)
race_name = st.selectbox("Yarış Seç", options=["Bahrain Grand Prix", "Spanish Grand Prix", "Monaco Grand Prix"])

session = st.selectbox("Seans Seç", ["FP1", "FP2", "FP3", "Q", "R"], index=0)

# Verileri yükle
@st.cache_data(show_spinner=True)
def load_data(year, race_name, session):
    gp = fastf1.get_event(year, race_name)
    ses = gp.get_session(session)
    ses.load()
    return ses

try:
    session_data = load_data(year, race_name, session)
    st.success("Veriler yüklendi!")
except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu: {e}")
    st.stop()

# Takım ve lastik filtresi
teams = session_data.laps['Team'].unique()
selected_team = st.selectbox("Takım Seç", options=teams)
filtered_laps = session_data.laps[session_data.laps['Team'] == selected_team]

drivers = filtered_laps['Driver'].unique()
selected_drivers = st.multiselect("Pilot(lar)ı Seç", options=drivers, default=list(drivers))

tyre_compounds = filtered_laps['Compound'].unique()
selected_compound = st.selectbox("Lastik Türü", options=tyre_compounds)

# Filtrele
laps = filtered_laps[
    (filtered_laps['Driver'].isin(selected_drivers)) &
    (filtered_laps['Compound'] == selected_compound)
]

# Ortalama tempo filtresi
filter_consistency = st.checkbox("Tutarlı turları filtrele (anormal yavaş turlar çıkarılır)", value=True)

def filter_consistent_laps(laps: Laps, max_diff=1.5):
    laps = laps.pick_quicklaps()
    lap_times = laps['LapTime'].dt.total_seconds()
    filtered_indices = []

    for i in range(1, len(lap_times)-1):
        prev_time = lap_times.iloc[i-1]
        curr_time = lap_times.iloc[i]
        next_time = lap_times.iloc[i+1]
        if abs(curr_time - prev_time) < max_diff and abs(curr_time - next_time) < max_diff:
            filtered_indices.append(i)

    return laps.iloc[filtered_indices]

if filter_consistency:
    laps = filter_consistent_laps(laps)

# Gösterim
if laps.empty:
    st.warning("Seçilen filtrelere uygun veri bulunamadı.")
else:
    st.subheader("⏱️ Ortalama Tur Verileri")
    for drv in selected_drivers:
        avg = laps[laps['Driver'] == drv]['LapTime'].dt.total_seconds().mean()
        st.write(f"**{drv}** ({selected_compound}): {avg:.3f} s")

    st.subheader("📈 Tur Zamanları Grafiği")
    fig, ax = plt.subplots(figsize=(10, 4))
    for drv in selected_drivers:
        driver_laps = laps[laps['Driver'] == drv]
        ax.plot(driver_laps['LapNumber'], driver_laps['LapTime'].dt.total_seconds(), label=drv)
    ax.set_xlabel("Tur")
    ax.set_ylabel("Süre (s)")
    ax.legend()
    st.pyplot(fig)
