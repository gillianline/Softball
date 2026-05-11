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
    def password_entered():
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect Password")
        return False
    return True

if check_password():

    # --- DATA LOADING (The 'Nuclear Sanitizer' Logic) ---
    @st.cache_data(ttl=300)
    def load_all_data():
        def heavy_sanitize(frame):
            frame.columns = frame.columns.str.strip()
            # Force numeric conversion for performance stats
            for col in frame.columns:
                if any(word in col.lower() for word in ['force', 'rfd', 'height', 'load', 'count', 'power']):
                    frame[col] = pd.to_numeric(frame[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            return frame

        # Load from secrets
        roster = heavy_sanitize(pd.read_csv(st.secrets["ROSTER_URL"]))
        ash = heavy_sanitize(pd.read_csv(st.secrets["ASH_URL"]))
        cmj = heavy_sanitize(pd.read_csv(st.secrets["CMJ_URL"]))
        throws = heavy_sanitize(pd.read_csv(st.secrets["THROWS_URL"]))
        swings = heavy_sanitize(pd.read_csv(st.secrets["SWINGS_URL"]))

        # Merge sequence (Assumes 'Player Name' is the key in all sheets)
        master = roster.merge(ash, on="Player Name", how="left") \
                       .merge(cmj, on="Player Name", how="left") \
                       .merge(throws, on="Player Name", how="left") \
                       .merge(swings, on="Player Name", how="left")
        return master

    df = load_all_data()

    # --- DASHBOARD UI ---
    st.title("🥎 Softball Performance Analytics")

    # Sidebar Filters
    pos_filter = st.sidebar.multiselect("Position", options=df['Position'].unique(), default=df['Position'].unique())
    filtered_df = df[df['Position'].isin(pos_filter)]

    # Player Profile Section
    st.subheader("Player Profile")
    sel_player = st.selectbox("Select Athlete", filtered_df['Player Name'])
    player_data = filtered_df[filtered_df['Player Name'] == sel_player].iloc[0]

    p_col1, p_col2, p_col3 = st.columns([1, 2, 2])
    with p_col1:
        # Assumes your roster sheet has a PhotoURL column
        photo = player_data.get('PhotoURL', "https://www.w3schools.com/howto/img_avatar.png")
        st.markdown(f'<img src="{photo}" class="player-photo-large">', unsafe_allow_html=True)
    
    with p_col2:
        st.metric("ASH Peak Force", f"{player_data['Peak Vertical Force [N]']} N")
        st.metric("CMJ Jump Height", f"{player_data['Jump Height (Imp-Mom) [cm]']} cm")
    
    with p_col3:
        st.metric("Max Swing Load", player_data['Sum Swing Max Player Load'])
        st.metric("Total Throws", player_data['Total Throw Count'])

    st.divider()

    # Correlation Plot
    st.subheader("Performance Correlations")
    col_x = st.selectbox("Gym Metric (X-Axis)", ['Peak Vertical Force [N]', 'Peak Power [W]', 'Jump Height (Imp-Mom) [cm]'])
    col_y = st.selectbox("Field Metric (Y-Axis)", ['Sum Swing Max Player Load', 'Total Throw Count'])

    fig = px.scatter(filtered_df, x=col_x, y=col_y, color="Position", 
                     hover_name="Player Name", trendline="ols",
                     template="plotly_white", color_discrete_sequence=["#FF8200", "#4895DB"])
    st.plotly_chart(fig, use_container_width=True)

    # Admin View
    with st.expander("View Full Master Data"):
        st.dataframe(filtered_df)
