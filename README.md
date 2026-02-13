📊 Assistente Comercial: Sistema de Gestão CRM & ERP
Este projeto é uma solução completa de Back-office desenvolvida em Python para automatizar o gerenciamento de pequenos negócios. Ele integra uma API RESTful robusta com uma Interface de Linha de Comando (CLI) interativa, permitindo o controle total sobre clientes, pedidos e fluxos financeiros.

🚀 Diferenciais Técnicos
Arquitetura Modular (MVC): Utiliza Blueprints do Flask para separar as responsabilidades de Autenticação, Clientes, Pedidos e Finanças.

Inteligência Financeira: Processamento de pagamentos com precisão decimal e algoritmos para métricas de lucro e serviços mais vendidos.

Automação de Tarefas: Integração com APScheduler para execução de rotinas em background, como lembretes de prazos e relatórios semanais.

Segurança de Dados: Hashing de senhas scrypt via Werkzeug e validações de integridade para garantir a proteção de informações sensíveis.

Gestão de Prazos: Monitoramento dinâmico de datas de entrega com alertas para pedidos próximos do vencimento.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.

Framework: Flask.

ORM: SQLAlchemy com suporte a SQLite e PostgreSQL.

Agendador: APScheduler.

Segurança: Werkzeug (Security & Auth).

📁 Estrutura do Projeto
main.py: Interface interativa via terminal (CLI) para operação do sistema.

app.py: Ponto de entrada da API Flask e inicialização do Scheduler.

backend/models/: Definição das entidades e relacionamentos do banco de dados.

backend/controllers/: Lógica de negócio e rotas da API organizadas por Blueprints.

🔧 Como Executar
Instale as dependências:

Bash

pip install -r requirements.txt
Configure o ambiente: Crie um arquivo .env com sua SECRET_KEY e DATABASE_URL.

Inicie a API:

Bash

python app.py
Ou use a CLI:

Bash

python main.py

