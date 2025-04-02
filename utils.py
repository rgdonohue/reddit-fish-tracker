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
    
    # Extract step information from message if it exists
    try:
        if " step " in message.lower() or " of " in message.lower():
            # Try to extract step counts from message format: "... - Step X of Y"
            parts = message.split(" - Step ")
            if len(parts) > 1:
                step_parts = parts[1].split(" of ")
                if len(step_parts) > 1:
                    current_step = int(step_parts[0])
                    total_steps = int(step_parts[1].split()[0])  # Split to handle any additional text
                    
                    # Update session state step counters
                    st.session_state.completed_steps = current_step
                    st.session_state.total_steps = total_steps
        
        # Another format: "Completed search for X mentions - All Y steps finished"
        elif "all" in message.lower() and "steps finished" in message.lower():
            parts = message.lower().split("all ")
            if len(parts) > 1:
                steps_part = parts[1].split(" steps")[0]
                if steps_part.isdigit():
                    total_steps = int(steps_part)
                    # Mark all steps as completed
                    st.session_state.completed_steps = total_steps
                    st.session_state.total_steps = total_steps
    except Exception as e:
        # If we encounter any errors parsing the message, just ignore them
        # Don't update step counters in this case
        print(f"Error parsing progress message: {str(e)}")

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
