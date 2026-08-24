import streamlit as st
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
        
        /* Banner */
        .athlete-banner {
            background-color: #F8F9FA; padding: 18px 24px; border-radius: 14px;
            border-left: 8px solid #FF8200; margin-bottom: 20px;
            display: flex; align-items: center; justify-content: space-between;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        }
        .athlete-info { display: flex; align-items: center; }
        .player-photo { border-radius: 50%; width: 90px; height: 90px; object-fit: cover; border: 3px solid #2F80ED; margin-right: 20px; }
        .athlete-name { margin: 0; font-size: 26px; font-weight: 800; color: #1D1D1F; }
        .athlete-sub { margin: 2px 0 0 0; color: #2F80ED; font-weight: 700; font-size: 14px; }
        
        /* Typography */
        .section-header {
            color: #2F80ED; font-size: 22px; font-weight: 800; letter-spacing: 0.5px;
            text-transform: uppercase; margin-top: 10px; margin-bottom: 4px;
        }
        .section-divider { height: 3px; background-color: #FF8200; margin-bottom: 22px; border-radius: 2px; }
        .sub-header-title {
            color: #2F80ED; font-size: 18px; font-weight: 800; letter-spacing: 0.5px;
            text-transform: uppercase; margin-bottom: 12px;
        }

        /* Best Hero Cards */
        .best-card {
            background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
            border: 1px solid #EAEAEA; border-top: 4px solid #FF8200;
            border-radius: 10px; padding: 14px 10px; text-align: center; margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .best-card h4 { margin: 0; color: #6c757d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        .best-card h2 { margin: 6px 0 2px 0; font-size: 24px; font-weight: 800; color: #FF8200; }
        .best-card p { margin: 0; font-size: 11px; color: #2F80ED; font-weight: 700; }

        /* Metric Tile Badges */
        .kpi-tile {
            border-radius: 12px; padding: 16px 8px; text-align: center; color: #FFFFFF;
            display: flex; flex-direction: column; justify-content: center; height: 90px;
        }
        .tile-green { background-color: #28a745; }
        .tile-red { background-color: #dc3545; }
        .tile-orange { background-color: #FF8200; }
        .kpi-tile h1 { margin: 0; font-size: 28px; font-weight: 800; line-height: 1.1; }
        .kpi-tile p { margin: 4px 0 0 0; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }

        /* Detail Callout Box */
        .detail-box {
            background-color: #F8F9FA; border-left: 4px solid #FF8200;
            padding: 10px 14px; border-radius: 4px; margin-top: 12px; font-size: 12px;
            color: #495057; font-weight: 600; line-height: 1.5;
        }

        /* Tables */
        .coach-table { width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; margin-top: 10px; }
        .coach-table th { background-color: #F8F9FA; padding: 10px; border-bottom: 2px solid #DEE2E6; color: #495057; font-weight: 700; font-size: 12px; }
        .coach-table td { padding: 10px; border-bottom: 1px solid #EEEEEE; font-size: 13px; }
        
        #MainMenu, footer, header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # Clean numeric helper to extract float values even if followed by L, R, %, etc.
    def clean_num_series(series):
        if series is None:
            return pd.Series(dtype=float)
        return series.astype(str).apply(lambda x: re.findall(r"[-+]?\d*\.?\d+", x)[0] if re.findall(r"[-+]?\d*\.?\d+", str(x)) else np.nan).astype(float)

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

            # Clean ASH numbers
            for col in ash_df.columns:
                if any(k in col.lower() for k in ['force', 'asym', 'rfd']):
                    ash_df[col] = clean_num_series(ash_df[col])

            # Clean CMJ numbers
            for col in cmj_df.columns:
                if any(k in col.lower() for k in ['height', 'power', 'rsi', 'velocity', 'force', 'impulse', 'rfd', 'stiffness', 'bw']):
                    cmj_df[col] = clean_num_series(cmj_df[col])

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

    def find_col(df, options):
        for opt in options:
            match = [c for c in df.columns if c.strip().lower() == opt.strip().lower()]
            if match:
                return match[0]
            match_part = [c for c in df.columns if opt.strip().lower() in c.strip().lower()]
            if match_part:
                return match_part[0]
        return None

    if not ash_df.empty or not cmj_df.empty:
        # --- 5. SEASON SETUP ---
        TODAY = pd.to_datetime(date.today())
        SPRING_START = pd.to_datetime("2026-01-01")
        SPRING_END = pd.to_datetime("2026-05-31 23:59:59")
        FALL_START = TODAY

        all_athletes = sorted(list(set(
            list(ash_df['Player Name'].dropna().unique() if 'Player Name' in ash_df.columns else []) +
            list(cmj_df['Player Name'].dropna().unique() if 'Player Name' in cmj_df.columns else [])
        )))

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected = st.selectbox("Select Athlete", all_athletes)
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

        # Athlete raw and season filtered slices
        raw_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in ash_df.columns else pd.DataFrame()
        raw_cmj = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date') if 'Player Name' in cmj_df.columns else pd.DataFrame()
        raw_swing = swing_df[swing_df['Name'] == selected].sort_values('Date') if 'Name' in swing_df.columns else pd.DataFrame()
        raw_throw = throw_df[throw_df['Name'] == selected].sort_values('Date') if 'Name' in throw_df.columns else pd.DataFrame()

        p_ash = filter_season(raw_ash).copy()
        p_cmj = filter_season(raw_cmj).copy()
        p_swing = filter_season(raw_swing).copy()
        p_throw = filter_season(raw_throw).copy()

        # Dynamic ASH Column Identification
        ash_f_col = find_col(ash_df, ['Peak Vertical Force [N]', 'Peak Force [N]'])
        ash_l_col = find_col(ash_df, ['Peak Vertical Force [N] (L)', 'Force (L)'])
        ash_r_col = find_col(ash_df, ['Peak Vertical Force [N] (R)', 'Force (R)'])
        ash_asym_col = find_col(ash_df, ['Peak Vertical Force [N] (Asym)(%)', 'Asymmetry'])

        # Dynamic CMJ Column Identification
        cmj_h_col = find_col(cmj_df, ['Jump Height (Imp-Mom) [cm]', 'Jump Height [cm]'])
        cmj_rsi_col = find_col(cmj_df, ['RSI-modified (Imp-Mom) [m/s]', 'RSI-modified'])

        # Header Photo
        photo_source = raw_ash if not raw_ash.empty else raw_cmj
        latest_photo_rec = photo_source.iloc[-1] if not photo_source.empty else None
        img_url = latest_photo_rec.get('Photo', 'https://www.w3schools.com/howto/img_avatar.png') if latest_photo_rec is not None else 'https://www.w3schools.com/howto/img_avatar.png'

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

        # --- 6. NAVIGATION TABS ---
        tab_testing, tab_catapult = st.tabs(["TESTING PROFILE", "CATAPULT PROFILE"])

        # =========================================================================
        # TAB 1: TESTING PROFILE
        # =========================================================================
        with tab_testing:
            # --- OVERALL BEST TEST HERO CARDS (WITH BOTH L & R SIDES) ---
            st.subheader("ALL-TIME PERSONAL BESTS")
            b_cmj_h, b_cmj_h_date = get_best_record(raw_cmj, cmj_h_col)
            b_rsi, b_rsi_date = get_best_record(raw_cmj, cmj_rsi_col)
            b_ash_l, b_ash_l_date = get_best_record(raw_ash, ash_l_col)
            b_ash_r, b_ash_r_date = get_best_record(raw_ash, ash_r_col)

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                val = f"{b_cmj_h:.1f} cm" if b_cmj_h is not None else "N/A"
                d_str = f"Set on {b_cmj_h_date}" if b_cmj_h_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best Jump Height</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b2:
                val = f"{b_rsi:.2f}" if b_rsi is not None else "N/A"
                d_str = f"Set on {b_rsi_date}" if b_rsi_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best RSI-modified</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b3:
                val = f"{int(b_ash_l)} N" if b_ash_l is not None else "N/A"
                d_str = f"Set on {b_ash_l_date}" if b_ash_l_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ASH Force (Left)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b4:
                val = f"{int(b_ash_r)} N" if b_ash_r is not None else "N/A"
                d_str = f"Set on {b_ash_r_date}" if b_ash_r_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ASH Force (Right)</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">WEEKLY READINESS PROFILE</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            # -------------------------------------------------------------
            # SECTION 1: COUNTERMOVEMENT JUMP
            # -------------------------------------------------------------
            st.markdown('<div class="sub-header-title">COUNTERMOVEMENT JUMP</div>', unsafe_allow_html=True)
            
            p_cmj_ready = p_cmj.dropna(subset=['Date']).sort_values('Date').copy() if not p_cmj.empty else pd.DataFrame()

            if not p_cmj_ready.empty and cmj_h_col and cmj_rsi_col and cmj_h_col in p_cmj_ready.columns and cmj_rsi_col in p_cmj_ready.columns:
                p_cmj_ready[cmj_h_col] = pd.to_numeric(p_cmj_ready[cmj_h_col], errors='coerce')
                p_cmj_ready[cmj_rsi_col] = pd.to_numeric(p_cmj_ready[cmj_rsi_col], errors='coerce')
                p_cmj_ready = p_cmj_ready.dropna(subset=[cmj_h_col, cmj_rsi_col])
                
                if not p_cmj_ready.empty:
                    # Group by Date to handle multiple daily trials cleanly
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
                        b1, b2 = st.columns(2)
                        with b1:
                            st.markdown(f"""
                                <div class="kpi-tile {h_tile_cls}">
                                    <h1>{latest_h:.1f}</h1>
                                    <p>CMJ HEIGHT</p>
                                </div>
                            """, unsafe_allow_html=True)
                        with b2:
                            st.markdown(f"""
                                <div class="kpi-tile {rsi_tile_cls}">
                                    <h1>{latest_rsi:.2f}</h1>
                                    <p>RSI MOD</p>
                                </div>
                            """, unsafe_allow_html=True)

                        st.markdown(f"""
                            <div class="detail-box">
                                <div><b>% Change from Base:</b> CMJ: {chg_h:+.1f}% | RSI: {chg_rsi:+.1f}%</div>
                                <div><b>Base Values:</b> CMJ: {base_h:.1f} | RSI: {base_rsi:.2f}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with c_right:
                        fig_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # Jump Height (Orange - Larger marker with border)
                        fig_cmj.add_trace(
                            go.Scatter(
                                x=cmj_plot_df['Date'], 
                                y=cmj_plot_df[cmj_h_col],
                                name="Jump Height", 
                                mode="lines+markers",
                                line=dict(color="#FF8200", width=3.5),
                                marker=dict(size=10, color="#FF8200", line=dict(width=2, color="#FFFFFF"))
                            ),
                            secondary_y=False
                        )
                        
                        # RSI Modified (Blue - Dot Dash)
                        fig_cmj.add_trace(
                            go.Scatter(
                                x=cmj_plot_df['Date'], 
                                y=cmj_plot_df[cmj_rsi_col],
                                name="RSI Modified", 
                                mode="lines+markers",
                                line=dict(color="#2F80ED", width=2.5, dash="dot"),
                                marker=dict(size=7, color="#2F80ED")
                            ),
                            secondary_y=True
                        )
                        
                        # Dynamic padded axis ranges for 1 data point or flat trends
                        h_min, h_max = cmj_plot_df[cmj_h_col].min(), cmj_plot_df[cmj_h_col].max()
                        r_min, r_max = cmj_plot_df[cmj_rsi_col].min(), cmj_plot_df[cmj_rsi_col].max()
                        
                        y1_range = [h_min - 2, h_max + 2] if h_min == h_max else [h_min * 0.95, h_max * 1.05]
                        y2_range = [r_min - 0.05, r_max + 0.05] if r_min == r_max else [r_min * 0.9, r_max * 1.1]

                        fig_cmj.update_layout(
                            template="plotly_white", 
                            height=240,
                            margin=dict(l=10, r=10, t=25, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                            xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y")
                        )
                        fig_cmj.update_yaxes(range=y1_range, showgrid=True, gridcolor="#F0F2F6", secondary_y=False)
                        fig_cmj.update_yaxes(range=y2_range, showgrid=False, secondary_y=True)
                        st.plotly_chart(fig_cmj, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No Countermovement Jump records available for this selection.")
            else:
                st.info("No Countermovement Jump records available for this season.")

            # -------------------------------------------------------------
            # SECTION 2: ASH SHOULDER: ISO I
            # -------------------------------------------------------------
            st.markdown('<div class="sub-header-title">ASH SHOULDER: ISO I</div>', unsafe_allow_html=True)

            p_ash_ready = p_ash.dropna(subset=['Date']).sort_values('Date').copy() if not p_ash.empty else pd.DataFrame()

            if not p_ash_ready.empty and ash_l_col and ash_r_col and ash_l_col in p_ash_ready.columns and ash_r_col in p_ash_ready.columns:
                p_ash_ready[ash_l_col] = pd.to_numeric(p_ash_ready[ash_l_col], errors='coerce').fillna(0)
                p_ash_ready[ash_r_col] = pd.to_numeric(p_ash_ready[ash_r_col], errors='coerce').fillna(0)
                
                # Filter rows where at least one side was recorded
                p_ash_ready = p_ash_ready[(p_ash_ready[ash_l_col] > 0) | (p_ash_ready[ash_r_col] > 0)]

                if not p_ash_ready.empty:
                    lat_ash_r = p_ash_ready.iloc[-1]
                    latest_l = lat_ash_r[ash_l_col]
                    latest_r = lat_ash_r[ash_r_col]

                    base_l = p_ash_ready[ash_l_col].replace(0, np.nan).mean()
                    base_r = p_ash_ready[ash_r_col].replace(0, np.nan).mean()
                    base_l = base_l if pd.notnull(base_l) else 0
                    base_r = base_r if pd.notnull(base_r) else 0

                    chg_l = ((latest_l - base_l) / base_l * 100) if base_l > 0 else 0
                    chg_r = ((latest_r - base_r) / base_r * 100) if base_r > 0 else 0

                    # Asymmetry logic: prefer precalculated or calculate dynamically
                    if ash_asym_col and ash_asym_col in lat_ash_r and pd.notnull(lat_ash_r[ash_asym_col]):
                        asym_val = float(lat_ash_r[ash_asym_col])
                    else:
                        asym_val = (abs(latest_l - latest_r) / max(latest_l, latest_r) * 100) if max(latest_l, latest_r) > 0 else 0.0
                    
                    l_tile_cls = "tile-red" if asym_val > 10 else "tile-green"
                    r_tile_cls = "tile-red" if asym_val > 10 else "tile-green"

                    a_left, a_right = st.columns([1.1, 2])
                    with a_left:
                        ab1, ab2 = st.columns(2)
                        with ab1:
                            st.markdown(f"""
                                <div class="kpi-tile {l_tile_cls}">
                                    <h1>{int(latest_l)} N</h1>
                                    <p>LEFT</p>
                                </div>
                            """, unsafe_allow_html=True)
                        with ab2:
                            st.markdown(f"""
                                <div class="kpi-tile {r_tile_cls}">
                                    <h1>{int(latest_r)} N</h1>
                                    <p>RIGHT</p>
                                </div>
                            """, unsafe_allow_html=True)

                        st.markdown(f"""
                            <div class="detail-box">
                                <div><b>Asymmetry:</b> {asym_val:+.1f}%</div>
                                <div><b>% Change from Base:</b> L: {chg_l:+.1f}% | R: {chg_r:+.1f}%</div>
                                <div><b>Base Force:</b> L: {int(base_l)} N | R: {int(base_r)} N</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with a_right:
                        fig_ash_p = go.Figure()
                        fig_ash_p.add_trace(
                            go.Scatter(
                                x=p_ash_ready['Date'], y=p_ash_ready[ash_l_col],
                                name="Left Peak Force", mode="lines+markers",
                                line=dict(color="#2F80ED", width=3),
                                marker=dict(size=6, color="#2F80ED")
                            )
                        )
                        fig_ash_p.add_trace(
                            go.Scatter(
                                x=p_ash_ready['Date'], y=p_ash_ready[ash_r_col],
                                name="Right Peak Force", mode="lines+markers",
                                line=dict(color="#FF8200", width=3, dash="dash"),
                                marker=dict(size=6, color="#FF8200")
                            )
                        )
                        fig_ash_p.update_layout(
                            template="plotly_white", height=230,
                            margin=dict(l=10, r=10, t=25, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                            xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"),
                            yaxis=dict(showgrid=True, gridcolor="#F0F2F6")
                        )
                        st.plotly_chart(fig_ash_p, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No ASH Shoulder records available for this selection.")
            else:
                st.info("No ASH Shoulder records available for this season.")

        # =========================================================================
        # TAB 2: CATAPULT PROFILE (SWING & THROW)
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
