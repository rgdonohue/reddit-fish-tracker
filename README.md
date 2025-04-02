# Fishing Industry Reddit Monitor

A Streamlit application that monitors Reddit for mentions of fishing industry entities, including fish processing plants and commercial fishing vessels.

## Features

- Upload and process CSV files containing fish processing plants and commercial fishing vessels data
- Extract keywords from uploaded data
- Search specified subreddits for mentions of these keywords
- Generate detailed reports with mention details
- Download results in CSV format
- Scrape additional content from Reddit posts

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Reddit API credentials:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=your_user_agent
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment

This app is configured for deployment on Streamlit Community Cloud. To deploy:

1. Push your code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository and branch
6. Set the main file path to `app.py`
7. Add your environment variables in the Streamlit Cloud dashboard
8. Deploy!

## Environment Variables

The following environment variables are required:

- `REDDIT_CLIENT_ID`: Your Reddit API client ID
- `REDDIT_CLIENT_SECRET`: Your Reddit API client secret
- `REDDIT_USER_AGENT`: Your Reddit API user agent string

## Data Files

The app expects two CSV files in the `data` directory:
- `Plants.csv`: Contains fish processing plant data
- `Ships.csv`: Contains commercial fishing vessel data

## License

MIT License 