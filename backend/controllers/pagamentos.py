from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.pagamento import Pagamento
from backend.models.pedido import Pedido
from backend.models.cliente import Cliente
from sqlalchemy.exc import IntegrityError
import os
from datetime import datetime, timedelta
import decimal
import csv

pagamentos_bp = Blueprint('pagamentos', __name__)

OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'output')
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@pagamentos_bp.route('/', methods=['POST'])
def registrar_pagamento():
    data = request.get_json()
    pedido_id = data.get('pedido_id')
    valor_pago = data.get('valor_pago')
    forma_pagamento = data.get('forma_pagamento')

    if not all([pedido_id, valor_pago, forma_pagamento]):
        return jsonify({'error': 'ID do pedido, valor pago e forma de pagamento são obrigatórios.'}), 400

    try:
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado.'}), 404
        
        valor_pago_decimal = decimal.Decimal(str(valor_pago))

        if pedido.status == 'pago':
             return jsonify({'error': 'Este pedido já foi pago.'}), 409

        if valor_pago_decimal < decimal.Decimal(str(pedido.valor_total)):
            return jsonify({'error': 'O valor pago é menor que o valor total do pedido. Este módulo assume pagamentos completos. Para pagamentos parciais, a lógica precisaria ser expandida.'}), 400

        new_pagamento = Pagamento(
            pedido_id=pedido_id,
            valor_pago=valor_pago_decimal,
            forma_pagamento=forma_pagamento
        )
        db.session.add(new_pagamento)

        pedido.status = 'pago'
        db.session.commit()

        return jsonify({'message': 'Pagamento registrado com sucesso!', 'pagamento': {
            'id': new_pagamento.id,
            'pedido_id': new_pagamento.pedido_id,
            'valor_pago': str(new_pagamento.valor_pago),
            'forma_pagamento': new_pagamento.forma_pagamento,
            'data_pagamento': new_pagamento.data_pagamento.isoformat()
        }}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Este pedido já possui um pagamento registrado.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pagamentos_bp.route('/<int:pagamento_id>/recibo', methods=['GET'])
def gerar_recibo(pagamento_id):
    pagamento = Pagamento.query.get(pagamento_id)
    if not pagamento:
        return jsonify({'error': 'Pagamento não encontrado.'}), 404

    pedido = Pedido.query.get(pagamento.pedido_id)
    if not pedido:
        return jsonify({'error': 'Pedido associado ao pagamento não encontrado.'}), 404

    cliente = Cliente.query.get(pedido.cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente associado ao pedido não encontrado.'}), 404


    recibo_info = {
        'id_pagamento': pagamento.id,
        'valor_pago': str(pagamento.valor_pago),
        'forma_pagamento': pagamento.forma_pagamento,
        'data_pagamento': pagamento.data_pagamento.isoformat(),
        'cliente_nome': cliente.nome,
        'servico_descricao': pedido.servicos
    }
    return jsonify({'message': 'Geração de recibo em PDF foi desativada. Informações do recibo:', 'recibo_data': recibo_info}), 200

@pagamentos_bp.route('/historico', methods=['GET'])
def historico_financeiro():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    forma_pagamento = request.args.get('forma_pagamento')
    
    query = Pagamento.query.order_by(Pagamento.data_pagamento.desc())

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Pagamento.data_pagamento >= start_date)
        except ValueError:
            return jsonify({'error': 'Formato de data inicial inválido. Use<ctrl42>-MM-DD.'}), 400

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Pagamento.data_pagamento < end_date)
        except ValueError:
            return jsonify({'error': 'Formato de data final inválido. Use<ctrl42>-MM-DD.'}), 400
    
    if forma_pagamento:
        query = query.filter(Pagamento.forma_pagamento.ilike(f'%{forma_pagamento}%'))

    pagamentos = query.all()

    historico = []
    for pgto in pagamentos:
        pedido = Pedido.query.get(pgto.pedido_id)
        cliente_nome = pedido.cliente.nome if pedido and pedido.cliente else 'N/A'
        historico.append({
            'id': pgto.id,
            'pedido_id': pgto.pedido_id,
            'cliente_nome': cliente_nome,
            'valor_pago': str(pgto.valor_pago),
            'forma_pagamento': pgto.forma_pagamento,
            'data_pagamento': pgto.data_pagamento.isoformat()
        })
    return jsonify(historico), 200

@pagamentos_bp.route('/exportar', methods=['GET'])
def exportar_historico_financeiro():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    forma_pagamento = request.args.get('forma_pagamento')

    query = Pagamento.query.order_by(Pagamento.data_pagamento.desc())

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Pagamento.data_pagamento >= start_date)
        except ValueError:
            return jsonify({'error': 'Formato de data inicial inválido. Use<ctrl42>-MM-DD.'}), 400

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Pagamento.data_pagamento < end_date)
        except ValueError:
            return jsonify({'error': 'Formato de data final inválido. Use<ctrl42>-MM-DD.'}), 400
    
    if forma_pagamento:
        query = query.filter(Pagamento.forma_pagamento.ilike(f'%{forma_pagamento}%'))

    pagamentos = query.all()

    csv_filename = "historico_financeiro.csv"
    csv_path = os.path.join(OUTPUT_FOLDER, csv_filename) # Salva na pasta OUTPUT_FOLDER

    with open(csv_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID Pagamento', 'ID Pedido', 'Nome Cliente', 'Valor Pago', 'Forma de Pagamento', 'Data Pagamento'])
        for pgto in pagamentos:
            pedido = Pedido.query.get(pgto.pedido_id)
            cliente_nome = pedido.cliente.nome if pedido and pedido.cliente else 'N/A'
            writer.writerow([
                pgto.id,
                pgto.pedido_id,
                cliente_nome,
                str(pgto.valor_pago),
                pgto.forma_pagamento,
                pgto.data_pagamento.isoformat()
            ])
    
    return jsonify({'message': f'Histórico financeiro exportado para: {csv_path}'}), 200