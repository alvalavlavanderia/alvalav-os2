import streamlit as st
import sqlite3
import pandas as pd

# ==========================
# BANCO DE DADOS
# ==========================
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            admin INTEGER NOT NULL
        )
    """)

    # Empresas
    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            telefone TEXT NOT NULL,
            rua TEXT,
            cep TEXT,
            numero TEXT,
            cidade TEXT,
            estado TEXT
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
            FOREIGN KEY (empresa_id) REFERENCES empresas (id),
            FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico (id)
        )
    """)

    # Usuário admin padrão
    c.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha, admin) VALUES (?, ?, ?)", ("admin", "1234", 1))

    conn.commit()
    conn.close()


# ==========================
# FUNÇÕES DE BANCO
# ==========================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user = c.fetchone()
    conn.close()
    return user


def cadastrar_empresa(nome, cnpj, telefone, rua, cep, numero, cidade, estado):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, cnpj, telefone, rua, cep, numero, cidade, estado))
    conn.commit()
    conn.close()


def cadastrar_tipo_servico(nome):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()


def atualizar_tipo_servico(id_, nome):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("UPDATE tipos_servico SET nome=? WHERE id=?", (nome, id_))
    conn.commit()
    conn.close()


def cadastrar_usuario(usuario, senha, admin):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("INSERT INTO usuarios (usuario, senha, admin) VALUES (?, ?, ?)", (usuario, senha, admin))
    conn.commit()
    conn.close()


