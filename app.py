import streamlit as st
import sqlite3
import bcrypt

# ========== BANCO DE DADOS ==========
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

    # Criar usuário admin padrão (senha fixa "1234")
    senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    c.execute("INSERT OR IGNORE INTO usuarios (id, usuario, senha, tipo) VALUES (1, 'admin', ?, 'admin')", (senha_hash,))
    
    conn.commit()
    conn.close()

# ========== AUTENTICAÇÃO ==========
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(senha.encode("utf-8"), user[2].encode("utf-8")):
        return {"id": user[0], "usuario": user[1], "tipo": user[3]}
    return None

# ========== TELAS DO SISTEMA ==========
def cadastro_empresa():
    st.subheader("Cadastro de Empresa")
    with st.form("form_empresa"):
        nome = st.text_input("Nome da Empresa*")
        cnpj = st.text_input("CNPJ*")
        telefone = st.text_input("Telefone*")
        rua = st.text_input("Rua*")
        cep = st.text_input("CEP*")
        numero = st.text_input("Número*")
        cidade = st.text_input("Cidade*")
        estado = st.text_input("Estado*")
        submit = st.form_submit_button("Salvar")

        if submit:
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
                st.error("Preencha todos os campos obrigatórios!")

def cadastro_tipo_servico():
    st.subheader("Cadastro de Tipo de Serviço")
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()

    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço*")
        submit = st.form_submit_button("Salvar")

        if submit and nome:
            c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
            conn.commit()
            st.success("Serviço cadastrado com sucesso!")

    # Listagem e edição
    st.write("### Serviços Cadastrados")
    c.execute("SELECT * FROM tipos_servico")
    servicos = c.fetchall()
    for s in servicos:
        novo_nome = st.text_input(f"Editar Serviço {s[0]}", s[1], key=f"servico_{s[0]}")
        if st.button(f"Salvar {s[0]}", key=f"btn_{s[0]}"):
            c.execute("UPDATE tipos_servico SET nome=? WHERE id=?", (novo_nome, s[0]))
            conn.commit()
            st.success("Serviço atualizado!")

    conn.close()

def cadastro_usuario():
    st.subheader("Cadastro de Usuários (apenas admin)")
    with st.form("form_usuario"):
        usuario = st.text_input("Usuário*")
        senha = st.text_input("Senha*", type="password")
        tipo = st.selectbox("Tipo*", ["admin", "usuario"])
        submit = st.form_submit_button("Salvar")

        if submit:
            if usuario and senha:
                senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                conn = sqlite3.connect("os_system.db")
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (usuario, senha_hash, tipo))
                    conn.commit()
                    st.success("Usuário cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Usuário já existe!")
                conn.close()
            else:
                st.error("Preencha todos os campos obrigatórios!")

def abrir_os():
    st.subheader("Abrir Ordem de Serviço")
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()

    # Empresas
    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    empresas_dict = {e[1]: e[0] for e in empresas}
    empresa_nome = st.selectbox("Empresa*", list(empresas_dict.keys())) if empresas else st.warning("Nenhuma empresa cadastrada.")

    # Tipos de serviço
    c.execute("SELECT id, nome FROM tipos_servico")
    tipos = c.fetchall()
    tipos_dict = {t[1]: t[0] for t in tipos}
    tipo_nome = st.selectbox("Tipo de Serviço*", list(tipos_dict.keys())) if tipos else st.warning("Nenhum tipo de serviço cadastrado.")

    titulo = st.text_input("Título*")
    descricao = st.text_area("Descrição*")

    if st.button("Abrir OS"):
        if empresa_nome and tipo_nome and titulo and descricao:
            c.execute("INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao) VALUES (?, ?, ?, ?, 'Aberta')",
                      (empresas_dict[empresa_nome], titulo, descricao, tipos_dict[tipo_nome]))
            conn.commit()
            st.success("Ordem de Serviço aberta com sucesso!")
        else:
            st.error("Preencha todos os campos obrigatórios!")

    conn.close()

def consultar_os():
    st.subheader("Consultar Ordens de Serviço")
    conn = sqlite3.connect("os_system.db")
    c = conn.cursor()

    filtro = st.radio("Filtrar por", ["Abertas", "Finalizadas", "Todas"])
    if filtro == "Abertas":
        c.execute("SELECT * FROM ordens_servico WHERE situacao='Aberta'")
    elif filtro == "Finalizadas":
        c.execute("SELECT * FROM ordens_servico WHERE situacao='Finalizada'")
    else:
        c.execute("SELECT * FROM ordens_servico")

    ordens = c.fetchall()
    for os in ordens:
        st.write(f"**ID:** {os[0]} | **Título:** {os[2]} | **Situação:** {os[5]}")
        if st.button(f"Editar {os[0]}"):
            nova_situacao = "Finalizada" if os[5] == "Aberta" else "Aberta"
            c.execute("UPDATE ordens_servico SET situacao=? WHERE id=?", (nova_situacao, os[0]))
            conn.commit()
            st.success("Situação alterada!")
        if st.button(f"Excluir {os[0]}"):
            c.execute("DELETE FROM ordens_servico WHERE id=?", (os[0],))
            conn.commit()
            st.success("Ordem excluída!")

    conn.close()

# ========== TELA PRINCIPAL ==========
def main():
    criar_banco()

    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    if not st.session_state.usuario:
        st.title("🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user = autenticar_usuario(usuario, senha)
            if user:
                st.session_state.usuario = user
                st.success(f"Bem-vindo, {user['usuario']}!")
            else:
                st.error("Usuário ou senha inválidos!")
    else:
        st.sidebar.title("Menu")
        menu = st.sidebar.radio("Selecione", ["Cadastro", "Ordem de Serviço", "Sair"], index=None)

        if menu == "Cadastro":
            submenu = st.sidebar.radio("Cadastros", ["Cadastro Empresa", "Cadastro Tipo de Serviço", "Cadastro Usuário"], index=None)
            if submenu == "Cadastro Empresa":
                cadastro_empresa()
            elif submenu == "Cadastro Tipo de Serviço":
                cadastro_tipo_servico()
            elif submenu == "Cadastro Usuário" and st.session_state.usuario["tipo"] == "admin":
                cadastro_usuario()

        elif menu == "Ordem de Serviço":
            submenu = st.sidebar.radio("Ordem de Serviço", ["Abrir OS", "Consultar OS"], index=None)
            if submenu == "Abrir OS":
                abrir_os()
            elif submenu == "Consultar OS":
                consultar_os()

        elif menu == "Sair":
            st.session_state.usuario = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()
