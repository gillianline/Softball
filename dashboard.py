import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- LADY VOL STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    .stTabs [role="tab"] { font-weight: 800; color: #4895DB; font-size: 18px; }
    .stTabs [aria-selected="true"] { color: #FF8200; border-bottom-color: #FF8200; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px;}
    .scout-table th { background-color: #4895DB; color: white; padding: 8px; border-bottom: 2px solid #FF8200; text-transform: uppercase; font-size: 12px; }
    .scout-table td { padding: 8px; border-bottom: 1px solid #F5F5F7; font-size: 12px; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        # 1. Load Primary Sheets
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        # 2. Process CMJ (Hawkin Dynamics Logic)
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        cmj_df.columns = cmj_df.columns.str.strip()
        cmj_df['Test Date'] = pd.to_datetime(cmj_df['Test Date'], errors='coerce')
        
        # Numeric Cleaning for Hawkin Metrics
        hawkin_metrics = ['Jump Height (Imp-Mom) [cm]', 'RSI-modified [m/s]']
        for col in hawkin_metrics:
            if col in cmj_df.columns:
                cmj_df[col] = pd.to_numeric(
                    cmj_df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), 
                    errors='coerce'
                ).fillna(0).astype(float)

        # 3. Process ASH Headers & Dates
        ash_df.columns = ash_df.columns.str.strip()
        ash_df['Date'] = pd.to_datetime(ash_df['Date'], errors='coerce')

        # 4. Process Roster
        roster_df.columns = roster_df.columns.str.strip()
        
        return ash_df, cmj_df, roster_df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*3

# --- INITIALIZE ---
LOCKED_CONFIG = {'staticPlot': True, 'displayModeBar': False}
ash_df, cmj_df, roster_df = load_all_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Performance Hub")
f1, f2 = st.columns(2)

# Helper to find date column safely
def find_date_col(df):
    return next((c for c in ['Date', 'Test Date', 'date', 'test_date'] if c in df.columns), None)

with f1:
    athlete_list = sorted(ash_df['Player Name'].unique()) if 'Player Name' in ash_df.columns else []
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    # Safely find date columns for both dataframes
    ash_date_col = find_date_col(ash_df)
    cmj_date_col = find_date_col(cmj_df)
    
    # Only concat if the columns actually exist
    dates_to_concat = []
    if ash_date_col: dates_to_concat.append(ash_df[ash_date_col])
    if cmj_date_col: dates_to_concat.append(cmj_df[cmj_date_col])
    
    if dates_to_concat:
        all_dates = pd.concat(dates_to_concat)
        years = sorted(all_dates.dt.year.dropna().unique().astype(int), reverse=True)
    else:
        years = []
        
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- FILTERING LOGIC ---
def filter_data_robust(df, athlete, year):
    if df.empty: return df
    
    # Find athlete column
    name_col = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in df.columns), None)
    # Find date column
    date_col = find_date_col(df)
    
    if not name_col or not date_col:
        return pd.DataFrame() # Return empty if columns are missing

    temp = df[df[name_col] == athlete].copy()
    if year != "All Time":
        temp = temp[temp[date_col].dt.year == year]
    return temp.sort_values(date_col)

# Apply the robust filters
ash_f = filter_data_robust(ash_df, selected, sel_year)
cmj_f = filter_data_robust(cmj_df, selected, sel_year)

# --- HEADER ---
pic_row = roster_df[roster_df['Player Name'] == selected]
photo = pic_row['Picture'].values[0] if not pic_row.empty else "https://www.w3schools.com/howto/img_avatar.png"

st.markdown(f"""
    <div class="athlete-header">
        <div style="display: flex; align-items: center;">
            <img src="{photo}" class="player-photo">
            <div style="margin-left: 30px;">
                <h1 style="margin:0;">{selected}</h1>
                <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">SOFTBALL PERFORMANCE DASHBOARD</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

# --- TAB 1: ASH ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        m3.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        # Single Axis Chart
        fig_ash = go.Figure(data=[
            go.Scatter(x=ash_f['Date'], y=ash_f['Peak Vertical Force [N]'], 
                       mode='lines+markers', line=dict(color="#FF8200", width=3))
        ])
        fig_ash.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20), height=350)
        st.plotly_chart(fig_ash, use_container_width=True, config=LOCKED_CONFIG)
    else:
        st.warning("No ASH data found.")

# --- TAB 2: CMJ (VOLLEYBALL DUAL-AXIS LOGIC) ---
with tab_cmj:
    h_col = 'Jump Height (Imp-Mom) [cm]'
    r_col = 'RSI-modified [m/s]'

    if not cmj_f.empty:
        # BYPASS DICTIONARY: Prevents Python 3.14 validation crash for dual-axis
        dual_axis_dict = {
            "data": [
                {
                    "x": cmj_f['Test Date'].dt.strftime('%Y-%m-%d').tolist(),
                    "y": cmj_f[h_col].tolist(),
                    "name": "Jump Height (cm)", "type": "scatter", "mode": "lines+markers",
                    "line": {"color": "#FF8200", "width": 3}
                },
                {
                    "x": cmj_f['Test Date'].dt.strftime('%Y-%m-%d').tolist(),
                    "y": cmj_f[r_col].tolist(),
                    "name": "RSI-mod", "type": "scatter", "mode": "lines+markers",
                    "yaxis": "y2", "line": {"color": "#4895DB", "width": 2, "dash": "dot"}
                }
            ],
            "layout": {
                "template": "plotly_white",
                "height": 450,
                "legend": {"orientation": "h", "y": 1.15, "x": 0.5, "xanchor": "center"},
                "xaxis": {"showgrid": False, "title": "Date"},
                "yaxis": {
                    "title": "Jump Height (cm)", "titlefont": {"color": "#FF8200"}, "tickfont": {"color": "#FF8200"},
                    "showgrid": True
                },
                "yaxis2": {
                    "title": "RSI-mod", "titlefont": {"color": "#4895DB"}, "tickfont": {"color": "#4895DB"}, 
                    "overlaying": "y", "side": "right", "showgrid": False
                },
                "margin": {"l": 50, "r": 50, "t": 60, "b": 40}
            }
        }
        
        st.plotly_chart(dual_axis_dict, use_container_width=True, theme=None, config=LOCKED_CONFIG)
        
        # Session History Table
        st.markdown("#### 📋 Session History")
        st.dataframe(
            cmj_f[['Test Date', h_col, r_col]].rename(columns={'Test Date': 'Date'}), 
            hide_index=True, use_container_width=True
        )
    else:
        st.info("No CMJ sessions found for this selection.")
