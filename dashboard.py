import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- 2. CUSTOM LADY VOL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA; padding: 20px; border-radius: 15px;
        border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    .metric-sub { font-size: 14px; font-weight: 700; margin-top: -15px; margin-bottom: 10px; }
    .red-text { color: #dc3545; }
    .green-text { color: #28a745; }
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Simplified Login Styling */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 15%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIMPLE LOGIN PAGE ---
if "auth" not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    # Minimalist center-aligned login
    _, col2, _ = st.columns([1, 0.8, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.title("Performance Access")
        pwd = st.text_input("Enter Password", type="password", label_visibility="collapsed", placeholder="Enter Password")
        if st.button("Login", use_container_width=True):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Access Key")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        # ADD THESE TWO LINES:
        swing_df = pd.read_csv(st.secrets["SWING_URL"])
        throw_df = pd.read_csv(st.secrets["THROW_URL"])
        
        for df in [ash_df, cmj_df, roster_df, swing_df, throw_df]:
            df.columns = df.columns.str.strip()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # ... (keep your existing merge logic for pictures) ...
        
        return ash_df, cmj_df, swing_df, throw_df # RETURN ALL FOUR
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Update the assignment line to match:
ash_df, cmj_df, swing_df, throw_df = load_all_data()

# --- 5. DASHBOARD UI ---
def quick_metric(col, label, best, current, unit):
    diff = ((current - best) / best * 100) if best != 0 else 0
    color = "red-text" if diff < -10 else "green-text"
    col.metric(label, f"{int(best)}{unit}")
    col.markdown(f'<p class="metric-sub {color}">Latest: {current:.1f}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

if not ash_df.empty:
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        selected = st.selectbox("Search Athlete", sorted(ash_df['Player Name'].unique()))
    
    p_ash_all = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
    
    with f_col2:
        years = sorted(p_ash_all['Date'].dt.year.dropna().unique().astype(int), reverse=True)
        selected_year = st.selectbox("Select Season", ["All Time"] + years)

    if selected_year == "All Time":
        ash_filt = p_ash_all
        cmj_filt = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')
        label = "All-Time"
    else:
        ash_filt = p_ash_all[p_ash_all['Date'].dt.year == selected_year]
        cmj_filt = cmj_df[(cmj_df['Player Name'] == selected) & (cmj_df['Date'].dt.year == selected_year)].sort_values('Date')
        label = str(selected_year)

    latest_ash = ash_filt.iloc[-1] if not ash_filt.empty else None
    if latest_ash is not None:
        st.markdown(f"""
            <div class="athlete-header">
                <div style="display: flex; align-items: center;">
                    <img src="{latest_ash.get('Picture', 'https://www.w3schools.com/howto/img_avatar.png')}" class="player-photo">
                    <div style="margin-left: 30px;">
                        <h1 style="margin:0;">{selected}</h1>
                        <p style="color:#4895DB; font-weight:700; margin:0;">PERFORMANCE HUB | {label}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    tab_ash, tab_cmj = st.tabs(["ASH TEST", "CMJ READINESS"])

    with tab_ash:
        if not ash_filt.empty:
            best_f, best_r = ash_filt['Peak Vertical Force [N]'].max(), ash_filt['RFD - 200ms [N/s]'].max()
            best_t = ash_filt['Start Time to Peak Force [s]'].min()

            def colored_metric(label, best_val, current_val, unit, is_time=False):
                diff = ((current_val - best_val) / best_val * 100) if best_val != 0 else 0
                is_bad = diff > 10 if is_time else diff < -10
                color = "red-text" if is_bad else "green-text"
                st.metric(label, f"{int(best_val) if not is_time else best_val}{unit}")
                st.markdown(f'<p class="metric-sub {color}">Latest: {current_val:.1f}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            with m1: colored_metric(f"{label} Best Force", best_f, latest_ash['Peak Vertical Force [N]'], " N")
            with m2: colored_metric(f"{label} Best RFD", best_r, latest_ash['RFD - 200ms [N/s]'], " N/s")
            with m3: st.metric("Latest Asymmetry", f"{latest_ash.get('Peak Vertical Force [N] (Asym)(%)', 0)}%")
            with m4: colored_metric(f"{label} Best Time", best_t, latest_ash['Start Time to Peak Force [s]'], "s", is_time=True)

            st.divider()
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("Left vs Right Force Profile")
                l_f, r_f = latest_ash.get('Peak Vertical Force [N] (L)', 0), latest_ash.get('Peak Vertical Force [N] (R)', 0)
                side_df = pd.DataFrame({'Side': ['Left (Lead)', 'Right (Trail)'], 'Force [N]': [l_f, r_f]})
                fig = px.bar(side_df, x='Side', y='Force [N]', text='Force [N]', color='Side', 
                             color_discrete_map={'Left (Lead)': '#4895DB', 'Right (Trail)': '#FF8200'}, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.subheader("Bilateral Profile")
                l_rfd = int(latest_ash.get('RFD - 200ms [N/s] (L)', 0))
                r_rfd = int(latest_ash.get('RFD - 200ms [N/s] (R)', 0))
                
                # --- SAFE ASYM CALCULATION ---
                raw_val = latest_ash.get('Peak Vertical Force [N] (Asym)(%)', 0)
                try:
                    # Strip % and convert to float so abs() works
                    clean_asym = float(str(raw_val).replace('%', '').strip())
                except:
                    clean_asym = 0.0
                
                asym_color = '#dc3545' if abs(clean_asym) > 10 else '#28a745'

                st.markdown(f"""
                    <div style="background-color:#F8F9FA; padding:15px; border-radius:10px; border:1px solid #E0E0E0;">
                        <div style="display:flex; justify-content:space-between;">
                            <div style="text-align:center; width:45%;"><p style="color:#4895DB; font-weight:800; margin:0; font-size:12px;">LEFT</p><h2 style="margin:0;">{l_f}<span style="font-size:14px;">N</span></h2><p style="color:grey; font-size:11px; margin:0;">{l_rfd} RFD</p></div>
                            <div style="text-align:center; width:45%;"><p style="color:#FF8200; font-weight:800; margin:0; font-size:12px;">RIGHT</p><h2 style="margin:0;">{r_f}<span style="font-size:14px;">N</span></h2><p style="color:grey; font-size:11px; margin:0;">{r_rfd} RFD</p></div>
                        </div>
                        <div style="text-align:center; border-top:1px solid #E0E0E0; padding-top:10px; margin-top:10px;">
                            <p style="margin:0; font-size:11px; color:grey; font-weight:700;">ASYMMETRY</p>
                            <h3 style="margin:0; color:{asym_color}">{clean_asym:.1f}%</h3>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.info(f"Dominance: **{'Right' if r_f > l_f else 'Left'}**")

            # --- ROBUST GAME LOOKUP (Athlete Specific) ---
            game_dates = set()
            
            def find_athlete_games(df, athlete_name, session_col):
                if df is not None and not df.empty and session_col in df.columns:
                    # Filter for the specific athlete AND session type 'Game'
                    games = df[(df['Player Name'] == athlete_name) & 
                               (df[session_col].astype(str).str.contains('Game', case=False, na=False))]
                    return set(pd.to_datetime(games['Date']).dt.date)
                return set()

            try:
                game_dates.update(find_athlete_games(swing_df, selected, 'Session Type'))
                game_dates.update(find_athlete_games(throw_df, selected, 'Session Type'))
            except NameError:
                st.warning("Swing or Throw data not loaded; Game status unavailable.")

            # Build Table
            ash_history = ash_filt[[
                'Date', 
                'Peak Vertical Force [N]', 
                'RFD - 200ms [N/s]', 
                'Start Time to Peak Force [s]', 
                'Peak Vertical Force [N] (Asym)(%)'
            ]].copy()

            ash_history['Game?'] = ash_history['Date'].dt.date.apply(
                lambda x: "✔️ Yes" if x in game_dates else "—"
            )
            
            ash_history['Date'] = ash_history['Date'].dt.strftime('%m/%d/%y')
            ash_history.columns = ['Date', 'Force (N)', 'RFD (N/s)', 'Time (s)', 'Asym %', 'Game?']

            st.table(ash_history.sort_values('Date', ascending=False).style.format({
                'Force (N)': '{:.0f}',
                'RFD (N/s)': '{:.0f}',
                'Time (s)': '{:.3f}',
                'Asym %': '{:.1f}%'
            }))
            
    with tab_cmj:
        if not cmj_filt.empty:
            # 1. IDENTIFY LATEST VS BEST FOR SELECTED YEAR
            c_lat = cmj_filt.iloc[-1]
            
            # Season Bests for the selected range
            b_h = cmj_filt['Jump Height (Imp-Mom) [cm]'].max()
            b_rsi = cmj_filt['RSI-modified (Imp-Mom) [m/s]'].max()
            b_pow = cmj_filt['Peak Power [W]'].max()

            # Current Values
            curr_h = c_lat['Jump Height (Imp-Mom) [cm]']
            curr_rsi = c_lat['RSI-modified (Imp-Mom) [m/s]']
            curr_pow = c_lat.get('Peak Power [W]', 0)

            # 2. THE COMPARISON ROW
            # Highlights the Season Best and compares the Latest directly
            m1, m2, m3 = st.columns(3)
            
            with m1:
                h_diff = ((curr_h - b_h) / b_h * 100) if b_h != 0 else 0
                st.metric(f"{label} Best Height", f"{b_h:.1f} cm", delta=f"{h_diff:+.1f}%")
                st.markdown(f'<p style="color:grey; font-weight:700; font-size:14px; margin-top:-15px;">Latest: {curr_h:.1f} cm</p>', unsafe_allow_html=True)

            with m2:
                rsi_diff = ((curr_rsi - b_rsi) / b_rsi * 100) if b_rsi != 0 else 0
                st.metric(f"{label} Best RSI-m", f"{b_rsi:.2f}", delta=f"{rsi_diff:+.1f}%")
                st.markdown(f'<p style="color:grey; font-weight:700; font-size:14px; margin-top:-15px;">Latest: {curr_rsi:.2f}</p>', unsafe_allow_html=True)

            with m3:
                pow_diff = ((curr_pow - b_pow) / b_pow * 100) if b_pow != 0 else 0
                st.metric(f"{label} Best Power", f"{int(b_pow)} W", delta=f"{pow_diff:+.1f}%")
                st.markdown(f'<p style="color:grey; font-weight:700; font-size:14px; margin-top:-15px;">Latest: {int(curr_pow)} W</p>', unsafe_allow_html=True)

            st.divider()

            # 3. PERFORMANCE TREND (CLEANED UP)
            st.subheader(f"Jump Height History")
            
            fig_cmj = px.line(
                cmj_filt, 
                x='Date', 
                y='Jump Height (Imp-Mom) [cm]', 
                markers=True, 
                template="plotly_white", 
                color_discrete_sequence=["#4895DB"]
            )
            
            # Formatting to handle the "All Time" timeline correctly
            fig_cmj.update_xaxes(
                tickformat="%b %d, %y", 
                tickangle=-45, 
                nticks=10,
                title=""
            )
            
            fig_cmj.update_layout(
                height=400, 
                yaxis_title="Jump Height (cm)",
                margin=dict(t=10, b=10, l=10, r=10)
            )
            
            st.plotly_chart(fig_cmj, use_container_width=True)

        else:
            st.info(f"No CMJ records found for {selected} in {selected_year}.")
