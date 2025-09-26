import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import bcrypt

# ==========================
# BANCO DE DADOS
# ==========================
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # tabela de usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha BLOB NOT NULL,
            admin INTEGER NOT NULL DEFAULT 0
        )
    """)

    # tabela de empresas
    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            telefone TEXT NOT NULL,
            rua TEXT,
            numero TEXT,
            cep TEXT,
            cidade TEXT,
            estado TEXT
        )
    """)

    # tabela de tipos de serviço
    c.execute("""
        CREATE TABLE IF NOT EXISTS tipos_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # tabela de ordens de serviço
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo_servico_id INTEGER NOT NULL,
            situacao TEXT NOT NULL DEFAULT 'Aberta',
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
        )
    """)

    # cria admin padrão, se não existir
    c.execute("SELECT * FROM usuarios WHERE usuario=?", ("admin",))
    if not c.fetchone():
        senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt())
        c.execute("INSERT INTO usuarios (usuario, senha, admin) VALUES (?, ?, ?)",
                  ("admin", senha_hash, 1))

    conn.commit()
    conn.close()

# ==========================
# USUÁRIOS
# ==========================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(senha.encode("utf-8"), user[2]):
        return user
    return None

def criar_usuario(usuario, senha, admin=0):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
    c.execute("INSERT INTO usuarios (usuario, senha, admin) VALUES (?, ?, ?)", (usuario, senha_hash, admin))
    conn.commit()
    conn.close()

# ==========================
# PDF
# ==========================
def gerar_pdf_os(os_dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Ordem de Servico", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    for k, v in os_dados.items():
        pdf.cell(200, 10, f"{k}: {v}", ln=True)

    return pdf.output(dest="S").encode("latin1")

# ==========================
# TELAS
# ==========================
def login_screen():
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = {"id": user[0], "nome": user[1], "admin": bool(user[3])}
            st.success(f"Bem-vindo, {usuario}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

def menu_cadastros():
    submenu = st.sidebar.radio("Cadastro", ["Nenhum", "Empresa", "Tipo de Serviço", "Usuário"], index=0)

    if submenu == "Empresa":
        st.subheader("Cadastro de Empresa")
        with st.form("cad_empresa"):
            nome = st.text_input("Empresa *")
            cnpj = st.text_input("CNPJ *")
            telefone = st.text_input("Telefone *")
            rua = st.text_input("Rua")
            numero = st.text_input("Número")
            cep = st.text_input("CEP")
            cidade = st.text_input("Cidade")
            estado = st.text_input("Estado")
            submit = st.form_submit_button("Salvar")
            if submit:
                if not nome or not cnpj or not telefone:
                    st.error("Campos obrigatórios: Empresa, CNPJ e Telefone")
                else:
                    conn = sqlite3.connect("sistema.db")
                    c = conn.cursor()
                    c.execute("""INSERT INTO empresas (nome, cnpj, telefone, rua, numero, cep, cidade, estado)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                              (nome, cnpj, telefone, rua, numero, cep, cidade, estado))
                    conn.commit()
                    conn.close()
                    st.success("Empresa cadastrada!")

    elif submenu == "Tipo de Serviço":
        st.subheader("Cadastro de Tipo de Serviço")
        with st.form("cad_servico"):
            nome = st.text_input("Nome do Serviço *")
            submit = st.form_submit_button("Salvar")
            if submit:
                if not nome:
                    st.error("Nome é obrigatório.")
                else:
                    conn = sqlite3.connect("sistema.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
                    conn.commit()
                    conn.close()
                    st.success("Serviço cadastrado!")

    elif submenu == "Usuário":
        if st.session_state["usuario"]["admin"]:
            st.subheader("Cadastro de Usuário")
            with st.form("cad_usuario"):
                nome = st.text_input("Usuário *")
                senha = st.text_input("Senha *", type="password")
                admin = st.checkbox("Administrador?")
                submit = st.form_submit_button("Salvar")
                if submit:
                    if not nome or not senha:
                        st.error("Usuário e senha são obrigatórios.")
                    else:
                        criar_usuario(nome, senha, int(admin))
                        st.success("Usuário criado com sucesso!")
        else:
            st.error("Apenas administradores podem cadastrar usuários.")

def menu_ordens():
    submenu = st.sidebar.radio("Ordem de Serviço", ["Nenhum", "Abrir OS", "Consultar OS"], index=0)

    if submenu == "Abrir OS":
        st.subheader("Abrir Ordem de Serviço")
        conn = sqlite3.connect("sistema.db")
        c = conn.cursor()
        empresas = pd.read_sql("SELECT id, nome FROM empresas", conn)
        tipos = pd.read_sql("SELECT id, nome FROM tipos_servico", conn)
        conn.close()

        with st.form("abrir_os"):
            empresa = st.selectbox("Empresa *", empresas["nome"].tolist())
            titulo = st.text_input("Título *")
            descricao = st.text_area("Descrição *")
            tipo = st.selectbox("Tipo de Serviço *", tipos["nome"].tolist())
            submit = st.form_submit_button("Abrir OS")
            if submit:
                if not empresa or not titulo or not descricao or not tipo:
                    st.error("Todos os campos são obrigatórios.")
                else:
                    empresa_id = empresas.loc[empresas["nome"] == empresa, "id"].values[0]
                    tipo_id = tipos.loc[tipos["nome"] == tipo, "id"].values[0]
                    conn = sqlite3.connect("sistema.db")
                    c = conn.cursor()
                    c.execute("""INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao)
                                 VALUES (?, ?, ?, ?, 'Aberta')""",
                              (empresa_id, titulo, descricao, tipo_id))
                    conn.commit()
                    conn.close()
                    st.success("Ordem de Serviço aberta!")

    elif submenu == "Consultar OS":
        st.subheader("Consultar Ordens de Serviço")
        situacao = st.selectbox("Filtrar Situação", ["Aberta", "Finalizada", "Todas"], index=0)

        query = """
            SELECT os.id, e.nome AS empresa, os.titulo, os.descricao, ts.nome AS tipo, os.situacao
            FROM ordens_servico os
            JOIN empresas e ON os.empresa_id = e.id
            JOIN tipos_servico ts ON os.tipo_servico_id = ts.id
        """
        if situacao != "Todas":
            query += f" WHERE os.situacao='{situacao}'"

        conn = sqlite3.connect("sistema.db")
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            st.info("Nenhuma OS encontrada.")
        else:
            st.dataframe(df)

            for i, row in df.iterrows():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"**{row['titulo']}** - {row['empresa']} ({row['situacao']})")
                with col2:
                    if st.button("Excluir", key=f"exc{row['id']}"):
                        conn = sqlite3.connect("sistema.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM ordens_servico WHERE id=?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                with col3:
                    if st.button("PDF", key=f"pdf{row['id']}"):
                        os_dados = row.to_dict()
                        pdf_bytes = gerar_pdf_os(os_dados)
                        st.download_button("Baixar PDF", data=pdf_bytes,
                                           file_name=f"OS_{row['id']}.pdf",
                                           mime="application/pdf")

# ==========================
# APP PRINCIPAL
# ==========================
def main():
    init_db()

    if "usuario" not in st.session_state:
        login_screen()
        return

    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Escolha", ["Nenhum", "Cadastros", "Ordens de Serviço", "Sair"], index=0)

    if menu == "Cadastros":
        menu_cadastros()
    elif menu == "Ordens de Serviço":
        menu_ordens()
    elif menu == "Sair":
        st.session_state.pop("usuario")
        st.rerun()

if __name__ == "__main__":
    main()
