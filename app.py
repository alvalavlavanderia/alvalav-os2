import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# ==============================
# BANCO DE DADOS
# ==============================
DB_NAME = "os_app.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Empresas
    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            rua TEXT,
            numero TEXT,
            cep TEXT,
            cidade TEXT,
            estado TEXT,
            telefone TEXT NOT NULL,
            cnpj TEXT NOT NULL
        )
    """)

    # Tipos de serviço
    c.execute("""
        CREATE TABLE IF NOT EXISTS tipos_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # Ordens de serviço
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            tipo_servico_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            situacao TEXT DEFAULT 'Aberta',
            data_abertura TEXT,
            data_atualizacao TEXT,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
        )
    """)

    # Usuário admin fixo
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))

    conn.commit()
    conn.close()

# ==============================
# AUTENTICAÇÃO
# ==============================
def login_user(usuario, senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, usuario, is_admin FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user = c.fetchone()
    conn.close()
    return user

def add_usuario(usuario, senha, is_admin=0):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)", (usuario, senha, is_admin))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ==============================
# CADASTROS
# ==============================
def add_empresa(nome, rua, numero, cep, cidade, estado, telefone, cnpj):
    if not nome or not telefone or not cnpj:
        return False
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO empresas (nome, rua, numero, cep, cidade, estado, telefone, cnpj)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, rua, numero, cep, cidade, estado, telefone, cnpj))
    conn.commit()
    conn.close()
    return True

def add_tipo_servico(nome):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()

def get_empresas():
    conn = get_conn()
    df = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()
    return df

def get_tipos_servico():
    conn = get_conn()
    df = pd.read_sql("SELECT id, nome FROM tipos_servico", conn)
    conn.close()
    return df

# ==============================
# ORDENS DE SERVIÇO
# ==============================
def add_os(empresa_id, tipo_servico_id, titulo, descricao):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO ordens (empresa_id, tipo_servico_id, titulo, descricao, situacao, data_abertura, data_atualizacao)
        VALUES (?, ?, ?, ?, 'Aberta', ?, ?)
    """, (empresa_id, tipo_servico_id, titulo, descricao, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()

def query_ordens(situacao=None, empresa_id=None):
    conn = get_conn()
    query = """SELECT o.id AS CODIGO, e.nome AS EMPRESA, o.titulo AS TITULO,
                      o.descricao AS DESCRICAO, o.situacao AS SITUACAO,
                      o.data_abertura, o.data_atualizacao
               FROM ordens o
               JOIN empresas e ON o.empresa_id = e.id
               WHERE 1=1"""
    params = []
    if situacao:
        query += " AND o.situacao = ?"
        params.append(situacao)
    if empresa_id:
        query += " AND o.empresa_id = ?"
        params.append(empresa_id)
    query += " ORDER BY o.id DESC"

    if params:
        df = pd.read_sql(query, conn, params=params)
    else:
        df = pd.read_sql(query, conn)

    conn.close()
    return df

def update_os(os_id, titulo, descricao, situacao):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE ordens
        SET titulo=?, descricao=?, situacao=?, data_atualizacao=?
        WHERE id=?
    """, (titulo, descricao, situacao, datetime.now(), os_id))
    conn.commit()
    conn.close()

def delete_os(os_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM ordens WHERE id=?", (os_id,))
    conn.commit()
    conn.close()

# ==============================
# TELAS
# ==============================
def login_screen():
    st.title("🔑 Login no Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = login_user(usuario, senha)
        if user:
            st.session_state['usuario'] = user[1]
            st.session_state['is_admin'] = user[2]
            st.success(f"Bem-vindo, {user[1]}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

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
        if add_empresa(nome, rua, numero, cep, cidade, estado, telefone, cnpj):
            st.success("Empresa cadastrada com sucesso!")
        else:
            st.error("Preencha os campos obrigatórios: Empresa, Telefone e CNPJ.")

def cadastro_usuario_ui():
    st.header("👤 Cadastro de Usuário (Admin)")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    is_admin = st.checkbox("Administrador?")
    if st.button("Cadastrar"):
        if add_usuario(usuario, senha, 1 if is_admin else 0):
            st.success("Usuário cadastrado!")
        else:
            st.error("Usuário já existe.")

def cadastro_tipo_servico_ui():
    st.header("🛠️ Cadastro de Tipo de Serviço")
    nome = st.text_input("Nome do Serviço")
    if st.button("Cadastrar"):
        add_tipo_servico(nome)
        st.success("Serviço cadastrado!")

def abrir_os_ui():
    st.header("📄 Abrir Ordem de Serviço")
    empresas = get_empresas()
    tipos = get_tipos_servico()

    empresa_id = st.selectbox("Empresa *", [""] + empresas['nome'].tolist())
    tipo_nome = st.selectbox("Tipo de Serviço *", [""] + tipos['nome'].tolist())
    titulo = st.text_input("Título *")
    descricao = st.text_area("Descrição *")

    if st.button("Abrir OS"):
        if empresa_id and tipo_nome and titulo and descricao:
            empresa_id = int(empresas.loc[empresas['nome'] == empresa_id, 'id'].values[0])
            tipo_id = int(tipos.loc[tipos['nome'] == tipo_nome, 'id'].values[0])
            add_os(empresa_id, tipo_id, titulo, descricao)
            st.success("OS aberta com sucesso!")
        else:
            st.error("Todos os campos são obrigatórios.")

def consultar_os_ui():
    st.header("🔍 Consultar Ordens de Serviço")

    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Finalizada"])
    empresas = get_empresas()
    empresa_nome = st.selectbox("Filtrar por Empresa", [""] + empresas['nome'].tolist())
    empresa_id = None
    if empresa_nome:
        empresa_id = int(empresas.loc[empresas['nome'] == empresa_nome, 'id'].values[0])

    df = query_ordens(situacao if situacao else None, empresa_id)

    if not df.empty:
        for _, row in df.iterrows():
            st.write(f"**Código:** {row['CODIGO']} | **Empresa:** {row['EMPRESA']} | **Título:** {row['TITULO']} | **Situação:** {row['SITUACAO']}")
            with st.expander("Detalhes / Editar"):
                titulo = st.text_input("Título", value=row['TITULO'], key=f"titulo_{row['CODIGO']}")
                descricao = st.text_area("Descrição", value=row['DESCRICAO'], key=f"desc_{row['CODIGO']}")
                situacao = st.selectbox("Situação", ["Aberta", "Finalizada"], index=0 if row['SITUACAO']=="Aberta" else 1, key=f"sit_{row['CODIGO']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar Alterações", key=f"save_{row['CODIGO']}"):
                        update_os(row['CODIGO'], titulo, descricao, situacao)
                        st.success("OS atualizada!")
                        st.rerun()
                with col2:
                    if st.button("❌ Excluir OS", key=f"del_{row['CODIGO']}"):
                        delete_os(row['CODIGO'])
                        st.warning("OS excluída!")
                        st.rerun()
            st.markdown("---")
    else:
        st.info("Nenhuma OS encontrada.")

# ==============================
# APP PRINCIPAL
# ==============================
def main():
    init_db()

    if 'usuario' not in st.session_state:
        login_screen()
        return

    st.sidebar.title("📌 Menu Principal")
    menu = st.sidebar.selectbox("Escolha uma opção", ["", "Cadastro", "Ordem de Serviço", "Sair"])

    if menu == "Cadastro":
        submenu = st.sidebar.selectbox("Cadastro", ["", "Cadastro Empresa", "Cadastro Usuário", "Cadastro Tipo de Serviço"])
        if submenu == "Cadastro Empresa":
            cadastro_empresa_ui()
        elif submenu == "Cadastro Usuário" and st.session_state.get("is_admin", 0) == 1:
            cadastro_usuario_ui()
        elif submenu == "Cadastro Tipo de Serviço":
            cadastro_tipo_servico_ui()

    elif menu == "Ordem de Serviço":
        submenu = st.sidebar.selectbox("Ordem de Serviço", ["", "Abrir OS", "Consultar OS"])
        if submenu == "Abrir OS":
            abrir_os_ui()
        elif submenu == "Consultar OS":
            consultar_os_ui()

    elif menu == "Sair":
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
