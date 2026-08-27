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
        .sub-header-title {
            color: #2F80ED; font-size: 17px; font-weight: 800; letter-spacing: 0.5px;
            text-transform: uppercase; margin-bottom: 12px;
        }

        /* Hero Personal Best Cards */
        .best-card {
            background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
            border: 1px solid #EAEAEA; border-top: 4px solid #FF8200;
            border-radius: 10px; padding: 14px 10px; text-align: center; margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .best-card h4 { margin: 0; color: #6c757d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        .best-card h2 { margin: 6px 0 2px 0; font-size: 22px; font-weight: 800; color: #FF8200; }
        .best-card p { margin: 0; font-size: 11px; color: #2F80ED; font-weight: 700; }

        /* Metric Tile Badges (Readiness Profile) */
        .kpi-tile {
            border-radius: 12px; padding: 16px 8px; text-align: center; color: #FFFFFF;
            display: flex; flex-direction: column; justify-content: center; height: 90px;
        }
        .tile-green { background-color: #28a745; }
        .tile-red { background-color: #dc3545; }
        .tile-orange { background-color: #FF8200; }
        .kpi-tile h1 { margin: 0; font-size: 26px; font-weight: 800; line-height: 1.1; }
        .kpi-tile p { margin: 4px 0 0 0; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }

        /* Detail Callout Box */
        .detail-box {
            background-color: #F8F9FA; border-left: 4px solid #FF8200;
            padding: 10px 14px; border-radius: 4px; margin-top: 12px; font-size: 12px;
            color: #495057; font-weight: 600; line-height: 1.5;
        }

        /* Intake Tab Assessment Cards */
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
        .card-metrics b { color: #1D1D1F; }

        .pct-up { color: #28a745; font-weight: 700; }
        .pct-down { color: #dc3545; font-weight: 700; }
        .pct-flat { color: #6c757d; font-weight: 700; }

        /* Tables & Expanders */
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
            lambda x: re.findall(r"[-+]?\d*\.?\d+", x)[0] if re.findall(r"[-+]?\d*\.?\d+", str(x)) else np.nan
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

        # Standardize athlete name column
        for df in [ash_df, cmj_df, er_df, grip_df, sprint_df, roster_df, swing_df, throw_df]:
            if not df.empty:
                if 'Name' in df.columns and 'Player Name' not in df.columns:
                    df.rename(columns={'Name': 'Player Name'}, inplace=True)
                if 'Player Name' in df.columns:
                    df['Player Name'] = df['Player Name'].astype(str).str.strip()

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

        # Clean numeric columns across datasets
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
                if any(k in col.lower() for k in ['rom', 'asymmetry', 'asym']):
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

    if not ash_df.empty or not cmj_df.empty or not er_df.empty or not grip_df.empty or not sprint_df.empty:
        # --- 5. SEASON SETUP ---
        SPRING_START = pd.to_datetime("2026-01-01")
        SPRING_END = pd.to_datetime("2026-05-31 23:59:59")
        FALL_START = pd.to_datetime("2026-08-24")  

        all_athletes = sorted(list(set(
            list(ash_df['Player Name'].dropna().unique() if 'Player Name' in ash_df.columns else []) +
            list(cmj_df['Player Name'].dropna().unique() if 'Player Name' in cmj_df.columns else []) +
            list(er_df['Player Name'].dropna().unique() if 'Player Name' in er_df.columns else []) +
            list(grip_df['Player Name'].dropna().unique() if 'Player Name' in grip_df.columns else []) +
            list(sprint_df['Player Name'].dropna().unique() if 'Player Name' in sprint_df.columns else [])
        )))

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

        # Slices
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
        ash_asym_col = find_col(ash_df, ['Peak Vertical Force [N] (Asym)(%)', 'Asymmetry'])

        cmj_h_col = find_col(cmj_df, ['Jump Height (Imp-Mom) [cm]', 'Jump Height [cm]', 'Jump Height (cm)'])
        cmj_rsi_col = find_col(cmj_df, ['RSI-modified (Imp-Mom) [m/s]', 'RSI-modified', 'RSI-m'])

        er_l_col = find_col(er_df, ['L Max ROM (°)', 'L Max ROM', 'Left Max ROM', 'L ROM'])
        er_r_col = find_col(er_df, ['R Max ROM (°)', 'R Max ROM', 'Right Max ROM', 'R ROM'])
        er_asym_col = find_col(er_df, ['ROM Asymmetry (%)', 'ROM Asymmetry', 'Asymmetry (%)', 'Asym (%)'])

        grip_l_col = find_col(grip_df, ['L Max Force (N)', 'L Max Force', 'Left Max Force (N)', 'Force (L)', 'L Grip'])
        grip_r_col = find_col(grip_df, ['R Max Force (N)', 'R Max Force', 'Right Max Force (N)', 'Force (R)', 'R Grip'])
        grip_asym_col = find_col(grip_df, ['Force Asymmetry (%)', 'Force Asymmetry', 'Asymmetry (%)', 'Asym (%)'])

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

        def get_best_record(df, col_name, is_min=False):
            if df.empty or not col_name or col_name not in df.columns:
                return None, None
            temp = df.dropna(subset=[col_name, 'Date']).copy()
            temp[col_name] = pd.to_numeric(temp[col_name], errors='coerce')
            temp = temp.dropna(subset=[col_name])
            if temp.empty:
                return None, None
            idx = temp[col_name].idxmin() if is_min else temp[col_name].idxmax()
            best_row = temp.loc[idx]
            return best_row[col_name], best_row['Date'].strftime('%m/%d/%Y')

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

        def render_table_html(df):
            if df.empty:
                return "<p style='color:#6C757D; font-size:13px; margin:8px 0;'>No records found.</p>"
            headers = "".join([f"<th>{col}</th>" for col in df.columns])
            rows = []
            for _, r in df.iterrows():
                tds = "".join([f"<td>{r[col]}</td>" for col in df.columns])
                rows.append(f"<tr>{tds}</tr>")
            return f'<table class="coach-table"><thead><tr>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table>'

        # --- 6. NAVIGATION TABS ---
        tab_intake, tab_profile, tab_catapult = st.tabs(["TESTING", "INDIVIDUAL PROFILE", "CATAPULT PROFILE"])

        # =========================================================================
        # TAB 1: INTAKE ASSESSMENT (ANATOMY HUD + ASSESSMENT CARDS + DROPDOWN LOGS)
        # =========================================================================
        with tab_intake:
            hud_col1, hud_col2 = st.columns([1.15, 1.85], gap="large")

            # --- LEFT: ANATOMY LOCATION MAP ---
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
                                <path d="M 22 104 C 20 106, 18 108, 17 110 M 23 105 C 21 108, 20 110, 19 112 M 24 105 C 23 108, 22 110, 21 112 M 25 104 C 25 107, 24 109, 23 111" fill="none" stroke-width="0.8" />
                                <path d="M 94 40 C 99 43, 101 52, 103 64 C 105 74, 107 82, 109 92 C 111 96, 113 100, 114 104 C 115 106, 113 107, 111 106 C 109 104, 108 98, 106 92 C 103 82, 100 74, 98 64 C 96 54, 94 48, 93 56 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 114 104 C 116 106, 118 108, 119 110 M 113 105 C 115 108, 116 110, 117 112 M 112 105 C 113 108, 114 110, 115 112 M 111 104 C 111 107, 112 109, 113 111" fill="none" stroke-width="0.8" />
                                <path d="M 52 44 L 54 75 L 52 92 L 68 106 L 84 92 L 82 75 L 84 44 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 52 92 C 50 105, 49 122, 53 138 C 55 144, 55 152, 54 162 C 52 175, 52 192, 54 205 L 48 210 L 58 210 L 59 203 C 60 190, 60 175, 60 162 C 60 152, 60 144, 62 138 C 66 122, 66 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                <path d="M 84 92 C 86 105, 87 122, 83 138 C 81 144, 81 152, 82 162 C 84 175, 84 192, 82 205 L 88 210 L 78 210 L 77 203 C 76 190, 76 175, 76 162 C 76 152, 76 144, 74 138 C 70 122, 70 105, 68 106 Z" fill="url(#anatomicalBodyGrad)" />
                                <line x1="68" y1="8" x2="68" y2="211" stroke="#FF8200" stroke-width="1.3" />
                            </g>
                            <!-- 1: ASH Shoulder (Right Shoulder) -->
                            <line x1="88" y1="44" x2="118" y2="44" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
                            <circle cx="88" cy="44" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
                            <rect x="118" y="36" width="16" height="16" rx="4" fill="#FF8200" />
                            <text x="126" y="48" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">1</text>
                            
                            <!-- 2: External Rotation (Left Shoulder) -->
                            <line x1="48" y1="44" x2="18" y2="44" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
                            <circle cx="48" cy="44" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
                            <rect x="2" y="36" width="16" height="16" rx="4" fill="#4895DB" />
                            <text x="10" y="48" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">2</text>
                            
                            <!-- 3: Grip Squeeze (Hand) -->
                            <line x1="24" y1="106" x2="2" y2="106" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
                            <circle cx="24" cy="106" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
                            <rect x="2" y="112" width="16" height="16" rx="4" fill="#FF8200" />
                            <text x="10" y="124" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">3</text>
                            
                            <!-- 4: Countermovement Jump / Lower Body (Knees/Legs) -->
                            <line x1="68" y1="162" x2="118" y2="162" stroke="#4895DB" stroke-width="2" stroke-dasharray="2 2" />
                            <circle cx="68" cy="162" r="4" fill="#4895DB" stroke="#FFFFFF" stroke-width="1.2" />
                            <rect x="118" y="154" width="16" height="16" rx="4" fill="#4895DB" />
                            <text x="126" y="166" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">4</text>

                            <!-- 5: 20m Sprint (Feet/Sprint Base) -->
                            <line x1="48" y1="205" x2="18" y2="205" stroke="#FF8200" stroke-width="2" stroke-dasharray="2 2" />
                            <circle cx="48" cy="205" r="4" fill="#FF8200" stroke="#FFFFFF" stroke-width="1.2" />
                            <rect x="2" y="197" width="16" height="16" rx="4" fill="#FF8200" />
                            <text x="10" y="209" font-size="10" font-weight="900" fill="#FFFFFF" text-anchor="middle">5</text>
                        </svg>
                    </div>
                </div>
                """
                components.html(hud_svg_html, height=530)

            # --- RIGHT: LOCATION ASSESSMENT CARDS ---
            with hud_col2:
                st.markdown(f'<div class="section-header" style="color:#1D1D1F; font-size:13px; letter-spacing:1px;">LOCATION ASSESSMENT ({season_option.upper()})</div>', unsafe_allow_html=True)

                # Card 1: ASH Shoulder
                if not p_ash.empty and ash_l_col and ash_r_col and ash_l_col in p_ash.columns and ash_r_col in p_ash.columns:
                    p_ash_val = p_ash.dropna(subset=[ash_l_col, ash_r_col]).copy()
                    if not p_ash_val.empty:
                        ash_max_l = p_ash_val[ash_l_col].max()
                        ash_max_r = p_ash_val[ash_r_col].max()
                        ash_rec = p_ash_val.iloc[-1]
                        ash_rec_l, ash_rec_r = ash_rec[ash_l_col], ash_rec[ash_r_col]
                        ash_date = ash_rec['Date'].strftime('%Y-%m-%d') if pd.notnull(ash_rec['Date']) else "N/A"
                        chg_l = ((ash_rec_l - ash_max_l) / ash_max_l * 100) if ash_max_l > 0 else 0
                        chg_r = ((ash_rec_r - ash_max_r) / ash_max_r * 100) if ash_max_r > 0 else 0

                        st.markdown(f"""
                            <div class="assessment-card border-orange">
                                <div class="card-top">
                                    <div class="card-title-wrap">
                                        <div class="badge-num badge-orange">1</div>
                                        <span class="card-title">ASH Shoulder (ISO I)</span>
                                    </div>
                                    <span class="card-date">Latest: {ash_date}</span>
                                </div>
                                <div class="card-metrics">
                                    <b>Peak Vertical Force:</b> Max L {int(ash_max_l)}N | R {int(ash_max_r)}N &nbsp;→&nbsp; 
                                    <b>Recent:</b> L {int(ash_rec_l)}N {fmt_pct(chg_l)} | R {int(ash_rec_r)}N {fmt_pct(chg_r)}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No ASH Shoulder data available for this season.")

                # Card 2: External Rotation
                if not p_er.empty and er_l_col and er_r_col and er_l_col in p_er.columns and er_r_col in p_er.columns:
                    p_er_val = p_er.dropna(subset=[er_l_col, er_r_col]).copy()
                    if not p_er_val.empty:
                        er_max_l = p_er_val[er_l_col].max()
                        er_max_r = p_er_val[er_r_col].max()
                        er_rec = p_er_val.iloc[-1]
                        er_rec_l, er_rec_r = er_rec[er_l_col], er_rec[er_r_col]
                        er_date = er_rec['Date'].strftime('%Y-%m-%d') if pd.notnull(er_rec['Date']) else "N/A"
                        chg_l = ((er_rec_l - er_max_l) / er_max_l * 100) if er_max_l > 0 else 0
                        chg_r = ((er_rec_r - er_max_r) / er_max_r * 100) if er_max_r > 0 else 0

                        st.markdown(f"""
                            <div class="assessment-card border-blue">
                                <div class="card-top">
                                    <div class="card-title-wrap">
                                        <div class="badge-num badge-blue">2</div>
                                        <span class="card-title">External Rotation (ER) ROM</span>
                                    </div>
                                    <span class="card-date">Latest: {er_date}</span>
                                </div>
                                <div class="card-metrics">
                                    <b>Max ROM:</b> Max L {int(er_max_l)}° | R {int(er_max_r)}° &nbsp;→&nbsp; 
                                    <b>Recent:</b> L {int(er_rec_l)}° {fmt_pct(chg_l)} | R {int(er_rec_r)}° {fmt_pct(chg_r)}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No External Rotation data available for this season.")

                # Card 3: Grip Squeeze
                if not p_grip.empty and grip_l_col and grip_r_col and grip_l_col in p_grip.columns and grip_r_col in p_grip.columns:
                    p_grip_val = p_grip.dropna(subset=[grip_l_col, grip_r_col]).copy()
                    if not p_grip_val.empty:
                        grip_max_l = p_grip_val[grip_l_col].max()
                        grip_max_r = p_grip_val[grip_r_col].max()
                        grip_rec = p_grip_val.iloc[-1]
                        grip_rec_l, grip_rec_r = grip_rec[grip_l_col], grip_rec[grip_r_col]
                        grip_date = grip_rec['Date'].strftime('%Y-%m-%d') if pd.notnull(grip_rec['Date']) else "N/A"
                        chg_l = ((grip_rec_l - grip_max_l) / grip_max_l * 100) if grip_max_l > 0 else 0
                        chg_r = ((grip_rec_r - grip_max_r) / grip_max_r * 100) if grip_max_r > 0 else 0

                        st.markdown(f"""
                            <div class="assessment-card border-orange">
                                <div class="card-top">
                                    <div class="card-title-wrap">
                                        <div class="badge-num badge-orange">3</div>
                                        <span class="card-title">Grip Squeeze Test</span>
                                    </div>
                                    <span class="card-date">Latest: {grip_date}</span>
                                </div>
                                <div class="card-metrics">
                                    <b>Max Force:</b> Max L {int(grip_max_l)}N | R {int(grip_max_r)}N &nbsp;→&nbsp; 
                                    <b>Recent:</b> L {int(grip_rec_l)}N {fmt_pct(chg_l)} | R {int(grip_rec_r)}N {fmt_pct(chg_r)}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No Grip Squeeze data available for this season.")

                # Card 4: Countermovement Jump
                if not p_cmj.empty and cmj_h_col and cmj_h_col in p_cmj.columns:
                    p_cmj_val = p_cmj.dropna(subset=[cmj_h_col]).copy()
                    if not p_cmj_val.empty:
                        cmj_max_h = p_cmj_val[cmj_h_col].max()
                        cmj_max_rsi = p_cmj_val[cmj_rsi_col].max() if cmj_rsi_col and cmj_rsi_col in p_cmj_val.columns else np.nan
                        cmj_rec = p_cmj_val.iloc[-1]
                        cmj_rec_h = cmj_rec[cmj_h_col]
                        cmj_rec_rsi = cmj_rec[cmj_rsi_col] if cmj_rsi_col and cmj_rsi_col in p_cmj_val.columns else np.nan
                        cmj_date = cmj_rec['Date'].strftime('%Y-%m-%d') if pd.notnull(cmj_rec['Date']) else "N/A"
                        chg_h = ((cmj_rec_h - cmj_max_h) / cmj_max_h * 100) if cmj_max_h > 0 else 0
                        chg_rsi = ((cmj_rec_rsi - cmj_max_rsi) / cmj_max_rsi * 100) if pd.notnull(cmj_max_rsi) and cmj_max_rsi > 0 else np.nan
                        rsi_str = f" | RSI-mod: Max {cmj_max_rsi:.2f} → Recent {cmj_rec_rsi:.2f} {fmt_pct(chg_rsi)}" if pd.notnull(cmj_rec_rsi) else ""

                        st.markdown(f"""
                            <div class="assessment-card border-blue">
                                <div class="card-top">
                                    <div class="card-title-wrap">
                                        <div class="badge-num badge-blue">4</div>
                                        <span class="card-title">Countermovement Jump (CMJ)</span>
                                    </div>
                                    <span class="card-date">Latest: {cmj_date}</span>
                                </div>
                                <div class="card-metrics">
                                    <b>Jump Height:</b> Max {cmj_max_h:.1f}cm &nbsp;→&nbsp; 
                                    <b>Recent:</b> {cmj_rec_h:.1f}cm {fmt_pct(chg_h)}{rsi_str}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No Countermovement Jump data available for this season.")

                # Card 5: 20m Sprint Test
                if not p_sprint.empty and sprint_time_col and sprint_time_col in p_sprint.columns:
                    p_sp_val = p_sprint.dropna(subset=[sprint_time_col]).copy()
                    if not p_sp_val.empty:
                        sp_best = p_sp_val[sprint_time_col].min()
                        sp_rec = p_sp_val.iloc[-1]
                        sp_rec_time = sp_rec[sprint_time_col]
                        sp_date = sp_rec['Date'].strftime('%Y-%m-%d') if pd.notnull(sp_rec['Date']) else "N/A"
                        chg_sp = ((sp_rec_time - sp_best) / sp_best * 100) if sp_best > 0 else 0

                        st.markdown(f"""
                            <div class="assessment-card border-orange">
                                <div class="card-top">
                                    <div class="card-title-wrap">
                                        <div class="badge-num badge-orange">5</div>
                                        <span class="card-title">20m Sprint Test</span>
                                    </div>
                                    <span class="card-date">Latest: {sp_date}</span>
                                </div>
                                <div class="card-metrics">
                                    <b>Best Time:</b> {sp_best:.2f}s &nbsp;→&nbsp; 
                                    <b>Recent:</b> {sp_rec_time:.2f}s {fmt_pct(chg_sp, lower_is_better=True)}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No 20m Sprint records available for this season.")

            # --- BOTTOM: RAW LOGS IN COLLAPSIBLE DROPDOWNS ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<h3 style="font-weight:800; font-size:22px; color:#1D1D1F; margin-bottom:14px;">Assessment Raw Logs for {selected} ({season_option})</h3>', unsafe_allow_html=True)

            with st.expander("20m Sprint Test Log", expanded=False):
                if not raw_sprint.empty and sprint_time_col in raw_sprint.columns:
                    t_sp = raw_sprint.dropna(subset=['Date', sprint_time_col]).sort_values('Date', ascending=False).copy()
                    t_sp['DATE'] = t_sp['Date'].dt.strftime('%Y-%m-%d')
                    t_sp['TEST'] = '20m Sprint'
                    t_sp['TIME (s)'] = t_sp[sprint_time_col].apply(lambda x: f"{x:.2f}s")
                    disp_sp = t_sp[['DATE', 'TEST', 'TIME (s)']]
                    st.markdown(render_table_html(disp_sp), unsafe_allow_html=True)
                else:
                    st.info("No 20m Sprint records available.")

            with st.expander("ASH Shoulder Test Log", expanded=False):
                if not raw_ash.empty and ash_l_col in raw_ash.columns and ash_r_col in raw_ash.columns:
                    t_ash = raw_ash.dropna(subset=['Date', ash_l_col, ash_r_col]).sort_values('Date', ascending=False).copy()
                    t_ash['DATE'] = t_ash['Date'].dt.strftime('%Y-%m-%d')
                    t_ash['TEST'] = 'ISO I'
                    t_ash['L MAX FORCE (N)'] = t_ash[ash_l_col].apply(lambda x: f"{x:.2f}")
                    t_ash['R MAX FORCE (N)'] = t_ash[ash_r_col].apply(lambda x: f"{x:.2f}")
                    if ash_asym_col and ash_asym_col in t_ash.columns:
                        t_ash['MAX IMBALANCE (%)'] = t_ash[ash_asym_col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                    else:
                        t_ash['MAX IMBALANCE (%)'] = ((t_ash[ash_l_col] - t_ash[ash_r_col]).abs() / t_ash[[ash_l_col, ash_r_col]].max(axis=1) * 100).apply(lambda x: f"{x:.2f}")
                    disp_ash = t_ash[['DATE', 'TEST', 'L MAX FORCE (N)', 'R MAX FORCE (N)', 'MAX IMBALANCE (%)']]
                    st.markdown(render_table_html(disp_ash), unsafe_allow_html=True)
                else:
                    st.info("No ASH Shoulder records available.")

            with st.expander("External Rotation (ER) Test Log", expanded=False):
                if not raw_er.empty and er_l_col in raw_er.columns and er_r_col in raw_er.columns:
                    t_er = raw_er.dropna(subset=['Date', er_l_col, er_r_col]).sort_values('Date', ascending=False).copy()
                    t_er['DATE'] = t_er['Date'].dt.strftime('%Y-%m-%d')
                    t_er['TEST'] = 'Max ER ROM'
                    t_er['L MAX ROM (°)'] = t_er[er_l_col].apply(lambda x: f"{int(x)}°" if pd.notnull(x) else "-")
                    t_er['R MAX ROM (°)'] = t_er[er_r_col].apply(lambda x: f"{int(x)}°" if pd.notnull(x) else "-")
                    if er_asym_col and er_asym_col in t_er.columns:
                        t_er['MAX IMBALANCE (%)'] = t_er[er_asym_col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                    else:
                        t_er['MAX IMBALANCE (%)'] = ((t_er[er_l_col] - t_er[er_r_col]).abs() / t_er[[er_l_col, er_r_col]].max(axis=1) * 100).apply(lambda x: f"{x:.2f}")
                    disp_er = t_er[['DATE', 'TEST', 'L MAX ROM (°)', 'R MAX ROM (°)', 'MAX IMBALANCE (%)']]
                    st.markdown(render_table_html(disp_er), unsafe_allow_html=True)
                else:
                    st.info("No External Rotation records available.")

            with st.expander("Grip Squeeze Test Log", expanded=False):
                if not raw_grip.empty and grip_l_col in raw_grip.columns and grip_r_col in raw_grip.columns:
                    t_grip = raw_grip.dropna(subset=['Date', grip_l_col, grip_r_col]).sort_values('Date', ascending=False).copy()
                    t_grip['DATE'] = t_grip['Date'].dt.strftime('%Y-%m-%d')
                    t_grip['TEST'] = 'Grip Squeeze'
                    t_grip['L MAX FORCE (N)'] = t_grip[grip_l_col].apply(lambda x: f"{x:.2f}")
                    t_grip['R MAX FORCE (N)'] = t_grip[grip_r_col].apply(lambda x: f"{x:.2f}")
                    if grip_asym_col and grip_asym_col in t_grip.columns:
                        t_grip['MAX IMBALANCE (%)'] = t_grip[grip_asym_col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                    else:
                        t_grip['MAX IMBALANCE (%)'] = ((t_grip[grip_l_col] - t_grip[grip_r_col]).abs() / t_grip[[grip_l_col, grip_r_col]].max(axis=1) * 100).apply(lambda x: f"{x:.2f}")
                    disp_grip = t_grip[['DATE', 'TEST', 'L MAX FORCE (N)', 'R MAX FORCE (N)', 'MAX IMBALANCE (%)']]
                    st.markdown(render_table_html(disp_grip), unsafe_allow_html=True)
                else:
                    st.info("No Grip Squeeze records available.")

            with st.expander("Countermovement Jump (CMJ) Test Log", expanded=False):
                if not raw_cmj.empty and cmj_h_col in raw_cmj.columns:
                    t_cmj = raw_cmj.dropna(subset=['Date', cmj_h_col]).sort_values('Date', ascending=False).copy()
                    t_cmj['DATE'] = t_cmj['Date'].dt.strftime('%Y-%m-%d')
                    t_cmj['TEST'] = 'CMJ'
                    t_cmj['JUMP HEIGHT (cm)'] = t_cmj[cmj_h_col].apply(lambda x: f"{x:.2f}")
                    t_cmj['RSI-MODIFIED'] = t_cmj[cmj_rsi_col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-") if cmj_rsi_col and cmj_rsi_col in t_cmj.columns else "-"
                    disp_cmj = t_cmj[['DATE', 'TEST', 'JUMP HEIGHT (cm)', 'RSI-MODIFIED']]
                    st.markdown(render_table_html(disp_cmj), unsafe_allow_html=True)
                else:
                    st.info("No Countermovement Jump records available.")

        # =========================================================================
        # TAB 2: TESTING PROFILE (INDIVIDUAL TESTS WITH PERSONAL BESTS & CHARTS)
        # =========================================================================
        with tab_profile:
            st.subheader("ALL-TIME PERSONAL BESTS")
            b_sprint, b_sprint_date = get_best_record(raw_sprint, sprint_time_col, is_min=True)
            b_cmj_h, b_cmj_h_date = get_best_record(raw_cmj, cmj_h_col)
            b_rsi, b_rsi_date = get_best_record(raw_cmj, cmj_rsi_col)
            b_ash_l, b_ash_l_date = get_best_record(raw_ash, ash_l_col)
            b_ash_r, b_ash_r_date = get_best_record(raw_ash, ash_r_col)
            b_er_l, b_er_l_date = get_best_record(raw_er, er_l_col)
            b_er_r, b_er_r_date = get_best_record(raw_er, er_r_col)
            b_grip_l, b_grip_l_date = get_best_record(raw_grip, grip_l_col)
            b_grip_r, b_grip_r_date = get_best_record(raw_grip, grip_r_col)

            # Row 1: Sprint, CMJ & RSI Best Cards
            b0, b1, b2 = st.columns(3)
            with b0:
                val = f"{b_sprint:.2f} s" if b_sprint is not None else "N/A"
                d_str = f"Set on {b_sprint_date}" if b_sprint_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best 20m Sprint</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b1:
                val = f"{b_cmj_h:.1f} cm" if b_cmj_h is not None else "N/A"
                d_str = f"Set on {b_cmj_h_date}" if b_cmj_h_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best Jump Height</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b2:
                val = f"{b_rsi:.2f}" if b_rsi is not None else "N/A"
                d_str = f"Set on {b_rsi_date}" if b_rsi_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best RSI-modified</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)

            # Row 2: ASH & ER Best Cards
            b3, b4, b5, b6 = st.columns(4)
            with b3:
                val = f"{int(b_ash_l)} N" if b_ash_l is not None else "N/A"
                d_str = f"Set on {b_ash_l_date}" if b_ash_l_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ASH Force (Left)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b4:
                val = f"{int(b_ash_r)} N" if b_ash_r is not None else "N/A"
                d_str = f"Set on {b_ash_r_date}" if b_ash_r_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ASH Force (Right)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b5:
                val = f"{int(b_er_l)}°" if b_er_l is not None else "N/A"
                d_str = f"Set on {b_er_l_date}" if b_er_l_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ER ROM (Left)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b6:
                val = f"{int(b_er_r)}°" if b_er_r is not None else "N/A"
                d_str = f"Set on {b_er_r_date}" if b_er_r_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ER ROM (Right)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)

            # Row 3: Grip Squeeze Cards
            b7, b8, _, _ = st.columns(4)
            with b7:
                val = f"{int(b_grip_l)} N" if b_grip_l is not None else "N/A"
                d_str = f"Set on {b_grip_l_date}" if b_grip_l_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best Grip (Left)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b8:
                val = f"{int(b_grip_r)} N" if b_grip_r is not None else "N/A"
                d_str = f"Set on {b_grip_r_date}" if b_grip_r_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best Grip (Right)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">WEEKLY READINESS PROFILE</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            # --- SECTION 0: 20M SPRINT SPEED ---
            st.markdown('<div class="sub-header-title">20M SPRINT SPEED</div>', unsafe_allow_html=True)
            p_sprint_ready = p_sprint.dropna(subset=['Date']).sort_values('Date').copy() if not p_sprint.empty else pd.DataFrame()

            if not p_sprint_ready.empty and sprint_time_col and sprint_time_col in p_sprint_ready.columns:
                p_sprint_ready[sprint_time_col] = pd.to_numeric(p_sprint_ready[sprint_time_col], errors='coerce')
                p_sprint_ready = p_sprint_ready.dropna(subset=[sprint_time_col])

                if not p_sprint_ready.empty:
                    sp_plot_df = p_sprint_ready.groupby('Date', as_index=False)[sprint_time_col].mean()
                    latest_sp = sp_plot_df.iloc[-1][sprint_time_col]
                    base_sp = sp_plot_df[sprint_time_col].mean()
                    chg_sp = ((latest_sp - base_sp) / base_sp * 100) if base_sp > 0 else 0

                    sp_tile_cls = "tile-green" if chg_sp <= 2.0 else "tile-red"

                    sp_left, sp_right = st.columns([1.1, 2])
                    with sp_left:
                        st.markdown(f'<div class="kpi-tile {sp_tile_cls}"><h1>{latest_sp:.2f} s</h1><p>LATEST 20M TIME</p></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><div><b>% Change from Base:</b> {chg_sp:+.1f}%</div><div><b>Base Value:</b> {base_sp:.2f} s</div></div>', unsafe_allow_html=True)

                    with sp_right:
                        fig_sp = go.Figure()
                        fig_sp.add_trace(go.Scatter(x=sp_plot_df['Date'], y=sp_plot_df[sprint_time_col], name="20m Sprint (s)", mode="lines+markers", line=dict(color="#FF8200", width=3.5), marker=dict(size=9, color="#FF8200")))
                        s_min, s_max = sp_plot_df[sprint_time_col].min(), sp_plot_df[sprint_time_col].max()
                        fig_sp.update_layout(
                            template="plotly_white", height=230, margin=dict(l=10, r=10, t=25, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
                            xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"),
                            yaxis=dict(title="Seconds", showgrid=True, gridcolor="#F0F2F6", range=[s_min * 0.95, s_max * 1.05] if s_min != s_max else [s_min - 0.2, s_max + 0.2])
                        )
                        st.plotly_chart(fig_sp, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No 20m Sprint records available for this selection.")
            else:
                st.info("No 20m Sprint records available for this season.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECTION 1: COUNTERMOVEMENT JUMP ---
            st.markdown('<div class="sub-header-title">COUNTERMOVEMENT JUMP</div>', unsafe_allow_html=True)
            p_cmj_ready = p_cmj.dropna(subset=['Date']).sort_values('Date').copy() if not p_cmj.empty else pd.DataFrame()

            if not p_cmj_ready.empty and cmj_h_col and cmj_rsi_col and cmj_h_col in p_cmj_ready.columns and cmj_rsi_col in p_cmj_ready.columns:
                p_cmj_ready[cmj_h_col] = pd.to_numeric(p_cmj_ready[cmj_h_col], errors='coerce')
                p_cmj_ready[cmj_rsi_col] = pd.to_numeric(p_cmj_ready[cmj_rsi_col], errors='coerce')
                p_cmj_ready = p_cmj_ready.dropna(subset=[cmj_h_col, cmj_rsi_col])
                
                if not p_cmj_ready.empty:
                    cmj_plot_df = p_cmj_ready.groupby('Date', as_index=False)[[cmj_h_col, cmj_rsi_col]].mean()
                    lat_cmj = cmj_plot_df.iloc[-1]
                    latest_h = lat_cmj[cmj_h_col]
                    latest_rsi = lat_cmj[cmj_rsi_col]
                    base_h = cmj_plot_df[cmj_h_col].mean()
                    base_rsi = cmj_plot_df[cmj_rsi_col].mean()

                    chg_h = ((latest_h - base_h) / base_h * 100) if base_h > 0 else 0
                    chg_rsi = ((latest_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0

                    h_tile_cls = "tile-green" if chg_h >= -5 else "tile-red"
                    rsi_tile_cls = "tile-green" if chg_rsi >= -5 else "tile-red"

                    c_left, c_right = st.columns([1.1, 2])
                    with c_left:
                        cb1, cb2 = st.columns(2)
                        with cb1:
                            st.markdown(f'<div class="kpi-tile {h_tile_cls}"><h1>{latest_h:.1f}</h1><p>CMJ HEIGHT</p></div>', unsafe_allow_html=True)
                        with cb2:
                            st.markdown(f'<div class="kpi-tile {rsi_tile_cls}"><h1>{latest_rsi:.2f}</h1><p>RSI MOD</p></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><div><b>% Change from Base:</b> CMJ: {chg_h:+.1f}% | RSI: {chg_rsi:+.1f}%</div><div><b>Base Values:</b> CMJ: {base_h:.1f} | RSI: {base_rsi:.2f}</div></div>', unsafe_allow_html=True)

                    with c_right:
                        fig_cmj = go.Figure()
                        fig_cmj.add_trace(go.Scatter(x=cmj_plot_df['Date'], y=cmj_plot_df[cmj_h_col], name="Jump Height", mode="lines+markers", line=dict(color="#FF8200", width=3.5), marker=dict(size=9, color="#FF8200")))
                        fig_cmj.add_trace(go.Scatter(x=cmj_plot_df['Date'], y=cmj_plot_df[cmj_rsi_col], name="RSI Modified", mode="lines+markers", yaxis="y2", line=dict(color="#2F80ED", width=2.5, dash="dot"), marker=dict(size=8, color="#2F80ED")))
                        h_min, h_max = cmj_plot_df[cmj_h_col].min(), cmj_plot_df[cmj_h_col].max()
                        r_min, r_max = cmj_plot_df[cmj_rsi_col].min(), cmj_plot_df[cmj_rsi_col].max()
                        fig_cmj.update_layout(
                            template="plotly_white", height=230, margin=dict(l=10, r=10, t=25, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
                            xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"),
                            yaxis=dict(title=None, showgrid=True, gridcolor="#F0F2F6", range=[h_min - 2, h_max + 2] if h_min == h_max else [h_min * 0.95, h_max * 1.05]),
                            yaxis2=dict(title=None, showgrid=False, range=[r_min - 0.05, r_max + 0.05] if r_min == r_max else [r_min * 0.9, r_max * 1.1], overlaying="y", side="right")
                        )
                        st.plotly_chart(fig_cmj, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No Countermovement Jump records available for this selection.")
            else:
                st.info("No Countermovement Jump records available for this season.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECTION 2: ASH SHOULDER: ISO I ---
            st.markdown('<div class="sub-header-title">ASH SHOULDER: ISO I</div>', unsafe_allow_html=True)
            p_ash_ready = p_ash.dropna(subset=['Date']).sort_values('Date').copy() if not p_ash.empty else pd.DataFrame()

            if not p_ash_ready.empty and ash_l_col and ash_r_col and ash_l_col in p_ash_ready.columns and ash_r_col in p_ash_ready.columns:
                p_ash_ready[ash_l_col] = pd.to_numeric(p_ash_ready[ash_l_col], errors='coerce').fillna(0)
                p_ash_ready[ash_r_col] = pd.to_numeric(p_ash_ready[ash_r_col], errors='coerce').fillna(0)
                p_ash_ready = p_ash_ready[(p_ash_ready[ash_l_col] > 0) | (p_ash_ready[ash_r_col] > 0)]

                if not p_ash_ready.empty:
                    lat_ash_r = p_ash_ready.iloc[-1]
                    latest_l, latest_r = lat_ash_r[ash_l_col], lat_ash_r[ash_r_col]
                    base_l = p_ash_ready[ash_l_col].replace(0, np.nan).mean() or 0
                    base_r = p_ash_ready[ash_r_col].replace(0, np.nan).mean() or 0
                    chg_l = ((latest_l - base_l) / base_l * 100) if base_l > 0 else 0
                    chg_r = ((latest_r - base_r) / base_r * 100) if base_r > 0 else 0

                    asym_val = float(lat_ash_r[ash_asym_col]) if ash_asym_col and ash_asym_col in lat_ash_r and pd.notnull(lat_ash_r[ash_asym_col]) else ((abs(latest_l - latest_r)/max(latest_l, latest_r)*100) if max(latest_l, latest_r) > 0 else 0.0)
                    ash_tile_cls = "tile-red" if asym_val > 10 else "tile-green"

                    a_left, a_right = st.columns([1.1, 2])
                    with a_left:
                        ab1, ab2 = st.columns(2)
                        with ab1:
                            st.markdown(f'<div class="kpi-tile {ash_tile_cls}"><h1>{int(latest_l)} N</h1><p>LEFT</p></div>', unsafe_allow_html=True)
                        with ab2:
                            st.markdown(f'<div class="kpi-tile {ash_tile_cls}"><h1>{int(latest_r)} N</h1><p>RIGHT</p></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><div><b>Asymmetry:</b> {asym_val:+.1f}%</div><div><b>% Change from Base:</b> L: {chg_l:+.1f}% | R: {chg_r:+.1f}%</div><div><b>Base Force:</b> L: {int(base_l)} N | R: {int(base_r)} N</div></div>', unsafe_allow_html=True)

                    with a_right:
                        fig_ash_p = go.Figure()
                        fig_ash_p.add_trace(go.Scatter(x=p_ash_ready['Date'], y=p_ash_ready[ash_l_col], name="Left Peak Force", mode="lines+markers", line=dict(color="#2F80ED", width=3), marker=dict(size=6, color="#2F80ED")))
                        fig_ash_p.add_trace(go.Scatter(x=p_ash_ready['Date'], y=p_ash_ready[ash_r_col], name="Right Peak Force", mode="lines+markers", line=dict(color="#FF8200", width=3, dash="dash"), marker=dict(size=6, color="#FF8200")))
                        fig_ash_p.update_layout(template="plotly_white", height=230, margin=dict(l=10, r=10, t=25, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"), yaxis=dict(showgrid=True, gridcolor="#F0F2F6"))
                        st.plotly_chart(fig_ash_p, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No ASH Shoulder records available for this selection.")
            else:
                st.info("No ASH Shoulder records available for this season.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECTION 3: EXTERNAL ROTATION (ER) TEST ---
            st.markdown('<div class="sub-header-title">EXTERNAL ROTATION (ER) TEST</div>', unsafe_allow_html=True)
            p_er_ready = p_er.dropna(subset=['Date']).sort_values('Date').copy() if not p_er.empty else pd.DataFrame()

            if not p_er_ready.empty and er_l_col and er_r_col and er_l_col in p_er_ready.columns and er_r_col in p_er_ready.columns:
                p_er_ready[er_l_col] = pd.to_numeric(p_er_ready[er_l_col], errors='coerce').fillna(0)
                p_er_ready[er_r_col] = pd.to_numeric(p_er_ready[er_r_col], errors='coerce').fillna(0)
                p_er_ready = p_er_ready[(p_er_ready[er_l_col] > 0) | (p_er_ready[er_r_col] > 0)]

                if not p_er_ready.empty:
                    lat_er = p_er_ready.iloc[-1]
                    latest_er_l, latest_er_r = lat_er[er_l_col], lat_er[er_r_col]
                    base_er_l = p_er_ready[er_l_col].replace(0, np.nan).mean() or 0
                    base_er_r = p_er_ready[er_r_col].replace(0, np.nan).mean() or 0
                    chg_er_l = ((latest_er_l - base_er_l) / base_er_l * 100) if base_er_l > 0 else 0
                    chg_er_r = ((latest_er_r - base_er_r) / base_er_r * 100) if base_er_r > 0 else 0

                    er_asym_val = float(lat_er[er_asym_col]) if er_asym_col and er_asym_col in lat_er and pd.notnull(lat_er[er_asym_col]) else ((abs(latest_er_l - latest_er_r)/max(latest_er_l, latest_er_r)*100) if max(latest_er_l, latest_er_r) > 0 else 0.0)
                    er_cls = "tile-red" if er_asym_val > 10 else "tile-green"

                    er_left, er_right = st.columns([1.1, 2])
                    with er_left:
                        erb1, erb2 = st.columns(2)
                        with erb1:
                            st.markdown(f'<div class="kpi-tile {er_cls}"><h1>{int(latest_er_l)}°</h1><p>LEFT MAX ROM</p></div>', unsafe_allow_html=True)
                        with erb2:
                            st.markdown(f'<div class="kpi-tile {er_cls}"><h1>{int(latest_er_r)}°</h1><p>RIGHT MAX ROM</p></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><div><b>ROM Asymmetry:</b> {er_asym_val:+.1f}%</div><div><b>% Change from Base:</b> L: {chg_er_l:+.1f}% | R: {chg_er_r:+.1f}%</div><div><b>Base ROM:</b> L: {int(base_er_l)}° | R: {int(base_er_r)}°</div></div>', unsafe_allow_html=True)

                    with er_right:
                        fig_er_p = go.Figure()
                        fig_er_p.add_trace(go.Scatter(x=p_er_ready['Date'], y=p_er_ready[er_l_col], name="Left Max ROM (°)", mode="lines+markers", line=dict(color="#2F80ED", width=3), marker=dict(size=6, color="#2F80ED")))
                        fig_er_p.add_trace(go.Scatter(x=p_er_ready['Date'], y=p_er_ready[er_r_col], name="Right Max ROM (°)", mode="lines+markers", line=dict(color="#FF8200", width=3, dash="dash"), marker=dict(size=6, color="#FF8200")))
                        fig_er_p.update_layout(template="plotly_white", height=230, margin=dict(l=10, r=10, t=25, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"), yaxis=dict(showgrid=True, gridcolor="#F0F2F6", title="Degrees (°)"))
                        st.plotly_chart(fig_er_p, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No External Rotation records available for this selection.")
            else:
                st.info("No External Rotation records found.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECTION 4: GRIP SQUEEZE TEST ---
            st.markdown('<div class="sub-header-title">GRIP SQUEEZE TEST</div>', unsafe_allow_html=True)
            p_grip_ready = p_grip.dropna(subset=["Date"]).sort_values("Date").copy() if not p_grip.empty else pd.DataFrame()

            if not p_grip_ready.empty and grip_l_col and grip_r_col and grip_l_col in p_grip_ready.columns and grip_r_col in p_grip_ready.columns:
                p_grip_ready[grip_l_col] = pd.to_numeric(p_grip_ready[grip_l_col], errors="coerce").fillna(0)
                p_grip_ready[grip_r_col] = pd.to_numeric(p_grip_ready[grip_r_col], errors="coerce").fillna(0)
                p_grip_ready = p_grip_ready[(p_grip_ready[grip_l_col] > 0) | (p_grip_ready[grip_r_col] > 0)]

                if not p_grip_ready.empty:
                    lat_grip = p_grip_ready.iloc[-1]
                    latest_grip_l, latest_grip_r = lat_grip[grip_l_col], lat_grip[grip_r_col]
                    base_grip_l = p_grip_ready[grip_l_col].replace(0, np.nan).mean() or 0
                    base_grip_r = p_grip_ready[grip_r_col].replace(0, np.nan).mean() or 0

                    chg_grip_l = ((latest_grip_l - base_grip_l) / base_grip_l * 100) if base_grip_l > 0 else 0
                    chg_grip_r = ((latest_grip_r - base_grip_r) / base_grip_r * 100) if base_grip_r > 0 else 0

                    grip_asym_val = float(lat_grip[grip_asym_col]) if grip_asym_col and grip_asym_col in lat_grip and pd.notnull(lat_grip[grip_asym_col]) else ((abs(latest_grip_l - latest_grip_r) / max(latest_grip_l, latest_grip_r) * 100) if max(latest_grip_l, latest_grip_r) > 0 else 0.0)

                    UPPER_THRESH, LOWER_THRESH = 499.47, 365.91
                    def get_grip_color(val):
                        return "tile-green" if val >= UPPER_THRESH else ("tile-orange" if val >= LOWER_THRESH else "tile-red")

                    l_grip_cls = get_grip_color(latest_grip_l)
                    r_grip_cls = get_grip_color(latest_grip_r)

                    g_left, g_right = st.columns([1.1, 2])
                    with g_left:
                        gb1, gb2 = st.columns(2)
                        with gb1:
                            st.markdown(f'<div class="kpi-tile {l_grip_cls}"><h1>{int(latest_grip_l)} N</h1><p>LEFT FORCE</p></div>', unsafe_allow_html=True)
                        with gb2:
                            st.markdown(f'<div class="kpi-tile {r_grip_cls}"><h1>{int(latest_grip_r)} N</h1><p>RIGHT FORCE</p></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><div><b>Force Asymmetry:</b> {grip_asym_val:+.1f}%</div><div><b>% Change from Base:</b> L: {chg_grip_l:+.1f}% | R: {chg_grip_r:+.1f}%</div><div><b>Base Force:</b> L: {int(base_grip_l)} N | R: {int(base_grip_r)} N</div></div>', unsafe_allow_html=True)

                    with g_right:
                        fig_grip_p = go.Figure()
                        fig_grip_p.add_trace(go.Scatter(x=p_grip_ready["Date"], y=p_grip_ready[grip_l_col], name="Left Max Force (N)", mode="lines+markers", line=dict(color="#2F80ED", width=3), marker=dict(size=6, color="#2F80ED")))
                        fig_grip_p.add_trace(go.Scatter(x=p_grip_ready["Date"], y=p_grip_ready[grip_r_col], name="Right Max Force (N)", mode="lines+markers", line=dict(color="#FF8200", width=3, dash="dash"), marker=dict(size=6, color="#FF8200")))
                        fig_grip_p.update_layout(template="plotly_white", height=230, margin=dict(l=10, r=10, t=25, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"), yaxis=dict(showgrid=True, gridcolor="#F0F2F6", title="Force (N)", range=[184 * 0.9, 612 * 1.05]))
                        st.plotly_chart(fig_grip_p, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("No Grip Squeeze records available for this selection.")
            else:
                st.info("No Grip Squeeze records found.")

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
                                <div style="background-color:{color}; padding:18px; border-radius:12px; color:white; text-align:center;">
                                    <h1 style="margin:0; font-size:28px;">{status} SESSION</h1>
                                    <p style="margin:0; font-size:15px; opacity:0.95;">Latest Session: {latest_s['Date'].strftime('%m/%d')} — {note}</p>
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
                            fig_s = px.bar(p_s_filt, x='Date', y='Total', color='Session', color_discrete_map={'Game': '#2F80ED', 'Practice': '#FF8200'}, text='Total', template="plotly_white")
                            fig_s.update_traces(texttemplate='%{text:.0f}', textposition='outside', cliponaxis=False)
                            fig_s.update_layout(height=320, yaxis_visible=False, xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""), xaxis=dict(tickformat="%m/%d"))
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
                                <div style="background-color:{color}; padding:18px; border-radius:12px; color:white; text-align:center;">
                                    <h1 style="margin:0; font-size:28px;">{status} SESSION</h1>
                                    <p style="margin:0; font-size:15px; opacity:0.95;">Latest Session: {latest_t['Date'].strftime('%m/%d')} — {note}</p>
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
                            fig_t = px.bar(p_t_filt, x='Date', y='Throws', color='Session', color_discrete_map={'Game': '#2F80ED', 'Practice': '#FF8200'}, text='Throws', template="plotly_white")
                            fig_t.update_traces(texttemplate='%{text}', textposition='outside', cliponaxis=False)
                            fig_t.update_layout(height=320, yaxis_visible=False, xaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""), xaxis=dict(tickformat="%m/%d"))
                            st.plotly_chart(fig_t, use_container_width=True)

                            st.subheader("Session Details")
                            hist_t = p_t_filt.sort_values('Date', ascending=False).copy()
                            hist_t['Date_Str'] = hist_t['Date'].dt.strftime('%m/%d')
                            rows_t = [f"<tr><td>{r['Date_Str']}</td><td>{r['Session Type']}</td><td>{int(r['Throws'])}</td><td>{int(r['Intent'])}</td></tr>" for _, r in hist_t.iterrows()]
                            st.markdown(f'<table class="coach-table"><thead><tr><th>Date</th><th>Session Type</th><th>Total</th><th>High Intent</th></tr></thead><tbody>{"".join(rows_t)}</tbody></table>', unsafe_allow_html=True)
                        else:
                            st.info(f"No throwing records found for {selected} in this range.")
