import os
import sys
from datetime import datetime, timedelta, date
import decimal
import csv
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))


from backend.app import app
from backend.models.database import db
from backend.models.usuario import Usuario
from backend.models.cliente import Cliente, AnotacaoCliente
from backend.models.pedido import Pedido
from backend.models.pagamento import Pagamento
from backend.config import Config
from backend.controllers.relatorios import calcular_metricas_semanais
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError


_logged_in_user = None 


def clear_screen():
   os.system('cls' if os.name == 'nt' else 'clear')

def print_menu(title, options):
    clear_screen()
    print(f"\n--- {title} ---")
    for key, value in options.items():
        print(f"{key}. {value[0]}")
    print("0. Voltar" if title != "Menu Principal" else "0. Sair")
    print("----------------------")

def get_input(prompt, type=str, optional=False, default=None):
    while True:
        value = input(prompt).strip()
        if not value:
            if optional:
                return default
            else:
                print("Campo obrigatório. Por favor, preencha.")
                continue
        try:
            if type == int:
                return int(value)
            elif type == float:
                return float(value)
            elif type == datetime.date: 
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value
        except ValueError:
            print(f"Entrada inválida. Por favor, insira um(a) {type.__name__} válido(a).")


def login_cli():
    global _logged_in_user
    print("\n--- Login ---")
    email = input("E-mail: ").lower() 
    senha = input("Senha: ")

    with app.app_context():
        user = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none()
        if user and user.check_password(senha):
            _logged_in_user = user 
            print(f"Login bem-sucedido! Bem-vindo(a), {user.nome}.")
            return True
        else:
            print("E-mail ou senha inválidos.")
            return False

def register_cli():
    print("\n--- Registrar Novo Usuário ---")
    nome = get_input("Nome: ")
    email = get_input("E-mail: ").lower()

    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        print("Erro: Formato de e-mail inválido.")
        return False
    

    senha = get_input("Senha: ")

    with app.app_context():
        if db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none():
            print("Erro: E-mail já registrado.")
            return False
        
        try:
            new_user = Usuario(nome=nome, email=email, senha_texto_claro=senha)
            db.session.add(new_user)
            db.session.commit()
            print("Usuário registrado com sucesso!")
            return True
        except IntegrityError:
            db.session.rollback()
            print("Erro ao registrar usuário: e-mail já existente ou outro erro de integridade.")
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao registrar usuário: {e}")
            return False

def logout_user_cli():
    global _logged_in_user
    _logged_in_user = None
    print("Logout realizado com sucesso.")


def list_clientes_cli():
    with app.app_context():
        print("\n--- Lista de Clientes ---")
        search_term = get_input("Termo de busca (nome/telefone/email, opcional): ", optional=True)
        
        clientes_query = db.session.query(Cliente)
        if search_term:
            clientes_query = clientes_query.filter(
                (Cliente.nome.ilike(f'%{search_term}%')) |
                (Cliente.telefone.ilike(f'%{search_term}%')) |
                (Cliente.email.ilike(f'%{search_term}%'))
            )
        
        clientes = clientes_query.all()
        if not clientes:
            print("Nenhum cliente encontrado.")
            return
        
        print("\n{:<5} {:<25} {:<15} {:<25}".format("ID", "Nome", "Telefone", "Email"))
        print("-" * 70)
        for cliente in clientes:
            print(f"{cliente.id:<5} {cliente.nome:<25} {cliente.telefone:<15} {cliente.email or 'N/A':<25}")

def add_cliente_cli():
    with app.app_context():
        print("\n--- Adicionar Novo Cliente ---")
        nome = get_input("Nome: ")
        telefone = get_input("Telefone: ")
        email = get_input("E-mail (opcional): ", optional=True)
        endereco = get_input("Endereço (opcional): ", optional=True)
        preferencias = get_input("Preferências/Observações (opcional): ", optional=True)

        try:
            new_cliente = Cliente(nome=nome, telefone=telefone, email=email, endereco=endereco, preferencias=preferencias)
            db.session.add(new_cliente)
            db.session.commit()
            print(f"Cliente '{nome}' adicionado com sucesso com ID: {new_cliente.id}")
        except IntegrityError:
            db.session.rollback()
            print("Erro: Telefone ou e-mail já cadastrado.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar cliente: {e}")

