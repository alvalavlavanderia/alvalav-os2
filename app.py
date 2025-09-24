import streamlit as st
import sqlite3
import os
from datetime import datetime

# ================================
# Conexão com banco de dados
# ================================
DB_FILE = "alvalav_os.db"

# ================================
# Funções de Banco de Dados e Auxiliares
# ================================

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE, cnpj TEXT, endereco TEXT, telefone TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE, senha TEXT, is_admin INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT, servico TEXT, titulo TEXT, descricao TEXT, status TEXT DEFAULT 'Aberta',
                data_abertura TEXT, data_atualizacao TEXT)''')

    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))
    
    conn.commit()
    conn.close()

def autenticar(usuario, senha):
    """Verifica as credenciais do usuário no banco de dados."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user_data = c.fetchone()
    conn.close()
    return user_data

def is_admin(usuario):
    """Verifica se o usuário tem permissões de administrador."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM usuarios WHERE usuario=?", (usuario,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def get_all_empresas():
    """Retorna a lista de nomes de todas as empresas cadastradas."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    empresas = [row[0] for row in c.execute("SELECT nome FROM empresas").fetchall()]
    conn.close()
    return empresas

def get_all_servicos():
    """Retorna a lista de descrições de todos os tipos de serviço."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    servicos = [row[0] for row in c.execute("SELECT descricao FROM tipos_servico").fetchall()]
    conn.close()
    return servicos

# ================================
# Verificação inicial do DB
# ================================
if not os.path.exists(DB_FILE):
    init_db()

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# ================================
# Lógica da Aplicação: Login vs. Conteúdo
# ================================

if "usuario" not in st.session_state or not st.session_state.usuario:
    # Bloco de Login
    st.title("🔐 Login no Sistema")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        u = autenticar(user, pwd)
        if u:
            st.session_state.usuario = user
            st.success(f"Bem-vindo, {user}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

else:
    # Bloco da Aplicação (seção logada)
    st.sidebar.title("📌 Menu Principal")
    
    if st.sidebar.button("Sair"):
        st.session_state.usuario = None
        st.rerun()

    menu = st.sidebar.selectbox("Escolha uma opção",
                                ["Ordem de Serviço", "Cadastro"])
    
    # --- CADASTROS ---
    if menu == "Cadastro":
        st.header("📂 Cadastros")
        submenu = st.selectbox("Selecione",
                               ["Cadastro Empresa", "Cadastro Tipo de Serviço"] +
                               (["Cadastro Usuário"] if is_admin(st.session_state.usuario) else []))

        # Estrutura if/elif para os submenus de Cadastro
        if submenu == "Cadastro Empresa":
            nome = st.text_input("Nome da Empresa")
            cnpj = st.text_input("CNPJ")
            endereco = st.text_input("Endereço")
            telefone = st.text_input("Telefone")
            if st.button("Salvar Empresa"):
                try:
                    c.execute("INSERT INTO empresas (nome, cnpj, endereco, telefone) VALUES (?, ?, ?, ?)",
                              (nome, cnpj, endereco, telefone))
                    conn.commit()
                    st.success("Empresa cadastrada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Erro: Empresa já cadastrada ou dados inválidos.")

        elif submenu == "Cadastro Tipo de Serviço":
            desc = st.text_input("Descrição do Serviço")
            if st.button("Salvar Serviço"):
                try:
                    c.execute("INSERT INTO tipos_servico (descricao) VALUES (?)", (desc,))
                    conn.commit()
                    st.success("Serviço cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Erro: Serviço já cadastrado.")

        elif submenu == "Cadastro Usuário" and is_admin(st.session_state.usuario):
            usuario = st.text_input("Novo Usuário")
            senha = st.text_input("Senha", type="password")
            admin_flag = st.checkbox("Usuário administrador?")
            if st.button("Salvar Usuário"):
                try:
                    c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                              (usuario, senha, 1 if admin_flag else 0))
                    conn.commit()
                    st.success("Usuário cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Erro: Usuário já existe.")

    # --- ORDEM DE SERVIÇO ---
    elif menu == "Ordem de Serviço":
        st.header("📑 Ordem de Serviço")
        submenu = st.selectbox("Selecione", ["Abrir OS", "Consultar OS"])

        # Estrutura if/elif para os submenus de Ordem de Serviço
        if submenu == "Abrir OS":
            empresas = get_all_empresas()
            servicos = get_all_servicos()
            if not empresas:
                st.warning("Nenhuma empresa cadastrada. Por favor, cadastre uma na seção 'Cadastro Empresa'.")
            if not servicos:
                st.warning("Nenhum tipo de serviço cadastrado. Por favor, cadastre um na seção 'Cadastro Tipo de Serviço'.")
            
            if empresas and servicos:
                empresa = st.selectbox("Empresa", empresas)
                servico = st.selectbox("Serviço", servicos)
                titulo = st.text_input("Título da OS")
                descricao = st.text_area("Descrição")
                if st.button("Abrir OS"):
                    c.execute("""INSERT INTO ordens_servico
                                 (empresa, servico, titulo, descricao, status, data_abertura, data_atualizacao)
                                 VALUES (?, ?, ?, ?, 'Aberta', ?, ?)""",
                              (empresa, servico, titulo, descricao, datetime.now().isoformat(), datetime.now().isoformat()))
                    conn.commit()
                    st.success("Ordem de serviço aberta com sucesso!")

        elif submenu == "Consultar OS":
            filtro = st.radio("Consultar por:", ["Todas Abertas", "Por Empresa", "Por Código"])

            query = ""
            params = ()
            if filtro == "Todas Abertas":
                query = "SELECT id, empresa, titulo, status FROM ordens_servico WHERE status='Aberta'"
            elif filtro == "Por Empresa":
                empresas = get_all_empresas()
                if empresas:
                    empresa_selecionada = st.selectbox("Selecione a empresa", empresas)
                    query = "SELECT id, empresa, titulo, status FROM ordens_servico WHERE empresa=?"
                    params = (empresa_selecionada,)
            elif filtro == "Por Código":
                codigo = st.number_input("Código da OS", min_value=1, step=1)
                if codigo:
                    query = "SELECT id, empresa, titulo, status FROM ordens_servico WHERE id=?"
                    params = (codigo,)

            if query:
                c.execute(query, params)
                rows = c.fetchall()
                if rows:
                    st.header("Lista de Ordens de Serviço")
                    st.dataframe(rows,
                                 column_names=["CÓDIGO", "EMPRESA", "TÍTULO", "SITUAÇÃO"],
                                 hide_index=True)

                    os_ids = [row[0] for row in rows]
                    st.write("---")
                    st.subheader("Finalizar Ordem de Serviço")
                    os_selecionada_id = st.selectbox("Selecione a OS pelo Código", os_ids)
                    
                    if st.button("Finalizar OS selecionada"):
                        c.execute("UPDATE ordens_servico SET status=?, data_atualizacao=? WHERE id=?", 
                                  ('Finalizada', datetime.now().isoformat(), os_selecionada_id))
                        conn.commit()
                        st.success(f"OS {os_selecionada_id} finalizada com sucesso!")
                        st.rerun()
                else:
                    st.info("Nenhuma OS encontrada com o critério selecionado.")
