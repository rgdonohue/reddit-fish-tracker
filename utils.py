import datetime
import time
import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional

def get_timestamp() -> str:
    """Generate a timestamp string for file naming"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def display_progress(progress: float, message: str):
    """
    Display progress in Streamlit
    
    Args:
        progress: Float between 0 and 1 representing progress percentage
        message: Message to display alongside the progress bar
    """
    # Update session state
    st.session_state.progress = progress
    st.session_state.current_task = message

def save_to_csv(data: List[Dict[Any, Any]], filename: str) -> bool:
    """
    Save data to CSV file
    
    Args:
        data: List of dictionaries to save
        filename: Name of file to save to
        
    Returns:
        Boolean indicating success
    """
    try:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return True
    except Exception as e:
        print(f"Error saving CSV: {str(e)}")
        return False

def format_reddit_url(permalink: str) -> str:
    """
    Format a Reddit permalink as a full URL
    
    Args:
        permalink: Reddit permalink string
        
    Returns:
        Full URL to Reddit post or comment
    """
    if not permalink:
        return ""
        
    # Add reddit domain if it doesn't exist
    if not permalink.startswith("http"):
        return f"https://www.reddit.com{permalink}"
    
    return permalink
