import smtplib
from email.message import EmailMessage
from flask import current_app

def send_mail(to_addr:str, subject:str, body_text:str) -> None:
    cfg = current_app.config
    if not cfg.get("MAIL_ENABLED"):
        current_app.logger.warning(f"[MAIL_DISABLED] Would send to {to_addr}: {subject}\n{body_text}")
        return
    msg = EmailMessage()
    msg["From"] = cfg.get("MAIL_FROM", "exterminus.app@gmail.com")
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body_text)
    with smtplib.SMTP(cfg.get("MAIL_HOST"), int(cfg.get("MAIL_PORT", 587))) as s:
        s.starttls()
        user, pwd = cfg.get("MAIL_USERNAME"), cfg.get("MAIL_PASSWORD")
        if user and pwd:
            s.login(user,pwd)
            s.send_message(msg)
