from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.models.database import db
from datetime import datetime

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    servicos = Column(Text, nullable=False)
    valor_total = Column(Float, nullable=False)
    status = Column(String(50), default='pendente', nullable=False) 
    data_pedido = Column(DateTime, default=datetime.now(), nullable=False)
    data_entrega = Column(DateTime, nullable=True) 

    pagamento = relationship('Pagamento', back_populates='pedido', uselist=False)

    def __repr__(self):
        return f'<Pedido {self.id} - Cliente {self.cliente_id} - Status: {self.status}>'