import streamlit as st
import pandas as pd
import datetime
import os
import time
# from dotenv import load_dotenv
from data_processor import DataProcessor
from reddit_service import RedditService
from utils import get_timestamp, display_progress, save_to_csv
from web_scraper import get_website_text_content

# Load environment variables
# try:
#     load_dotenv()
# except:
#     pass  # Ignore if .env file is not found, we'll use streamlit secrets instead

# Initialize services
data_processor = DataProcessor()

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
    st.session_state.plants_results = []
if 'vessels_results' not in st.session_state:
    st.session_state.vessels_results = []
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
if 'search_log' not in st.session_state:
    st.session_state.search_log = []
if 'reddit_client_id' not in st.session_state:
    st.session_state.reddit_client_id = st.secrets.get("REDDIT_CLIENT_ID") or os.getenv('REDDIT_CLIENT_ID', '')
if 'reddit_client_secret' not in st.session_state:
    st.session_state.reddit_client_secret = st.secrets.get("REDDIT_CLIENT_SECRET") or os.getenv('REDDIT_CLIENT_SECRET', '')
if 'reddit_user_agent' not in st.session_state:
    st.session_state.reddit_user_agent = st.secrets.get("REDDIT_USER_AGENT") or os.getenv('REDDIT_USER_AGENT', '')
if 'subreddits' not in st.session_state:
    st.session_state.subreddits = []
if 'search_limit' not in st.session_state:
    st.session_state.search_limit = 100
if 'time_filter' not in st.session_state:
    st.session_state.time_filter = "month"
if 'test_mode' not in st.session_state:
    st.session_state.test_mode = False
if 'default_files_loaded' not in st.session_state:
    st.session_state.default_files_loaded = False

