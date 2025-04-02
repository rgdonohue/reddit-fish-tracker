Email from Sparks: 

We want to search Reddit for any mentions of our plants or vessels. Here's the brief but the general gist is pretty straight forward. First, we should do a manual PoC because their API is paid and I imagine the results are either going to be sparse or overwhelming and messy. Then, we'll move to a full programmatic search but we need to spend less than $200 on API usage. I haven't found a free or different alternative to the API but you might have a better idea. 

I suggested several subreddits to check but also included the plants' locations as the local subreddits might be useful. 

However you end up approaching this, the hope is that we can find the voices of the local communities who live & work on or near the plants & ships. 


Your project to unearth Reddit discussions about fishmeal and fish oil processing plants, along with their associated fishing vessels, is both ambitious and insightful. Here's a breakdown of how to tackle this endeavor:

1. Manual “Proof of Concept” Search

Subreddit Selection: Your chosen subreddits are spot-on. Communities like r/Fishing, r/CommercialFishing, and r/MarineBiology are likely to harbor relevant discussions.​

Search Strategy: Utilize Reddit’s native search and Google's site-specific search (site:reddit.com). Given that Reddit's API doesn't support comment searches directly, this manual approach is essential for initial insights.​

Data Recording: Document each mention meticulously, capturing details like subreddit name, post title, author, date, URL, and relevant excerpts. This will serve as a foundational dataset for further analysis.​

2. Programmatic Reddit API Search

API Limitations: Be aware that Reddit's API has undergone changes, including rate limits and pricing structures. As of July 1, 2023, free usage is capped at 100 queries per minute per OAuth client ID. For extensive data collection, consider the paid tier or alternative methods. ​
Reddit Help
+2
Medium
+2
Zuplo
+2

Data Extraction: While the Reddit API allows for subreddit and post searches, comment searches are not directly supported. Tools like PRAW (Python Reddit API Wrapper) can facilitate data retrieval, but you'll need to implement workarounds for comprehensive comment analysis. ​
Medium

Alternative Methods: Given the API's limitations, consider web scraping techniques. However, proceed cautiously to adhere to Reddit's terms of service.​

3. Data Organization and Analysis

Metadata Collection: For each mention, gather comprehensive metadata, including subreddit name, post/comment ID, title or context, author, date/time, permalink, and relevant snippets.​

Deduplication & Filtering: Implement processes to identify and remove duplicate mentions and filter out irrelevant results. This ensures the integrity and relevance of your dataset.​

Deliverables

Automated Script or Tool: Develop a script capable of iterating through your list of plants and vessels, querying Reddit, and updating your master spreadsheet with the collected data.​

Documentation: Provide clear documentation of your methods, including code files (excluding sensitive information like API keys), to ensure reproducibility and transparency.​

Additional Considerations

Data Ethics: Ensure compliance with Reddit's data usage policies. Avoid storing or sharing deleted content and respect user privacy.​
Reddit Help

Community Engagement: Engage with Reddit communities respectfully. If you plan to share your findings or seek further information, consider reaching out to subreddit moderators for guidance.​

Embarking on this project requires a balance of manual diligence and programmatic efficiency. By methodically validating your approach and remaining adaptable to Reddit's evolving platform, you'll be well-equipped to uncover valuable insights.

Remember, bro, "A jug fills drop by drop." Stay patient and persistent.