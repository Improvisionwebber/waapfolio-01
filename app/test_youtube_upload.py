import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video(file_path, title, description="", tags=None, privacy_status="unlisted"):
    # OAuth Authentication
    creds = None
    token_file = "youtube_credentials/token.json"

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "youtube_credentials/client_secret.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    # Build YouTube service
    youtube = build('youtube', 'v3', credentials=creds)

    # Prepare video
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
            },
            "status": {
                "privacyStatus": privacy_status
            }
        },
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return video_id, video_url

if __name__ == "__main__":
    video_file = "test_video.mp4"  # Path to your test video
    title = "Test Upload Video"
    description = "This is a test upload from Python"
    
    video_id, video_url = upload_video(video_file, title, description)
    print("Uploaded Video ID:", video_id)
    print("YouTube URL:", video_url)
