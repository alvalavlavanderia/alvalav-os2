import streamlit as st
import sqlite3
import bcrypt

DB = "sistema_os.db"

# ----------------------
# Banco
# ----------------------
def criar_banco():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL
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
            empresa_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo_servico_id INTEGER NOT NULL,
            situacao TEXT NOT NULL,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            FOREIGN KEY (tipo_servico_id) REFERENCES servicos(id)
        )
    """)

    # cria admin apenas se não existir (senha padrão 1234 -> armazenada com bcrypt)
    c.execute("SELECT id FROM usuarios WHERE usuario = 'admin'")
    if not c.fetchone():
        senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        c.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", ("admin", senha_hash, "admin"))

    conn.commit()
    conn.close()


# ----------------------
# Autenticação (com fallback)
# ----------------------
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user = c.fetchone()
    conn.close()
    if not user:
        return None

    senha_bd = user[2]  # string
    # tenta bcrypt (hash armazenado como string->encode)
    try:
        if bcrypt.checkpw(senha.encode("utf-8"), senha_bd.encode("utf-8")):
            return user
    except Exception:
        # fallback: se banco tinha senha em texto claro
        if senha == senha_bd:
            return user
    return None


# ----------------------
# Funções auxiliares OS
# ----------------------
def listar_ordens_por_situacao(situacao):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if situacao == "Todas":
        c.execute("""
            SELECT o.id, e.nome, o.titulo, o.descricao, ts.nome, o.situacao
            FROM ordens o
            JOIN empresas e ON o.empresa_id = e.id
            JOIN servicos ts ON o.tipo_servico_id = ts.id
            ORDER BY o.id DESC
        """)
    else:
        c.execute("""
            SELECT o.id, e.nome, o.titulo, o.descricao, ts.nome, o.situacao
            FROM ordens o
            JOIN empresas e ON o.empresa_id = e.id
            JOIN servicos ts ON o.tipo_servico_id = ts.id
            WHERE o.situacao = ?
            ORDER BY o.id DESC
        """, (situacao,))
    rows = c.fetchall()
    conn.close()
    return rows


def apagar_ordem(ordem_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM ordens WHERE id = ?", (ordem_id,))
    conn.commit()
    conn.close()


def atualizar_ordem(ordem_id, empresa_id, titulo, descricao, tipo_servico_id, situacao):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        UPDATE ordens
        SET empresa_id=?, titulo=?, descricao=?, tipo_servico_id=?, situacao=?
        WHERE id=?
    """, (empresa_id, titulo, descricao, tipo_servico_id, situacao, ordem_id))
    conn.commit()
    conn.close()


# ----------------------
# Tela de edição OS
# ----------------------
def editar_os(ordem_id):
    st.markdown("---")
    st.subheader(f"✏️ Editar OS #{ordem_id}")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # pegamos dados completos da OS
    c.execute("""
        SELECT o.id, o.empresa_id, e.nome, o.titulo, o.descricao, o.tipo_servico_id, ts.nome, o.situacao
        FROM ordens o
        JOIN empresas e ON o.empresa_id = e.id
        JOIN servicos ts ON o.tipo_servico_id = ts.id
        WHERE o.id = ?
    """, (ordem_id,))
    ordem = c.fetchone()
    # listas para selects
    empresas = c.execute("SELECT id, nome FROM empresas ORDER BY nome").fetchall()
    servicos = c.execute("SELECT id, nome FROM servicos ORDER BY nome").fetchall()
    conn.close()

    if not ordem:
        st.error("OS não encontrada.")
        return

    # montar opções para selectbox e definir índice padrão
    empresas_opts = [f"{e[0]} - {e[1]}" for e in empresas]
    servicos_opts = [f"{s[0]} - {s[1]}" for s in servicos]

    empresa_atual_id = ordem[1]
    servico_atual_id = ordem[5]

    try:
        empresa_index = next(i for i, v in enumerate(empresas_opts) if v.startswith(f"{empresa_atual_id} -"))
    except StopIteration:
        empresa_index = 0
    try:
        servico_index = next(i for i, v in enumerate(servicos_opts) if v.startswith(f"{servico_atual_id} -"))
    except StopIteration:
        servico_index = 0

    # Form de edição (Salvar dentro do form; Cancel fora)
    with st.form(f"form_edit_os_{ordem_id}"):
        empresa_sel = st.selectbox("Empresa *", empresas_opts, index=empresa_index)
        titulo = st.text_input("Título *", value=ordem[3])
        descricao = st.text_area("Descrição *", value=ordem[4])
        servico_sel = st.selectbox("Tipo de Serviço *", servicos_opts, index=servico_index)
        situacao = st.selectbox("Situação *", ["Aberta", "Finalizada"], index=0 if ordem[7] == "Aberta" else 1)

        submitted = st.form_submit_button("💾 Salvar Alterações")

        if submitted:
            empresa_id = int(empresa_sel.split(" - ")[0])
            servico_id = int(servico_sel.split(" - ")[0])

            atualizar_ordem(ordem_id, empresa_id, titulo.strip(), descricao.strip(), servico_id, situacao)
            st.success("✅ OS atualizada com sucesso!")
            # limpa o estado de edição e atualiza a tela
            if "editando_os" in st.session_state:
                st.session_state.pop("editando_os")
            st.rerun()

    # botão Cancelar OUTSIDE do form
    if st.button("↩️ Cancelar Edição", key=f"cancel_{ordem_id}"):
        if "editando_os" in st.session_state:
            st.session_state.pop("editando_os")
        st.info("Edição cancelada.")
        st.rerun()


