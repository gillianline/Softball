import streamlit as st
import pandas as pd

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

# --- UTILITY: DYNAMIC COLUMN FINDER ---
def find_col(df, options):
    return next((c for c in options if c in df.columns), None)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data():
    try:
        ash = pd.read_csv(st.secrets["ASH_URL"])
        cmj = pd.read_csv(st.secrets["CMJ_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        
        # Immediate Header and Data Cleaning
        for df in [ash, cmj, roster]:
            df.columns = df.columns.str.strip()
            # Standardize names to uppercase and strip whitespace
            n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
            if n_col:
                df[n_col] = df[n_col].astype(str).str.strip().str.upper()
            # Standardize Dates
            d_col = find_col(df, ['Date', 'Test Date', 'date'])
            if d_col:
                df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
                
        return ash, cmj, roster
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*3

ash_df, cmj_df, roster_df = load_data()

# --- MAIN PAGE FILTERS ---
f1, f2 = st.columns(2)

with f1:
    n_col_main = find_col(ash_df, ['Player Name', 'Athlete', 'Name', 'Player'])
    athlete_list = sorted(ash_df[n_col_main].unique()) if n_col_main else []
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    all_years = sorted(ash_df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + all_years)

# --- GLOBAL FILTERING ---
def filter_season(df, athlete, year):
    n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
    temp = df[df[n_col] == athlete].copy()
    if year != "All Time":
        temp = temp[temp['Parsed_Date'].dt.year == year]
    return temp.sort_values('Parsed_Date')

ash_f = filter_season(ash_df, selected, sel_year)
cmj_f = filter_season(cmj_df, selected, sel_year)

# --- HEADER ---
r_name = find_col(roster_df, ['Player Name', 'Athlete', 'Name', 'Player'])
pic_row = roster_df[roster_df[r_name] == selected] if r_name else pd.DataFrame()
photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in pic_row.columns else "https://www.w3schools.com/howto/img_avatar.png"

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

# --- TAB 1: ASH PROFILE ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2 = st.columns(2)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        
        # Using Streamlit Native Chart (Crash-proof, formatting-proof)
        chart_data = ash_f.set_index('Parsed_Date')[['Peak Vertical Force [N]']]
        st.line_chart(chart_data, color="#FF8200")
    else:
        st.warning("No ASH data found for selection.")

# --- TAB 2: CMJ RECOVERY ---
with tab_cmj:
    h_col = find_col(cmj_f, ['Jump Height (Imp-Mom) [cm]', 'Jump Height'])
    r_col = find_col(cmj_f, ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI'])
    
    if not cmj_f.empty and h_col and r_col:
        st.markdown("#### Jump Height & RSI Trends")
        
        # Dual axis is what keeps crashing/failing in 3.14. 
        # For maximum stability, we show them as two synced charts or a combined normalized chart.
        # Here we use two charts stacked to ensure they ALWAYS render.
        
        c_data = cmj_f.set_index('Parsed_Date')[[h_col, r_col]]
        
        st.write("Jump Height (cm)")
        st.line_chart(c_data[[h_col]], color="#FF8200")
        
        st.write("RSI Modified")
        st.line_chart(c_data[[r_col]], color="#4895DB")
        
        # History Table
        st.markdown("#### History Table")
        table_df = cmj_f[['Parsed_Date', h_col, r_col]].copy()
        table_df['Date'] = table_df['Parsed_Date'].dt.strftime('%m/%d/%Y')
        st.dataframe(table_df[['Date', h_col, r_col]], use_container_width=True, hide_index=True)
    else:
        st.warning("No CMJ data found for selection.")
