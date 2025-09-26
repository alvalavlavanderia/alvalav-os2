import streamlit as st
import sqlite3
import bcrypt

# ======================
# CONFIGURAÇÃO
# ======================
DB_NAME = "sistema_os.db"
ADMIN_PASSWORD = "1234" # Senha inicial para o admin

# ======================
# BANCO DE DADOS - Operações Centralizadas
# ======================
def conectar_bd():
    """Retorna uma conexão e um cursor para o banco de dados."""
    return sqlite3.connect(DB_NAME), sqlite3.connect(DB_NAME).cursor()

def criar_banco():
    """Cria as tabelas e o usuário administrador inicial."""
    conn, c = conectar_bd()

    # Criação das tabelas
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT,
            tipo TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT UNIQUE NOT NULL, -- CNPJ com UNIQUE
            telefone TEXT NOT NULL,
            rua TEXT NOT NULL,
            cep TEXT NOT NULL,
            numero TEXT NOT NULL,
            cidade TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL -- Serviço com UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            titulo TEXT,
            descricao TEXT,
            tipo_servico_id INTEGER,
            situacao TEXT,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id) ON DELETE CASCADE,
            FOREIGN KEY (tipo_servico_id) REFERENCES servicos (id) ON DELETE RESTRICT
        )
    """)

    # Criação do usuário admin
    senha_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt())
    # Note: O ID fixo 1 pode causar problemas se o autoincrement for resetado.
    # Removendo o 'id' do INSERT, apenas o 'INSERT OR IGNORE' no 'usuario' (UNIQUE) garante que só insere uma vez.
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
              ("admin", senha_hash, "admin"))

    conn.commit()
    conn.close()

def db_fetch(query, params=()):
    """Executa SELECT e retorna todos os resultados."""
    conn, c = conectar_bd()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

def db_execute(query, params=()):
    """Executa INSERT/UPDATE/DELETE e retorna True em sucesso."""
    conn, c = conectar_bd()
    try:
        c.execute(query, params)
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.close()
        # Retorna o erro de integridade (ex: UNIQUE constraint failed)
        return str(e)
    except Exception as e:
        conn.close()
        return str(e)
    finally:
        conn.close()


# ======================
# AUTENTICAÇÃO
# ======================
def autenticar_usuario(usuario, senha):
    """Verifica se o usuário e a senha estão corretos."""
    user = db_fetch("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    if user and bcrypt.checkpw(senha.encode("utf-8"), user[0][2]): # user[0] pois db_fetch retorna lista de tuplas
        return user[0]
    return None

def logout():
    """Executa o logout e limpa os estados da sessão de navegação de OS."""
    if "usuario" in st.session_state:
        del st.session_state["usuario"]
    if "editando_os" in st.session_state:
        del st.session_state["editando_os"]
    st.rerun()


# ======================
# FUNÇÕES DE UTILIDADE
# ======================
def get_options_from_db(table_name):
    """Busca ID e NOME para SelectBox."""
    return db_fetch(f"SELECT id, nome FROM {table_name}")

def formatar_opcao_select(item):
    """Formata (ID, NOME) para SelectBox (ex: '1 - Nome')."""
    return f"{item[0]} - {item[1]}"

def parse_opcao_select(opcao_formatada):
    """Extrai o ID de uma opção formatada (ex: '1 - Nome' -> 1)."""
    if not opcao_formatada:
        return None
    return int(opcao_formatada.split(" - ")[0])

def validar_campos(campos):
    """Verifica se todos os campos na lista são não vazios."""
    return all(campos)


# ======================
# CADASTRO EMPRESA
# ======================
def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")

    with st.form("form_empresa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Empresa*").strip()
            cnpj = st.text_input("CNPJ*").strip()
            telefone = st.text_input("Telefone*").strip()
        with col2:
            rua = st.text_input("Rua*").strip()
            cep = st.text_input("CEP*").strip()
            numero = st.text_input("Número*").strip()
        cidade = st.text_input("Cidade*").strip()
        estado = st.selectbox("Estado*", ["SP", "RJ", "MG", "PR", "SC", "RS", "Outro"], index=0).strip() # Usando selectbox

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            dados = [nome, cnpj, telefone, rua, cep, numero, cidade, estado]
            if not validar_campos(dados):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                query = """
                    INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                resultado = db_execute(query, dados)
                if resultado is True:
                    st.success("✅ Empresa cadastrada com sucesso!")
                elif "UNIQUE constraint failed: empresas.cnpj" in resultado:
                    st.error("⚠️ Erro: CNPJ já cadastrado!")
                else:
                    st.error(f"❌ Erro ao cadastrar empresa: {resultado}")


