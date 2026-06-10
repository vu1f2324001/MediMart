import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, ADMIN_EMAIL
import random
from datetime import datetime, timedelta

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [to_email], msg.as_string())
    except Exception as e:
        print('Email Error:', e)

def send_order_email(user_email, order_details):
    msg = EmailMessage()
    msg['Subject'] = '📦 New Order Placed'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ADMIN_EMAIL
    msg.set_content(f'''
Hello Admin,

A new order has been placed!

👤 Customer: {user_email}
🛍️ Order Summary:
{order_details}

Please check the admin dashboard for full details.

Thanks,
Your Website Bot 🤖
''')

    # Send email via Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_delivery_otp_email(user_email, otp):
    """Send delivery OTP to user"""
    msg = EmailMessage()
    msg['Subject'] = '📦 Delivery OTP - Confirm Medicine Delivery'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = user_email
    msg.set_content(f'''
Hello,

Your order has been marked as delivered!

Please provide this OTP to the delivery person to confirm successful delivery:

🔐 OTP: {otp}

This OTP is valid for 24 hours.

If you did not receive your order or have any issues, please contact our support team.

Thank you for choosing our pharmacy!

Best regards,
Pharma Team
''')

    # Send email via Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def send_prescription_delivery_otp_email(user_email, otp):
    """Send prescription delivery OTP to user"""
    msg = EmailMessage()
    msg['Subject'] = '📋 Prescription Delivery OTP - Confirm Medicine Receipt'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = user_email
    msg.set_content(f'''
Hello,

Your prescription medicines have been marked as delivered!

Please provide this OTP to confirm that you have received your prescription medicines:

🔐 OTP: {otp}

This OTP is valid for 24 hours.

If you did not receive your prescription medicines or have any issues, please contact our support team.

Thank you for choosing our pharmacy!

Best regards,
Pharma Team
''')

    # Send email via Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
