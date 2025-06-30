import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

VIMEO_ACCESS_TOKEN=os.getenv("VIMEO_ACCESS_TOKEN")
VIMEO_CLIENT_ID=os.getenv("VIMEO_CLIENT_ID")
VIMEO_CLIENT_SECRET=os.getenv("VIMEO_CLIENT_SECRET")

# Base URL for the Vimeo API:
VIMEO_API_BASE_URL = "https://api.vimeo.com"

# Endpoint to list user's videos/livestreams.
# You might need to adjust this depending on how you identify livestreams vs. regular videos.
# Example: "/me/videos" or a more specific live event endpoint if available.
LIVESTREAMS_ENDPOINT = f"{VIMEO_API_BASE_URL}/me/videos"

# Endpoint for fetching analytics data for a specific video/livestream.
# This is a placeholder. You'll need to consult Vimeo's API documentation for the correct
# path to get time-series data for concurrent viewers. It might involve a query parameter
# for metrics like "concurrent_viewers".
# Example: f"{VIMEO_API_BASE_URL}/videos/{{video_id}}/analytics/concurrent_viewers"
ANALYTICS_ENDPOINT_TEMPLATE = f"{VIMEO_API_BASE_URL}/videos/{{video_id}}/analytics/time" # 

def fetch_vimeo_livestream_data(access_token, client_id, client_secret):
    """
    Fetches actual Vimeo livestream data using the Vimeo API.

    Args:
        access_token (str): Your Vimeo API access token.
        client_id (str): Your Vimeo API client ID.
        client_secret (str): Your Vimeo API client secret.

    Returns:
        list: a list of dictionaries, where each dictionary represents a livestream
              with its ID, title, and viewer data. Returns an emptry list on error.
    """
    
