import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball ASH Performance", layout="wide")

# --- CUSTOM SCOUT CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #FF8200;
        margin-bottom: 25px;
    }
    .player-photo {
        border-radius: 50%;
        width: 150px;
        height: 150px;
        object-fit: cover;
        border: 4px solid #4895DB;
    }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD GATE ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col2, _ = st.columns([1,1,1])
    with col2:
        st.title("🔐 Performance Access")
        pwd = st.text_input("Enter Key", type="password")
        if st.button("Login"):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- DATA LOADING (ASH + ROSTER) ---
@st.cache_data(ttl=300)
def load_performance_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        ash_df.columns = ash_df.columns.str.strip()
        roster_df.columns = roster_df.columns.str.strip()
        
        # Numeric Sanitizer
        num_cols = ['Peak Vertical Force [N]', 'RFD - 200ms [N/s]', 'Start Time to Peak Force [s]']
        for col in ash_df.columns:
            if any(m in col for m in num_cols) or 'Asym' in col:
                ash_df[col] = pd.to_numeric(ash_df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        
        df = ash_df.merge(roster_df[['Player Name', 'Picture']], on='Player Name', how='left')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return pd.DataFrame()

df = load_performance_data()

# --- DASHBOARD UI ---
if not df.empty:
    # Top Level Filters
    filt_col1, filt_col2 = st.columns(2)
    
    with filt_col1:
        athlete_list = sorted(df['Player Name'].unique())
        selected = st.selectbox("Search Athlete", athlete_list)
    
    # Filter data for selected athlete to populate years
    p_athlete_data = df[df['Player Name'] == selected].sort_values('Date')
    
    with filt_col2:
        # Extract years from the athlete's specific data
        available_years = sorted(p_athlete_data['Date'].dt.year.dropna().unique().astype(int), reverse=True)
        selected_year = st.selectbox("Select Season", ["All Time"] + available_years)

    # Apply Year Filter
    if selected_year == "All Time":
        p_filtered = p_athlete_data
    else:
        p_filtered = p_athlete_data[p_athlete_data['Date'].dt.year == selected_year]

    if not p_filtered.empty:
        p_latest = p_filtered.iloc[-1]

        # Athlete Header Card
        st.markdown(f"""
            <div class="athlete-header">
                <div style="display: flex; align-items: center;">
                    <img src="{p_latest.get('Picture', 'https://www.w3schools.com/howto/img_avatar.png')}" class="player-photo">
                    <div style="margin-left: 30px;">
                        <h1 style="margin:0;">{selected}</h1>
                        <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">ASH TEST PROFILE</p>
                        <p style="color:#8E8E93; margin:0;">Latest Test: {p_latest['Date'].strftime('%m/%d/%Y') if pd.notnull(p_latest['Date']) else 'N/A'}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Metric Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peak Force", f"{int(p_latest['Peak Vertical Force [N]'])} N")
        m2.metric("RFD (200ms)", f"{int(p_latest['RFD - 200ms [N/s]'])} N/s")
        
        asym = p_latest.get('Peak Vertical Force [N] (Asym)(%)', 0)
        m3.metric("Force Asymmetry", f"{asym}%", delta="- Injury Risk" if asym > 10 else None, delta_color="inverse")
        
        m4.metric("Time to Peak", f"{p_latest.get('Start Time to Peak Force [s]', 0)}s")

        st.divider()

        # Visualizations
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader(f"Force Trend ({selected_year})")
            if len(p_filtered) > 1:
                fig_trend = px.line(p_filtered, x='Date', y='Peak Vertical Force [N]', 
                                    markers=True, template="plotly_white", color_discrete_sequence=["#FF8200"])
                # Ensure the x-axis shows proper dates even if filtered
                fig_trend.update_xaxes(dtick="M1", tickformat="%b %d\n%Y")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Additional test dates in this range required for trend lines.")

        with col_right:
            st.subheader("Side-by-Side Comparison")
            l_force = p_latest.get('Peak Vertical Force [N] (L)', 0)
            r_force = p_latest.get('Peak Vertical Force [N] (R)', 0)
            
            side_df = pd.DataFrame({
                'Side': ['Left', 'Right'],
                'Force [N]': [l_force, r_force]
            })
            
            fig_side = px.bar(side_df, x='Side', y='Force [N]', 
                              color='Side', color_discrete_map={'Left': '#4895DB', 'Right': '#FF8200'},
                              template="plotly_white")
            st.plotly_chart(fig_side, use_container_width=True)
            
    else:
        st.warning(f"No data found for {selected} in {selected_year}.")

else:
    st.warning("Data load failed. Please check your source sheets.")
