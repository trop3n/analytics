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
    # Check if credentials are provided
    if not access_token:
        print("Error: VIMEO_ACCESS_TOKEN not found in env variables. Please set it in your .env file.")
        return []

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.vimeo.*+json;version=3.4"
    }

    livestreams_data = []

    try:
        # Step 1: Fetch a list of livestreams/videos
        print(f"Attempting to fetch livestreams from: {LIVESTREAMS_ENDPOINT}")
        response = requests.get(LIVESTREAMS_ENDPOINT, headers=headers)
        response.raise_for_status()
        videos = response.json().get("data", [])
        
        print(f"Found {len(videos)} videos/livstreams. Fetching analytics...")

        for video in videos:
            video_id = video.get("uri", "").split("/")[-1] # Extract ID from URI
            video_name = video.get("name", "Untitled Video")

            if not video_id:
                print(f"Skipping video with no ID: {video_name}")
                continue

            # Step 2: For each livestream, fetch it's analytics data (concurrent viewers)
            # This part is highly dependent on the actual Vimeo API structure for analytics.
            # You might need to adjust the endpoint and how you extract viewer data.
            analytics_endpoint = ANALYTICS_ENDPOINT_TEMPLATE.format(video_id=video_id)

            # For common parameters for analytics data (concurrent viewers)
            # For simplicity, let's fetch data for the last 24 hours.
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=1)
            params = {
                "start_date": start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "end_date": end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "interval": "minute", # Or "hour", "day" depending on granularity needed
                "metrics": "concurrent_viewers" # This parameter might be needed               
            }

            print(f"   Fetching analytics for '{video_name}' (ID: {video_id}) from: {analytics_endpoint}")
            analytics_response = requests.get(analytics_endpoint, headers=headers, params=params)
            analytics_response.raise_for_status()
            analytics_data = analytics_response.json()

            # --- PARSING ANALYTICS DATA (YOU WILL LIKELY NEED TO CUSTOMIZE THIS) ---
            # This is a generic assumption based on common analytics API structures.
            # You'll need to inspect the actual JSON response from Vimeo to parse it correctly.
            viewer_data_points = []
            if 'data' in analytics_data and isinstance(analytics_data['data'], list):
                for point in analytics_data['data']:
                    # Assuming API returns a 'time' and 'concurrent viewers' key
                    if 'time' in point and 'concurrent_viewers' in point:
                        viewer_data_points.append({
                            "timestamp": point['time'],
                            "concurrent_viewers": point['concurrent_viewers']
                        })
                    # If 'concurrent_viewers' is nested, e.g. in a 'metrics' object:
                    elif 'time' in point and 'metrics' in point and 'concurrent_viewers' in point['metrics']:
                        viewer_data_points.append({
                            "timestamp": point['time'],
                            "concurrent_viewers": point['metrics']['concurrent_viewers']
                        })
            else:
                print(f"   No viewer data found or unexpected format for Video ID {video_id}. Response: {analytics_data}")

            livestreams_data.append({
                "id": video_id,
                "title": video_name,
                "viewer_data": viewer_data_points
            })

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error Occurred: {http_err} - Response: {http_err.response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during API request: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return livestreams_data

def get_peak_viewers(viewer_data):
    """
    Calculates the peak concurrent viewers from a list of viewer data points.

    Args:
        viewer_data (list): A list of dictionaries, where each dictionary
                            has a "concurrent_viewers" key.

    Returns:
        int: The highest concurrent viewer count found. Returns 0 if no data.
    """
    if not viewer_data:
        return 0
    # Extract all concurrent viewer counts and find the maximum
    peak_viewers = max([data["concurrent_viewers"] for data in viewer_data])
    return peak_viewers

def generate_vimeo_analytics_report(livestreams_data):
    """
    Generates a formatted report of Vimeo livestream analytics,
    focusing on peak concurrent viewers.

    Args:
        livestreams_data (list): A list of dictionaries, each representing
                                 a livestream with its associated data.

    Returns:
        str: A multi-line string containing the formatted report.
    """
    report_lines = ["Vimeo Livestream Peak Viewers Report\n"]
    report_lines.append(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append("-" * 50)

    if not livestreams_data:
        report_lines.append("No livestream data available to generate a report.")