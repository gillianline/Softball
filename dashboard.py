import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- LADY VOL STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 120px; height: 120px; object-fit: cover; border: 3px solid #4895DB; }
    .chart-container { background-color: #FFFFFF; padding: 15px; border-radius: 10px; border: 1px solid #E1E4E8; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        ash = pd.read_csv(st.secrets["ASH_URL"])
        cmj = pd.read_csv(st.secrets["CMJ_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        
        def clean(df):
            df.columns = df.columns.str.strip()
            # Dynamic Name & Date Find
            n_col = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in df.columns), None)
            d_col = next((c for c in ['Date', 'Test Date'] if c in df.columns), None)
            if n_col: df['Player_Match'] = df[n_col].astype(str).str.strip().str.upper()
            if d_col: df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
            return df
        return clean(ash), clean(cmj), clean(roster)
    except: return [pd.DataFrame()]*3

ash_df, cmj_df, roster_df = load_all_data()

# --- TOP FILTERS ---
st.title("🥎 Lady Vol Performance")
f1, f2 = st.columns(2)
with f1:
    athlete_list = sorted(ash_df['Player_Match'].unique()) if not ash_df.empty else []
    selected = st.selectbox("Select Athlete", athlete_list)
with f2:
    years = sorted(ash_df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True) if not ash_df.empty else []
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- DATA FILTERING ---
def filter_df(df, athlete, year):
    if df.empty: return df
    temp = df[df['Player_Match'] == athlete].copy()
    if year != "All Time": temp = temp[temp['Parsed_Date'].dt.year == year]
    return temp.sort_values('Parsed_Date')

ash_f = filter_df(ash_df, selected, sel_year)
cmj_f = filter_df(cmj_df, selected, sel_year)

# --- HEADER ---
photo = roster_df[roster_df['Player_Match'] == selected]['Picture'].values[0] if not roster_df.empty else "https://www.w3schools.com/howto/img_avatar.png"
st.markdown(f'<div class="athlete-header"><div style="display: flex; align-items: center;"><img src="{photo}" class="player-photo"><div style="margin-left: 25px;"><h1 style="margin:0;">{selected}</h1><p style="color:#4895DB; font-weight:700; margin:0;">SOFTBALL PERFORMANCE</p></div></div></div>', unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH PROFILE", "🚀 CMJ RECOVERY"])

with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        c2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        c3.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        fig_ash = px.line(ash_f, x='Parsed_Date', y='Peak Vertical Force [N]', markers=True, color_discrete_sequence=['#FF8200'])
        fig_ash.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Force (N)", height=350)
        st.plotly_chart(fig_ash, use_container_width=True)

with tab_cmj:
    h_col = next((c for c in cmj_f.columns if 'height' in c.lower()), None)
    r_col = next((c for c in cmj_f.columns if 'rsi' in c.lower()), None)
    
    if not cmj_f.empty and h_col and r_col:
        # Stacked Charts (Prevents Python 3.14 Dual-Axis Crash)
        st.markdown("### Jump Performance & RSI Readiness")
        
        # 1. Height Chart
        fig_h = px.line(cmj_f, x='Parsed_Date', y=h_col, markers=True, title="Jump Height (cm)", color_discrete_sequence=['#4895DB'])
        fig_h.update_layout(template="plotly_white", height=300, xaxis_title="", yaxis_title="cm")
        # Add red baseline
        fig_h.add_hline(y=float(cmj_f.iloc[0][h_col]), line_dash="dash", line_color="red")
        st.plotly_chart(fig_h, use_container_width=True)
        
        # 2. RSI Chart
        fig_r = px.line(cmj_f, x='Parsed_Date', y=r_col, markers=True, title="RSI Modified", color_discrete_sequence=['#FF8200'])
        fig_r.update_layout(template="plotly_white", height=300, xaxis_title="Date", yaxis_title="RSI-mod")
        st.plotly_chart(fig_r, use_container_width=True)
        
        # History Table
        st.markdown("### 📋 Session Logs")
        st.dataframe(cmj_f[['Parsed_Date', h_col, r_col]].rename(columns={'Parsed_Date': 'Date'}), hide_index=True, use_container_width=True)
    else:
        st.info("No CMJ data available for this selection.")
