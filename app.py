# app.py
import streamlit as st
import sqlite3
import bcrypt
from typing import Optional, List, Tuple

DB = "sistema_os.db"

# ---------------------------
# Helpers DB
# ---------------------------
def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def safe_execute(query: str, params: tuple = ()):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit()
        result = cur.fetchall()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e
    conn.close()
    return result

# ---------------------------
# Inicializa DB (cria tabelas e ADMIN se necessário)
# ---------------------------
def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cnpj TEXT,
        telefone TEXT,
        rua TEXT,
        numero TEXT,
        cep TEXT,
        cidade TEXT,
        estado TEXT
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
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        tipo_servico_id INTEGER NOT NULL,
        situacao TEXT NOT NULL,
        FOREIGN KEY (empresa_id) REFERENCES empresas(id),
        FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
    )
    """)

    # Criar ADMIN somente se não existir (usuário padrão: ADMIN / senha: 1234)
    c.execute("SELECT id FROM usuarios WHERE usuario = ?", ("ADMIN",))
    if not c.fetchone():
        senha_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                  ("ADMIN", senha_hash, 1))

    conn.commit()
    conn.close()

# ---------------------------
# Autenticação
# ---------------------------
def authenticate(usuario: str, senha: str) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, usuario, senha, is_admin FROM usuarios WHERE usuario = ?", (usuario,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    uid, uname, senha_bd, is_admin = row
    # senha_bd armazenada como string (hash) normalmente; tratar bytes/str
    try:
        if isinstance(senha_bd, bytes):
            stored = senha_bd
        else:
            stored = senha_bd.encode("utf-8")
        if bcrypt.checkpw(senha.encode("utf-8"), stored):
            return {"id": uid, "usuario": uname, "is_admin": bool(is_admin)}
    except Exception:
        # fallback caso senha esteja em texto puro (compatibilidade)
        if senha == senha_bd:
            return {"id": uid, "usuario": uname, "is_admin": bool(is_admin)}
    return None

# ---------------------------
# Usuários CRUD
# ---------------------------
def list_users() -> List[Tuple[int, str, int]]:
    rows = safe_execute("SELECT id, usuario, is_admin FROM usuarios ORDER BY id")
    return rows

def create_user(usuario: str, senha: str, is_admin: bool):
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    safe_execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                 (usuario, senha_hash, 1 if is_admin else 0))

def update_user(uid: int, usuario: str, is_admin: bool):
    safe_execute("UPDATE usuarios SET usuario=?, is_admin=? WHERE id=?", (usuario, 1 if is_admin else 0, uid))

def update_user_password(uid: int, nova_senha: str):
    senha_hash = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    safe_execute("UPDATE usuarios SET senha=? WHERE id=?", (senha_hash, uid))

def delete_user(uid: int):
    safe_execute("DELETE FROM usuarios WHERE id=?", (uid,))

# ---------------------------
# Empresas CRUD
# ---------------------------
def list_companies() -> List[Tuple[int, str]]:
    return safe_execute("SELECT id, nome FROM empresas ORDER BY nome")

def create_company(nome, cnpj, telefone, rua, numero, cep, cidade, estado):
    safe_execute("""
        INSERT INTO empresas (nome, cnpj, telefone, rua, numero, cep, cidade, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, cnpj, telefone, rua, numero, cep, cidade, estado))

def update_company(uid, nome, cnpj, telefone, rua, numero, cep, cidade, estado):
    safe_execute("""
        UPDATE empresas SET nome=?, cnpj=?, telefone=?, rua=?, numero=?, cep=?, cidade=?, estado=? WHERE id=?
    """, (nome, cnpj, telefone, rua, numero, cep, cidade, estado, uid))

def company_has_orders(uid) -> bool:
    rows = safe_execute("SELECT 1 FROM ordens_servico WHERE empresa_id=? LIMIT 1", (uid,))
    return len(rows) > 0

def delete_company(uid):
    safe_execute("DELETE FROM empresas WHERE id=?", (uid,))

