import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball ASH Analysis", layout="wide")

# --- VOLLEYBALL STYLE CSS ---
st.markdown("""
    <style>
    th, td {text-align: center !important;}
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    .scout-table th { background-color: #4895DB; color: white; padding: 4px; border-bottom: 2px solid #FF8200; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD GATE ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    pwd = st.sidebar.text_input("Access Key", type="password")
    if st.sidebar.button("Unlock"):
        if pwd == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect Password")
    st.stop()

# --- DATA LOADING (Single Sheet) ---
@st.cache_data(ttl=300)
def load_ash_only():
    try:
        df = pd.read_csv(st.secrets["ASH_URL"])
        df.columns = df.columns.str.strip()
        
        # Clean numeric columns (Mango Type 1 logic)
        for col in df.columns:
            if any(w in col.lower() for w in ['force', 'rfd', 'time', 'asym']):
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading ASH sheet: {e}")
        return pd.DataFrame()

df = load_ash_only()

# --- DASHBOARD UI ---
if not df.empty:
    st.title("🥎 ASH Test Analysis")
    
    # 1. Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tests", len(df))
    col2.metric("Avg Peak Force", f"{int(df['Peak Vertical Force [N]'].mean())} N")
    col3.metric("Avg RFD (200ms)", f"{int(df['RFD - 200ms [N/s]'].mean())} N/s")

    # 2. Athlete Selection
    athlete = st.selectbox("Select Athlete", df['Player Name'].unique())
    p_data = df[df['Player Name'] == athlete]

    # 3. Trends over time
    st.subheader(f"Performance History: {athlete}")
    # Assumes your ASH sheet has a 'Date' column
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        fig_trend = px.line(p_data.sort_values('Date'), x='Date', y='Peak Vertical Force [N]', 
                            markers=True, template="plotly_white", color_discrete_sequence=["#FF8200"])
        st.plotly_chart(fig_trend, use_container_width=True)

    # 4. Raw Data Inspection
    with st.expander("View Full ASH Dataset"):
        st.dataframe(df)
else:
    st.warning("Sheet is empty or link is incorrect.")
