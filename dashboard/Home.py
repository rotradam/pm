
import streamlit as st
from dashboard.utils.ui import load_css

st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()

# Header
st.title("🚀 Portfolio Management Dashboard")
st.markdown("""
Welcome to the advanced portfolio management system. Select a module below to get started.
""")

st.markdown("---")

# Navigation Cards
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True, height=400):
        st.markdown("### 📈 Strategy Analysis")
        st.markdown("""
        Deep dive into individual strategy performance.
        
        *   Analyze Equity Curves
        *   View Historical Weights
        *   Check Risk Metrics
        """)
        st.markdown("<br>" * 2, unsafe_allow_html=True) # Spacer
        if st.button("Go to Analysis", type="primary", use_container_width=True):
            st.switch_page("pages/2_Strategy_Analysis.py")

with col2:
    with st.container(border=True, height=400):
        st.markdown("### ⚖️ Comparison")
        st.markdown("""
        Compare multiple strategies side-by-side.
        
        *   Benchmark vs. Active
        *   Risk/Return Scatter
        *   Detailed Metrics Table
        """)
        st.markdown("<br>" * 2, unsafe_allow_html=True) # Spacer
        if st.button("Go to Comparison", type="primary", use_container_width=True):
            st.switch_page("pages/3_Comparison.py")

with col3:
    with st.container(border=True, height=400):
        st.markdown("### 💾 Data Management")
        st.markdown("""
        Manage your market data universe.
        
        *   Update Price Data
        *   Check Data Quality
        *   Manage Tickers
        """)
        st.markdown("<br>" * 2, unsafe_allow_html=True) # Spacer
        if st.button("Go to Data", type="primary", use_container_width=True):
            st.switch_page("pages/4_Data_Management.py")

# Quick Stats or Info
st.markdown("---")
st.markdown("### 💡 Quick Tips")
col_a, col_b = st.columns(2)
with col_a:
    st.info("**Tip:** Use the 'Comparison' tab to find the best performing strategy for the current market regime.")
with col_b:
    st.info("**Tip:** Ensure your data is up-to-date in 'Data Management' before running live trading simulations.")