# ---------------------------
# Tipos de Serviço CRUD
# ---------------------------
def list_service_types() -> List[Tuple[int, str]]:
    return safe_execute("SELECT id, nome FROM tipos_servico ORDER BY nome")

def create_service_type(nome):
    safe_execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome,))

def update_service_type(uid, nome):
    safe_execute("UPDATE tipos_servico SET nome=? WHERE id=?", (nome, uid))

def service_type_has_orders(uid) -> bool:
    rows = safe_execute("SELECT 1 FROM ordens_servico WHERE tipo_servico_id=? LIMIT 1", (uid,))
    return len(rows) > 0

def delete_service_type(uid):
    safe_execute("DELETE FROM tipos_servico WHERE id=?", (uid,))

# ---------------------------
# Ordens de Serviço CRUD
# ---------------------------
def list_orders(situacao: Optional[str] = None) -> List[Tuple]:
    if situacao and situacao != "Todas":
        return safe_execute("""
            SELECT o.id, e.nome, o.titulo, o.descricao, ts.nome, o.situacao, o.empresa_id, o.tipo_servico_id
            FROM ordens_servico o
            JOIN empresas e ON o.empresa_id = e.id
            JOIN tipos_servico ts ON o.tipo_servico_id = ts.id
            WHERE o.situacao = ?
            ORDER BY o.id DESC
        """, (situacao,))
    else:
        return safe_execute("""
            SELECT o.id, e.nome, o.titulo, o.descricao, ts.nome, o.situacao, o.empresa_id, o.tipo_servico_id
            FROM ordens_servico o
            JOIN empresas e ON o.empresa_id = e.id
            JOIN tipos_servico ts ON o.tipo_servico_id = ts.id
            ORDER BY o.id DESC
        """)

def create_order(empresa_id: int, titulo: str, descricao: str, tipo_servico_id: int):
    safe_execute("""
        INSERT INTO ordens_servico (empresa_id, titulo, descricao, tipo_servico_id, situacao)
        VALUES (?, ?, ?, ?, 'Aberta')
    """, (empresa_id, titulo, descricao, tipo_servico_id))

def update_order(uid: int, empresa_id: int, titulo: str, descricao: str, tipo_servico_id: int, situacao: str):
    safe_execute("""
        UPDATE ordens_servico
        SET empresa_id=?, titulo=?, descricao=?, tipo_servico_id=?, situacao=?
        WHERE id=?
    """, (empresa_id, titulo, descricao, tipo_servico_id, situacao, uid))

def delete_order(uid: int):
    safe_execute("DELETE FROM ordens_servico WHERE id=?", (uid,))

