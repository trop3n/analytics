import vimeo
import pandas as pd
from datetime import datetime, timedelta
import os

# --- Configuration ---
# IMPORTANT: Replace these with your actual Vimeo API credentials.
# You need a Vimeo Enterprise account and an API application created on the Vimeo Developer Site.
# Ensure your Personal Access Token has the necessary scopes (e.g., public, private, video_files, analytics).
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN'

# --- Analytics Parameters ---
# Define the date range for your report
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=7) # Example: Last 30 days

# Dimensions you want to pull (e.g., 'date', 'country', 'device_types', 'embed_domains')
# Refer to Vimeo Analytics API documentation for available dimensions.
DIMENSIONS = ['date', 'video_id', 'country', 'device_type']

# Metrics you want to pull (e.g. 'plays', 'finishes', 'total_atch_time', etc.)
# Refer to Vimeo Analytics API docs for available metrics.
METRICS = ['plays', 'finishes', 'total_watch_time', 'impressions']

# --- Initialize Vimeo Client ---
def initialize_vimeo_client(client_id, client_secret, access_token):
    """
    Initializes and returns a Vimeo API client.
    """
    try:
        client = vimeo.VimeoClient(
            token=access_token,
            key=client_id,
            secret=client_secret
        )
        print("Vimeo API client initialized successfully.")
        return client
    except Exception as e:
        print(f"Error initializing Vimeo API client: {e}")
        return None

# --- Function to Fetch Analytics Data ---
def get_video_analytics(client, video_id=None, start_date=None, end_date=None, dimensions=None, metrics=None):
    """
    Fetches analytics data from Vimeo for a specific video or all videos.

    Args:
        client (vimeo.VimeoClient): An initialized Vimeo API client.
        video_id (str, optional): The ID of the video to get analytics for.
                                  If None, fetches for all videos accessible by the token (account-wide).
        start_date (datetime): The start date for the analytics data.
        end_date (datetime): The end date for the analytics data.
        dimensions (list): A list of dimensions to include in the report.
        metrics (list): A list of metrics to include in the report.

    Returns:
        list: A list of dictionaries, each representing an analytics data point.
    """
    if not client:
        print("Vimeo client not initialized. Cannot fetch data.")
        return []
    if not start_date or not end_date or not dimensions or not metrics:
        print("Error: start_date, end_date, dimensions, and metrics are required.")
        return []
        
# Format dates for API request
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

params = {
    'start_date': start_date_str,
    'end_date': end_date_str,
    'dimensions': ','.join(dimensions),
    'metrics': ','.join(metrics),
    'per_page': 100, # Max per_page for Vimeo API
}