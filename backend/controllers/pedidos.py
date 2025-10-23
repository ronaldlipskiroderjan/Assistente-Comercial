from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.pedido import Pedido
from backend.models.cliente import Cliente
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import decimal

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/', methods=['POST'])
def criar_pedido():
    data = request.get_json()
    cliente_id = data.get('cliente_id')
    servicos = data.get('servicos')
    valor_total = data.get('valor_total')
    status = data.get('status', 'pendente')
    data_entrega_str = data.get('data_entrega')

    if not all([cliente_id, servicos, valor_total]):
        return jsonify({'error': 'ID do cliente, serviços e valor total são obrigatórios.'}), 400

    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado.'}), 404
    
    data_entrega = None
    if data_entrega_str:
        try:
            data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data de entrega inválido. Use<ctrl42>-MM-DD.'}), 400

    try:
        novo_pedido = Pedido(
            cliente_id=cliente_id,
            servicos=servicos,
            valor_total=decimal.Decimal(str(valor_total)),
            status=status,
            data_entrega=data_entrega
        )
        db.session.add(novo_pedido)
        db.session.commit()
        return jsonify({'message': 'Pedido criado com sucesso!', 'pedido': {
            'id': novo_pedido.id,
            'cliente_id': novo_pedido.cliente_id,
            'servicos': novo_pedido.servicos,
            'valor_total': str(novo_pedido.valor_total),
            'status': novo_pedido.status,
            'data_pedido': novo_pedido.data_pedido.isoformat(),
            'data_entrega': novo_pedido.data_entrega.isoformat() if novo_pedido.data_entrega else None
        }}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pedidos_bp.route('/', methods=['GET'])
def listar_pedidos():
    status_filter = request.args.get('status')
    cliente_id_filter = request.args.get('cliente_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Pedido.query.order_by(Pedido.data_pedido.desc())

    if status_filter:
        query = query.filter_by(status=status_filter)
    if cliente_id_filter:
        query = query.filter_by(cliente_id=cliente_id_filter)

    pedidos_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    pedidos = pedidos_pagination.items

    pedidos_data = []
    for pedido in pedidos:
        cliente_nome = pedido.cliente.nome if pedido.cliente else 'N/A'
        pedidos_data.append({
            'id': pedido.id,
            'cliente_id': pedido.cliente_id,
            'cliente_nome': cliente_nome,
            'servicos': pedido.servicos,
            'valor_total': str(pedido.valor_total),
            'status': pedido.status,
            'data_pedido': pedido.data_pedido.isoformat(),
            'data_entrega': pedido.data_entrega.isoformat() if pedido.data_entrega else None,
            'dias_para_entrega': (pedido.data_entrega.date() - datetime.now().date()).days if pedido.data_entrega and pedido.status != 'entregue' else None
        })
    return jsonify({
        'pedidos': pedidos_data,
        'total_pages': pedidos_pagination.pages,
        'current_page': pedidos_pagination.page,
        'total_items': pedidos_pagination.total
    }), 200

@pedidos_bp.route('/<int:pedido_id>', methods=['GET'])
def obter_pedido(pedido_id):
    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'error': 'Pedido não encontrado.'}), 404

    cliente_nome = pedido.cliente.nome if pedido.cliente else 'N/A'
    
    dias_para_entrega = None
    if pedido.data_entrega and pedido.status != 'entregue':
        dias_para_entrega = (pedido.data_entrega.date() - datetime.now().date()).days

    return jsonify({
        'id': pedido.id,
        'cliente_id': pedido.cliente_id,
        'cliente_nome': cliente_nome,
        'servicos': pedido.servicos,
        'valor_total': str(pedido.valor_total),
        'status': pedido.status,
        'data_pedido': pedido.data_pedido.isoformat(),
        'data_entrega': pedido.data_entrega.isoformat() if pedido.data_entrega else None,
        'dias_para_entrega': dias_para_entrega,
        'pagamento_registrado': bool(pedido.pagamento)
    }), 200

@pedidos_bp.route('/<int:pedido_id>', methods=['PUT'])
def atualizar_pedido(pedido_id):
    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'error': 'Pedido não encontrado.'}), 404

    data = request.get_json()
    
    if 'cliente_id' in data:
        cliente_id = data.get('cliente_id')
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado.'}), 404
        pedido.cliente_id = cliente_id

    pedido.servicos = data.get('servicos', pedido.servicos)
    
    if 'valor_total' in data:
        pedido.valor_total = decimal.Decimal(str(data.get('valor_total')))

    new_status = data.get('status', pedido.status)
    if new_status not in ['pendente', 'pago', 'entregue', 'cancelado']:
        return jsonify({'error': 'Status inválido. Use pendente, pago, entregue ou cancelado.'}), 400
    pedido.status = new_status

    if 'data_entrega' in data:
        data_entrega_str = data.get('data_entrega')
        if data_entrega_str:
            try:
                pedido.data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Formato de data de entrega inválido. Use<ctrl42>-MM-DD.'}), 400
        else:
            pedido.data_entrega = None

    try:
        db.session.commit()
        return jsonify({'message': 'Pedido atualizado com sucesso!', 'pedido': {
            'id': pedido.id,
            'cliente_id': pedido.cliente_id,
            'servicos': pedido.servicos,
            'valor_total': str(pedido.valor_total),
            'status': pedido.status,
            'data_pedido': pedido.data_pedido.isoformat(),
            'data_entrega': pedido.data_entrega.isoformat() if pedido.data_entrega else None
        }}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pedidos_bp.route('/<int:pedido_id>', methods=['DELETE'])
def deletar_pedido(pedido_id):
    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'error': 'Pedido não encontrado.'}), 404

    try:
        if pedido.pagamento:
            db.session.delete(pedido.pagamento)

        db.session.delete(pedido)
        db.session.commit()
        return jsonify({'message': 'Pedido deletado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pedidos_bp.route('/prazos', methods=['GET'])
def verificar_prazos():
    dias_futuros = request.args.get('dias_futuros', 7, type=int)
    hoje = datetime.now().date()
    data_limite = hoje + timedelta(days=dias_futuros)

    pedidos_com_prazos = Pedido.query.filter(
        Pedido.data_entrega.isnot(None),
        Pedido.data_entrega >= hoje,
        Pedido.data_entrega <= data_limite,
        Pedido.status.in_(['pendente', 'pago'])
    ).order_by(Pedido.data_entrega.asc()).all()

    prazos_data = []
    for pedido in pedidos_com_prazos:
        cliente_nome = pedido.cliente.nome if pedido.cliente else 'N/A'
        dias_restantes = (pedido.data_entrega.date() - hoje).days
        prazos_data.append({
            'id': pedido.id,
            'cliente_id': pedido.cliente_id,
            'cliente_nome': cliente_nome,
            'servicos': pedido.servicos,
            'status': pedido.status,
            'data_entrega': pedido.data_entrega.isoformat(),
            'dias_restantes': dias_restantes
        })
    return jsonify(prazos_data), 200 