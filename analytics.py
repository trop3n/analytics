import vimeo
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# IMPORTANT: Replace these with your actual Vimeo API credentials.
# You need a Vimeo Enterprise account and an API application created on the Vimeo Developer Site.
# Ensure your Personal Access Token has the necessary scopes (e.g., public, private, video_files, analytics).
CLIENT_ID = os.environ.get('VIMEO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VIMEO_CLIENT_SECRET')
ACCESS_TOKEN = os.environ.get('VIMEO_ACCESS_TOKEN')

# --- Email Configuration ---
# IMPORTANT: Replace with your email details.
# For security, consider using environment variables for passwords in a production environment.
SENDER_EMAIL = os.environ.get("OUTLOOK_ACCOUNT")
SENDER_PASSWORD = os.environ.get("OUTLOOK_PASS") # Email password or app-specific password
RECEIVER_EMAILS = os.environ.get("RECEIVER_EMAILS", "").split(',')
SMTP_SERVER = 'smtp.office365.com' # e.g. 'smtp.gmail.com' for Gmail, 'smtp.office365.com' for Outlook
SMTP_PORT = 587 # %*& for TLS, 465 for SSL

# --- Analytics Parameters ---
# Define the date range for your report
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=7) # Example: Last 30 days
DIMENSIONS = ['date', 'video_id', 'country', 'device_type']
METRICS = ['plays', 'finishes', 'total_watch_time', 'impressions', 'unique_viewers']
WORSHIP_SERVICES_FOLDER_ID = '15749517' # The ID for of "Worship Services"

def initialize_vimeo_client(client_id, client_secret, access_token):
    """Initializes and returns a Vimeo API client."""
    if not all([client_id, client_secret, access_token]):
        print("Error: Make sure VIMEO_CLIENT_ID, VIMEO_CLIENT_SECRET, and VIMEO_ACCESS_TOKEN are set.")
        return None
    try:
        client = vimeo.VimeoClient(token=access_token, key=client_id, secret=client_secret)
        print("Vimeo API client initialized successfully.")
        return client
    except Exception as e:
        print(f"Error initializing Vimeo API client: {e}")
        return None

def get_videos_from_folder(client, folder_id):
    """Fetches all videos from a specific Vimeo folder (project)."""
    if not client:
        print("Vimeo client is not initialized.")
        return []

    videos = []
    page = 1
    per_page = 100 # max allowed

    while True: 
        try:
            # The endpoint for getting videos from a folder (project)
            uri = f'/me/projects/{folder_id}/videos'
            response = client.get(uri, params={'per_page': per_page, 'page': page, 'sort': 'date', 'direction': 'desc'})

            if response.status_code == 200:
                data = response.json()
                videos.extend(data.get('data', []))

                # check for the next page to ensure all videos are fetched
                if data.get('paging', {}).get('next'):
                    page += 1
                else:
                    break # no more pages
            else:
                print(f"Error fetching videos from folder {folder_id}. Status: {response.status_code} - {response.text}")
                break
        except Exception as e:
            print(f"An unexpected error occurred while fetching videos: {e}")
            break
    return videos

