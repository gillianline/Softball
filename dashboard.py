import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# Lady Vol Visuals
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F0F2F6; padding: 20px; border-radius: 15px; 
        border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 120px; height: 120px; object-fit: cover; border: 3px solid #4895DB; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
@st.cache_data(ttl=300)
def load_ash_data():
    try:
        # Load the ASH sheet and Roster
        df = pd.read_csv(st.secrets["ASH_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        
        # Standardize Columns (Strip spaces, etc)
        df.columns = df.columns.str.strip()
        roster.columns = roster.columns.str.strip()
        
        # Clean Dates: Find any column with "date" in it
        d_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if d_col:
            df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
        
        # Clean Names: Find any column with "name" or "athlete" in it
        n_col = next((c for c in df.columns if 'name' in c.lower() or 'athlete' in c.lower()), None)
        if n_col:
            df['Athlete_Name'] = df[n_col].astype(str).str.strip()
            roster['Athlete_Name'] = roster[n_col].astype(str).str.strip()
            
        return df, roster
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, roster = load_ash_data()

# --- 3. MAIN PAGE FILTERS ---
st.title("🥎 Lady Vol Performance")

if not df.empty:
    f1, f2 = st.columns(2)
    with f1:
        selected_athlete = st.selectbox("Search Athlete", sorted(df['Athlete_Name'].unique()))
    with f2:
        years = sorted(df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True)
        sel_year = st.selectbox("Select Season", ["All Time"] + years)

    # Filtering Logic
    ash_f = df[df['Athlete_Name'] == selected_athlete].copy()
    if sel_year != "All Time":
        ash_f = ash_f[ash_f['Parsed_Date'].dt.year == sel_year]
    ash_f = ash_f.sort_values('Parsed_Date')

    # --- 4. ATHLETE HEADER ---
    pic_row = roster[roster['Athlete_Name'] == selected_athlete]
    photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in pic_row.columns else "https://www.w3schools.com/howto/img_avatar.png"

    st.markdown(f"""
        <div class="athlete-header">
            <div style="display: flex; align-items: center;">
                <img src="{photo}" class="player-photo">
                <div style="margin-left: 25px;">
                    <h1 style="margin:0;">{selected_athlete}</h1>
                    <p style="color:#4895DB; font-weight:700; margin:0;">SOFTBALL PERFORMANCE | ASH TEST PROFILE</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. ASH TEST CONTENT ---
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        m3.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        # Trend Chart (Clean Matplotlib Look)
        st.write("")
        st.markdown("#### Peak Force Trend")
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ax.plot(ash_f['Parsed_Date'], ash_f['Peak Vertical Force [N]'], 
                color='#FF8200', marker='o', linewidth=3, markersize=8)
        
        # Styling to match a dashboard
        ax.set_facecolor('none')
        for spine in ['top', 'right']: ax.spines[spine].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=0)
        
        st.pyplot(fig)
        
        # Session History Table
        st.markdown("#### Session History")
        history_df = ash_f[['Parsed_Date', 'Peak Vertical Force [N]', 'RFD - 200ms [N/s]']].copy()
        history_df['Date'] = history_df['Parsed_Date'].dt.strftime('%m/%d/%Y')
        st.dataframe(history_df[['Date', 'Peak Vertical Force [N]', 'RFD - 200ms [N/s]']], 
                     hide_index=True, use_container_width=True)
    else:
        st.warning("No ASH data found for this selection.")
else:
    st.info("Please ensure ASH_URL and ROSTER_URL are set in your Secrets.")