def view_cliente_details_cli():
    with app.app_context():
        print("\n--- Detalhes do Cliente ---")
        cliente_id = get_input("Digite o ID do cliente: ", type=int)
        
        cliente = db.session.get(Cliente, cliente_id)
        if not cliente:
            print("Cliente não encontrado.")
            return

        print(f"\n--- Detalhes do Cliente ID: {cliente.id} ---")
        print(f"Nome: {cliente.nome}")
        print(f"Telefone: {cliente.telefone}")
        print(f"Email: {cliente.email or 'N/A'}")
        print(f"Endereço: {cliente.endereco or 'N/A'}")
        print(f"Preferências: {cliente.preferencias or 'N/A'}")

        print("\n--- Histórico de Pedidos ---")
        pedidos = cliente.pedidos.order_by(Pedido.data_pedido.desc()).all() 
        if pedidos:
            print("{:<10} {:<30} {:<10} {:<15} {:<15}".format("ID Pedido", "Serviços", "Valor", "Status", "Data Pedido"))
            print("-" * 80)
            for pedido in pedidos:
                print(f"{pedido.id:<10} {pedido.servicos[:27]:<30} R${pedido.valor_total:<8.2f} {pedido.status:<15} {pedido.data_pedido.strftime('%d/%m/%Y'):<15}")
        else:
            print("Nenhum pedido para este cliente.")
        
        print("\n--- Anotações ---")
        anotacoes = cliente.anotacoes.order_by(AnotacaoCliente.data_criacao.desc()).all()
        if anotacoes:
            for anotacao in anotacoes:
                print(f"- {anotacao.texto} ({anotacao.data_criacao.strftime('%d/%m/%Y %H:%M')})")
        else:
            print("Nenhuma anotação para este cliente.")
        
        add_anotacao = get_input("Deseja adicionar uma anotação? (s/n): ", default='n').lower()
        if add_anotacao == 's':
            texto_anotacao = get_input("Digite a nova anotação: ")
            try:
                nova_anotacao = AnotacaoCliente(cliente_id=cliente.id, texto=texto_anotacao)
                db.session.add(nova_anotacao)
                db.session.commit()
                print("Anotação adicionada com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao adicionar anotação: {e}")

def update_cliente_cli():
    with app.app_context():
        print("\n--- Atualizar Cliente ---")
        cliente_id = get_input("Digite o ID do cliente a atualizar: ", type=int)
        
        cliente = db.session.get(Cliente, cliente_id)
        if not cliente:
            print("Cliente não encontrado.")
            return

        print(f"\nAtualizando Cliente: {cliente.nome}")
        print("Deixe em branco para manter o valor atual.")
        
        cliente.nome = get_input(f"Nome ({cliente.nome}): ", optional=True, default=cliente.nome)
        cliente.telefone = get_input(f"Telefone ({cliente.telefone}): ", optional=True, default=cliente.telefone)
        cliente.email = get_input(f"E-mail ({cliente.email or 'N/A'}): ", optional=True, default=cliente.email)
        cliente.endereco = get_input(f"Endereço ({cliente.endereco or 'N/A'}): ", optional=True, default=cliente.endereco)
        cliente.preferencias = get_input(f"Preferências ({cliente.preferencias or 'N/A'}): ", optional=True, default=cliente.preferencias)

        try:
            db.session.commit()
            print("Cliente atualizado com sucesso!")
        except IntegrityError:
            db.session.rollback()
            print("Erro: Telefone ou e-mail já cadastrado para outro cliente.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar cliente: {e}")

def delete_cliente_cli():
    with app.app_context():
        print("\n--- Deletar Cliente ---")
        cliente_id = get_input("Digite o ID do cliente a deletar: ", type=int)
        
        cliente = db.session.get(Cliente, cliente_id)
        if not cliente:
            print("Cliente não encontrado.")
            return

        confirm = get_input(f"Tem certeza que deseja deletar o cliente '{cliente.nome}' (ID: {cliente.id})? (s/n): ", default='n').lower()
        if confirm == 's':
            try:
                db.session.delete(cliente) 
                db.session.commit()
                print("Cliente deletado com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao deletar cliente: {e}")
        else:
            print("Operação cancelada.")


