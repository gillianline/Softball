import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance", layout="wide")

# --- 1. CRITICAL: CHECK SECRETS FIRST ---
# This prevents the app from crashing silently if a key is missing
if "PASSWORD" not in st.secrets:
    st.error("Missing 'PASSWORD' in Streamlit Secrets.")
    st.stop()

# --- 2. AUTHENTICATION ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🥎 Softball Analytics Login")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == st.secrets["PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid Password")
    st.stop()

# --- 3. DATA LOADING ---
@st.cache_data(ttl=600)
def load_data():
    try:
        # We use a simple pandas read here to ensure the connection is stable
        # Make sure your secret names match these EXACTLY
        r = pd.read_csv(st.secrets["ROSTER_URL"])
        a = pd.read_csv(st.secrets["ASH_URL"])
        
        # Simple Merge to test stability
        df = pd.merge(r, a, on="Player Name", how="left")
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

# If we get here, the user is authenticated
st.title("🥎 Dashboard Active")
data = load_data()

if not data.empty:
    st.write("### Data Preview")
    st.dataframe(data.head())
else:
    st.warning("Data loaded but appears empty. Check your Google Sheet URLs.")
