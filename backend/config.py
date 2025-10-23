import os
import secrets
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-padrao-para-dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///assistente.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = True 

    SCHEDULER_API_ENABLED = True

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_urlsafe(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)