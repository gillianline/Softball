import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        # Load sheets
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        # Helper to clean and find columns
        def clean_df(df):
            df.columns = df.columns.str.strip()
            # Find Name Column
            n_col = next((c for c in ['Player Name', 'Athlete', 'Name', 'Player'] if c in df.columns), None)
            if n_col:
                df['Player_Match'] = df[n_col].astype(str).str.strip().str.upper()
            
            # Find Date Column - ONLY convert if it exists
            d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), None)
            if d_col:
                df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
            else:
                df['Parsed_Date'] = pd.Timestamp.now() # Fallback if no date exists
            return df

        return clean_df(ash_df), clean_df(cmj_df), clean_df(roster_df)
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return [pd.DataFrame()]*3

ash_df, cmj_df, roster_df = load_all_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Lady Vol Performance")
f1, f2 = st.columns(2)

with f1:
    # Use the normalized 'Player_Match' column for the list
    athlete_list = sorted(ash_df['Player_Match'].unique()) if not ash_df.empty else []
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    # Extract years safely
    if not ash_df.empty:
        years = sorted(ash_df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True)
        sel_year = st.selectbox("Select Season", ["All Time"] + years)
    else:
        sel_year = "All Time"

# --- FILTERING ---
def filter_data(df, athlete, year):
    if df.empty: return df
    temp = df[df['Player_Match'] == athlete].copy()
    if year != "All Time":
        temp = temp[temp['Parsed_Date'].dt.year == year]
    return temp.sort_values('Parsed_Date')

ash_f = filter_data(ash_df, selected, sel_year)
cmj_f = filter_data(cmj_df, selected, sel_year)

# --- HEADER ---
if not roster_df.empty:
    pic_row = roster_df[roster_df['Player_Match'] == selected]
    photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in pic_row.columns else "https://www.w3schools.com/howto/img_avatar.png"
else:
    photo = "https://www.w3schools.com/howto/img_avatar.png"

st.markdown(f"""
    <div class="athlete-header">
        <div style="display: flex; align-items: center;">
            <img src="{photo}" class="player-photo">
            <div style="margin-left: 30px;">
                <h1 style="margin:0;">{selected}</h1>
                <p style="color:#4895DB; font-weight:700; margin:0;">SOFTBALL PERFORMANCE DASHBOARD</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

# --- TAB 1: ASH ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        st.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(ash_f['Parsed_Date'], ash_f['Peak Vertical Force [N]'], color='#FF8200', marker='o', linewidth=3)
        ax.set_title("Peak Vertical Force Trend", color='#FF8200', fontweight='bold')
        ax.set_facecolor('#F8F9FA')
        fig.patch.set_facecolor('#FFFFFF')
        st.pyplot(fig)

# --- TAB 2: CMJ (MATPLOTLIB DUAL AXIS) ---
with tab_cmj:
    # Use keyword search for columns to avoid KeyErrors
    h_col = next((c for c in cmj_f.columns if 'height' in c.lower()), None)
    r_col = next((c for c in cmj_f.columns if 'rsi' in c.lower()), None)
    
    if not cmj_f.empty and h_col and r_col:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        # Height Axis (Blue)
        ax1.plot(cmj_f['Parsed_Date'], cmj_f[h_col], color='#4895DB', marker='o', linewidth=3, label="Jump Height")
        ax1.set_ylabel('Height (cm)', color='#4895DB', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#4895DB')
        
        # RSI Axis (Orange)
        ax2 = ax1.twinx()
        ax2.plot(cmj_f['Parsed_Date'], cmj_f[r_col], color='#FF8200', marker='s', linestyle='--', linewidth=2, label="RSI")
        ax2.set_ylabel('RSI-mod', color='#FF8200', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#FF8200')
        
        # Baseline
        base_val = float(cmj_f.iloc[0][h_col])
        ax1.axhline(y=base_val, color='red', linestyle=':', alpha=0.7, label="Baseline")
        
        fig.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No CMJ data found for this athlete.")
