import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import re
import plotly.graph_objects as go
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
        .stApp { 
            background-color: #FFFFFF; 
            color: #1D1D1F; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
        }
        
        /* Athlete Banner */
        .athlete-banner {
            background-color: #F8F9FA; 
            padding: 16px 20px; 
            border-radius: 12px;
            border-left: 6px solid #FF8200; 
            margin-bottom: 16px;
            display: flex; 
            align-items: center; 
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .athlete-info { display: flex; align-items: center; }
        .player-photo { 
            border-radius: 50%; 
            width: 80px; 
            height: 80px; 
            object-fit: cover; 
            border: 2px solid #2F80ED; 
            margin-right: 18px; 
        }
        .athlete-name { margin: 0; font-size: 24px; font-weight: 800; color: #1D1D1F; }
        .athlete-sub { margin: 2px 0 0 0; color: #2F80ED; font-weight: 700; font-size: 13.5px; }
        
        /* Section Typography & Dividers */
        .section-header {
            color: #2F80ED; 
            font-size: 18px; 
            font-weight: 800; 
            letter-spacing: 0.5px;
            text-transform: uppercase; 
            margin-top: 6px; 
            margin-bottom: 2px;
        }
        .sub-header-title {
            color: #1D1D1F;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .section-divider { 
            height: 3px; 
            background-color: #FF8200; 
            margin-top: 4px;
            margin-bottom: 16px; 
            border-radius: 2px; 
        }
        
        /* KPI / Metric Cards */
        .catapult-card {
            background: #F8F9FA; 
            border: 1px solid #EAEAEA; 
            border-top: 4px solid #FF8200;
            border-radius: 8px; 
            padding: 10px 12px; 
            text-align: center; 
            margin-bottom: 12px;
        }
        .catapult-card h5 { 
            margin: 0; 
            color: #6C757D; 
            font-size: 11px; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
        }
        .catapult-card h3 { 
            margin: 4px 0 2px 0; 
            font-size: 22px; 
            font-weight: 800; 
            color: #1D1D1F; 
        }
        .catapult-card p { 
            margin: 0; 
            font-size: 11px; 
            color: #2F80ED; 
            font-weight: 700; 
        }

        /* Assessment Cards */
        .assessment-card {
            background: #FFFFFF; 
            border: 1px solid #EAEAEA; 
            border-radius: 8px;
            padding: 12px 16px; 
            margin-bottom: 12px; 
            position: relative;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .border-orange { border-left: 5px solid #FF8200; }
        .border-blue { border-left: 5px solid #4895DB; }

        .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .card-title-wrap { display: flex; align-items: center; gap: 8px; }
        .badge-num {
            width: 22px; 
            height: 22px; 
            border-radius: 5px; 
            color: #FFFFFF;
            font-weight: 800; 
            font-size: 12px; 
            display: inline-flex;
            align-items: center; 
            justify-content: center;
        }
        .badge-orange { background-color: #FF8200; }
        .badge-blue { background-color: #4895DB; }

        .card-title { font-weight: 800; font-size: 13px; color: #1D1D1F; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }
        .card-date { font-size: 11.5px; color: #6C757D; font-weight: 600; }
        .card-metrics { font-size: 13px; color: #333333; line-height: 1.4; }

        /* Custom Styled Coach Tables with Scroll Fix */
        .table-container {
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            overflow-x: auto;
            overflow-y: auto;
            max-height: 450px;
            margin-top: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }
        .coach-table { 
            width: 100%; 
            border-collapse: collapse; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            text-align: center; 
        }
        .coach-table th { 
            position: sticky;
            top: 0;
            background-color: #F8FAFC; 
            padding: 10px 12px; 
            border-bottom: 1px solid #E2E8F0; 
            color: #475569; 
            font-weight: 700; 
            font-size: 11px; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
            z-index: 10;
        }
        .coach-table td { 
            padding: 8px 12px; 
            border-bottom: 1px solid #F1F5F9; 
            font-size: 12.5px; 
            color: #1E293B; 
            white-space: nowrap;
        }
        .coach-table tr:last-child td { border-bottom: none; }
        .coach-table tr:nth-child(even) { background-color: #FAFAFA; }
        .coach-table tr:hover { background-color: #F1F5F9; transition: background-color 0.15s ease-in-out; }

        /* Metric Legend / Description Cards */
        .legend-card {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 12px;
            height: 100%;
        }
        .legend-title {
            font-size: 12px;
            font-weight: 800;
            color: #0F172A;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .legend-desc {
            font-size: 12px;
            color: #475569;
            line-height: 1.45;
        }
        
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

        for df in [ash_df, cmj_df, er_df, grip_df, sprint_df, roster_df, swing_df, throw_df]:
            if not df.empty:
                if 'Name' in df.columns and 'Player Name' not in df.columns:
                    df.rename(columns={'Name': 'Player Name'}, inplace=True)
                if 'Player Name' in df.columns:
                    df['Player Name'] = df['Player Name'].astype(str).str.strip()

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

            agg_dict = {c: 'sum' for c in swing_cols if c in swing_df.columns}
            if 'Session Type' in swing_df.columns:
                agg_dict['Session Type'] = lambda x: ', '.join(x.dropna().unique())
            if 'Activity' in swing_df.columns:
                agg_dict['Activity'] = lambda x: ', '.join(x.dropna().unique())
            
            swing_df = swing_df.groupby(['Player Name', 'Date'], as_index=False).agg(agg_dict)

        if not throw_df.empty:
            throw_cols = [
                'Total Throw Count', 'Total Throw Player Load',
                'Total Throw Count - Player Load 1', 'Total Throw Count - Player Load 2', 'Total Throw Count - Player Load 3',
                'Total Throw Count - Rotation Band 1', 'Total Throw Count - Rotation Band 2', 'Total Throw Count - Rotation Band 3'
            ]
            for col in throw_cols:
                if col in throw_df.columns:
                    throw_df[col] = clean_num_series(throw_df[col])

            agg_dict_t = {c: 'sum' for c in throw_cols if c in throw_df.columns}
            if 'Session Type' in throw_df.columns:
                agg_dict_t['Session Type'] = lambda x: ', '.join(x.dropna().unique())
            if 'Activity' in throw_df.columns:
                agg_dict_t['Activity'] = lambda x: ', '.join(x.dropna().unique())

            throw_df = throw_df.groupby(['Player Name', 'Date'], as_index=False).agg(agg_dict_t)

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

        for df, col_keywords in [
            (ash_df, ['force', 'asym', 'rfd']),
            (cmj_df, ['height', 'power', 'rsi', 'velocity', 'force', 'impulse', 'rfd', 'stiffness', 'bw']),
            (er_df, ['rom', 'asymmetry', 'asym', 'max']),
            (grip_df, ['force', 'asymmetry', 'asym']),
            (sprint_df, ['time', '20m', 'sec', 'speed'])
        ]:
            if not df.empty:
                for col in df.columns:
                    if any(k in col.lower() for k in col_keywords):
                        df[col] = clean_num_series(df[col])

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

    # --- 5. SEASON & CALENDAR DATE RANGE SETUP ---
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
        f_col1, f_col2, f_col3 = st.columns([1.2, 1, 1.3])
        with f_col1:
            selected = st.selectbox("Select Athlete", all_athletes)
        with f_col2:
            season_option = st.selectbox("Season Preset", ["Custom Range", "Fall 2026 (Current)", "Spring 2026", "All Time"], index=1)

        all_dates = []
        for df in [ash_df, cmj_df, er_df, grip_df, sprint_df, swing_df, throw_df]:
            if not df.empty and 'Date' in df.columns:
                all_dates.extend(df['Date'].dropna().tolist())

        min_date = min(all_dates).date() if all_dates else date(2026, 1, 1)
        max_date = max(all_dates).date() if all_dates else date(2026, 12, 31)

        if season_option == "Spring 2026":
            default_start, default_end = date(2026, 1, 1), date(2026, 5, 31)
        elif season_option == "Fall 2026 (Current)":
            default_start, default_end = date(2026, 8, 21), max_date
        elif season_option == "All Time":
            default_start, default_end = min_date, max_date
        else:
            default_start, default_end = min_date, max_date

        with f_col3:
            date_range = st.date_input(
                "Select Date Range",
                value=(default_start, default_end),
                min_value=min_date,
                max_value=max_date
            )

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        else:
            start_dt, end_dt = pd.to_datetime(default_start), pd.to_datetime(default_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        def filter_season(df):
            if df.empty or 'Date' not in df.columns:
                return df
            return df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt)]

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

        date_str_display = f"{start_dt.strftime('%b %d, %Y')} – {end_dt.strftime('%b %d, %Y')}"
        st.markdown(f"""
            <div class="athlete-banner">
                <div class="athlete-info">
                    <img src="{img_url}" class="player-photo">
                    <div>
                        <h1 class="athlete-name">{selected}</h1>
                        <p class="athlete-sub">Softball Performance | {date_str_display}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        def render_custom_table(df):
            if df.empty:
                return "<p style='font-size:12px; color:#6C757D; text-align:center;'>No records found.</p>"
            html = '<div class="table-container"><table class="coach-table"><thead><tr>'
            for col in df.columns:
                html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            for _, row in df.iterrows():
                html += '<tr>'
                for val in row:
                    html += f'<td>{val}</td>'
                html += '</tr>'
            html += '</tbody></table></div>'
            return html

        # --- Helper for Assessment Cards Rendering ---
        def render_assessment_cards():
            # 1. ASH
            if not p_ash.empty and ash_l_col and ash_r_col:
                last_ash = p_ash.iloc[-1]
                ash_date = pd.to_datetime(last_ash['Date']).strftime('%b %d, %Y')
                st.markdown(f"""
                    <div class="assessment-card border-orange">
                        <div class="card-top">
                            <div class="card-title-wrap">
                                <span class="badge-num badge-orange">1</span>
                                <span class="card-title">ASH Isometric Shoulder Test</span>
                            </div>
                            <span class="card-date">{ash_date}</span>
                        </div>
                        <div class="card-metrics">
                            <strong>Left Peak Force:</strong> {last_ash[ash_l_col]:.1f} N &nbsp;|&nbsp; 
                            <strong>Right Peak Force:</strong> {last_ash[ash_r_col]:.1f} N
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # 2. CMJ
            if not p_cmj.empty and cmj_h_col:
                last_cmj = p_cmj.iloc[-1]
                cmj_date = pd.to_datetime(last_cmj['Date']).strftime('%b %d, %Y')
                rsi_val = f" | <strong>RSI-m:</strong> {last_cmj[cmj_rsi_col]:.2f}" if cmj_rsi_col and not pd.isna(last_cmj[cmj_rsi_col]) else ""
                st.markdown(f"""
                    <div class="assessment-card border-blue">
                        <div class="card-top">
                            <div class="card-title-wrap">
                                <span class="badge-num badge-blue">2</span>
                                <span class="card-title">Countermovement Jump</span>
                            </div>
                            <span class="card-date">{cmj_date}</span>
                        </div>
                        <div class="card-metrics">
                            <strong>Jump Height:</strong> {last_cmj[cmj_h_col]:.1f} cm{rsi_val}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # 3. Shoulder ER ROM
            if not p_er.empty and er_l_col and er_r_col:
                last_er = p_er.iloc[-1]
                er_date = pd.to_datetime(last_er['Date']).strftime('%b %d, %Y')
                st.markdown(f"""
                    <div class="assessment-card border-orange">
                        <div class="card-top">
                            <div class="card-title-wrap">
                                <span class="badge-num badge-orange">3</span>
                                <span class="card-title">External Rotation (ER) ROM</span>
                            </div>
                            <span class="card-date">{er_date}</span>
                        </div>
                        <div class="card-metrics">
                            <strong>Left Max ROM:</strong> {last_er[er_l_col]:.1f}° &nbsp;|&nbsp; 
                            <strong>Right Max ROM:</strong> {last_er[er_r_col]:.1f}°
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # 4. Grip Strength
            if not p_grip.empty and grip_l_col and grip_r_col:
                last_grip = p_grip.iloc[-1]
                grip_date = pd.to_datetime(last_grip['Date']).strftime('%b %d, %Y')
                st.markdown(f"""
                    <div class="assessment-card border-blue">
                        <div class="card-top">
                            <div class="card-title-wrap">
                                <span class="badge-num badge-blue">4</span>
                                <span class="card-title">Grip Strength Test</span>
                            </div>
                            <span class="card-date">{grip_date}</span>
                        </div>
                        <div class="card-metrics">
                            <strong>Left Max Force:</strong> {last_grip[grip_l_col]:.1f} N &nbsp;|&nbsp; 
                            <strong>Right Max Force:</strong> {last_grip[grip_r_col]:.1f} N
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # 5. 20m Sprint
            if not p_sprint.empty and sprint_time_col:
                last_sprint = p_sprint.iloc[-1]
                sprint_date = pd.to_datetime(last_sprint['Date']).strftime('%b %d, %Y')
                st.markdown(f"""
                    <div class="assessment-card border-orange">
                        <div class="card-top">
                            <div class="card-title-wrap">
                                <span class="badge-num badge-orange">5</span>
                                <span class="card-title">20m Sprint Performance</span>
                            </div>
                            <span class="card-date">{sprint_date}</span>
                        </div>
                        <div class="card-metrics">
                            <strong>Time:</strong> {last_sprint[sprint_time_col]:.2f} s
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # --- 6. NAVIGATION TABS ---
        tab_testing, tab_catapult = st.tabs(["TESTING", "CATAPULT PROFILE"])

        # =========================================================================
        # TAB 1: TESTING
        # =========================================================================
        with tab_testing:
            st.markdown('<div class="section-header">Latest Assessment Summary</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            render_assessment_cards()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Testing History Tables</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            # 1. ASH History Table
            if not p_ash.empty:
                st.markdown('<div class="sub-header-title">ASH Isometric Shoulder Test History</div>', unsafe_allow_html=True)
                ash_cols = [c for c in ['Date', ash_l_col, ash_r_col] if c and c in p_ash.columns]
                ash_tbl = p_ash[ash_cols].copy()
                if 'Date' in ash_tbl.columns:
                    ash_tbl['Date'] = ash_tbl['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(ash_tbl), unsafe_allow_html=True)

            # 2. CMJ History Table
            if not p_cmj.empty:
                st.markdown('<div class="sub-header-title">Countermovement Jump History</div>', unsafe_allow_html=True)
                cmj_cols = [c for c in ['Date', cmj_h_col, cmj_rsi_col] if c and c in p_cmj.columns]
                cmj_tbl = p_cmj[cmj_cols].copy()
                if 'Date' in cmj_tbl.columns:
                    cmj_tbl['Date'] = cmj_tbl['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(cmj_tbl), unsafe_allow_html=True)

            # 3. ER ROM History Table
            if not p_er.empty:
                st.markdown('<div class="sub-header-title">External Rotation (ER) ROM History</div>', unsafe_allow_html=True)
                er_cols = [c for c in ['Date', er_l_col, er_r_col] if c and c in p_er.columns]
                er_tbl = p_er[er_cols].copy()
                if 'Date' in er_tbl.columns:
                    er_tbl['Date'] = er_tbl['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(er_tbl), unsafe_allow_html=True)

            # 4. Grip Strength History Table
            if not p_grip.empty:
                st.markdown('<div class="sub-header-title">Grip Strength History</div>', unsafe_allow_html=True)
                grip_cols = [c for c in ['Date', grip_l_col, grip_r_col] if c and c in p_grip.columns]
                grip_tbl = p_grip[grip_cols].copy()
                if 'Date' in grip_tbl.columns:
                    grip_tbl['Date'] = grip_tbl['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(grip_tbl), unsafe_allow_html=True)

            # 5. 20m Sprint History Table
            if not p_sprint.empty:
                st.markdown('<div class="sub-header-title">20m Sprint Performance History</div>', unsafe_allow_html=True)
                sprint_cols = [c for c in ['Date', sprint_time_col] if c and c in p_sprint.columns]
                sprint_tbl = p_sprint[sprint_cols].copy()
                if 'Date' in sprint_tbl.columns:
                    sprint_tbl['Date'] = sprint_tbl['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(sprint_tbl), unsafe_allow_html=True)

        # =========================================================================
        # TAB 2: CATAPULT PROFILE
        # =========================================================================
        with tab_catapult:
            st.markdown('<div class="section-header">Catapult Swing & Throw Analytics</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            with st.expander("Metric Descriptions", expanded=False):
                st.markdown("#### **Throwing Metrics Legend**")
                t_l1, t_l2, t_l3 = st.columns(3)
                with t_l1:
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Player Load 1</div>
                            <div class="legend-desc">Light, low-effort throws. Examples include short-distance warming up, playing light catch, or casual sub-maximal returns.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Rotation Band 1</div>
                            <div class="legend-desc">Throws made with minimal hip/torso separation or torso whip. These are typically flick throws, touch passes, or flat-footed tossing.</div>
                        </div>
                    """, unsafe_allow_html=True)
                with t_l2:
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Player Load 2</div>
                            <div class="legend-desc">Moderate-effort throws. Examples include standard situational plays, standard infield/outfield drill throws, or medium-distance tracking.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Rotation Band 2</div>
                            <div class="legend-desc">Standard mechanical throws where the body goes through a normal, controlled rotational sequence.</div>
                        </div>
                    """, unsafe_allow_html=True)
                with t_l3:
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Player Load 3</div>
                            <div class="legend-desc">Max-effort, high-stress throws. Examples include high-velocity pitches, max-effort outfield crow-hops, or deep downfield passes.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Rotation Band 3</div>
                            <div class="legend-desc">Highly explosive throws with aggressive trunk rotation and arm-whip. Tracks when an athlete is using full rotational power.</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### **Batting Swing Metrics Legend**")
                s_l1, s_l2, s_l3 = st.columns(3)
                with s_l1:
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Rotation Band 1</div>
                            <div class="legend-desc">Total number of low-intensity/slower swings (e.g., check swings, warm-up swings).</div>
                        </div>
                    """, unsafe_allow_html=True)
                with s_l2:
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Rotation Band 2</div>
                            <div class="legend-desc">Moderate-speed swings from standard practice reps and controlled contact drills.</div>
                        </div>
                    """, unsafe_allow_html=True)
                with s_l3:
                    st.markdown("""
                        <div class="legend-card">
                            <div class="legend-title">Rotation Band 3</div>
                            <div class="legend-desc">Game-speed, max-effort rotational swings tracking high bat-speed efforts.</div>
                        </div>
                    """, unsafe_allow_html=True)

            # --- THROW LOGS ---
            st.markdown('<div class="sub-header-title">Throw Data Log</div>', unsafe_allow_html=True)
            if not p_throw.empty:
                disp_throw = p_throw.copy()
                if 'Date' in disp_throw.columns:
                    disp_throw['Date'] = disp_throw['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(disp_throw), unsafe_allow_html=True)
            else:
                st.info("No throw data available for selected date range.")

            # --- SWING LOGS ---
            st.markdown('<div class="sub-header-title">Batting Swing Data Log</div>', unsafe_allow_html=True)
            if not p_swing.empty:
                disp_swing = p_swing.copy()
                if 'Date' in disp_swing.columns:
                    disp_swing['Date'] = disp_swing['Date'].dt.strftime('%b %d, %Y')
                st.markdown(render_custom_table(disp_swing), unsafe_allow_html=True)
            else:
                st.info("No swing data available for selected date range.")
