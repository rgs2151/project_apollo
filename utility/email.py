import smtplib, traceback as tb, re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class EmailSendException(Exception): pass


def check_email(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def check_smtp_credentials(login_username, login_password):
    
    trace = None
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(login_username, login_password)
        
    except Exception as err:
        trace = ''.join(tb.format_exception(None, err, err.__traceback__))
    
    finally:
        server.quit()

    return trace


def send_email(
    login_username,
    login_password, 
    from_email, 
    to_emails, 
    cc_emails, 
    subject,
    message, 
    attachment_path=None,
    attachment_image_path=None
):
  
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(to_emails)
    msg['Cc'] = ', '.join(cc_emails)
    msg['Subject'] = subject


    # Attach the file if provided
    if attachment_path:
        for file in attachment_path:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file[1].read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename={file[0]}')
            msg.attach(attachment)
    
    
    # Attach image with content-ids | index will be taken as content id
    if attachment_image_path:
        for i, file in enumerate(attachment_image_path):
            attachment = MIMEBase('image', 'png')
            attachment.set_payload(file[1].read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'inline; filename={file[0]}')
            attachment.add_header('Content-ID', f'<image{i}>')
            msg.attach(attachment)
    
    
    # Attach the message
    msg.attach(MIMEText(message, 'html'))
    

    # Connect to the SMTP server and send the email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(login_username, login_password)
        server.sendmail(from_email, to_emails + cc_emails, msg.as_string())
    
    except Exception as err: EmailSendException("error sending email")
        
    finally:
        server.quit()