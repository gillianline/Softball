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
    ash_df = pd.read_csv(st.secrets["ASH_URL"])
    cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
    roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
    for df in [ash_df, cmj_df, roster_df]:
        df.columns = df.columns.str.strip()
        d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), 'Date')
        df['Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
    return ash_df, cmj_df, roster_df

ash_df, cmj_df, roster_df = load_all_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Lady Vol Performance")
f1, f2 = st.columns(2)
with f1:
    selected = st.selectbox("Search Athlete", sorted(ash_df['Player Name'].unique()))
with f2:
    years = sorted(ash_df['Date'].dt.year.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- FILTERING ---
ash_f = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
cmj_f = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')
if sel_year != "All Time":
    ash_f = ash_f[ash_f['Date'].dt.year == sel_year]
    cmj_f = cmj_f[cmj_f['Date'].dt.year == sel_year]

# --- HEADER ---
pic_row = roster_df[roster_df['Player Name'] == selected]
photo = pic_row['Picture'].values[0] if not pic_row.empty else "https://www.w3schools.com/howto/img_avatar.png"
st.markdown(f'<div class="athlete-header"><div style="display: flex; align-items: center;"><img src="{photo}" class="player-photo"><div style="margin-left: 30px;"><h1 style="margin:0;">{selected}</h1><p style="color:#4895DB; font-weight:700; margin:0;">SOFTBALL PERFORMANCE</p></div></div></div>', unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

with tab_ash:
    if not ash_f.empty:
        st.metric("Peak Force", f"{int(ash_f.iloc[-1].get('Peak Vertical Force [N]', 0))} N")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(ash_f['Date'], ash_f['Peak Vertical Force [N]'], color='#FF8200', marker='o', linewidth=3)
        ax.set_facecolor('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        st.pyplot(fig)

with tab_cmj:
    h_col = next((c for c in cmj_f.columns if 'Height' in c), None)
    r_col = next((c for c in cmj_f.columns if 'RSI' in c), None)
    
    if not cmj_f.empty and h_col and r_col:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        # Primary Axis (Height - Blue)
        ax1.plot(cmj_f['Date'], cmj_f[h_col], color='#4895DB', marker='o', linewidth=3, label="Height")
        ax1.set_ylabel('Height (cm)', color='#4895DB', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#4895DB')
        
        # Secondary Axis (RSI - Orange)
        ax2 = ax1.twinx()
        ax2.plot(cmj_f['Date'], cmj_f[r_col], color='#FF8200', marker='s', linestyle='--', linewidth=2, label="RSI")
        ax2.set_ylabel('RSI-mod', color='#FF8200', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#FF8200')
        
        # Baseline (Red Dash)
        base_val = float(cmj_f.iloc[0][h_col])
        ax1.axhline(y=base_val, color='red', linestyle='--', alpha=0.6, label="Baseline")
        
        plt.title(f"CMJ Recovery Trend: {selected}", fontweight='bold')
        fig.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("Ensure 'Height' and 'RSI' columns exist in your CMJ sheet.")
