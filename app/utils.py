import requests

IMGBB_API_KEY = "c346e6e29bbc0340846deb957f6d510a"

def upload_to_imgbb(image_file):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": IMGBB_API_KEY}
    files = {"image": image_file.read()}
    response = requests.post(url, data=payload, files=files)
    result = response.json()
    if response.status_code == 200 and result.get("success"):
        return result["data"]["url"]
    return None
