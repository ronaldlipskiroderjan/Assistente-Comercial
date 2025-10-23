from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.pedido import Pedido
from backend.models.cliente import Cliente
from backend.models.pagamento import Pagamento
from backend.config import Config
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from collections import defaultdict
import os
import decimal

relatorios_bp = Blueprint('relatorios', __name__)

def calcular_metricas_semanais():
    hoje = datetime.now()
    dias_para_ultima_segunda = hoje.weekday() + 7
    data_inicio_semana = hoje - timedelta(days=dias_para_ultima_segunda)
    data_fim_semana = data_inicio_semana + timedelta(days=6)

    data_inicio_periodo = datetime(data_inicio_semana.year, data_inicio_semana.month, data_inicio_semana.day, 0, 0, 0)
    data_fim_periodo = datetime(data_fim_semana.year, data_fim_semana.month, data_fim_semana.day, 23, 59, 59)

    pedidos_semanais = Pedido.query.filter(
        Pedido.data_pedido >= data_inicio_periodo,
        Pedido.data_pedido <= data_fim_periodo,
        Pedido.status.in_(['pago', 'entregue'])
    ).all()

    total_vendas = decimal.Decimal('0.00')
    clientes_atendidos = set()
    servicos_contagem = defaultdict(int)

    for pedido in pedidos_semanais:
        total_vendas += decimal.Decimal(str(pedido.valor_total))
        clientes_atendidos.add(pedido.cliente_id)
        servicos_contagem[pedido.servicos] += 1

    servicos_mais_vendidos = sorted(servicos_contagem.items(), key=lambda item: item[1], reverse=True)[:5]
    lucro_estimado = total_vendas * decimal.Decimal('0.70')

    return {
        'total_vendas': str(total_vendas.quantize(decimal.Decimal('0.01'))),
        'clientes_atendidos_count': len(clientes_atendidos),
        'servicos_mais_vendidos': servicos_mais_vendidos,
        'lucro_estimado': str(lucro_estimado.quantize(decimal.Decimal('0.01'))),
        'data_inicio': data_inicio_periodo.strftime('%d/%m/%Y'),
        'data_fim': data_fim_periodo.strftime('%d/%m/%Y')
    }

@relatorios_bp.route('/semanal/metricas', methods=['GET'])
@login_required
def obter_metricas_semanais_json():
    metricas = calcular_metricas_semanais()
    return jsonify(metricas), 200

@relatorios_bp.route('/semanal', methods=['GET'])
@login_required
def gerar_relatorio_semanal():
    metricas = calcular_metricas_semanais()
    return jsonify({'message': 'Geração de relatório em PDF foi desativada.', 'metricas': metricas}), 200

@relatorios_bp.route('/semanal/enviar', methods=['POST'])
@login_required
def enviar_relatorio_semanal_manual():
    data = request.get_json()
    enviar_email_opt = data.get('enviar_email', False)

    metricas = calcular_metricas_semanais()

    try:
        return jsonify({'message': 'Envio de relatórios por e-mail foi desativado.'}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao enviar relatório: {str(e)}'}), 500