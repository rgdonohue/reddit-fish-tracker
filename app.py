import streamlit as st
import pandas as pd
import datetime
import os
import time
from data_processor import DataProcessor
from reddit_service import RedditService
from utils import get_timestamp, display_progress, save_to_csv

# Page configuration
st.set_page_config(
    page_title="Fishing Industry Reddit Monitor",
    page_icon="🎣",
    layout="wide"
)

# Initialize session state variables
if 'plants_data' not in st.session_state:
    st.session_state.plants_data = None
if 'vessels_data' not in st.session_state:
    st.session_state.vessels_data = None
if 'plants_results' not in st.session_state:
    st.session_state.plants_results = None
if 'vessels_results' not in st.session_state:
    st.session_state.vessels_results = None
if 'search_in_progress' not in st.session_state:
    st.session_state.search_in_progress = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'current_task' not in st.session_state:
    st.session_state.current_task = ""
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'total_steps' not in st.session_state:
    st.session_state.total_steps = 0
if 'completed_steps' not in st.session_state:
    st.session_state.completed_steps = 0

# Title and description
st.title("Fishing Industry Reddit Mention Monitor")
st.markdown("""
This application monitors Reddit for mentions of fishing industry entities:
1. Upload CSV files containing fish processing plants and commercial fishing vessels data
2. Extract keywords from these files (plant names, vessel names, owners)
3. Search specified subreddits for mentions of these keywords
4. Generate reports with the details of mentions
""")

# Main sections
tab1, tab2, tab3 = st.tabs(["Data Upload", "Reddit Search", "Results"])

# Data Upload Tab
with tab1:
    st.header("Upload CSV Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fish Processing Plants")
        plants_file = st.file_uploader("Upload Plants CSV", type="csv", key="plants_uploader")
        
        if plants_file is not None:
            try:
                plants_df = pd.read_csv(plants_file)
                st.success(f"Plants CSV loaded successfully: {plants_df.shape[0]} rows")
                st.session_state.plants_data = plants_df
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(plants_df.head())
                
                # Display columns
                st.subheader("Available Columns")
                st.write(", ".join(plants_df.columns.tolist()))
            except Exception as e:
                st.error(f"Error loading plants CSV: {str(e)}")
                st.session_state.plants_data = None
    
    with col2:
        st.subheader("Commercial Fishing Vessels")
        vessels_file = st.file_uploader("Upload Vessels CSV", type="csv", key="vessels_uploader")
        
        if vessels_file is not None:
            try:
                vessels_df = pd.read_csv(vessels_file)
                st.success(f"Vessels CSV loaded successfully: {vessels_df.shape[0]} rows")
                st.session_state.vessels_data = vessels_df
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(vessels_df.head())
                
                # Display columns
                st.subheader("Available Columns")
                st.write(", ".join(vessels_df.columns.tolist()))
            except Exception as e:
                st.error(f"Error loading vessels CSV: {str(e)}")
                st.session_state.vessels_data = None
    
    # Configuration section
    st.header("Configuration")
    
    plants_config_expander = st.expander("Plants Data Configuration")
    vessels_config_expander = st.expander("Vessels Data Configuration")
    
    with plants_config_expander:
        if st.session_state.plants_data is not None:
            columns = st.session_state.plants_data.columns.tolist()
            
            st.subheader("Select Keyword Columns")
            st.info("Select columns that contain names or identifiers to search for on Reddit")
            
            # Initialize session state values if not present
            if 'plants_name_col_value' not in st.session_state:
                st.session_state.plants_name_col_value = "name" if "name" in columns else columns[0]
            if 'plants_owner_col_value' not in st.session_state:
                st.session_state.plants_owner_col_value = "owner" if "owner" in columns else columns[0]
            
            # Use selectbox widgets (the widget itself updates session_state.plants_name_col)
            st.selectbox(
                "Plant Name Column", 
                options=columns,
                index=columns.index(st.session_state.plants_name_col_value) if st.session_state.plants_name_col_value in columns else 0,
                key="plants_name_col"
            )
            
            st.selectbox(
                "Plant Owner Column", 
                options=columns,
                index=columns.index(st.session_state.plants_owner_col_value) if st.session_state.plants_owner_col_value in columns else 0,
                key="plants_owner_col"
            )
            
            # Update our values from the widget state
            st.session_state.plants_name_col_value = st.session_state.plants_name_col
            st.session_state.plants_owner_col_value = st.session_state.plants_owner_col
        else:
            st.info("Please upload plants CSV data first")
    
    with vessels_config_expander:
        if st.session_state.vessels_data is not None:
            columns = st.session_state.vessels_data.columns.tolist()
            
            st.subheader("Select Keyword Columns")
            st.info("Select columns that contain names or identifiers to search for on Reddit")
            
            # Initialize session state values if not present
            if 'vessels_name_col_value' not in st.session_state:
                st.session_state.vessels_name_col_value = "name" if "name" in columns else columns[0]
            if 'vessels_owner_col_value' not in st.session_state:
                st.session_state.vessels_owner_col_value = "owner" if "owner" in columns else columns[0]
            
            # Use selectbox widgets (the widget itself updates session_state.vessels_name_col)
            st.selectbox(
                "Vessel Name Column", 
                options=columns,
                index=columns.index(st.session_state.vessels_name_col_value) if st.session_state.vessels_name_col_value in columns else 0,
                key="vessels_name_col"
            )
            
            st.selectbox(
                "Vessel Owner Column", 
                options=columns,
                index=columns.index(st.session_state.vessels_owner_col_value) if st.session_state.vessels_owner_col_value in columns else 0,
                key="vessels_owner_col"
            )
            
            # Update our values from the widget state
            st.session_state.vessels_name_col_value = st.session_state.vessels_name_col
            st.session_state.vessels_owner_col_value = st.session_state.vessels_owner_col
        else:
            st.info("Please upload vessels CSV data first")

