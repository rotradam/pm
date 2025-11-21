import streamlit as st
import pandas as pd
from dashboard.utils.ui import load_css
from backend.data.categories import CATEGORIES
from backend.data.prices import PriceFetcher
from backend.data.universe import Universe

# Initialize Session State
if "selected_tickers" not in st.session_state:
    st.session_state["selected_tickers"] = []

if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""

st.set_page_config(
    page_title="Portfolio Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()

def add_ticker():
    """Callback to add ticker from input."""
    ticker = st.session_state.search_input.strip().upper()
    if ticker:
        # Basic validation or check if already exists
        if ticker not in st.session_state["selected_tickers"]:
            # Optional: Validate with PriceFetcher here if we want strict checking
            # fetcher = PriceFetcher()
            # if fetcher.check_ticker_availability(ticker):
            st.session_state["selected_tickers"].append(ticker)
            # else:
            #     st.toast(f"⚠️ Could not find data for {ticker}", icon="⚠️")
        else:
            st.toast(f"{ticker} is already in your portfolio", icon="ℹ️")
    st.session_state.search_input = "" # Clear input

def remove_ticker(ticker):
    """Remove ticker from list."""
    if ticker in st.session_state["selected_tickers"]:
        st.session_state["selected_tickers"].remove(ticker)

def add_category(category_name):
    """Add all tickers from a category."""
    tickers = CATEGORIES.get(category_name, [])
    added_count = 0
    for t in tickers:
        if t not in st.session_state["selected_tickers"]:
            st.session_state["selected_tickers"].append(t)
            added_count += 1
    if added_count > 0:
        st.toast(f"Added {added_count} assets from {category_name}", icon="✅")

# --- UI ---

st.title("🚀 Build Your Universe")
st.markdown("### Search, Select, and Analyze.")

# 1. Search Bar
col_search, col_btn = st.columns([4, 1])
with col_search:
    st.text_input(
        "Search Ticker", 
        placeholder="Type a ticker (e.g., AAPL, BTC-USD) and press Enter...",
        key="search_input",
        on_change=add_ticker,
        label_visibility="collapsed"
    )

# 2. Categories
with st.expander("📚 Browse Categories"):
    cat_cols = st.columns(4)
    categories = list(CATEGORIES.keys())
    
    for i, category in enumerate(categories):
        col_idx = i % 4
        with cat_cols[col_idx]:
            if st.button(category, use_container_width=True):
                add_category(category)

st.markdown("---")

# 3. Selected Assets (The "Bag")
st.subheader(f"🎒 Your Portfolio ({len(st.session_state['selected_tickers'])})")

if not st.session_state["selected_tickers"]:
    st.info("Your portfolio is empty. Start by adding assets above!")
else:
    # Display as chips/tags
    # Since Streamlit doesn't have native deletable chips, we'll use columns
    
    # Group into rows of 6
    cols_per_row = 6
    tickers = st.session_state["selected_tickers"]
    
    for i in range(0, len(tickers), cols_per_row):
        row_tickers = tickers[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for j, ticker in enumerate(row_tickers):
            with cols[j]:
                st.button(
                    f"❌ {ticker}", 
                    key=f"remove_{ticker}", 
                    on_click=remove_ticker, 
                    args=(ticker,),
                    help="Click to remove",
                    use_container_width=True
                )

st.markdown("---")

# 4. Actions
col_act1, col_act2 = st.columns(2)

with col_act1:
    if st.button("📈 Analyze Strategy", type="primary", use_container_width=True, disabled=len(st.session_state["selected_tickers"]) == 0):
        # We need to ensure the backend knows about these tickers.
        # We'll pass them via session state, but the pages need to handle them.
        # Also, we might want to trigger a data download here if missing?
        st.switch_page("pages/2_Strategy_Analysis.py")

with col_act2:
    if st.button("⚖️ Compare Strategies", type="primary", use_container_width=True, disabled=len(st.session_state["selected_tickers"]) == 0):
        st.switch_page("pages/3_Comparison.py")
