# app.py
import streamlit as st
import sqlite3
import bcrypt

DB = "sistema_os.db"

# ----------------------------
# UTIL: Conectar DB
# ----------------------------
def get_conn():
    return sqlite3.connect(DB)

# ----------------------------
# INIT DB
# ----------------------------
def init_db():
    conn = sqlite3.connect("sistema_os.db")
    c = conn.cursor()

    # Criação das tabelas
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            is_admin INTEGER NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            endereco TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tipos_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            tipo_servico_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            situacao TEXT NOT NULL,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id),
            FOREIGN KEY(tipo_servico_id) REFERENCES tipos_servico(id)
        )
    """)

    # Criar usuário admin padrão apenas se não existir
    senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    c.execute("SELECT * FROM usuarios WHERE usuario = ?", ("ADMIN",))
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                  ("ADMIN", senha_hash, 1))

    conn.commit()
    conn.close()


# ----------------------------
# AUTENTICAÇÃO
# ----------------------------
def autenticar_usuario(usuario, senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, usuario, senha, is_admin FROM usuarios WHERE usuario = ?", (usuario,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    uid, uname, senha_bd, is_admin = row
    # senha_bd é string (hash) — tentar bcrypt
    try:
        if bcrypt.checkpw(senha.encode("utf-8"), senha_bd.encode("utf-8")):
            return {"id": uid, "usuario": uname, "is_admin": bool(is_admin)}
    except Exception:
        # fallback se senha guardada em texto puro (compatibilidade)
        if senha == senha_bd:
            return {"id": uid, "usuario": uname, "is_admin": bool(is_admin)}
    return None

# ----------------------------
# USUÁRIO CRUD (apenas admin pode criar/edit/delete via UI)
# ----------------------------
def listar_usuarios():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, usuario, is_admin FROM usuarios ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def criar_usuario(usuario, senha, is_admin):
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              (usuario, senha_hash, 1 if is_admin else 0))
    conn.commit()
    conn.close()

def atualizar_usuario(uid, usuario, is_admin):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET usuario=?, is_admin=? WHERE id=?", (usuario, 1 if is_admin else 0, uid))
    conn.commit()
    conn.close()

def deletar_usuario(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    conn.commit()
    conn.close()

def mudar_senha_usuario(uid, nova_senha):
    senha_hash = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET senha=? WHERE id=?", (senha_hash, uid))
    conn.commit()
    conn.close()

# ----------------------------
# EMPRESA CRUD
# ----------------------------
def listar_empresas():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM empresas ORDER BY nome")
    rows = c.fetchall()
    conn.close()
    return rows

def criar_empresa(nome, cnpj, telefone, rua, numero, cep, cidade, estado):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO empresas (nome, cnpj, telefone, rua, numero, cep, cidade, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, cnpj, telefone, rua, numero, cep, cidade, estado))
    conn.commit()
    conn.close()

def atualizar_empresa(uid, nome, cnpj, telefone, rua, numero, cep, cidade, estado):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE empresas
        SET nome=?, cnpj=?, telefone=?, rua=?, numero=?, cep=?, cidade=?, estado=?
        WHERE id=?
    """, (nome, cnpj, telefone, rua, numero, cep, cidade, estado, uid))
    conn.commit()
    conn.close()

