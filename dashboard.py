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
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADING & MERGING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        # 1. Load Raw Data
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        swing_df = pd.read_csv(st.secrets["SWING_URL"])
        throw_df = pd.read_csv(st.secrets["THROW_URL"])
        
        # 2. Clean Column Names
        for df in [ash_df, cmj_df, roster_df, swing_df, throw_df]:
            df.columns = df.columns.str.strip()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # 3. DYNAMIC PHOTO COLUMN FIX
        # This finds whatever column you named the photos and renames it to 'Photo'
        photo_col = [c for c in roster_df.columns if 'photo' in c.lower() or 'picture' in c.lower()]
        if photo_col:
            roster_df = roster_df.rename(columns={photo_col[0]: 'Photo'})
        else:
            # Fallback if no photo column exists at all
            roster_df['Photo'] = 'https://www.w3schools.com/howto/img_avatar.png'

        # 4. MERGE (Ensuring 'Photo' and 'Player Name' exist)
        if 'Player Name' in roster_df.columns:
            # Merge photo into performance dataframes
            ash_df = ash_df.merge(roster_df[['Player Name', 'Photo']], on='Player Name', how='left')
            cmj_df = cmj_df.merge(roster_df[['Player Name', 'Photo']], on='Player Name', how='left')
        
        return ash_df, cmj_df, swing_df, throw_df

    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        

ash_df, cmj_df, swing_df, throw_df = load_all_data()

