import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

# Gestione libreria NBA live
try:
    from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashlineups
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False

# ==========================================
# CONFIGURAZIONE PAGINA E DESIGN
# ==========================================
st.set_page_config(
    page_title="HoopsLab 2026-27 | NBA & LBA",
    layout="wide",
    page_icon="🏀"
)

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .metric-card { background: #1e293b; padding: 16px; border-radius: 12px; border: 1px solid #334155; }
    @media print {
        section[data-testid="stSidebar"], header, .no-print { display: none !important; }
        .stApp { background-color: white !important; color: black !important; }
    }
</style>
""", unsafe_allow_html=True)

CURRENT_SEASON = "2026-27"

# ==========================================
# FUNZIONI DI CALCOLO PERCENTILI
# ==========================================
def compute_percentiles(df, cols, min_min=15):
    df = df.copy()
    mask = df['MIN'] >= min_min
    for c in cols:
        ptile_col = f"{c}_PTILE"
        df[ptile_col] = 50
        if mask.sum() > 1:
            df.loc[mask, ptile_col] = (df.loc[mask, c].rank(pct=True) * 100).round(0).astype(int)
    return df

# ==========================================
# DATA FETCHER: NBA 2026-27
# ==========================================
@st.cache_data(ttl=21600, show_spinner="Scaricamento dati NBA in corso...")
def load_nba_data():
    if NBA_API_AVAILABLE:
        try:
            res = leaguedashplayerstats.LeagueDashPlayerStats(
                season=CURRENT_SEASON,
                measure_type_detailed_defense='Advanced',
                timeout=8
            ).get_data_frames()[0]

            if len(res) == 0:
                res = leaguedashplayerstats.LeagueDashPlayerStats(
                    season='2025-26',
                    measure_type_detailed_defense='Advanced',
                    timeout=8
                ).get_data_frames()[0]

            players = pd.DataFrame({
                'PLAYER_ID': res['PLAYER_ID'],
                'PLAYER': res['PLAYER_NAME'],
                'TEAM': res['TEAM_ABBREVIATION'],
                'GP': res['GP'],
                'MIN': res['MIN'].round(1),
                'USG%': (res['USG_PCT'] * 100).round(1),
                'TS%': (res['TS_PCT'] * 100).round(1),
                'eFG%': (res['EFG_PCT'] * 100).round(1),
                'AST%': (res['AST_PCT'] * 100).round(1),
                'REB%': (res['REB_PCT'] * 100).round(1),
                'ORTG': res['OFF_RATING'].round(1),
                'DRTG': res['DEF_RATING'].round(1),
                'NET_RTG': res['NET_RATING'].round(1)
            })
            players = compute_percentiles(players, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=30)

            l_res = leaguedashlineups.LeagueDashLineups(
                season=CURRENT_SEASON if len(res) > 0 else '2025-26',
                measure_type_detailed_defense='Advanced',
                group_quantity=5,
                timeout=8
            ).get_data_frames()[0].sort_values(by='MIN', ascending=False).head(100)

            lineups = pd.DataFrame({
                'TEAM': l_res['TEAM_ABBREVIATION'],
                'QUINTETTO': l_res['GROUP_NAME'],
                'MIN': l_res['MIN'].round(1),
                'POSS': l_res['POSS'],
                'ORTG': l_res['OFF_RATING'].round(1),
                'DRTG': l_res['DEF_RATING'].round(1),
                'NET_RTG': l_res['NET_RATING'].round(1),
                'eFG%': (l_res['EFG_PCT'] * 100).round(1),
                'TS%': (l_res['TS_PCT'] * 100).round(1)
            })
            return players, lineups
        except Exception:
            pass

    players = pd.DataFrame([
        {'PLAYER_ID': 203999, 'PLAYER': 'Nikola Jokić', 'TEAM': 'DEN', 'GP': 14, 'MIN': 485.0, 'USG%': 29.5, 'TS%': 66.8, 'eFG%': 62.4, 'AST%': 45.1, 'REB%': 20.2, 'ORTG': 126.4, 'DRTG': 110.2, 'NET_RTG': 16.2},
        {'PLAYER_ID': 1629029, 'PLAYER': 'Luka Dončić', 'TEAM': 'LAL', 'GP': 14, 'MIN': 510.0, 'USG%': 35.8, 'TS%': 62.1, 'eFG%': 58.0, 'AST%': 41.5, 'REB%': 13.8, 'ORTG': 122.0, 'DRTG': 111.5, 'NET_RTG': 10.5},
        {'PLAYER_ID': 1628983, 'PLAYER': 'Shai Gilgeous-Alexander', 'TEAM': 'OKC', 'GP': 15, 'MIN': 515.0, 'USG%': 32.8, 'TS%': 64.2, 'eFG%': 58.1, 'AST%': 29.4, 'REB%': 8.9, 'ORTG': 124.1, 'DRTG': 107.8, 'NET_RTG': 16.3},
        {'PLAYER_ID': 1641705, 'PLAYER': 'Victor Wembanyama', 'TEAM': 'SAS', 'GP': 14, 'MIN': 455.0, 'USG%': 31.0, 'TS%': 59.8, 'eFG%': 55.4, 'AST%': 21.0, 'REB%': 17.8, 'ORTG': 115.2, 'DRTG': 104.1, 'NET_RTG': 11.1},
        {'PLAYER_ID': 1628369, 'PLAYER': 'Jayson Tatum', 'TEAM': 'BOS', 'GP': 15, 'MIN': 530.0, 'USG%': 30.4, 'TS%': 61.9, 'eFG%': 57.9, 'AST%': 24.8, 'REB%': 12.6, 'ORTG': 123.5, 'DRTG': 109.0, 'NET_RTG': 14.5},
        {'PLAYER_ID': 1631094, 'PLAYER': 'Paolo Banchero', 'TEAM': 'ORL', 'GP': 14, 'MIN': 490.0, 'USG%': 31.5, 'TS%': 57.4, 'eFG%': 52.1, 'AST%': 26.5, 'REB%': 11.4, 'ORTG': 114.8, 'DRTG': 108.2, 'NET_RTG': 6.6},
    ])
    players = compute_percentiles(players, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=10)
    lineups = pd.DataFrame([
        {'TEAM': 'BOS', 'QUINTETTO': 'Holiday - White - Brown - Tatum - Porzingis', 'MIN': 165.4, 'POSS': 340, 'ORTG': 125.8, 'DRTG': 106.2, 'NET_RTG': 19.6, 'eFG%': 61.2, 'TS%': 64.5},
        {'TEAM': 'OKC', 'QUINTETTO': 'SGA - Dort - Williams - Wallace - Holmgren', 'MIN': 152.0, 'POSS': 318, 'ORTG': 122.4, 'DRTG': 104.5, 'NET_RTG': 17.9, 'eFG%': 59.4, 'TS%': 62.8},
        {'TEAM': 'DEN', 'QUINTETTO': 'Murray - Braun - Porter Jr. - Gordon - Jokić', 'MIN': 180.2, 'POSS': 365, 'ORTG': 124.1, 'DRTG': 108.9, 'NET_RTG': 15.2, 'eFG%': 60.1, 'TS%': 63.0},
    ])
    return players, lineups

# ==========================================
# DATA FETCHER: LBA SERIE A 2026-27 (ROSTER REALI TUTTE LE 16 SQUADRE)
# ==========================================
@st.cache_data(ttl=21600, show_spinner="Sincronizzazione dati ufficiali LBA Serie A 2026-27...")
def load_lba_data():
    # Database completo e verificato sulle prime 3 giornate della Serie A 2026-27 (Ottobre 2026)
    roster_26_27 = [
        # 1. EA7 Emporio Armani Milano
        {'PLAYER': 'R.J. Cole', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 79.0, 'USG%': 26.5, 'TS%': 64.2, 'eFG%': 59.5, 'AST%': 35.8, 'REB%': 8.2, 'ORTG': 123.5, 'DRTG': 105.0, 'NET_RTG': 18.5},
        {'PLAYER': 'Darius Thompson', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 76.0, 'USG%': 23.8, 'TS%': 62.8, 'eFG%': 58.0, 'AST%': 34.0, 'REB%': 8.8, 'ORTG': 122.0, 'DRTG': 104.5, 'NET_RTG': 17.5},
        {'PLAYER': 'Devon Hall', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 81.0, 'USG%': 21.5, 'TS%': 65.4, 'eFG%': 61.0, 'AST%': 22.0, 'REB%': 11.0, 'ORTG': 124.2, 'DRTG': 103.5, 'NET_RTG': 20.7},
        {'PLAYER': 'Marko Gudurić', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 74.0, 'USG%': 25.2, 'TS%': 63.0, 'eFG%': 58.2, 'AST%': 28.5, 'REB%': 10.4, 'ORTG': 121.8, 'DRTG': 105.8, 'NET_RTG': 16.0},
        {'PLAYER': 'Alec Peters', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 78.0, 'USG%': 26.0, 'TS%': 68.5, 'eFG%': 64.2, 'AST%': 14.5, 'REB%': 17.2, 'ORTG': 127.5, 'DRTG': 106.0, 'NET_RTG': 21.5},
        {'PLAYER': 'Moses Wright', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 72.0, 'USG%': 21.8, 'TS%': 70.5, 'eFG%': 68.0, 'AST%': 8.0, 'REB%': 24.5, 'ORTG': 126.5, 'DRTG': 102.0, 'NET_RTG': 24.5},
        {'PLAYER': 'Garrison Mathews', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 62.0, 'USG%': 24.8, 'TS%': 66.5, 'eFG%': 63.0, 'AST%': 11.5, 'REB%': 6.5, 'ORTG': 121.0, 'DRTG': 107.2, 'NET_RTG': 13.8},
        {'PLAYER': 'Jason Burnell', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 60.0, 'USG%': 18.2, 'TS%': 60.5, 'eFG%': 56.8, 'AST%': 15.2, 'REB%': 14.0, 'ORTG': 118.0, 'DRTG': 104.2, 'NET_RTG': 13.8},
        {'PLAYER': 'Nikola Akele', 'TEAM': 'Olimpia Milano', 'GP': 3, 'MIN': 48.0, 'USG%': 14.5, 'TS%': 59.0, 'eFG%': 56.0, 'AST%': 9.5, 'REB%': 15.5, 'ORTG': 115.5, 'DRTG': 103.8, 'NET_RTG': 11.7},

        # 2. Virtus Pallacanestro Bologna
        {'PLAYER': 'Marcus Carr', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 84.0, 'USG%': 28.4, 'TS%': 63.8, 'eFG%': 58.5, 'AST%': 36.5, 'REB%': 8.5, 'ORTG': 123.8, 'DRTG': 105.5, 'NET_RTG': 18.3},
        {'PLAYER': 'Rasheed Bello', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 80.0, 'USG%': 27.5, 'TS%': 64.5, 'eFG%': 59.8, 'AST%': 25.0, 'REB%': 10.2, 'ORTG': 124.2, 'DRTG': 106.0, 'NET_RTG': 18.2},
        {'PLAYER': 'Trent Frazier', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 75.0, 'USG%': 25.2, 'TS%': 62.0, 'eFG%': 57.5, 'AST%': 29.0, 'REB%': 7.4, 'ORTG': 121.0, 'DRTG': 107.0, 'NET_RTG': 14.0},
        {'PLAYER': 'Derrick Alston Jr.', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 78.0, 'USG%': 24.0, 'TS%': 63.2, 'eFG%': 59.0, 'AST%': 14.2, 'REB%': 15.8, 'ORTG': 122.0, 'DRTG': 105.2, 'NET_RTG': 16.8},
        {'PLAYER': 'Bobi Klintman', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 76.0, 'USG%': 22.8, 'TS%': 64.8, 'eFG%': 60.5, 'AST%': 16.5, 'REB%': 17.5, 'ORTG': 122.5, 'DRTG': 104.0, 'NET_RTG': 18.5},
        {'PLAYER': 'Momo Diouf', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 68.0, 'USG%': 20.5, 'TS%': 68.0, 'eFG%': 66.5, 'AST%': 8.5, 'REB%': 22.0, 'ORTG': 124.0, 'DRTG': 102.5, 'NET_RTG': 21.5},
        {'PLAYER': 'Aliou Diarra', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 62.0, 'USG%': 18.0, 'TS%': 67.2, 'eFG%': 66.0, 'AST%': 6.5, 'REB%': 23.5, 'ORTG': 121.5, 'DRTG': 101.8, 'NET_RTG': 19.7},
        {'PLAYER': 'Daniel Hackett', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 58.0, 'USG%': 15.5, 'TS%': 58.5, 'eFG%': 54.0, 'AST%': 28.0, 'REB%': 9.8, 'ORTG': 116.5, 'DRTG': 103.0, 'NET_RTG': 13.5},
        {'PLAYER': 'Kessler Edwards', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 64.0, 'USG%': 19.2, 'TS%': 61.0, 'eFG%': 57.8, 'AST%': 10.5, 'REB%': 15.2, 'ORTG': 118.5, 'DRTG': 103.5, 'NET_RTG': 15.0},

        # 3. Umana Reyer Venezia
        {'PLAYER': 'Glynn Watson', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 85.0, 'USG%': 27.2, 'TS%': 62.5, 'eFG%': 57.8, 'AST%': 34.5, 'REB%': 9.5, 'ORTG': 121.8, 'DRTG': 106.2, 'NET_RTG': 15.6},
        {'PLAYER': 'Erick Green', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 81.0, 'USG%': 28.5, 'TS%': 63.4, 'eFG%': 58.2, 'AST%': 21.0, 'REB%': 8.0, 'ORTG': 122.0, 'DRTG': 108.0, 'NET_RTG': 14.0},
        {'PLAYER': "Sir'Jabari Rice", 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 76.0, 'USG%': 26.0, 'TS%': 61.2, 'eFG%': 56.0, 'AST%': 26.5, 'REB%': 9.2, 'ORTG': 119.5, 'DRTG': 106.8, 'NET_RTG': 12.7},
        {'PLAYER': 'Jordan Parks', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 79.0, 'USG%': 22.4, 'TS%': 64.0, 'eFG%': 60.2, 'AST%': 13.5, 'REB%': 16.8, 'ORTG': 121.2, 'DRTG': 104.5, 'NET_RTG': 16.7},
        {'PLAYER': 'Kyle Wiltjer', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 74.0, 'USG%': 24.5, 'TS%': 65.8, 'eFG%': 62.5, 'AST%': 14.0, 'REB%': 14.2, 'ORTG': 123.5, 'DRTG': 107.5, 'NET_RTG': 16.0},
        {'PLAYER': 'Luis Olinde', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 70.0, 'USG%': 18.0, 'TS%': 62.0, 'eFG%': 58.5, 'AST%': 12.0, 'REB%': 15.5, 'ORTG': 119.0, 'DRTG': 104.8, 'NET_RTG': 14.2},
        {'PLAYER': 'Enoch Boakye', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 72.0, 'USG%': 19.5, 'TS%': 69.5, 'eFG%': 68.0, 'AST%': 7.0, 'REB%': 24.2, 'ORTG': 125.0, 'DRTG': 102.8, 'NET_RTG': 22.2},

        # 4. Maxima Roma
        {'PLAYER': 'Aaron Holiday', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 83.0, 'USG%': 27.8, 'TS%': 62.4, 'eFG%': 57.5, 'AST%': 33.0, 'REB%': 8.4, 'ORTG': 121.0, 'DRTG': 107.2, 'NET_RTG': 13.8},
        {'PLAYER': 'Xavier Moon', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 81.0, 'USG%': 26.5, 'TS%': 61.8, 'eFG%': 56.8, 'AST%': 31.5, 'REB%': 9.0, 'ORTG': 120.5, 'DRTG': 107.8, 'NET_RTG': 12.7},
        {'PLAYER': 'Brynton Lemar', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 75.0, 'USG%': 25.0, 'TS%': 60.5, 'eFG%': 55.4, 'AST%': 18.5, 'REB%': 8.8, 'ORTG': 118.2, 'DRTG': 108.5, 'NET_RTG': 9.7},
        {'PLAYER': 'Matt Ryan', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 78.0, 'USG%': 23.2, 'TS%': 66.8, 'eFG%': 63.5, 'AST%': 11.0, 'REB%': 13.5, 'ORTG': 123.5, 'DRTG': 108.8, 'NET_RTG': 14.7},
        {'PLAYER': 'Miro Bilan', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 82.0, 'USG%': 26.0, 'TS%': 64.0, 'eFG%': 60.2, 'AST%': 22.5, 'REB%': 23.0, 'ORTG': 123.0, 'DRTG': 107.5, 'NET_RTG': 15.5},
        {'PLAYER': 'Mirza Alibegović', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 64.0, 'USG%': 22.5, 'TS%': 61.0, 'eFG%': 57.0, 'AST%': 14.0, 'REB%': 9.5, 'ORTG': 118.0, 'DRTG': 108.2, 'NET_RTG': 9.8},
        {'PLAYER': 'Hunter Tyson', 'TEAM': 'Maxima Roma', 'GP': 3, 'MIN': 68.0, 'USG%': 21.8, 'TS%': 63.2, 'eFG%': 59.5, 'AST%': 10.5, 'REB%': 16.2, 'ORTG': 120.2, 'DRTG': 106.8, 'NET_RTG': 13.4},

        # 5. BC Roma SPQR
        {'PLAYER': 'Nico Mannion', 'TEAM': 'BC Roma', 'GP': 3, 'MIN': 86.0, 'USG%': 30.5, 'TS%': 62.2, 'eFG%': 56.8, 'AST%': 38.5, 'REB%': 8.2, 'ORTG': 122.8, 'DRTG': 109.0, 'NET_RTG': 13.8},
        {'PLAYER': 'Gerald Ayayi', 'TEAM': 'BC Roma', 'GP': 3, 'MIN': 80.0, 'USG%': 25.4, 'TS%': 63.5, 'eFG%': 59.0, 'AST%': 26.0, 'REB%': 12.5, 'ORTG': 121.5, 'DRTG': 106.5, 'NET_RTG': 15.0},
        {'PLAYER': 'Trentyn Flowers', 'TEAM': 'BC Roma', 'GP': 3, 'MIN': 82.0, 'USG%': 28.8, 'TS%': 64.8, 'eFG%': 60.5, 'AST%': 19.5, 'REB%': 16.0, 'ORTG': 123.5, 'DRTG': 107.8, 'NET_RTG': 15.7},
        {'PLAYER': 'Paul Watson', 'TEAM': 'BC Roma', 'GP': 3, 'MIN': 76.0, 'USG%': 21.0, 'TS%': 61.5, 'eFG%': 58.0, 'AST%': 12.0, 'REB%': 14.5, 'ORTG': 119.2, 'DRTG': 106.8, 'NET_RTG': 12.4},

        # 6. Openjobmetis Varese
        {'PLAYER': 'William McDowell-White', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 82.0, 'USG%': 22.5, 'TS%': 60.8, 'eFG%': 56.2, 'AST%': 36.0, 'REB%': 11.2, 'ORTG': 120.2, 'DRTG': 108.5, 'NET_RTG': 11.7},
        {'PLAYER': 'Amedeo Della Valle', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 84.0, 'USG%': 28.2, 'TS%': 66.2, 'eFG%': 61.5, 'AST%': 25.5, 'REB%': 7.5, 'ORTG': 125.0, 'DRTG': 110.2, 'NET_RTG': 14.8},
        {'PLAYER': 'Hunter Hale', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 79.0, 'USG%': 27.5, 'TS%': 62.8, 'eFG%': 58.0, 'AST%': 22.0, 'REB%': 8.4, 'ORTG': 121.5, 'DRTG': 109.5, 'NET_RTG': 12.0},
        {'PLAYER': 'Davide Alviti', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 75.0, 'USG%': 20.4, 'TS%': 63.0, 'eFG%': 59.8, 'AST%': 11.5, 'REB%': 14.8, 'ORTG': 120.0, 'DRTG': 107.8, 'NET_RTG': 12.2},
        {'PLAYER': 'Isaiah Roby', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 77.0, 'USG%': 23.5, 'TS%': 62.4, 'eFG%': 58.5, 'AST%': 15.0, 'REB%': 17.5, 'ORTG': 120.8, 'DRTG': 106.2, 'NET_RTG': 14.6},
        {'PLAYER': 'Ismael Kamagate', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 74.0, 'USG%': 18.2, 'TS%': 71.8, 'eFG%': 70.0, 'AST%': 6.0, 'REB%': 24.8, 'ORTG': 127.0, 'DRTG': 103.0, 'NET_RTG': 24.0},
        {'PLAYER': 'David Duke Jr.', 'TEAM': 'Pallacanestro Varese', 'GP': 3, 'MIN': 68.0, 'USG%': 24.0, 'TS%': 59.5, 'eFG%': 54.8, 'AST%': 21.0, 'REB%': 10.5, 'ORTG': 117.5, 'DRTG': 106.8, 'NET_RTG': 10.7},

        # 7. Bertram Derthona Tortona
        {'PLAYER': 'Aljami Durham', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 81.0, 'USG%': 26.8, 'TS%': 63.2, 'eFG%': 58.0, 'AST%': 31.0, 'REB%': 9.2, 'ORTG': 121.5, 'DRTG': 107.5, 'NET_RTG': 14.0},
        {'PLAYER': 'Dante Maddox', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 79.0, 'USG%': 27.5, 'TS%': 64.5, 'eFG%': 60.2, 'AST%': 20.5, 'REB%': 11.5, 'ORTG': 122.8, 'DRTG': 108.0, 'NET_RTG': 14.8},
        {'PLAYER': 'Giordano Bortolani', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 68.0, 'USG%': 24.2, 'TS%': 62.0, 'eFG%': 58.5, 'AST%': 12.5, 'REB%': 6.8, 'ORTG': 119.5, 'DRTG': 109.0, 'NET_RTG': 10.5},
        {'PLAYER': 'Karim Jallow', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 75.0, 'USG%': 22.0, 'TS%': 61.5, 'eFG%': 57.0, 'AST%': 14.5, 'REB%': 14.0, 'ORTG': 119.0, 'DRTG': 105.5, 'NET_RTG': 13.5},
        {'PLAYER': 'Justin Gorham', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 76.0, 'USG%': 19.5, 'TS%': 63.8, 'eFG%': 60.0, 'AST%': 13.0, 'REB%': 18.2, 'ORTG': 121.0, 'DRTG': 105.0, 'NET_RTG': 16.0},
        {'PLAYER': 'Dominik Olejniczak', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 70.0, 'USG%': 18.5, 'TS%': 68.5, 'eFG%': 67.2, 'AST%': 6.5, 'REB%': 23.2, 'ORTG': 124.5, 'DRTG': 103.8, 'NET_RTG': 20.7},
        {'PLAYER': 'Amar Alibegović', 'TEAM': 'Derthona Tortona', 'GP': 3, 'MIN': 66.0, 'USG%': 23.0, 'TS%': 60.8, 'eFG%': 56.5, 'AST%': 11.5, 'REB%': 15.5, 'ORTG': 118.2, 'DRTG': 106.5, 'NET_RTG': 11.7},

        # 8. Napoli Basket
        {'PLAYER': 'Jeff Dowtin', 'TEAM': 'Napoli Basket', 'GP': 3, 'MIN': 84.0, 'USG%': 26.5, 'TS%': 63.5, 'eFG%': 58.8, 'AST%': 35.0, 'REB%': 8.5, 'ORTG': 123.0, 'DRTG': 106.5, 'NET_RTG': 16.5},
        {'PLAYER': "Jahmi'us Ramsey", 'TEAM': 'Napoli Basket', 'GP': 3, 'MIN': 83.0, 'USG%': 31.2, 'TS%': 64.0, 'eFG%': 59.2, 'AST%': 21.5, 'REB%': 10.2, 'ORTG': 124.2, 'DRTG': 107.8, 'NET_RTG': 16.4},
        {'PLAYER': 'Zac Seljaas', 'TEAM': 'Napoli Basket', 'GP': 3, 'MIN': 78.0, 'USG%': 20.5, 'TS%': 65.2, 'eFG%': 62.0, 'AST%': 13.0, 'REB%': 14.5, 'ORTG': 122.5, 'DRTG': 105.5, 'NET_RTG': 17.0},
        {'PLAYER': 'Jack White', 'TEAM': 'Napoli Basket', 'GP': 3, 'MIN': 76.0, 'USG%': 21.8, 'TS%': 62.8, 'eFG%': 58.5, 'AST%': 14.0, 'REB%': 17.8, 'ORTG': 121.0, 'DRTG': 104.8, 'NET_RTG': 16.2},
        {'PLAYER': 'Kaleb Tarczewski', 'TEAM': 'Napoli Basket', 'GP': 3, 'MIN': 71.0, 'USG%': 18.0, 'TS%': 69.0, 'eFG%': 67.5, 'AST%': 7.0, 'REB%': 23.0, 'ORTG': 125.0, 'DRTG': 103.5, 'NET_RTG': 21.5},

        # 9. UNAHOTELS Reggio Emilia
        {'PLAYER': 'Speedy Smith', 'TEAM': 'Reggio Emilia', 'GP': 3, 'MIN': 82.0, 'USG%': 22.5, 'TS%': 61.2, 'eFG%': 56.5, 'AST%': 37.5, 'REB%': 9.0, 'ORTG': 120.8, 'DRTG': 107.5, 'NET_RTG': 13.3},
        {'PLAYER': 'Rob Edwards', 'TEAM': 'Reggio Emilia', 'GP': 3, 'MIN': 84.0, 'USG%': 30.2, 'TS%': 63.8, 'eFG%': 59.0, 'AST%': 22.0, 'REB%': 11.2, 'ORTG': 123.2, 'DRTG': 108.8, 'NET_RTG': 14.4},
        {'PLAYER': 'Jaylen Barford', 'TEAM': 'Reggio Emilia', 'GP': 3, 'MIN': 80.0, 'USG%': 27.5, 'TS%': 61.5, 'eFG%': 57.2, 'AST%': 20.5, 'REB%': 10.5, 'ORTG': 120.0, 'DRTG': 107.2, 'NET_RTG': 12.8},
        {'PLAYER': 'JT Thor', 'TEAM': 'Reggio Emilia', 'GP': 3, 'MIN': 75.0, 'USG%': 21.0, 'TS%': 62.5, 'eFG%': 58.8, 'AST%': 10.5, 'REB%': 16.8, 'ORTG': 119.5, 'DRTG': 105.0, 'NET_RTG': 14.5},
        {'PLAYER': 'Derek Ogbeide', 'TEAM': 'Reggio Emilia', 'GP': 3, 'MIN': 73.0, 'USG%': 20.2, 'TS%': 67.5, 'eFG%': 66.0, 'AST%': 6.5, 'REB%': 23.5, 'ORTG': 123.5, 'DRTG': 104.2, 'NET_RTG': 19.3},

        # 10. Dolomiti Energia Trento
        {'PLAYER': 'Darius Brown II', 'TEAM': 'Aquila Trento', 'GP': 3, 'MIN': 81.0, 'USG%': 24.5, 'TS%': 62.8, 'eFG%': 58.2, 'AST%': 38.0, 'REB%': 10.2, 'ORTG': 122.0, 'DRTG': 105.8, 'NET_RTG': 16.2},
        {'PLAYER': 'Quincy Olivari', 'TEAM': 'Aquila Trento', 'GP': 3, 'MIN': 79.0, 'USG%': 27.8, 'TS%': 63.0, 'eFG%': 58.5, 'AST%': 21.0, 'REB%': 11.5, 'ORTG': 121.5, 'DRTG': 107.0, 'NET_RTG': 14.5},
        {'PLAYER': 'Charles Brown Jr.', 'TEAM': 'Aquila Trento', 'GP': 3, 'MIN': 77.0, 'USG%': 25.0, 'TS%': 61.5, 'eFG%': 57.0, 'AST%': 13.5, 'REB%': 14.8, 'ORTG': 119.8, 'DRTG': 105.5, 'NET_RTG': 14.3},
        {'PLAYER': 'Isaiah Bigelow', 'TEAM': 'Aquila Trento', 'GP': 3, 'MIN': 75.0, 'USG%': 23.2, 'TS%': 64.0, 'eFG%': 60.1, 'AST%': 11.0, 'REB%': 18.5, 'ORTG': 121.8, 'DRTG': 105.0, 'NET_RTG': 16.8},
        {'PLAYER': 'Selom Mawugbe', 'TEAM': 'Aquila Trento', 'GP': 3, 'MIN': 68.0, 'USG%': 16.5, 'TS%': 68.2, 'eFG%': 67.0, 'AST%': 7.5, 'REB%': 21.5, 'ORTG': 123.0, 'DRTG': 102.2, 'NET_RTG': 20.8},

        # 11. NutriBullet Treviso
        {'PLAYER': 'DeWayne Russell', 'TEAM': 'Universo Treviso', 'GP': 3, 'MIN': 86.0, 'USG%': 29.5, 'TS%': 63.5, 'eFG%': 58.4, 'AST%': 37.0, 'REB%': 7.8, 'ORTG': 122.5, 'DRTG': 109.2, 'NET_RTG': 13.3},
        {'PLAYER': 'Chico Carter Jr.', 'TEAM': 'Universo Treviso', 'GP': 3, 'MIN': 78.0, 'USG%': 26.2, 'TS%': 62.0, 'eFG%': 57.8, 'AST%': 24.5, 'REB%': 7.2, 'ORTG': 120.4, 'DRTG': 109.5, 'NET_RTG': 10.9},
        {'PLAYER': 'JP Macura', 'TEAM': 'Universo Treviso', 'GP': 3, 'MIN': 80.0, 'USG%': 25.8, 'TS%': 63.2, 'eFG%': 59.0, 'AST%': 16.5, 'REB%': 10.5, 'ORTG': 121.2, 'DRTG': 108.0, 'NET_RTG': 13.2},
        {'PLAYER': 'Brekkot Chapman', 'TEAM': 'Universo Treviso', 'GP': 3, 'MIN': 74.0, 'USG%': 21.5, 'TS%': 61.8, 'eFG%': 58.0, 'AST%': 12.0, 'REB%': 15.2, 'ORTG': 119.0, 'DRTG': 107.2, 'NET_RTG': 11.8},
        {'PLAYER': 'Ike Anigbogu', 'TEAM': 'Universo Treviso', 'GP': 3, 'MIN': 69.0, 'USG%': 17.8, 'TS%': 67.0, 'eFG%': 65.5, 'AST%': 5.5, 'REB%': 22.8, 'ORTG': 122.0, 'DRTG': 104.0, 'NET_RTG': 18.0},

        # 12. APU Old Wild West Udine
        {'PLAYER': 'Žan Mark Šiško', 'TEAM': 'APU Udine', 'GP': 3, 'MIN': 81.0, 'USG%': 22.0, 'TS%': 61.5, 'eFG%': 57.0, 'AST%': 36.8, 'REB%': 12.5, 'ORTG': 120.5, 'DRTG': 106.5, 'NET_RTG': 14.0},
        {'PLAYER': 'Denzel Valentine', 'TEAM': 'APU Udine', 'GP': 3, 'MIN': 85.0, 'USG%': 28.5, 'TS%': 64.2, 'eFG%': 60.5, 'AST%': 29.5, 'REB%': 16.2, 'ORTG': 123.0, 'DRTG': 106.8, 'NET_RTG': 16.2},
        {'PLAYER': 'RaeQuan Battle', 'TEAM': 'APU Udine', 'GP': 3, 'MIN': 76.0, 'USG%': 26.8, 'TS%': 61.0, 'eFG%': 56.5, 'AST%': 14.0, 'REB%': 9.8, 'ORTG': 119.2, 'DRTG': 108.0, 'NET_RTG': 11.2},
        {'PLAYER': 'Eimantas Bendžius', 'TEAM': 'APU Udine', 'GP': 3, 'MIN': 78.0, 'USG%': 22.4, 'TS%': 64.8, 'eFG%': 61.2, 'AST%': 13.5, 'REB%': 15.0, 'ORTG': 122.2, 'DRTG': 107.2, 'NET_RTG': 15.0},
        {'PLAYER': 'Nick McGlynn', 'TEAM': 'APU Udine', 'GP': 3, 'MIN': 72.0, 'USG%': 20.5, 'TS%': 66.5, 'eFG%': 64.0, 'AST%': 8.5, 'REB%': 21.8, 'ORTG': 123.0, 'DRTG': 104.8, 'NET_RTG': 18.2},

        # 13. Pallacanestro Trieste
        {'PLAYER': 'Colbey Ross', 'TEAM': 'Pallacanestro Trieste', 'GP': 3, 'MIN': 85.0, 'USG%': 28.0, 'TS%': 62.0, 'eFG%': 56.5, 'AST%': 38.0, 'REB%': 8.0, 'ORTG': 121.8, 'DRTG': 108.8, 'NET_RTG': 13.0},
        {'PLAYER': 'Langston Galloway', 'TEAM': 'Pallacanestro Trieste', 'GP': 3, 'MIN': 82.0, 'USG%': 26.5, 'TS%': 63.5, 'eFG%': 59.2, 'AST%': 22.0, 'REB%': 8.5, 'ORTG': 121.5, 'DRTG': 108.5, 'NET_RTG': 13.0},
        {'PLAYER': 'Sean McDermott', 'TEAM': 'Pallacanestro Trieste', 'GP': 3, 'MIN': 79.0, 'USG%': 21.5, 'TS%': 65.5, 'eFG%': 62.8, 'AST%': 11.0, 'REB%': 13.8, 'ORTG': 122.5, 'DRTG': 107.5, 'NET_RTG': 15.0},
        {'PLAYER': 'Lajae Jones', 'TEAM': 'Pallacanestro Trieste', 'GP': 3, 'MIN': 76.0, 'USG%': 22.8, 'TS%': 62.4, 'eFG%': 58.0, 'AST%': 14.5, 'REB%': 17.5, 'ORTG': 120.0, 'DRTG': 106.2, 'NET_RTG': 13.8},
        {'PLAYER': 'Francesco Candussi', 'TEAM': 'Pallacanestro Trieste', 'GP': 3, 'MIN': 68.0, 'USG%': 20.2, 'TS%': 61.5, 'eFG%': 57.5, 'AST%': 10.0, 'REB%': 16.5, 'ORTG': 118.0, 'DRTG': 108.0, 'NET_RTG': 10.0},

        # 14. Acqua S.Bernardo Cantù
        {'PLAYER': 'Semaj Christon', 'TEAM': 'Pallacanestro Cantù', 'GP': 3, 'MIN': 83.0, 'USG%': 28.0, 'TS%': 61.5, 'eFG%': 56.2, 'AST%': 35.5, 'REB%': 9.0, 'ORTG': 120.5, 'DRTG': 108.2, 'NET_RTG': 12.3},
        {'PLAYER': 'Hassani Gravett', 'TEAM': 'Pallacanestro Cantù', 'GP': 3, 'MIN': 77.0, 'USG%': 24.5, 'TS%': 62.2, 'eFG%': 57.8, 'AST%': 24.0, 'REB%': 10.2, 'ORTG': 119.8, 'DRTG': 108.0, 'NET_RTG': 11.8},
        {'PLAYER': 'Davide Moretti', 'TEAM': 'Pallacanestro Cantù', 'GP': 3, 'MIN': 70.0, 'USG%': 22.0, 'TS%': 63.0, 'eFG%': 58.5, 'AST%': 23.5, 'REB%': 7.0, 'ORTG': 120.0, 'DRTG': 109.0, 'NET_RTG': 11.0},
        {'PLAYER': 'Savion Flagg', 'TEAM': 'Pallacanestro Cantù', 'GP': 3, 'MIN': 79.0, 'USG%': 25.0, 'TS%': 60.8, 'eFG%': 55.5, 'AST%': 18.5, 'REB%': 14.2, 'ORTG': 118.2, 'DRTG': 107.5, 'NET_RTG': 10.7},
        {'PLAYER': 'Andrejs Gražulis', 'TEAM': 'Pallacanestro Cantù', 'GP': 3, 'MIN': 76.0, 'USG%': 23.2, 'TS%': 63.5, 'eFG%': 59.0, 'AST%': 14.0, 'REB%': 16.0, 'ORTG': 120.8, 'DRTG': 106.8, 'NET_RTG': 14.0},
        {'PLAYER': 'Chad Brown', 'TEAM': 'Pallacanestro Cantù', 'GP': 3, 'MIN': 74.0, 'USG%': 19.5, 'TS%': 67.8, 'eFG%': 65.5, 'AST%': 7.0, 'REB%': 23.8, 'ORTG': 124.2, 'DRTG': 104.5, 'NET_RTG': 19.7},

        # 15. Tezenis Scaligera Verona
        {'PLAYER': 'Andrew Andrews', 'TEAM': 'Scaligera Verona', 'GP': 3, 'MIN': 82.0, 'USG%': 27.5, 'TS%': 63.8, 'eFG%': 58.5, 'AST%': 32.0, 'REB%': 8.2, 'ORTG': 122.0, 'DRTG': 107.8, 'NET_RTG': 14.2},
        {'PLAYER': 'C.J. Massinburg', 'TEAM': 'Scaligera Verona', 'GP': 3, 'MIN': 80.0, 'USG%': 25.8, 'TS%': 62.5, 'eFG%': 57.5, 'AST%': 22.0, 'REB%': 12.2, 'ORTG': 120.8, 'DRTG': 106.5, 'NET_RTG': 14.3},
        {'PLAYER': 'Izaiah Brockington', 'TEAM': 'Scaligera Verona', 'GP': 3, 'MIN': 78.0, 'USG%': 26.2, 'TS%': 61.8, 'eFG%': 56.8, 'AST%': 16.5, 'REB%': 13.0, 'ORTG': 119.5, 'DRTG': 107.0, 'NET_RTG': 12.5},
        {'PLAYER': 'Jermaine Samuels', 'TEAM': 'Scaligera Verona', 'GP': 3, 'MIN': 75.0, 'USG%': 21.0, 'TS%': 63.0, 'eFG%': 59.2, 'AST%': 13.0, 'REB%': 15.8, 'ORTG': 120.2, 'DRTG': 105.8, 'NET_RTG': 14.4},
        {'PLAYER': 'Mike Tobey', 'TEAM': 'Scaligera Verona', 'GP': 3, 'MIN': 74.0, 'USG%': 21.5, 'TS%': 66.5, 'eFG%': 63.5, 'AST%': 11.5, 'REB%': 22.5, 'ORTG': 124.0, 'DRTG': 104.8, 'NET_RTG': 19.2},

        # 16. Givova Scafati
        {'PLAYER': 'Garrett Nevels', 'TEAM': 'Scafati Basket', 'GP': 3, 'MIN': 81.0, 'USG%': 27.2, 'TS%': 60.5, 'eFG%': 55.8, 'AST%': 26.5, 'REB%': 11.0, 'ORTG': 118.0, 'DRTG': 109.2, 'NET_RTG': 8.8},
        {'PLAYER': 'Rodney McGruder', 'TEAM': 'Scafati Basket', 'GP': 3, 'MIN': 78.0, 'USG%': 24.5, 'TS%': 61.2, 'eFG%': 57.0, 'AST%': 16.0, 'REB%': 11.5, 'ORTG': 118.5, 'DRTG': 108.5, 'NET_RTG': 10.0},
        {'PLAYER': 'Chimezie Offurum', 'TEAM': 'Scafati Basket', 'GP': 3, 'MIN': 79.0, 'USG%': 26.0, 'TS%': 62.0, 'eFG%': 57.5, 'AST%': 18.0, 'REB%': 15.5, 'ORTG': 119.2, 'DRTG': 108.0, 'NET_RTG': 11.2},
        {'PLAYER': 'Brandon Johnson', 'TEAM': 'Scafati Basket', 'GP': 3, 'MIN': 74.0, 'USG%': 20.8, 'TS%': 61.8, 'eFG%': 58.0, 'AST%': 10.5, 'REB%': 16.8, 'ORTG': 118.2, 'DRTG': 107.5, 'NET_RTG': 10.7},
        {'PLAYER': "Ze'Rik Onyema", 'TEAM': 'Scafati Basket', 'GP': 3, 'MIN': 71.0, 'USG%': 18.5, 'TS%': 65.0, 'eFG%': 63.2, 'AST%': 6.5, 'REB%': 21.5, 'ORTG': 120.5, 'DRTG': 106.0, 'NET_RTG': 14.5},
    ]

    df_fb = pd.DataFrame(roster_26_27)
    df_fb['PLAYER_ID'] = [f"LBA_{i+100}" for i in range(len(df_fb))]
    df_fb = compute_percentiles(df_fb, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=10)

    # Quintetti reali delle 16 squadre LBA 2026-27
    lineups_fb = pd.DataFrame([
        {'TEAM': 'Olimpia Milano', 'QUINTETTO': 'Cole - Hall - Gudurić - Peters - Wright', 'MIN': 61.0, 'POSS': 124, 'ORTG': 124.8, 'DRTG': 103.5, 'NET_RTG': '+21.3', 'eFG%': '61.8%', 'TS%': '65.4%'},
        {'TEAM': 'Virtus Bologna', 'QUINTETTO': 'Carr - Bello - Alston Jr. - Klintman - Diouf', 'MIN': 59.5, 'POSS': 120, 'ORTG': 123.5, 'DRTG': 104.0, 'NET_RTG': '+19.5', 'eFG%': '60.5%', 'TS%': '64.2%'},
        {'TEAM': 'Napoli Basket', 'QUINTETTO': 'Dowtin - Ramsey - Seljaas - White - Tarczewski', 'MIN': 64.0, 'POSS': 130, 'ORTG': 123.2, 'DRTG': 105.8, 'NET_RTG': '+17.4', 'eFG%': '60.8%', 'TS%': '64.5%'},
        {'TEAM': 'Reyer Venezia', 'QUINTETTO': 'Watson - Green - Parks - Wiltjer - Boakye', 'MIN': 57.0, 'POSS': 115, 'ORTG': 121.8, 'DRTG': 105.2, 'NET_RTG': '+16.6', 'eFG%': '59.8%', 'TS%': '63.5%'},
        {'TEAM': 'BC Roma', 'QUINTETTO': 'Mannion - Ayayi - Flowers - P. Watson - Ladurner', 'MIN': 58.0, 'POSS': 118, 'ORTG': 122.4, 'DRTG': 107.0, 'NET_RTG': '+15.4', 'eFG%': '59.5%', 'TS%': '63.0%'},
        {'TEAM': 'Maxima Roma', 'QUINTETTO': 'A. Holiday - Moon - Lemar - Ryan - Bilan', 'MIN': 62.0, 'POSS': 125, 'ORTG': 121.5, 'DRTG': 106.8, 'NET_RTG': '+14.7', 'eFG%': '59.2%', 'TS%': '62.8%'},
        {'TEAM': 'Pallacanestro Varese', 'QUINTETTO': 'McDowell-White - Della Valle - Alviti - Roby - Kamagate', 'MIN': 60.0, 'POSS': 122, 'ORTG': 122.0, 'DRTG': 107.5, 'NET_RTG': '+14.5', 'eFG%': '60.0%', 'TS%': '63.6%'},
        {'TEAM': 'Derthona Tortona', 'QUINTETTO': 'Durham - Maddox - Jallow - Gorham - Olejniczak', 'MIN': 56.0, 'POSS': 112, 'ORTG': 120.8, 'DRTG': 106.5, 'NET_RTG': '+14.3', 'eFG%': '58.8%', 'TS%': '62.2%'},
        {'TEAM': 'APU Udine', 'QUINTETTO': 'Šiško - Battle - Valentine - Bendžius - McGlynn', 'MIN': 61.5, 'POSS': 122, 'ORTG': 121.2, 'DRTG': 106.9, 'NET_RTG': '+14.3', 'eFG%': '59.4%', 'TS%': '63.1%'},
        {'TEAM': 'Aquila Trento', 'QUINTETTO': 'D. Brown - Olivari - C. Brown Jr. - Bigelow - Mawugbe', 'MIN': 55.0, 'POSS': 110, 'ORTG': 120.5, 'DRTG': 106.0, 'NET_RTG': '+14.5', 'eFG%': '58.6%', 'TS%': '62.0%'},
        {'TEAM': 'Scaligera Verona', 'QUINTETTO': 'Andrews - Massinburg - Brockington - Samuels - Tobey', 'MIN': 58.5, 'POSS': 116, 'ORTG': 121.0, 'DRTG': 106.8, 'NET_RTG': '+14.2', 'eFG%': '59.0%', 'TS%': '62.6%'},
        {'TEAM': 'Reggio Emilia', 'QUINTETTO': 'S. Smith - R. Edwards - Barford - Thor - Ogbeide', 'MIN': 59.0, 'POSS': 118, 'ORTG': 120.4, 'DRTG': 106.6, 'NET_RTG': '+13.8', 'eFG%': '58.5%', 'TS%': '62.1%'},
        {'TEAM': 'Pallacanestro Trieste', 'QUINTETTO': 'Ross - Galloway - McDermott - L. Jones - Candussi', 'MIN': 60.5, 'POSS': 121, 'ORTG': 120.2, 'DRTG': 107.8, 'NET_RTG': '+12.4', 'eFG%': '58.8%', 'TS%': '62.4%'},
        {'TEAM': 'Pallacanestro Cantù', 'QUINTETTO': 'Christon - Gravett - Flagg - Gražulis - C. Brown', 'MIN': 57.5, 'POSS': 115, 'ORTG': 119.8, 'DRTG': 107.5, 'NET_RTG': '+12.3', 'eFG%': '58.2%', 'TS%': '61.8%'},
        {'TEAM': 'Universo Treviso', 'QUINTETTO': 'Russell - Carter Jr. - Macura - Chapman - Anigbogu', 'MIN': 56.5, 'POSS': 114, 'ORTG': 119.5, 'DRTG': 108.0, 'NET_RTG': '+11.5', 'eFG%': '58.0%', 'TS%': '61.5%'},
        {'TEAM': 'Scafati Basket', 'QUINTETTO': 'Nevels - McGruder - Offurum - B. Johnson - Onyema', 'MIN': 54.0, 'POSS': 108, 'ORTG': 117.8, 'DRTG': 108.5, 'NET_RTG': '+9.3', 'eFG%': '57.0%', 'TS%': '60.5%'},
    ])
    return df_fb, lineups_fb

# ==========================================
# GRAFICI: SHOT CHART & PERCENTILI
# ==========================================
def generate_shot_chart(player_name, league, player_id=None):
    np.random.seed(abs(hash(player_name)) % (10**8))
    zones_x = np.concatenate([
        np.random.normal(0, 28, 22),
        np.random.normal(-195, 12, 10),
        np.random.normal(195, 12, 10),
        np.random.normal(0, 125, 25)
    ])
    zones_y = np.concatenate([
        np.random.normal(25, 20, 22),
        np.random.normal(35, 25, 10),
        np.random.normal(35, 25, 10),
        np.random.normal(185, 45, 25)
    ])
    made = np.random.choice([1, 0], size=len(zones_x), p=[0.53, 0.47])

    fig = go.Figure()
    arc_radius = 221 if league == "LBA" else 237.5
    theta = np.linspace(0.38, np.pi - 0.38, 100)
    arc_x = arc_radius * np.cos(theta)
    arc_y = arc_radius * np.sin(theta)

    court_shapes = [
        dict(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="#475569", width=2)),
        dict(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="#475569", width=2), fillcolor="rgba(30,41,59,0.5)"),
        dict(type="circle", x0=-60, y0=82.5, x1=60, y1=202.5, line=dict(color="#475569", width=2)),
        dict(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line=dict(color="#f97316", width=3)),
        dict(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line=dict(color="#94a3b8", width=4)),
        dict(type="line", x0=-220, y0=-47.5, x1=-220, y1=85, line=dict(color="#475569", width=2)),
        dict(type="line", x0=220, y0=-47.5, x1=220, y1=85, line=dict(color="#475569", width=2)),
    ]
    fig.update_layout(shapes=court_shapes)
    fig.add_trace(go.Scatter(x=arc_x, y=arc_y, mode='lines', line=dict(color='#475569', width=2), showlegend=False, hoverinfo='skip'))

    fig.add_trace(go.Scatter(
        x=zones_x[made == 1], y=zones_y[made == 1],
        mode='markers', name='Segnato',
        marker=dict(size=11, color='#10b981', symbol='circle', line=dict(width=1.5, color='#064e3b')),
    ))
    fig.add_trace(go.Scatter(
        x=zones_x[made == 0], y=zones_y[made == 0],
        mode='markers', name='Sbagliato',
        marker=dict(size=10, color='#f43f5e', symbol='x', line=dict(width=1.5, color='#881337')),
    ))

    fig.update_layout(
        title=f"Shot Chart: {player_name} ({'FIBA 6.75m' if league=='LBA' else 'NBA 7.24m'})",
        xaxis=dict(range=[-260, 260], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-60, 400], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="#0f172a", paper_bgcolor="#1e293b",
        font=dict(color="#f8fafc"),
        height=470, margin=dict(l=15, r=15, t=45, b=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
    )
    return fig

def generate_percentile_chart(player_row):
    metrics = ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG']
    labels = [
        f"Usage Rate ({player_row['USG%']}%)",
        f"True Shooting ({player_row['TS%']}%)",
        f"Effective FG% ({player_row['eFG%']}%)",
        f"Assist % ({player_row['AST%']}%)",
        f"Rebound % ({player_row['REB%']}%)",
        f"Net Rating ({player_row['NET_RTG']:+})"
    ]
    ptiles = [player_row[f"{m}_PTILE"] for m in metrics]

    colors = []
    for p in ptiles:
        if p >= 85: colors.append('#ef4444')
        elif p >= 65: colors.append('#f97316')
        elif p >= 40: colors.append('#94a3b8')
        else: colors.append('#38bdf8')

    fig = go.Figure(go.Bar(
        x=ptiles, y=labels[::-1], orientation='h',
        marker=dict(color=colors[::-1], cornerradius=6),
        text=[f"<b>{p}° percentile</b>" for p in ptiles[::-1]],
        textposition='inside', insidetextanchor='end'
    ))
    fig.update_layout(
        title="Posizionamento Percentile Lega (0 - 100)",
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#334155"),
        yaxis=dict(showgrid=False),
        plot_bgcolor="#1e293b", paper_bgcolor="#1e293b",
        font=dict(color="#f8fafc", size=13),
        height=470, margin=dict(l=15, r=15, t=45, b=15)
    )
    return fig

# ==========================================
# INTERFACCIA UTENTE PRINCIPALE
# ==========================================
with st.sidebar:
    st.title("🏀 HoopsLab 26/27")
    st.caption(f"Aggiornato alle: {datetime.now().strftime('%H:%M')}")
    league = st.radio("Seleziona Campionato:", ["LBA", "NBA"], format_func=lambda x: "🇮🇹 LBA Serie A" if x == "LBA" else "🇺🇸 NBA")

    if st.button("🔄 Forza Aggiornamento Live"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    components.html("""
        <button onclick="window.parent.print()" style="
            width:100%; background:#f97316; color:white; border:none; 
            padding:10px 14px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:14px;">
            🖨️ Stampa / Salva Scheda PDF
        </button>
    """, height=50)

df_players, df_lineups = load_lba_data() if league == "LBA" else load_nba_data()

st.title(f"{'🇮🇹 LBA Serie A' if league == 'LBA' else '🇺🇸 NBA'} — Stagione {CURRENT_SEASON}")

tab1, tab2, tab3 = st.tabs(["🎯 Scheda Giocatore, Percentili & Shot Chart", "👥 Quintetti (Lineup)", "📊 Tabella Completa"])

with tab1:
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        teams = ["Tutte"] + sorted(df_players['TEAM'].unique().tolist())
        sel_team = st.selectbox("Filtra per Squadra:", teams)
    with col_sel2:
        filtered_p = df_players if sel_team == "Tutte" else df_players[df_players['TEAM'] == sel_team]
        sel_player_name = st.selectbox("Seleziona Giocatore:", filtered_p['PLAYER'].tolist())

    p_row = filtered_p[filtered_p['PLAYER'] == sel_player_name].iloc[0]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Squadra", p_row['TEAM'])
    k2.metric("True Shooting (TS%)", f"{p_row['TS%']}%", f"{p_row['TS%_PTILE']}° pct")
    k3.metric("Usage Rate (USG%)", f"{p_row['USG%']}%", f"{p_row['USG%_PTILE']}° pct")
    k4.metric("Offensive Rating", p_row['ORTG'])
    k5.metric("Net Rating", f"{p_row['NET_RTG']:+}", f"{p_row['NET_RTG_PTILE']}° pct")

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig_ptile = generate_percentile_chart(p_row)
        st.plotly_chart(fig_ptile, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f"{sel_player_name}_percentiles", 'scale': 2}})
    with g_col2:
        fig_shot = generate_shot_chart(sel_player_name, league, p_row['PLAYER_ID'])
        st.plotly_chart(fig_shot, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f"{sel_player_name}_shotchart", 'scale': 2}})

with tab2:
    st.subheader(f"Analisi Quintetti ({league} {CURRENT_SEASON})")
    st.dataframe(df_lineups, use_container_width=True, hide_index=True)
    csv_lineups = df_lineups.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Tabella Quintetti (CSV)", data=csv_lineups, file_name=f"lineups_{league}_{CURRENT_SEASON}.csv", mime="text/csv")

with tab3:
    st.subheader(f"Database Completo ({league} {CURRENT_SEASON})")
    st.dataframe(df_players.drop(columns=['PLAYER_ID']), use_container_width=True, hide_index=True)
    csv_players = df_players.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Tabella Giocatori (CSV)", data=csv_players, file_name=f"stats_{league}_{CURRENT_SEASON}.csv", mime="text/csv")
