import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance", layout="wide")

# --- CSS: FORMATTING ---
st.markdown("""
    <style>
    th, td {text-align: center !important;}
    [data-testid="stMetricValue"] {font-size: 24px;}
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    .scout-table th { background-color: #4895DB; color: white; padding: 4px; border-bottom: 2px solid #FF8200; font-weight: 700; font-size: 11px; }
    .player-photo-large { border-radius: 50%; width: 200px; height: 200px; object-fit: contain; border: 6px solid #FF8200; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD PROTECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        _, col2, _ = st.columns([1,1,1])
        with col2:
            st.title("🥎 Access Key")
            pwd = st.text_input("Enter Password", type="password")
            if st.button("Login"):
                # Use lowercase 'password' to match standard Streamlit secret naming
                if pwd == st.secrets.get("password", st.secrets.get("PASSWORD")):
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Incorrect Password")
        return False
    return True

if check_password():

    @st.cache_data(ttl=300)
    def load_all_data():
        def heavy_sanitize(frame, name):
            frame.columns = frame.columns.str.strip()
            # Find the Name column dynamically
            name_options = ['Player Name', 'Name', 'Athlete', 'Player']
            found_col = next((c for c in frame.columns if c in name_options or c.lower() in [p.lower() for p in name_options]), None)
            
            if found_col:
                frame.rename(columns={found_col: "Player Name"}, inplace=True)
                frame["Player Name"] = frame["Player Name"].astype(str).str.strip()
            else:
                st.error(f"Critical Error: No 'Player Name' column found in {name} sheet.")
                st.stop()

            # Clean numeric data (Mango Type 1 logic)
            for col in frame.columns:
                if any(word in col.lower() for word in ['force', 'rfd', 'height', 'load', 'count', 'power']):
                    frame[col] = pd.to_numeric(frame[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
            return frame

        try:
            # Loading directly from secrets keys
            # Verify your secrets have these EXACT names
            roster = heavy_sanitize(pd.read_csv(st.secrets["ROSTER_URL"]), "Roster")
            ash    = heavy_sanitize(pd.read_csv(st.secrets["ASH_URL"]), "ASH")
            cmj    = heavy_sanitize(pd.read_csv(st.secrets["CMJ_URL"]), "CMJ")
            throws = heavy_sanitize(pd.read_csv(st.secrets["THROWS_URL"]), "Throws")
            swings = heavy_sanitize(pd.read_csv(st.secrets["SWINGS_URL"]), "Swings")

            # Sequential Merge
            m = roster.merge(ash, on="Player Name", how="left")
            m = m.merge(cmj, on="Player Name", how="left")
            m = m.merge(throws, on="Player Name", how="left")
            m = m.merge(swings, on="Player Name", how="left")
            return m
        except Exception as e:
            st.error(f"Failed to load sheets: {e}")
            st.info("Check your URL secrets. They must end in /export?format=csv")
            st.stop()

    df = load_all_data()

    # --- DASHBOARD UI ---
    st.title("🥎 Softball Performance Analytics")

    # Metrics Bar
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Roster", len(df))
    m2.metric("Avg Peak Force", f"{int(df.get('Peak Vertical Force [N]', [0]).mean())}N")
    
    # Athlete Selection
    athlete = st.selectbox("Select Athlete", df["Player Name"].unique())
    p_data = df[df["Player Name"] == athlete].iloc[0]

    c1, c2, c3 = st.columns([1, 2, 2])
    with c1:
        img = p_data.get('PhotoURL', "https://www.w3schools.com/howto/img_avatar.png")
        st.markdown(f'<img src="{img}" class="player-photo-large">', unsafe_allow_html=True)
    
    with c2:
        st.subheader("Physical Metrics")
        st.write(f"**ASH Force:** {p_data.get('Peak Vertical Force [N]', 'N/A')} N")
        st.write(f"**CMJ Height:** {p_data.get('Jump Height (Imp-Mom) [cm]', 'N/A')} cm")
    
    with c3:
        st.subheader("Field Load")
        st.write(f"**Swing Load:** {p_data.get('Sum Swing Max Player Load', 'N/A')}")
        st.write(f"**Throw Count:** {p_data.get('Total Throw Count', 'N/A')}")

    st.divider()

    # Correlation Plot
    st.subheader("Performance Correlations")
    # Dynamically find numeric columns for the axes
    nums = df.select_dtypes(include=['number']).columns.tolist()
    if len(nums) >= 2:
        x_ax = st.selectbox("X-Axis", nums, index=0)
        y_ax = st.selectbox("Y-Axis", nums, index=min(len(nums)-1, 5))
        
        fig = px.scatter(df, x=x_ax, y=y_ax, color=df.get("Position", None), 
                         hover_name="Player Name", trendline="ols",
                         template="plotly_white", color_discrete_sequence=["#FF8200", "#4895DB"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Not enough numeric data to show correlations.")
