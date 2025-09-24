import streamlit as st
import sqlite3
import os
from datetime import datetime

# ================================
# Conexão com banco de dados
# ================================
DB_FILE = "alvalav_os.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# ================================
# Inicialização e migração do DB
# ================================
def init_db():
    # Criação inicial das tabelas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE, cnpj TEXT, endereco TEXT, telefone TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE, senha TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT, servico TEXT, descricao TEXT, status TEXT DEFAULT 'Aberta',
                data_abertura TEXT, data_atualizacao TEXT)''')
    
    # Adicionando as colunas que podem não existir.
    # A verificação e o ALTER TABLE precisam ser um commit separado
    
    # Criar usuário admin se não existir
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                ("admin", "Alv32324@", 1))
    
    # Todas as operações de DDL e DML são feitas.
    # Agora, o commit único no final.
    conn.commit()

# Removendo a função auxiliar, pois a lógica de migração pode ser integrada
# para simplificar. O erro é que a função `ensure_column` tentava comitar
# dentro de um bloco maior de `init_db`.

init_db()

# ================================
# Funções auxiliares
# ================================
def autenticar(usuario, senha):
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    return c.fetchone()

def is_admin(usuario):
    c.execute("SELECT is_admin FROM usuarios WHERE usuario=?", (usuario,))
    result = c.fetchone()
    return result and result[0] == 1

# ================================
# Login
# ================================
# Verifique se o usuário NÃO está na sessão.
if "usuario" not in st.session_state or not st.session_state.usuario:
    st.title("🔐 Login no Sistema")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        u = autenticar(user, pwd)
        if u:
            st.session_state.usuario = user
            st.success(f"Bem-vindo, {user}!")
            # O rerun aqui é o que reinicia o script para o próximo passo.
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    # Use st.stop() para garantir que nada abaixo seja executado se o login não foi feito.
    st.stop()

# ================================
# Sistema logado (Este código só é executado se o login foi bem-sucedido)
# ================================
st.sidebar.title("📌 Menu Principal")
# ... (o resto do seu código, sem nenhuma mudança de indentação)

# ================================
# CADASTROS
# ================================
if menu == "Cadastro":
    st.header("📂 Cadastros")
    submenu = st.selectbox("Selecione", 
                           ["Cadastro Empresa", "Cadastro Tipo de Serviço"] + 
                           (["Cadastro Usuário"] if is_admin(st.session_state.usuario) else []))

    # Cadastro Empresa
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
            except:
                st.error("Erro: Empresa já cadastrada ou dados inválidos.")

    # Cadastro Tipo de Serviço
    if submenu == "Cadastro Tipo de Serviço":
        desc = st.text_input("Descrição do Serviço")
        if st.button("Salvar Serviço"):
            try:
                c.execute("INSERT INTO tipos_servico (descricao) VALUES (?)", (desc,))
                conn.commit()
                st.success("Serviço cadastrado com sucesso!")
            except:
                st.error("Erro: Serviço já cadastrado.")

    # Cadastro Usuário (somente admin)
    if submenu == "Cadastro Usuário" and is_admin(st.session_state.usuario):
        usuario = st.text_input("Novo Usuário")
        senha = st.text_input("Senha", type="password")
        admin_flag = st.checkbox("Usuário administrador?")
        if st.button("Salvar Usuário"):
            try:
                c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                          (usuario, senha, 1 if admin_flag else 0))
                conn.commit()
                st.success("Usuário cadastrado com sucesso!")
            except:
                st.error("Erro: Usuário já existe.")

# ================================
# ORDEM DE SERVIÇO
# ================================
elif menu == "Ordem de Serviço":
    st.header("📑 Ordem de Serviço")
    submenu = st.selectbox("Selecione", ["Abrir OS", "Consultar OS"])

    # Abrir OS
    if submenu == "Abrir OS":
        empresas = [row[0] for row in c.execute("SELECT nome FROM empresas").fetchall()]
        servicos = [row[0] for row in c.execute("SELECT descricao FROM tipos_servico").fetchall()]
        empresa = st.selectbox("Empresa", empresas)
        servico = st.selectbox("Serviço", servicos)
        descricao = st.text_area("Descrição")
        if st.button("Abrir OS"):
            c.execute("""INSERT INTO ordens_servico 
             (empresa, servico, descricao, status, data_abertura, data_atualizacao) 
             VALUES (?, ?, ?, 'Aberta', ?, ?)""",
             (empresa, servico, descricao, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            st.success("Ordem de serviço aberta com sucesso!")

    # Consultar OS
    if submenu == "Consultar OS":
        filtro = st.radio("Consultar por:", ["Todas Pendentes", "Por Empresa", "Por Código"])

        if filtro == "Todas Pendentes":
            c.execute("SELECT id, empresa, servico, status FROM ordens_servico WHERE status='Pendente'")
            rows = c.fetchall()
            st.table(rows)

        elif filtro == "Por Empresa":
            empresas = [row[0] for row in c.execute("SELECT nome FROM empresas").fetchall()]
            empresa = st.selectbox("Selecione a empresa", empresas)
            c.execute("SELECT id, empresa, servico, status FROM ordens_servico WHERE empresa=?", (empresa,))
            st.table(c.fetchall())

        elif filtro == "Por Código":
            codigo = st.number_input("Código da OS", min_value=1, step=1)
            c.execute("SELECT id, empresa, servico, descricao, status FROM ordens_servico WHERE id=?", (codigo,))
            st.table(c.fetchall())

# ================================
# SAIR
# ================================
elif menu == "Sair":
    st.session_state.usuario = None
    st.rerun()
