import os
import base64
import requests
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from django.core.mail import EmailMultiAlternatives

# ---- Config ----
IMGBB_API_KEY = getattr(settings, "IMGBB_API_KEY", None)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

YOUTUBE_CREDENTIALS_DIR = os.path.join(os.path.dirname(__file__), "youtube_credentials")
CLIENT_SECRETS_FILE = os.path.join(YOUTUBE_CREDENTIALS_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(YOUTUBE_CREDENTIALS_DIR, "token.json")

# ---- ImgBB Upload ----
def upload_to_imgbb(image_file):
    if not IMGBB_API_KEY:
        print("ImgBB API key is missing in settings.")
        return None
    try:
        image_file.seek(0)
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY}
        files = {"image": base64.b64encode(image_file.read()).decode('utf-8')}
        response = requests.post(url, data=payload, timeout=15)
        result = response.json()
        if response.status_code == 200 and result.get("success"):
            return result["data"]["url"]
        else:
            print("ImgBB upload failed:", result.get("error", "Unknown error"))
    except requests.exceptions.RequestException as e:
        print("ImgBB request failed:", e)
    except Exception as e:
        print("Unexpected error during ImgBB upload:", e)
    return None

# ---- YouTube Auth ----
def get_youtube_service():
    """
    Loads saved token.json and refreshes if expired.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                raise Exception("YouTube token refresh failed. Re-generate token.json.") from e
        else:
            raise Exception("No valid YouTube credentials. Run local auth script to generate token.json.")

    return build("youtube", "v3", credentials=creds, static_discovery=False)

# ---- YouTube Upload ----
def upload_video_to_youtube(file_path, title="My Video", description="Uploaded via Waapfolio"):
    try:
        youtube = get_youtube_service()
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "unlisted"}
            },
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        print(f"Video uploaded successfully: {video_url}")
        return video_id, video_url
    except Exception as e:
        print("YouTube upload failed:", e)
        return None, None

# ---- Email via Brevo ----
def send_email(subject, html_content, to_email):
    """
    Send an HTML email using Django's EmailMultiAlternatives.
    SMTP settings (Brevo) must be in settings.py.
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body="",  # plain text fallback
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True, "Email sent successfully"
    except Exception as e:
        print("Email send failed:", e)
        return False, str(e)
