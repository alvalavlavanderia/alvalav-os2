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
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL)''')

    # Sempre garante que admin exista
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))

    # Tabela de empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cnpj TEXT NOT NULL,
                    telefone TEXT NOT NULL)''')

    # Tabela de ordens de serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    situacao TEXT NOT NULL,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id))''')

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

# ==========================
# EXPORTAR OS EM PDF
# ==========================
def exportar_pdf(dados_os):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Ordem de Serviço", ln=True, align="C")
    pdf.ln(10)

    for chave, valor in dados_os.items():
        pdf.cell(200, 10, txt=f"{chave}: {valor}", ln=True)

    filename = f"OS_{dados_os['ID']}.pdf"
    pdf.output(filename)
    return filename

# ==========================
# TELA DE LOGIN
# ==========================
def login_screen():
    st.title("Login no Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = usuario
            st.success(f"Bem-vindo, {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos!")

# ==========================
# CADASTRO DE EMPRESAS
# ==========================
def cadastro_empresas():
    st.subheader("Cadastro de Empresa")

    nome = st.text_input("Nome da Empresa *")
    cnpj = st.text_input("CNPJ *")
    telefone = st.text_input("Telefone *")

    if st.button("Salvar Empresa"):
        if not nome or not cnpj or not telefone:
            st.error("Todos os campos são obrigatórios!")
        else:
            conn = sqlite3.connect("sistema.db")
            c = conn.cursor()
            c.execute("INSERT INTO empresas (nome, cnpj, telefone) VALUES (?, ?, ?)", (nome, cnpj, telefone))
            conn.commit()
            conn.close()
            st.success("Empresa cadastrada com sucesso!")

# ==========================
# ABRIR ORDEM DE SERVIÇO
# ==========================
def abrir_os():
    st.subheader("Abrir Ordem de Serviço")

    conn = sqlite3.connect("sistema.db")
    empresas = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()

    empresa_id = st.selectbox("Selecione a Empresa *", [""] + list(empresas["id"].astype(str)))
    titulo = st.text_input("Título *")
    descricao = st.text_area("Descrição *")
    situacao = st.selectbox("Situação *", ["", "Aberta", "Em Andamento", "Fechada"])

    if st.button("Salvar OS"):
        if not empresa_id or not titulo or not descricao or not situacao:
            st.error("Todos os campos são obrigatórios!")
        else:
            conn = sqlite3.connect("sistema.db")
            c = conn.cursor()
            c.execute("INSERT INTO ordens_servico (empresa_id, titulo, descricao, situacao) VALUES (?, ?, ?, ?)",
                      (empresa_id, titulo, descricao, situacao))
            conn.commit()
            conn.close()
            st.success("Ordem de serviço aberta com sucesso!")

# ==========================
# CONSULTAR ORDEM DE SERVIÇO
# ==========================
def consultar_os():
    st.subheader("Consultar Ordens de Serviço")

    filtro_situacao = st.selectbox("Filtrar por Situação", [""] + ["Aberta", "Em Andamento", "Fechada"], index=1)

    query = "SELECT os.id, e.nome AS empresa, os.titulo, os.descricao, os.situacao " \
            "FROM ordens_servico os JOIN empresas e ON os.empresa_id = e.id"
    if filtro_situacao:
        query += " WHERE os.situacao=?"

    conn = sqlite3.connect("sistema.db")
    if filtro_situacao:
        df = pd.read_sql(query, conn, params=(filtro_situacao,))
    else:
        df = pd.read_sql(query, conn)
    conn.close()

    if not df.empty:
        for i, row in df.iterrows():
            st.write(f"**OS {row['id']} - {row['titulo']}**")
            st.write(f"Empresa: {row['empresa']}")
            st.write(f"Descrição: {row['descricao']}")
            st.write(f"Situação: {row['situacao']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Exportar PDF - OS {row['id']}"):
                    dados_os = {
                        "ID": row['id'],
                        "Empresa": row['empresa'],
                        "Título": row['titulo'],
                        "Descrição": row['descricao'],
                        "Situação": row['situacao']
                    }
                    arquivo = exportar_pdf(dados_os)
                    st.success(f"PDF gerado: {arquivo}")
            with col2:
                st.write("---")

    else:
        st.info("Nenhuma OS encontrada.")

# ==========================
# MAIN
# ==========================
def main():
    init_db()

    if "usuario" not in st.session_state:
        login_screen()
    else:
        st.sidebar.title("Menu")
        opcao = st.sidebar.radio("Escolha uma opção", ["Cadastro de Empresa", "Abrir OS", "Consultar OS", "Sair"])

        if opcao == "Cadastro de Empresa":
            cadastro_empresas()
        elif opcao == "Abrir OS":
            abrir_os()
        elif opcao == "Consultar OS":
            consultar_os()
        elif opcao == "Sair":
            del st.session_state["usuario"]
            st.experimental_rerun()

if __name__ == "__main__":
    main()
