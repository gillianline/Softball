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
            # 1. MANUAL ASYMMETRY & FORCE CALCULATION
            # Pulling raw values from the latest test
            l_f = latest_ash.get('Peak Vertical Force [N] (L)', 0)
            r_f = latest_ash.get('Peak Vertical Force [N] (R)', 0)
            
            # Calculate Asymmetry manually to ensure accuracy
            if l_f > 0 and r_f > 0:
                clean_asym = (abs(l_f - r_f) / max(l_f, r_f)) * 100
            else:
                clean_asym = 0.0

            # 2. TOP METRIC ROW
            m1, m2, m3 = st.columns(3)
            
            # Left Peak Force
            m1.metric("Left Peak Force", f"{l_f} N")
            
            # Right Peak Force
            m2.metric("Right Peak Force", f"{r_f} N")
            
            # Calculated Asymmetry
            # Colors turn red if asymmetry exceeds 10%
            m3.metric(
                "Asymmetry", 
                f"{clean_asym:.1f}%", 
                delta="High" if clean_asym > 10 else "Normal", 
                delta_color="inverse"
            )

            st.divider()

            # 3. VISUAL BALANCE BOX
            # High-contrast summary box for quick review
            asym_color = '#dc3545' if clean_asym > 10 else '#28a745'
            
            st.markdown(f"""
                <div style="background-color:#F8F9FA; padding:20px; border-radius:15px; border:1px solid #E0E0E0; text-align:center;">
                    <div style="display:flex; justify-content:space-around; margin-bottom:20px;">
                        <div>
                            <p style="color:#4895DB; font-weight:800; margin:0; font-size:14px;">LEFT ARM</p>
                            <h1 style="margin:0; font-size:48px;">{l_f}<span style="font-size:20px;">N</span></h1>
                        </div>
                        <div style="border-left:1px solid #E0E0E0; height:60px; margin-top:10px;"></div>
                        <div>
                            <p style="color:#FF8200; font-weight:800; margin:0; font-size:14px;">RIGHT ARM</p>
                            <h1 style="margin:0; font-size:48px;">{r_f}<span style="font-size:20px;">N</span></h1>
                        </div>
                    </div>
                    <p style="margin:0; font-size:12px; color:grey; font-weight:700; letter-spacing:1px;">TOTAL ASYMMETRY</p>
                    <h1 style="margin:0; color:{asym_color}; font-size:56px;">{clean_asym:.1f}%</h1>
                </div>
            """, unsafe_allow_html=True)

            # 4. DOMINANCE INDICATOR
            if l_f != r_f:
                dom_side = "Left" if l_f > r_f else "Right"
                st.info(f"Dominant Side: **{dom_side}**")

        else:
            st.info("No ASH records found for the selected athlete.")
            
            
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
