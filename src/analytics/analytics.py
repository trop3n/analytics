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

# Metrics you want to pull (e.g. 'plays',)