# ---------------------------
# UI: Login
# ---------------------------
def ui_login():
    st.title("🔐 Login")
    with st.form("login_form"):
        usuario = st.text_input("Usuário").strip()
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
    if submitted:
        try:
            user = authenticate(usuario, senha)
        except Exception as e:
            st.error("Erro ao autenticar (ver logs).")
            return
        if user:
            st.session_state.user = user
            st.success(f"Bem-vindo, {user['usuario']}!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# ---------------------------
# UI: Usuários (Novo / Editar / Excluir) - ADMIN only
# ---------------------------
def ui_users():
    st.header("👥 Gestão de Usuários")
    if not st.session_state.user.get("is_admin", False):
        st.error("Acesso restrito: apenas administradores podem gerenciar usuários.")
        return

    option = st.radio("Opção", ["-- Selecione --", "Novo", "Editar / Excluir"], index=0, horizontal=True)

    if option == "Novo":
        with st.form("form_new_user"):
            nome = st.text_input("Usuário *").strip()
            senha = st.text_input("Senha *", type="password")
            is_admin = st.checkbox("Administrador?")
            submitted = st.form_submit_button("Criar")
        if submitted:
            if not nome or not senha:
                st.error("Usuário e senha são obrigatórios.")
            else:
                try:
                    create_user(nome, senha, is_admin)
                    st.success("Usuário criado com sucesso.")
                except sqlite3.IntegrityError:
                    st.error("Usuário já existe.")
                except Exception as e:
                    st.error("Erro ao criar usuário.")

    elif option == "Editar / Excluir":
        users = list_users()
        if not users:
            st.info("Nenhum usuário cadastrado.")
            return
        st.write("Usuários cadastrados:")
        for uid, uname, is_admin in users:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.markdown(f"**{uname}** {'(admin)' if is_admin else ''}")
            with cols[1]:
                if st.button("✏️", key=f"edit_user_{uid}"):
                    st.session_state.edit_user = uid
                    st.experimental_rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_user_{uid}"):
                    # prevenção: não deletar ADMIN padrão
                    if uname == "ADMIN":
                        st.error("Não é permitido excluir o usuário padrão ADMIN.")
                    else:
                        try:
                            delete_user(uid)
                            st.success("Usuário excluído.")
                        except Exception:
                            st.error("Erro ao excluir usuário.")
                        st.experimental_rerun()

        if "edit_user" in st.session_state:
            uid = st.session_state.edit_user
            # carregar dados
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, usuario, is_admin FROM usuarios WHERE id=?", (uid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                st.error("Usuário não encontrado.")
                del st.session_state.edit_user
                return
            _, usuario_atual, is_admin_flag = row
            st.info(f"Editando: {usuario_atual}")
            with st.form(f"form_edit_user_{uid}"):
                novo_usuario = st.text_input("Usuário *", value=usuario_atual).strip()
                novo_admin = st.checkbox("Administrador?", value=bool(is_admin_flag))
                nova_senha = st.text_input("Nova senha (deixe em branco para manter)", type="password")
                salvar = st.form_submit_button("Salvar")
            if salvar:
                if not novo_usuario:
                    st.error("Nome do usuário não pode ficar vazio.")
                else:
                    try:
                        update_user(uid, novo_usuario, novo_admin)
                        if nova_senha:
                            update_user_password(uid, nova_senha)
                        st.success("Usuário atualizado.")
                        del st.session_state.edit_user
                        st.experimental_rerun()
                    except sqlite3.IntegrityError:
                        st.error("Nome de usuário já existe.")
                    except Exception:
                        st.error("Erro ao atualizar usuário.")

# ---------------------------
# UI: Empresas (Novo / Mostrar / Editar / Excluir)
# ---------------------------
def ui_companies():
    st.header("🏢 Cadastro de Empresas")
    option = st.radio("Opção", ["-- Selecione --", "Novo", "Mostrar / Editar / Excluir"], index=0, horizontal=True)

    if option == "Novo":
        with st.form("form_new_company"):
            nome = st.text_input("Empresa *").strip()
            cnpj = st.text_input("CNPJ *").strip()
            telefone = st.text_input("Telefone *").strip()
            rua = st.text_input("Rua").strip()
            numero = st.text_input("Número").strip()
            cep = st.text_input("CEP").strip()
            cidade = st.text_input("Cidade").strip()
            estado = st.text_input("Estado").strip()
            submitted = st.form_submit_button("Criar")
        if submitted:
            if not nome or not cnpj or not telefone:
                st.error("Campos obrigatórios: Empresa, CNPJ e Telefone.")
            else:
                try:
                    create_company(nome, cnpj, telefone, rua, numero, cep, cidade, estado)
                    st.success("Empresa criada.")
                except Exception:
                    st.error("Erro ao criar empresa.")

    elif option == "Mostrar / Editar / Excluir":
        companies = list_companies()
        if not companies:
            st.info("Nenhuma empresa cadastrada.")
            return
        for cid, cname in companies:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.write(cname)
            with cols[1]:
                if st.button("✏️", key=f"edit_comp_{cid}"):
                    st.session_state.edit_company = cid
                    st.experimental_rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_comp_{cid}"):
                    # impedir exclusão se houver ordens vinculadas
                    if company_has_orders(cid):
                        st.error("Não é possível excluir: existem OS vinculadas a esta empresa.")
                    else:
                        try:
                            delete_company(cid)
                            st.success("Empresa excluída.")
                        except Exception:
                            st.error("Erro ao excluir empresa.")
                        st.experimental_rerun()

        if "edit_company" in st.session_state:
            cid = st.session_state.edit_company
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, cnpj, telefone, rua, numero, cep, cidade, estado FROM empresas WHERE id=?", (cid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                st.error("Empresa não encontrada.")
                del st.session_state.edit_company
                return
            (_, nome, cnpj, telefone, rua, numero, cep, cidade, estado) = row
            st.info(f"Editando: {nome}")
            with st.form(f"form_edit_company_{cid}"):
                novo_nome = st.text_input("Empresa *", value=nome).strip()
                novo_cnpj = st.text_input("CNPJ *", value=cnpj).strip()
                novo_tel = st.text_input("Telefone *", value=telefone).strip()
                novo_rua = st.text_input("Rua", value=rua).strip()
                novo_num = st.text_input("Número", value=numero).strip()
                novo_cep = st.text_input("CEP", value=cep).strip()
                novo_cid = st.text_input("Cidade", value=cidade).strip()
                novo_est = st.text_input("Estado", value=estado).strip()
                salvar = st.form_submit_button("Salvar")
            if salvar:
                if not novo_nome or not novo_cnpj or not novo_tel:
                    st.error("Campos obrigatórios: Empresa, CNPJ e Telefone.")
                else:
                    try:
                        update_company(cid, novo_nome, novo_cnpj, novo_tel, novo_rua, novo_num, novo_cep, novo_cid, novo_est)
                        st.success("Empresa atualizada.")
                        del st.session_state.edit_company
                        st.experimental_rerun()
                    except Exception:
                        st.error("Erro ao atualizar empresa.")

# ---------------------------
# UI: Tipos de Serviço (Novo / Mostrar / Editar / Excluir)
# ---------------------------
def ui_service_types():
    st.header("🛠 Tipos de Serviço")
    option = st.radio("Opção", ["-- Selecione --", "Novo", "Mostrar / Editar / Excluir"], index=0, horizontal=True)

    if option == "Novo":
        with st.form("form_new_type"):
            nome = st.text_input("Nome do Tipo de Serviço *").strip()
            submitted = st.form_submit_button("Criar")
        if submitted:
            if not nome:
                st.error("Nome é obrigatório.")
            else:
                try:
                    create_service_type(nome)
                    st.success("Tipo de serviço criado.")
                except sqlite3.IntegrityError:
                    st.error("Tipo de serviço já existe.")
                except Exception:
                    st.error("Erro ao criar tipo de serviço.")

    elif option == "Mostrar / Editar / Excluir":
        tipos = list_service_types()
        if not tipos:
            st.info("Nenhum tipo de serviço cadastrado.")
            return
        for tid, tname in tipos:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.write(tname)
            with cols[1]:
                if st.button("✏️", key=f"edit_type_{tid}"):
                    st.session_state.edit_type = tid
                    st.experimental_rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_type_{tid}"):
                    if service_type_has_orders(tid):
                        st.error("Não é possível excluir: existem OS vinculadas a este tipo de serviço.")
                    else:
                        try:
                            delete_service_type(tid)
                            st.success("Tipo de serviço excluído.")
                        except Exception:
                            st.error("Erro ao excluir tipo de serviço.")
                        st.experimental_rerun()

        if "edit_type" in st.session_state:
            tid = st.session_state.edit_type
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM tipos_servico WHERE id=?", (tid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                st.error("Tipo não encontrado.")
                del st.session_state.edit_type
                return
            _, nome_atual = row
            with st.form(f"form_edit_type_{tid}"):
                novo_nome = st.text_input("Nome *", value=nome_atual).strip()
                salvar = st.form_submit_button("Salvar")
            if salvar:
                if not novo_nome:
                    st.error("Nome não pode ficar vazio.")
                else:
                    try:
                        update_service_type(tid, novo_nome)
                        st.success("Tipo atualizado.")
                        del st.session_state.edit_type
                        st.experimental_rerun()
                    except sqlite3.IntegrityError:
                        st.error("Nome já existe.")
                    except Exception:
                        st.error("Erro ao atualizar tipo.")

# ---------------------------
# UI: Abrir OS
# ---------------------------
def ui_open_order():
    st.header("📄 Abrir Ordem de Serviço")
    companies = list_companies()
    types = list_service_types()
    if not companies:
        st.warning("Cadastre ao menos uma empresa antes de abrir OS.")
        return
    if not types:
        st.warning("Cadastre ao menos um tipo de serviço antes de abrir OS.")
        return

    company_opts = ["-- Selecione --"] + [f"{c[0]} - {c[1]}" for c in companies]
    type_opts = ["-- Selecione --"] + [f"{t[0]} - {t[1]}" for t in types]

    with st.form("form_open_order"):
        empresa_sel = st.selectbox("Empresa *", company_opts, index=0)
        tipo_sel = st.selectbox("Tipo de Serviço *", type_opts, index=0)
        titulo = st.text_input("Título *").strip()
        descricao = st.text_area("Descrição *").strip()
        submitted = st.form_submit_button("Abrir OS")
    if submitted:
        if empresa_sel == "-- Selecione --" or tipo_sel == "-- Selecione --" or not titulo or not descricao:
            st.error("Todos os campos são obrigatórios e devem ser selecionados.")
        else:
            empresa_id = int(empresa_sel.split(" - ")[0])
            tipo_id = int(tipo_sel.split(" - ")[0])
            try:
                create_order(empresa_id, titulo, descricao, tipo_id)
                st.success("OS criada com sucesso (situação: Aberta).")
                st.experimental_rerun()
            except Exception:
                st.error("Erro ao criar OS.")

# ---------------------------
# UI: Consultar OS (listar Abertas por default) + Edit / Delete
# ---------------------------
def ui_consult_orders():
    st.header("🔎 Consultar Ordens de Serviço")
    filtro = st.selectbox("Mostrar", ["Abertas", "Finalizadas", "Todas"], index=0)
    situacao = filtro if filtro != "Todas" else None
    try:
        rows = list_orders(situacao if situacao else "Todas")
    except Exception:
        st.error("Erro ao buscar ordens.")
        return

    if not rows:
        st.info("Nenhuma OS encontrada para o filtro selecionado.")
        return

    for row in rows:
        oid, empresa_nome, titulo, descricao, tipo_nome, situacao, empresa_id, tipo_id = row
        cols = st.columns([6, 1, 1])
        with cols[0]:
            st.markdown(f"**OS #{oid} — {titulo}**")
            st.caption(f"{empresa_nome}  •  {tipo_nome}  •  Situação: **{situacao}**")
            st.write(descricao)
        with cols[1]:
            if st.button("✏️", key=f"order_edit_{oid}"):
                st.session_state.editing_order = oid
                st.experimental_rerun()
        with cols[2]:
            if st.button("🗑️", key=f"order_del_{oid}"):
                try:
                    delete_order(oid)
                    st.success(f"OS #{oid} excluída.")
                except Exception:
                    st.error("Erro ao excluir OS.")
                st.experimental_rerun()

    # Se está editando uma OS, mostrar formulário de edição abaixo da lista
    if "editing_order" in st.session_state:
        edit_id = st.session_state.editing_order
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, empresa_id, titulo, descricao, tipo_servico_id, situacao FROM ordens_servico WHERE id=?", (edit_id,))
        data = cur.fetchone()
        conn.close()
        if not data:
            st.error("OS não encontrada.")
            del st.session_state.editing_order
            return
        _, empresa_cur, titulo_cur, desc_cur, tipo_cur, sit_cur = data
        companies = list_companies()
        types = list_service_types()
        comp_opts = [f"{c[0]} - {c[1]}" for c in companies]
        type_opts = [f"{t[0]} - {t[1]}" for t in types]
        try:
            comp_idx = next(i for i, v in enumerate(comp_opts) if v.startswith(f"{empresa_cur} -"))
        except StopIteration:
            comp_idx = 0
        try:
            type_idx = next(i for i, v in enumerate(type_opts) if v.startswith(f"{tipo_cur} -"))
        except StopIteration:
            type_idx = 0

        st.subheader(f"✏️ Editar OS #{edit_id}")
        with st.form(f"form_edit_order_{edit_id}"):
            empresa_sel = st.selectbox("Empresa *", ["-- Selecione --"] + comp_opts, index=1 + comp_idx if comp_opts else 0)
            tipo_sel = st.selectbox("Tipo de Serviço *", ["-- Selecione --"] + type_opts, index=1 + type_idx if type_opts else 0)
            titulo_new = st.text_input("Título *", value=titulo_cur).strip()
            desc_new = st.text_area("Descrição *", value=desc_cur).strip()
            situacao_new = st.selectbox("Situação *", ["Aberta", "Finalizada"], index=0 if sit_cur == "Aberta" else 1)
            salvar = st.form_submit_button("Salvar alterações")
        if salvar:
            if empresa_sel == "-- Selecione --" or tipo_sel == "-- Selecione --" or not titulo_new or not desc_new:
                st.error("Todos os campos são obrigatórios.")
            else:
                empresa_id_new = int(empresa_sel.split(" - ")[0])
                tipo_id_new = int(tipo_sel.split(" - ")[0])
                try:
                    update_order(edit_id, empresa_id_new, titulo_new, desc_new, tipo_id_new, situacao_new)
                    st.success("OS atualizada.")
                    del st.session_state.editing_order
                    st.experimental_rerun()
                except Exception:
                    st.error("Erro ao atualizar OS.")
        if st.button("↩️ Cancelar edição", key=f"cancel_edit_{edit_id}"):
            if "editing_order" in st.session_state:
                del st.session_state.editing_order
            st.experimental_rerun()

# ---------------------------
# App main
# ---------------------------
def main():
    st.set_page_config(page_title="Sistema OS", layout="wide")
    init_db()

    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        ui_login()
        return

    # Sidebar: main menu e submenu
    st.sidebar.title("Menu")
    main_menu = st.sidebar.selectbox("Principal", ["-- Selecione --", "CADASTRO", "ORDEM DE SERVIÇO", "SAIR"], index=0)
    submenu = None
    if main_menu == "CADASTRO":
        submenu = st.sidebar.selectbox("Cadastro", ["-- Selecione --", "CADASTRO EMPRESA", "CADASTRO TIPO DE SERVIÇO", "CADASTRO USUÁRIO"], index=0)
    elif main_menu == "ORDEM DE SERVIÇO":
        submenu = st.sidebar.selectbox("Ordem de Serviço", ["-- Selecione --", "ABRIR OS", "CONSULTAR OS"], index=0)
    elif main_menu == "SAIR":
        if st.sidebar.button("Confirmar logout"):
            st.session_state.user = None
            st.experimental_rerun()

    # Roteamento
    if main_menu == "CADASTRO":
        if submenu == "CADASTRO EMPRESA":
            ui_companies()
        elif submenu == "CADASTRO TIPO DE SERVIÇO":
            ui_service_types()
        elif submenu == "CADASTRO USUÁRIO":
            ui_users()
        else:
            st.info("Selecione uma opção em CADASTRO no menu lateral.")
    elif main_menu == "ORDEM DE SERVIÇO":
        if submenu == "ABRIR OS":
            ui_open_order()
        elif submenu == "CONSULTAR OS":
            ui_consult_orders()
        else:
            st.info("Selecione uma opção em ORDEM DE SERVIÇO no menu lateral.")
    else:
        st.info("Use o menu lateral para navegar (CADASTRO / ORDEM DE SERVIÇO / SAIR).")

if __name__ == "__main__":
    main()
