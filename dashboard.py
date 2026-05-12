import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball ASH Performance", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA; padding: 20px; border-radius: 15px;
        border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    .metric-sub { font-size: 14px; font-weight: 700; }
    .red-text { color: #dc3545; }
    .green-text { color: #28a745; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD GATE ---
if "auth" not in st.session_state: st.session_state.auth = False
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

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_performance_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        ash_df.columns = ash_df.columns.str.strip()
        roster_df.columns = roster_df.columns.str.strip()
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

if not df.empty:
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        selected = st.selectbox("Search Athlete", sorted(df['Player Name'].unique()))
    
    p_athlete_data = df[df['Player Name'] == selected].sort_values('Date')
    
    with f_col2:
        available_years = sorted(p_athlete_data['Date'].dt.year.dropna().unique().astype(int), reverse=True)
        selected_year = st.selectbox("Select Season", ["All Time"] + available_years)

    if selected_year == "All Time":
        p_filtered = p_athlete_data
        season_label = "All-Time"
    else:
        p_filtered = p_athlete_data[p_athlete_data['Date'].dt.year == selected_year]
        season_label = f"{selected_year}"

    if not p_filtered.empty:
        p_latest = p_filtered.iloc[-1]
        
        # Calculations
        best_force = p_filtered['Peak Vertical Force [N]'].max()
        best_rfd = p_filtered['RFD - 200ms [N/s]'].max()
        best_time = p_filtered['Start Time to Peak Force [s]'].min()

        # Helper for color-coded metrics
        def colored_metric(label, main_val, latest_val, best_val, unit):
            diff_pct = ((latest_val - best_val) / best_val * 100) if best_val != 0 else 0
            color_class = "red-text" if diff_pct < -10 else "green-text"
            st.metric(label=label, value=f"{main_val}{unit}")
            st.markdown(f'<p class="metric-sub {color_class}">Latest: {latest_val:.1f}{unit} ({diff_pct:+.1f}%)</p>', unsafe_allow_html=True)

        # Header
        st.markdown(f"""<div class="athlete-header"><div style="display: flex; align-items: center;"><img src="{p_latest.get('Picture', 'https://www.w3schools.com/howto/img_avatar.png')}" class="player-photo"><div style="margin-left: 30px;"><h1 style="margin:0;">{selected}</h1><p style="color:#4895DB; font-weight:700; margin:0;">ASH TEST PROFILE | {season_label}</p></div></div></div>""", unsafe_allow_html=True)

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1: colored_metric(f"{season_label} Best Force", int(best_force), p_latest['Peak Vertical Force [N]'], best_force, " N")
        with m2: colored_metric(f"{season_label} Best RFD", int(best_rfd), p_latest['RFD - 200ms [N/s]'], best_rfd, " N/s")
        with m3: 
            st.metric("Latest Asymmetry", f"{p_latest.get('Peak Vertical Force [N] (Asym)(%)', 0)}%")
            st.markdown('<p class="metric-sub" style="color:grey;">L/R Balance</p>', unsafe_allow_html=True)
        with m4:
            # For time, smaller is better, so color logic is flipped
            time_diff = ((p_latest['Start Time to Peak Force [s]'] - best_time) / best_time * 100) if best_time != 0 else 0
            t_color = "red-text" if time_diff > 10 else "green-text"
            st.metric(f"{season_label} Best Time", f"{best_time}s")
            st.markdown(f'<p class="metric-sub {t_color}">Latest: {p_latest["Start Time to Peak Force [s]"]:.2f}s ({time_diff:+.1f}%)</p>', unsafe_allow_html=True)

        st.divider()

        # Split Comparisons
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader(f"Left vs Right Force Profile")
            l_force = p_latest.get('Peak Vertical Force [N] (L)', 0)
            r_force = p_latest.get('Peak Vertical Force [N] (R)', 0)
            side_df = pd.DataFrame({'Side': ['Left', 'Right'], 'Force [N]': [l_force, r_force]})
            fig_side = px.bar(side_df, x='Side', y='Force [N]', text='Force [N]',
                              color='Side', color_discrete_map={'Left': '#4895DB', 'Right': '#FF8200'},
                              template="plotly_white")
            fig_side.update_traces(textposition='outside')
            st.plotly_chart(fig_side, use_container_width=True)

        with c2:
            st.subheader("Bilateral Profile")
            
            # Pull metrics
            l_rfd = int(p_latest.get('RFD - 200ms [N/s] (L)', 0))
            r_rfd = int(p_latest.get('RFD - 200ms [N/s] (R)', 0))
            raw_asym = p_latest.get('Peak Vertical Force [N] (Asym)(%)', 0)
            
            # --- CUSTOM L/R BREAKDOWN CARD ---
            st.markdown(f"""
                <div style="background-color:#F8F9FA; padding:15px; border-radius:10px; border:1px solid #E0E0E0;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <div style="text-align:center; width:45%;">
                            <p style="color:#4895DB; font-weight:800; margin:0; font-size:12px;">LEFT</p>
                            <h2 style="margin:0;">{l_force}<span style="font-size:14px;">N</span></h2>
                            <p style="color:grey; font-size:11px; margin:0;">{l_rfd} N/s RFD</p>
                        </div>
                        <div style="border-left:1px solid #E0E0E0; height:50px; margin-top:10px;"></div>
                        <div style="text-align:center; width:45%;">
                            <p style="color:#FF8200; font-weight:800; margin:0; font-size:12px;">RIGHT</p>
                            <h2 style="margin:0;">{r_force}<span style="font-size:14px;">N</span></h2>
                            <p style="color:grey; font-size:11px; margin:0;">{r_rfd} N/s RFD</p>
                        </div>
                    </div>
                    <div style="text-align:center; border-top:1px solid #E0E0E0; padding-top:10px; margin-top:5px;">
                        <p style="margin:0; font-size:11px; color:grey; font-weight:700;">TOTAL ASYMMETRY</p>
                        <h3 style="margin:0; color:{'#dc3545' if abs(raw_asym) > 10 else '#28a745'}">{raw_asym}%</h3>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Dominant Side Indicator
            st.write("")
            st.info(f"Dominance: **{'Right' if r_force > l_force else 'Left'}**")
            
        # Trend
        st.subheader(f"Force Trend Timeline ({season_label})")
        fig_trend = px.line(p_filtered, x='Date', y='Peak Vertical Force [N]', markers=True, 
                            template="plotly_white", color_discrete_sequence=["#FF8200"])
        fig_trend.update_xaxes(tickformat="%b %d, %y", tickangle=-45)
        st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.warning("Data load failed. Check Google Sheet connectivity.")
