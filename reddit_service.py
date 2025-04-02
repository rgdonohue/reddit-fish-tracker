import praw
import time
import datetime
import pandas as pd
import re
from typing import List, Dict, Any, Callable, Optional

class RedditService:
    """Service for interacting with Reddit API to search for mentions"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.rate_limit_delay = 2  # Seconds between API calls to avoid rate limiting
    
    def search_reddit(
        self, 
        keywords: List[str], 
        subreddits: List[str], 
        limit: int = 100, 
        time_filter: str = "month", 
        include_comments: bool = True, 
        comments_limit: int = 100,
        entity_type: str = "general",
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[Any, Any]]:
        """
        Search Reddit for mentions of keywords in specified subreddits
        
        Args:
            keywords: List of keywords to search for
            subreddits: List of subreddit names to search in
            limit: Maximum number of posts to search per subreddit
            time_filter: Time filter for search (day, week, month, year, all)
            include_comments: Whether to search comments as well
            comments_limit: Maximum number of comments to search per post
            entity_type: Type of entity being searched (for reporting)
            progress_callback: Callback function to report progress
        
        Returns:
            List of dictionaries containing mention information
        """
        results = []
        total_progress_steps = len(keywords) * len(subreddits)
        current_step = 0
        
        if progress_callback:
            progress_callback(0.0, f"Starting Reddit search for {entity_type} mentions")
        
        # Search each subreddit for each keyword
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for keyword in keywords:
                    current_step += 1
                    progress = current_step / total_progress_steps
                    
                    if progress_callback:
                        task_description = f"Searching r/{subreddit_name} for '{keyword}' ({entity_type}) - Step {current_step} of {total_progress_steps}"
                        progress_callback(
                            progress, 
                            task_description
                        )
                    
                    # Search in post titles and text
                    search_query = keyword
                    submissions = subreddit.search(search_query, limit=limit, time_filter=time_filter)
                    
                    # Process each submission
                    for submission in submissions:
                        # Check if keyword is in title or selftext
                        title_match = self._check_keyword_match(submission.title, keyword)
                        text_match = False
                        
                        if hasattr(submission, 'selftext') and submission.selftext:
                            text_match = self._check_keyword_match(submission.selftext, keyword)
                        
                        if title_match or text_match:
                            # Add submission to results
                            result = {
                                'id': submission.id,
                                'title': submission.title,
                                'author': str(submission.author),
                                'datetime': datetime.datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                                'subreddit': subreddit_name,
                                'permalink': submission.permalink,
                                'source': 'submission',
                                'keyword': keyword,
                                'entity_type': entity_type
                            }
                            
                            # Get snippet from title or selftext
                            if title_match:
                                result['snippet'] = self._get_context_snippet(submission.title, keyword)
                            else:
                                result['snippet'] = self._get_context_snippet(submission.selftext, keyword)
                            
                            results.append(result)
                    
                    # Search comments if enabled
                    if include_comments:
                        if progress_callback:
                            task_description = f"Searching comments in r/{subreddit_name} for '{keyword}' ({entity_type}) - Step {current_step} of {total_progress_steps}"
                            progress_callback(
                                progress, 
                                task_description
                            )
                        
                        # Get all submissions again for comment search
                        submissions = subreddit.search(search_query, limit=limit, time_filter=time_filter)
                        
                        for submission in submissions:
                            # Replace with actual submission ID
                            submission.comments.replace_more(limit=0)  # Don't fetch MoreComments
                            
                            # Get all comments up to the limit
                            comments = list(submission.comments.list())[:comments_limit]
                            
                            for comment in comments:
                                if hasattr(comment, 'body') and comment.body:
                                    comment_match = self._check_keyword_match(comment.body, keyword)
                                    
                                    if comment_match:
                                        result = {
                                            'id': comment.id,
                                            'title': submission.title + f" (Comment by u/{comment.author})",
                                            'author': str(comment.author),
                                            'datetime': datetime.datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                                            'subreddit': subreddit_name,
                                            'permalink': comment.permalink,
                                            'source': 'comment',
                                            'snippet': self._get_context_snippet(comment.body, keyword),
                                            'keyword': keyword,
                                            'entity_type': entity_type
                                        }
                                        
                                        results.append(result)
                    
                    # Respect Reddit's rate limits
                    time.sleep(self.rate_limit_delay)
            
            except Exception as e:
                print(f"Error searching subreddit {subreddit_name}: {str(e)}")
                # Continue with other subreddits
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(1.0, f"Completed search for {entity_type} mentions - All {total_progress_steps} steps finished")
        
        return results
    
    def _check_keyword_match(self, text: str, keyword: str) -> bool:
        """Check if keyword appears in text using regex word boundaries"""
        if not text or not keyword:
            return False
            
        # Create regex pattern with word boundaries
        pattern = r'\b' + re.escape(keyword) + r'\b'
        match = re.search(pattern, text, re.IGNORECASE)
        return match is not None
    
    def _get_context_snippet(self, text: str, keyword: str, context_chars: int = 100) -> str:
        """Extract a snippet of text containing the keyword with surrounding context"""
        if not text:
            return ""
            
        try:
            # Find keyword position (case insensitive)
            keyword_pos = text.lower().find(keyword.lower())
            
            if keyword_pos == -1:
                return text[:200] + "..."  # Return start of text if keyword not found
            
            # Calculate snippet bounds
            start = max(0, keyword_pos - context_chars)
            end = min(len(text), keyword_pos + len(keyword) + context_chars)
            
            # Extract snippet
            snippet = text[start:end].strip()
            
            # Add ellipsis if truncated
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
                
            return snippet
            
        except Exception as e:
            print(f"Error creating snippet: {str(e)}")
            return text[:200] + "..."  # Fallback to first 200 chars