def cadastrar_os(empresa_id, titulo, descricao, tipo_servico_id):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao)
        VALUES (?, ?, ?, ?, ?)
    """, (empresa_id, titulo, descricao, tipo_servico_id, "Aberta"))
    conn.commit()
    conn.close()


def listar_empresas():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    conn.close()
    return empresas


def listar_tipos_servico():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("SELECT id, nome FROM tipos_servico")
    tipos = c.fetchall()
    conn.close()
    return tipos


def listar_os(situacao=None):
    conn = sqlite3.connect("sistema.db")
    query = """
        SELECT os.id, e.nome, os.titulo, os.descricao, ts.nome, os.situacao
        FROM ordens_servico os
        JOIN empresas e ON os.empresa_id = e.id
        JOIN tipos_servico ts ON os.tipo_servico_id = ts.id
    """
    params = []
    if situacao:
        query += " WHERE os.situacao=?"
        params.append(situacao)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def atualizar_os(id_, titulo, descricao, situacao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("UPDATE ordens_servico SET titulo=?, descricao=?, situacao=? WHERE id=?", 
              (titulo, descricao, situacao, id_))
    conn.commit()
    conn.close()


def excluir_os(id_):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id=?", (id_,))
    conn.commit()
    conn.close()


# ==========================
# TELAS
# ==========================
def login_screen():
    st.title("🔑 Login no Sistema")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state["usuario"] = {"nome": user[1], "admin": bool(user[3])}
            st.success(f"Bem-vindo, {usuario}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos!")


def cadastro_empresas_ui():
    st.subheader("🏢 Cadastro de Empresa")

    nome = st.text_input("Empresa*")
    cnpj = st.text_input("CNPJ*")
    telefone = st.text_input("Telefone*")
    rua = st.text_input("Rua")
    cep = st.text_input("CEP")
    numero = st.text_input("Número")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")

    if st.button("Salvar Empresa"):
        if not nome or not cnpj or not telefone:
            st.error("Empresa, CNPJ e Telefone são obrigatórios.")
        else:
            cadastrar_empresa(nome, cnpj, telefone, rua, cep, numero, cidade, estado)
            st.success("Empresa cadastrada com sucesso!")


def cadastro_tipo_servico_ui():
    st.subheader("🛠 Cadastro de Tipo de Serviço")

    nome = st.text_input("Nome do Serviço")
    if st.button("Salvar Serviço"):
        if not nome:
            st.error("O nome é obrigatório.")
        else:
            cadastrar_tipo_servico(nome)
            st.success("Serviço cadastrado com sucesso!")

    st.write("### Serviços cadastrados")
    tipos = listar_tipos_servico()
    for id_, nome in tipos:
        novo_nome = st.text_input(f"Editar serviço {id_}", value=nome, key=f"serv{id_}")
        if st.button(f"Atualizar {id_}"):
            atualizar_tipo_servico(id_, novo_nome)
            st.success("Serviço atualizado com sucesso!")
            st.rerun()


def cadastro_usuario_ui():
    if not st.session_state["usuario"]["admin"]:
        st.error("Somente administradores podem cadastrar usuários.")
        return

    st.subheader("👤 Cadastro de Usuário")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    admin = st.checkbox("Administrador?")

    if st.button("Salvar Usuário"):
        if not usuario or not senha:
            st.error("Usuário e senha são obrigatórios.")
        else:
            cadastrar_usuario(usuario, senha, 1 if admin else 0)
            st.success("Usuário cadastrado com sucesso!")


def abrir_os_ui():
    st.subheader("📝 Abrir Ordem de Serviço")

    empresas = listar_empresas()
    empresa_dict = {nome: id_ for id_, nome in empresas}
    empresa_nome = st.selectbox("Selecione a Empresa*", options=[""] + list(empresa_dict.keys()))
    empresa_id = empresa_dict.get(empresa_nome)

    titulo = st.text_input("Título*")
    descricao = st.text_area("Descrição*")

    tipos = listar_tipos_servico()
    tipo_dict = {nome: id_ for id_, nome in tipos}
    tipo_nome = st.selectbox("Tipo de Serviço*", options=[""] + list(tipo_dict.keys()))
    tipo_servico_id = tipo_dict.get(tipo_nome)

    if st.button("Salvar OS"):
        if not empresa_id or not titulo or not descricao or not tipo_servico_id:
            st.error("Todos os campos são obrigatórios.")
        else:
            cadastrar_os(empresa_id, titulo, descricao, tipo_servico_id)
            st.success("OS cadastrada com sucesso!")


def consultar_os_ui():
    st.subheader("🔍 Consultar Ordens de Serviço")

    situacao = st.selectbox("Filtrar por Situação", ["Aberta", "Finalizada", "Todas"], index=0)
    situacao = None if situacao == "Todas" else situacao

    df = listar_os(situacao=situacao)
    if not df.empty:
        for _, row in df.iterrows():
            st.write(f"**{row['titulo']}** ({row['situacao']}) - {row['nome']}")
            if st.button("Editar", key=f"edit{row['id']}"):
                novo_titulo = st.text_input("Novo Título", value=row['titulo'], key=f"titulo{row['id']}")
                nova_desc = st.text_area("Nova Descrição", value=row['descricao'], key=f"desc{row['id']}")
                nova_sit = st.selectbox("Situação", ["Aberta", "Finalizada"], index=0 if row['situacao']=="Aberta" else 1, key=f"sit{row['id']}")
                if st.button("Salvar Alterações", key=f"save{row['id']}"):
                    atualizar_os(row['id'], novo_titulo, nova_desc, nova_sit)
                    st.success("OS atualizada com sucesso!")
                    st.rerun()
            if st.button("Excluir", key=f"del{row['id']}"):
                excluir_os(row['id'])
                st.warning("OS excluída com sucesso!")
                st.rerun()
    else:
        st.info("Nenhuma OS encontrada.")


# ==========================
# MAIN
# ==========================
def main():
    init_db()

    if "usuario" not in st.session_state:
        login_screen()
        return

    st.sidebar.title("📌 Menu")

    menu = st.sidebar.radio("Selecione uma opção:", 
                            ["", "Cadastro", "Ordem de Serviço"], 
                            index=0)

    if menu == "Cadastro":
        submenu = st.sidebar.radio("Cadastros", ["", "Cadastro Empresa", "Cadastro Tipo de Serviço", "Cadastro Usuário"], index=0)
        if submenu == "Cadastro Empresa":
            cadastro_empresas_ui()
        elif submenu == "Cadastro Tipo de Serviço":
            cadastro_tipo_servico_ui()
        elif submenu == "Cadastro Usuário":
            cadastro_usuario_ui()

    elif menu == "Ordem de Serviço":
        submenu = st.sidebar.radio("OS", ["", "Abrir OS", "Consultar OS"], index=0)
        if submenu == "Abrir OS":
            abrir_os_ui()
        elif submenu == "Consultar OS":
            consultar_os_ui()

    if st.sidebar.button("Sair"):
        del st.session_state["usuario"]
        st.rerun()


if __name__ == "__main__":
    main()
