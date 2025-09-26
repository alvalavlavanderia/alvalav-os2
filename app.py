import streamlit as st
import sqlite3
import bcrypt

# ========================
# BANCO DE DADOS
# ========================
def criar_banco():
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()

    # Usuários
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
    """)

    # Empresas
    c.execute("""
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

    # Tipos de serviço
    c.execute("""
    CREATE TABLE IF NOT EXISTS tipos_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    """)

    # Ordens de serviço
    c.execute("""
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

    # Criar usuário admin padrão
    senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    c.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES ('admin', ?, 'admin')", (senha_hash,))

    conn.commit()
    conn.close()


# ========================
# AUTENTICAÇÃO
# ========================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(senha.encode("utf-8"), user[2].encode("utf-8")):
        return user
    return None


# ========================
# TELAS
# ========================
def login_screen():
    st.subheader("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = {"nome": user[1], "admin": (user[3] == "admin")}
            st.success(f"Bem-vindo, {user[1]}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


# CADASTRO EMPRESA
def cadastro_empresa():
    st.subheader("Cadastro de Empresa")
    nome = st.text_input("Empresa*")
    cnpj = st.text_input("CNPJ*")
    telefone = st.text_input("Telefone*")
    rua = st.text_input("Rua*")
    cep = st.text_input("CEP*")
    numero = st.text_input("Número*")
    cidade = st.text_input("Cidade*")
    estado = st.text_input("Estado*")

    if st.button("Salvar Empresa"):
        if nome and cnpj and telefone and rua and cep and numero and cidade and estado:
            conn = sqlite3.connect("os_system.db")
            c = conn.cursor()
            c.execute("""
            INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, cnpj, telefone, rua, cep, numero, cidade, estado))
            conn.commit()
            conn.close()
            st.success("Empresa cadastrada com sucesso!")
        else:
            st.error("Todos os campos são obrigatórios!")


# CADASTRO TIPO SERVIÇO
def cadastro_tipo_servico():
    st.subheader("Cadastro de Tipo de Serviço")
    nome = st.text_input("Nome do serviço")

    if st.button("Salvar Tipo de Serviço"):
        if nome:
            conn = sqlite3.connect("os_system.db")
            c = conn.cursor()
            c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
            st.success("Serviço cadastrado com sucesso!")
        else:
            st.error("Informe o nome do serviço.")


# CADASTRO USUÁRIO (somente admin)
def cadastro_usuario():
    st.subheader("Cadastro de Usuário (somente Admin)")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    tipo = st.selectbox("Tipo", ["admin", "comum"])

    if st.button("Salvar Usuário"):
        if usuario and senha:
            senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn = sqlite3.connect("os_system.db")
            c = conn.cursor()
            try:
                c.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (usuario, senha_hash, tipo))
                conn.commit()
                st.success("Usuário cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Usuário já existe.")
            conn.close()
        else:
            st.error("Preencha todos os campos.")


# ABRIR OS
def abrir_os():
    st.subheader("Abrir Ordem de Serviço")
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()
    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    c.execute("SELECT id, nome FROM tipos_servico")
    tipos = c.fetchall()
    conn.close()

    empresa = st.selectbox("Selecione a Empresa*", empresas, format_func=lambda x: x[1] if x else "")
    titulo = st.text_input("Título*")
    descricao = st.text_area("Descrição*")
    tipo_servico = st.selectbox("Tipo de Serviço*", tipos, format_func=lambda x: x[1] if x else "")

    if st.button("Abrir OS"):
        if empresa and titulo and descricao and tipo_servico:
            conn = sqlite3.connect("os_system.db")
            c = conn.cursor()
            c.execute("""
            INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao)
            VALUES (?, ?, ?, ?, 'Aberta')
            """, (empresa[0], titulo, descricao, tipo_servico[0]))
            conn.commit()
            conn.close()
            st.success("OS aberta com sucesso!")
        else:
            st.error("Preencha todos os campos obrigatórios.")


# CONSULTAR OS
def consultar_os():
    st.subheader("Consultar Ordens de Serviço")

    filtro = st.radio("Situação", ["Abertas", "Finalizadas", "Todas"])
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()

    if filtro == "Abertas":
        c.execute("SELECT * FROM ordens_servico WHERE situacao='Aberta'")
    elif filtro == "Finalizadas":
        c.execute("SELECT * FROM ordens_servico WHERE situacao='Finalizada'")
    else:
        c.execute("SELECT * FROM ordens_servico")

    ordens = c.fetchall()
    conn.close()

    for os in ordens:
        with st.expander(f"OS {os[0]} - {os[1]} - {os[5]}"):
            st.write(f"**Título:** {os[2]}")
            st.write(f"**Descrição:** {os[3]}")
            st.write(f"**Situação:** {os[5]}")

            if st.button("Excluir", key=f"del_{os[0]}"):
                conn = sqlite3.connect("os_system.db")
                c = conn.cursor()
                c.execute("DELETE FROM ordens_servico WHERE id=?", (os[0],))
                conn.commit()
                conn.close()
                st.rerun()

            if st.button("Finalizar", key=f"fin_{os[0]}"):
                conn = sqlite3.connect("os_system.db")
                c = conn.cursor()
                c.execute("UPDATE ordens_servico SET situacao='Finalizada' WHERE id=?", (os[0],))
                conn.commit()
                conn.close()
                st.rerun()


# ========================
# MAIN
# ========================
def main():
    criar_banco()

    if "usuario" not in st.session_state:
        login_screen()
        return

    st.sidebar.title("Menu")

    menu = st.sidebar.radio("Selecione uma opção", ["Cadastro", "Ordem de Serviço"], index=None)

    if menu == "Cadastro":
        submenu = st.sidebar.radio("Cadastro", ["Empresa", "Tipo de Serviço", "Usuário"], index=None)
        if submenu == "Empresa":
            cadastro_empresa()
        elif submenu == "Tipo de Serviço":
            cadastro_tipo_servico()
        elif submenu == "Usuário" and st.session_state["usuario"]["admin"]:
            cadastro_usuario()
        elif submenu == "Usuário":
            st.error("Apenas administradores podem cadastrar usuários.")

    elif menu == "Ordem de Serviço":
        submenu = st.sidebar.radio("Ordem de Serviço", ["Abrir OS", "Consultar OS"], index=None)
        if submenu == "Abrir OS":
            abrir_os()
        elif submenu == "Consultar OS":
            consultar_os()


if __name__ == "__main__":
    main()
