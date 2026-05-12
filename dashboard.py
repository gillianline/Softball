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
        
        for df in [ash_df, cmj_df, roster_df]:
            df.columns = df.columns.str.strip()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        ash_metrics = ['Peak Vertical Force [N]', 'RFD - 200ms [N/s]', 'Start Time to Peak Force [s]']
        cmj_metrics = ['Jump Height (Imp-Mom) [cm]', 'RSI-modified (Imp-Mom) [m/s]', 'Peak Power [W]']
        
        for df, metrics in [(ash_df, ash_metrics), (cmj_df, cmj_metrics)]:
            for col in df.columns:
                if any(m in col for m in metrics) or 'Asym' in col:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        
        ash_df = ash_df.merge(roster_df[['Player Name', 'Picture']], on='Player Name', how='left')
        cmj_df = cmj_df.merge(roster_df[['Player Name', 'Picture']], on='Player Name', how='left')
        
        return ash_df, cmj_df
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df = load_all_data()

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
                raw_asym = latest_ash.get('Peak Vertical Force [N] (Asym)(%)', 0)
                st.markdown(f"""
                    <div style="background-color:#F8F9FA; padding:15px; border-radius:10px; border:1px solid #E0E0E0;">
                        <div style="display:flex; justify-content:space-between;">
                            <div style="text-align:center; width:45%;"><p style="color:#4895DB; font-weight:800; margin:0; font-size:12px;">LEFT</p><h2 style="margin:0;">{l_f}<span style="font-size:14px;">N</span></h2><p style="color:grey; font-size:11px; margin:0;">{l_rfd} RFD</p></div>
                            <div style="text-align:center; width:45%;"><p style="color:#FF8200; font-weight:800; margin:0; font-size:12px;">RIGHT</p><h2 style="margin:0;">{r_f}<span style="font-size:14px;">N</span></h2><p style="color:grey; font-size:11px; margin:0;">{r_rfd} RFD</p></div>
                        </div>
                        <div style="text-align:center; border-top:1px solid #E0E0E0; padding-top:10px; margin-top:10px;">
                            <p style="margin:0; font-size:11px; color:grey; font-weight:700;">ASYMMETRY</p>
                            <h3 style="margin:0; color:{'#dc3545' if abs(raw_asym) > 10 else '#28a745'}">{raw_asym}%</h3>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.info(f"Dominance: **{'Right' if r_f > l_f else 'Left'}**")

    with tab_cmj:
        if not cmj_filt.empty:
            c_lat = cmj_filt.iloc[-1]
            
            # 1. THE BIG NUMBERS
            # Force RSI to 2 decimals and Jump Height to 1
            curr_h = c_lat['Jump Height (Imp-Mom) [cm]']
            curr_rsi = c_lat['RSI-modified (Imp-Mom) [m/s]']
            curr_pow = int(c_lat.get('Peak Power [W]', 0))
            
            # Get Bests for the range
            b_h = cmj_filt['Jump Height (Imp-Mom) [cm]'].max()
            b_rsi = cmj_filt['RSI-modified (Imp-Mom) [m/s]'].max()

            # Display Logic
            m1, m2, m3 = st.columns(3)
            
            with m1:
                diff_h = ((curr_h - b_h) / b_h * 100) if b_h != 0 else 0
                st.metric("Jump Height", f"{curr_h:.1f} cm", delta=f"{diff_h:+.1f}% vs Best")
                st.write(f"Season Best: **{b_h:.1f} cm**")

            with m2:
                diff_rsi = ((curr_rsi - b_rsi) / b_rsi * 100) if b_rsi != 0 else 0
                st.metric("RSI-modified", f"{curr_rsi:.2f}", delta=f"{diff_rsi:+.1f}% vs Best")
                st.write(f"Season Best: **{b_rsi:.2f}**")

            with m3:
                st.metric("Peak Power", f"{curr_pow} W")
                st.write(f"Body Weight: **{c_lat.get('BW [KG]', 0):.1f} kg**")

            st.divider()

            # 2. THE TREND (Simplified for clarity)
            st.subheader("Jump Height History")
            fig_cmj = px.line(
                cmj_filt, 
                x='Date', 
                y='Jump Height (Imp-Mom) [cm]', 
                markers=True, 
                template="plotly_white", 
                color_discrete_sequence=["#4895DB"]
            )
            
            # Fix the "All Time" Date weirdness
            fig_cmj.update_xaxes(
                tickformat="%b %d, %y", 
                tickangle=-45, 
                nticks=10,
                title=""
            )
            
            fig_cmj.update_layout(
                height=400, 
                yaxis_title="Height (cm)",
                margin=dict(t=10, b=10, l=10, r=10)
            )
            
            st.plotly_chart(fig_cmj, use_container_width=True)

            # 3. QUICK MECHANICAL CHECK
            st.write("")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write("**Landing Stiffness**")
                st.write(f"{int(c_lat.get('CMJ Stiffness [N/m]', 0))} N/m")
            with col_b:
                st.write("**Braking RFD**")
                st.write(f"{int(c_lat.get('Eccentric Braking RFD [N/s]', 0))} N/s")
            with col_c:
                st.write("**L/R Balance**")
                st.write(f"{c_lat.get('Concentric Mean Force % (Asym) (%)', 0):.1f}%")

        else:
            st.info("No CMJ records found for the selected season.")
