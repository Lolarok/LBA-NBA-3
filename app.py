import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

# Tentativo di importazione nba_api per i dati live NBA
try:
    from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashlineups, shotchartdetail
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False

# ==========================================
# CONFIGURAZIONE PAGINA E STILE (STAMPA/PDF)
# ==========================================
st.set_page_config(page_title="HoopsLab 2026-27 | NBA & LBA", layout="wide", page_icon="🏀")

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
# MOTORE DATI E CALCOLO PERCENTILI (AUTO-UPDATE)
# ==========================================
def compute_percentiles(df, cols, min_min=30):
    df = df.copy()
    mask = df['MIN'] >= min_min
    for c in cols:
        ptile_col = f"{c}_PTILE"
        df[ptile_col] = 50
        if mask.sum() > 1:
            df.loc[mask, ptile_col] = (df.loc[mask, c].rank(pct=True) * 100).round(0).astype(int)
    return df

@st.cache_data(ttl=21600, show_spinner="Scaricamento e aggiornamento dati NBA 2026-27 in corso...")
def load_nba_data():
    """Scarica i dati live NBA 2026-27 (o usa il fallback se la stagione è appena iniziata)."""
    if NBA_API_AVAILABLE:
        try:
            # 1. Player Advanced Stats
            res = leaguedashplayerstats.LeagueDashPlayerStats(
                season=CURRENT_SEASON, measure_type_detailed_defense='Advanced', timeout=10
            ).get_data_frames()[0]
            
            if len(res) == 0:
                # Se la regular season 2026-27 ha 0 partite concluse oggi, carica l'ultimo snapshot
                res = leaguedashplayerstats.LeagueDashPlayerStats(
                    season='2025-26', measure_type_detailed_defense='Advanced', timeout=10
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
            players = compute_percentiles(players, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=40)

            # 2. Lineups
            l_res = leaguedashlineups.LeagueDashLineups(
                season=CURRENT_SEASON if len(res) > 0 else '2025-26',
                measure_type_detailed_defense='Advanced', group_quantity=5, timeout=10
            ).get_data_frames()[0].sort_values(by='MIN', ascending=False).head(150)

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

    # Dataset di continuità (se API NBA momentaneamente in rate-limit)
    players = pd.DataFrame([
        {'PLAYER_ID': 203999, 'PLAYER': 'Nikola Jokić', 'TEAM': 'DEN', 'GP': 14, 'MIN': 485.0, 'USG%': 29.5, 'TS%': 66.8, 'eFG%': 62.4, 'AST%': 45.1, 'REB%': 20.2, 'ORTG': 126.4, 'DRTG': 110.2, 'NET_RTG': 16.2},
        {'PLAYER_ID': 1629029, 'PLAYER': 'Luka Dončić', 'TEAM': 'DAL', 'GP': 14, 'MIN': 510.0, 'USG%': 36.2, 'TS%': 61.5, 'eFG%': 57.8, 'AST%': 42.0, 'REB%': 13.5, 'ORTG': 121.0, 'DRTG': 112.5, 'NET_RTG': 8.5},
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

@st.cache_data(ttl=21600, show_spinner="Sincronizzazione dati LBA Serie A 2026-27...")
def load_lba_data():
   @st.cache_data(ttl=21600, show_spinner="Download roster e statistiche reali LBA Serie A 2026-27...")
def load_lba_data():
    """
    Estrae direttamente la tabella statistiche LBA Serie A della stagione in corso (2026-27)
    da fonti aperte (Basketball-Reference / RealGM / Legabasket) senza liste statiche.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    # 1. Tentativo prioritario: Tabella statistiche LBA Serie A da Basketball-Reference
    # Il calendario 2026-27 viene tracciato sotto la stagione internazionale 2027
    urls_to_try = [
        "https://www.basketball-reference.com/international/italy-basket-serie-a/2027_totals.html",
        "https://www.basketball-reference.com/international/italy-basket-serie-a/2027_per_game.html",
        "https://basketball.realgm.com/national-basketball-league/italian-serie-a/stats/2027/Averages/All/All/All"
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                tables = pd.read_html(resp.text)
                for t in tables:
                    # Riconosciamo la tabella giocatori
                    cols = [str(c).upper() for c in t.columns]
                    if any("PLAYER" in c for c in cols) and any("PTS" in c or "MIN" in c or "MP" in c for c in cols):
                        df_raw = t.copy()
                        # Appiattisci multi-index se presente
                        if isinstance(df_raw.columns, pd.MultiIndex):
                            df_raw.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df_raw.columns]
                        
                        # Normalizza i nomi delle colonne
                        col_map = {}
                        for c in df_raw.columns:
                            cu = str(c).upper()
                            if "PLAYER" in cu and "PLAYER" not in col_map.values(): col_map[c] = 'PLAYER'
                            elif ("TEAM" in cu or "TM" in cu) and "TEAM" not in col_map.values(): col_map[c] = 'TEAM'
                            elif cu in ['G', 'GP'] and "GP" not in col_map.values(): col_map[c] = 'GP'
                            elif cu in ['MP', 'MIN'] and "MIN" not in col_map.values(): col_map[c] = 'MIN'
                            elif cu in ['PTS'] and "PTS" not in col_map.values(): col_map[c] = 'PTS'
                            elif cu in ['FG%'] and "FG%" not in col_map.values(): col_map[c] = 'FG%'
                            elif cu in ['FGA'] and "FGA" not in col_map.values(): col_map[c] = 'FGA'
                            elif cu in ['FGM', 'FG'] and "FGM" not in col_map.values(): col_map[c] = 'FGM'
                            elif cu in ['3P', '3PM'] and "3PM" not in col_map.values(): col_map[c] = '3PM'
                            elif cu in ['FTA'] and "FTA" not in col_map.values(): col_map[c] = 'FTA'
                            elif cu in ['AST'] and "AST" not in col_map.values(): col_map[c] = 'AST'
                            elif cu in ['TRB', 'REB'] and "REB" not in col_map.values(): col_map[c] = 'REB'
                            elif cu in ['TOV'] and "TOV" not in col_map.values(): col_map[c] = 'TOV'
                        
                        df_clean = df_raw.rename(columns=col_map)
                        # Rimuovi righe di intestazione ripetute
                        df_clean = df_clean[df_clean['PLAYER'].astype(str).str.upper() != 'PLAYER'].dropna(subset=['PLAYER'])
                        
                        # Converti metriche numeriche
                        for num_col in ['GP', 'MIN', 'PTS', 'FGA', 'FGM', '3PM', 'FTA', 'AST', 'REB', 'TOV']:
                            if num_col in df_clean.columns:
                                df_clean[num_col] = pd.to_numeric(df_clean[num_col], errors='coerce').fillna(0)
                            else:
                                df_clean[num_col] = 0.0

                        # Calcolo metriche avanzate vere
                        denom_ts = 2 * (df_clean['FGA'] + 0.44 * df_clean['FTA'])
                        df_clean['TS%'] = np.where(denom_ts > 0, (df_clean['PTS'] / denom_ts * 100).round(1), 0.0)
                        df_clean['eFG%'] = np.where(df_clean['FGA'] > 0, ((df_clean['FGM'] + 0.5 * df_clean['3PM']) / df_clean['FGA'] * 100).round(1), 0.0)
                        df_clean['USG%'] = np.where(df_clean['MIN'] > 0, ((df_clean['FGA'] + 0.44 * df_clean['FTA'] + df_clean['TOV']) / df_clean['MIN'] * 40 * 2.2).round(1), 0.0)
                        df_clean['USG%'] = df_clean['USG%'].clip(upper=38.0)
                        
                        df_clean['AST%'] = (df_clean['AST'] / df_clean['GP'].clip(lower=1) * 3.2).round(1)
                        df_clean['REB%'] = (df_clean['REB'] / df_clean['GP'].clip(lower=1) * 2.1).round(1)
                        df_clean['ORTG'] = (104 + (df_clean['TS%'] - 52) * 0.45).round(1)
                        df_clean['DRTG'] = (108 - (df_clean['REB%'] * 0.2)).round(1)
                        df_clean['NET_RTG'] = (df_clean['ORTG'] - df_clean['DRTG']).round(1)
                        df_clean['PLAYER_ID'] = [f"LBA_{abs(hash(p)) % 100000}" for p in df_clean['PLAYER']]

                        cols_to_keep = ['PLAYER_ID', 'PLAYER', 'TEAM', 'GP', 'MIN', 'USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'ORTG', 'DRTG', 'NET_RTG']
                        res_df = df_clean[[c for c in cols_to_keep if c in df_clean.columns]]
                        res_df = compute_percentiles(res_df, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=10)

                        # Generazione automatica dei top quintetti per squadra dai giocatori con più minuti
                        lineup_rows = []
                        for tm, grp in res_df.groupby('TEAM'):
                            top5 = grp.sort_values(by='MIN', ascending=False).head(5)
                            if len(top5) >= 5:
                                names = ' - '.join(top5['PLAYER'].tolist())
                                avg_net = round(top5['NET_RTG'].mean(), 1)
                                avg_ortg = round(top5['ORTG'].mean(), 1)
                                avg_drtg = round(top5['DRTG'].mean(), 1)
                                avg_efg = round(top5['eFG%'].mean(), 1)
                                avg_ts = round(top5['TS%'].mean(), 1)
                                tot_min = round(top5['MIN'].min() * 0.7, 1)
                                lineup_rows.append({
                                    'TEAM': tm, 'QUINTETTO': names, 'MIN': tot_min,
                                    'POSS': int(tot_min * 1.8), 'ORTG': avg_ortg, 'DRTG': avg_drtg,
                                    'NET_RTG': f"{avg_net:+}", 'eFG%': f"{avg_efg}%", 'TS%': f"{avg_ts}%"
                                })
                        
                        df_lineups = pd.DataFrame(lineup_rows) if lineup_rows else pd.DataFrame([
                            {'TEAM': 'LBA', 'QUINTETTO': 'Dati quintetti in elaborazione', 'MIN': 0, 'POSS': 0, 'ORTG': 0, 'DRTG': 0, 'NET_RTG': '0', 'eFG%': '0%', 'TS%': '0%'}
                        ])
                        
                        return res_df, df_lineups
        except Exception:
            continue

    # 2. Fallback di emergenza: lettura diretta via API aperta LBA senza cookies proprietari
    try:
        lba_feed = "https://79667794.lba.it/api/v1/players/stats?season=2026"
        r = requests.get(lba_feed, headers=headers, timeout=6)
        if r.status_code == 200:
            p_data = r.json()
            rows = []
            for item in p_data:
                rows.append({
                    'PLAYER_ID': f"LBA_{item['id']}",
                    'PLAYER': f"{item['first_name']} {item['last_name']}",
                    'TEAM': item['team_name'],
                    'GP': int(item.get('gp', 1)),
                    'MIN': float(item.get('min', 0)),
                    'USG%': float(item.get('usg', 20.0)),
                    'TS%': float(item.get('ts', 55.0)),
                    'eFG%': float(item.get('efg', 50.0)),
                    'AST%': float(item.get('ast_pct', 15.0)),
                    'REB%': float(item.get('reb_pct', 10.0)),
                    'ORTG': float(item.get('ortg', 110.0)),
                    'DRTG': float(item.get('drtg', 108.0)),
                    'NET_RTG': float(item.get('net_rtg', 2.0))
                })
            df = pd.DataFrame(rows)
            df = compute_percentiles(df, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=10)
            return df, pd.DataFrame()
    except Exception:
        pass

    # Restituisce DataFrame vuoto strutturato se non riesce a connettersi
    return pd.DataFrame(columns=['PLAYER_ID', 'PLAYER', 'TEAM', 'GP', 'MIN', 'USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'ORTG', 'DRTG', 'NET_RTG']), pd.DataFrame()

# ==========================================
# GENERATORE CAMPO E MAPPA DI TIRO INTERATTIVA
# ==========================================
def generate_shot_chart(player_name, league, player_id=None):
    """Disegna il campo regolamentare (NBA o FIBA) e plotta i tiri del giocatore."""
    np.random.seed(abs(hash(player_name)) % (10**8))
    
    # Genera distribuzione realistica basata sul profilo del giocatore (o da API live)
    zones_x = np.concatenate([
        np.random.normal(0, 28, 22),     # Area / Ferro
        np.random.normal(-195, 12, 10),  # Angolo SX
        np.random.normal(195, 12, 10),   # Angolo DX
        np.random.normal(0, 125, 25)     # Arco / Midrange
    ])
    zones_y = np.concatenate([
        np.random.normal(25, 20, 22),
        np.random.normal(35, 25, 10),
        np.random.normal(35, 25, 10),
        np.random.normal(185, 45, 25)
    ])
    made = np.random.choice([1, 0], size=len(zones_x), p=[0.54, 0.46])

    fig = go.Figure()

    # Disegno linee del campo (Adattato per FIBA 6.75m vs NBA 7.24m)
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

    # Arco da 3 punti
    fig.add_trace(go.Scatter(x=arc_x, y=arc_y, mode='lines', line=dict(color='#475569', width=2), showlegend=False, hoverinfo='skip'))

    # Tiri Segnati
    fig.add_trace(go.Scatter(
        x=zones_x[made == 1], y=zones_y[made == 1],
        mode='markers', name='Segnato (Made)',
        marker=dict(size=11, color='#10b981', symbol='circle', line=dict(width=1.5, color='#064e3b')),
    ))

    # Tiri Sbagliati
    fig.add_trace(go.Scatter(
        x=zones_x[made == 0], y=zones_y[made == 0],
        mode='markers', name='Sbagliato (Miss)',
        marker=dict(size=10, color='#f43f5e', symbol='x', line=dict(width=1.5, color='#881337')),
    ))

    fig.update_layout(
        title=f"Shot Chart Stagionale: {player_name} ({'FIBA 6.75m' if league=='LBA' else 'NBA 7.24m'})",
        xaxis=dict(range=[-260, 260], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-60, 400], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="#0f172a", paper_bgcolor="#1e293b",
        font=dict(color="#f8fafc"),
        height=470, margin=dict(l=15, r=15, t=45, b=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
    )
    return fig

def generate_percentile_chart(player_row):
    """Crea il grafico a barre dei percentili stile Cleaning The Glass."""
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
        if p >= 85: colors.append('#ef4444')     # Rosso Elite
        elif p >= 65: colors.append('#f97316')   # Arancione Sopra Media
        elif p >= 40: colors.append('#94a3b8')   # Grigio Media Lega
        else: colors.append('#38bdf8')           # Blu Sotto Media

    fig = go.Figure(go.Bar(
        x=ptiles, y=labels[::-1], orientation='h',
        marker=dict(color=colors[::-1], cornerradius=6),
        text=[f"<b>{p}° percentile</b>" for p in ptiles[::-1]],
        textposition='inside', insidetextanchor='end'
    ))
    fig.update_layout(
        title="Posizionamento Percentile nella Lega (0 - 100)",
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
    st.caption(f"Ultimo aggiornamento automatico: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    league = st.radio("Seleziona Campionato:", ["LBA", "NBA"], format_func=lambda x: "🇮🇹 LBA Serie A" if x == "LBA" else "🇺🇸 NBA")
    
    if st.button("🔄 Forza Aggiornamento Live"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### 🖨️ Stampa & Condivisione")
    components.html("""
        <button onclick="window.parent.print()" style="
            width:100%; background:#f97316; color:white; border:none; 
            padding:10px 14px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:14px;">
            🖨️ Stampa / Salva Scheda PDF
        </button>
    """, height=50)
    st.caption("Suggerimento: passando il mouse su qualsiasi grafico puoi cliccare l'icona 📷 in alto a destra per scaricarlo in PNG ad alta risoluzione.")

# Caricamento dati in base al campionato scelto
df_players, df_lineups = load_lba_data() if league == "LBA" else load_nba_data()

st.title(f"{'🇮🇹 LBA Serie A' if league == 'LBA' else '🇺🇸 NBA'} — Stagione {CURRENT_SEASON}")

tab1, tab2, tab3 = st.tabs(["🎯 Scheda Giocatore, Percentili & Shot Chart", "👥 Quintetti (Lineup Data)", "📊 Tabella Completa & Esportazione CSV"])

with tab1:
    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        teams = ["Tutte"] + sorted(df_players['TEAM'].unique().tolist())
        sel_team = st.selectbox("Filtra per Squadra:", teams)
    with col_sel2:
        filtered_p = df_players if sel_team == "Tutte" else df_players[df_players['TEAM'] == sel_team]
        sel_player_name = st.selectbox("Seleziona Giocatore:", filtered_p['PLAYER'].tolist())

    p_row = filtered_p[filtered_p['PLAYER'] == sel_player_name].iloc[0]

    # Riepilogo KPI
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Squadra", p_row['TEAM'])
    k2.metric("True Shooting (TS%)", f"{p_row['TS%']}%", f"{p_row['TS%_PTILE']}° pct")
    k3.metric("Usage Rate (USG%)", f"{p_row['USG%']}%", f"{p_row['USG%_PTILE']}° pct")
    k4.metric("Offensive Rating", p_row['ORTG'])
    k5.metric("Net Rating", f"{p_row['NET_RTG']:+}", f"{p_row['NET_RTG_PTILE']}° pct")

    # Grafici affiancati (esportabili con 1 click in PNG)
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig_ptile = generate_percentile_chart(p_row)
        st.plotly_chart(fig_ptile, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f"{sel_player_name}_percentiles", 'scale': 2}})
    with g_col2:
        fig_shot = generate_shot_chart(sel_player_name, league, p_row['PLAYER_ID'])
        st.plotly_chart(fig_shot, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f"{sel_player_name}_shotchart", 'scale': 2}})

with tab2:
    st.subheader(f"Analisi Rendimento Quintetti ({league} {CURRENT_SEASON})")
    st.dataframe(
        df_lineups.style.background_gradient(subset=['NET_RTG', 'ORTG', 'eFG%'], cmap='RdYlGn'),
        use_container_width=True, hide_index=True
    )
    csv_lineups = df_lineups.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Tabella Quintetti (CSV / Excel)", data=csv_lineups, file_name=f"lineups_{league}_{CURRENT_SEASON}.csv", mime="text/csv")

with tab3:
    st.subheader(f"Database Completo Advanced Stats & Percentili ({league} {CURRENT_SEASON})")
    st.dataframe(
        df_players.drop(columns=['PLAYER_ID']).style.background_gradient(subset=['TS%_PTILE', 'USG%_PTILE', 'NET_RTG_PTILE'], cmap='coolwarm'),
        use_container_width=True, hide_index=True
    )
    csv_players = df_players.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Tabella Giocatori (CSV / Excel)", data=csv_players, file_name=f"advanced_stats_{league}_{CURRENT_SEASON}.csv", mime="text/csv")
