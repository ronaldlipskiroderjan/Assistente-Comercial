from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models.database import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    report_email = Column(String(120), nullable=True)

    def __init__(self, nome, email, senha_texto_claro, report_email=None):
        self.nome = nome
        self.email = email
        self.set_password(senha_texto_claro)
        self.report_email = report_email

    def set_password(self, senha_texto_claro):
        self.senha_hash = generate_password_hash(senha_texto_claro)

    def check_password(self, senha_texto_claro):
        return check_password_hash(self.senha_hash, senha_texto_claro)

    def __repr__(self):
        return f'<Usuario {self.email}>'