from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.usuario import Usuario
from sqlalchemy.exc import IntegrityError
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email').lower()
    senha_texto_claro = data.get('senha')

    if not all([nome, email, senha_texto_claro]):
        return jsonify({'error': 'Nome, e-mail e senha são obrigatórios'}), 400

   
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        return jsonify({'error': 'Formato de e-mail inválido.'}), 400
    

    try:
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'error': 'E-mail já registrado.'}), 409

        new_user = Usuario(nome=nome, email=email, senha_texto_claro=senha_texto_claro)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Usuário registrado com sucesso!', 'user_id': new_user.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Erro ao registrar usuário: e-mail já existente.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email').lower() 
    senha_texto_claro = data.get('senha')

    if not all([email, senha_texto_claro]):
        return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400

    
    user = Usuario.query.filter_by(email=email).first()

    if user and user.check_password(senha_texto_claro):
        
        return jsonify({'message': 'Login bem-sucedido!', 'user_id': user.id, 'user_nome': user.nome, 'user_email': user.email}), 200
    else:
        return jsonify({'error': 'E-mail ou senha inválidos'}), 401
