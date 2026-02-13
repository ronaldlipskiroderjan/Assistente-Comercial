                            =====================================================
                            API de Gestão de Clientes, Pedidos e Pagamentos
                            =====================================================



# API de Gestão de Clientes e Pedidos (Backend)

Backend API robusto desenvolvido em Python com Flask e SQLAlchemy para um sistema completo de gerenciamento de clientes (CRM), pedidos, pagamentos e relatórios automatizados.

---

### 🌟 Sobre o Projeto

Este repositório contém o código-fonte de uma API RESTful projetada para ser o backend de um sistema de gestão comercial. Ela permite o cadastro e gerenciamento de clientes, o controle de pedidos (desde a criação até a entrega), o registro de pagamentos e a autenticação de usuários.

Um dos principais recursos é um agendador de tarefas (`APScheduler`) que opera em segundo plano para automatizar o envio de relatórios e lembretes de pagamento.

### ✨ Funcionalidades Principais

* **Gestão de Clientes (CRM):**
    * CRUD completo de clientes (Nome, telefone, e-mail, etc.).
    * Registro de preferências e anotações privadas por cliente.
    * Visualização do histórico de pedidos de cada cliente.
* **Gestão de Pedidos:**
    * CRUD de pedidos, associando-os a um cliente.
    * Controle de status (ex: `pendente`, `pago`, `entregue`, `cancelado`).
    * Gerenciamento de datas de entrega e consulta de prazos futuros.
* **Gestão de Pagamentos:**
    * Registro de pagamentos (assumindo pagamento integral) para pedidos.
    * Atualização automática do status do pedido para "pago".
    * Endpoint para histórico financeiro com filtros por data e forma de pagamento.
* **Relatórios e Métricas:**
    * Endpoint de métricas semanais (total de vendas, serviços mais vendidos, lucro estimado).
    * Exportação do histórico financeiro para arquivo `.csv`.
* **Autenticação de Usuários:**
    * Sistema de registro e login de usuários para acesso à API.
    * Uso de `Werkzeug` para hashing seguro de senhas.
* **Tarefas Automatizadas (Scheduler):**
    * **Relatório Semanal:** Envio automático de relatórios semanais agendado para toda segunda-feira às 09:00.
    * **Lembretes de Pagamento:** Verificação diária (às 10:00) de pedidos pendentes para enviar lembretes.

### 🛠️ Tecnologias Utilizadas

* **Python 3**
* **Flask:** Micro-framework web para a criação da API.
* **Flask-SQLAlchemy:** ORM para interação com o banco de dados SQL.
* **Flask-CORS:** Para habilitar o Cross-Origin Resource Sharing.
* **APScheduler:** Para execução de tarefas agendadas em segundo plano (background tasks).
* **Werkzeug:** Para hashing seguro de senhas de usuário.
* **python-dotenv:** Para gerenciamento de variáveis de ambiente.

---

### 🚀 Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    (Crie um arquivo `requirements.txt` com as bibliotecas do projeto e execute)
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-CORS apscheduler python-dotenv
    ```

4.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto e adicione suas configurações. Você pode usar `config.py` como referência:
    ```.env
    SECRET_KEY='s ua-chave-secreta-forte'
    DATABASE_URL='sqlite:///gestao.db' 
    # Ou use uma URL de banco de dados diferente (ex: PostgreSQL)
    ```

5.  **Execute a aplicação:**
    ```bash
    python app.py
    ```

6.  **Usuário Admin Padrão:**
    Na primeira execução, um usuário administrador padrão será criado.
    * **E-mail:** `admin@example.com`
    * **Senha:** `admin123`

    *(Recomenda-se alterar esta senha em produção!)*
