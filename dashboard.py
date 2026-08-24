import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Lady Vol Performance", layout="wide")

# --- 2. PASSWORD GATE ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password to Access Dashboard", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password to Access Dashboard", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True

# --- MAIN APP EXECUTION ---
if check_password():

    # --- 3. CUSTOM LADY VOL STYLING ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        
        /* Metric & Cards */
        [data-testid="stMetricValue"] { font-size: 26px; font-weight: 800; color: #FF8200; }
        .athlete-header {
            background-color: #F8F9FA; padding: 20px 24px; border-radius: 16px;
            border-left: 10px solid #FF8200; margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .player-photo { border-radius: 50%; width: 130px; height: 130px; object-fit: cover; border: 4px solid #4895DB; }
        .metric-sub { font-size: 13px; font-weight: 700; margin-top: -12px; margin-bottom: 10px; }
        .red-text { color: #dc3545; }
        .green-text { color: #28a745; }
        
        /* Centered Tables */
        [data-testid="stHeaderCell"] { text-align: center !important; display: flex; justify-content: center; }
        [data-testid="stTable"] td, [data-testid="stDataFrameDataLayer"] td { text-align: center !important; }
        .coach-table { width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; margin-top: 10px; }
        .coach-table th { background-color: #F8F9FA; padding: 12px; border-bottom: 2px solid #DEE2E6; color: #495057; font-weight: 700; font-size: 13px; }
        .coach-table td { padding: 12px; border-bottom: 1px solid #EEEEEE; font-size: 14px; }
        
        #MainMenu, footer, header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # --- 4. DATA LOADING & MERGING ---
    @st.cache_data(ttl=300)
    def load_all_data():
        try:
            ash_df = pd.read_csv(st.secrets["ASH_URL"])
            cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
            roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
            swing_df = pd.read_csv(st.secrets["SWING_URL"])
            throw_df = pd.read_csv(st.secrets["THROW_URL"])

            for df in [ash_df, cmj_df, roster_df, swing_df, throw_df]:
                df.columns = df.columns.str.strip()
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            photo_col = [c for c in roster_df.columns if 'photo' in c.lower() or 'picture' in c.lower()]
            if photo_col:
                roster_df = roster_df.rename(columns={photo_col[0]: 'Photo'})
            else:
                roster_df['Photo'] = 'https://www.w3schools.com/howto/img_avatar.png'

            if 'Player Name' in roster_df.columns:
                ash_df = ash_df.merge(roster_df[['Player Name', 'Photo']], on='Player Name', how='left')
                cmj_df = cmj_df.merge(roster_df[['Player Name', 'Photo']], on='Player Name', how='left')
                swing_df = swing_df.merge(roster_df[['Player Name', 'Photo']].rename(columns={'Player Name': 'Name'}), on='Name', how='left')
                throw_df = throw_df.merge(roster_df[['Player Name', 'Photo']].rename(columns={'Player Name': 'Name'}), on='Name', how='left')

            return ash_df, cmj_df, swing_df, throw_df
        except Exception as e:
            st.error(f"Data Sync Error: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    ash_df, cmj_df, swing_df, throw_df = load_all_data()

    if not ash_df.empty:
        # --- 5. SEASON SETUP ---
        TODAY = pd.to_datetime(date.today())
        SPRING_START = pd.to_datetime("2026-01-01")
        SPRING_END = pd.to_datetime("2026-05-31 23:59:59")
        FALL_START = TODAY

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            all_athletes = sorted(list(set(ash_df['Player Name'].dropna().unique())))
            selected = st.selectbox("Search Athlete", all_athletes)
        with f_col2:
            season_option = st.selectbox("Select Season", ["Spring 2026", "Fall 2026 (Current)", "All Time"])

        def filter_season(df):
            if df.empty or 'Date' not in df.columns:
                return df
            if season_option == "Spring 2026":
                return df[(df['Date'] >= SPRING_START) & (df['Date'] <= SPRING_END)]
            elif season_option == "Fall 2026 (Current)":
                return df[df['Date'] >= FALL_START]
            return df

        # Filtered subsets
        p_ash = filter_season(ash_df[ash_df['Player Name'] == selected].sort_values('Date')).copy()
        p_cmj = filter_season(cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')).copy()
        p_swing = filter_season(swing_df[swing_df['Name'] == selected].sort_values('Date')).copy()
        p_throw = filter_season(throw_df[throw_df['Name'] == selected].sort_values('Date')).copy()

        # Header Photo & Metadata
        latest_ash = p_ash.iloc[-1] if not p_ash.empty else (ash_df[ash_df['Player Name'] == selected].iloc[-1] if not ash_df[ash_df['Player Name'] == selected].empty else None)
        img_url = latest_ash.get('Photo', 'https://www.w3schools.com/howto/img_avatar.png') if latest_ash is not None else 'https://www.w3schools.com/howto/img_avatar.png'

        st.markdown(f"""
            <div class="athlete-header">
                <div style="display: flex; align-items: center;">
                    <img src="{img_url}" class="player-photo">
                    <div style="margin-left: 25px;">
                        <h1 style="margin:0; font-size:32px; font-weight:800;">{selected}</h1>
                        <p style="color:#4895DB; font-weight:700; font-size:16px; margin:4px 0 0 0;">{season_option}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- 6. NAVIGATION TABS ---
        tab_profile, tab_testing, tab_catapult = st.tabs(["INDIVIDUAL PROFILE", "TESTING PROFILE", "CATAPULT PROFILE"])

        # =========================================================================
        # TAB 1: INDIVIDUAL PROFILE
        # =========================================================================
        with tab_profile:
            st.markdown("<br>", unsafe_allow_html=True)
            all_dates = [df['Date'].max() for df in [p_ash, p_cmj, p_swing, p_throw] if not df.empty and 'Date' in df.columns]
            max_p_date = max(all_dates).date() if all_dates and pd.notnull(max(all_dates)) else date.today()
            min_p_date = max_p_date - pd.Timedelta(days=7)

            p_dates = st.date_input("Scouting Window", value=(min_p_date, max_p_date), key="prof_scout_window")

            if isinstance(p_dates, tuple) and len(p_dates) == 2:
                start_p, end_p = p_dates
                w_ash = p_ash[(p_ash['Date'].dt.date >= start_p) & (p_ash['Date'].dt.date <= end_p)]
                w_cmj = p_cmj[(p_cmj['Date'].dt.date >= start_p) & (p_cmj['Date'].dt.date <= end_p)]
                w_swing = p_swing[(p_swing['Date'].dt.date >= start_p) & (p_swing['Date'].dt.date <= end_p)]
                w_throw = p_throw[(p_throw['Date'].dt.date >= start_p) & (p_throw['Date'].dt.date <= end_p)]

                st.subheader("ATHLETE STATUS")
                s1, s2, s3, s4 = st.columns(4)

                # RSI
                rsi_col = 'RSI-modified (Imp-Mom) [m/s]'
                rsi_best = pd.to_numeric(p_cmj[rsi_col], errors='coerce').max() if rsi_col in p_cmj.columns and not p_cmj.empty else 0
                rsi_curr = pd.to_numeric(w_cmj[rsi_col], errors='coerce').mean() if rsi_col in w_cmj.columns and not w_cmj.empty else 0
                rsi_diff = rsi_curr - rsi_best
                rsi_status = "PEAKING" if rsi_curr >= (rsi_best * 0.95 and rsi_best > 0) else "STABLE" if rsi_curr >= (rsi_best * 0.85 and rsi_best > 0) else "FATIGUED"
                s1.metric("RSI-modified", rsi_status, delta=f"{rsi_diff:+.2f} vs Best" if rsi_best > 0 else "N/A")
                s1.markdown(f'<p class="metric-sub">Window Avg: <b>{rsi_curr:.2f}</b> (Best: {rsi_best:.2f})</p>', unsafe_allow_html=True)

                # ASH Asymmetry
                l_avg = pd.to_numeric(w_ash.get('Peak Vertical Force [N] (L)', 0), errors='coerce').mean() if not w_ash.empty else 0
                r_avg = pd.to_numeric(w_ash.get('Peak Vertical Force [N] (R)', 0), errors='coerce').mean() if not w_ash.empty else 0
                asym = (abs(l_avg - r_avg) / max(l_avg, r_avg) * 100) if max(l_avg, r_avg) > 0 else 0
                s2.metric("Asymmetry", f"{asym:.1f}%", delta="LOW" if asym < 10 else "HIGH", delta_color="inverse")
                s2.markdown(f'<p class="metric-sub">L: {int(l_avg)}N | R: {int(r_avg)}N</p>', unsafe_allow_html=True)

                # Load
                s_vol = pd.to_numeric(w_swing.get('Swing Count', 0), errors='coerce').sum() if not w_swing.empty else 0
                t_vol = pd.to_numeric(w_throw.get('Total Throw Count', 0), errors='coerce').sum() if not w_throw.empty else 0
                total_reps = int(s_vol + t_vol)
                s3.metric("Load", "MODERATE" if 150 < total_reps < 300 else "HIGH" if total_reps >= 300 else "LOW")
                s3.markdown(f'<p class="metric-sub">Total Reps: <b>{total_reps}</b></p>', unsafe_allow_html=True)

                # Intent
                s_int = pd.to_numeric(w_swing.get('Swing Max Rotation Band 3 Count', 0), errors='coerce').sum() if not w_swing.empty else 0
                s_qual = (s_int / s_vol * 100) if s_vol > 0 else 0
                s4.metric("Intent", "HIGH" if s_qual > 25 else "NORMAL")
                s4.markdown(f'<p class="metric-sub">Quality: <b>{s_qual:.1f}%</b></p>', unsafe_allow_html=True)

                st.divider()
                st.subheader("Window ASH Force Trend (L vs R)")
                if not w_ash.empty and 'Peak Vertical Force [N] (L)' in w_ash.columns:
                    fig_w_ash = px.line(w_ash, x='Date', y=['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)'],
                                        markers=True, color_discrete_map={'Peak Vertical Force [N] (L)': '#4895DB', 'Peak Vertical Force [N] (R)': '#FF8200'},
                                        template="plotly_white")
                    fig_w_ash.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="Force (N)", legend=dict(orientation="h", y=1.2))
                    st.plotly_chart(fig_w_ash, use_container_width=True)

                n_col, a_col = st.columns(2)
                with n_col:
                    st.subheader("COACHING NOTES")
                    st.markdown(f"""
                    * **RSI**: {rsi_status} ({rsi_curr:.2f}).
                    * **Symmetry**: {asym:.1f}% variance. {'✅ Normal' if asym < 10 else '⚠️ High - Check Lead Leg.'}
                    * **Volume**: {int(total_reps)} reps in this window.
                    """)
                with a_col:
                    st.subheader("RECENT ACTIVITY")
                    st.markdown(f"""
                    * **Hitting**: {int(s_vol)} Swings
                    * **Throwing**: {int(t_vol)} Throws
                    * **ASH Sessions**: {len(w_ash)}
                    * **CMJ Sessions**: {len(w_cmj)}
                    """)

        # =========================================================================
        # TAB 2: TESTING PROFILE (ASH & CMJ)
        # =========================================================================
        with tab_testing:
            sub_ash, sub_cmj = st.tabs(["ASH TEST", "CMJ"])

            with sub_ash:
                if not p_ash.empty:
                    lat_ash = p_ash.iloc[-1]
                    l_f = pd.to_numeric(lat_ash.get('Peak Vertical Force [N] (L)', 0), errors='coerce') or 0
                    r_f = pd.to_numeric(lat_ash.get('Peak Vertical Force [N] (R)', 0), errors='coerce') or 0
                    clean_asym = (abs(l_f - r_f) / max(l_f, r_f) * 100) if max(l_f, r_f) > 0 else 0.0

                    p_ash['Peak Vertical Force [N] (L)'] = pd.to_numeric(p_ash['Peak Vertical Force [N] (L)'], errors='coerce').fillna(0)
                    p_ash['Peak Vertical Force [N] (R)'] = pd.to_numeric(p_ash['Peak Vertical Force [N] (R)'], errors='coerce').fillna(0)
                    base_l = p_ash['Peak Vertical Force [N] (L)'].mean()
                    base_r = p_ash['Peak Vertical Force [N] (R)'].mean()

                    best_f = pd.to_numeric(p_ash.get('Peak Vertical Force [N]', 0), errors='coerce').max()
                    best_r = pd.to_numeric(p_ash.get('RFD - 200ms [N/s]', 0), errors='coerce').max()
                    best_t = pd.to_numeric(p_ash.get('Start Time to Peak Force [s]', 0), errors='coerce').min()

                    def colored_metric(label, best_val, curr_val, unit, is_time=False):
                        diff = ((curr_val - best_val) / best_val * 100) if best_val != 0 else 0
                        is_bad = diff > 10 if is_time else diff < -10
                        color = "red-text" if is_bad else "green-text"
                        st.metric(label, f"{int(best_val) if not is_time else best_val:.2f}{unit}")
                        st.markdown(f'<p class="metric-sub {color}">Latest: {curr_val:.1f}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

                    m1, m2, m3, m4 = st.columns(4)
                    with m1: colored_metric("Best Force", best_f, pd.to_numeric(lat_ash.get('Peak Vertical Force [N]', 0), errors='coerce'), " N")
                    with m2: colored_metric("Best RFD", best_r, pd.to_numeric(lat_ash.get('RFD - 200ms [N/s]', 0), errors='coerce'), " N/s")
                    with m3: st.metric("Asymmetry", f"{clean_asym:.1f}%", delta="High" if clean_asym > 10 else "Normal", delta_color="inverse")
                    with m4: colored_metric("Best Time", best_t, pd.to_numeric(lat_ash.get('Start Time to Peak Force [s]', 0), errors='coerce'), "s", is_time=True)

                    st.divider()
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.subheader("Left vs Right Force Profile")
                        side_df = pd.DataFrame({'Side': ['Left', 'Right'], 'Force [N]': [l_f, r_f]})
                        fig_side = px.bar(side_df, x='Side', y='Force [N]', text='Force [N]', color='Side',
                                          color_discrete_map={'Left': '#4895DB', 'Right': '#FF8200'}, template="plotly_white")
                        st.plotly_chart(fig_side, use_container_width=True)
                    with c2:
                        st.subheader("Balance Details")
                        l_rfd = int(pd.to_numeric(lat_ash.get('RFD - 200ms [N/s] (L)', 0), errors='coerce') or 0)
                        r_rfd = int(pd.to_numeric(lat_ash.get('RFD - 200ms [N/s] (R)', 0), errors='coerce') or 0)
                        asym_color = '#dc3545' if clean_asym > 10 else '#28a745'
                        st.markdown(f"""
                            <div style="background-color:#F8F9FA; padding:15px; border-radius:10px; border:1px solid #E0E0E0; text-align:center;">
                                <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                                    <div style="width:45%;"><p style="color:#4895DB; font-weight:800; margin:0;">LEFT</p><h2>{int(l_f)}N</h2><p style="color:grey; font-size:12px;">{l_rfd} RFD</p></div>
                                    <div style="width:45%;"><p style="color:#FF8200; font-weight:800; margin:0;">RIGHT</p><h2>{int(r_f)}N</h2><p style="color:grey; font-size:12px;">{r_rfd} RFD</p></div>
                                </div>
                                <p style="margin:0; font-size:11px; color:grey; font-weight:700;">ASYMMETRY</p>
                                <h1 style="margin:0; color:{asym_color};">{clean_asym:.1f}%</h1>
                            </div>
                        """, unsafe_allow_html=True)

                    st.divider()
                    st.subheader("Peak Force History: Left vs Right")
                    fig_trend = px.line(p_ash, x='Date', y=['Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)'],
                                        markers=True, color_discrete_map={'Peak Vertical Force [N] (L)': '#4895DB', 'Peak Vertical Force [N] (R)': '#FF8200'},
                                        template="plotly_white")
                    fig_trend.update_layout(height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_trend, use_container_width=True)

                    st.divider()
                    st.subheader("Test History (Match Proximity)")
                    match_map = {}
                    try:
                        all_sess = pd.concat([swing_df, throw_df], ignore_index=True)
                        ath_games = all_sess[(all_sess['Name'] == selected) & (all_sess['Session Type'].astype(str).str.contains('Game', case=False, na=False))]
                        for _, row in ath_games.iterrows():
                            match_map[row['Date'].date()] = f"{row.get('Activity', 'Game')}"
                    except:
                        pass

                    ash_hist = p_ash[['Date', 'Peak Vertical Force [N] (L)', 'Peak Vertical Force [N] (R)']].copy()
                    def get_match_ctx(t_date):
                        d = t_date.date()
                        past_matches = [m for m in match_map.keys() if m <= d]
                        if not past_matches: return "N/A", 999
                        near = max(past_matches)
                        return match_map[near], (d - near).days

                    ash_hist[['Prev Match', 'Days Since']] = ash_hist['Date'].apply(lambda x: pd.Series(get_match_ctx(x)))
                    ash_table = ash_hist[ash_hist['Days Since'] <= 3].sort_values('Date', ascending=False).copy()

                    if not ash_table.empty:
                        ash_table['L vs Base'] = ash_table['Peak Vertical Force [N] (L)'] - base_l
                        ash_table['R vs Base'] = ash_table['Peak Vertical Force [N] (R)'] - base_r
                        ash_disp = ash_table[['Date', 'Prev Match', 'Peak Vertical Force [N] (L)', 'L vs Base', 'Peak Vertical Force [N] (R)', 'R vs Base']].copy()
                        ash_disp['Date'] = ash_disp['Date'].dt.strftime('%m/%d/%Y')
                        ash_disp.columns = ['Test Date', 'Previous Match', 'Force (L)', '+/- Base (L)', 'Force (R)', '+/- Base (R)']
                        st.dataframe(
                            ash_disp.style.format({'Force (L)': '{:.0f}N', '+/- Base (L)': '{:+.1f}N', 'Force (R)': '{:.0f}N', '+/- Base (R)': '{:+.1f}N'})
                            .map(lambda x: f'color: {"#28a745" if x > 0 else "#dc3545"}; font-weight: bold', subset=['+/- Base (L)', '+/- Base (R)']),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("No ASH tests found within 3 days of a match.")
                else:
                    st.info("No ASH records found for this season.")

            with sub_cmj:
                if not p_cmj.empty:
                    metrics_map = {
                        'Jump Height (Imp-Mom) [cm]': 'Jump Height (cm)',
                        'Peak Power [W]': 'Peak Power (W)',
                        'RSI-modified (Imp-Mom) [m/s]': 'RSI-m',
                        'Force at Zero Velocity [N]': 'Force @ Zero Velocity (N)',
                        'Eccentric Braking RFD [N/s]': 'Ecc. Braking RFD (N/s)',
                        'Concentric Peak Velocity [m/s]': 'Conc. Peak Velocity (m/s)'
                    }
                    for m in metrics_map.keys():
                        p_cmj[m] = pd.to_numeric(p_cmj[m], errors='coerce').fillna(0) if m in p_cmj.columns else 0.0

                    c_lat = p_cmj.iloc[-1]
                    st.subheader("CMJ Season Bests & Latest Status")

                    def cmj_metric_box(col, label_text, col_name, unit, precision=".1f"):
                        best_val = p_cmj[col_name].max()
                        curr_val = c_lat[col_name]
                        diff = ((curr_val - best_val) / best_val * 100) if best_val != 0 else 0
                        col.metric(label_text, f"{best_val:{precision}}{unit}")
                        color = "red-text" if diff < -10 else "green-text"
                        col.markdown(f'<p class="metric-sub {color}">Latest: {curr_val:{precision}}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

                    m_keys = list(metrics_map.keys())
                    r1 = st.columns(3)
                    cmj_metric_box(r1[0], "Best Jump Height", m_keys[0], " cm")
                    cmj_metric_box(r1[1], "Best Peak Power", m_keys[1], " W", precision=".0f")
                    cmj_metric_box(r1[2], "Best RSI-m", m_keys[2], "")

                    r2 = st.columns(3)
                    cmj_metric_box(r2[0], "Force @ Zero Velocity", m_keys[3], " N", precision=".0f")
                    cmj_metric_box(r2[1], "Ecc. Braking RFD", m_keys[4], " N/s", precision=".0f")
                    cmj_metric_box(r2[2], "Conc. Peak Velocity", m_keys[5], " m/s", precision=".2f")

                    st.divider()
                    st.subheader("Performance Trends: All Metrics")

                    def create_sparkline(df, y_col, title_text):
                        fig = px.line(df, x='Date', y=y_col, markers=True, template="plotly_white", color_discrete_sequence=["#FF8200"])
                        fig.update_layout(height=280, title={'text': title_text, 'x': 0.5, 'xanchor': 'center'},
                                          xaxis_title="", yaxis_title="", margin=dict(t=40, b=10, l=10, r=10),
                                          yaxis=dict(range=[0, max(df[y_col].max() * 1.1, 1)]))
                        return fig

                    g1, g2 = st.columns(2)
                    with g1: st.plotly_chart(create_sparkline(p_cmj, m_keys[0], metrics_map[m_keys[0]]), use_container_width=True)
                    with g2: st.plotly_chart(create_sparkline(p_cmj, m_keys[1], metrics_map[m_keys[1]]), use_container_width=True)

                    g3, g4 = st.columns(2)
                    with g3: st.plotly_chart(create_sparkline(p_cmj, m_keys[2], metrics_map[m_keys[2]]), use_container_width=True)
                    with g4: st.plotly_chart(create_sparkline(p_cmj, m_keys[3], metrics_map[m_keys[3]]), use_container_width=True)

                    g5, g6 = st.columns(2)
                    with g5: st.plotly_chart(create_sparkline(p_cmj, m_keys[4], metrics_map[m_keys[4]]), use_container_width=True)
                    with g6: st.plotly_chart(create_sparkline(p_cmj, m_keys[5], metrics_map[m_keys[5]]), use_container_width=True)
                else:
                    st.info("No CMJ records found for this season.")

        # =========================================================================
        # TAB 3: CATAPULT PROFILE (SWING & THROW)
        # =========================================================================
        with tab_catapult:
            sub_swing, sub_throw = st.tabs(["SWING", "THROW"])

            with sub_swing:
                if not p_swing.empty:
                    f1, f2 = st.columns([2, 1])
                    with f1:
                        df_s_dates = pd.to_datetime(p_swing['Date'])
                        max_s = df_s_dates.max()
                        min_s = max_s - pd.Timedelta(days=7)
                        sel_dates_s = st.date_input("Select Date Range", value=(min_s.date(), max_s.date()), key="s_tab_dates")
                    with f2:
                        s_cat = st.segmented_control("Session Type", options=["All", "Games", "Practices"], default="All", key="s_tab_cat")

                    if isinstance(sel_dates_s, tuple) and len(sel_dates_s) == 2:
                        p_s_filt = p_swing[(p_swing['Date'].dt.date >= sel_dates_s[0]) & (p_swing['Date'].dt.date <= sel_dates_s[1])].copy()
                        if s_cat == "Games":
                            p_s_filt = p_s_filt[p_s_filt['Session Type'].astype(str).str.contains('Game', case=False, na=False)]
                        elif s_cat == "Practices":
                            p_s_filt = p_s_filt[p_s_filt['Session Type'].astype(str).str.contains('Practice|Session', case=False, na=False)]

                        if not p_s_filt.empty:
                            p_s_filt['Total'] = pd.to_numeric(p_s_filt.get('Swing Count', 0), errors='coerce').fillna(0)
                            p_s_filt['Max Intent'] = pd.to_numeric(p_s_filt.get('Swing Max Rotation Band 3 Count', 0), errors='coerce').fillna(0)
                            p_s_filt['Load'] = pd.to_numeric(p_s_filt.get('Sum Swing Max Player Load', 0), errors='coerce').fillna(0)
                            p_s_filt['Intensity'] = p_s_filt['Load'] / p_s_filt['Total'].replace(0, 1)
                            p_s_filt['Rot_Pct'] = pd.to_numeric(p_s_filt.get('Swing Max Player Load Side % (median)', 0), errors='coerce').fillna(0)

                            latest_s = p_s_filt.iloc[-1]
                            intent_val = int(latest_s['Max Intent'])
                            total_swings = int(latest_s['Total'])
                            intent_pct = (intent_val / total_swings * 100) if total_swings > 0 else 0

                            if intent_pct > 25: status, color, note = "EXPLOSIVE", "#dc3545", "High percentage of Max Intent swings. Training for power/speed."
                            elif intent_pct > 10: status, color, note = "STEADY", "#ffc107", "Standard training output. Good for maintenance and skill work."
                            else: status, color, note = "LOW OUTPUT", "#28a745", "Sub-maximal effort. Focused on technical feel or recovery."

                            st.markdown(f"""
                                <div style="background-color:{color}; padding:20px; border-radius:15px; color:white; text-align:center;">
                                    <h1 style="margin:0; font-size:30px;">{status} SESSION</h1>
                                    <p style="margin:0; font-size:16px; opacity:0.95;">Latest Session: {latest_s['Date'].strftime('%m/%d')} — {note}</p>
                                </div>
                            """, unsafe_allow_html=True)

                            st.divider()
                            st.subheader(f"Swing Report: {sel_dates_s[0].strftime('%m/%d')} - {sel_dates_s[1].strftime('%m/%d')}")
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Total Swings", f"{int(p_s_filt['Total'].sum())}")
                            m2.metric("Max Intent", f"{int(p_s_filt['Max Intent'].sum())}")
                            m3.metric("Load/Sw (Intensity)", f"{p_s_filt['Intensity'].mean():.2f}")
                            m4.metric("Avg Rot %", f"{p_s_filt['Rot_Pct'].mean():.1f}%")

                            st.divider()
                            p_s_filt['Session'] = p_s_filt['Session Type'].apply(lambda x: 'Game' if 'Game' in str(x) else 'Practice')
                            fig_s = px.bar(p_s_filt, x='Date', y='Total', color='Session', color_discrete_map={'Game': '#4895DB', 'Practice': '#FF8200'}, text='Total', template="plotly_white")
                            fig_s.update_traces(texttemplate='%{text:.0f}', textposition='outside', cliponaxis=False)
                            fig_s.update_layout(height=350, yaxis_visible=False, xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""), xaxis=dict(tickformat="%m/%d"))
                            st.plotly_chart(fig_s, use_container_width=True)

                            st.subheader("Session Details")
                            hist_s = p_s_filt.sort_values('Date', ascending=False).copy()
                            hist_s['Date_Str'] = hist_s['Date'].dt.strftime('%m/%d')
                            rows_s = [f"<tr><td>{r['Date_Str']}</td><td>{r['Session Type']}</td><td>{int(r['Total'])}</td><td>{int(r['Max Intent'])}</td><td>{r['Intensity']:.2f}</td><td>{r['Rot_Pct']:.1f}%</td></tr>" for _, r in hist_s.iterrows()]
                            st.markdown(f'<table class="coach-table"><thead><tr><th>Date</th><th>Type</th><th>Total</th><th>Max Intent</th><th>Load/Sw</th><th>Rot %</th></tr></thead><tbody>{"".join(rows_s)}</tbody></table>', unsafe_allow_html=True)
                        else:
                            st.info(f"No swing records found for {selected} in this range.")

            with sub_throw:
                if not p_throw.empty:
                    f1, f2 = st.columns([2, 1])
                    with f1:
                        df_t_dates = pd.to_datetime(p_throw['Date'])
                        max_date = df_t_dates.max()
                        min_date = max_date - pd.Timedelta(days=7)
                        sel_dates_t = st.date_input("Select Date Range", value=(min_date.date(), max_date.date()), key="t_tab_dates")
                    with f2:
                        t_cat = st.segmented_control("Session Type", options=["All", "Games", "Practices"], default="All", key="t_tab_cat")

                    if isinstance(sel_dates_t, tuple) and len(sel_dates_t) == 2:
                        p_t_filt = p_throw[(p_throw['Date'].dt.date >= sel_dates_t[0]) & (p_throw['Date'].dt.date <= sel_dates_t[1])].copy()
                        if t_cat == "Games":
                            p_t_filt = p_t_filt[p_t_filt['Session Type'].astype(str).str.contains('Game', case=False, na=False)]
                        elif t_cat == "Practices":
                            p_t_filt = p_t_filt[p_t_filt['Session Type'].astype(str).str.contains('Practice|Session', case=False, na=False)]

                        if not p_t_filt.empty:
                            p_t_filt['Throws'] = pd.to_numeric(p_t_filt.get('Total Throw Count', 0), errors='coerce').fillna(0)
                            p_t_filt['Intent'] = pd.to_numeric(p_t_filt.get('Total Throw Count - Rotation Band 3', 0), errors='coerce').fillna(0)

                            latest_t = p_t_filt.iloc[-1]
                            intent_val = int(latest_t['Intent'])
                            if intent_val > 15: status, color, note = "HIGH INTENT", "#dc3545", "Max effort defensive/pitching work detected."
                            elif intent_val > 5: status, color, note = "MODERATE", "#ffc107", "Standard skill work or active warm-up."
                            else: status, color, note = "RECOVERY", "#28a745", "Light catch or low-intent technical work."

                            st.markdown(f"""
                                <div style="background-color:{color}; padding:20px; border-radius:15px; color:white; text-align:center;">
                                    <h1 style="margin:0; font-size:30px;">{status} SESSION</h1>
                                    <p style="margin:0; font-size:16px; opacity:0.95;">Latest Session: {latest_t['Date'].strftime('%m/%d')} — {note}</p>
                                </div>
                            """, unsafe_allow_html=True)

                            st.divider()
                            st.subheader(f"Summary: {sel_dates_t[0].strftime('%m/%d')} - {sel_dates_t[1].strftime('%m/%d')}")
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Total Range Volume", f"{int(p_t_filt['Throws'].sum())} Throws")
                            c2.metric("Total High-Intent", f"{int(p_t_filt['Intent'].sum())}")
                            avg_q = (p_t_filt['Intent'].sum() / p_t_filt['Throws'].sum() * 100) if p_t_filt['Throws'].sum() > 0 else 0
                            c3.metric("Avg Work Quality", f"{avg_q:.1f}%")

                            st.divider()
                            p_t_filt['Session'] = p_t_filt['Session Type'].apply(lambda x: 'Game' if 'Game' in str(x) else 'Practice')
                            fig_t = px.bar(p_t_filt, x='Date', y='Throws', color='Session', color_discrete_map={'Game': '#4895DB', 'Practice': '#FF8200'}, text='Throws', template="plotly_white")
                            fig_t.update_traces(texttemplate='%{text}', textposition='outside', cliponaxis=False)
                            fig_t.update_layout(height=350, yaxis_visible=False, xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""), xaxis=dict(tickformat="%m/%d"))
                            st.plotly_chart(fig_t, use_container_width=True)

                            st.subheader("Session Details")
                            hist_t = p_t_filt.sort_values('Date', ascending=False).copy()
                            hist_t['Date_Str'] = hist_t['Date'].dt.strftime('%m/%d')
                            rows_t = [f"<tr><td>{r['Date_Str']}</td><td>{r['Session Type']}</td><td>{int(r['Throws'])}</td><td>{int(r['Intent'])}</td></tr>" for _, r in hist_t.iterrows()]
                            st.markdown(f'<table class="coach-table"><thead><tr><th>Date</th><th>Session Type</th><th>Total</th><th>High Intent</th></tr></thead><tbody>{"".join(rows_t)}</tbody></table>', unsafe_allow_html=True)
                        else:
                            st.info(f"No throwing records found for {selected} in this range.")
