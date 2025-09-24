import streamlit as st
import sqlite3
import pandas as pd

# ------------------- BANCO DE DADOS -------------------
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Usuários
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT,
        is_admin INTEGER DEFAULT 0
    )
    """)

    # Empresas
    c.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        endereco TEXT,
        numero TEXT,
        cep TEXT,
        cidade TEXT,
        estado TEXT,
        telefone TEXT NOT NULL,
        cnpj TEXT NOT NULL
    )
    """)

    # Ordens de Serviço
    c.execute("""
    CREATE TABLE IF NOT EXISTS ordens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        situacao TEXT DEFAULT 'Aberta',
        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
    )
    """)

    # Usuário admin padrão
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)", 
              ("admin", "Alv32324@", 1))

    conn.commit()
    conn.close()

# ------------------- FUNÇÕES AUXILIARES -------------------
def get_connection():
    return sqlite3.connect("sistema.db")

def check_login(usuario, senha):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, is_admin FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user = c.fetchone()
    conn.close()
    return user

# ------------------- LOGIN -------------------
def login_screen():
    st.title("🔑 Login no Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = check_login(usuario, senha)
        if user:
            st.session_state["logged_in"] = True
            st.session_state["usuario_id"] = user[0]
            st.session_state["is_admin"] = bool(user[1])
            st.success(f"Bem-vindo, {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# ------------------- CADASTRO DE USUÁRIOS (Admin) -------------------
def cadastro_usuarios():
    st.subheader("👤 Cadastro de Usuários")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha")
    is_admin = st.checkbox("Administrador?")

    if st.button("Cadastrar Usuário"):
        if usuario and senha:
            conn = get_connection()
            c = conn.cursor()
            try:
                c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)", 
                          (usuario, senha, 1 if is_admin else 0))
                conn.commit()
                st.success("Usuário cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Usuário já existe!")
            conn.close()
        else:
            st.error("Preencha todos os campos.")

# ------------------- CADASTRO DE EMPRESAS -------------------
def cadastro_empresas():
    st.subheader("🏢 Cadastro de Empresas")
    nome = st.text_input("Empresa *")
    endereco = st.text_input("Rua")
    numero = st.text_input("Número")
    cep = st.text_input("CEP")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")
    telefone = st.text_input("Telefone *")
    cnpj = st.text_input("CNPJ *")

    if st.button("Cadastrar Empresa"):
        if nome and telefone and cnpj:
            conn = get_connection()
            c = conn.cursor()
            c.execute("""INSERT INTO empresas 
                        (nome, endereco, numero, cep, cidade, estado, telefone, cnpj) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (nome, endereco, numero, cep, cidade, estado, telefone, cnpj))
            conn.commit()
            conn.close()
            st.success("Empresa cadastrada com sucesso!")
        else:
            st.error("Preencha todos os campos obrigatórios (*)")

# ------------------- ORDEM DE SERVIÇO -------------------
def abrir_os():
    st.subheader("📝 Abrir Ordem de Serviço")
    conn = get_connection()
    empresas = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()

    empresa_id = st.selectbox("Empresa *", [""] + empresas["nome"].tolist())
    titulo = st.text_input("Título *")
    descricao = st.text_area("Descrição *")

    if st.button("Abrir OS"):
        if empresa_id and titulo and descricao:
            conn = get_connection()
            c = conn.cursor()
            empresa_id_real = empresas.loc[empresas["nome"] == empresa_id, "id"].values[0]
            c.execute("INSERT INTO ordens (empresa_id, titulo, descricao, situacao) VALUES (?, ?, ?, ?)",
                      (empresa_id_real, titulo, descricao, "Aberta"))
            conn.commit()
            conn.close()
            st.success("OS aberta com sucesso!")
        else:
            st.error("Todos os campos são obrigatórios.")

def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")

    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Finalizada"])
    conn = get_connection()
    empresas = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()

    empresa = st.selectbox("Filtrar por Empresa", [""] + empresas["nome"].tolist())

    query = """SELECT o.id as CODIGO, e.nome as EMPRESA, o.titulo as TITULO, 
               o.descricao as DESCRICAO, o.situacao as SITUACAO 
               FROM ordens o JOIN empresas e ON o.empresa_id = e.id WHERE 1=1"""
    params = []

    if situacao:
        query += " AND o.situacao=?"
        params.append(situacao)
    if empresa:
        query += " AND e.nome=?"
        params.append(empresa)

    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)

    if not df.empty:
        st.dataframe(df[["CODIGO", "EMPRESA", "TITULO", "DESCRICAO", "SITUACAO"]])

        # Edição e exclusão
        for i, row in df.iterrows():
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button(f"✏️ Editar {row['CODIGO']}"):
                    nova_titulo = st.text_input("Novo Título", row["TITULO"], key=f"titulo{row['CODIGO']}")
                    nova_desc = st.text_area("Nova Descrição", row["DESCRICAO"], key=f"desc{row['CODIGO']}")
                    nova_sit = st.selectbox("Situação", ["Aberta", "Finalizada"], index=0 if row["SITUACAO"]=="Aberta" else 1, key=f"sit{row['CODIGO']}")
                    if st.button("Salvar Alterações", key=f"salvar{row['CODIGO']}"):
                        c = conn.cursor()
                        c.execute("UPDATE ordens SET titulo=?, descricao=?, situacao=? WHERE id=?",
                                  (nova_titulo, nova_desc, nova_sit, row["CODIGO"]))
                        conn.commit()
                        st.success("OS atualizada!")
                        st.experimental_rerun()
            with col2:
                if st.button(f"❌ Excluir {row['CODIGO']}"):
                    c = conn.cursor()
                    c.execute("DELETE FROM ordens WHERE id=?", (row["CODIGO"],))
                    conn.commit()
                    st.warning("OS excluída!")
                    st.experimental_rerun()
    else:
        st.info("Nenhuma OS encontrada.")

    conn.close()

# ------------------- MENU PRINCIPAL -------------------
def main_app():
    st.sidebar.title("📌 Menu")
    menu = ["Cadastro de Empresas", "Abrir OS", "Consultar OS"]
    if st.session_state["is_admin"]:
        menu.insert(0, "Cadastro de Usuários")
    escolha = st.sidebar.radio("Escolha uma opção", menu)

    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.experimental_rerun()

    if escolha == "Cadastro de Usuários":
        cadastro_usuarios()
    elif escolha == "Cadastro de Empresas":
        cadastro_empresas()
    elif escolha == "Abrir OS":
        abrir_os()
    elif escolha == "Consultar OS":
        consultar_os()

# ------------------- MAIN -------------------
def main():
    init_db()
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main()
