import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.data.prices import PriceFetcher
from dashboard.utils.ui import load_css

st.set_page_config(page_title="Data Management", page_icon="💾", layout="wide")
load_css()

st.title("💾 Data Management")

fetcher = PriceFetcher()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="stCard">
        <h3>Data Status</h3>
        <p>Manage your local data cache. Regular updates ensure your backtests use the latest market data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load current data stats
    try:
        # This is a bit of a hack to get stats without loading everything
        # In a real app, we'd have a metadata file
        # Find the latest prices file
        processed_dir = Path("data/processed")
        price_files = list(processed_dir.glob("prices_*.parquet"))
        
        if price_files:
            # Sort by modification time, newest first
            latest_file = sorted(price_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            df = pd.read_parquet(latest_file)
            st.metric("Total Assets", len(df.columns))
            st.metric("Date Range", f"{df.index.min().date()} to {df.index.max().date()}")
            st.metric("Total Days", len(df))
            st.caption(f"Source: {latest_file.name}")
        else:
            st.warning("No processed data found.")
    except Exception as e:
        st.error(f"Error reading data: {e}")

with col2:
    st.markdown("### Actions")
    if st.button("🔄 Update Data Now (Force Refresh)", type="primary", use_container_width=True):
        with st.status("Updating data...", expanded=True) as status:
            st.write("Triggering download script with force refresh...")
            # We need to modify the update_data method to accept arguments or change the script call
            # For now, we'll assume update_data runs the script which defaults to checking cache
            # To force, we should pass --force to the script.
            # Let's update the PriceFetcher.update_data method first.
            success, output = fetcher.update_data(force=True)
            
            if success:
                status.update(label="Update Complete!", state="complete", expanded=False)
                st.success("Data updated successfully!")
                st.code(output[-500:]) # Show last 500 chars of log
            else:
                status.update(label="Update Failed", state="error")
                st.error("Data update failed.")
                st.error(output)

st.markdown("### Data Quality")
if 'df' in locals():
    completeness = df.notna().sum() / len(df) * 100
    quality_df = pd.DataFrame({
        'Ticker': completeness.index,
        'Completeness (%)': completeness.values
    }).sort_values('Completeness (%)', ascending=False)
    
    st.dataframe(
        quality_df,
        column_config={
            "Completeness (%)": st.column_config.ProgressColumn(
                "Completeness",
                help="Percentage of non-missing values",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True
    )
