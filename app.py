import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ===============================
# BANCO DE DADOS
# ===============================
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE,
                    senha TEXT
                )''')

    # Empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    rua TEXT,
                    numero TEXT,
                    cep TEXT,
                    cidade TEXT,
                    estado TEXT,
                    telefone TEXT NOT NULL,
                    cnpj TEXT NOT NULL
                )''')

    # Ordens de Serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    tipo_servico TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    situacao TEXT DEFAULT 'Aberta',
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )''')

    # Usuário admin padrão
    c.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))

    conn.commit()
    conn.close()

# ===============================
# FUNÇÕES DE BANCO
# ===============================
def get_empresas():
    conn = sqlite3.connect("sistema.db")
    df = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()
    return df

def add_empresa(nome, rua, numero, cep, cidade, estado, telefone, cnpj):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""INSERT INTO empresas (nome, rua, numero, cep, cidade, estado, telefone, cnpj)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (nome, rua, numero, cep, cidade, estado, telefone, cnpj))
    conn.commit()
    conn.close()

def add_ordem_servico(empresa_id, tipo_servico, titulo, descricao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""INSERT INTO ordens_servico (empresa_id, tipo_servico, titulo, descricao, situacao)
                 VALUES (?, ?, ?, ?, 'Aberta')""",
              (empresa_id, tipo_servico, titulo, descricao))
    conn.commit()
    conn.close()

def query_ordens(situacao=None, empresa_id=None):
    conn = sqlite3.connect("sistema.db")
    query = """SELECT os.id AS Codigo, e.nome AS Empresa, os.titulo AS Titulo, 
                      os.descricao AS Descricao, os.situacao AS Situacao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id
               WHERE 1=1 """
    params = []

    if situacao:
        query += " AND os.situacao = ?"
        params.append(situacao)
    if empresa_id:
        query += " AND os.empresa_id = ?"
        params.append(empresa_id)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def update_ordem_servico(codigo, titulo, descricao, situacao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""UPDATE ordens_servico 
                 SET titulo = ?, descricao = ?, situacao = ?
                 WHERE id = ?""",
              (titulo, descricao, situacao, codigo))
    conn.commit()
    conn.close()

def delete_ordem_servico(codigo):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id = ?", (codigo,))
    conn.commit()
    conn.close()

# ===============================
# FUNÇÃO GERAR PDF
# ===============================
def gerar_pdf(ordem):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, "Ordem de Serviço")

    c.setFont("Helvetica", 12)
    c.drawString(50, altura - 100, f"Código: {ordem['Codigo']}")
    c.drawString(50, altura - 120, f"Empresa: {ordem['Empresa']}")
    c.drawString(50, altura - 140, f"Título: {ordem['Titulo']}")
    c.drawString(50, altura - 160, f"Situação: {ordem['Situacao']}")

    c.drawString(50, altura - 200, "Descrição:")
    text = c.beginText(50, altura - 220)
    text.setFont("Helvetica", 11)
    for linha in ordem["Descricao"].split("\n"):
        text.textLine(linha)
    c.drawText(text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ===============================
# INTERFACE - LOGIN
# ===============================
def login_screen():
    st.title("🔑 Login no Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        conn = sqlite3.connect("sistema.db")
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
        user = c.fetchone()
        conn.close()

        if user:
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.success(f"Bem-vindo, {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# ===============================
# INTERFACE - EMPRESAS
# ===============================
def cadastro_empresa_ui():
    st.header("🏢 Cadastro de Empresa")

    nome = st.text_input("Empresa *")
    rua = st.text_input("Rua")
    numero = st.text_input("Número")
    cep = st.text_input("CEP")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")
    telefone = st.text_input("Telefone *")
    cnpj = st.text_input("CNPJ *")

    if st.button("Salvar"):
        if not nome or not telefone or not cnpj:
            st.error("Preencha todos os campos obrigatórios (*).")
        else:
            add_empresa(nome, rua, numero, cep, cidade, estado, telefone, cnpj)
            st.success("Empresa cadastrada com sucesso!")

# ===============================
# INTERFACE - ORDEM DE SERVIÇO
# ===============================
def abrir_os_ui():
    st.header("📝 Abrir Ordem de Serviço")

    empresas = get_empresas()
    empresa_nome = st.selectbox("Empresa *", [""] + empresas['nome'].tolist())
    tipo_servico = st.text_input("Tipo de Serviço *")
    titulo = st.text_input("Título *")
    descricao = st.text_area("Descrição *")

    if st.button("Abrir OS"):
        if not empresa_nome or not tipo_servico or not titulo or not descricao:
            st.error("Todos os campos são obrigatórios!")
        else:
            empresa_id = int(empresas.loc[empresas['nome'] == empresa_nome, 'id'].values[0])
            add_ordem_servico(empresa_id, tipo_servico, titulo, descricao)
            st.success("Ordem de Serviço aberta com sucesso!")

# ===============================
# INTERFACE - CONSULTAR OS
# ===============================
def consultar_os_ui():
    st.header("🔍 Consultar Ordens de Serviço")

    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Finalizada"], index=1)

    empresas = get_empresas()
    empresa_nome = st.selectbox("Filtrar por Empresa", [""] + empresas['nome'].tolist())
    empresa_id = None
    if empresa_nome:
        empresa_id = int(empresas.loc[empresas['nome'] == empresa_nome, 'id'].values[0])

    df = query_ordens(situacao if situacao else None, empresa_id)

    if not df.empty:
        for i, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1,2,2,2,2,2,2])
            col1.write(row["Codigo"])
            col2.write(row["Empresa"])
            col3.write(row["Titulo"])
            col4.write(row["Situacao"])

            if col5.button("✏️ Editar", key=f"edit_{row['Codigo']}"):
                with st.form(f"form_edit_{row['Codigo']}"):
                    novo_titulo = st.text_input("Título", value=row["Titulo"])
                    nova_descricao = st.text_area("Descrição", value=row["Descricao"])
                    nova_situacao = st.selectbox("Situação", ["Aberta", "Finalizada"], 
                                                 index=0 if row["Situacao"]=="Aberta" else 1)
                    salvar = st.form_submit_button("Salvar Alterações")
                    if salvar:
                        update_ordem_servico(row["Codigo"], novo_titulo, nova_descricao, nova_situacao)
                        st.success("OS atualizada com sucesso!")
                        st.experimental_rerun()

            if col6.button("❌ Excluir", key=f"del_{row['Codigo']}"):
                delete_ordem_servico(row["Codigo"])
                st.warning("OS excluída!")
                st.experimental_rerun()

            if col7.download_button(
                label="📄 Exportar PDF",
                data=gerar_pdf(row).getvalue(),
                file_name=f"OS_{row['Codigo']}.pdf",
                mime="application/pdf",
                key=f"pdf_{row['Codigo']}"
            ):
                st.success("PDF gerado com sucesso!")
    else:
        st.info("Nenhuma OS encontrada.")

# ===============================
# MAIN APP
# ===============================
def main_app():
    st.sidebar.title("📌 Menu")
    menu = st.sidebar.radio("Escolha uma opção", ["Cadastro de Empresa", "Abrir OS", "Consultar OS"])

    if menu == "Cadastro de Empresa":
        cadastro_empresa_ui()
    elif menu == "Abrir OS":
        abrir_os_ui()
    elif menu == "Consultar OS":
        consultar_os_ui()

def main():
    init_db()
    if "logado" not in st.session_state or not st.session_state["logado"]:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main()
