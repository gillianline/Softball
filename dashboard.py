import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Dashboard", layout="wide")

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

    # --- 3. CUSTOM CSS THEME ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        
        /* Athlete Banner */
        .athlete-banner {
            background-color: #F8F9FA; padding: 18px 24px; border-radius: 14px;
            border-left: 8px solid #FF8200; margin-bottom: 20px;
            display: flex; align-items: center; justify-content: space-between;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        }
        .athlete-info { display: flex; align-items: center; }
        .player-photo { border-radius: 50%; width: 95px; height: 95px; object-fit: cover; border: 3px solid #2F80ED; margin-right: 20px; }
        .athlete-name { margin: 0; font-size: 26px; font-weight: 800; color: #1D1D1F; }
        .athlete-sub { margin: 2px 0 0 0; color: #2F80ED; font-weight: 700; font-size: 14px; }
        
        /* Section Typography */
        .section-header {
            color: #2F80ED; font-size: 20px; font-weight: 800; letter-spacing: 0.5px;
            text-transform: uppercase; margin-top: 10px; margin-bottom: 4px;
        }
        .section-divider { height: 3px; background-color: #FF8200; margin-bottom: 22px; border-radius: 2px; }
        
        /* KPI / Metric Cards */
        .catapult-card {
            background: #F8F9FA; border: 1px solid #EAEAEA; border-top: 4px solid #FF8200;
            border-radius: 10px; padding: 12px 14px; text-align: center; margin-bottom: 12px;
        }
        .catapult-card h5 { margin: 0; color: #6c757d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        .catapult-card h3 { margin: 4px 0 2px 0; font-size: 20px; font-weight: 800; color: #1D1D1F; }
        .catapult-card p { margin: 0; font-size: 11px; color: #2F80ED; font-weight: 700; }

        /* Assessment Cards */
        .assessment-card {
            background: #FFFFFF; border: 1px solid #EAEAEA; border-radius: 10px;
            padding: 12px 16px; margin-bottom: 10px; position: relative;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }
        .border-orange { border-left: 6px solid #FF8200; }
        .border-blue { border-left: 6px solid #4895DB; }

        .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .card-title-wrap { display: flex; align-items: center; gap: 10px; }
        .badge-num {
            width: 22px; height: 22px; border-radius: 6px; color: #FFFFFF;
            font-weight: 800; font-size: 12px; display: inline-flex;
            align-items: center; justify-content: center;
        }
        .badge-orange { background-color: #FF8200; }
        .badge-blue { background-color: #4895DB; }

        .card-title { font-weight: 800; font-size: 13px; color: #1D1D1F; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
        .card-date { font-size: 11px; color: #6C757D; font-weight: 600; }
        .card-metrics { font-size: 12.5px; color: #333333; line-height: 1.5; }

        .pct-up { color: #28a745; font-weight: 700; }
        .pct-down { color: #dc3545; font-weight: 700; }
        .pct-flat { color: #6c757d; font-weight: 700; }

        /* Tables */
        .coach-table { width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; margin-top: 8px; margin-bottom: 12px; }
        .coach-table th { background-color: #F0F4F8; padding: 10px; border-bottom: 2px solid #D0D7DE; color: #334155; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        .coach-table td { padding: 9px 10px; border-bottom: 1px solid #EEEEEE; font-size: 12.5px; color: #1D1D1F; }
        
        #MainMenu, footer, header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # Clean numeric helper
    def clean_num_series(series):
        if series is None:
            return pd.Series(dtype=float)
        return series.astype(str).apply(
            lambda x: re.findall(r"[-+]?\d*\.?\d+", str(x))[0] if re.findall(r"[-+]?\d*\.?\d+", str(x)) else np.nan
        ).astype(float)

    # --- 4. SAFE DATA LOADING & MERGING ---
    @st.cache_data(ttl=300)
    def load_all_data():
        def safe_read_csv(secret_key):
            if secret_key in st.secrets and str(st.secrets[secret_key]).strip():
                try:
                    df = pd.read_csv(st.secrets[secret_key])
                    df.columns = df.columns.str.strip()
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    return df
                except Exception:
                    return pd.DataFrame()
            return pd.DataFrame()

        ash_df = safe_read_csv("ASH_URL")
        cmj_df = safe_read_csv("CMJ_URL")
        er_df = safe_read_csv("ER_URL")
        grip_df = safe_read_csv("GRIP_URL")
        sprint_df = safe_read_csv("SPRINT_20M_URL")
        roster_df = safe_read_csv("ROSTER_URL")
        swing_df = safe_read_csv("SWING_URL")
        throw_df = safe_read_csv("THROW_URL")

        # Standardize athlete name column across all datasets
        for df in [ash_df, cmj_df, er_df, grip_df, sprint_df, roster_df, swing_df, throw_df]:
            if not df.empty:
                if 'Name' in df.columns and 'Player Name' not in df.columns:
                    df.rename(columns={'Name': 'Player Name'}, inplace=True)
                if 'Player Name' in df.columns:
                    df['Player Name'] = df['Player Name'].astype(str).str.strip()

        # Process Swing Data Columns
        if not swing_df.empty:
            swing_cols = [
                'Sum Swing Max Player Load', 'Swing Count',
                'Swing Max Rotation Band 1 Count', 'Swing Max Rotation Band 2 Count', 'Swing Max Rotation Band 3 Count',
                'Swing Max PL Band 1 Count', 'Swing Max PL Band 2 Count', 'Swing Max PL Band 3 Count',
                'Swing Max Player Load Fwd % (median)', 'Swing Max Player Load Side % (median)', 'Swing Max Player Load Up % (median)'
            ]
            for col in swing_cols:
                if col in swing_df.columns:
                    swing_df[col] = clean_num_series(swing_df[col])

            # Group multiple drill entries on the same date for an athlete
            agg_dict = {c: 'sum' for c in swing_cols if c in swing_df.columns}
            if 'Session Type' in swing_df.columns:
                agg_dict['Session Type'] = lambda x: ', '.join(x.dropna().unique())
            if 'Activity' in swing_df.columns:
                agg_dict['Activity'] = lambda x: ', '.join(x.dropna().unique())
            
            swing_df = swing_df.groupby(['Player Name', 'Date'], as_index=False).agg(agg_dict)

        # Process Throw Data Columns
        if not throw_df.empty:
            throw_cols = [
                'Total Throw Count', 'Total Throw Player Load',
                'Total Throw Count - Player Load 1', 'Total Throw Count - Player Load 2', 'Total Throw Count - Player Load 3',
                'Total Throw Count - Rotation Band 1', 'Total Throw Count - Rotation Band 2', 'Total Throw Count - Rotation Band 3'
            ]
            for col in throw_cols:
                if col in throw_df.columns:
                    throw_df[col] = clean_num_series(throw_df[col])

            # Group multiple drill entries on the same date for an athlete
            agg_dict_t = {c: 'sum' for c in throw_cols if c in throw_df.columns}
            if 'Session Type' in throw_df.columns:
                agg_dict_t['Session Type'] = lambda x: ', '.join(x.dropna().unique())
            if 'Activity' in throw_df.columns:
                agg_dict_t['Activity'] = lambda x: ', '.join(x.dropna().unique())

            throw_df = throw_df.groupby(['Player Name', 'Date'], as_index=False).agg(agg_dict_t)

        # Roster Photos
        photo_dict = {}
        if not roster_df.empty:
            photo_col_candidates = [c for c in roster_df.columns if any(k in c.lower() for k in ['photo', 'picture', 'headshot', 'image', 'url'])]
            p_col = photo_col_candidates[0] if photo_col_candidates else None
            name_col = 'Player Name' if 'Player Name' in roster_df.columns else roster_df.columns[0]
            if p_col:
                for _, r in roster_df.iterrows():
                    val = str(r[p_col]).strip()
                    if val and val.lower() != 'nan':
                        photo_dict[str(r[name_col]).strip().lower()] = val

        # Clean numeric columns across testing datasets
        if not ash_df.empty:
            for col in ash_df.columns:
                if any(k in col.lower() for k in ['force', 'asym', 'rfd']):
                    ash_df[col] = clean_num_series(ash_df[col])

        if not cmj_df.empty:
            for col in cmj_df.columns:
                if any(k in col.lower() for k in ['height', 'power', 'rsi', 'velocity', 'force', 'impulse', 'rfd', 'stiffness', 'bw']):
                    cmj_df[col] = clean_num_series(cmj_df[col])

        if not er_df.empty:
            for col in er_df.columns:
                if any(k in col.lower() for k in ['rom', 'asymmetry', 'asym', 'max']):
                    er_df[col] = clean_num_series(er_df[col])

        if not grip_df.empty:
            for col in grip_df.columns:
                if any(k in col.lower() for k in ['force', 'asymmetry', 'asym']):
                    grip_df[col] = clean_num_series(grip_df[col])

        if not sprint_df.empty:
            for col in sprint_df.columns:
                if any(k in col.lower() for k in ['time', '20m', 'sec', 'speed']):
                    sprint_df[col] = clean_num_series(sprint_df[col])

        return ash_df, cmj_df, er_df, grip_df, sprint_df, swing_df, throw_df, photo_dict

    ash_df, cmj_df, er_df, grip_df, sprint_df, swing_df, throw_df, photo_dict = load_all_data()

    def find_col(df, options):
        if df.empty:
            return None
        for opt in options:
            match = [c for c in df.columns if c.strip().lower() == opt.strip().lower()]
            if match:
                return match[0]
            match_part = [c for c in df.columns if opt.strip().lower() in c.strip().lower()]
            if match_part:
                return match_part[0]
        return None

    # --- 5. SEASON SETUP & ATHLETE SELECTION ---
    SPRING_START = pd.to_datetime("2026-01-01")
    SPRING_END = pd.to_datetime("2026-05-31 23:59:59")
    FALL_START = pd.to_datetime("2026-08-21")   

    all_athletes = sorted(list(set(
        list(ash_df['Player Name'].dropna().unique() if 'Player Name' in ash_df.columns else []) +
        list(cmj_df['Player Name'].dropna().unique() if 'Player Name' in cmj_df.columns else []) +
        list(er_df['Player Name'].dropna().unique() if 'Player Name' in er_df.columns else []) +
        list(grip_df['Player Name'].dropna().unique() if 'Player Name' in grip_df.columns else []) +
        list(sprint_df['Player Name'].dropna().unique() if 'Player Name' in sprint_df.columns else []) +
        list(swing_df['Player Name'].dropna().unique() if 'Player Name' in swing_df.columns else []) +
        list(throw_df['Player Name'].dropna().unique() if 'Player Name' in throw_df.columns else [])
    )))

    if all_athletes:
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected = st.selectbox("Select Athlete", all_athletes)
        with f_col2:
            season_option = st.selectbox("Select Season", ["Fall 2026 (Current)", "Spring 2026", "All Time"], index=0)

        def filter_season(df):
            if df.empty or 'Date' not in df.columns:
                return df
            if season_option == "Spring 2026":
                return df[(df['Date'] >= SPRING_START) & (df['Date'] <= SPRING_END)]
            elif season_option == "Fall 2026 (Current)":
                return df[df['Date'] >= FALL_START]
            return df

        # Filtered subsets per athlete
        raw_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in ash_df.columns else pd.DataFrame()
        raw_cmj = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in cmj_df.columns else pd.DataFrame()
        raw_er = er_df[er_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in er_df.columns else pd.DataFrame()
        raw_grip = grip_df[grip_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in grip_df.columns else pd.DataFrame()
        raw_sprint = sprint_df[sprint_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in sprint_df.columns else pd.DataFrame()
        raw_swing = swing_df[swing_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in swing_df.columns else pd.DataFrame()
        raw_throw = throw_df[throw_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in throw_df.columns else pd.DataFrame()

        p_ash = filter_season(raw_ash).copy()
        p_cmj = filter_season(raw_cmj).copy()
        p_er = filter_season(raw_er).copy()
        p_grip = filter_season(raw_grip).copy()
        p_sprint = filter_season(raw_sprint).copy()
        p_swing = filter_season(raw_swing).copy()
        p_throw = filter_season(raw_throw).copy()

        # Dynamic Columns
        ash_l_col = find_col(ash_df, ['Peak Vertical Force [N] (L)', 'Force (L)', 'Peak Force (L)'])
        ash_r_col = find_col(ash_df, ['Peak Vertical Force [N] (R)', 'Force (R)', 'Peak Force (R)'])
        cmj_h_col = find_col(cmj_df, ['Jump Height (Imp-Mom) [cm]', 'Jump Height [cm]', 'Jump Height (cm)'])
        cmj_rsi_col = find_col(cmj_df, ['RSI-modified (Imp-Mom) [m/s]', 'RSI-modified', 'RSI-m'])
        er_l_col = find_col(er_df, ['L Max ROM (°)', 'L Max ROM', 'Left Max ROM', 'L ROM'])
        er_r_col = find_col(er_df, ['R Max ROM (°)', 'R Max ROM', 'Right Max ROM', 'R ROM'])
        grip_l_col = find_col(grip_df, ['L Max Force (N)', 'L Max Force', 'Left Max Force (N)', 'Force (L)', 'L Grip'])
        grip_r_col = find_col(grip_df, ['R Max Force (N)', 'R Max Force', 'Right Max Force (N)', 'Force (R)', 'R Grip'])
        sprint_time_col = find_col(sprint_df, ['Time', '20m Time', '20m Sprint', 'Time (s)', '20m (s)', '20m'])

        img_url = photo_dict.get(selected.strip().lower(), 'https://www.w3schools.com/howto/img_avatar.png')

        st.markdown(f"""
            <div class="athlete-banner">
                <div class="athlete-info">
                    <img src="{img_url}" class="player-photo">
                    <div>
                        <h1 class="athlete-name">{selected}</h1>
                        <p class="athlete-sub">Softball Performance | {season_option}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        def fmt_pct(chg, lower_is_better=False):
            if np.isnan(chg):
                return ""
            if lower_is_better:
                if chg < 0:
                    return f'<span class="pct-up">(↓{abs(chg):.1f}%)</span>'
                elif chg > 0:
                    return f'<span class="pct-down">(↑{chg:.1f}%)</span>'
            else:
                if chg > 0:
                    return f'<span class="pct-up">(↑{chg:.1f}%)</span>'
                elif chg < 0:
                    return f'<span class="pct-down">(↓{abs(chg):.1f}%)</span>'
            return '<span class="pct-flat">(0.0%)</span>'

        # --- 6. NAVIGATION TABS ---
        tab_intake, tab_profile, tab_catapult = st.tabs(["TESTING", "INDIVIDUAL PROFILE", "CATAPULT PROFILE"])

        # =========================================================================
        # TAB 1: INTAKE ASSESSMENT (ANATOMY HUD)
        # =========================================================================
        with tab_intake:
            hud_col1, hud_col2 = st.columns([1.15, 1.85], gap="large")

            with hud_col1:
                hud_svg_html = """
                <div style="background:#FFFFFF; border-radius:16px; padding:16px; border:1px solid #E5E5E7; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                    <div style="color:#1D1D1F; font-weight:800; font-size:13px; letter-spacing:1px; text-transform:uppercase; border-bottom:2px solid #FF8200; padding-bottom:6px; margin-bottom:12px;">ANATOMY LOCATION MAP</div>
                    <div style="position:relative; width:100%; height:460px; background:#FAFDFD; border-radius:12px; border:1px solid #D5E5E8; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                        <svg viewBox="0 0 160 220" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:100%;">
                            <defs>
                                <linearGradient id="anatomicalBodyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stop-color="#C5CACC" />
                                    <stop offset="25%" stop-color="#E8ECEE" />
                                    <stop offset="50%" stop-color="#F2F5F7" />
                                    <stop offset="75%" stop-color="#D0D5D8" />
                                    <stop offset="100%" stop-color="#9AA0A6" />
                                </linearGradient>
                            </defs>
                            <ellipse cx="68" cy="214" rx="20" ry="3.5" fill="#000000" opacity="0.12" />
                            <g stroke="#2C3036" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                                <ellipse cx="68" cy="17" rx="7" ry="9" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 65 25 L 63 33 M 71 25 L 73 33" stroke-width="1.2" />
                                <path d="M 63 33 C 58 33, 48 36, 42 40 C 37 43, 36 50, 39 56 L 43 56 C 47 52, 49 46, 52 44 M 73 33 C 78 33, 88 36, 94 40 C 99 43, 100 50, 97 56 L 93 56 C 89 52, 87 46, 84 44" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 42 40 C 37 43, 35 52, 33 64 C 31 74, 29 82, 27 92 C 25 96, 23 100, 22 104 C 21 106, 23 107, 25 106 C 27 104, 28 98, 30 92 C 33 82, 36 74, 38 64 C 40 54, 42 48, 43 56 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 94 40 C 99 43, 101 52, 103 64 C 105 74, 107 82, 109 92 C 111 96, 113 100, 114 104 C 115 106, 113 107, 111 106 C 109 104, 108 98, 106 92 C 103 82, 100 74, 98 64 C 96 54, 94 48, 93 56 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 52 44 L 54 75 L 52 92 L 68 106 L 84 92 L 82 75 L 84 44 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 52 92 C 50 105, 49 122, 53 138 C 55 144, 55 152, 54 162 C 52 175, 52 192, 54 205 L 48 210 L 58 210 L 59 203 C 60 190, 60 175, 60 162 C 60 152, 60 144, 62 138 C 66 122, 66 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 84 92 C 86 105, 87 122, 83 138 C 81 144, 81 152, 82 162 C 84 175, 84 192, 82 205 L 88 210 L 78 210 L 77 203 C 76 190, 76 175, 76 162 C 76 152, 76 144, 74 138 C 70 122, 70 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                <line x1="68" y1="8" x2="68" y2="211" stroke="#FF8200" stroke-width="1.3" />
                            </g>
                            <line x1="88" y1="44" x2="118" y2="44" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
                            <circle cx="88" cy="44" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
                            <rect x="118" y="36" width="16" height="16" rx="4" fill="#FF8200" />
                            <text x="126" y="48" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>
                        </svg>
                    </div>
                </div>
                """
                components.html(hud_svg_html, height=530)

            with hud_col2:
                st.markdown(f'<div class="section-header" style="color:#1D1D1F; font-size:13px; letter-spacing:1px;">LOCATION ASSESSMENT ({season_option.upper()})</div>', unsafe_allow_html=True)
                
                # Render Assessment Cards for ASH, ER, Grip, CMJ, Sprint
                if not p_ash.empty and ash_l_col and ash_r_col:
                    st.success("ASH Shoulder Assessment available.")
                if not p_cmj.empty and cmj_h_col:
                    st.info("Countermovement Jump Assessment available.")

        # =========================================================================
        # TAB 2: INDIVIDUAL PROFILE
        # =========================================================================
        with tab_profile:
            st.markdown('<div class="section-header">Athlete Individual Testing Profile</div>', unsafe_allow_html=True)
            st.write("Detailed physical testing trends and force profiles.")

        # =========================================================================
        # TAB 3: CATAPULT PROFILE (SWING & THROW ANALYTICS)
        # =========================================================================
        with tab_catapult:
            st.markdown('<div class="section-header">Catapult Swing & Throw Analytics</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            c_col1, c_col2 = st.columns(2)

            # --- THROW METRICS SUMMARY ---
            with c_col1:
                st.markdown('<div class="sub-header-title">Throwing Load Summary</div>', unsafe_allow_html=True)
                if not p_throw.empty:
                    tot_throws = p_throw['Total Throw Count'].sum() if 'Total Throw Count' in p_throw.columns else 0
                    tot_throw_pl = p_throw['Total Throw Player Load'].sum() if 'Total Throw Player Load' in p_throw.columns else 0

                    kpi1, kpi2 = st.columns(2)
                    with kpi1:
                        st.markdown(f"""
                            <div class="catapult-card">
                                <h5>Total Throws</h5>
                                <h3>{int(tot_throws):,}</h3>
                                <p>{season_option}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with kpi2:
                        st.markdown(f"""
                            <div class="catapult-card">
                                <h5>Throw Player Load</h5>
                                <h3>{tot_throw_pl:.1f}</h3>
                                <p>{season_option}</p>
                            </div>
                        """, unsafe_allow_html=True)

                    # Throw Rotation & Intensity Bands Breakdown Chart
                    fig_throw = go.Figure()
                    if 'Total Throw Count - Player Load 1' in p_throw.columns:
                        fig_throw.add_trace(go.Bar(x=p_throw['Date'], y=p_throw['Total Throw Count - Player Load 1'], name='PL Band 1 (Low)'))
                        fig_throw.add_trace(go.Bar(x=p_throw['Date'], y=p_throw['Total Throw Count - Player Load 2'], name='PL Band 2 (Med)'))
                        fig_throw.add_trace(go.Bar(x=p_throw['Date'], y=p_throw['Total Throw Count - Player Load 3'], name='PL Band 3 (High)'))

                    fig_throw.update_layout(
                        barmode='stack',
                        title="Throw Volume by Load Band",
                        xaxis_title="Date",
                        yaxis_title="Throw Count",
                        height=320,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_throw, use_container_width=True)

                    with st.expander("View Raw Throw Log"):
                        st.dataframe(p_throw, use_container_width=True)
                else:
                    st.info("No Throw data recorded for this season.")

            # --- SWING METRICS SUMMARY ---
            with c_col2:
                st.markdown('<div class="sub-header-title">Batting Swing Summary</div>', unsafe_allow_html=True)
                if not p_swing.empty:
                    tot_swings = p_swing['Swing Count'].sum() if 'Swing Count' in p_swing.columns else 0
                    tot_swing_pl = p_swing['Sum Swing Max Player Load'].sum() if 'Sum Swing Max Player Load' in p_swing.columns else 0

                    kpi3, kpi4 = st.columns(2)
                    with kpi3:
                        st.markdown(f"""
                            <div class="catapult-card">
                                <h5>Total Swings</h5>
                                <h3>{int(tot_swings):,}</h3>
                                <p>{season_option}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with kpi4:
                        st.markdown(f"""
                            <div class="catapult-card">
                                <h5>Swing Max Player Load</h5>
                                <h3>{tot_swing_pl:.1f}</h3>
                                <p>{season_option}</p>
                            </div>
                        """, unsafe_allow_html=True)

                    # Swing Rotation Bands Chart
                    fig_swing = go.Figure()
                    if 'Swing Max Rotation Band 1 Count' in p_swing.columns:
                        fig_swing.add_trace(go.Bar(x=p_swing['Date'], y=p_swing['Swing Max Rotation Band 1 Count'], name='Rotation Band 1'))
                        fig_swing.add_trace(go.Bar(x=p_swing['Date'], y=p_swing['Swing Max Rotation Band 2 Count'], name='Rotation Band 2'))
                        fig_swing.add_trace(go.Bar(x=p_swing['Date'], y=p_swing['Swing Max Rotation Band 3 Count'], name='Rotation Band 3'))

                    fig_swing.update_layout(
                        barmode='stack',
                        title="Swing Volume by Rotation Velocity Band",
                        xaxis_title="Date",
                        yaxis_title="Swing Count",
                        height=320,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_swing, use_container_width=True)

                    with st.expander("View Raw Swing Log"):
                        st.dataframe(p_swing, use_container_width=True)
                else:
                    st.info("No Swing data recorded for this season.")

    else:
        st.warning("No athlete data loaded. Please check your data source URLs in secrets.")