# ======================
# CADASTRO SERVIÇO
# ======================
def cadastro_servico():
    st.subheader("🛠️ Cadastro de Tipo de Serviço")

    with st.form("form_servico", clear_on_submit=True):
        nome = st.text_input("Nome do Serviço*").strip()
        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not nome:
                st.error("⚠️ O nome do serviço é obrigatório.")
            else:
                resultado = db_execute("INSERT INTO servicos (nome) VALUES (?)", (nome,))
                if resultado is True:
                    st.success("✅ Serviço cadastrado com sucesso!")
                elif "UNIQUE constraint failed: servicos.nome" in resultado:
                    st.error("⚠️ Erro: Tipo de Serviço já existe!")
                else:
                    st.error(f"❌ Erro ao cadastrar serviço: {resultado}")


# ======================
# CADASTRO USUÁRIO
# ======================
def cadastro_usuario():
    st.subheader("👤 Cadastro de Usuário (apenas Admin)")
    # Restrição de acesso a não-admin
    if st.session_state["usuario"][3] != "admin": # tipo de usuário está no índice 3
        st.warning("🔒 Apenas usuários administradores podem cadastrar outros usuários.")
        return

    with st.form("form_usuario", clear_on_submit=True):
        usuario = st.text_input("Usuário*").strip()
        senha = st.text_input("Senha*", type="password").strip()
        # Removendo selectbox para 'tipo' (simplificação, já que só tem 'admin')
        tipo = "admin" # Valor fixo

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not usuario or not senha:
                st.error("⚠️ Usuário e senha são obrigatórios.")
            else:
                senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
                resultado = db_execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                                       (usuario, senha_hash, tipo))

                if resultado is True:
                    st.success("✅ Usuário cadastrado com sucesso!")
                elif "UNIQUE constraint failed: usuarios.usuario" in resultado:
                    st.error("⚠️ Usuário já existe!")
                else:
                    st.error(f"❌ Erro ao cadastrar usuário: {resultado}")


# ======================
# ABRIR ORDEM DE SERVIÇO
# ======================
def abrir_os():
    st.subheader("📌 Abrir Ordem de Serviço")

    empresas = get_options_from_db("empresas")
    servicos = get_options_from_db("servicos")

    if not empresas or not servicos:
        st.warning("⚠️ É necessário cadastrar pelo menos uma **Empresa** e um **Tipo de Serviço** antes de abrir uma OS.")
        return

    empresa_opcoes = [formatar_opcao_select(e) for e in empresas]
    servico_opcoes = [formatar_opcao_select(s) for s in servicos]

    with st.form("form_os", clear_on_submit=True):
        empresa = st.selectbox("Empresa*", empresa_opcoes)
        titulo = st.text_input("Título*").strip()
        descricao = st.text_area("Descrição*").strip()
        tipo_servico = st.selectbox("Tipo de Serviço*", servico_opcoes)
        situacao = "Aberta" # Padrão

        submitted = st.form_submit_button("Abrir OS")

        if submitted:
            if not validar_campos([empresa, titulo, descricao, tipo_servico]):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                empresa_id = parse_opcao_select(empresa)
                servico_id = parse_opcao_select(tipo_servico)

                query = """
                    INSERT INTO ordens (empresa_id, titulo, descricao, tipo_servico_id, situacao)
                    VALUES (?, ?, ?, ?, ?)
                """
