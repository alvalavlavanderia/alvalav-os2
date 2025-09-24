import streamlit as st
import sqlite3
import os

# Arquivo do banco
DB_FILE = "alvalav.db"

# Função para abrir conexão
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

# Inicialização do banco
def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE,
                    senha TEXT,
                    is_admin INTEGER DEFAULT 0
                )''')

    # Tabela de empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    rua TEXT,
                    numero TEXT,
                    cep TEXT,
                    cidade TEXT,
                    estado TEXT,
                    telefone TEXT,
                    cnpj TEXT
                )''')

    # Tabela de tipos de serviço
    c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE
                )''')

    # Tabela de ordens de serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    tipo_servico_id INTEGER,
                    titulo TEXT,
                    descricao TEXT,
                    situacao TEXT DEFAULT 'Aberta',
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                    FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
                )''')

    # Cria admin
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))

    conn.commit()
    conn.close()

# Reset do banco
def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        user = c.fetchone()
        conn.close()

        if user:
            st.session_state["usuario"] = usuario
            st.session_state["is_admin"] = bool(user[3])
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

# ---------------- CADASTROS ----------------
def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")
    nome = st.text_input("Nome da Empresa")
    rua = st.text_input("Rua")
    numero = st.text_input("Número")
    cep = st.text_input("CEP")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")
    telefone = st.text_input("Telefone")
    cnpj = st.text_input("CNPJ")

    if st.button("Salvar Empresa"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO empresas (nome, rua, numero, cep, cidade, estado, telefone, cnpj) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (nome, rua, numero, cep, cidade, estado, telefone, cnpj))
        conn.commit()
        conn.close()
        st.success("✅ Empresa cadastrada com sucesso!")

def cadastro_usuario():
    if not st.session_state.get("is_admin", False):
        st.error("⚠️ Apenas administradores podem cadastrar usuários.")
        return

    st.subheader("👤 Cadastro de Usuário")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    is_admin = st.checkbox("Administrador")

    if st.button("Salvar Usuário"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)", 
                      (usuario, senha, int(is_admin)))
            conn.commit()
            conn.close()
            st.success("✅ Usuário cadastrado com sucesso!")
        except:
            st.error("❌ Usuário já existe.")

def cadastro_tipo_servico():
    st.subheader("🛠 Cadastro de Tipo de Serviço")
    nome = st.text_input("Nome do Serviço")

    if st.button("Salvar Serviço"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
            st.success("✅ Tipo de serviço cadastrado com sucesso!")
        except:
            st.error("❌ Esse tipo de serviço já existe.")

# ---------------- ORDEM DE SERVIÇO ----------------
def abrir_os():
    st.subheader("📄 Abrir Ordem de Serviço")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    c.execute("SELECT id, nome FROM tipos_servico")
    tipos = c.fetchall()
    conn.close()

    empresa = st.selectbox("Empresa", empresas, format_func=lambda x: x[1] if x else "")
    tipo = st.selectbox("Tipo de Serviço", tipos, format_func=lambda x: x[1] if x else "")
    titulo = st.text_input("Título")
    descricao = st.text_area("Descrição")

    if st.button("Salvar OS"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO ordens_servico (empresa_id, tipo_servico_id, titulo, descricao, situacao) VALUES (?, ?, ?, ?, 'Aberta')",
                  (empresa[0], tipo[0], titulo, descricao))
        conn.commit()
        conn.close()
        st.success("✅ OS aberta com sucesso!")

def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT situacao FROM ordens_servico")
    situacoes = [row[0] for row in c.fetchall()]
    situacao = st.selectbox("Filtrar por Situação", [""] + situacoes)

    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    empresa = st.selectbox("Filtrar por Empresa", [""] + [e[1] for e in empresas])

    query = """SELECT os.id, e.nome, os.titulo, os.situacao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id
               WHERE 1=1"""
    params = []

    if situacao:
        query += " AND os.situacao=?"
        params.append(situacao)
    if empresa:
        query += " AND e.nome=?"
        params.append(empresa)

    c.execute(query, params)
    dados = c.fetchall()
    conn.close()

    st.table(dados)

# ---------------- MAIN APP ----------------
def main():
    # Reset DB (botão escondido para testes/admin)
    with st.sidebar:
        if st.button("⚠️ Resetar Banco de Dados"):
            reset_db()
            st.success("✅ Banco resetado com sucesso.")
            st.rerun()

    menu = st.sidebar.selectbox("📌 Menu Principal", ["", "Cadastros", "Ordem de Serviço"])

    if menu == "Cadastros":
        submenu = st.sidebar.selectbox("Cadastros", ["", "Cadastro Empresa", "Cadastro Usuário", "Cadastro Tipo de Serviço"])
        if submenu == "Cadastro Empresa":
            cadastro_empresa()
        elif submenu == "Cadastro Usuário":
            cadastro_usuario()
        elif submenu == "Cadastro Tipo de Serviço":
            cadastro_tipo_servico()

    elif menu == "Ordem de Serviço":
        submenu = st.sidebar.selectbox("Ordem de Serviço", ["", "Abrir OS", "Consultar OS"])
        if submenu == "Abrir OS":
            abrir_os()
        elif submenu == "Consultar OS":
            consultar_os()

# ---------------- EXECUÇÃO ----------------
if __name__ == "__main__":
    if "usuario" not in st.session_state:
        init_db()
        login()
    else:
        st.sidebar.write(f"👋 Olá, {st.session_state['usuario']}")
        if st.sidebar.button("Sair"):
            st.session_state.clear()
            st.rerun()
        main()
