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
                    senha TEXT NOT NULL
                )''')

    # Tabela de empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    endereco TEXT,
                    numero TEXT,
                    cep TEXT,
                    cidade TEXT,
                    estado TEXT,
                    telefone TEXT NOT NULL,
                    cnpj TEXT NOT NULL
                )''')

    # Tabela de ordens de serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    tipo_servico TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    situacao TEXT NOT NULL DEFAULT 'Aberta',
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                )''')

    # Usuário admin padrão
    c.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "admin"))

    conn.commit()
    conn.close()

# ==========================
# FUNÇÕES AUXILIARES
# ==========================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user = c.fetchone()
    conn.close()
    return user

def cadastrar_empresa(nome, endereco, numero, cep, cidade, estado, telefone, cnpj):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("INSERT INTO empresas (nome, endereco, numero, cep, cidade, estado, telefone, cnpj) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (nome, endereco, numero, cep, cidade, estado, telefone, cnpj))
    conn.commit()
    conn.close()

def listar_empresas():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    conn.close()
    return empresas

def abrir_os(empresa_id, tipo_servico, titulo, descricao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("INSERT INTO ordens_servico (empresa_id, tipo_servico, titulo, descricao, situacao) VALUES (?, ?, ?, ?, 'Aberta')",
              (empresa_id, tipo_servico, titulo, descricao))
    conn.commit()
    conn.close()

def consultar_os(situacao=None, empresa_id=None):
    conn = sqlite3.connect("sistema.db")
    query = """SELECT os.id, e.nome as empresa, os.titulo, os.situacao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id
               WHERE 1=1"""
    params = []
    if situacao:
        query += " AND os.situacao=?"
        params.append(situacao)
    if empresa_id:
        query += " AND os.empresa_id=?"
        params.append(empresa_id)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def editar_os(id_os, titulo, descricao, situacao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""
        UPDATE ordens_servico
        SET titulo = ?, descricao = ?, situacao = ?
        WHERE id = ?
    """, (titulo, descricao, situacao, id_os))
    conn.commit()
    conn.close()

def excluir_os(id_os):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id=?", (id_os,))
    conn.commit()
    conn.close()

def exportar_os_pdf(id_os):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""SELECT os.id, e.nome, os.tipo_servico, os.titulo, os.descricao, os.situacao
                 FROM ordens_servico os
                 JOIN empresas e ON os.empresa_id = e.id
                 WHERE os.id=?""", (id_os,))
    os_dados = c.fetchone()
    conn.close()

    if not os_dados:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Ordem de Serviço #{os_dados[0]}", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Empresa: {os_dados[1]}", ln=True)
    pdf.cell(200, 10, txt=f"Tipo de Serviço: {os_dados[2]}", ln=True)
    pdf.cell(200, 10, txt=f"Título: {os_dados[3]}", ln=True)
    pdf.multi_cell(0, 10, txt=f"Descrição: {os_dados[4]}")
    pdf.cell(200, 10, txt=f"Situação: {os_dados[5]}", ln=True)

    filename = f"os_{os_dados[0]}.pdf"
    pdf.output(filename)
    return filename

# ==========================
# TELAS DO SISTEMA
# ==========================
def login_screen():
    st.title("🔑 Login no Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = usuario
            st.success(f"Bem-vindo, {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def main_app():
    st.sidebar.title("📋 Menu")
    menu = st.sidebar.selectbox("Escolha uma opção", ["Cadastrar Empresa", "Abrir OS", "Consultar OS", "Sair"])

    if menu == "Cadastrar Empresa":
        st.header("🏢 Cadastro de Empresa")
        nome = st.text_input("Empresa*")
        endereco = st.text_input("Rua")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        telefone = st.text_input("Telefone*")
        cnpj = st.text_input("CNPJ*")

        if st.button("Cadastrar"):
            if nome and telefone and cnpj:
                cadastrar_empresa(nome, endereco, numero, cep, cidade, estado, telefone, cnpj)
                st.success("Empresa cadastrada com sucesso!")
            else:
                st.error("Preencha todos os campos obrigatórios (*)")

    elif menu == "Abrir OS":
        st.header("📝 Abrir Ordem de Serviço")
        empresas = listar_empresas()
        empresa_dict = {e[1]: e[0] for e in empresas}
        empresa = st.selectbox("Empresa*", [""] + list(empresa_dict.keys()))
        tipo_servico = st.text_input("Tipo de Serviço*")
        titulo = st.text_input("Título*")
        descricao = st.text_area("Descrição*")

        if st.button("Abrir OS"):
            if empresa and tipo_servico and titulo and descricao:
                abrir_os(empresa_dict[empresa], tipo_servico, titulo, descricao)
                st.success("Ordem de Serviço aberta com sucesso!")
            else:
                st.error("Preencha todos os campos obrigatórios (*)")

    elif menu == "Consultar OS":
        st.header("🔍 Consultar Ordens de Serviço")
        situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Finalizada"])
        empresas = listar_empresas()
        empresa_dict = {e[1]: e[0] for e in empresas}
        empresa = st.selectbox("Filtrar por Empresa", [""] + list(empresa_dict.keys()))

        empresa_id = empresa_dict.get(empresa) if empresa else None
        df = consultar_os(situacao if situacao else None, empresa_id)

        if not df.empty:
            st.dataframe(df)

            id_os = st.number_input("Informe o código da OS para Editar/Excluir/Exportar", min_value=1, step=1)

            if st.button("Exportar PDF"):
                filename = exportar_os_pdf(id_os)
                if filename:
                    with open(filename, "rb") as f:
                        st.download_button("📥 Baixar PDF", f, file_name=filename)
                else:
                    st.error("OS não encontrada.")

            if st.button("Excluir OS"):
                excluir_os(id_os)
                st.success("OS excluída com sucesso!")
                st.experimental_rerun()

        else:
            st.info("Nenhuma OS encontrada.")

    elif menu == "Sair":
        st.session_state.clear()
        st.success("Você saiu do sistema.")
        st.experimental_rerun()

# ==========================
# INICIALIZAÇÃO
# ==========================
def main():
    init_db()
    if "usuario" not in st.session_state:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main()