def deletar_empresa(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM empresas WHERE id=?", (uid,))
    conn.commit()
    conn.close()

# ----------------------------
# TIPO SERVIÇO CRUD
# ----------------------------
def listar_tipos_servico():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM tipos_servico ORDER BY nome")
    rows = c.fetchall()
    conn.close()
    return rows

def criar_tipo_servico(nome):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()

def atualizar_tipo_servico(uid, nome):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tipos_servico SET nome=? WHERE id=?", (nome, uid))
    conn.commit()
    conn.close()

def deletar_tipo_servico(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tipos_servico WHERE id=?", (uid,))
    conn.commit()
    conn.close()

# ----------------------------
# ORDEM DE SERVIÇO CRUD
# ----------------------------
def listar_ordens(situacao=None):
    conn = get_conn()
    c = conn.cursor()
    base = """
        SELECT o.id, e.nome AS empresa, o.titulo, o.descricao, ts.nome AS tipo_servico, o.situacao
        FROM ordens_servico o
        JOIN empresas e ON o.empresa_id=e.id
        JOIN tipos_servico ts ON o.tipo_servico_id=ts.id
    """
    if situacao and situacao != "Todas":
        base += " WHERE o.situacao = ? ORDER BY o.id DESC"
        c.execute(base, (situacao,))
    else:
        base += " ORDER BY o.id DESC"
        c.execute(base)
    rows = c.fetchall()
    conn.close()
    return rows

def criar_ordem(empresa_id, titulo, descricao, tipo_servico_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao)
        VALUES (?, ?, ?, ?, 'Aberta')
    """, (empresa_id, titulo, descricao, tipo_servico_id))
    conn.commit()
    conn.close()

def atualizar_ordem(uid, empresa_id, titulo, descricao, tipo_servico_id, situacao):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE ordens_servico
        SET empresa_id=?, titulo=?, descricao=?, tipo_servico_id=?, situacao=?
        WHERE id=?
    """, (empresa_id, titulo, descricao, tipo_servico_id, situacao, uid))
    conn.commit()
    conn.close()

def deletar_ordem(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id=?", (uid,))
    conn.commit()
    conn.close()

# ----------------------------
# UI: Login
# ----------------------------
def login_ui():
    st.title("🔐 Login")
    usuario = st.text_input("Usuário").strip()
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = autenticar_usuario(usuario, senha)
        if user:
            st.session_state.user = user
            st.success(f"Bem-vindo, {user['usuario']}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# ----------------------------
# UI: Cadastro > Usuários
# ----------------------------
def cadastro_usuario_ui():
    st.header("👥 Cadastro de Usuários")
    if not st.session_state.user.get("is_admin", False):
        st.error("Acesso restrito: apenas administradores podem gerenciar usuários.")
        return

    tab = st.radio("Opção", ["-- Selecione --", "Novo", "Editar / Excluir"], index=0)
    if tab == "Novo":
        with st.form("form_novo_usuario"):
            novo_usuario = st.text_input("Nome de usuário *").strip()
            nova_senha = st.text_input("Senha *", type="password")
            is_admin = st.checkbox("Tornar administrador?")
            submitted = st.form_submit_button("Criar usuário")
            if submitted:
                if not novo_usuario or not nova_senha:
                    st.error("Usuário e senha são obrigatórios.")
                else:
                    try:
                        criar_usuario(novo_usuario, nova_senha, is_admin)
                        st.success("Usuário criado com sucesso.")
                    except sqlite3.IntegrityError:
                        st.error("Usuário já existe.")
    elif tab == "Editar / Excluir":
        usuarios = listar_usuarios()
        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
            return
        st.write("Usuários cadastrados:")
        for uid, uname, is_admin in usuarios:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.markdown(f"**{uname}** {'(admin)' if is_admin else ''}")
            with cols[1]:
                if st.button("✏️", key=f"edit_user_{uid}"):
                    st.session_state.edit_user = uid
                    st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_user_{uid}"):
                    if uname == "ADMIN":
                        st.error("Não é permitido excluir o usuário padrão ADMIN.")
                    else:
                        deletar_usuario(uid)
                        st.success("Usuário excluído.")
                        st.rerun()
        # Form de edição
        if "edit_user" in st.session_state:
            uid = st.session_state.edit_user
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, usuario, is_admin FROM usuarios WHERE id=?", (uid,))
            row = c.fetchone()
            conn.close()
            if row:
                _, usuario_atual, is_admin_flag = row
                st.info(f"Editando: {usuario_atual}")
                with st.form(f"form_edit_user_{uid}"):
                    novo_nome = st.text_input("Usuário", value=usuario_atual)
                    novo_is_admin = st.checkbox("Administrador?", value=bool(is_admin_flag))
                    nova_senha = st.text_input("Nova senha (deixe em branco para manter)", type="password")
                    salvar = st.form_submit_button("Salvar alterações")
                    if salvar:
                        if novo_nome.strip() == "":
                            st.error("Nome não pode ficar vazio.")
                        else:
                            try:
                                atualizar_usuario(uid, novo_nome.strip(), novo_is_admin)
                                if nova_senha:
                                    mudar_senha_usuario(uid, nova_senha)
                                st.success("Usuário atualizado.")
                                del st.session_state.edit_user
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Nome de usuário já existe. Escolha outro.")
            else:
                st.error("Usuário não encontrado.")
                if "edit_user" in st.session_state:
                    del st.session_state.edit_user

# ----------------------------
# UI: Cadastro > Empresas
# ----------------------------
def cadastro_empresa_ui():
    st.header("🏢 Cadastro de Empresas")
    tab = st.radio("Opção", ["-- Selecione --", "Novo", "Mostrar / Editar / Excluir"], index=0)
    if tab == "Novo":
        with st.form("form_empresa_nova"):
            nome = st.text_input("Nome da Empresa *").strip()
            cnpj = st.text_input("CNPJ").strip()
            telefone = st.text_input("Telefone").strip()
            rua = st.text_input("Rua").strip()
            numero = st.text_input("Número").strip()
            cep = st.text_input("CEP").strip()
            cidade = st.text_input("Cidade").strip()
            estado = st.text_input("Estado").strip()
            submitted = st.form_submit_button("Criar empresa")
            if submitted:
                if not nome:
                    st.error("Nome da empresa é obrigatório.")
                else:
                    criar_empresa(nome, cnpj, telefone, rua, numero, cep, cidade, estado)
                    st.success("Empresa criada.")
    elif tab == "Mostrar / Editar / Excluir":
        empresas = listar_empresas()
        if not empresas:
            st.info("Nenhuma empresa cadastrada.")
            return
        st.write("Empresas:")
        for eid, ename in empresas:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.write(ename)
            with cols[1]:
                if st.button("✏️", key=f"edit_emp_{eid}"):
                    st.session_state.edit_empresa = eid
                    st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_emp_{eid}"):
                    deletar_empresa(eid)
                    st.success("Empresa excluída.")
                    st.rerun()
        # Form edição
        if "edit_empresa" in st.session_state:
            eid = st.session_state.edit_empresa
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, nome, cnpj, telefone, rua, numero, cep, cidade, estado FROM empresas WHERE id=?", (eid,))
            row = c.fetchone()
            conn.close()
            if row:
                _, nome, cnpj, telefone, rua, numero, cep, cidade, estado = row
                st.info(f"Editando {nome}")
                with st.form(f"form_edit_emp_{eid}"):
                    novo_nome = st.text_input("Nome", value=nome)
                    novo_cnpj = st.text_input("CNPJ", value=cnpj)
                    novo_tel = st.text_input("Telefone", value=telefone)
                    novo_rua = st.text_input("Rua", value=rua)
                    novo_num = st.text_input("Número", value=numero)
                    novo_cep = st.text_input("CEP", value=cep)
                    novo_cid = st.text_input("Cidade", value=cidade)
                    novo_est = st.text_input("Estado", value=estado)
                    salvar = st.form_submit_button("Salvar")
                    if salvar:
                        if not novo_nome.strip():
                            st.error("Nome é obrigatório.")
                        else:
                            atualizar_empresa(eid, novo_nome.strip(), novo_cnpj.strip(), novo_tel.strip(),
                                              novo_rua.strip(), novo_num.strip(), novo_cep.strip(), novo_cid.strip(), novo_est.strip())
                            st.success("Empresa atualizada.")
                            del st.session_state.edit_empresa
                            st.rerun()
            else:
                st.error("Empresa não encontrada.")
                del st.session_state.edit_empresa

# ----------------------------
# UI: Cadastro > Tipos de Serviço
# ----------------------------
def cadastro_tipos_servico_ui():
    st.header("🛠 Tipos de Serviço")
    tab = st.radio("Opção", ["-- Selecione --", "Novo", "Mostrar / Editar / Excluir"], index=0)
    if tab == "Novo":
        with st.form("form_novo_tipo"):
            nome = st.text_input("Nome do Tipo de Serviço *").strip()
            submitted = st.form_submit_button("Criar")
            if submitted:
                if not nome:
                    st.error("Nome é obrigatório.")
                else:
                    criar_tipo_servico(nome)
                    st.success("Tipo de serviço criado.")
    elif tab == "Mostrar / Editar / Excluir":
        tipos = listar_tipos_servico()
        if not tipos:
            st.info("Nenhum tipo de serviço cadastrado.")
            return
        for tid, tnome in tipos:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.write(tnome)
            with cols[1]:
                if st.button("✏️", key=f"edit_tipo_{tid}"):
                    st.session_state.edit_tipo = tid
                    st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_tipo_{tid}"):
                    deletar_tipo_servico(tid)
                    st.success("Tipo de serviço excluído.")
                    st.rerun()
        if "edit_tipo" in st.session_state:
            tid = st.session_state.edit_tipo
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, nome FROM tipos_servico WHERE id=?", (tid,))
            row = c.fetchone()
            conn.close()
            if row:
                _, nome_atual = row
                with st.form(f"form_edit_tipo_{tid}"):
                    novo_nome = st.text_input("Nome", value=nome_atual)
                    salvar = st.form_submit_button("Salvar")
                    if salvar:
                        if not novo_nome.strip():
                            st.error("Nome não pode ficar vazio.")
                        else:
                            atualizar_tipo_servico(tid, novo_nome.strip())
                            st.success("Tipo atualizado.")
                            del st.session_state.edit_tipo
                            st.rerun()
            else:
                st.error("Tipo não encontrado.")
                del st.session_state.edit_tipo

# ----------------------------
# UI: Ordem de Serviço -> Abrir
# ----------------------------
def abrir_os_ui():
    st.header("📄 Abrir Ordem de Serviço")
    empresas = listar_empresas()
    tipos = listar_tipos_servico()
    if not empresas:
        st.warning("Cadastre pelo menos uma empresa antes de abrir uma OS.")
        return
    if not tipos:
        st.warning("Cadastre pelo menos um tipo de serviço antes de abrir uma OS.")
        return

    opts_emp = ["-- Selecione --"] + [f"{e[0]} - {e[1]}" for e in empresas]
    opts_tipo = ["-- Selecione --"] + [f"{t[0]} - {t[1]}" for t in tipos]

    with st.form("form_abrir_os"):
        empresa_sel = st.selectbox("Empresa *", opts_emp, index=0)
        tipo_sel = st.selectbox("Tipo de Serviço *", opts_tipo, index=0)
        titulo = st.text_input("Título *").strip()
        descricao = st.text_area("Descrição *").strip()
        # Situação fixa como Aberta na criação
        submitted = st.form_submit_button("Abrir OS")
        if submitted:
            if empresa_sel == "-- Selecione --" or tipo_sel == "-- Selecione --" or not titulo or not descricao:
                st.error("Todos os campos são obrigatórios.")
            else:
                empresa_id = int(empresa_sel.split(" - ")[0])
                tipo_id = int(tipo_sel.split(" - ")[0])
                criar_ordem(empresa_id, titulo, descricao, tipo_id)
                st.success("Ordem de serviço criada (situação: Aberta).")
                st.rerun()

# ----------------------------
# UI: Ordem de Serviço -> Consultar (listar Abertas por default)
# ----------------------------
def consultar_os_ui():
    st.header("🔎 Consultar Ordens de Serviço")
    filtro = st.selectbox("Mostrar", ["Abertas", "Finalizadas", "Todas"], index=0)
    situacao = filtro if filtro != "Todas" else None
    rows = listar_ordens(situacao if situacao else "Todas")

    if not rows:
        st.info("Nenhuma OS encontrada para o filtro selecionado.")
        return

    for row in rows:
        oid, emp, titulo, descricao, tipo_serv, sit = row
        st.markdown("---")
        col_left, col_edit, col_del = st.columns([6, 1, 1])
        with col_left:
            st.markdown(f"**OS #{oid} — {titulo}**")
            st.caption(f"{emp}  •  {tipo_serv}  •  Situação: **{sit}**")
            st.write(descricao)
        with col_edit:
            if st.button("✏️", key=f"os_edit_{oid}"):
                st.session_state.editing_os = oid
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"os_del_{oid}"):
                deletar_ordem(oid)
                st.success(f"OS #{oid} excluída.")
                st.rerun()

    # Se houver edição em progresso, exibir o form de edição
    if "editing_os" in st.session_state:
        edit_id = st.session_state.editing_os
        # carregar dados atuais
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, empresa_id, titulo, descricao, tipo_servico_id, situacao
            FROM ordens_servico WHERE id=?
        """, (edit_id,))
        data = c.fetchone()
        conn.close()
        if not data:
            st.error("OS não encontrada.")
            del st.session_state.editing_os
            return

        _, empresa_id_cur, titulo_cur, descricao_cur, tipo_id_cur, sit_cur = data
        empresas = listar_empresas()
        tipos = listar_tipos_servico()
        opts_emp = [f"{e[0]} - {e[1]}" for e in empresas]
        opts_tipo = [f"{t[0]} - {t[1]}" for t in tipos]
        # encontrar índices
        try:
            emp_idx = next(i for i,v in enumerate(opts_emp) if v.startswith(f"{empresa_id_cur} -"))
        except StopIteration:
            emp_idx = 0
        try:
            tipo_idx = next(i for i,v in enumerate(opts_tipo) if v.startswith(f"{tipo_id_cur} -"))
        except StopIteration:
            tipo_idx = 0

        st.subheader(f"✏️ Editar OS #{edit_id}")
        with st.form(f"form_edit_os_{edit_id}"):
            empresa_edit = st.selectbox("Empresa *", ["-- Selecione --"] + opts_emp, index=1+emp_idx if opts_emp else 0)
            tipo_edit = st.selectbox("Tipo de Serviço *", ["-- Selecione --"] + opts_tipo, index=1+tipo_idx if opts_tipo else 0)
            titulo_edit = st.text_input("Título *", value=titulo_cur)
            descricao_edit = st.text_area("Descrição *", value=descricao_cur)
            situacao_edit = st.selectbox("Situação *", ["Aberta", "Finalizada"], index=0 if sit_cur=="Aberta" else 1)
            salvar = st.form_submit_button("Salvar alterações")
            if salvar:
                if empresa_edit == "-- Selecione --" or tipo_edit == "-- Selecione --" or not titulo_edit.strip() or not descricao_edit.strip():
                    st.error("Todos os campos obrigatórios precisam ser preenchidos.")
                else:
                    empresa_id_new = int(empresa_edit.split(" - ")[0])
                    tipo_id_new = int(tipo_edit.split(" - ")[0])
                    atualizar_ordem(edit_id, empresa_id_new, titulo_edit.strip(), descricao_edit.strip(), tipo_id_new, situacao_edit)
                    st.success("OS atualizada com sucesso.")
                    del st.session_state.editing_os
                    st.rerun()
        # Cancelar fora do form
        if st.button("↩️ Cancelar edição", key=f"cancel_os_{edit_id}"):
            if "editing_os" in st.session_state:
                del st.session_state.editing_os
            st.info("Edição cancelada.")
            st.rerun()

# ----------------------------
# APP
# ----------------------------
def main():
    st.set_page_config(page_title="Sistema OS", layout="wide")
    init_db()

    if "user" not in st.session_state:
        st.session_state.user = None

    # se não logado, exibir login
    if not st.session_state.user:
        login_ui()
        return

    # Sidebar menu (suspenso)
    st.sidebar.title("Menu")
    main_menu = st.sidebar.selectbox("Selecione", ["-- Selecione --", "CADASTRO", "ORDEM DE SERVIÇO", "SAIR"], index=0)
    submenu = None
    if main_menu == "CADASTRO":
        submenu = st.sidebar.selectbox("CADASTRO", ["-- Selecione --", "CADASTRO EMPRESA", "CADASTRO TIPO DE SERVIÇO", "CADASTRO USUÁRIO"], index=0)
    elif main_menu == "ORDEM DE SERVIÇO":
        submenu = st.sidebar.selectbox("ORDEM DE SERVIÇO", ["-- Selecione --", "ABRIR OS", "CONSULTAR OS"], index=0)
    elif main_menu == "SAIR":
        # logout
        if st.sidebar.button("Confirmar logout"):
            st.session_state.user = None
            st.rerun()

    # Roteamento
    if main_menu == "CADASTRO":
        if submenu == "CADASTRO EMPRESA":
            cadastro_empresa_ui()
        elif submenu == "CADASTRO TIPO DE SERVIÇO":
            cadastro_tipos_servico_ui()
        elif submenu == "CADASTRO USUÁRIO":
            cadastro_usuario_ui()
        else:
            st.info("Selecione uma opção em CADASTRO no menu lateral.")
    elif main_menu == "ORDEM DE SERVIÇO":
        if submenu == "ABRIR OS":
            abrir_os_ui()
        elif submenu == "CONSULTAR OS":
            consultar_os_ui()
        else:
            st.info("Selecione uma opção em ORDEM DE SERVIÇO no menu lateral.")
    else:
        st.info("Use o menu lateral para navegar (CADASTRO / ORDEM DE SERVIÇO / SAIR).")

if __name__ == "__main__":
    main()