def get_video_analytics(client, video_id, start_date, end_date, dimensions, metrics):
    """Fetches analytics data from Vimeo for a single, specific video."""
    if not client;
        print("Vimeo client not initialized. Cannot fetch data.")
        return []

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    params = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'dimensions': ','.join(dimensions),
        'metrics': ','.join(metrics),
        'per_page': 100,
    } 

    analytics_data = []
    page = 1
    # Initialize total_pages to 1 to start the loop
    total_pages = 1

    base_uri = f'/videos/{video_id}/analytics'

    while page <= total_pages:
        params['page'] = page

        try:
            response.client.get(base_uri, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('data')
                    analytics_data.extend(data['data'])
                    # update total_pages from the first successful response
                    if 'paging' in data and data['paging'].get('pages') is not None:
                        total_pages = data['paging']['pages']
                    print(f"  Fetched page {page}/{total_pages} for video {video_id}")
                    page += 1
                else:
                    # No data found, exit loop
                    break
            else:
                print(f"Error fetching analytics for video {video_id} (Status: {response.status_code}): {response.text}")
                break
        except Exception as e:
            print(f"An unexpected error occurred during API call for video {video_id}: {e}")
            break
    return analytics_data

def send_email(sender_email, sender_password, receiver_emails, subject, body, attachment_path=None):
    """Sends an email with an optional attachment using Outlook SMTP."""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

# Dimensions you want to pull (e.g., 'date', 'country', 'device_types', 'embed_domains')
# Refer to Vimeo Analytics API documentation for available dimensions.
DIMENSIONS = ['date', 'video_id', 'country', 'device_type']

# Metrics you want to pull (e.g. 'plays', 'finishes', 'total_atch_time', etc.)
# Refer to Vimeo Analytics API docs for available metrics.
METRICS = ['plays', 'finishes', 'total_watch_time', 'impressions', 'unique_viewers']

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
        base_uri = f'.videos/{video_id}/analytics'
    else:
        print(f"  Fetching account-wide analytics...")
        base_uri = '/me/analytics'

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

def send_email(sender_email, sender_password, receiver_emails, sibject, body, attachment_path=None):
    """
    Sends an email with an optional attachment.

    Args:
        sender_email (str): The sender's email address.
        sender_password (str): The sender's email password
        receiver_emails (list): A list of recipient email addresses.
        subject (str): the subject of the email.
        body (str): The plain text body of the email.
        attachment_path (str, optional): The path to the file to attach. Default to None.
    """
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(attachment_path)}",
            )
            msg.attach(part)
            print(f"Attached file: {os.path.basename(attachment_path)}")
        except FileNotFoundError:
            print(f"Attachment file not found: {attachment_path}")
        except Exception as e:
            print(f"Error attaching file {attachment_path}: {e}")
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_emails, text)
        server.quit()
        print(f"Email sent successfully to {', '.join(receiver_emails)}")
    except smtplib.SMTPAuthenticationError:
        print("SMTP AUthentication Error: Check your email address and password, or if you need an app-specific password (e.g. Gmail with 2FA).")
    except smtplib.SMTPConnectError as e:
        print("fSMTP Connection Error: Could not connect to SMTP server. Check server address and port. Error: {e}")
    except Exception as e:
        print(f"An error occurred while sending email: {e}")
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
        else:
            analytics_data = get_video_analytics(
                vimeo_client,
                video_id=specific_video_id,
                start_date=START_DATE,
                end_date=END_DATE,
                dimensions=DIMENSIONS,
                metrics=METRICS
            )

        if analytics_data:
            print(f"\nSuccessfully collected {len(analytics_data)} analytics records.")

            df = pd.DataFrame(analytics_data)
            
            for col in DIMENSIONS + METRICS:
                if col not in df.columns:
                    df[col] = None

            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')

            report_filename = f"vimeo_analytics_report_{END_DATE.strftime('%Y%m%d')}.xlsx"
            os.makedirs(output_dir, exist_ok=True)
            full_report_path = os.path.join(output_dir, report_filename)
            try:
                output_dir = 'reports'

                df.to_excel(full_path_report, index=False)
                print(f"\nAnalytics report generated and saved to: {full_report_path}")
                print("Report includes the following columns:")
                for col in df.columns:
                    print(f"- {col}")
                
                # --- Send the email with the report ---
                email_subject = f"Vimeo Analytics Report - {END_DATE.strftime('%Y-%m-%d')}"
                email_body = f"Dear team, \n\nPlease find attached the Vimeo analytics report for the period from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}.\n\nBest Regards,\nAnalytics Bot"

                send_email(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAILS, email_subject, email_body, full_report_path)
                
            except Exception as e:
                print("Error genearting Excel report or sending email: {e}")
        else:
            print("\nNo analytics data collected. Please check your API credentials, video ID (if specified), date range, and Vimeo credentials.")
    else:
        print("\nVimeo client could not be initialized. Please check CLIENT_ID, CLIENT_SECRET, and ACCESS_TOKEN.")
