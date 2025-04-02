import trafilatura


def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    The results is not directly readable, better to be summarized by LLM before consume
    by the user.

    Args:
        url: URL of the website to scrape
        
    Returns:
        Extracted text content from the website
        
    Raises:
        Exception: If there is an error fetching or processing the URL
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            raise Exception(f"Failed to download content from {url}")
            
        # Extract main text content
        text = trafilatura.extract(downloaded)
        
        if not text:
            raise Exception(f"Failed to extract text content from {url}")
            
        return text
    except Exception as e:
        raise Exception(f"Error scraping website: {str(e)}")