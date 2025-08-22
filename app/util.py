import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

def send_otp_email(email, otp):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    subject = "Your OTP Code"
    html_content = f"<p>Your OTP code is <strong>{otp}</strong>. It expires in 5 minutes.</p>"
    sender = {"name": "Waapfolio", "email": "gospele247@gmail.com"}  # Use verified email
    to = [{"email": email}]
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        html_content=html_content,
        subject=subject,
        sender=sender
    )
    
    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("Email sent:", api_response)
        return True
    except ApiException as e:
        print("Error when sending OTP:", e)
        if hasattr(e, 'body'):
            print("Details:", e.body)
        return False
