import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF

# ==========================
# BANCO DE DADOS
# ==========================
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Tabela de usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT
        )
    """)

    # Tabela de ordens de serviço
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            descricao TEXT,
            situacao TEXT
        )
    """)

    # Usuário admin padrão
    c.execute("SELECT * FROM usuarios WHERE usuario=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))

    conn.commit()
    conn.close()

# ==========================
# FUNÇÕES DE USUÁRIO
# ==========================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user = c.fetchone()
    conn.close()
    return user

def registrar_usuario(usuario, senha):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False
    conn.close()
    return sucesso

# ==========================
# FUNÇÕES DE ORDENS DE SERVIÇO
# ==========================
def adicionar_ordem(titulo, descricao, situacao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("INSERT INTO ordens_servico (titulo, descricao, situacao) VALUES (?, ?, ?)", (titulo, descricao, situacao))
    conn.commit()
    conn.close()

def listar_ordens():
    conn = sqlite3.connect("sistema.db")
    df = pd.read_sql_query("SELECT * FROM ordens_servico", conn)
    conn.close()
    return df

def atualizar_ordem(id_, titulo, descricao, situacao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("UPDATE ordens_servico SET titulo=?, descricao=?, situacao=? WHERE id=?", (titulo, descricao, situacao, id_))
    conn.commit()
    conn.close()

def deletar_ordem(id_):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id=?", (id_,))
    conn.commit()
    conn.close()

# ==========================
# GERAR PDF
# ==========================
def gerar_pdf():
    df = listar_ordens()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "Relatório de Ordens de Serviço", ln=True, align="C")
    pdf.ln(10)

    for index, row in df.iterrows():
        pdf.cell(0, 10, f"ID: {row['id']} - Título: {row['titulo']} - Situação: {row['situacao']}", ln=True)

    pdf.output("relatorio_os.pdf")

# ==========================
# TELA DE LOGIN
# ==========================
def login_screen():
    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = usuario
            st.success(f"Bem-vindo, {usuario}!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

    st.write("Ainda não tem conta?")
    if st.button("Registrar"):
        if usuario and senha:
            if registrar_usuario(usuario, senha):
                st.success("Usuário registrado com sucesso!")
            else:
                st.error("Usuário já existe.")

# ==========================
# DASHBOARD PRINCIPAL
# ==========================
def main_screen():
    st.title("📋 Sistema de Ordens de Serviço")

    menu = ["Listar Ordens", "Nova Ordem", "Gerar PDF", "Sair"]
    escolha = st.sidebar.selectbox("Menu", menu)

    if escolha == "Listar Ordens":
        df = listar_ordens()
        st.dataframe(df)

        if not df.empty:
            id_ = st.number_input("ID da OS para editar/deletar", min_value=1, step=1)

            if st.button("Deletar OS"):
                deletar_ordem(id_)
                st.success("Ordem deletada com sucesso!")
                st.rerun()

            if st.button("Atualizar OS"):
                titulo = st.text_input("Novo Título")
                descricao = st.text_area("Nova Descrição")
                situacao = st.selectbox("Nova Situação", ["Aberta", "Em andamento", "Concluída"])
                atualizar_ordem(id_, titulo, descricao, situacao)
                st.success("Ordem atualizada com sucesso!")
                st.rerun()

    elif escolha == "Nova Ordem":
        st.subheader("Criar Nova Ordem de Serviço")
        titulo = st.text_input("Título")
        descricao = st.text_area("Descrição")
        situacao = st.selectbox("Situação", ["Aberta", "Em andamento", "Concluída"])
        if st.button("Salvar"):
            adicionar_ordem(titulo, descricao, situacao)
            st.success("Ordem adicionada com sucesso!")

    elif escolha == "Gerar PDF":
        gerar_pdf()
        st.success("PDF gerado com sucesso! (relatorio_os.pdf)")

    elif escolha == "Sair":
        st.session_state.pop("usuario", None)
        st.success("Logout realizado com sucesso!")
        st.rerun()

# ==========================
# MAIN
# ==========================
def main():
    init_db()

    if "usuario" not in st.session_state:
        login_screen()
    else:
        main_screen()

if __name__ == "__main__":
    main()
