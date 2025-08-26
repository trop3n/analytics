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
CLIENT_ID = os.environ.get('VIMEO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VIMEO_CLIENT_SECRET')
ACCESS_TOKEN = os.environ.get('VIMEO_ACCESS_TOKEN')

# --- Email Configuration ---
SENDER_EMAIL = os.environ.get("OUTLOOK_ACCOUNT")
SENDER_PASSWORD = os.environ.get("OUTLOOK_PASS")
RECEIVER_EMAILS = os.environ.get("RECEIVER_EMAILS", "").split(',')
SMTP_SERVER = 'smtp.office365.com'
SMTP_PORT = 587

# --- Analytics Parameters ---
WORSHIP_SERVICES_FOLDER_ID = '15749517' # The ID for "Worship Services"

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
    """Fetches videos from a specific Vimeo folder created after the cutoff_date."""
    if not client:
        print("Vimeo client is not initialized.")
        return []

    videos = []
    page = 1
    per_page = 100

    while True:
        try:
            uri = f'/me/projects/{folder_id}/videos'
            response = client.get(uri, params={'per_page': per_page, 'page': page, 'sort': 'date', 'direction': 'desc'})

            if response.status_code == 200:
                data = response.json()
                page_videos = data.get('data', [])
                if not page_videos:
                    break
                
                videos.extend(page_videos)

                last_video_date = datetime.fromisoformat(page_videos[-1]['created_time'].replace('Z', '+00:00'))
                if last_video_date < cutoff_date:
                    print("  Found videos older than the cutoff date. Stopping pagination.")
                    break

                if data.get('paging', {}).get('next'):
                    page += 1
                else:
                    break
            else:
                print(f"Error fetching videos from folder {folder_id}. Status: {response.status_code} - {response.text}")
                break
        except Exception as e:
            print(f"An unexpected error occurred while fetching videos: {e}")
            break
    return videos

def get_simple_video_stats(client, video_id):
    """
    Fetches basic stats (like total plays) for a single video.
    This is a fallback for when the detailed /analytics endpoint is not enabled.
    """
    if not client:
        return None
    
    try:
        uri = f'/videos/{video_id}'
        response = client.get(uri, params={'fields': 'name,link,stats.plays,created_time'})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  -> Error fetching stats for video {video_id} (Status: {response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"  -> An unexpected error occurred during API call for video {video_id}: {e}")
        return None

def send_email(sender_email, sender_password, receiver_emails, subject, body, attachment_path=None):
    """Sends an email with an optional attachment."""
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
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)
            print(f"Attached file: {os.path.basename(attachment_path)}")
        except Exception as e:
            print(f"Error attaching file {attachment_path}: {e}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {', '.join(receiver_emails)}")
    except Exception as e:
        print(f"An error occurred while sending email: {e}")

if __name__ == '__main__':
    vimeo_client = initialize_vimeo_client(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN)

    if vimeo_client:
        report_data = []
        
        # Set the date range to capture videos from the last week.
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        print(f"Fetching videos from 'Worship Services' folder (ID: {WORSHIP_SERVICES_FOLDER_ID})...")
        videos_in_folder = get_videos_from_folder(vimeo_client, WORSHIP_SERVICES_FOLDER_ID, one_week_ago)
        
        recent_videos = [
            v for v in videos_in_folder 
            if datetime.fromisoformat(v['created_time'].replace('Z', '+00:00')) > one_week_ago
        ]
        
        if recent_videos:
            print(f"Found {len(recent_videos)} video(s) uploaded in the last week to process.")

            for video in recent_videos:
                video_id = video['uri'].split('/')[-1]
                print(f"\nFetching stats for video ID: {video_id} ('{video['name']}')")
                
                stats_data = get_simple_video_stats(vimeo_client, video_id)
                
                if stats_data:
                    report_data.append({
                        'Video Name': stats_data.get('name', 'N/A'),
                        'Total Plays': stats_data.get('stats', {}).get('plays', 0),
                        'Upload Date': datetime.fromisoformat(stats_data['created_time'].replace('Z', '+00:00')).strftime('%Y-%m-%d'),
                        'Link': stats_data.get('link', 'N/A')
                    })

        if report_data:
            print(f"\nSuccessfully collected stats for {len(report_data)} video(s).")
            
            df = pd.DataFrame(report_data)
            
            output_dir = 'reports'
            os.makedirs(output_dir, exist_ok=True)
            report_filename = f"vimeo_total_plays_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            full_report_path = os.path.join(output_dir, report_filename)

            try:
                df.to_excel(full_report_path, index=False)
                print(f"\nAnalytics report generated and saved to: {full_report_path}")

                email_subject = f"Vimeo Weekly Plays Report - {datetime.now().strftime('%Y-%m-%d')}"
                email_body = (
                    "Dear team,\n\n"
                    "Please find attached the weekly Vimeo 'Total Plays' report for videos uploaded to the 'Worship Services' folder in the last 7 days.\n\n"
                    "NOTE: This is a basic report. To get detailed analytics (like watch time, impressions, etc.), the 'Analytics API' feature must be enabled for our account by our Vimeo account manager.\n\n"
                    "Best Regards,\n"
                    "Analytics Bot"
                )
                send_email(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAILS, email_subject, email_body, full_report_path)
            except Exception as e:
                print(f"Error generating Excel report or sending email: {e}")
        else:
            print("\nNo data collected for recent videos.")
    else:
        print("\nVimeo client could not be initialized. Please check your API credentials.")