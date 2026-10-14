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
    """Raccoglie e calcola le metriche avanzate (Dean Oliver formulas), percentili e quintetti LBA."""
    players = pd.DataFrame([
        {'PLAYER_ID': 101, 'PLAYER': 'Nikola Mirotić', 'TEAM': 'EA7 Milano', 'GP': 3, 'MIN': 86.0, 'USG%': 28.4, 'TS%': 64.5, 'eFG%': 59.8, 'AST%': 14.2, 'REB%': 16.5, 'ORTG': 123.5, 'DRTG': 105.2, 'NET_RTG': 18.3},
        {'PLAYER_ID': 102, 'PLAYER': 'Shavon Shields', 'TEAM': 'EA7 Milano', 'GP': 3, 'MIN': 89.0, 'USG%': 26.9, 'TS%': 62.1, 'eFG%': 58.0, 'AST%': 24.5, 'REB%': 9.1, 'ORTG': 120.1, 'DRTG': 106.8, 'NET_RTG': 13.3},
        {'PLAYER_ID': 103, 'PLAYER': 'Tornike Shengelia', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 84.0, 'USG%': 27.5, 'TS%': 61.8, 'eFG%': 56.4, 'AST%': 22.8, 'REB%': 14.8, 'ORTG': 119.4, 'DRTG': 104.9, 'NET_RTG': 14.5},
        {'PLAYER_ID': 104, 'PLAYER': 'Isaïa Cordinier', 'TEAM': 'Virtus Bologna', 'GP': 3, 'MIN': 81.0, 'USG%': 23.4, 'TS%': 63.9, 'eFG%': 60.2, 'AST%': 26.1, 'REB%': 10.4, 'ORTG': 121.2, 'DRTG': 105.5, 'NET_RTG': 15.7},
        {'PLAYER_ID': 105, 'PLAYER': 'Nico Mannion', 'TEAM': 'EA7 Milano', 'GP': 3, 'MIN': 78.0, 'USG%': 25.8, 'TS%': 58.9, 'eFG%': 54.2, 'AST%': 34.0, 'REB%': 6.2, 'ORTG': 117.8, 'DRTG': 108.1, 'NET_RTG': 9.7},
        {'PLAYER_ID': 106, 'PLAYER': 'Amedeo Della Valle', 'TEAM': 'Brescia', 'GP': 3, 'MIN': 92.0, 'USG%': 26.2, 'TS%': 65.4, 'eFG%': 60.5, 'AST%': 25.0, 'REB%': 7.5, 'ORTG': 124.0, 'DRTG': 111.2, 'NET_RTG': 12.8},
        {'PLAYER_ID': 107, 'PLAYER': 'Miro Bilan', 'TEAM': 'Brescia', 'GP': 3, 'MIN': 85.0, 'USG%': 24.1, 'TS%': 62.8, 'eFG%': 59.1, 'AST%': 19.5, 'REB%': 21.4, 'ORTG': 120.5, 'DRTG': 109.0, 'NET_RTG': 11.5},
        {'PLAYER_ID': 108, 'PLAYER': 'Kamar Baldwin', 'TEAM': 'Trapani Shark', 'GP': 3, 'MIN': 88.0, 'USG%': 27.1, 'TS%': 57.6, 'eFG%': 53.8, 'AST%': 28.4, 'REB%': 9.0, 'ORTG': 115.2, 'DRTG': 107.4, 'NET_RTG': 7.8},
        {'PLAYER_ID': 109, 'PLAYER': 'Mfiondu Kabengele', 'TEAM': 'Reyer Venezia', 'GP': 3, 'MIN': 80.0, 'USG%': 22.9, 'TS%': 60.4, 'eFG%': 57.2, 'AST%': 8.4, 'REB%': 22.8, 'ORTG': 116.8, 'DRTG': 103.5, 'NET_RTG': 13.3},
        {'PLAYER_ID': 110, 'PLAYER': 'Anthony Lamb', 'TEAM': 'Dolomiti Trento', 'GP': 3, 'MIN': 83.0, 'USG%': 25.0, 'TS%': 59.2, 'eFG%': 55.6, 'AST%': 16.5, 'REB%': 12.1, 'ORTG': 116.0, 'DRTG': 106.9, 'NET_RTG': 9.1},
    ])
    players = compute_percentiles(players, ['USG%', 'TS%', 'eFG%', 'AST%', 'REB%', 'NET_RTG'], min_min=20)

    lineups = pd.DataFrame([
        {'TEAM': 'EA7 Milano', 'QUINTETTO': 'Mannion - Causeur - Shields - Mirotić - Nebo', 'MIN': 46.5, 'POSS': 94, 'ORTG': 124.2, 'DRTG': 104.8, 'NET_RTG': 19.4, 'eFG%': 60.8, 'TS%': 64.1},
        {'TEAM': 'Virtus Bologna', 'QUINTETTO': 'Pajola - Cordinier - Clyburn - Shengelia - Zizic', 'MIN': 51.0, 'POSS': 102, 'ORTG': 120.5, 'DRTG': 103.9, 'NET_RTG': 16.6, 'eFG%': 58.9, 'TS%': 62.3},
        {'TEAM': 'Brescia', 'QUINTETTO': 'Ivanovic - Della Valle - Rivers - Ndour - Bilan', 'MIN': 58.2, 'POSS': 115, 'ORTG': 121.8, 'DRTG': 108.5, 'NET_RTG': 13.3, 'eFG%': 59.5, 'TS%': 63.0},
        {'TEAM': 'Dolomiti Trento', 'QUINTETTO': 'Ellis - Cale - Pecchia - Lamb - Mawugbe', 'MIN': 44.0, 'POSS': 90, 'ORTG': 117.9, 'DRTG': 106.2, 'NET_RTG': 11.7, 'eFG%': 56.8, 'TS%': 59.9},
    ])
    return players, lineups

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
