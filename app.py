import streamlit as st
import sqlite3
import pandas as pd

# =========================
# Funções de Banco de Dados
# =========================
def get_conn():
    return sqlite3.connect("alvalav.db", check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Tabela de usuários
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT,
        is_admin INTEGER DEFAULT 0
    )
    """)

    # Criar usuário admin padrão
    c.execute("""INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin)
                 VALUES (?, ?, ?)""", ("admin", "Alv32324@", 1))

    # Tabela de empresas
    c.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        rua TEXT,
        numero TEXT,
        cep TEXT,
        cidade TEXT,
        estado TEXT,
        telefone TEXT,
        cnpj TEXT
    )
    """)

    # Tabela de serviços
    c.execute("""
    CREATE TABLE IF NOT EXISTS tipos_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
    """)

    # Tabela de ordens de serviço
    c.execute("""
    CREATE TABLE IF NOT EXISTS ordens_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER,
        tipo_servico_id INTEGER,
        titulo TEXT,
        descricao TEXT,
        situacao TEXT DEFAULT 'Aberta',
        FOREIGN KEY (empresa_id) REFERENCES empresas(id),
        FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
    )
    """)

    conn.commit()
    conn.close()

# =========================
# Autenticação
# =========================
def login():
    st.title("🔐 Login no Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        user = c.fetchone()
        conn.close()

        if user:
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario
            st.session_state["is_admin"] = bool(user[3])
            st.success(f"Bem-vindo, {usuario}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos!")

# =========================
# Cadastros
# =========================
def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")

    with st.form("empresa_form"):
        nome = st.text_input("Nome da Empresa")
        rua = st.text_input("Rua")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        telefone = st.text_input("Telefone")
        cnpj = st.text_input("CNPJ")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO empresas (nome, rua, numero, cep, cidade, estado, telefone, cnpj)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (nome, rua, numero, cep, cidade, estado, telefone, cnpj))
            conn.commit()
            conn.close()
            st.success("✅ Empresa cadastrada com sucesso!")

def cadastro_usuario():
    if not st.session_state.get("is_admin", False):
        st.warning("⚠️ Apenas o administrador pode cadastrar usuários.")
        return

    st.subheader("👤 Cadastro de Usuário")

    with st.form("usuario_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha")
        is_admin = st.checkbox("Administrador?")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                      (usuario, senha, int(is_admin)))
            conn.commit()
            conn.close()
            st.success("✅ Usuário cadastrado com sucesso!")

def cadastro_servico():
    st.subheader("🛠 Cadastro de Tipo de Serviço")

    with st.form("servico_form"):
        nome = st.text_input("Nome do Serviço")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
            st.success("✅ Tipo de serviço cadastrado com sucesso!")

# =========================
# Ordens de Serviço
# =========================
def abrir_os():
    st.subheader("📄 Abrir Ordem de Serviço")

    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    c.execute("SELECT id, nome FROM tipos_servico")
    servicos = c.fetchall()
    conn.close()

    empresa = st.selectbox("Empresa", empresas, format_func=lambda x: x[1] if x else "")
    servico = st.selectbox("Tipo de Serviço", servicos, format_func=lambda x: x[1] if x else "")
    titulo = st.text_input("Título")
    descricao = st.text_area("Descrição")

    if st.button("Abrir OS"):
        if empresa and servico and titulo:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO ordens_servico (empresa_id, tipo_servico_id, titulo, descricao, situacao)
                         VALUES (?, ?, ?, ?, 'Aberta')""",
                      (empresa[0], servico[0], titulo, descricao))
            conn.commit()
            conn.close()
            st.success("✅ Ordem de Serviço criada com sucesso!")
        else:
            st.error("⚠️ Preencha todos os campos obrigatórios!")

def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT situacao FROM ordens_servico")
    situacoes = [row[0] for row in c.fetchall()]
    situacao = st.selectbox("Filtrar por Situação", [""] + situacoes)

    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    empresa = st.selectbox("Filtrar por Empresa", [""] + [e[1] for e in empresas])

    query = """SELECT os.id, e.nome, os.titulo, os.situacao, os.descricao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id
               WHERE 1=1"""
    params = []

    if situacao:
        query += " AND os.situacao=?"
        params.append(situacao)
    if empresa:
        query += " AND e.nome=?"
        params.append(empresa)

    c.execute(query, params)
    dados = c.fetchall()
    conn.close()

    if not dados:
        st.info("Nenhuma OS encontrada.")
        return

    df = pd.DataFrame(dados, columns=["CÓDIGO", "EMPRESA", "TÍTULO", "SITUAÇÃO", "DESCRIÇÃO"])
    st.dataframe(df[["CÓDIGO", "EMPRESA", "TÍTULO", "SITUAÇÃO"]], use_container_width=True)

    codigo = st.selectbox("Selecione o CÓDIGO da OS:", df["CÓDIGO"])

    if codigo:
        os_dados = df[df["CÓDIGO"] == codigo].iloc[0]

        with st.expander("✏️ Editar OS"):
            novo_titulo = st.text_input("Título", os_dados["TÍTULO"])
            nova_descricao = st.text_area("Descrição", os_dados["DESCRIÇÃO"])
            nova_situacao = st.selectbox("Situação", ["Aberta", "Finalizada"],
                                         index=0 if os_dados["SITUAÇÃO"] == "Aberta" else 1)

            if st.button("Salvar Alterações"):
                conn = get_conn()
                c = conn.cursor()
                c.execute("""UPDATE ordens_servico 
                             SET titulo=?, descricao=?, situacao=? 
                             WHERE id=?""",
                          (novo_titulo, nova_descricao, nova_situacao, int(codigo)))
                conn.commit()
                conn.close()
                st.success("✅ OS atualizada com sucesso!")
                st.rerun()

        with st.expander("❌ Excluir OS"):
            if st.button("Confirmar Exclusão"):
                conn = get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM ordens_servico WHERE id=?", (int(codigo),))
                conn.commit()
                conn.close()
                st.success("🗑 OS excluída com sucesso!")
                st.rerun()

# =========================
# Menu Principal
# =========================
def menu():
    st.sidebar.title("📌 Menu Principal")
    escolha = st.sidebar.selectbox("Escolha uma opção", ["", "Cadastros", "Ordens de Serviço"])

    if escolha == "Cadastros":
        submenu = st.sidebar.radio("Cadastros", ["Cadastro Empresa", "Cadastro Usuário", "Cadastro Tipo de Serviço"])
        if submenu == "Cadastro Empresa":
            cadastro_empresa()
        elif submenu == "Cadastro Usuário":
            cadastro_usuario()
        elif submenu == "Cadastro Tipo de Serviço":
            cadastro_servico()

    elif escolha == "Ordens de Serviço":
        submenu = st.sidebar.radio("Ordens de Serviço", ["Abrir OS", "Consultar OS"])
        if submenu == "Abrir OS":
            abrir_os()
        elif submenu == "Consultar OS":
            consultar_os()

# =========================
# Aplicação
# =========================
init_db()

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    login()
else:
    menu()
