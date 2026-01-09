# ===== app/services/email_service.py =====
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio de email usando Gmail SMTP gratuito"""
    
    @staticmethod
    def create_smtp_connection():
        """Crear conexión SMTP"""
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            return server
        except Exception as e:
            logger.error(f"❌ Error conectando a SMTP: {e}")
            return None
    
    @staticmethod
    async def send_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Enviar email"""
        try:
            server = EmailService.create_smtp_connection()
            if not server:
                return False
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            
            # Agregar contenido de texto plano
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Agregar contenido HTML
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Enviar
            text = msg.as_string()
            server.sendmail(settings.FROM_EMAIL, to_emails, text)
            server.quit()
            
            logger.info(f"✅ Email enviado exitosamente a {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return False
        
    @staticmethod
    async def send_verification_code_email(
        email: str, 
        code: str, 
        user_name: str = "",
        expires_minutes: int = 15
    ) -> bool:
        """Enviar email con código de verificación accesible"""
        
        subject = "Código de Verificación - App Accesible"
        
        # Formatear código para mejor lectura por TTS (espaciado)
        spaced_code = ' '.join(code)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 30px 20px; text-align: center; border-radius: 12px 12px 0 0; }}
                .content {{ padding: 30px 20px; background: white; }}
                .code-container {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px; 
                    text-align: center; 
                    border-radius: 16px;
                    margin: 30px 0;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                }}
                .verification-code {{ 
                    font-size: 48px; 
                    font-weight: bold; 
                    color: white;
                    letter-spacing: 12px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                    margin: 20px 0;
                    font-family: 'Courier New', monospace;
                }}
                .code-label {{
                    color: white;
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                .accessible-info {{ 
                    background-color: #f0f9ff; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-left: 4px solid #2563eb;
                    border-radius: 8px;
                }}
                .info-box {{
                    background-color: #fef3c7;
                    padding: 15px;
                    border-left: 4px solid #f59e0b;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                ul {{
                    list-style: none;
                    padding-left: 0;
                }}
                li {{
                    padding: 8px 0;
                }}
                li:before {{
                    content: "✓ ";
                    color: #16a34a;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Código de Verificación</h1>
                </div>
                
                <div class="content">
                    <p>Hola{"" if not user_name else f" {user_name}"},</p>
                    
                    <p style="font-size: 17px;">Tu código de verificación para activar tu cuenta es:</p>
                    
                    <div class="code-container">
                        <div class="code-label">TU CÓDIGO ES:</div>
                        <div class="verification-code">
                            {code}
                        </div>
                        <p style="color: white; margin-top: 15px; font-size: 14px;">
                            ⏱️ Válido por {expires_minutes} minutos
                        </p>
                    </div>
                    
                    <div class="accessible-info">
                        <h3 style="margin-top: 0; color: #2563eb;">📱 Para usuarios de lectores de pantalla:</h3>
                        <p style="font-size: 16px;">
                            El código es: <strong style="font-size: 18px; letter-spacing: 4px;">{spaced_code}</strong>
                        </p>
                    </div>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #f59e0b;">⚠️ Importante:</h3>
                        <ul>
                            <li>No compartas este código con nadie</li>
                            <li>El código expira en {expires_minutes} minutos</li>
                            <li>Tienes 5 intentos para ingresar el código correcto</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
    Código de Verificación

    Hola{"" if not user_name else f" {user_name}"},

    Tu código de verificación es: {code}
    (Espaciado: {spaced_code})

    Válido por {expires_minutes} minutos.
    Tienes 5 intentos para ingresarlo.

    No compartas este código con nadie.
        """
        
        return await EmailService.send_email([email], subject, html_content, text_content)

    @staticmethod
    async def send_verification_email(email: str, token: str, user_name: str = "") -> bool:
        """Enviar email de verificación accesible"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        subject = "Verificación de cuenta - App Accesible"
        
        # Contenido accesible para lectores de pantalla
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    background-color: #16a34a; 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .accessible-info {{ background-color: #f3f4f6; padding: 15px; margin: 20px 0; border-left: 4px solid #2563eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header" role="banner">
                    <h1>¡Bienvenido{"" if not user_name else f", {user_name}"}!</h1>
                </div>
                
                <div class="content" role="main">
                    <h2>Verificación de Cuenta</h2>
                    <p>Gracias por registrarte en nuestra aplicación accesible. Para completar tu registro, necesitas verificar tu dirección de email.</p>
                    
                    <div class="accessible-info" role="complementary">
                        <h3>Para usuarios de lectores de pantalla:</h3>
                        <p>Este email contiene un enlace de verificación. También puedes copiar y pegar el siguiente enlace en tu navegador:</p>
                        <p><strong>{verification_url}</strong></p>
                    </div>
                    
                    <p>Haz clic en el siguiente botón para verificar tu cuenta:</p>
                    
                    <a href="{verification_url}" class="button" role="button" aria-label="Verificar cuenta de email">
                        Verificar Mi Cuenta
                    </a>
                    
                    <p>Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:</p>
                    <p>{verification_url}</p>
                    
                    <p><small>Este enlace expirará en 24 horas por seguridad.</small></p>
                    
                    <hr>
                    <p><small>Si no creaste una cuenta, puedes ignorar este email de forma segura.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Versión de texto plano para lectores de pantalla
        text_content = f"""
        ¡Bienvenido{"" if not user_name else f", {user_name}"}!
        
        Verificación de Cuenta
        
        Gracias por registrarte en nuestra aplicación accesible. Para completar tu registro, necesitas verificar tu dirección de email.
        
        Copia y pega el siguiente enlace en tu navegador para verificar tu cuenta:
        {verification_url}
        
        Este enlace expirará en 24 horas por seguridad.
        
        Si no creaste una cuenta, puedes ignorar este email de forma segura.
        """
        
        return await EmailService.send_email([email], subject, html_content, text_content)
    
    @staticmethod
    async def send_password_reset_email(email: str, token: str, user_name: str = "") -> bool:
        """Enviar email de reseteo de contraseña accesible"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        subject = "Reseteo de Contraseña - App Accesible"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    background-color: #dc2626; 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .accessible-info {{ background-color: #fef3c7; padding: 15px; margin: 20px 0; border-left: 4px solid #f59e0b; }}
                .security-warning {{ background-color: #fee2e2; padding: 15px; margin: 20px 0; border-left: 4px solid #dc2626; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header" role="banner">
                    <h1>Reseteo de Contraseña</h1>
                </div>
                
                <div class="content" role="main">
                    <p>Hola{"" if not user_name else f" {user_name}"},</p>
                    
                    <p>Recibimos una solicitud para resetear la contraseña de tu cuenta. Si no hiciste esta solicitud, puedes ignorar este email de forma segura.</p>
                    
                    <div class="security-warning" role="alert">
                        <h3>⚠️ Importante por Seguridad:</h3>
                        <p>Solo haz clic en este enlace si solicitaste un reseteo de contraseña. Este enlace te permitirá cambiar tu contraseña.</p>
                    </div>
                    
                    <div class="accessible-info" role="complementary">
                        <h3>Para usuarios de lectores de pantalla:</h3>
                        <p>Este email contiene un enlace seguro para resetear tu contraseña. También puedes copiar y pegar el siguiente enlace:</p>
                        <p><strong>{reset_url}</strong></p>
                    </div>
                    
                    <a href="{reset_url}" class="button" role="button" aria-label="Resetear mi contraseña de forma segura">
                        Resetear Mi Contraseña
                    </a>
                    
                    <p>Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:</p>
                    <p>{reset_url}</p>
                    
                    <p><small>Este enlace expirará en 1 hora por seguridad.</small></p>
                    
                    <hr>
                    <p><small>Si no solicitaste este reseteo, tu cuenta sigue siendo segura. Puedes ignorar este email.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reseteo de Contraseña
        
        Hola{"" if not user_name else f" {user_name}"},
        
        Recibimos una solicitud para resetear la contraseña de tu cuenta. Si no hiciste esta solicitud, puedes ignorar este email de forma segura.
        
        IMPORTANTE POR SEGURIDAD:
        Solo usa este enlace si solicitaste un reseteo de contraseña.
        
        Copia y pega el siguiente enlace en tu navegador para resetear tu contraseña:
        {reset_url}
        
        Este enlace expirará en 1 hora por seguridad.
        
        Si no solicitaste este reseteo, tu cuenta sigue siendo segura. Puedes ignorar este email.
        """
        
        return await EmailService.send_email([email], subject, html_content, text_content)

email_service = EmailService()

