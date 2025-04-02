import praw
import time
import datetime
import pandas as pd
import re
from typing import List, Dict, Any, Callable, Optional
from prawcore.exceptions import ResponseException, RequestException

class RedditService:
    """Service for interacting with Reddit API to search for mentions"""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.rate_limit_delay = 2  # Base delay between API calls
        self.max_retries = 3  # Maximum number of retries for rate limits
        self.base_backoff = 5  # Base backoff time in seconds
    
    def _handle_rate_limit(self, attempt: int) -> None:
        """Handle rate limiting with exponential backoff"""
        backoff_time = self.base_backoff * (2 ** (attempt - 1))  # Exponential backoff
        time.sleep(backoff_time)
    
    def _make_api_request(self, subreddit: str, keyword: str, limit: int, time_filter: str, 
                         include_comments: bool, comments_limit: int, attempt: int = 1) -> List[Dict[Any, Any]]:
        """Make API request with rate limit handling"""
        try:
            subreddit_instance = self.reddit.subreddit(subreddit)
            search_results = []
            
            # Search in posts
            for submission in subreddit_instance.search(keyword, limit=limit, time_filter=time_filter):
                # Check post title and content
                if self._check_keyword_match(submission.title, keyword):
                    search_results.append({
                        'id': submission.id,
                        'title': submission.title,
                        'author': str(submission.author),
                        'datetime': datetime.datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'permalink': submission.permalink,
                        'snippet': self._get_context_snippet(submission.title, keyword),
                        'source': 'post',
                        'subreddit': subreddit,
                        'keyword': keyword
                    })
                
                # Check comments if enabled
                if include_comments:
                    try:
                        submission.comments.replace_more(limit=0)  # Load all comments
                        for comment in submission.comments.list()[:comments_limit]:
                            if self._check_keyword_match(comment.body, keyword):
                                search_results.append({
                                    'id': comment.id,
                                    'title': submission.title,
                                    'author': str(comment.author),
                                    'datetime': datetime.datetime.fromtimestamp(comment.created_utc).isoformat(),
                                    'permalink': submission.permalink,
                                    'snippet': self._get_context_snippet(comment.body, keyword),
                                    'source': 'comment',
                                    'subreddit': subreddit,
                                    'keyword': keyword
                                })
                    except Exception as e:
                        print(f"Error processing comments for submission {submission.id}: {str(e)}")
                        continue
                
                time.sleep(self.rate_limit_delay)  # Delay between submissions
            
            return search_results
            
        except ResponseException as e:
            if e.response.status_code == 429 and attempt < self.max_retries:
                print(f"Rate limit hit for subreddit {subreddit}, attempt {attempt}. Backing off...")
                self._handle_rate_limit(attempt)
                return self._make_api_request(subreddit, keyword, limit, time_filter, 
                                           include_comments, comments_limit, attempt + 1)
            else:
                print(f"Error searching subreddit {subreddit}: {str(e)}")
                return []
        except Exception as e:
            print(f"Error searching subreddit {subreddit}: {str(e)}")
            return []
    
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
        
        for subreddit in subreddits:
            for keyword in keywords:
                if progress_callback:
                    current_step += 1
                    progress = current_step / total_progress_steps
                    progress_callback(progress, f"Searching r/{subreddit} for '{keyword}'")
                
                # Make API request with rate limit handling
                subreddit_results = self._make_api_request(
                    subreddit=subreddit,
                    keyword=keyword,
                    limit=limit,
                    time_filter=time_filter,
                    include_comments=include_comments,
                    comments_limit=comments_limit
                )
                
                results.extend(subreddit_results)
                time.sleep(self.rate_limit_delay)  # Delay between keywords
        
        return results

    def _check_keyword_match(self, text: str, keyword: str) -> bool:
        """Check if keyword appears in text"""
        if not isinstance(text, str):
            return False
        return keyword.lower() in text.lower()

    def _get_context_snippet(self, text: str, keyword: str, context_chars: int = 100) -> str:
        """Get a snippet of text around the keyword"""
        if not isinstance(text, str):
            return ""
            
        text = text.lower()
        keyword = keyword.lower()
        
        # Find keyword position
        pos = text.find(keyword)
        if pos == -1:
            return text[:context_chars] + "..." if len(text) > context_chars else text
            
        # Get context around keyword
        start = max(0, pos - context_chars // 2)
        end = min(len(text), pos + len(keyword) + context_chars // 2)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
            
        return snippet
