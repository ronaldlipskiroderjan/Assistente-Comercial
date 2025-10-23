from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.database import db
from datetime import datetime 

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'), nullable=False, unique=True) 
    valor_pago = Column(Float, nullable=False)
    forma_pagamento = Column(String(50), nullable=False) 
    data_pagamento = Column(DateTime, default=db.func.current_timestamp())

    pedido = relationship('Pedido', back_populates='pagamento')

    def __repr__(self):
        return f'<Pagamento {self.id} - Pedido {self.pedido_id} - R${self.valor_pago:.2f}>'