# Reddit Search Tab
with tab2:
    st.header("Reddit Search Configuration")
    
    # Reddit API credentials
    st.subheader("Reddit API Credentials")
    
    reddit_client_id = st.text_input("Client ID", value=os.getenv("REDDIT_CLIENT_ID", ""), type="password")
    reddit_client_secret = st.text_input("Client Secret", value=os.getenv("REDDIT_CLIENT_SECRET", ""), type="password")
    reddit_user_agent = st.text_input("User Agent", value=os.getenv("REDDIT_USER_AGENT", f"FishingMentionTracker/1.0 (by u/fishingmonitor)"))
    
    # Subreddit selection
    st.subheader("Subreddits to Search")
    
    default_subreddits = [
        "Fishing", "CommercialFishing", "OceanFishing", "Seafood", 
        "MarineBiology", "MarineConservation", "Maritime", 
        "EnvironmentalScience", "WorldNews", "News"
    ]
    
    subreddits_input = st.text_area(
        "Enter subreddits to search (one per line)",
        value="\n".join(default_subreddits)
    )
    subreddits = [sub.strip() for sub in subreddits_input.split("\n") if sub.strip()]
    
    # Search parameters
    st.subheader("Search Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_limit = st.number_input("Maximum posts to search per subreddit", min_value=10, max_value=1000, value=100)
        time_filter = st.selectbox(
            "Time filter", 
            options=["all", "day", "week", "month", "year"],
            index=3  # Default to "month"
        )
    
    with col2:
        include_comments = st.checkbox("Include comment search", value=True)
        comments_limit = st.number_input("Maximum comments to search per post", min_value=10, max_value=500, value=100, disabled=not include_comments)
    
    # Search button
    search_button = st.button("Start Reddit Search", disabled=st.session_state.search_in_progress)
    
    # Progress indicators
    if st.session_state.search_in_progress:
        st.subheader("Search Progress")
        progress_bar = st.progress(0)
        status_container = st.container()
        
        # Update progress display
        progress_bar.progress(st.session_state.progress)
        
        # Calculate time metrics if available
        elapsed_time = None
        remaining_time = None
        total_steps_completed = 0
        
        if st.session_state.start_time is not None:
            elapsed_time = time.time() - st.session_state.start_time
            
            if st.session_state.progress > 0:
                total_time_estimate = elapsed_time / st.session_state.progress
                remaining_time = total_time_estimate - elapsed_time
        
        with status_container:
            st.markdown(f"**Current task:** {st.session_state.current_task}")
            
            # Only show these metrics if we have timing data
            if elapsed_time is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Elapsed time:** {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
                
                with col2:
                    if remaining_time is not None and remaining_time > 0:
                        st.markdown(f"**Estimated time left:** {time.strftime('%H:%M:%S', time.gmtime(remaining_time))}")
            
            if st.session_state.completed_steps > 0 and st.session_state.total_steps > 0:
                st.markdown(f"**Progress:** {st.session_state.completed_steps} of {st.session_state.total_steps} steps completed")
    
    # Handle search button click
    if search_button:
        # Validate inputs
        if not reddit_client_id or not reddit_client_secret:
            st.error("Reddit API credentials are required")
        elif not subreddits:
            st.error("At least one subreddit must be specified")
        elif st.session_state.plants_data is None and st.session_state.vessels_data is None:
            st.error("You must upload at least one CSV file")
        else:
            with st.spinner("Processing data and searching Reddit..."):
                st.session_state.search_in_progress = True
                
                # Initialize services
                data_processor = DataProcessor()
                reddit_service = RedditService(
                    client_id=reddit_client_id,
                    client_secret=reddit_client_secret,
                    user_agent=reddit_user_agent
                )
                
                # Process keywords
                plants_keywords = []
                vessels_keywords = []
                
                if st.session_state.plants_data is not None:
                    plants_keywords = data_processor.extract_keywords(
                        st.session_state.plants_data,
                        name_col=st.session_state.plants_name_col_value,
                        owner_col=st.session_state.plants_owner_col_value
                    )
                
                if st.session_state.vessels_data is not None:
                    vessels_keywords = data_processor.extract_keywords(
                        st.session_state.vessels_data,
                        name_col=st.session_state.vessels_name_col_value,
                        owner_col=st.session_state.vessels_owner_col_value
                    )
                
                # Set progress display and initialize timing metrics
                st.session_state.progress = 0
                st.session_state.current_task = "Connecting to Reddit API..."
                st.session_state.start_time = time.time()
                
                # Calculate total steps for progress tracking
                total_subreddits = len(subreddits)
                total_plant_keywords = len(plants_keywords) if plants_keywords else 0
                total_vessel_keywords = len(vessels_keywords) if vessels_keywords else 0
                
                # Total steps = (subreddits × plant keywords) + (subreddits × vessel keywords)
                st.session_state.total_steps = (total_subreddits * total_plant_keywords) + (total_subreddits * total_vessel_keywords)
                st.session_state.completed_steps = 0
                
                # Progress updates for display
                def progress_update_callback(progress, task_description):
                    st.session_state.progress = progress
                    st.session_state.current_task = task_description
                    
                    # Update step counter based on progress percentage
                    if st.session_state.total_steps > 0:
                        st.session_state.completed_steps = int(progress * st.session_state.total_steps)
                    
                    time.sleep(0.1)  # Small delay to allow UI to update
                
                # Perform search
                plants_results = []
                vessels_results = []
                
                try:
                    # Search for plants mentions
                    if plants_keywords:
                        plants_results = reddit_service.search_reddit(
                            keywords=plants_keywords,
                            subreddits=subreddits,
                            limit=search_limit,
                            time_filter=time_filter,
                            include_comments=include_comments,
                            comments_limit=comments_limit,
                            entity_type="plant",
                            progress_callback=progress_update_callback
                        )
                        
                    # Search for vessels mentions
                    if vessels_keywords:
                        vessels_results = reddit_service.search_reddit(
                            keywords=vessels_keywords,
                            subreddits=subreddits,
                            limit=search_limit,
                            time_filter=time_filter,
                            include_comments=include_comments,
                            comments_limit=comments_limit,
                            entity_type="vessel",
                            progress_callback=progress_update_callback
                        )
                    
                    # Store results in session state
                    st.session_state.plants_results = plants_results
                    st.session_state.vessels_results = vessels_results
                    
                    # Display results count
                    st.success(f"Search completed! Found {len(plants_results)} plant mentions and {len(vessels_results)} vessel mentions.")
                    
                    # Automatically switch to results tab
                    time.sleep(1)
                    # Reset search-related session state
                    st.session_state.search_in_progress = False
                    st.session_state.progress = 0
                    st.session_state.current_task = ""
                    st.session_state.start_time = None
                    st.session_state.total_steps = 0
                    st.session_state.completed_steps = 0
                    
                    # Switch to Results tab
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Error during Reddit search: {str(e)}")
                    # Reset search-related session state
                    st.session_state.search_in_progress = False
                    st.session_state.progress = 0
                    st.session_state.current_task = ""
                    st.session_state.start_time = None
                    st.session_state.total_steps = 0
                    st.session_state.completed_steps = 0

# Results Tab
with tab3:
    st.header("Search Results")
    
    # Check if results exist
    if st.session_state.plants_results is None and st.session_state.vessels_results is None:
        st.info("No search results yet. Please go to the Reddit Search tab to start a search.")
    else:
        # Results tabs for plants and vessels
        results_tab1, results_tab2 = st.tabs(["Plants Results", "Vessels Results"])
        
        # Plants Results Tab
        with results_tab1:
            if st.session_state.plants_results:
                st.subheader(f"Found {len(st.session_state.plants_results)} mentions of plants")
                
                # Convert results to DataFrame for display
                plants_df = pd.DataFrame(st.session_state.plants_results)
                
                # Display results table
                st.dataframe(plants_df)
                
                # Download button
                csv_filename = f"plants_reddit_mentions_{get_timestamp()}.csv"
                
                if st.download_button(
                    label="Download Plants Results as CSV",
                    data=plants_df.to_csv(index=False),
                    file_name=csv_filename,
                    mime="text/csv"
                ):
                    st.success(f"Downloaded {csv_filename}")
                
                # Detailed view of mentions
                st.subheader("Detailed View")
                
                for i, mention in enumerate(st.session_state.plants_results):
                    with st.expander(f"{mention['keyword']} - {mention['title']}"):
                        st.markdown(f"**Keyword:** {mention['keyword']}")
                        st.markdown(f"**Post/Comment ID:** {mention['id']}")
                        st.markdown(f"**Title/Context:** {mention['title']}")
                        st.markdown(f"**Author:** {mention['author']}")
                        st.markdown(f"**Date/Time:** {mention['datetime']}")
                        st.markdown(f"**Subreddit:** r/{mention['subreddit']}")
                        st.markdown(f"**Permalink:** [Link to post](https://www.reddit.com{mention['permalink']})")
                        st.markdown("**Snippet:**")
                        st.markdown(f"> {mention['snippet']}")
                        
                        # Source label (post or comment)
                        st.markdown(f"**Source:** {mention['source']}")
            else:
                st.info("No plants mentions found in the search results.")
        
        # Vessels Results Tab
        with results_tab2:
            if st.session_state.vessels_results:
                st.subheader(f"Found {len(st.session_state.vessels_results)} mentions of vessels")
                
                # Convert results to DataFrame for display
                vessels_df = pd.DataFrame(st.session_state.vessels_results)
                
                # Display results table
                st.dataframe(vessels_df)
                
                # Download button
                csv_filename = f"vessels_reddit_mentions_{get_timestamp()}.csv"
                
                if st.download_button(
                    label="Download Vessels Results as CSV",
                    data=vessels_df.to_csv(index=False),
                    file_name=csv_filename,
                    mime="text/csv"
                ):
                    st.success(f"Downloaded {csv_filename}")
                
                # Detailed view of mentions
                st.subheader("Detailed View")
                
                for i, mention in enumerate(st.session_state.vessels_results):
                    with st.expander(f"{mention['keyword']} - {mention['title']}"):
                        st.markdown(f"**Keyword:** {mention['keyword']}")
                        st.markdown(f"**Post/Comment ID:** {mention['id']}")
                        st.markdown(f"**Title/Context:** {mention['title']}")
                        st.markdown(f"**Author:** {mention['author']}")
                        st.markdown(f"**Date/Time:** {mention['datetime']}")
                        st.markdown(f"**Subreddit:** r/{mention['subreddit']}")
                        st.markdown(f"**Permalink:** [Link to post](https://www.reddit.com{mention['permalink']})")
                        st.markdown("**Snippet:**")
                        st.markdown(f"> {mention['snippet']}")
                        
                        # Source label (post or comment)
                        st.markdown(f"**Source:** {mention['source']}")
            else:
                st.info("No vessels mentions found in the search results.")

# About section in sidebar
with st.sidebar:
    st.title("About")
    st.markdown("""
    **Fishing Industry Reddit Monitor**
    
    This application helps monitor Reddit for mentions of fishing industry entities 
    by searching for keywords extracted from CSV data about fish processing plants 
    and commercial fishing vessels.
    
    ### How it works:
    1. Upload CSV files with plant and vessel data
    2. Configure search parameters
    3. Search Reddit for mentions
    4. View and download results
    
    ### Tips:
    - Higher search limits may take longer but find more results
    - Reddit API has rate limits, so very large searches may be throttled
    - For best results, use specific and unique names as keywords
    """)