# --- 4. DASHBOARD UI ---
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
        # PROFILE HEADER FIX
        # Using the merged 'Photo' column
        img_url = latest_ash.get('Photo', 'https://www.w3schools.com/howto/img_avatar.png')
        
        st.markdown(f"""
            <div class="athlete-header">
                <div style="display: flex; align-items: center;">
                    <img src="{img_url}" class="player-photo">
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
                # 1. ASYMMETRY REPAIR
                asym_raw = latest_ash.get('Peak Vertical Force [N] (Asym)(%)', 0)
                try:
                    # Robust cleaning: convert to string, remove % sign, convert to float
                    clean_asym = float(str(asym_raw).replace('%', '').strip())
                except (ValueError, TypeError):
                    clean_asym = 0.0

                # 2. CALC METRICS
                ash_filt['Peak Vertical Force [N]'] = pd.to_numeric(ash_filt['Peak Vertical Force [N]'], errors='coerce').fillna(0)
                best_f = ash_filt['Peak Vertical Force [N]'].max()
                best_r = ash_filt['RFD - 200ms [N/s]'].max()
                best_t = ash_filt['Start Time to Peak Force [s]'].min()
                base_f = ash_filt['Peak Vertical Force [N]'].mean()

                def colored_metric(label, best_val, current_val, unit, is_time=False):
                    diff = ((current_val - best_val) / best_val * 100) if best_val != 0 else 0
                    is_bad = diff > 10 if is_time else diff < -10
                    color = "red-text" if is_bad else "green-text"
                    st.metric(label, f"{int(best_val) if not is_time else best_val}{unit}")
                    st.markdown(f'<p class="metric-sub {color}">Latest: {current_val:.1f}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

                # 3. TOP METRIC ROW
                m1, m2, m3, m4 = st.columns(4)
                with m1: colored_metric("Best Force", best_f, latest_ash['Peak Vertical Force [N]'], " N")
                with m2: colored_metric("Best RFD", best_r, latest_ash['RFD - 200ms [N/s]'], " N/s")
                with m3: st.metric("Asymmetry", f"{clean_asym:.1f}%", delta="High" if abs(clean_asym) > 10 else "Normal", delta_color="inverse")
                with m4: colored_metric("Best Time", best_t, latest_ash['Start Time to Peak Force [s]'], "s", is_time=True)

                st.divider()

                # 4. BILATERAL DETAILS
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.subheader("Force Distribution")
                    l_f, r_f = latest_ash.get('Peak Vertical Force [N] (L)', 0), latest_ash.get('Peak Vertical Force [N] (R)', 0)
                    side_df = pd.DataFrame({'Side': ['Left (Lead)', 'Right (Trail)'], 'Force [N]': [l_f, r_f]})
                    fig = px.bar(side_df, x='Side', y='Force [N]', text='Force [N]', color='Side', 
                                 color_discrete_map={'Left (Lead)': '#4895DB', 'Right (Trail)': '#FF8200'}, template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                
                with c2:
                    st.subheader("Balance Details")
                    l_f = latest_ash.get('Peak Vertical Force [N] (L)', 0)
                    r_f = latest_ash.get('Peak Vertical Force [N] (R)', 0)
                    l_rfd = int(latest_ash.get('RFD - 200ms [N/s] (L)', 0))
                    r_rfd = int(latest_ash.get('RFD - 200ms [N/s] (R)', 0))

                    # --- MANUAL CALCULATION (Fixes the 0.0% issue) ---
                    if l_f > 0 and r_f > 0:
                        # Standard asymmetry formula: ((High - Low) / High) * 100
                        diff = abs(l_f - r_f)
                        high_val = max(l_f, r_f)
                        clean_asym = (diff / high_val) * 100
                    else:
                        clean_asym = 0.0
                
                    asym_color = '#dc3545' if clean_asym > 10 else '#28a745'

                    st.markdown(f"""
                        <div style="background-color:#F8F9FA; padding:15px; border-radius:10px; border:1px solid #E0E0E0; text-align:center;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                                <div style="width:45%;"><p style="color:#4895DB; font-weight:800; margin:0;">LEFT</p><h2>{l_f}N</h2><p style="color:grey; font-size:12px;">{l_rfd} RFD</p></div>
                                <div style="width:45%;"><p style="color:#FF8200; font-weight:800; margin:0;">RIGHT</p><h2>{r_f}N</h2><p style="color:grey; font-size:12px;">{r_rfd} RFD</p></div>
                            </div>
                            <p style="margin:0; font-size:11px; color:grey; font-weight:700;">CALCULATED ASYMMETRY</p>
                            <h1 style="margin:0; color:{asym_color};">{clean_asym:.1f}%</h1>
                        </div>
                    """, unsafe_allow_html=True)
                
                    # Dynamic Dominance Note
                    dominance = "Left" if l_f > r_f else "Right"
                    st.info(f"Dominance: **{dominance}** ({clean_asym:.1f}%)")
                
                    st.divider()

                # 5. MATCH CONTEXT TABLE
                st.subheader("ASH History & Match Context")
                match_map = {}
                try:
                    all_sessions = pd.concat([swing_df, throw_df], ignore_index=True)
                    athlete_games = all_sessions[(all_sessions['Player Name'] == selected) & (all_sessions['Session Type'].astype(str).str.contains('Game', case=False, na=False))]
                    for _, row in athlete_games.iterrows():
                        match_map[row['Date'].date()] = f"{row.get('Opponent', 'Game')} ({row['Date'].strftime('%m/%d')})"
                except: pass

                ash_hist_df = ash_filt[['Date', 'Peak Vertical Force [N]', 'RFD - 200ms [N/s]']].copy()
                ash_hist_df['Previous Match'] = ash_hist_df['Date'].apply(lambda x: match_map[max([d for d in match_map.keys() if d < x.date()])] if any(d < x.date() for d in match_map.keys()) else "N/A")
                ash_hist_df['Vs. Baseline'] = ash_hist_df['Peak Vertical Force [N]'] - base_f
                
                ash_display = ash_hist_df[['Date', 'Previous Match', 'Peak Vertical Force [N]', 'Vs. Baseline', 'RFD - 200ms [N/s]']].copy()
                ash_display['Date'] = ash_display['Date'].dt.strftime('%m/%d/%Y')
                ash_display.columns = ['Test Date', 'Previous Match', 'Peak Force', 'Vs. Baseline', 'RFD']

                st.table(
                    ash_display.sort_values('Test Date', ascending=False)
                    .style.format({'Peak Force': '{:.0f} N', 'Vs. Baseline': '{:+.1f} N', 'RFD': '{:.0f} N/s'})
                    .map(lambda x: f'color: {"#28a745" if x > 0 else "#dc3545"}; font-weight: bold', subset=['Vs. Baseline'])
                )
                
            
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
