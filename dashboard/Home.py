import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.data.universe import Universe
from backend.data.prices import PriceFetcher
from backend.data.database import AssetDatabase

# Initialize Session State
if "selected_tickers" not in st.session_state:
    st.session_state["selected_tickers"] = []

if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""

@st.cache_resource
def load_resources():
    universe = Universe()
    price_fetcher = PriceFetcher()
    db = AssetDatabase()
    return universe, price_fetcher, db

universe, price_fetcher, db = load_resources()

st.set_page_config(
    page_title="Portfolio Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


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
    categories = db.get_categories()
    
    # Group by main category
    main_cats = list(categories.keys())
    selected_cat = st.selectbox("Select Category", main_cats)
    
    if selected_cat:
        subcats = categories[selected_cat]
        if subcats:
            selected_sub = st.selectbox("Select Subcategory", ["All"] + subcats)
            
            if selected_sub == "All":
                assets = db.get_assets_by_category(selected_cat)
            else:
                assets = db.get_assets_by_category(selected_cat, selected_sub)
        else:
            assets = db.get_assets_by_category(selected_cat)
            
        st.write(f"Found {len(assets)} assets in {selected_cat}")
        
        # Display as multiselect for easy adding
        selected_in_cat = st.multiselect(
            "Select Assets to Add",
            options=assets['ticker'].tolist(),
            format_func=lambda x: f"{x} - {assets[assets['ticker']==x]['name'].iloc[0]}"
        )
        
        if st.button("Add Selected Assets"):
            count = 0
            for t in selected_in_cat:
                if t not in st.session_state["selected_tickers"]:
                    st.session_state["selected_tickers"].append(t)
                    count += 1
            if count > 0:
                st.success(f"Added {count} assets!")
                st.rerun()

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

# New DB Search Bar and Results
query = st.text_input("🔍 Search for assets (stocks, crypto, ETFs...)", placeholder="Type 'AAPL', 'Bitcoin', or 'Gold'...")

if query:
    # Search using DB
    results = db.search_assets(query, limit=10)
    
    if not results.empty:
        st.subheader("Search Results")
        for _, row in results.iterrows():
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.markdown(f"**{row['ticker']}**")
            with col2:
                st.write(f"{row['name']} ({row['category']})")
            with col3:
                if st.button("Add", key=f"add_{row['ticker']}"):
                    if row['ticker'] not in st.session_state["selected_tickers"]:
                        st.session_state["selected_tickers"].append(row['ticker'])
                        st.rerun()
    else:
        st.info("No matching assets found.")

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

