from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.models.database import db
from backend.models.usuario import Usuario
import os
import secrets
from datetime import timedelta
import atexit
from dotenv import load_dotenv

load_dotenv()

from backend.controllers.clientes import clientes_bp
from backend.controllers.pedidos import pedidos_bp
from backend.controllers.pagamentos import pagamentos_bp
from backend.controllers.relatorios import relatorios_bp
from backend.controllers.auth import auth_bp
from backend.services.scheduler import start_scheduler, stop_scheduler
from backend.config import Config

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)

    app.debug = True 

    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
        print("SECRET_KEY gerada (apenas para desenvolvimento):", app.config['SECRET_KEY'])
    
    db.init_app(app)
   
    CORS(app, supports_credentials=True) 

    app.register_blueprint(clientes_bp, url_prefix='/api/clientes')
    app.register_blueprint(pedidos_bp, url_prefix='/api/pedidos')
    app.register_blueprint(pagamentos_bp, url_prefix='/api/pagamentos')
    app.register_blueprint(relatorios_bp, url_prefix='/api/relatorios')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app

app = create_app()

with app.app_context():
    db.create_all() 
    if Usuario.query.count() == 0:
        print("Nenhum usuário encontrado. Criando usuário admin padrão.")
        admin_user = Usuario(nome="Admin", email="admin@example.com", senha_texto_claro="admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário admin 'admin@example.com' com senha 'admin123' criado. POR FAVOR, MUDE A SENHA EM PRODUÇÃO!")

with app.app_context():
    start_scheduler(app)
    atexit.register(lambda: stop_scheduler())

if __name__ == '__main__':
    app.run(debug=True, port=5000)