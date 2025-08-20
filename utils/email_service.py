import requests

BREVO_API_KEY = "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"
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def send_email(subject, html_content, to_email):
    """
    Send an email via Brevo SMTP API.
    
    Args:
        subject (str): Subject of the email.
        html_content (str): HTML content of the email.
        to_email (str): Recipient's email address.
        
    Returns:
        tuple: (status_code, response_text) from the API request.
    """
    payload = {
        "sender": {
            "name": "WAAP FOLIO",
            "email": "emzyjunior73@gmail.com"  # Your verified sender email
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    response = requests.post(BREVO_API_URL, json=payload, headers=headers)
    return response.status_code, response.text
