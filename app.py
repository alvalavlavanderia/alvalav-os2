import streamlit as st
import sqlite3
import bcrypt
import pandas as pd

# ====================================
# BANCO DE DADOS
# ====================================
def init_db():
    conn = sqlite3.connect("os_system.db")
    cursor = conn.cursor()

    # Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            admin INTEGER NOT NULL
        )
    """)

    # Empresas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            telefone TEXT NOT NULL,
            rua TEXT NOT NULL,
            cep TEXT NOT NULL,
            numero TEXT NOT NULL,
            cidade TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)

    # Tipos de Serviço
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # Ordens de Serviço
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo_servico_id INTEGER NOT NULL,
            situacao TEXT NOT NULL,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
        )
    """)

    # Cria usuário admin padrão (senha 1234) se não existir
    senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt())
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (usuario, senha, admin)
        VALUES (?, ?, ?)
    """, ("admin", senha_hash.decode("utf-8"), 1))

    conn.commit()
    conn.close()


# ====================================
# AUTENTICAÇÃO
# ====================================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("os_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    user = cursor.fetchone()
    conn.close()

    if user:
        senha_bd = user[2]
        if bcrypt.checkpw(senha.encode("utf-8"), senha_bd.encode("utf-8")):
            return user
    return None


# ====================================
# TELAS DE CADASTRO
# ====================================
def cadastro_empresa():
    st.subheader("📌 Cadastro de Empresa")

    with st.form("form_empresa"):
        nome = st.text_input("Empresa *")
        cnpj = st.text_input("CNPJ *")
        telefone = st.text_input("Telefone *")
        rua = st.text_input("Rua *")
        cep = st.text_input("CEP *")
        numero = st.text_input("Número *")
        cidade = st.text_input("Cidade *")
        estado = st.text_input("Estado *")
        submit = st.form_submit_button("Salvar")

        if submit:
            if not (nome and cnpj and telefone and rua and cep and numero and cidade and estado):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                conn = sqlite3.connect("os_system.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, cnpj, telefone, rua, cep, numero, cidade, estado))
                conn.commit()
                conn.close()
                st.success("✅ Empresa cadastrada com sucesso!")


def cadastro_tipo_servico():
    st.subheader("🛠️ Cadastro de Tipo de Serviço")

    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço *")
        submit = st.form_submit_button("Salvar")

        if submit:
            if not nome:
                st.error("⚠️ Informe o nome do serviço.")
            else:
                conn = sqlite3.connect("os_system.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
                conn.commit()
                conn.close()
                st.success("✅ Serviço cadastrado com sucesso!")

    # Exibir serviços já cadastrados
    conn = sqlite3.connect("os_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tipos_servico")
    servicos = cursor.fetchall()
    conn.close()

    if servicos:
        st.write("### Serviços cadastrados")
        for s in servicos:
            st.write(f"- {s[1]}")


def cadastro_usuario():
    st.subheader("👤 Cadastro de Usuário (apenas Admin)")

    if not st.session_state["usuario"]["admin"]:
        st.error("⚠️ Apenas administradores podem cadastrar usuários.")
        return

    with st.form("form_usuario"):
        usuario = st.text_input("Usuário *")
        senha = st.text_input("Senha *", type="password")
        admin = st.checkbox("Administrador?")
        submit = st.form_submit_button("Salvar")

        if submit:
            if not usuario or not senha:
                st.error("⚠️ Preencha usuário e senha.")
            else:
                senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
                conn = sqlite3.connect("os_system.db")
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO usuarios (usuario, senha, admin) VALUES (?, ?, ?)",
                                   (usuario, senha_hash.decode("utf-8"), int(admin)))
                    conn.commit()
                    st.success("✅ Usuário cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("⚠️ Usuário já existe.")
                conn.close()


# ====================================
# TELAS DE ORDENS DE SERVIÇO
# ====================================
def abrir_os():
    st.subheader("📄 Abrir Ordem de Serviço")

    conn = sqlite3.connect("os_system.db")
    cursor = conn.cursor()

    # Empresas
    cursor.execute("SELECT id, nome FROM empresas")
    empresas = cursor.fetchall()
    empresa_dict = {e[1]: e[0] for e in empresas}

    # Serviços
    cursor.execute("SELECT id, nome FROM tipos_servico")
    servicos = cursor.fetchall()
    servico_dict = {s[1]: s[0] for s in servicos}

    conn.close()

    with st.form("form_os"):
        empresa = st.selectbox("Empresa *", list(empresa_dict.keys()) if empresas else ["Nenhuma cadastrada"])
        titulo = st.text_input("Título *")
        descricao = st.text_area("Descrição *")
        tipo_servico = st.selectbox("Tipo de Serviço *", list(servico_dict.keys()) if servicos else ["Nenhum cadastrado"])
        submit = st.form_submit_button("Abrir OS")

        if submit:
            if not (empresa and titulo and descricao and tipo_servico):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                conn = sqlite3.connect("os_system.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao)
                    VALUES (?, ?, ?, ?, 'Aberta')
                """, (empresa_dict[empresa], titulo, descricao, servico_dict[tipo_servico]))
                conn.commit()
                conn.close()
                st.success("✅ OS aberta com sucesso!")


def consultar_os():
    st.subheader("🔍 Consultar Ordens de Serviço")

    filtro = st.radio("Filtrar por:", ["Abertas", "Finalizadas", "Todas"], horizontal=True)

    query = "SELECT os.id, e.nome, os.titulo, os.descricao, ts.nome, os.situacao FROM ordens_servico os JOIN empresas e ON os.empresa_id = e.id JOIN tipos_servico ts ON os.tipo_servico_id = ts.id"
    if filtro == "Abertas":
        query += " WHERE os.situacao='Aberta'"
    elif filtro == "Finalizadas":
        query += " WHERE os.situacao='Finalizada'"

    conn = sqlite3.connect("os_system.db")
    cursor = conn.cursor()
    cursor.execute(query)
    ordens = cursor.fetchall()
    conn.close()

    if ordens:
        df = pd.DataFrame(ordens, columns=["ID", "Empresa", "Título", "Descrição", "Tipo Serviço", "Situação"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma OS encontrada.")


# ====================================
# LOGIN
# ====================================
def login_screen():
    st.title("🔐 Login do Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = {"id": user[0], "nome": user[1], "admin": bool(user[3])}
            st.success(f"Bem-vindo, {user[1]}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")


# ====================================
# MAIN
# ====================================
def main():
    init_db()

    if "usuario" not in st.session_state:
        login_screen()
        return

    st.sidebar.title("📌 Menu")

    menu_cadastro = ["Cadastro Empresa", "Cadastro Tipo de Serviço", "Cadastro Usuário"]
    menu_os = ["Abrir OS", "Consultar OS"]

    escolha = st.sidebar.radio("Cadastro", menu_cadastro, index=None)
    escolha_os = st.sidebar.radio("Ordem de Serviço", menu_os, index=None)

    if escolha == "Cadastro Empresa":
        cadastro_empresa()
    elif escolha == "Cadastro Tipo de Serviço":
        cadastro_tipo_servico()
    elif escolha == "Cadastro Usuário":
        cadastro_usuario()

    if escolha_os == "Abrir OS":
        abrir_os()
    elif escolha_os == "Consultar OS":
        consultar_os()


if __name__ == "__main__":
    main()