def list_pedidos_cli():
    with app.app_context():
        print("\n--- Lista de Pedidos ---")
        status_filter_raw = get_input("Filtrar por status (pendente, pago, entregue, cancelado, ou vazio para todos): ", optional=True)
        status_filter = status_filter_raw.lower() if status_filter_raw is not None else None
        
        cliente_id_filter = get_input("Filtrar por ID do Cliente (opcional): ", type=int, optional=True)

        query = db.session.query(Pedido).order_by(Pedido.data_pedido.desc())
        if status_filter:
            query = query.filter_by(status=status_filter)
        if cliente_id_filter:
            query = query.filter_by(cliente_id=cliente_id_filter)
        
        pedidos = query.all()

        if not pedidos:
            print("Nenhum pedido encontrado com os filtros especificados.")
            return
        
        print("\n{:<5} {:<25} {:<25} {:<10} {:<12} {:<12} {:<15} {:<15}".format("ID", "Cliente", "Serviços", "Valor", "Status", "Dt. Pedido", "Dt. Entrega", "Dias Rest."))
        print("-" * 125)
        for pedido in pedidos:
            cliente_nome = pedido.cliente.nome if pedido.cliente else 'N/A' 
            dias_restantes = (pedido.data_entrega.date() - datetime.now().date()).days if pedido.data_entrega and pedido.status not in ['entregue', 'cancelado'] else 'N/A'
            print(f"{pedido.id:<5} {cliente_nome:<25} {pedido.servicos[:22]:<25} R${pedido.valor_total:<8.2f} {pedido.status:<12} {pedido.data_pedido.strftime('%d/%m/%Y'):<12} {pedido.data_entrega.strftime('%d/%m/%Y') if pedido.data_entrega else 'N/A':<15} {str(dias_restantes):<15}")

def add_pedido_cli():
    with app.app_context():
        print("\n--- Adicionar Novo Pedido ---")
        clientes = db.session.query(Cliente).all()
        if not clientes:
            print("Nenhum cliente cadastrado. Por favor, adicione um cliente primeiro.")
            return
        
        print("Clientes disponíveis:")
        for c in clientes:
            print(f"ID: {c.id}, Nome: {c.nome}")
        cliente_id = get_input("ID do Cliente: ", type=int)
        cliente = db.session.get(Cliente, cliente_id)
        if not cliente:
            print("Cliente não encontrado.")
            return

        servicos = get_input("Descrição dos Serviços: ")
        valor_total = get_input("Valor Total: ", type=float)
        status = get_input("Status (pendente, pago, entregue, cancelado): ", optional=True, default='pendente').lower()
        while status not in ['pendente', 'pago', 'entregue', 'cancelado']:
            print("Status inválido. Use 'pendente', 'pago', 'entregue' ou 'cancelado'.")
            status = get_input("Status: ").lower()
        
        data_entrega_str = get_input("Data de Entrega (YYYY-MM-DD, opcional): ", optional=True)
        data_entrega = None
        if data_entrega_str:
            try:
                data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()
            except ValueError:
                print("Formato de data de entrega inválido. Deixando em branco.")


        try:
            new_pedido = Pedido(cliente_id=cliente_id, servicos=servicos, valor_total=valor_total, status=status, data_entrega=data_entrega)
            db.session.add(new_pedido)
            db.session.commit()
            print(f"Pedido para '{cliente.nome}' adicionado com sucesso! ID: {new_pedido.id}")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar pedido: {e}")

