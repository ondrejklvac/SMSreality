import os

class Config:
    SECRET_KEY = 'tajny-klic-pro-zabezpeceni-aplikace'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///eshop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
    MAIL_SERVER = 'smtp.gmail.com'  # Nastavte podle vašeho poskytovatele e-mailu
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'vas-email@gmail.com'  # Změňte na váš e-mail
    MAIL_PASSWORD = 'vase-heslo'  # Změňte na vaše heslo
    MAIL_DEFAULT_SENDER = 'vas-email@gmail.com'  # Změňte na váš e-mail