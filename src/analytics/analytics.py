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

analytics_data = []
page = 1
total_pages = 1 #initialize the loop

print(f"Fetching analytics for dates: {start_date_str} to {end_date_str}")

if video_id:
    print(f"   For video ID: {video_id}")
    # This endpoint is for specific video analytics.
    base_uri = f'.videos/{video_id}/analytics'
else:
    # This endpoint is for specific video analytics.
    # Note: Access to this may vary based on your Vimeo Enterprise plan and API scopes.
    print(f"  Fetching account-wide analytics...")
    base_uri = '/me/analytics' # or '/users/{user_id}/analytics if targeting a user's analytics

    while page <= total_pages:
        params['page'] = page
        uri_with_params = f"{base_uri}?{pd.io.common.urlencode(params)}"

        try:
            response = client.get(uri_with_params)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    analytics_data.extend(data['data'])
                    if 'paging' in data and 'pages' in data['paging']:
                        total_pages = data['paging']['pages']
                    else:
                        total_pages = page
                    print(f"  Fetched page {page}/{total_pages}")
                    page += 1
                else:
                    print(f"No data found for page {page} or end of data.")
                    break
            elif response.status_code == 403:
                print(f"Access Denied (403): Check your API token scopes and Vimeo account type.")
                print(f"Response: {response.text}")
                break
            else:
                print(f"Error fetching analytics data (Status: {response.status_code}): {response.text}")
                break
        except Exception as e:
            print(f"An unexpected error has occurred during API call: {e}")
            break
    return analytics_data

# --- Main Script Execution ---
if __name__ == '__main__':
    vimeo_client = initialize_vimeo_client(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN)

    if vimeo_client:
        specific_video_id = 'YOUR_VIDEO_ID'

        if specific_video_id == 'YOUR_VIDEO_ID' or specific_video_id is None:
            print("\nNote: 'YOUR_VIDEO_ID' is a placeholder. If you want specific video analytics,")
            print("      please replace it with an actual video ID from your Vimeo account.")
            print("      Attempting to fetch account-wide analytics (if supported by your API access).")
            analytics_data = get_video_analytics(
                vimeo_client,
                video_id=None,
                start_date=START_DATE,
                end_date=END_DATE,
                dimensions=DIMENSIONS,
                metrics=METRICS
            )
