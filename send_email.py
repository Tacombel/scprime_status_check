import smtplib, ssl
from email.message import EmailMessage
from config_local import Config

def send_email(subject, content):
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = Config.email
    msg['To'] = Config.dest_email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", Config.port, context=context) as server:
        server.login(Config.email, Config.password)
        server.send_message(msg)

if __name__=='__main__':
    send_email('Prueba', 'Hola')
