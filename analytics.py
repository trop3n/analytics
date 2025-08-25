import vimeo
import pandas as pd
from datetime import datetime, timedelta, timezone
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

def get_videos_from_folder(client, folder_id, cutoff_date):
    """Fetches all videos from a specific Vimeo folder optimized to stop when videos are older than the cutoff_date."""
    if not client:
        print("Vimeo client is not initialized.")
        return []

    videos = []
    page = 1
    per_page = 100 # max allowed

    while True: 
        try:
            # The endpoint for getting videos from a folder (project), sorted by date descending
            uri = f'/me/projects/{folder_id}/videos'
            response = client.get(uri, params={'per_page': per_page, 'page': page, 'sort': 'date', 'direction': 'desc'})

            if response.status_code == 200:
                data = response.json()

                page_videos = data.get('data', [])

                if not page_videos:
                    # no more videos found on this page, so we're done.
                    break

                videos.extend(page_videos)

                # --- OPTIMIZATION --- 
                # Check the date of the LAST video on the current page.
                # If it's older than our cutoff, we don't need to fetch any more pages.
                last_video_date = datetime.fromisoformat(page_videos[-1]['created_time'].replace('Z', '+00:00'))
                if last_video_date < cutoff_date:
                    print("  Found videos older than the cutoff date. Stopping pagination to improve performance.")
                    break # Exit the loop, no need to fetch older videos.

                # Check for the next page to continue fetching if needed.
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
    if not client:
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
            response = client.get(base_uri, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
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

    if attachment_path:
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment: filename = {os.path.basename(attachment_path)}")
            msg.attach(part)
            print(f"Attached file: {os.path.basename(attachment_path)}")
        except Exception as e:
            print(f"Error attaching file {attachment_path}: {e}")
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmai(sender_email, receiver_emails, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {', '.join(receiver_emails)}")
    except Exception as e:
        print(f"An error occurred while sneding email: {e}")

if __name__ == '__main__':
    vimeo_client = initialize_vimeo_client(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN)

    if vimeo_client:
        all_analytics_data = []
        
        # Define the cutoff date: videos created after this date will be processed.
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        print(f"Fetching videos from 'Worship Services' folder (ID: {WORSHIP_SERVICES_FOLDER_ID})...")
        # Pass the cutoff date to the function for optimization
        videos_in_folder = get_videos_from_folder(vimeo_client, WORSHIP_SERVICES_FOLDER_ID, one_week_ago)
        
        # Now that we have a smaller list, filter it to get only the recent videos
        recent_videos = [
            v for v in videos_in_folder 
            if datetime.fromisoformat(v['created_time'].replace('Z', '+00:00')) > one_week_ago
        ]
        
        if recent_videos:
            print(f"Found {len(recent_videos)} video(s) uploaded in the last week to process.")

            for video in recent_videos:
                video_id = video['uri'].split('/')[-1]
                print(f"\nFetching analytics for video ID: {video_id} ('{video['name']}')")
                
                analytics_data = get_video_analytics(
                    vimeo_client,
                    video_id=video_id,
                    start_date=START_DATE,
                    end_date=END_DATE,
                    dimensions=DIMENSIONS,
                    metrics=METRICS
                )
                all_analytics_data.extend(analytics_data)

        if all_analytics_data:
            print(f"\nSuccessfully collected {len(all_analytics_data)} total analytics records.")
            
            df = pd.DataFrame(all_analytics_data)
            
            output_dir = 'reports'
            os.makedirs(output_dir, exist_ok=True)
            report_filename = f"vimeo_analytics_report_{END_DATE.strftime('%Y%m%d')}.xlsx"
            full_report_path = os.path.join(output_dir, report_filename)

            try:
                df.to_excel(full_report_path, index=False)
                print(f"\nAnalytics report generated and saved to: {full_report_path}")

                email_subject = f"Vimeo Analytics Report - {END_DATE.strftime('%Y-%m-%d')}"
                email_body = f"Dear team,\n\nPlease find attached the Vimeo analytics report for the period from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}.\n\nThis report includes data for videos uploaded to the 'Worship Services' folder in the last week.\n\nBest Regards,\nAnalytics Bot"
                send_email(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAILS, email_subject, email_body, full_report_path)
            except Exception as e:
                print(f"Error generating Excel report or sending email: {e}")
        else:
            print("\nNo recent analytics data collected. This could be because no new videos were found in the folder for the specified date range.")
    else:
        print("\nVimeo client could not be initialized. Please check your API credentials in your .env file.")