import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance", layout="wide")

# --- CSS: FORMATTING (Matches your VB style) ---
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
                if pwd == st.secrets["PASSWORD"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Incorrect Password")
        return False
    return True

if check_password():

    @st.cache_data(ttl=300)
    def load_all_data():
        def heavy_sanitize(frame, sheet_name):
            # Strip whitespace from headers
            frame.columns = frame.columns.str.strip()
            
            # Find the Name column
            name_col = None
            possible_names = ['Player Name', 'Name', 'Athlete', 'Player']
            for col in frame.columns:
                if col in possible_names or col.lower() in [p.lower() for p in possible_names]:
                    name_col = col
                    break
            
            if name_col:
                frame.rename(columns={name_col: "Player Name"}, inplace=True)
                # Clean up the names themselves
                frame["Player Name"] = frame["Player Name"].astype(str).str.strip()
            else:
                st.error(f"Missing Name column in {sheet_name} sheet.")
                st.stop()

            # Clean numeric data
            for col in frame.columns:
                if any(word in col.lower() for word in ['force', 'rfd', 'height', 'load', 'count', 'power']):
                    frame[col] = pd.to_numeric(frame[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            return frame

        try:
            # 1. Fetch
            roster = heavy_sanitize(pd.read_csv(st.secrets["ROSTER_URL"]), "Roster")
            ash    = heavy_sanitize(pd.read_csv(st.secrets["ASH_URL"]), "ASH")
            cmj    = heavy_sanitize(pd.read_csv(st.secrets["CMJ_URL"]), "CMJ")
            throws = heavy_sanitize(pd.read_csv(st.secrets["THROWS_URL"]), "Throws")
            swings = heavy_sanitize(pd.read_csv(st.secrets["SWINGS_URL"]), "Swings")

            # 2. Merge - Inner merge on roster first to establish our list
            master = roster.merge(ash, on="Player Name", how="left")
            master = master.merge(cmj, on="Player Name", how="left")
            master = master.merge(throws, on="Player Name", how="left")
            master = master.merge(swings, on="Player Name", how="left")
            
            return master
        except Exception as e:
            st.error(f"Data Load Error: {e}")
            st.stop()

    df = load_all_data()

    # --- DASHBOARD UI ---
    st.title("🥎 Softball Performance Analytics")

    # Sidebar
    st.sidebar.header("Filters")
    pos_list = df['Position'].unique().tolist() if 'Position' in df.columns else ["N/A"]
    pos_filter = st.sidebar.multiselect("Position", options=pos_list, default=pos_list)
    
    filtered_df = df[df['Position'].isin(pos_filter)] if 'Position' in df.columns else df

    # Profiles
    sel_player = st.selectbox("Select Athlete", filtered_df['Player Name'].unique())
    p_data = filtered_df[filtered_df['Player Name'] == sel_player].iloc[0]

    c1, c2, c3 = st.columns([1, 2, 2])
    with c1:
        img = p_data.get('PhotoURL', "https://www.w3schools.com/howto/img_avatar.png")
        st.markdown(f'<img src="{img}" class="player-photo-large">', unsafe_allow_html=True)
    
    with c2:
        # Using .get() prevents crash if column name is slightly different
        st.metric("ASH Peak Force", f"{p_data.get('Peak Vertical Force [N]', 0)} N")
        st.metric("CMJ Jump Height", f"{p_data.get('Jump Height (Imp-Mom) [cm]', 0)} cm")
    
    with c3:
        st.metric("Max Swing Load", p_data.get('Sum Swing Max Player Load', 0))
        st.metric("Total Throws", p_data.get('Total Throw Count', 0))

    st.divider()

    # Scatter Plot
    st.subheader("Performance Correlations")
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    col_x = st.selectbox("X-Axis", options=numeric_cols, index=0)
    col_y = st.selectbox("Y-Axis", options=numeric_cols, index=min(len(numeric_cols)-1, 5))

    fig = px.scatter(filtered_df, x=col_x, y=col_y, color="Position", 
                     hover_name="Player Name", trendline="ols",
                     template="plotly_white", color_discrete_sequence=["#FF8200", "#4895DB"])
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Admin: Raw Master Data"):
        st.write(df)
