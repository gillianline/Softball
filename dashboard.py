import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

st.markdown("""
    <style>
    /* Centers everything inside the dataframe cells */
    [data-testid="stHeaderCell"] {
        text-align: center !important;
        display: flex;
        justify-content: center;
    }
    [data-testid="stTable"] td, [data-testid="stDataFrameDataLayer"] td {
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

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
            # 1. DATE & CATEGORY FILTERS
            f1, f2 = st.columns([2, 1])
            with f1:
                df_s_dates = pd.to_datetime(swing_df['Date'])
                max_s = df_s_dates.max()
                min_s = max_s - pd.Timedelta(days=7)
            
                selected_dates_s = st.date_input(
                    "Select Date Range",
                    value=(min_s.date(), max_s.date()),
                    key="swing_date_range_final"
                )
        
            with f2:
                s_cat = st.segmented_control(
                    "Session Type", 
                    options=["All", "Games", "Practices"], 
                    default="All", 
                    key="s_ct_final"
                )

            # 2. DATA PROCESSING & SAFETY GATE
            if isinstance(selected_dates_s, tuple) and len(selected_dates_s) == 2:
                start_s, end_s = selected_dates_s
            
                df_s = swing_df.copy()
                df_s.columns = df_s.columns.str.strip()
                df_s['Date'] = pd.to_datetime(df_s['Date'])
            
                p_s = df_s[(df_s['Name'] == selected) & 
                           (df_s['Date'].dt.date >= start_s) & 
                           (df_s['Date'].dt.date <= end_s)].copy()

                if s_cat == "Games":
                    p_s = p_s[p_s['Session Type'].astype(str).str.contains('Game', case=False, na=False)]
                elif s_cat == "Practices":
                    p_s = p_s[p_s['Session Type'].astype(str).str.contains('Practice|Session', case=False, na=False)]

                if not p_s.empty:
                    # --- FIXING THE COLUMN NAMES HERE ---
                    p_s['Total'] = pd.to_numeric(p_s['Swing Count'], errors='coerce').fillna(0)
                    # Ensure this name matches the HTML loop exactly
                    p_s['Max Intent'] = pd.to_numeric(p_s['Swing Max Rotation Band 3 Count'], errors='coerce').fillna(0)
                    p_s['Load'] = pd.to_numeric(p_s['Sum Swing Max Player Load'], errors='coerce').fillna(0)
                
                    p_s['Intensity'] = p_s['Load'] / p_s['Total'].replace(0, 1)
                    p_s['Rot_Pct'] = pd.to_numeric(p_s['Swing Max Player Load Side % (median)'], errors='coerce').fillna(0)
                
                    p_s = p_s.sort_values('Date')

                    # 3. RANGE SUMMARY HEADER
                    st.subheader(f"Swing Report: {start_s.strftime('%m/%d')} - {end_s.strftime('%m/%d')}")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Swings", f"{int(p_s['Total'].sum())}")
                    m2.metric("Max Intent", f"{int(p_s['Max Intent'].sum())}")
                    m3.metric("Avg Intensity", f"{p_s['Intensity'].mean():.2f}")
                    m4.metric("Avg Rot %", f"{p_s['Rot_Pct'].mean():.1f}%")

                    st.divider()

                    # 4. COLOR-CODED BAR GRAPH
                    p_s['Session'] = p_s['Session Type'].apply(lambda x: 'Game' if 'Game' in str(x) else 'Practice')
                
                    fig_s = px.bar(p_s, x='Date', y='Total', 
                                 color='Session',
                                 color_discrete_map={'Game': '#4895DB', 'Practice': '#FF8200'},
                                 text='Total', 
                                 template="plotly_white")
                
                    fig_s.update_traces(texttemplate='%{text:.0f}', textposition='outside', cliponaxis=False)
                    fig_s.update_layout(
                        height=350, yaxis_visible=False, xaxis_title="",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
                        uniformtext=dict(minsize=10, mode='hide'),
                        xaxis=dict(tickformat="%m/%d")
                    )
                
                    st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

                    # 5. CENTERED HTML TABLE
                    st.subheader("Session Details")
                    hist_s = p_s.sort_values('Date', ascending=False).copy()
                    hist_s['Date'] = hist_s['Date'].dt.strftime('%m/%d')
                
                    rows_html = ""
                    for _, row in hist_s.iterrows():
                        rows_html += f"""
                        <tr>
                            <td>{row['Date']}</td>
                            <td>{row['Session Type']}</td>
                            <td>{int(row['Total'])}</td>
                            <td>{int(row['Max Intent'])}</td>
                            <td>{row['Intensity']:.2f}</td>
                            <td>{row['Rot_Pct']:.1f}%</td>
                        </tr>
                        """

                    table_html = f"""
                    <style>
                        .coach-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; }}
                        .coach-table th {{ background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #dee2e6; text-align: center !important; }}
                        .coach-table td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: center !important; }}
                    </style>
                    <table class="coach-table">
                        <thead>
                            <tr>
                                <th>Date</th><th>Type</th><th>Total</th><th>Max Intent</th><th>Load/Sw</th><th>Rot %</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                    """
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.info(f"No records found for {selected} in this range.")
            else:
                st.warning("Please select both a start and end date.")

    with tab_throwing:
        if not throw_df.empty:
            # 1. DATE & CATEGORY FILTERS
            f1, f2 = st.columns([2, 1])
            with f1:
                df_t_dates = pd.to_datetime(throw_df['Date'])
                max_date = df_t_dates.max()
                # Default to last 7 days of data
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

            # 2. DATA PROCESSING & SAFETY CHECK
            # This 'if' ensures we don't calculate anything until 2 dates are picked
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
                
                df_t = throw_df.copy()
                df_t.columns = df_t.columns.str.strip()
                df_t['Date'] = pd.to_datetime(df_t['Date'])
                
                # Apply Athlete & Date Range Filter
                p_t = df_t[(df_t['Name'] == selected) & 
                           (df_t['Date'].dt.date >= start_date) & 
                           (df_t['Date'].dt.date <= end_date)].copy()

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
                    st.subheader(f"Summary: {start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Total Range Volume", f"{int(p_t['Throws'].sum())} Throws")
                    with c2:
                        st.metric("Total High-Intent", f"{int(p_t['Intent'].sum())}")
                    with c3:
                        avg_q = (p_t['Intent'].sum() / p_t['Throws'].sum() * 100) if p_t['Throws'].sum() > 0 else 0
                        st.metric("Avg Work Quality", f"{avg_q:.1f}%")

                    st.divider()

                    # 5. SIMPLE TREND (Color-Coded & Locked)
                    st.subheader("Daily Volume")
                    
                    # Map colors: Game = Blue, Practice = Orange
                    p_t['Session'] = p_t['Session Type'].apply(lambda x: 'Game' if 'Game' in str(x) else 'Practice')

                    fig_simple = px.bar(
                        p_t, x='Date', y='Throws',
                        color='Session',
                        color_discrete_map={'Game': '#4895DB', 'Practice': '#FF8200'},
                        text='Throws', 
                        template="plotly_white"
                    )

                    fig_simple.update_traces(
                        texttemplate='%{text}', 
                        textposition='outside', # Forced outside
                        cliponaxis=False         # Prevents top numbers from cutting off
                    )

                    fig_simple.update_layout(
                        height=350, 
                        yaxis_visible=False, 
                        xaxis_title="",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
                        uniformtext=dict(minsize=10, mode='hide'), # Prevents sideways text
                        xaxis=dict(tickformat="%m/%d")
                    )

                    st.plotly_chart(
                        fig_simple, 
                        use_container_width=True, 
                        config={'displayModeBar': False, 'staticPlot': True}
                    )

                    # 6. TABLE (HTML Forced Centering & No Index)
                    st.subheader("Session Details")
                    hist = p_t.sort_values('Date', ascending=False).copy()
                    hist['Date'] = hist['Date'].dt.strftime('%m/%d')
                    
                    display_hist = hist[['Date', 'Session Type', 'Throws', 'Intent']].rename(columns={
                        'Throws': 'Total',
                        'Intent': 'High Intent'
                    })

                    table_html = f"""
                    <style>
                        .coach-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; }}
                        .coach-table th, .coach-table td {{ text-align: center !important; padding: 12px; border-bottom: 1px solid #f0f2f6; }}
                        .coach-table th {{ background-color: #f8f9fa; color: #495057; font-weight: bold; }}
                    </style>
                    <table class="coach-table">
                        <thead><tr>{" ".join([f"<th>{col}</th>" for col in display_hist.columns])}</tr></thead>
                        <tbody>
                            {" ".join([f"<tr>{' '.join([f'<td>{int(val) if isinstance(val, (int, float)) else val}</td>' for val in row])}</tr>" for row in display_hist.values])}
                        </tbody>
                    </table>
                    """
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.info(f"No records found for {selected} in this range.")
            else:
                # Placeholder while picking dates to prevent NameErrors
                st.warning("Please select an end date to view report.")

            # --- COACHING GLOSSARY ---
        with st.expander("What do these metrics mean?"):
            st.markdown("""
            ### Throwing Metric Definitions
    
            * **Total Volume**: The total number of throws recorded during the selected date range.
            * **High Intent**: Any throw that reaches **Rotation Band 3**. This measures maximal torso rotation and arm speed."
            * **Avg Work Quality**: The percentage of total throws that were 'High Intent.' 
                * *Example:* 10 High Intent throws out of 100 total throws = **10% Work Quality**.
    
            ---
    
            ### Intensity Status Guide
            * 🔴 **HIGH INTENT**: A high volume of maximal effort throws. Typically seen in Games or high-effort defensive drills.
            * 🟡 **MODERATE**: A balanced mix of warm-ups and skill work. This is the "standard" training zone.
            * 🟢 **RECOVERY**: Low intent intensity. Focused on arm health, light catch, or technical "feel" drills.
            """)
