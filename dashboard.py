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

        tab_ash, tab_cmj, tab_swing, tab_throwing = st.tabs(["ASH TEST", "CMJ READINESS", "SWING", "THROW"])

    with tab_ash:
        if not ash_filt.empty:
            # 1. MANUAL ASYMMETRY CALCULATION
            l_f_latest = latest_ash.get('Peak Vertical Force [N] (L)', 0)
            r_f_latest = latest_ash.get('Peak Vertical Force [N] (R)', 0)
            
            if l_f_latest > 0 and r_f_latest > 0:
                clean_asym = (abs(l_f_latest - r_f_latest) / max(l_f_latest, r_f_latest)) * 100
            else:
                clean_asym = 0.0

            # 2. CALCULATE BASELINES & BESTS
            ash_filt['Peak Vertical Force [N] (L)'] = pd.to_numeric(ash_filt['Peak Vertical Force [N] (L)'], errors='coerce').fillna(0)
            ash_filt['Peak Vertical Force [N] (R)'] = pd.to_numeric(ash_filt['Peak Vertical Force [N] (R)'], errors='coerce').fillna(0)
            
            base_f_l = ash_filt['Peak Vertical Force [N] (L)'].mean()
            base_f_r = ash_filt['Peak Vertical Force [N] (R)'].mean()
            
            best_f = ash_filt['Peak Vertical Force [N]'].max()
            best_r = ash_filt['RFD - 200ms [N/s]'].max()
            best_t = ash_filt['Start Time to Peak Force [s]'].min()

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
            with m3: st.metric("Asymmetry", f"{clean_asym:.1f}%", delta="High" if clean_asym > 10 else "Normal", delta_color="inverse")
            with m4: colored_metric("Best Time", best_t, latest_ash['Start Time to Peak Force [s]'], "s", is_time=True)

            st.divider()
            
            # 4. BILATERAL PROFILE (Left vs Right Distribution)
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("Left vs Right Force Profile")
                side_df = pd.DataFrame({'Side': ['Left (Lead)', 'Right (Trail)'], 'Force [N]': [l_f_latest, r_f_latest]})
                fig = px.bar(side_df, x='Side', y='Force [N]', text='Force [N]', color='Side', 
                             color_discrete_map={'Left (Lead)': '#4895DB', 'Right (Trail)': '#FF8200'}, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("Balance Details")
                l_rfd = int(latest_ash.get('RFD - 200ms [N/s] (L)', 0))
                r_rfd = int(latest_ash.get('RFD - 200ms [N/s] (R)', 0))
                asym_color = '#dc3545' if clean_asym > 10 else '#28a745'
                st.markdown(f"""
                    <div style="background-color:#F8F9FA; padding:15px; border-radius:10px; border:1px solid #E0E0E0; text-align:center;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                            <div style="width:45%;"><p style="color:#4895DB; font-weight:800; margin:0;">LEFT</p><h2>{l_f_latest}N</h2><p style="color:grey; font-size:12px;">{l_rfd} RFD</p></div>
                            <div style="width:45%;"><p style="color:#FF8200; font-weight:800; margin:0;">RIGHT</p><h2>{r_f_latest}N</h2><p style="color:grey; font-size:12px;">{r_rfd} RFD</p></div>
                        </div>
                        <p style="margin:0; font-size:11px; color:grey; font-weight:700;">CALCULATED ASYMMETRY</p>
                        <h1 style="margin:0; color:{asym_color};">{clean_asym:.1f}%</h1>
                    </div>
                """, unsafe_allow_html=True)

            st.divider()

            # 5. PEAK FORCE HISTORY GRAPH
            st.subheader("Peak Force History: Left vs Right")
            fig_trend = px.line(ash_filt, x='Date', y=['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)'],
                                markers=True, color_discrete_map={'Peak Vertical Force [N] (L)': '#4895DB', 'Peak Vertical Force [N] (R)': '#FF8200'},
                                template="plotly_white")
            fig_trend.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_trend, use_container_width=True)

            st.divider()

           # 3. FILTERED & SORTED TABLE: No Index Column
            st.subheader("Test History (Match Proximity)")
            
            match_map = {}
            try:
                all_sessions = pd.concat([swing_df, throw_df], ignore_index=True)
                athlete_games = all_sessions[
                    (all_sessions['Name'] == selected) & 
                    (all_sessions['Session Type'].astype(str).str.contains('Game', case=False, na=False))
                ]
                for _, row in athlete_games.iterrows():
                    # Simplified: Activity name only (no extra date)
                    match_map[row['Date'].date()] = f"{row.get('Activity', 'Game')}"
            except: 
                pass

            ash_hist_df = ash_filt[['Date', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)']].copy()
            
            def get_match_context(test_date):
                t_date = test_date.date()
                past_matches = [d for d in match_map.keys() if d <= t_date]
                
                if not past_matches:
                    return "N/A", 999
                
                nearest_match_date = max(past_matches)
                days_since = (t_date - nearest_match_date).days
                return match_map[nearest_match_date], days_since

            ash_hist_df[['Prev Match', 'Days Since']] = ash_hist_df['Date'].apply(
                lambda x: pd.Series(get_match_context(x))
            )

            # Filter for 3-day proximity and sort most recent to oldest
            ash_table_filt = ash_hist_df[ash_hist_df['Days Since'] <= 3].copy()
            
            if not ash_table_filt.empty:
                ash_table_filt = ash_table_filt.sort_values('Date', ascending=False)
                
                ash_table_filt['L vs Base'] = ash_table_filt['Peak Vertical Force [N] (L)'] - base_f_l
                ash_table_filt['R vs Base'] = ash_table_filt['Peak Vertical Force [N] (R)'] - base_f_r
                
                ash_display = ash_table_filt[['Date', 'Prev Match', 'Peak Vertical Force [N] (L)', 'L vs Base', 'Peak Vertical Force [N] (R)', 'R vs Base']].copy()
                ash_display['Date'] = ash_display['Date'].dt.strftime('%m/%d/%Y')
                ash_display.columns = ['Test Date', 'Previous Match', 'Force (L)', '+/- Base (L)', 'Force (R)', '+/- Base (R)']

                # USE DATAFRAME WITH HIDE_INDEX TO REMOVE THE EXTRA COLUMN
                st.dataframe(
                    ash_display.style.format({
                        'Force (L)': '{:.0f}N', 
                        '+/- Base (L)': '{:+.1f}N', 
                        'Force (R)': '{:.0f}N', 
                        '+/- Base (R)': '{:+.1f}N'
                    })
                    .map(lambda x: f'color: {"#28a745" if x > 0 else "#dc3545"}; font-weight: bold', 
                         subset=['+/- Base (L)', '+/- Base (R)']),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No ASH tests found within 3 days of a match.")
            
            
            
    with tab_cmj:
        if not cmj_filt.empty:
            # 1. PREP DATA & KPI LIST
            metrics_map = {
                'Jump Height (Imp-Mom) [cm]': 'Jump Height (cm)',
                'Peak Power [W]': 'Peak Power (W)',
                'RSI-modified (Imp-Mom) [m/s]': 'RSI-m',
                'Force at Zero Velocity [N]': 'Force @ Zero Velocity (N)',
                'Eccentric Braking RFD [N/s]': 'Ecc. Braking RFD (N/s)',
                'Concentric Peak Velocity [m/s]': 'Conc. Peak Velocity (m/s)'
            }
            
            metrics_list = list(metrics_map.keys())
            for m in metrics_list:
                cmj_filt[m] = pd.to_numeric(cmj_filt[m], errors='coerce').fillna(0)
            
            c_lat = cmj_filt.iloc[-1]

            # 2. TOP METRIC GRID (6 Metrics)
            st.subheader(f"CMJ Season Bests & Latest Status")
            
            def cmj_metric_box(col, label_text, col_name, unit, precision=".1f"):
                best_val = cmj_filt[col_name].max()
                curr_val = c_lat[col_name]
                diff = ((curr_val - best_val) / best_val * 100) if best_val != 0 else 0
                
                col.metric(label_text, f"{best_val:{precision}}{unit}")
                color = "red-text" if diff < -10 else "green-text"
                col.markdown(f'<p class="metric-sub {color}">Latest: {curr_val:{precision}}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

            m_row1 = st.columns(3)
            cmj_metric_box(m_row1[0], "Best Jump Height", metrics_list[0], " cm")
            cmj_metric_box(m_row1[1], "Best Peak Power", metrics_list[1], " W", precision=".0f")
            cmj_metric_box(m_row1[2], "Best RSI-m", metrics_list[2], "")

            m_row2 = st.columns(3)
            cmj_metric_box(m_row2[0], "Force @ Zero Velocity", metrics_list[3], " N", precision=".0f")
            cmj_metric_box(m_row2[1], "Ecc. Braking RFD", metrics_list[4], " N/s", precision=".0f")
            cmj_metric_box(m_row2[2], "Conc. Peak Velocity", metrics_list[5], " m/s", precision=".2f")

            st.divider()

            # 3. SIDE-BY-SIDE TREND GRAPHS (2x3 Grid)
            st.subheader("Performance Trends: All Metrics")
            
            def create_sparkline(df, y_col, title_text):
                fig = px.line(df, x='Date', y=y_col, markers=True, template="plotly_white", 
                             color_discrete_sequence=["#FF8200"])
                fig.update_layout(
                    height=300, title={'text': title_text, 'x': 0.5, 'xanchor': 'center'},
                    xaxis_title="", yaxis_title="", margin=dict(t=40, b=10, l=10, r=10),
                    # FORCES Y-AXIS TO START AT 0
                    yaxis=dict(range=[0, df[y_col].max() * 1.1])
                )
                return fig

            # Corrected Grid Layout
            g_row1_col1, g_row1_col2 = st.columns(2)
            with g_row1_col1: st.plotly_chart(create_sparkline(cmj_filt, metrics_list[0], metrics_map[metrics_list[0]]), use_container_width=True)
            with g_row1_col2: st.plotly_chart(create_sparkline(cmj_filt, metrics_list[1], metrics_map[metrics_list[1]]), use_container_width=True)

            g_row2_col1, g_row2_col2 = st.columns(2)
            with g_row2_col1: st.plotly_chart(create_sparkline(cmj_filt, metrics_list[2], metrics_map[metrics_list[2]]), use_container_width=True)
            with g_row2_col2: st.plotly_chart(create_sparkline(cmj_filt, metrics_list[3], metrics_map[metrics_list[3]]), use_container_width=True)

            g_row3_col1, g_row3_col2 = st.columns(2)
            with g_row3_col1: st.plotly_chart(create_sparkline(cmj_filt, metrics_list[4], metrics_map[metrics_list[4]]), use_container_width=True)
            with g_row3_col2: st.plotly_chart(create_sparkline(cmj_filt, metrics_list[5], metrics_map[metrics_list[5]]), use_container_width=True)

        else:
            st.info("No CMJ records found for the selected criteria.")

    with tab_swing:
        if not swing_df.empty:
            # 1. INTERNAL TAB FILTERS
            f1, f2 = st.columns([1, 2])
            with f1:
                swing_year = st.selectbox("Season", options=[2026, 2025, 2024], key="swing_yr")
            with f2:
                swing_cat = st.segmented_control("Session Type", options=["All", "Games", "Practices"], default="All", key="swing_ct")

            # 2. DATA PROCESSING & NUMERIC CONVERSION
            df_s = swing_df.copy()
            df_s.columns = df_s.columns.str.strip()
            df_s['Date'] = pd.to_datetime(df_s['Date'])
            
            p_swing = df_s[df_s['Name'] == selected].copy()
            p_swing = p_swing[p_swing['Date'].dt.year == swing_year]
            
            if swing_cat == "Games":
                p_swing = p_swing[p_swing['Session Type'].str.contains('Game', case=False, na=False)]
            elif swing_cat == "Practices":
                p_swing = p_swing[p_swing['Session Type'].str.contains('Practice|Session', case=False, na=False)]

            if not p_swing.empty:
                # MANDATORY: Define the numeric columns right here to avoid KeyErrors
                p_swing['Forward'] = pd.to_numeric(p_swing['Swing Max Player Load Fwd % (median)'], errors='coerce').fillna(0)
                p_swing['Side'] = pd.to_numeric(p_swing['Swing Max Player Load Side % (median)'], errors='coerce').fillna(0)
                p_swing['Up'] = pd.to_numeric(p_swing['Swing Max Player Load Up % (median)'], errors='coerce').fillna(0)
                p_swing['Swing Count'] = pd.to_numeric(p_swing['Swing Count'], errors='coerce').fillna(1)
                p_swing['Total Load'] = pd.to_numeric(p_swing['Sum Swing Max Player Load'], errors='coerce').fillna(0)
                
                # Calculate Intensity (Load per Swing)
                p_swing['Intensity'] = p_swing['Total Load'] / p_swing['Swing Count']
                
                p_swing = p_swing.sort_values('Date')
                latest = p_swing.iloc[-1]

                # 3. RADAR CHART DATA
                # Season Averages
                avg_fwd = p_swing['Forward'].mean()
                avg_side = p_swing['Side'].mean()
                avg_up = p_swing['Up'].mean()
                avg_int = p_swing['Intensity'].mean()

                # Latest Session
                lat_fwd = latest['Forward']
                lat_side = latest['Side']
                lat_up = latest['Up']
                lat_int = latest['Intensity']

                # Normalize intensity for the radar (multiply by 10 so it fits the 0-100 scale)
                categories = ['Linear (Fwd)', 'Rotational (Side)', 'Vertical (Up)', 'Intensity']
                
                import plotly.graph_objects as go
                fig_radar = go.Figure()

                # Season Baseline Shape
                fig_radar.add_trace(go.Scatterpolar(
                    r=[avg_fwd, avg_side, avg_up, avg_int * 10],
                    theta=categories,
                    fill='toself',
                    name='Season Average',
                    line_color='rgba(150, 150, 150, 0.5)',
                    fillcolor='rgba(200, 200, 200, 0.2)'
                ))

                # Current Session Shape
                fig_radar.add_trace(go.Scatterpolar(
                    r=[lat_fwd, lat_side, lat_up, lat_int * 10],
                    theta=categories,
                    fill='toself',
                    name='Latest Session',
                    line_color='#FF8200',
                    fillcolor='rgba(255, 130, 0, 0.3)'
                ))

                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    height=450,
                    margin=dict(t=40, b=40, l=60, r=60)
                )

                st.subheader("Swing 'Fingerprint': Latest vs. Season Average")
                st.plotly_chart(fig_radar, use_container_width=True)

                # 4. RECENT HISTORY TABLE (Clean & Sorted)
                st.subheader("Recent Session Breakdown")
                summary_df = p_swing.sort_values('Date', ascending=False).head(5).copy()
                summary_df['Date'] = summary_df['Date'].dt.strftime('%m/%d')
                
                # Clean up display columns
                display_df = summary_df[['Date', 'Session Type', 'Swing Count', 'Intensity', 'Forward', 'Side', 'Up']].copy()
                
                st.dataframe(
                    display_df.style.format({
                        'Swing Count': '{:.0f}',
                        'Intensity': '{:.2f}',
                        'Forward': '{:.1f}%',
                        'Side': '{:.1f}%',
                        'Up': '{:.1f}%'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info(f"No records found for {selected} in {swing_year}.")

    with tab_throwing:
        if not throw_df.empty:
            # 1. DATE & CATEGORY FILTERS
            f1, f2 = st.columns([2, 1])
            with f1:
                # Defaulting to the last 7 days of data available
                df_t_dates = pd.to_datetime(throw_df['Date'])
                max_date = df_t_dates.max()
                min_date = max_date - pd.Timedelta(days=7)
                
                selected_dates = st.date_input(
                    "Select Date Range",
                    value=(min_date, max_date),
                    key="throw_date_range"
                )
            
            with f2:
                t_cat = st.segmented_control(
                    "Session Type", 
                    options=["All", "Games", "Practices"], 
                    default="All", 
                    key="t_ct_date"
                )

            # 2. DATA PROCESSING
            df_t = throw_df.copy()
            df_t.columns = df_t.columns.str.strip()
            df_t['Date'] = pd.to_datetime(df_t['Date'])
            
            # Apply Athlete & Date Range Filter
            p_t = df_t[df_t['Name'] == selected].copy()
            
            if len(selected_dates) == 2:
                start_date, end_date = selected_dates
                p_t = p_t[(p_t['Date'].dt.date >= start_date) & (p_t['Date'].dt.date <= end_date)]

            # Apply Category Filter
            if t_cat == "Games":
                p_t = p_t[p_t['Session Type'].astype(str).str.contains('Game', case=False, na=False)]
            elif t_cat == "Practices":
                p_t = p_t[p_t['Session Type'].astype(str).str.contains('Practice|Session', case=False, na=False)]

            if not p_t.empty:
                # DEFINE COACHING NAMES
                p_t['Throws'] = pd.to_numeric(p_t['Total Throw Count'], errors='coerce').fillna(0)
                p_t['Intent'] = pd.to_numeric(p_t['Total Throw Count - Rotation Band 3'], errors='coerce').fillna(0)
                
                p_t = p_t.sort_values('Date')
                latest = p_t.iloc[-1]
                
                # 3. THE COACH'S "BOTTOM LINE" BOX
                intent_val = int(latest['Intent'])
                if intent_val > 15:
                    status, color, note = "HIGH INTENT", "#dc3545", "Max effort defensive/pitching work detected."
                elif intent_val > 5:
                    status, color, note = "MODERATE", "#ffc107", "Standard skill work or active warm-up."
                else:
                    status, color, note = "RECOVERY", "#28a745", "Light catch or low-intent technical work."

                st.markdown(f"""
                    <div style="background-color:{color}; padding:20px; border-radius:15px; color:white; text-align:center;">
                        <h1 style="margin:0; font-size:32px;">{status} SESSION</h1>
                        <p style="margin:0; font-size:18px; opacity:0.9;">Latest Session: {latest['Date'].strftime('%m/%d')} — {note}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.divider()

                # 4. BIG NUMBER METRICS (Range Summaries)
                st.subheader(f"Summary for {start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    total_vol = p_t['Throws'].sum()
                    st.metric("Total Range Volume", f"{int(total_vol)} Throws")
                with c2:
                    total_intent = p_t['Intent'].sum()
                    st.metric("Total High-Intent", f"{int(total_intent)}")
                with c3:
                    avg_quality = (p_t['Intent'].sum() / p_t['Throws'].sum() * 100) if p_t['Throws'].sum() > 0 else 0
                    st.metric("Avg Work Quality", f"{avg_quality:.1f}%")

                st.divider()

                # 5. SIMPLE TREND (The Bars)
                st.subheader("Daily Volume in Selected Range")
                fig_simple = px.bar(
                    p_t, x='Date', y='Throws',
                    text_auto='.0f',
                    color_discrete_sequence=["#4895DB"],
                    template="plotly_white"
                )
                fig_simple.update_layout(height=300, yaxis_visible=False, xaxis_title="")
                st.plotly_chart(fig_simple, use_container_width=True)

                # 6. TABLE
                st.subheader("Session Details")
                hist = p_t.sort_values('Date', ascending=False).copy()
                hist['Date'] = hist['Date'].dt.strftime('%m/%d')
                
                # Create a clean version with only your 4 columns
                display_hist = hist[['Date', 'Session Type', 'Throws', 'Intent']].rename(columns={
                    'Throws': 'Total',
                    'Intent': 'High Intent'
                })
                
                # Using st.dataframe instead of st.table to allow index hiding
                st.dataframe(
                    display_hist,
                    hide_index=True,
                    use_container_width=True
                )