# ----------------------
# Tela de listagem (consultar) -> com editar / excluir
# ----------------------
def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")
    filtro = st.radio("Filtrar por situação:", ["Aberta", "Finalizada", "Todas"], index=0, horizontal=True)

    rows = listar_ordens_por_situacao(filtro)

    if not rows:
        st.info("Nenhuma OS encontrada.")
        return

    # Exibir com botões por linha
    for row in rows:
        ordem_id, empresa_nome, titulo, descricao, servico_nome, situacao = row
        cols = st.columns([6, 1, 1])
        with cols[0]:
            st.markdown(f"**OS #{ordem_id}** — **{titulo}**")
            st.caption(f"{empresa_nome}  •  {servico_nome}  •  Situação: **{situacao}**")
            st.write(descricao)
        with cols[1]:
            # botão Editar
            if st.button("✏️", key=f"edit_btn_{ordem_id}", help="Editar OS"):
                # marca sistema para edição e força rerun para mostrar o form abaixo
                st.session_state["editando_os"] = ordem_id
                st.rerun()
        with cols[2]:
            # botão Excluir
            if st.button("🗑️", key=f"del_btn_{ordem_id}", help="Excluir OS"):
                apagar_ordem(ordem_id)
                st.success(f"OS #{ordem_id} excluída.")
                st.rerun()

    # Se estamos editando alguma OS, mostramos o form de edição (abaixo da lista)
    if "editando_os" in st.session_state:
        editar_os(st.session_state["editando_os"])


# ----------------------
# Abrir OS (form)
# ----------------------
def abrir_os():
    st.subheader("📄 Abrir Nova Ordem de Serviço")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    empresas = c.execute("SELECT id, nome FROM empresas ORDER BY nome").fetchall()
    servicos = c.execute("SELECT id, nome FROM servicos ORDER BY nome").fetchall()
    conn.close()

    if not empresas:
        st.warning("Cadastre ao menos uma empresa antes de abrir OS.")
        return
    if not servicos:
        st.warning("Cadastre ao menos um tipo de serviço antes de abrir OS.")
        return

    empresas_opts = [f"{e[0]} - {e[1]}" for e in empresas]
    servicos_opts = [f"{s[0]} - {s[1]}" for s in servicos]

    with st.form("form_nova_os", clear_on_submit=True):
        empresa_sel = st.selectbox("Empresa *", empresas_opts)
        titulo = st.text_input("Título *")
        descricao = st.text_area("Descrição *")
        servico_sel = st.selectbox("Tipo de Serviço *", servicos_opts)
        # situação é automaticamente Aberta na criação
        submitted = st.form_submit_button("Abrir OS")
        if submitted:
            # valida
            if not (empresa_sel and titulo.strip() and descricao.strip() and servico_sel):
                st.error("Preencha todos os campos obrigatórios.")
            else:
                empresa_id = int(empresa_sel.split(" - ")[0])
                servico_id = int(servico_sel.split(" - ")[0])
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO ordens (empresa_id, titulo, descricao, tipo_servico_id, situacao)
                    VALUES (?, ?, ?, ?, ?)
                """, (empresa_id, titulo.strip(), descricao.strip(), servico_id, "Aberta"))
                conn.commit()
                conn.close()
                st.success("✅ OS aberta com sucesso!")
                st.rerun()


# ----------------------
# Outros cadastros (empresa/serviço/usuario) — simples
# ----------------------
def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")
    with st.form("form_empresa", clear_on_submit=True):
        nome = st.text_input("Empresa *").strip()
        cnpj = st.text_input("CNPJ *").strip()
        telefone = st.text_input("Telefone *").strip()
        rua = st.text_input("Rua *").strip()
        cep = st.text_input("CEP *").strip()
        numero = st.text_input("Número *").strip()
        cidade = st.text_input("Cidade *").strip()
        estado = st.text_input("Estado *").strip()
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if not all([nome, cnpj, telefone, rua, cep, numero, cidade, estado]):
                st.error("Todos os campos são obrigatórios.")
            else:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, cnpj, telefone, rua, cep, numero, cidade, estado))
                conn.commit()
                conn.close()
                st.success("Empresa cadastrada com sucesso.")
                st.rerun()


def cadastro_servico():
    st.subheader("🛠 Cadastro Tipo de Serviço")
    with st.form("form_servico", clear_on_submit=True):
        nome = st.text_input("Nome do serviço *").strip()
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if not nome:
                st.error("Nome é obrigatório.")
            else:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("INSERT INTO servicos (nome) VALUES (?)", (nome,))
                conn.commit()
                conn.close()
                st.success("Serviço cadastrado.")
                st.rerun()


def cadastro_usuario():
    st.subheader("👤 Cadastro de Usuário (apenas admin)")
    # checar se é admin
    if "usuario" not in st.session_state or st.session_state["usuario"][3] != "admin":
        st.error("Apenas administradores podem cadastrar usuários.")
        return
    with st.form("form_usuario", clear_on_submit=True):
        nome = st.text_input("Usuário *").strip()
        senha = st.text_input("Senha *", type="password").strip()
        tipo = st.selectbox("Tipo", ["admin", "comum"])
        submitted = st.form_submit_button("Salvar")
        if submitted:
            if not (nome and senha):
                st.error("Usuário e senha obrigatórios.")
            else:
                senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (nome, senha_hash, tipo))
                    conn.commit()
                    st.success("Usuário cadastrado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Usuário já existe.")
                conn.close()


# ----------------------
# Interface principal
# ----------------------
def main():
    criar_banco()
    st.title("📂 Sistema de Ordens de Serviço")

    # login
    if "usuario" not in st.session_state:
        st.subheader("🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            user = autenticar_usuario(usuario, senha)
            if user:
                st.session_state["usuario"] = user
                st.success(f"Bem-vindo, {user[1]}!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        return

    # menu lateral (expanders)
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

    # roteamento
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
