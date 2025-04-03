import smtplib
from email.message import EmailMessage

def enviar_email(destinatario, assunto, mensagem):    
    smtp_servidor = "smtp.gmail.com"
    smtp_porta = 587
    email_usuario = "ademilsonvianatkd@gmail.com"  
    email_senha = "oqzq sdgp baum wmgf"  
    
    email = EmailMessage()
    email["From"] = email_usuario
    email["To"] = destinatario
    email["Subject"] = assunto
    email.set_content(mensagem)

    try:        
        with smtplib.SMTP(smtp_servidor, smtp_porta) as servidor:
            servidor.starttls()  
            servidor.login(email_usuario, email_senha)
            servidor.send_message(email)
            print("Notificação enviada")
    except Exception as e:
        print(f"Falha ao enviar o email: {e}")

destinatario = "ademilson@dominiumfinanceiro.com"
assunto = "Execussão datapipeline"