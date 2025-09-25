import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF

# --------------------------
# BANCO DE DADOS
# --------------------------

def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE,
                    senha TEXT,
                    is_admin INTEGER)''')

    # Usuário admin fixo
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))

    # Empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    endereco TEXT,
                    numero TEXT,
                    cep TEXT,
                    cidade TEXT,
                    estado TEXT,
                    telefone TEXT,
                    cnpj TEXT)''')

    # Tipos de Serviço
    c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT)''')

    # Ordens de Serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    tipo_servico_id INTEGER,
                    titulo TEXT,
                    descricao TEXT,
                    situacao TEXT,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id),
                    FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico (id))''')

    conn.commit()
    conn.close()

# ==========================
# PDF
# ==========================
def gerar_pdf_os(codigo, empresa, titulo, descricao, situacao):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)

    pdf.cell(200, 10, "Ordem de Servico", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, f"Codigo: {codigo}", ln=True)
    pdf.cell(200, 10, f"Empresa: {empresa}", ln=True)
    pdf.cell(200, 10, f"Titulo: {titulo}", ln=True)
    pdf.multi_cell(200, 10, f"Descricao: {descricao}")
    pdf.cell(200, 10, f"Situacao: {situacao}", ln=True)

    file_name = f"os_{codigo}.pdf"
    pdf.output(file_name)
    return file_name

# ==========================
# TELAS
# ==========================
def login_screen():
    st.title("🔑 Login no Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        conn = sqlite3.connect("sistema.db")
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        user = c.fetchone()
        conn.close()

        if user:
            st.session_state["usuario"] = usuario
            st.session_state["is_admin"] = user[3]
            st.success(f"Bem-vindo, {usuario}!")
        else:
            st.error("Usuário ou senha inválidos.")

def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")

    with st.form("cadastro_empresa"):
        nome = st.text_input("Empresa *")
        endereco = st.text_input("Rua")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        telefone = st.text_input("Telefone *")
        cnpj = st.text_input("CNPJ *")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            if not nome or not telefone or not cnpj:
                st.error("Preencha todos os campos obrigatórios (*)")
            else:
                conn = sqlite3.connect("sistema.db")
                c = conn.cursor()
                c.execute("INSERT INTO empresas (nome,endereco,numero,cep,cidade,estado,telefone,cnpj) VALUES (?,?,?,?,?,?,?,?)",
                          (nome, endereco, numero, cep, cidade, estado, telefone, cnpj))
                conn.commit()
                conn.close()
                st.success("Empresa cadastrada com sucesso!")

def cadastro_tipo_servico():
    st.subheader("🛠 Cadastro de Tipo de Serviço")
    nome = st.text_input("Nome do Serviço")
    if st.button("Salvar"):
        if nome:
            conn = sqlite3.connect("sistema.db")
            c = conn.cursor()
            c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
            st.success("Tipo de serviço cadastrado com sucesso!")

def cadastro_usuario():
    st.subheader("👤 Cadastro de Usuário")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    is_admin = st.checkbox("Administrador?")

    if st.button("Salvar Usuário"):
        if usuario and senha:
            conn = sqlite3.connect("sistema.db")
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?,?,?)",
                      (usuario, senha, 1 if is_admin else 0))
            conn.commit()
            conn.close()
            st.success("Usuário cadastrado com sucesso!")

def abrir_os():
    st.subheader("📌 Abrir Ordem de Serviço")

    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    empresas = c.execute("SELECT id, nome FROM empresas").fetchall()
    tipos = c.execute("SELECT id, nome FROM tipos_servico").fetchall()
    conn.close()

    empresa = st.selectbox("Empresa *", [("", "")] + empresas, format_func=lambda x: x[1] if x else "")
    tipo_servico = st.selectbox("Tipo de Serviço *", [("", "")] + tipos, format_func=lambda x: x[1] if x else "")
    titulo = st.text_input("Título *")
    descricao = st.text_area("Descrição *")

    if st.button("Salvar OS"):
        if not empresa[0] or not tipo_servico[0] or not titulo or not descricao:
            st.error("Preencha todos os campos obrigatórios (*)")
        else:
            conn = sqlite3.connect("sistema.db")
            c = conn.cursor()
            c.execute("INSERT INTO ordens_servico (empresa_id,tipo_servico_id,titulo,descricao,situacao) VALUES (?,?,?,?,?)",
                      (empresa[0], tipo_servico[0], titulo, descricao, "Aberta"))
            conn.commit()
            conn.close()
            st.success("Ordem de serviço aberta com sucesso!")

def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")

    conn = sqlite3.connect("sistema.db")
    query = """SELECT os.id, e.nome, os.titulo, os.descricao, os.situacao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id"""
    df = pd.read_sql(query, conn)
    conn.close()

    # Filtros
    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Finalizada"], index=1)
    empresa = st.selectbox("Filtrar por Empresa", [""] + df["nome"].unique().tolist())

    if situacao:
        df = df[df["situacao"] == situacao]
    if empresa:
        df = df[df["nome"] == empresa]

    if not df.empty:
        for _, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([1,2,2,2,2])
            col1.write(row["id"])
            col2.write(row["nome"])
            col3.write(row["titulo"])
            col4.write(row["situacao"])

            if col5.button("✏️", key=f"edit_{row['id']}"):
                with st.form(f"edit_form_{row['id']}"):
                    novo_titulo = st.text_input("Novo título", row["titulo"])
                    nova_desc = st.text_area("Nova descrição", row["descricao"])
                    nova_sit = st.selectbox("Situação", ["Aberta", "Finalizada"], index=0 if row["situacao"]=="Aberta" else 1)
                    submitted = st.form_submit_button("Salvar alterações")
                    if submitted:
                        conn = sqlite3.connect("sistema.db")
                        c = conn.cursor()
                        c.execute("UPDATE ordens_servico SET titulo=?, descricao=?, situacao=? WHERE id=?",
