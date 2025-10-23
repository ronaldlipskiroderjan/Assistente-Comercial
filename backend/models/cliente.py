from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.models.database import db

class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    endereco = Column(String(255), nullable=True)
    preferencias = Column(Text, nullable=True)

    pedidos = relationship('Pedido', backref='cliente', lazy='dynamic', cascade="all, delete-orphan") 

    anotacoes = relationship('AnotacaoCliente', backref='cliente', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Cliente {self.nome} ({self.telefone})>'


class AnotacaoCliente(db.Model):
    __tablename__ = 'anotacoes_cliente'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, db.ForeignKey('clientes.id'), nullable=False)
    texto = Column(Text, nullable=False)
    data_criacao = Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Anotacao Cliente {self.cliente_id}: {self.texto[:20]}...>'