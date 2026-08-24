import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance", layout="wide")

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

    # --- 3. CUSTOM LADY VOL & TESTING CSS ---
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #1D1D1F; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        
        /* Metric & General Header */
        [data-testid="stMetricValue"] { font-size: 26px; font-weight: 800; color: #FF8200; }
        .athlete-header {
            background-color: #F8F9FA; padding: 20px 24px; border-radius: 16px;
            border-left: 10px solid #FF8200; margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .player-photo { border-radius: 50%; width: 120px; height: 120px; object-fit: cover; border: 4px solid #4895DB; }

        /* Testing Section Headers */
        .section-header {
            color: #2F80ED; font-size: 24px; font-weight: 800; letter-spacing: 0.5px;
            text-transform: uppercase; margin-top: 10px; margin-bottom: 6px;
        }
        .section-bar { height: 3px; background-color: #FF8200; margin-bottom: 25px; border-radius: 2px; }
        .sub-header-title {
            color: #2F80ED; font-size: 20px; font-weight: 800; letter-spacing: 0.5px;
            text-transform: uppercase; margin-bottom: 15px;
        }

        /* Testing Metric Badges */
        .kpi-badge {
            border-radius: 12px; padding: 18px 10px; text-align: center; color: white;
            display: flex; flex-direction: column; justify-content: center; height: 95px;
        }
        .kpi-badge-green { background-color: #28a745; }
        .kpi-badge-red { background-color: #dc3545; }
        .kpi-badge-orange { background-color: #FF8200; }
        .kpi-badge h1 { margin: 0; font-size: 32px; font-weight: 800; line-height: 1.1; }
        .kpi-badge p { margin: 4px 0 0 0; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; opacity: 0.95; }

        /* Context Callout Box */
        .context-box {
            background-color: #F8F9FA; border-left: 5px solid #FF8200;
            padding: 12px 14px; border-radius: 4px; margin-top: 15px; font-size: 13px;
            color: #495057; font-weight: 600; line-height: 1.6;
        }

        /* Best Hero Card */
        .best-card {
            background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
            border: 1px solid #E0E0E0; border-top: 4px solid #FF8200;
            border-radius: 12px; padding: 14px; text-align: center; margin-bottom: 20px;
        }
        .best-card h4 { margin: 0; color: #6c757d; font-size: 12px; text-transform: uppercase; }
        .best-card h2 { margin: 6px 0 2px 0; font-size: 24px; font-weight: 800; color: #FF8200; }
        .best-card p { margin: 0; font-size: 11px; color: #4895DB; font-weight: 700; }

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

        raw_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
        raw_cmj = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')
        raw_swing = swing_df[swing_df['Name'] == selected].sort_values('Date')
        raw_throw = throw_df[throw_df['Name'] == selected].sort_values('Date')

        p_ash = filter_season(raw_ash).copy()
        p_cmj = filter_season(raw_cmj).copy()
        p_swing = filter_season(raw_swing).copy()
        p_throw = filter_season(raw_throw).copy()

        latest_ash = p_ash.iloc[-1] if not p_ash.empty else (raw_ash.iloc[-1] if not raw_ash.empty else None)
        img_url = latest_ash.get('Photo', 'https://www.w3schools.com/howto/img_avatar.png') if latest_ash is not None else 'https://www.w3schools.com/howto/img_avatar.png'

        st.markdown(f"""
            <div class="athlete-header">
                <div style="display: flex; align-items: center;">
                    <img src="{img_url}" class="player-photo">
                    <div style="margin-left: 25px;">
                        <h1 style="margin:0; font-size:30px; font-weight:800;">{selected}</h1>
                        <p style="color:#4895DB; font-weight:700; font-size:15px; margin:4px 0 0 0;">{season_option}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        def get_best_record(df, col_name, is_min=False):
            if df.empty or col_name not in df.columns:
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
        tab_profile, tab_testing, tab_catapult = st.tabs(["INDIVIDUAL PROFILE", "TESTING PROFILE", "CATAPULT PROFILE"])

        # =========================================================================
        # TAB 1: INDIVIDUAL PROFILE
        # =========================================================================
        with tab_profile:
            st.subheader("ALL-TIME PERSONAL BESTS")
            b_cmj_h, b_cmj_h_date = get_best_record(raw_cmj, 'Jump Height (Imp-Mom) [cm]')
            b_rsi, b_rsi_date = get_best_record(raw_cmj, 'RSI-modified (Imp-Mom) [m/s]')
            b_ash_f, b_ash_f_date = get_best_record(raw_ash, 'Peak Vertical Force [N]')
            b_ash_rfd, b_ash_rfd_date = get_best_record(raw_ash, 'RFD - 200ms [N/s]')

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
                val = f"{int(b_ash_f)} N" if b_ash_f is not None else "N/A"
                d_str = f"Set on {b_ash_f_date}" if b_ash_f_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ASH Force</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)
            with b4:
                val = f"{int(b_ash_rfd)} N/s" if b_ash_rfd is not None else "N/A"
                d_str = f"Set on {b_ash_rfd_date}" if b_ash_rfd_date else "No Record"
                st.markdown(f'<div class="best-card"><h4>Best ASH RFD</h4><h2>{val}</h2><p>{d_str}</p></div>', unsafe_allow_html=True)

            st.divider()

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

                st.subheader("ATHLETE STATUS (WINDOW)")
                s1, s2, s3, s4 = st.columns(4)

                rsi_col = 'RSI-modified (Imp-Mom) [m/s]'
                rsi_best = pd.to_numeric(p_cmj[rsi_col], errors='coerce').max() if rsi_col in p_cmj.columns and not p_cmj.empty else 0
                rsi_curr = pd.to_numeric(w_cmj[rsi_col], errors='coerce').mean() if rsi_col in w_cmj.columns and not w_cmj.empty else 0
                rsi_diff = rsi_curr - rsi_best
                rsi_status = "PEAKING" if rsi_curr >= (rsi_best * 0.95 and rsi_best > 0) else "STABLE" if rsi_curr >= (rsi_best * 0.85 and rsi_best > 0) else "FATIGUED"
                s1.metric("RSI-modified", rsi_status, delta=f"{rsi_diff:+.2f} vs Best" if rsi_best > 0 else "N/A")
                s1.markdown(f'<p class="metric-sub">Window Avg: <b>{rsi_curr:.2f}</b> (Best: {rsi_best:.2f})</p>', unsafe_allow_html=True)

                l_avg = pd.to_numeric(w_ash.get('Peak Vertical Force [N] (L)', 0), errors='coerce').mean() if not w_ash.empty else 0
                r_avg = pd.to_numeric(w_ash.get('Peak Vertical Force [N] (R)', 0), errors='coerce').mean() if not w_ash.empty else 0
                asym = (abs(l_avg - r_avg) / max(l_avg, r_avg) * 100) if max(l_avg, r_avg) > 0 else 0
                s2.metric("Asymmetry", f"{asym:.1f}%", delta="LOW" if asym < 10 else "HIGH", delta_color="inverse")
                s2.markdown(f'<p class="metric-sub">L: {int(l_avg)}N | R: {int(r_avg)}N</p>', unsafe_allow_html=True)

                s_vol = pd.to_numeric(w_swing.get('Swing Count', 0), errors='coerce').sum() if not w_swing.empty else 0
                t_vol = pd.to_numeric(w_throw.get('Total Throw Count', 0), errors='coerce').sum() if not w_throw.empty else 0
                total_reps = int(s_vol + t_vol)
                s3.metric("Load", "MODERATE" if 150 < total_reps < 300 else "HIGH" if total_reps >= 300 else "LOW")
                s3.markdown(f'<p class="metric-sub">Total Reps: <b>{total_reps}</b></p>', unsafe_allow_html=True)

                s_int = pd.to_numeric(w_swing.get('Swing Max Rotation Band 3 Count', 0), errors='coerce').sum() if not w_swing.empty else 0
                s_qual = (s_int / s_vol * 100) if s_vol > 0 else 0
                s4.metric("Intent", "HIGH" if s_qual > 25 else "NORMAL")
                s4.markdown(f'<p class="metric-sub">Quality: <b>{s_qual:.1f}%</b></p>', unsafe_allow_html=True)

                st.divider()
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
        # TAB 2: TESTING PROFILE (MATCHING EXACT VISUAL SPECIFICATION)
        # =========================================================================
        with tab_testing:
            st.markdown('<div class="section-header">WEEKLY READINESS PROFILE</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-bar"></div>', unsafe_allow_html=True)

            # -------------------------------------------------------------
            # SECTION 1: COUNTERMOVEMENT JUMP
            # -------------------------------------------------------------
            st.markdown('<div class="sub-header-title">COUNTERMOVEMENT JUMP</div>', unsafe_allow_html=True)
            
            # Prep CMJ Data
            p_cmj_ready = p_cmj.dropna(subset=['Date']).sort_values('Date').copy() if not p_cmj.empty else pd.DataFrame()
            cmj_h_col = 'Jump Height (Imp-Mom) [cm]'
            rsi_col = 'RSI-modified (Imp-Mom) [m/s]'

            if not p_cmj_ready.empty and cmj_h_col in p_cmj_ready.columns and rsi_col in p_cmj_ready.columns:
                p_cmj_ready[cmj_h_col] = pd.to_numeric(p_cmj_ready[cmj_h_col], errors='coerce')
                p_cmj_ready[rsi_col] = pd.to_numeric(p_cmj_ready[rsi_col], errors='coerce')
                
                # Latest & Baselines
                lat_cmj = p_cmj_ready.iloc[-1]
                latest_h = lat_cmj[cmj_h_col]
                latest_rsi = lat_cmj[rsi_col]
                
                base_h = p_cmj_ready[cmj_h_col].mean()
                base_rsi = p_cmj_ready[rsi_col].mean()

                chg_h = ((latest_h - base_h) / base_h * 100) if base_h > 0 else 0
                chg_rsi = ((latest_rsi - base_rsi) / base_rsi * 100) if base_rsi > 0 else 0

                # Badge colors
                h_badge_cls = "kpi-badge-green" if chg_h >= -5 else "kpi-badge-red"
                rsi_badge_cls = "kpi-badge-green" if chg_rsi >= -5 else "kpi-badge-red"

                c_left, c_right = st.columns([1.1, 2])
                with c_left:
                    b1, b2 = st.columns(2)
                    with b1:
                        st.markdown(f"""
                            <div class="kpi-badge {h_badge_cls}">
                                <h1>{latest_h:.1f}</h1>
                                <p>CMJ HEIGHT</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with b2:
                        st.markdown(f"""
                            <div class="kpi-badge {rsi_badge_cls}">
                                <h1>{latest_rsi:.2f}</h1>
                                <p>RSI MOD</p>
                            </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f"""
                        <div class="context-box">
                            <div><b>% Change from Base:</b> CMJ: {chg_h:+.1f}% | RSI: {chg_rsi:+.1f}%</div>
                            <div><b>Base Values:</b> CMJ: {base_h:.1f} | RSI: {base_rsi:.2f}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with c_right:
                    # Dual Y-Axis Line Chart
                    fig_cmj = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_cmj.add_trace(
                        go.Scatter(
                            x=p_cmj_ready['Date'], y=p_cmj_ready[cmj_h_col],
                            name="Jump Height", mode="lines+markers",
                            line=dict(color="#FF8200", width=3),
                            marker=dict(size=7, color="#FF8200")
                        ),
                        secondary_y=False
                    )
                    fig_cmj.add_trace(
                        go.Scatter(
                            x=p_cmj_ready['Date'], y=p_cmj_ready[rsi_col],
                            name="RSI Modified", mode="lines+markers",
                            line=dict(color="#2F80ED", width=2.5, dash="dot"),
                            marker=dict(size=7, color="#2F80ED")
                        ),
                        secondary_y=True
                    )
                    fig_cmj.update_layout(
                        template="plotly_white",
                        height=240,
                        margin=dict(l=10, r=10, t=30, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12, color="#1D1D1F")),
                        xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y")
                    )
                    fig_cmj.update_yaxes(showgrid=True, gridcolor="#F0F2F6", secondary_y=False)
                    fig_cmj.update_yaxes(showgrid=False, secondary_y=True)
                    st.plotly_chart(fig_cmj, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No Countermovement Jump records available for this season.")

            st.markdown("<br>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # SECTION 2: ASH SHOULDER: ISO I
            # -------------------------------------------------------------
            st.markdown('<div class="sub-header-title">ASH SHOULDER: ISO I</div>', unsafe_allow_html=True)

            p_ash_ready = p_ash.dropna(subset=['Date']).sort_values('Date').copy() if not p_ash.empty else pd.DataFrame()
            f_l_col = 'Peak Vertical Force [N] (L)'
            f_r_col = 'Peak Vertical Force [N] (R)'

            if not p_ash_ready.empty and f_l_col in p_ash_ready.columns and f_r_col in p_ash_ready.columns:
                p_ash_ready[f_l_col] = pd.to_numeric(p_ash_ready[f_l_col], errors='coerce').fillna(0)
                p_ash_ready[f_r_col] = pd.to_numeric(p_ash_ready[f_r_col], errors='coerce').fillna(0)

                lat_ash_r = p_ash_ready.iloc[-1]
                latest_l = lat_ash_r[f_l_col]
                latest_r = lat_ash_r[f_r_col]

                base_l = p_ash_ready[f_l_col].mean()
                base_r = p_ash_ready[f_r_col].mean()

                chg_l = ((latest_l - base_l) / base_l * 100) if base_l > 0 else 0
                chg_r = ((latest_r - base_r) / base_r * 100) if base_r > 0 else 0

                asym_val = (abs(latest_l - latest_r) / max(latest_l, latest_r) * 100) if max(latest_l, latest_r) > 0 else 0
                
                # Asymmetry & Status logic
                l_badge_cls = "kpi-badge-red" if asym_val > 10 else "kpi-badge-green"
                r_badge_cls = "kpi-badge-red" if asym_val > 10 else "kpi-badge-green"

                a_left, a_right = st.columns([1.1, 2])
                with a_left:
                    ab1, ab2 = st.columns(2)
                    with ab1:
                        st.markdown(f"""
                            <div class="kpi-badge {l_badge_cls}">
                                <h1>{int(latest_l)} N</h1>
                                <p>LEFT</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with ab2:
                        st.markdown(f"""
                            <div class="kpi-badge {r_badge_cls}">
                                <h1>{int(latest_r)} N</h1>
                                <p>RIGHT</p>
                            </div>
                        """, unsafe_allow_html=True)

                    st.markdown(f"""
                        <div class="context-box">
                            <div><b>Asymmetry:</b> {asym_val:+.1f}%</div>
                            <div><b>% Change from Base:</b> L: {chg_l:+.1f}% | R: {chg_r:+.1f}%</div>
                            <div><b>Base Force:</b> L: {int(base_l)} N | R: {int(base_r)} N</div>
                        </div>
                    """, unsafe_allow_html=True)

                with a_right:
                    # Left vs Right Line Chart with Solid & Dashed Styling
                    fig_ash_p = go.Figure()
                    fig_ash_p.add_trace(
                        go.Scatter(
                            x=p_ash_ready['Date'], y=p_ash_ready[f_l_col],
                            name="Left Peak Force", mode="lines+markers",
                            line=dict(color="#2F80ED", width=3),
                            marker=dict(size=7, color="#2F80ED")
                        )
                    )
                    fig_ash_p.add_trace(
                        go.Scatter(
                            x=p_ash_ready['Date'], y=p_ash_ready[f_r_col],
                            name="Right Peak Force", mode="lines+markers",
                            line=dict(color="#FF8200", width=3, dash="dash"),
                            marker=dict(size=7, color="#FF8200")
                        )
                    )
                    fig_ash_p.update_layout(
                        template="plotly_white",
                        height=240,
                        margin=dict(l=10, r=10, t=30, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12, color="#1D1D1F")),
                        xaxis=dict(showgrid=True, gridcolor="#F0F2F6", tickformat="%b %d<br>%Y"),
                        yaxis=dict(showgrid=True, gridcolor="#F0F2F6")
                    )
                    st.plotly_chart(fig_ash_p, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No ASH Shoulder records available for this season.")

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