def view_update_pedido_cli():
    with app.app_context():
        print("\n--- Ver/Atualizar Pedido ---")
        pedido_id = get_input("Digite o ID do pedido: ", type=int)
        
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            print("Pedido não encontrado.")
            return

        cliente_nome = pedido.cliente.nome if pedido.cliente else 'N/A'
        print(f"\n--- Detalhes do Pedido ID: {pedido.id} ---")
        print(f"Cliente: {cliente_nome} (ID: {pedido.cliente_id})")
        print(f"Serviços: {pedido.servicos}")
        print(f"Valor Total: R${pedido.valor_total:.2f}")
        print(f"Status Atual: {pedido.status}")
        print(f"Data do Pedido: {pedido.data_pedido.strftime('%d/%m/%Y')}")
        print(f"Data de Entrega: {pedido.data_entrega.strftime('%d/%m/%Y') if pedido.data_entrega else 'N/A'}")
        
        update_opt = get_input("Deseja atualizar este pedido? (s/n): ", default='n').lower()
        if update_opt == 's':
            print("\n--- Atualizar Pedido ---")
            print("Deixe em branco para manter o valor atual.")
            
            servicos = get_input(f"Serviços ({pedido.servicos}): ", optional=True, default=pedido.servicos)
            valor_total_str = get_input(f"Valor Total ({pedido.valor_total:.2f}): ", optional=True)
            status = get_input(f"Status ({pedido.status}) [pendente, pago, entregue, cancelado]: ", optional=True, default=pedido.status).lower()
            while status not in ['pendente', 'pago', 'entregue', 'cancelado']:
                print("Status inválido. Use 'pendente', 'pago', 'entregue' ou 'cancelado'.")
                status = get_input("Status: ").lower()
            
            data_entrega_str = get_input(f"Data de Entrega ({pedido.data_entrega.strftime('%Y-%m-%d') if pedido.data_entrega else 'N/A'}) (YYYY-MM-DD, vazio para remover): ", optional=True)
            data_entrega = None
            if data_entrega_str:
                try:
                    data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Formato de data de entrega inválido. Mantendo o valor anterior.")
                    data_entrega = pedido.data_entrega

            try:
                pedido.servicos = servicos
                pedido.valor_total = float(valor_total_str) if valor_total_str else pedido.valor_total
                pedido.status = status
                pedido.data_entrega = data_entrega
                db.session.commit()
                print("Pedido atualizado com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao atualizar pedido: {e}")

def delete_pedido_cli():
    with app.app_context():
        print("\n--- Deletar Pedido ---")
        pedido_id = get_input("Digite o ID do pedido a deletar: ", type=int)
        
        pedido = db.session.get(Pedido, pedido_id)
        if not pedido:
            print("Pedido não encontrado.")
            return

        confirm = get_input(f"Tem certeza que deseja deletar o pedido {pedido.id}? (s/n): ", default='n').lower()
        if confirm == 's':
            try:
                if pedido.pagamento: 
                    db.session.delete(pedido.pagamento)
                db.session.delete(pedido)
                db.session.commit()
                print("Pedido deletado com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao deletar pedido: {e}")
        else:
            print("Operação cancelada.")

def list_pedidos_prazos_cli():
    with app.app_context():
        print("\n--- Pedidos com Prazos Próximos ---")
        dias_futuros = get_input("Quantos dias futuros para verificar (padrão 7): ", type=int, optional=True, default=7)
        hoje = datetime.now().date()
        data_limite = hoje + timedelta(days=dias_futuros)

   
        print(f"Verificando pedidos com data de entrega entre: {hoje.strftime('%d/%m/%Y')} e {data_limite.strftime('%d/%m/%Y')}")
        print(f"Status considerados: 'pendente' ou 'pago'")
       

        pedidos_com_prazos = db.session.query(Pedido).filter(
            Pedido.data_entrega.isnot(None),
            Pedido.data_entrega >= hoje,
            Pedido.data_entrega <= data_limite,
            Pedido.status.in_(['pendente', 'pago'])
        ).order_by(Pedido.data_entrega.asc()).all()

        if not pedidos_com_prazos:
            print("Nenhum pedido com prazo próximo encontrado.")
            return
        
        print("\n{:<5} {:<25} {:<25} {:<10} {:<12} {:<15}".format("ID", "Cliente", "Serviços", "Status", "Dt. Entrega", "Dias Restantes"))
        print("-" * 100)
        for pedido in pedidos_com_prazos:
            cliente_nome = pedido.cliente.nome if pedido.cliente else 'N/A'
            dias_restantes = (pedido.data_entrega.date() - hoje).days
            print(f"{pedido.id:<5} {cliente_nome:<25} {pedido.servicos[:22]:<25} R${pedido.valor_total:<8.2f} {pedido.status:<12} {pedido.data_pedido.strftime('%d/%m/%Y'):<12} {pedido.data_entrega.strftime('%d/%m/%Y') if pedido.data_entrega else 'N/A':<15} {str(dias_restantes):<15}")


