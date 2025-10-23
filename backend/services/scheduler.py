from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app 
from backend.controllers.relatorios import calcular_metricas_semanais
from backend.models.pedido import Pedido
from backend.models.cliente import Cliente
from backend.config import Config
from datetime import datetime, timedelta
import os
import atexit
import decimal
import functools

scheduler = BackgroundScheduler()


def enviar_relatorio_semanal_agendado(app): 
    with app.app_context():
        print("Executando tarefa agendada: Envio de Relatório Semanal...")
        
        try:
            metricas = calcular_metricas_semanais()

            print("Envio agendado de relatório por e-mail foi desativado. Relatório gerado no sistema CLI.")

        except Exception as e:
            print(f"Erro geral ao enviar relatório semanal agendado: {e}")
        finally:
            pass


def enviar_lembretes_pagamento(app):
    with app.app_context():
        print("Executando tarefa agendada: Envio de Lembretes de Pagamento...")
        
        dias_limite_lembrete = 3
        data_limite = datetime.now() - timedelta(days=dias_limite_lembrete)

        pedidos_pendentes_para_lembrete = Pedido.query.filter(
            Pedido.status == 'pendente',
            Pedido.data_pedido <= data_limite
        ).all()

        for pedido in pedidos_pendentes_para_lembrete:
            cliente = Cliente.query.get(pedido.cliente_id)
            if cliente and cliente.telefone:
                print(f"Lembrete para o pedido {pedido.id} não enviado (sem integração WhatsApp ou sem telefone).")
            else:
                print(f"Nenhum método de lembrete configurado para o pedido {pedido.id}.")


def start_scheduler(app_instance):
    global scheduler
    if not scheduler.running:
        scheduler.start()
    
    
    scheduler.add_job(
        func=functools.partial(enviar_relatorio_semanal_agendado, app_instance),
        trigger=CronTrigger(day_of_week='mon', hour=9, minute='0'),
        id='relatorio_semanal',
        replace_existing=True,
        max_instances=1
    )
    print("Job de Relatório Semanal agendado para toda segunda-feira às 09:00.")

    scheduler.add_job(
        func=functools.partial(enviar_lembretes_pagamento, app_instance),
        trigger=CronTrigger(hour=10, minute='0'),
        id='lembretes_pagamento',
        replace_existing=True,
        max_instances=1
    )
    print("Job de Lembretes de Pagamento agendado para todo dia às 10:00.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler desligado.")