# Load default CSV files if not already loaded
if not st.session_state.default_files_loaded:
    try:
        # Load plants data
        plants_df = pd.read_csv("data/Plants.csv")
        st.session_state.plants_data = plants_df
        st.session_state.plants_name_col_value = "Company name"
        st.session_state.plants_owner_col_value = "Company name"  # Using same column for both since only one is specified
        
        # Load vessels data
        vessels_df = pd.read_csv("data/Ships.csv")
        st.session_state.vessels_data = vessels_df
        st.session_state.vessels_name_col_value = "Vessel Name"
        st.session_state.vessels_owner_col_value = "Owner Name"
        
        st.session_state.default_files_loaded = True
    except Exception as e:
        st.error(f"Error loading default CSV files: {str(e)}")

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
        if st.session_state.plants_data is not None:
            st.success(f"Plants CSV loaded: {st.session_state.plants_data.shape[0]} rows")
            st.info("Using default Plants.csv file")
            
            # Display preview
            st.subheader("Preview")
            st.dataframe(st.session_state.plants_data.head())
            
            # Display columns
            st.subheader("Available Columns")
            st.write(", ".join(st.session_state.plants_data.columns.tolist()))
        
        # Allow uploading a different file
        plants_file = st.file_uploader("Upload Different Plants CSV", type="csv", key="plants_uploader")
        if plants_file is not None:
            try:
                plants_df = pd.read_csv(plants_file)
                st.success(f"New Plants CSV loaded successfully: {plants_df.shape[0]} rows")
                st.session_state.plants_data = plants_df
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(plants_df.head())
                
                # Display columns
                st.subheader("Available Columns")
                st.write(", ".join(plants_df.columns.tolist()))
            except Exception as e:
                st.error(f"Error loading plants CSV: {str(e)}")
    
    with col2:
        st.subheader("Commercial Fishing Vessels")
        if st.session_state.vessels_data is not None:
            st.success(f"Vessels CSV loaded: {st.session_state.vessels_data.shape[0]} rows")
            st.info("Using default Ships.csv file")
            
            # Display preview
            st.subheader("Preview")
            st.dataframe(st.session_state.vessels_data.head())
            
            # Display columns
            st.subheader("Available Columns")
            st.write(", ".join(st.session_state.vessels_data.columns.tolist()))
        
        # Allow uploading a different file
        vessels_file = st.file_uploader("Upload Different Vessels CSV", type="csv", key="vessels_uploader")
        if vessels_file is not None:
            try:
                vessels_df = pd.read_csv(vessels_file)
                st.success(f"New Vessels CSV loaded successfully: {vessels_df.shape[0]} rows")
                st.session_state.vessels_data = vessels_df
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(vessels_df.head())
                
                # Display columns
                st.subheader("Available Columns")
                st.write(", ".join(vessels_df.columns.tolist()))
            except Exception as e:
                st.error(f"Error loading vessels CSV: {str(e)}")
    
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
    
    # Test mode toggle
    st.subheader("Test Mode")
    test_mode = st.checkbox("Enable test mode (select specific keywords)", value=False)
    
    if test_mode:
        st.info("Test mode allows you to select specific keywords to search for")
        
        # Plants keyword selection
        if st.session_state.plants_data is not None:
            plants_keywords = data_processor.extract_keywords(
                st.session_state.plants_data,
                name_col=st.session_state.plants_name_col_value,
                owner_col=st.session_state.plants_owner_col_value
            )
            st.subheader("Select Plant Keywords")
            selected_plant_keywords = st.multiselect(
                "Choose plant keywords to search for",
                options=plants_keywords,
                default=plants_keywords[:5] if len(plants_keywords) > 5 else plants_keywords,
                help="Select specific plant keywords to search for. In test mode, only these keywords will be used."
            )
            st.info(f"Selected {len(selected_plant_keywords)} plant keywords")
        
        # Vessels keyword selection
        if st.session_state.vessels_data is not None:
            vessels_keywords = data_processor.extract_keywords(
                st.session_state.vessels_data,
                name_col=st.session_state.vessels_name_col_value,
                owner_col=st.session_state.vessels_owner_col_value
            )
            st.subheader("Select Vessel Keywords")
            selected_vessel_keywords = st.multiselect(
                "Choose vessel keywords to search for",
                options=vessels_keywords,
                default=vessels_keywords[:5] if len(vessels_keywords) > 5 else vessels_keywords,
                help="Select specific vessel keywords to search for. In test mode, only these keywords will be used."
            )
            st.info(f"Selected {len(selected_vessel_keywords)} vessel keywords")
    
    # Reddit API credentials
    st.subheader("Reddit API Credentials")
    
    reddit_client_id = st.text_input("Client ID", value=st.session_state.reddit_client_id, type="password")
    reddit_client_secret = st.text_input("Client Secret", value=st.session_state.reddit_client_secret, type="password")
    reddit_user_agent = st.text_input("User Agent", value=st.session_state.reddit_user_agent)
    
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
        
        # Create a progress bar that updates with the progress value
        progress_bar = st.progress(st.session_state.progress)
        
        # Create a container for status updates
        status_container = st.container()
        
        with status_container:
            # Show the current task description
            st.markdown(f"**Current task:** {st.session_state.current_task}")
            
            # Calculate and display time metrics
            if st.session_state.start_time is not None:
                elapsed_time = time.time() - st.session_state.start_time
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Elapsed time:** {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
                
                with col2:
                    if st.session_state.progress > 0:
                        # Estimate remaining time based on progress so far
                        total_time_estimate = elapsed_time / st.session_state.progress
                        remaining_time = total_time_estimate - elapsed_time
                        if remaining_time > 0:
                            st.markdown(f"**Estimated time left:** {time.strftime('%H:%M:%S', time.gmtime(remaining_time))}")
            
            # Show step counting progress if available
            if st.session_state.completed_steps > 0 and st.session_state.total_steps > 0:
                st.markdown(f"**Progress:** {st.session_state.completed_steps} of {st.session_state.total_steps} steps completed")
    
    # Setup for searching
    if 'do_search' not in st.session_state:
        st.session_state.do_search = False
    
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
            # Store search parameters in session state
            st.session_state.reddit_client_id = reddit_client_id
            st.session_state.reddit_client_secret = reddit_client_secret
            st.session_state.reddit_user_agent = reddit_user_agent
            st.session_state.subreddits = subreddits
            st.session_state.search_limit = search_limit
            st.session_state.time_filter = time_filter
            st.session_state.include_comments = include_comments
            st.session_state.comments_limit = comments_limit
            st.session_state.test_mode = test_mode
            
            # Set search flag and trigger rerun
            st.session_state.do_search = True
            st.session_state.search_in_progress = True  # Set search in progress flag
            st.rerun()
    
    # Execute search if flag is set
    if st.session_state.do_search and st.session_state.search_in_progress:
        st.session_state.do_search = False  # Reset flag
        
        with st.spinner("Processing data and searching Reddit..."):
            # Initialize services
            data_processor = DataProcessor()
            
            # Initialize Reddit service with stored credentials
            try:
                reddit_service = RedditService(
                    client_id=st.session_state.reddit_client_id,
                    client_secret=st.session_state.reddit_client_secret,
                    user_agent=st.session_state.reddit_user_agent
                )
            except Exception as e:
                st.error(f"Error connecting to Reddit API: {str(e)}")
                # Reset search state
                st.session_state.search_in_progress = False
                st.rerun()  # Rerun to update UI
            
            # Process keywords
            plants_keywords = []
            vessels_keywords = []
            
            if st.session_state.plants_data is not None:
                if test_mode:
                    plants_keywords = selected_plant_keywords
                    st.info(f"Test mode: Using selected plant keywords: {', '.join(plants_keywords)}")
                else:
                    plants_keywords = data_processor.extract_keywords(
                        st.session_state.plants_data,
                        name_col=st.session_state.plants_name_col_value,
                        owner_col=st.session_state.plants_owner_col_value
                    )
            
            if st.session_state.vessels_data is not None:
                if test_mode:
                    vessels_keywords = selected_vessel_keywords
                    st.info(f"Test mode: Using selected vessel keywords: {', '.join(vessels_keywords)}")
                else:
                    vessels_keywords = data_processor.extract_keywords(
                        st.session_state.vessels_data,
                        name_col=st.session_state.vessels_name_col_value,
                        owner_col=st.session_state.vessels_owner_col_value
                    )
            
            # Set progress display and initialize timing metrics
            st.session_state.progress = 0
            st.session_state.current_task = "Connecting to Reddit API..."
            st.session_state.start_time = time.time()
            st.session_state.search_log = []  # Reset search log
            
            # Calculate total steps for progress tracking
            total_subreddits = len(st.session_state.subreddits)
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
                
                # Add to search log
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.search_log.append(f"[{timestamp}] {task_description}")
                
                time.sleep(0.1)  # Small delay to allow UI to update
            
            # Perform search
            try:
                # Search for plants mentions
                if plants_keywords:
                    for keyword in plants_keywords:
                        for subreddit in st.session_state.subreddits:
                            current_task = f"Searching r/{subreddit} for plant keyword: {keyword}"
                            progress_update_callback(
                                st.session_state.progress,
                                current_task
                            )
                            
                            subreddit_results = reddit_service._make_api_request(
                                subreddit=subreddit,
                                keyword=keyword,
                                limit=st.session_state.search_limit,
                                time_filter=st.session_state.time_filter,
                                include_comments=st.session_state.include_comments,
                                comments_limit=st.session_state.comments_limit
                            )
                            
                            # Add results to session state immediately
                            for result in subreddit_results:
                                result['entity_type'] = 'plant'
                                st.session_state.plants_results.append(result)
                            
                            # Update progress
                            st.session_state.completed_steps += 1
                            if st.session_state.total_steps > 0:
                                st.session_state.progress = st.session_state.completed_steps / st.session_state.total_steps
                    
                # Search for vessels mentions
                if vessels_keywords:
                    for keyword in vessels_keywords:
                        for subreddit in st.session_state.subreddits:
                            current_task = f"Searching r/{subreddit} for vessel keyword: {keyword}"
                            progress_update_callback(
                                st.session_state.progress,
                                current_task
                            )
                            
                            subreddit_results = reddit_service._make_api_request(
                                subreddit=subreddit,
                                keyword=keyword,
                                limit=st.session_state.search_limit,
                                time_filter=st.session_state.time_filter,
                                include_comments=st.session_state.include_comments,
                                comments_limit=st.session_state.comments_limit
                            )
                            
                            # Add results to session state immediately
                            for result in subreddit_results:
                                result['entity_type'] = 'vessel'
                                st.session_state.vessels_results.append(result)
                            
                            # Update progress
                            st.session_state.completed_steps += 1
                            if st.session_state.total_steps > 0:
                                st.session_state.progress = st.session_state.completed_steps / st.session_state.total_steps
                
                # Display final results count
                st.success(f"Search completed! Found {len(st.session_state.plants_results)} plant mentions and {len(st.session_state.vessels_results)} vessel mentions.")
                
                # Add download button for search log
                if st.download_button(
                    label="Download Search Log",
                    data="\n".join(st.session_state.search_log),
                    file_name=f"reddit_search_log_{get_timestamp()}.txt",
                    mime="text/plain"
                ):
                    st.success("Search log downloaded")
                
                # Reset search-related session state
                st.session_state.search_in_progress = False
                st.session_state.progress = 0
                st.session_state.current_task = ""
                st.session_state.start_time = None
                st.session_state.total_steps = 0
                st.session_state.completed_steps = 0
                
                # Switch to Results tab
                time.sleep(1)
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
    
    # Show current search status if search is in progress
    if st.session_state.search_in_progress:
        st.subheader("Search in Progress")
        st.progress(st.session_state.progress)
        st.markdown(f"**Current task:** {st.session_state.current_task}")
        
        if st.session_state.start_time is not None:
            elapsed_time = time.time() - st.session_state.start_time
            st.markdown(f"**Elapsed time:** {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
        
        if st.session_state.completed_steps > 0 and st.session_state.total_steps > 0:
            st.markdown(f"**Progress:** {st.session_state.completed_steps} of {st.session_state.total_steps} steps completed")
    
    # Check if results exist
    if not st.session_state.plants_results and not st.session_state.vessels_results:
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
                        
                        # Create a permalink with full URL
                        full_url = f"https://www.reddit.com{mention['permalink']}"
                        st.markdown(f"**Permalink:** [Link to post]({full_url})")
                        
                        st.markdown("**Snippet:**")
                        st.markdown(f"> {mention['snippet']}")
                        
                        # Source label (post or comment)
                        st.markdown(f"**Source:** {mention['source']}")
                        
                        # Add a button to scrape additional content
                        if st.button(f"Get additional content for {mention['keyword']}", key=f"scrape_plant_{i}"):
                            try:
                                with st.spinner("Fetching additional content..."):
                                    scraped_content = get_website_text_content(full_url)
                                    if scraped_content:
                                        st.subheader("Additional Content")
                                        st.text_area("Full Text Content", scraped_content, height=300)
                                        st.success("Successfully retrieved additional content")
                                    else:
                                        st.warning("No additional content could be retrieved")
                            except Exception as e:
                                st.error(f"Error retrieving additional content: {str(e)}")
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
                        
                        # Create a permalink with full URL
                        full_url = f"https://www.reddit.com{mention['permalink']}"
                        st.markdown(f"**Permalink:** [Link to post]({full_url})")
                        
                        st.markdown("**Snippet:**")
                        st.markdown(f"> {mention['snippet']}")
                        
                        # Source label (post or comment)
                        st.markdown(f"**Source:** {mention['source']}")
                        
                        # Add a button to scrape additional content
                        if st.button(f"Get additional content for {mention['keyword']}", key=f"scrape_vessel_{i}"):
                            try:
                                with st.spinner("Fetching additional content..."):
                                    scraped_content = get_website_text_content(full_url)
                                    if scraped_content:
                                        st.subheader("Additional Content")
                                        st.text_area("Full Text Content", scraped_content, height=300)
                                        st.success("Successfully retrieved additional content")
                                    else:
                                        st.warning("No additional content could be retrieved")
                            except Exception as e:
                                st.error(f"Error retrieving additional content: {str(e)}")
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
    5. Optionally scrape additional content from links
    
    ### Tips:
    - Higher search limits may take longer but find more results
    - Reddit API has rate limits, so very large searches may be throttled
    - For best results, use specific and unique names as keywords
    - Use the "Get additional content" buttons to scrape more details from posts
    """)