def register_pagamento_cli():
    with app.app_context():
        print("\n--- Registrar Novo Pagamento ---")
        pedidos_pendentes = db.session.query(Pedido).filter_by(status='pendente').all()
        if not pedidos_pendentes:
            print("Nenhum pedido pendente para registrar pagamento.")
            return

        print("Pedidos Pendentes:")
        for p in pedidos_pendentes:
            cliente_nome = p.cliente.nome if p.cliente else 'N/A'
            print(f"ID: {p.id}, Cliente: {cliente_nome}, Serviços: {p.servicos[:30]}..., Valor: R${p.valor_total:.2f}")
        
        pedido_id = get_input("ID do Pedido a Pagar: ", type=int)
        pedido = db.session.get(Pedido, pedido_id)

        if not pedido or pedido.status != 'pendente':
            print("Pedido não encontrado ou não está pendente.")
            return

        print(f"Valor total do pedido {pedido.id}: R${pedido.valor_total:.2f}")
        valor_pago = get_input("Valor Pago: ", type=float)
        forma_pagamento = get_input("Forma de Pagamento (PIX, Dinheiro, Cartão, Transferência): ")

        try:
            if valor_pago < pedido.valor_total:
                print("O valor pago é menor que o valor total do pedido. (Este módulo espera pagamentos completos).")
                return

            new_pagamento = Pagamento(pedido_id=pedido_id, valor_pago=valor_pago, forma_pagamento=forma_pagamento)
            db.session.add(new_pagamento)
            pedido.status = 'pago'
            db.session.commit()
            print("Pagamento registrado com sucesso! Pedido marcado como 'pago'.")
        except IntegrityError:
            db.session.rollback()
            print("Erro: Este pedido já possui um pagamento registrado.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao registrar pagamento: {e}")

def list_historico_pagamentos_cli():
    with app.app_context():
        print("\n--- Histórico de Pagamentos ---")
        start_date = get_input("Data de Início (YYYY-MM-DD, opcional): ", type=datetime.date, optional=True)
        end_date = get_input("Data de Fim (YYYY-MM-DD, opcional): ", type=datetime.date, optional=True)
        forma_pagamento_filter = get_input("Forma de Pagamento (opcional): ", optional=True)

        query = db.session.query(Pagamento).order_by(Pagamento.data_pagamento.desc())
        if start_date:
            query = query.filter(Pagamento.data_pagamento >= start_date)
        if end_date:
            query = query.filter(Pagamento.data_pagamento < (end_date + timedelta(days=1)))
        if forma_pagamento_filter:
            query = query.filter(Pagamento.forma_pagamento.ilike(f'%{forma_pagamento_filter}%'))

        pagamentos = query.all()

        if not pagamentos:
            print("Nenhum pagamento encontrado com os filtros especificados.")
            return
        
        print("\n{:<5} {:<10} {:<25} {:<12} {:<15} {:<20}".format("ID", "Ped. ID", "Cliente", "Valor", "Forma Pgto", "Data Pgto"))
        print("-" * 90)
        for pgto in pagamentos:
            pedido = db.session.get(Pedido, pgto.pedido_id)
            cliente_nome = pedido.cliente.nome if pedido and pedido.cliente else 'N/A'
            print(f"{pgto.id:<5} {pgto.pedido_id:<10} {cliente_nome:<25} R${pgto.valor_pago:<10.2f} {pgto.forma_pagamento:<15} {pgto.data_pagamento.strftime('%d/%m/%Y %H:%M'):<20}")
    input("\nPressione Enter para continuar...")

