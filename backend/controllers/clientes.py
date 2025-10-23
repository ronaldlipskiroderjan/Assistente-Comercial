from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.cliente import Cliente, AnotacaoCliente
from backend.models.pedido import Pedido
from sqlalchemy.exc import IntegrityError

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/', methods=['POST'])
def criar_cliente():
    data = request.get_json()
    nome = data.get('nome')
    telefone = data.get('telefone')
    email = data.get('email')
    endereco = data.get('endereco')
    preferencias = data.get('preferencias')

    if not nome or not telefone:
        return jsonify({'error': 'Nome e telefone são campos obrigatórios.'}), 400

    try:
        novo_cliente = Cliente(
            nome=nome,
            telefone=telefone,
            email=email,
            endereco=endereco,
            preferencias=preferencias
        )
        db.session.add(novo_cliente)
        db.session.commit()
        return jsonify({'message': 'Cliente criado com sucesso!', 'cliente': {
            'id': novo_cliente.id,
            'nome': novo_cliente.nome,
            'telefone': novo_cliente.telefone,
            'email': novo_cliente.email,
            'endereco': novo_cliente.endereco,
            'preferencias': novo_cliente.preferencias
        }}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Telefone ou e-mail já cadastrado.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    search_term = request.args.get('search', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    clientes_query = Cliente.query

    if search_term:
        clientes_query = clientes_query.filter(
            (Cliente.nome.ilike(f'%{search_term}%')) |
            (Cliente.telefone.ilike(f'%{search_term}%')) |
            (Cliente.email.ilike(f'%{search_term}%'))
        )

    clientes_pagination = clientes_query.paginate(page=page, per_page=per_page, error_out=False)
    clientes = clientes_pagination.items

    clientes_data = []
    for cliente in clientes:
        clientes_data.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': cliente.endereco,
            'preferencias': cliente.preferencias
        })

    return jsonify({
        'clientes': clientes_data,
        'total_pages': clientes_pagination.pages,
        'current_page': clientes_pagination.page,
        'total_items': clientes_pagination.total
    }), 200

@clientes_bp.route('/<int:cliente_id>', methods=['GET'])
def obter_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado.'}), 404

    historico_pedidos = []
    for pedido in cliente.pedidos.order_by(Pedido.data_pedido.desc()).all():
        historico_pedidos.append({
            'id': pedido.id,
            'servicos': pedido.servicos,
            'valor_total': str(pedido.valor_total),
            'status': pedido.status,
            'data_pedido': pedido.data_pedido.isoformat() if pedido.data_pedido else None,
            'data_entrega': pedido.data_entrega.isoformat() if pedido.data_entrega else None
        })

    anotacoes_cliente = []
    if hasattr(cliente, 'anotacoes'):
        for anotacao in cliente.anotacoes.order_by(AnotacaoCliente.data_criacao.desc()).all():
            anotacoes_cliente.append({
                'id': anotacao.id,
                'texto': anotacao.texto,
                'data_criacao': anotacao.data_criacao.isoformat() if anotacao.data_criacao else None
            })


    return jsonify({
        'id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone,
        'email': cliente.email,
        'endereco': cliente.endereco,
        'preferencias': cliente.preferencias,
        'historico_pedidos': historico_pedidos,
        'anotacoes': anotacoes_cliente
    }), 200

@clientes_bp.route('/<int:cliente_id>', methods=['PUT'])
def atualizar_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado.'}), 404

    data = request.get_json()
    
    cliente.nome = data.get('nome', cliente.nome)
    cliente.telefone = data.get('telefone', cliente.telefone)
    cliente.email = data.get('email', cliente.email)
    cliente.endereco = data.get('endereco', cliente.endereco)
    cliente.preferencias = data.get('preferencias', cliente.preferencias)

    try:
        db.session.commit()
        return jsonify({'message': 'Cliente atualizado com sucesso!', 'cliente': {
            'id': cliente.id,
            'nome': cliente.nome,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': cliente.endereco,
            'preferencias': cliente.preferencias
        }}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Telefone ou e-mail já cadastrado para outro cliente.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clientes_bp.route('/<int:cliente_id>', methods=['DELETE'])
def deletar_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado.'}), 404

    try:
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({'message': 'Cliente deletado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clientes_bp.route('/<int:cliente_id>/anotacoes', methods=['POST'])
def adicionar_anotacao_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado.'}), 404

    data = request.get_json()
    texto_anotacao = data.get('texto')

    if not texto_anotacao:
        return jsonify({'error': 'O texto da anotação é obrigatório.'}), 400

    try:
        nova_anotacao = AnotacaoCliente(cliente_id=cliente_id, texto=texto_anotacao)
        db.session.add(nova_anotacao)
        db.session.commit()
        return jsonify({'message': 'Anotação adicionada com sucesso!', 'anotacao': {
            'id': nova_anotacao.id,
            'texto': nova_anotacao.texto,
            'data_criacao': nova_anotacao.data_criacao.isoformat()
        }}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@clientes_bp.route('/<int:cliente_id>/anotacoes/<int:anotacao_id>', methods=['DELETE'])
def deletar_anotacao_cliente(cliente_id, anotacao_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado.'}), 404

    anotacao = AnotacaoCliente.query.filter_by(id=anotacao_id, cliente_id=cliente_id).first()
    if not anotacao:
        return jsonify({'error': 'Anotação não encontrada para este cliente.'}), 404

    try:
        db.session.delete(anotacao)
        db.session.commit()
        return jsonify({'message': 'Anotação deletada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500