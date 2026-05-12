import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- LADY VOL STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F0F2F6; padding: 20px; border-radius: 15px; border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 120px; height: 120px; object-fit: cover; border: 3px solid #4895DB; }
    .stTable { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING (REUSE PREVIOUS LOAD LOGIC) ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        def clean_df(df):
            df.columns = df.columns.str.strip()
            n_col = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in df.columns), None)
            if n_col: df['Player_Match'] = df[n_col].astype(str).str.strip().str.upper()
            d_col = next((c for c in ['Date', 'Test Date'] if c in df.columns), None)
            if d_col: df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
            return df

        return clean_df(ash_df), clean_df(cmj_df), clean_df(roster_df)
    except Exception:
        return [pd.DataFrame()]*3

ash_df, cmj_df, roster_df = load_all_data()

# --- TOP ROW FILTERS ---
st.title("🥎 Performance Hub")
f1, f2 = st.columns(2)
with f1:
    selected = st.selectbox("Search Athlete", sorted(ash_df['Player_Match'].unique()) if not ash_df.empty else [])
with f2:
    years = sorted(ash_df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True) if not ash_df.empty else []
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- FILTERING ---
def filter_data(df, athlete, year):
    if df.empty: return df
    temp = df[df['Player_Match'] == athlete].copy()
    if year != "All Time": temp = temp[temp['Parsed_Date'].dt.year == year]
    return temp.sort_values('Parsed_Date')

ash_f = filter_data(ash_df, selected, sel_year)
cmj_f = filter_data(cmj_df, selected, sel_year)

# --- HEADER ---
photo = roster_df[roster_df['Player_Match'] == selected]['Picture'].values[0] if not roster_df.empty else "https://www.w3schools.com/howto/img_avatar.png"
st.markdown(f'<div class="athlete-header"><div style="display: flex; align-items: center;"><img src="{photo}" class="player-photo"><div style="margin-left: 25px;"><h1 style="margin:0;">{selected}</h1><p style="color:#4895DB; font-weight:700; margin:0;">LADY VOL PERFORMANCE</p></div></div></div>', unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH PROFILE", "🚀 CMJ RECOVERY"])

# --- TAB 1: ASH ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        c2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        c3.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(ash_f['Parsed_Date'], ash_f['Peak Vertical Force [N]'], color='#FF8200', marker='o', linewidth=3, markersize=8)
        
        # Clean Styling
        ax.set_facecolor('none')
        for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=0)
        
        st.pyplot(fig)

# --- TAB 2: CMJ (CLEAN DUAL AXIS) ---
with tab_cmj:
    h_col = next((c for c in cmj_f.columns if 'height' in c.lower()), None)
    r_col = next((c for c in cmj_f.columns if 'rsi' in c.lower()), None)
    
    if not cmj_f.empty and h_col and r_col:
        fig, ax1 = plt.subplots(figsize=(12, 5))
        
        # Plot Height
        ax1.plot(cmj_f['Parsed_Date'], cmj_f[h_col], color='#4895DB', marker='o', linewidth=3, label="Jump Height")
        ax1.set_ylabel('Height (cm)', color='#4895DB', fontweight='bold', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='#4895DB')
        
        # Plot RSI
        ax2 = ax1.twinx()
        ax2.plot(cmj_f['Parsed_Date'], cmj_f[r_col], color='#FF8200', marker='s', linestyle='--', linewidth=2, label="RSI")
        ax2.set_ylabel('RSI-mod', color='#FF8200', fontweight='bold', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='#FF8200')
        
        # Baseline
        base_val = float(cmj_f.iloc[0][h_col])
        ax1.axhline(y=base_val, color='#dc3545', linestyle=':', alpha=0.8, label="Baseline")
        
        # Axis cleanup
        ax1.set_facecolor('none')
        ax1.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        fig.tight_layout()
        st.pyplot(fig)
        
        # Data Table for quick reference
        st.markdown("### 📊 Session History")
        table_data = cmj_f[['Parsed_Date', h_col, r_col]].copy()
        table_data['Date'] = table_data['Parsed_Date'].dt.strftime('%m/%d/%Y')
        st.dataframe(table_data[['Date', h_col, r_col]], hide_index=True, use_container_width=True)
    else:
        st.info("No CMJ sessions found for the selected athlete/season.")