def generate_recibo_cli():
    with app.app_context():
        print("\n--- Gerar Recibo (Visualização no Console) ---")
        pagamento_id = get_input("Digite o ID do pagamento para gerar o recibo: ", type=int)
        
        pagamento = db.session.get(Pagamento, pagamento_id)
        if not pagamento:
            print("Pagamento não encontrado.")
            return
        
        pedido = db.session.get(Pedido, pagamento.pedido_id)
        cliente = db.session.get(Cliente, pedido.cliente_id)

        print(f"\n--- Detalhes do Recibo para Pagamento ID: {pagamento.id} ---")
        print(f"Número do Recibo: REC-{pagamento.id:05d}")
        print(f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y')}")
        print(f"\nDados do Cliente:")
        print(f"  Nome: {cliente.nome}")
        print(f"  Telefone: {cliente.telefone}")
        print(f"  E-mail: {cliente.email or 'Não informado'}")
        print(f"  Endereço: {cliente.endereco or 'Não informado'}")
        print(f"\nDetalhes do Pagamento:")
        print(f"  Descrição do Serviço: {pedido.servicos}")
        print(f"  Valor do Pedido: R$ {pedido.valor_total:.2f}")
        print(f"  Valor Pago: R$ {pagamento.valor_pago:.2f}")
        print(f"  Forma de Pagamento: {pagamento.forma_pagamento}")
        print(f"  Data do Pagamento: {pagamento.data_pagamento.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"\nEmitido por: {_logged_in_user.nome if _logged_in_user else 'Administrador'}")
        print("\nEste é um recibo para visualização no console. A geração em PDF foi desativada.")
    input("\nPressione Enter para continuar...")

def export_historico_pagamentos_cli():
    with app.app_context():
        print("\n--- Exportar Histórico de Pagamentos para CSV ---")
        start_date = get_input("Data de Início (YYYY-MM-DD, opcional): ", type=datetime.date, optional=True)
        end_date = get_input("Data de Fim (YYYY-MM-DD, opcional): ", type=datetime.date, optional=True)
        forma_pagamento_filter = get_input("Forma de Pagamento (opcional): ", optional=True)

        query = db.session.query(Pagamento).order_by(Pagamento.data_pagamento.desc())
        if start_date:
            query = query.filter(Pagamento.data_pagamento >= start_date)
        if end_date:
            query = query.filter(Pagamento.data_pagamento < (end_date + timedelta(days=1)))
        if forma_pagamento_filter:
            query = query.filter(Pagamento.forma_pagamento.ilike(f'%{forma_pagamento_filter}%'))

        pagamentos = query.all()

        if not pagamentos:
            print("Nenhum pagamento encontrado com os filtros especificados para exportação.")
            return

        csv_filename = f"historico_pagamentos_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', csv_filename)

        with open(csv_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID Pagamento', 'ID Pedido', 'Nome Cliente', 'Valor Pago', 'Forma de Pagamento', 'Data Pagamento'])
            for pgto in pagamentos:
                pedido = db.session.get(Pedido, pgto.pedido_id)
                cliente_nome = pedido.cliente.nome if pedido and pedido.cliente else 'N/A'
                writer.writerow([
                    pgto.id,
                    pgto.pedido_id,
                    cliente_nome,
                    str(pgto.valor_pago),
                    pgto.forma_pagamento,
                    pgto.data_pagamento.isoformat()
                ])
        
        print(f"Histórico financeiro exportado para: {csv_path}")
    input("\nPressione Enter para continuar...")

def generate_weekly_report_cli():
    with app.app_context():
        print("\n--- Gerar Relatório Semanal ---")
        metricas = calcular_metricas_semanais()
        
        print("\nResumo da Semana:")
        print(f"Período: {metricas['data_inicio']} a {metricas['data_fim']}")
        print(f"Total de Vendas: R$ {metricas['total_vendas']}")
        print(f"Clientes Atendidos: {metricas['clientes_atendidos_count']}")
        print(f"Lucro Estimado: R$ {metricas['lucro_estimado']}")
        
        print("\nServiços Mais Vendidos:")
        if metricas['servicos_mais_vendidos']:
            for servico, contagem in metricas['servicos_mais_vendidos']:
                print(f"- {servico}: {contagem} vendas")
        else:
            print("Nenhum serviço vendido nesta semana.")
        
        print("\nEnvio de relatórios por e-mail foi desativado.")
        input("\nPressione Enter para continuar...")


def clientes_menu():
    while True:
        options = {
            "1": ("Listar Clientes", list_clientes_cli),
            "2": ("Adicionar Cliente", add_cliente_cli),
            "3": ("Ver Detalhes do Cliente", view_cliente_details_cli),
            "4": ("Atualizar Cliente", update_cliente_cli),
            "5": ("Deletar Cliente", delete_cliente_cli)
        }
        print_menu("Gestão de Clientes", options)
        choice = input("Escolha uma opção: ")

        if choice == '1':
            list_clientes_cli()
        elif choice == '2':
            add_cliente_cli()
        elif choice == '3':
            view_cliente_details_cli()
        elif choice == '4':
            update_cliente_cli()
        elif choice == '5':
            delete_cliente_cli()
        elif choice == '0':
            break
        else:
            print("Opção inválida.")
        input("Pressione Enter para continuar...")


def pedidos_menu():
    while True:
        options = {
            "1": ("Listar Pedidos", list_pedidos_cli),
            "2": ("Adicionar Pedido", add_pedido_cli),
            "3": ("Ver Detalhes/Atualizar Pedido", view_update_pedido_cli),
            "4": ("Deletar Pedido", delete_pedido_cli),
            "5": ("Ver Pedidos com Prazos Próximos", list_pedidos_prazos_cli)
        }
        print_menu("Gestão de Pedidos", options)
        choice = input("Escolha uma opção: ")

        if choice == '1':
            list_pedidos_cli()
        elif choice == '2':
            add_pedido_cli()
        elif choice == '3':
            view_update_pedido_cli()
        elif choice == '4':
            delete_pedido_cli()
        elif choice == '5':
            list_pedidos_prazos_cli()
        elif choice == '0':
            break
        else:
            print("Opção inválida.")
        input("Pressione Enter para continuar...")

def pagamentos_menu():
    while True:
        options = {
            "1": ("Registrar Pagamento", register_pagamento_cli),
            "2": ("Listar Histórico de Pagamentos", list_historico_pagamentos_cli),
            "3": ("Gerar Recibo (Visualizar)", generate_recibo_cli),
            "4": ("Exportar Histórico CSV", export_historico_pagamentos_cli)
        }
        print_menu("Gestão de Pagamentos", options)
        choice = input("Escolha uma opção: ")

        if choice == '1':
            register_pagamento_cli()
        elif choice == '2':
            list_historico_pagamentos_cli()
        elif choice == '3':
            generate_recibo_cli()
        elif choice == '4':
            export_historico_pagamentos_cli()
        elif choice == '0':
            break
        else:
            print("Opção inválida.")
        input("Pressione Enter para continuar...")

def main_menu():
    global _logged_in_user
    
    print("DEBUG: main_menu() iniciado.")

    while True:
        is_logged_in = (_logged_in_user is not None)

        if not is_logged_in:
            options = {
                "1": ("Login", login_cli),
                "2": ("Registrar", register_cli)
            }
            print_menu("Menu Principal", options)
            choice = input("Escolha uma opção: ")

            if choice == '1':
                if login_cli():
                    is_logged_in = True
                input("Pressione Enter para continuar...")
            elif choice == '2':
                register_cli()
                input("Pressione Enter para continuar...")
            elif choice == '0':
                print("Saindo do programa.")
                break
            else:
                print("Opção inválida.")
                input("Pressione Enter para continuar...")
        else:
            options = {
                "1": ("Gestão de Clientes", clientes_menu),
                "2": ("Gestão de Pedidos", pedidos_menu),
                "3": ("Gestão de Pagamentos", pagamentos_menu),
                "4": ("Relatórios", generate_weekly_report_cli),
                "5": ("Sair (Logout)", logout_user_cli)
            }
            user_name_display = _logged_in_user.nome if _logged_in_user else "Usuário"
            print_menu(f"Menu Principal (Logado como {user_name_display})", options)
            choice = input("Escolha uma opção: ")

            if choice == '1':
                clientes_menu()
            elif choice == '2':
                pedidos_menu()
            elif choice == '3':
                pagamentos_menu()
            elif choice == '4':
                generate_weekly_report_cli()
            elif choice == '5':
                logout_user_cli()
            elif choice == '0':
                if _logged_in_user:
                    logout_user_cli()
                print("Saindo do programa.")
                break
            else:
                print("Opção inválida.")
                input("Pressione Enter para continuar...")

if __name__ == '__main__':
    print("Iniciando o Assistente via Terminal...")
    main_menu()