import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from datetime import datetime

# ==============================
# BANCO DE DADOS
# ==============================
def init_db():
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()

    # Tabela de usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    # Usuário admin default
    c.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))

    # Tabela de empresas
    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            telefone TEXT NOT NULL
        )
    """)

    # Tabela de OS
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            situacao TEXT NOT NULL,
            data_abertura TEXT NOT NULL,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    """)

    conn.commit()
    conn.close()

# ==============================
# FUNÇÕES DE BANCO
# ==============================
def get_empresas():
    conn = sqlite3.connect("os_system.db")
    df = pd.read_sql("SELECT * FROM empresas", conn)
    conn.close()
    return df

def add_empresa(nome, cnpj, telefone):
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()
    c.execute("INSERT INTO empresas (nome, cnpj, telefone) VALUES (?, ?, ?)", (nome, cnpj, telefone))
    conn.commit()
    conn.close()

def add_os(empresa_id, descricao, situacao="Aberta"):
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO ordens_servico (empresa_id, descricao, situacao, data_abertura) VALUES (?, ?, ?, ?)",
        (empresa_id, descricao, situacao, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def get_os(situacao=None, empresa_id=None):
    conn = sqlite3.connect("os_system.db")
    query = """
        SELECT os.id, e.nome as empresa, os.descricao, os.situacao, os.data_abertura
        FROM ordens_servico os
        JOIN empresas e ON os.empresa_id = e.id
        WHERE 1=1
    """
    params = []
    if situacao:
        query += " AND os.situacao = ?"
        params.append(situacao)
    if empresa_id:
        query += " AND e.id = ?"
        params.append(empresa_id)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def delete_os(os_id):
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id=?", (os_id,))
    conn.commit()
    conn.close()

# ==============================
# EXPORTAR PDF
# ==============================
def gerar_pdf_os(os_data):
    """
    Gera um PDF da Ordem de Serviço usando FPDF.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Adiciona título
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(w=0, h=10, txt="Ordem de Serviço - Detalhes", ln=1, align="C")
    pdf.ln(10)

    # Adiciona os dados
    pdf.set_font("Helvetica", "", 12)
    for campo, valor in os_data.items():
        pdf.cell(w=0, h=8, txt=f"{campo}: {valor}", ln=1)

    # Cria o PDF em memória
    return BytesIO(pdf.output(dest='S').encode('latin-1'))

# ==============================
# TELAS
# ==============================
def login_screen():
    st.title("🔑 Login no Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        conn = sqlite3.connect("os_system.db")
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        user = c.fetchone()
        conn.close()

        if user:
            st.session_state["logged_in"] = True
            st.success(f"Bem-vindo, {usuario}!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def cadastrar_empresa_ui():
    st.subheader("🏢 Cadastrar Empresa")

    with st.form("form_empresa"):
        nome = st.text_input("Nome da Empresa *")
        cnpj = st.text_input("CNPJ *")
        telefone = st.text_input("Telefone *")
        submit = st.form_submit_button("Cadastrar")

        if submit:
            if not nome or not cnpj or not telefone:
                st.error("Todos os campos são obrigatórios!")
            else:
                add_empresa(nome, cnpj, telefone)
                st.success("Empresa cadastrada com sucesso!")

def abrir_os_ui():
    st.subheader("📝 Abrir Ordem de Serviço")

    empresas = get_empresas()
    if empresas.empty:
        st.warning("Cadastre uma empresa antes de abrir uma OS.")
        return

    with st.form("form_os"):
        empresa = st.selectbox("Selecione a Empresa *", empresas["nome"].tolist(), index=None, placeholder="Escolha...")
        descricao = st.text_area("Descrição *")
        submit = st.form_submit_button("Abrir OS")

        if submit:
            if not empresa or not descricao:
                st.error("Todos os campos são obrigatórios!")
            else:
                empresa_id = empresas.loc[empresas["nome"] == empresa, "id"].values[0]
                add_os(empresa_id, descricao)
                st.success("OS aberta com sucesso!")

def consultar_os_ui():
    st.subheader("📋 Consultar Ordens de Serviço")

    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Fechada"], index=1)
    empresas = get_empresas()
    empresa = st.selectbox("Filtrar por Empresa", [""] + empresas["nome"].tolist())

    empresa_id = None
    if empresa and empresa != "":
        empresa_id = empresas.loc[empresas["nome"] == empresa, "id"].values[0]

    df = get_os(situacao if situacao else None, empresa_id)

    if df.empty:
        st.info("Nenhuma OS encontrada.")
    else:
        for i, row in df.iterrows():
            st.write(f"**ID:** {row['id']} | **Empresa:** {row['empresa']} | **Situação:** {row['situacao']} | **Data:** {row['data_abertura']}")
            st.write(f"**Descrição:** {row['descricao']}")

            col1, col2, col3 = st.columns([1,1,2])
            with col1:
                if st.button(f"❌ Excluir OS {row['id']}"):
                    delete_os(row["id"])
                    st.success(f"OS {row['id']} excluída.")
                    st.rerun()
            with col2:
                os_data = {
                    "ID": row["id"],
                    "Empresa": row["empresa"],
                    "Situação": row["situacao"],
                    "Data Abertura": row["data_abertura"],
                    "Descrição": row["descricao"],
                }
                pdf_buffer = gerar_pdf_os(os_data)
                st.download_button(
                    label=f"📄 Exportar OS {row['id']} em PDF",
                    data=pdf_buffer,
                    file_name=f"os_{row['id']}.pdf",
                    mime="application/pdf"
                )
            st.markdown("---")

# ==============================
# MAIN
# ==============================
def main():
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
    else:
        menu = ["Cadastrar Empresa", "Abrir OS", "Consultar OS"]
        choice = st.sidebar.radio("Menu", menu)

        if choice == "Cadastrar Empresa":
            cadastrar_empresa_ui()
        elif choice == "Abrir OS":
            abrir_os_ui()
        elif choice == "Consultar OS":
            consultar_os_ui()

if __name__ == "__main__":
    main()
