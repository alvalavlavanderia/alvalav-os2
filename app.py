import streamlit as st
import sqlite3
import bcrypt

# ======================
# BANCO DE DADOS
# ======================
def criar_banco():
    conn = sqlite3.connect("sistema_os.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT,
            tipo TEXT
        )
    """)

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

    c.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            titulo TEXT,
            descricao TEXT,
            tipo_servico_id INTEGER,
            situacao TEXT,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id),
            FOREIGN KEY (tipo_servico_id) REFERENCES servicos (id)
        )
    """)

    senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt())
    c.execute("INSERT OR IGNORE INTO usuarios (id, usuario, senha, tipo) VALUES (1, ?, ?, ?)",
              ("admin", senha_hash, "admin"))

    conn.commit()
    conn.close()


# ======================
# AUTENTICAÇÃO
# ======================
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("sistema_os.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(senha.encode("utf-8"), user[2]):
        return user
    return None


# ======================
# CADASTRO EMPRESA
# ======================
def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")

    with st.form("form_empresa", clear_on_submit=True):
        nome = st.text_input("Empresa*").strip()
        cnpj = st.text_input("CNPJ*").strip()
        telefone = st.text_input("Telefone*").strip()
        rua = st.text_input("Rua*").strip()
        cep = st.text_input("CEP*").strip()
        numero = st.text_input("Número*").strip()
        cidade = st.text_input("Cidade*").strip()
        estado = st.text_input("Estado*").strip()

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not all([nome, cnpj, telefone, rua, cep, numero, cidade, estado]):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                conn = sqlite3.connect("sistema_os.db")
                c = conn.cursor()
                c.execute("""
                    INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, cnpj, telefone, rua, cep, numero, cidade, estado))
                conn.commit()
                conn.close()
                st.success("✅ Empresa cadastrada com sucesso!")


# ======================
# CADASTRO SERVIÇO
# ======================
def cadastro_servico():
    st.subheader("🛠️ Cadastro de Tipo de Serviço")

    with st.form("form_servico", clear_on_submit=True):
        nome = st.text_input("Nome do Serviço*").strip()
        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not nome:
                st.error("⚠️ O nome do serviço é obrigatório.")
            else:
                conn = sqlite3.connect("sistema_os.db")
                c = conn.cursor()
                c.execute("INSERT INTO servicos (nome) VALUES (?)", (nome,))
                conn.commit()
                conn.close()
                st.success("✅ Serviço cadastrado com sucesso!")


# ======================
# CADASTRO USUÁRIO
# ======================
def cadastro_usuario():
    st.subheader("👤 Cadastro de Usuário (apenas Admin)")

    with st.form("form_usuario", clear_on_submit=True):
        usuario = st.text_input("Usuário*").strip()
        senha = st.text_input("Senha*", type="password").strip()
        tipo = st.selectbox("Tipo de Usuário*", ["admin"])
        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not usuario or not senha:
                st.error("⚠️ Usuário e senha são obrigatórios.")
            else:
                senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
                conn = sqlite3.connect("sistema_os.db")
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                              (usuario, senha_hash, tipo))
                    conn.commit()
                    st.success("✅ Usuário cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("⚠️ Usuário já existe!")
                conn.close()


# ======================
# ABRIR ORDEM DE SERVIÇO
# ======================
def abrir_os():
    st.subheader("📌 Abrir Ordem de Serviço")

    conn = sqlite3.connect("sistema_os.db")
    c = conn.cursor()
    empresas = c.execute("SELECT id, nome FROM empresas").fetchall()
    servicos = c.execute("SELECT id, nome FROM servicos").fetchall()
    conn.close()

    with st.form("form_os", clear_on_submit=True):
        empresa = st.selectbox("Empresa*", [f"{e[0]} - {e[1]}" for e in empresas]) if empresas else None
        titulo = st.text_input("Título*").strip()
        descricao = st.text_area("Descrição*").strip()
        tipo_servico = st.selectbox("Tipo de Serviço*", [f"{s[0]} - {s[1]}" for s in servicos]) if servicos else None
        situacao = "Aberta"

        submitted = st.form_submit_button("Abrir OS")

        if submitted:
            if not all([empresa, titulo, descricao, tipo_servico]):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                empresa_id = int(empresa.split(" - ")[0])
                servico_id = int(tipo_servico.split(" - ")[0])

                conn = sqlite3.connect("sistema_os.db")
                c = conn.cursor()
                c.execute("""
                    INSERT INTO ordens (empresa_id, titulo, descricao, tipo_servico_id, situacao)
                    VALUES (?, ?, ?, ?, ?)
                """, (empresa_id, titulo, descricao, servico_id, situacao))
                conn.commit()
                conn.close()
                st.success("✅ Ordem de Serviço aberta com sucesso!")


# ======================
# EDITAR ORDEM DE SERVIÇO
# ======================
def editar_os(ordem_id):
    st.subheader(f"✏️ Editar OS {ordem_id}")

    conn = sqlite3.connect("sistema_os.db")
    c = conn.cursor()
    ordem = c.execute("SELECT empresa_id, titulo, descricao, tipo_servico_id, situacao FROM ordens WHERE id=?",
                      (ordem_id,)).fetchone()
    empresas = c.execute("SELECT id, nome FROM empresas").fetchall()
    servicos = c.execute("SELECT id, nome FROM servicos").fetchall()
    conn.close()

    if not ordem:
        st.error("⚠️ OS não encontrada!")
        return

    with st.form(f"form_edit_os_{ordem_id}"):
        empresa_atual = f"{ordem[0]} - {[e[1] for e in empresas if e[0] == ordem[0]][0]}"
        empresa = st.selectbox("Empresa*", [f"{e[0]} - {e[1]}" for e in empresas], index=[f"{e[0]} - {e[1]}" for e in empresas].index(empresa_atual))
        titulo = st.text_input("Título*", ordem[1])
        descricao = st.text_area("Descrição*", ordem[2])
        servico_atual = f"{ordem[3]} - {[s[1] for s in servicos if s[0] == ordem[3]][0]}"
        tipo_servico = st.selectbox("Tipo de Serviço*", [f"{s[0]} - {s[1]}" for s in servicos], index=[f"{s[0]} - {s[1]}" for s in servicos].index(servico_atual))
        situacao = st.selectbox("Situação*", ["Aberta", "Finalizada"], index=0 if ordem[4] == "Aberta" else 1)

        submitted = st.form_submit_button("Salvar Alterações")

        if submitted:
            empresa_id = int(empresa.split(" - ")[0])
            servico_id = int(tipo_servico.split(" - ")[0])

            conn = sqlite3.connect("sistema_os.db")
            c = conn.cursor()
            c.execute("""
                UPDATE ordens
                SET empresa_id=?, titulo=?, descricao=?, tipo_servico_id=?, situacao=?
                WHERE id=?
            """, (empresa_id, titulo, descricao, servico_id, situacao, ordem_id))
            conn.commit()
            conn.close()
            st.success("✅ OS atualizada com sucesso!")


# ======================
# CONSULTAR OS
# ======================
def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")

    filtro = st.radio("Filtrar por situação:", ["Aberta", "Finalizada"])
    conn = sqlite3.connect("sistema_os.db")
    c = conn.cursor()
    ordens = c.execute("""
        SELECT o.id, e.nome, o.titulo, o.situacao
        FROM ordens o
        JOIN empresas e ON o.empresa_id = e.id
        WHERE o.situacao=?
    """, (filtro,)).fetchall()
    conn.close()

    for ordem in ordens:
        st.write(f"**ID:** {ordem[0]} | **Empresa:** {ordem[1]} | **Título:** {ordem[2]} | **Situação:** {ordem[3]}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Editar", key=f"edit_{ordem[0]}"):
                st.session_state["editando_os"] = ordem[0]
        with col2:
            if st.button("🗑️ Excluir", key=f"delete_{ordem[0]}"):
                conn = sqlite3.connect("sistema_os.db")
                c = conn.cursor()
                c.execute("DELETE FROM ordens WHERE id=?", (ordem[0],))
                conn.commit()
                conn.close()
                st.success(f"✅ OS {ordem[0]} excluída!")

    if "editando_os" in st.session_state:
        editar_os(st.session_state["editando_os"])


# ======================
# APP PRINCIPAL
# ======================
def main():
    criar_banco()
    st.title("📂 Sistema de Ordens de Serviço")

    if "usuario" not in st.session_state:
        st.subheader("🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user = autenticar_usuario(usuario, senha)
            if user:
                st.session_state["usuario"] = user
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
        return

    menu = None
    with st.sidebar:
        st.title("📋 Menu")

        with st.expander("Cadastro"):
            if st.button("Cadastro Empresa"):
                menu = "cad_empresa"
            if st.button("Cadastro Tipo de Serviço"):
                menu = "cad_servico"
            if st.button("Cadastro de Usuário"):
                menu = "cad_usuario"

        with st.expander("Ordem de Serviço"):
            if st.button("Abrir OS"):
                menu = "abrir_os"
            if st.button("Consultar OS"):
                menu = "consultar_os"

        st.write("---")
        if st.button("🚪 Logout"):
            del st.session_state["usuario"]
            st.rerun()

    if menu == "cad_empresa":
        cadastro_empresa()
    elif menu == "cad_servico":
        cadastro_servico()
    elif menu == "cad_usuario":
        cadastro_usuario()
    elif menu == "abrir_os":
        abrir_os()
    elif menu == "consultar_os":
        consultar_os()
    else:
        st.info("👈 Selecione uma opção no menu ao lado.")


if __name__ == "__main__":
    main()
