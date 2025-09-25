# app.py (corrigido: usa st.rerun() e session_state consistente)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_FILE = "sistema.db"

# -------------------------
# Inicialização do banco
# -------------------------
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT,
        is_admin INTEGER DEFAULT 0
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        rua TEXT,
        numero TEXT,
        cep TEXT,
        cidade TEXT,
        estado TEXT,
        telefone TEXT,
        cnpj TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS tipos_servico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS ordens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER,
        tipo_servico_id INTEGER,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        situacao TEXT DEFAULT 'Aberta',
        data_abertura TEXT,
        data_atualizacao TEXT,
        FOREIGN KEY (empresa_id) REFERENCES empresas(id),
        FOREIGN KEY (tipo_servico_id) REFERENCES tipos_servico(id)
    )""")

    # garante admin padrão (não sobrescreve)
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))

    conn.commit()
    conn.close()

# -------------------------
# Utilitários DB
# -------------------------
def list_empresas():
    conn = get_conn()
    df = pd.read_sql("SELECT id, nome FROM empresas ORDER BY nome", conn)
    conn.close()
    return df

def list_servicos():
    conn = get_conn()
    df = pd.read_sql("SELECT id, nome FROM tipos_servico ORDER BY nome", conn)
    conn.close()
    return df

def query_ordens(situacao=None, empresa_id=None):
    conn = get_conn()
    query = """SELECT o.id AS CODIGO, e.nome AS EMPRESA, o.titulo AS TITULO,
                      o.descricao AS DESCRICAO, o.situacao AS SITUACAO,
                      o.data_abertura, o.data_atualizacao
               FROM ordens o
               JOIN empresas e ON o.empresa_id = e.id
               WHERE 1=1"""
    params = []
    if situacao:
        query += " AND o.situacao = ?"
        params.append(situacao)
    if empresa_id:
        query += " AND o.empresa_id = ?"
        params.append(empresa_id)
    query += " ORDER BY o.id DESC"
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def delete_ordem(os_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM ordens WHERE id = ?", (os_id,))
    conn.commit()
    conn.close()

def update_ordem(os_id, titulo, descricao, situacao):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    c.execute("UPDATE ordens SET titulo=?, descricao=?, situacao=?, data_atualizacao=? WHERE id=?",
              (titulo, descricao, situacao, now, os_id))
    conn.commit()
    conn.close()

# -------------------------
# Autenticação
# -------------------------
def autenticar(usuario, senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, is_admin FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    row = c.fetchone()
    conn.close()
    return row  # None ou (id, is_admin)

# -------------------------
# Reset DB (opcional - admin)
# -------------------------
def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()

# -------------------------
# UI: Login
# -------------------------
def tela_login():
    st.title("🔐 Login no Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        auth = autenticar(usuario.strip(), senha)
        if auth:
            st.session_state["logged_in"] = True
            st.session_state["usuario_id"] = auth[0]
            st.session_state["usuario_name"] = usuario.strip()
            st.session_state["is_admin"] = bool(auth[1])
            st.success(f"Bem-vindo(a), {usuario.strip()}!")
            st.rerun()   # substitui experimental_rerun
        else:
            st.error("Usuário ou senha inválidos.")

# -------------------------
# UI: Cadastros
# -------------------------
def cadastro_empresa_ui():
    st.header("🏢 Cadastro de Empresa")
    with st.form("form_empresa", clear_on_submit=True):
        nome = st.text_input("Empresa *")
        rua = st.text_input("Rua")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        telefone = st.text_input("Telefone *")
        cnpj = st.text_input("CNPJ *")
        enviar = st.form_submit_button("Salvar Empresa")
        if enviar:
            if not nome.strip() or not telefone.strip() or not cnpj.strip():
                st.error("Preencha os campos obrigatórios: Empresa, Telefone e CNPJ.")
            else:
                conn = get_conn()
                c = conn.cursor()
                try:
                    c.execute("""INSERT INTO empresas (nome, rua, numero, cep, cidade, estado, telefone, cnpj)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                              (nome.strip(), rua.strip(), numero.strip(), cep.strip(), cidade.strip(), estado.strip(), telefone.strip(), cnpj.strip()))
                    conn.commit()
                    st.success("✅ Empresa cadastrada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Empresa com esse nome já existe.")
                finally:
                    conn.close()

def cadastro_usuario_ui():
    st.header("👤 Cadastro de Usuário (apenas admin)")
    if not st.session_state.get("is_admin", False):
        st.error("Apenas administradores podem cadastrar usuários.")
        return

    with st.form("form_usuario", clear_on_submit=True):
        usuario = st.text_input("Nome de usuário")
        senha = st.text_input("Senha")
        is_admin = st.checkbox("Dar permissão de admin?")
        enviar = st.form_submit_button("Salvar Usuário")
        if enviar:
            if not usuario.strip() or not senha:
                st.error("Preencha usuário e senha.")
            else:
                conn = get_conn()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                              (usuario.strip(), senha, 1 if is_admin else 0))
                    conn.commit()
                    st.success("✅ Usuário criado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Usuário já existe.")
                finally:
                    conn.close()

def cadastro_servico_ui():
    st.header("🛠 Cadastro de Tipo de Serviço")
    with st.form("form_servico", clear_on_submit=True):
        nome = st.text_input("Descrição do serviço *")
        enviar = st.form_submit_button("Salvar Serviço")
        if enviar:
            if not nome.strip():
                st.error("Descrição obrigatória.")
            else:
                conn = get_conn()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO tipos_servico (nome) VALUES (?)", (nome.strip(),))
                    conn.commit()
                    st.success("✅ Tipo de serviço cadastrado.")
                except sqlite3.IntegrityError:
                    st.error("Esse tipo de serviço já existe.")
                finally:
                    conn.close()

# -------------------------
# UI: Abrir OS
# -------------------------
def abrir_os_ui():
    st.header("📝 Abrir Ordem de Serviço")
    empresas = list_empresas()
    servicos = list_servicos()

    with st.form("form_abriros", clear_on_submit=True):
        empresa_sel = st.selectbox("Empresa *", ["-- Selecionar --"] + empresas["nome"].tolist())
        servico_sel = st.selectbox("Tipo de Serviço *", ["-- Selecionar --"] + servicos["nome"].tolist())
        titulo = st.text_input("Título *")
        descricao = st.text_area("Descrição *")
        enviar = st.form_submit_button("Salvar OS")
        if enviar:
            if empresa_sel == "-- Selecionar --" or servico_sel == "-- Selecionar --" or not titulo.strip() or not descricao.strip():
                st.error("Preencha todos os campos obrigatórios.")
            else:
                empresa_id = empresas.loc[empresas["nome"] == empresa_sel, "id"].values[0]
                servico_id = servicos.loc[servicos["nome"] == servico_sel, "id"].values[0]
                now = datetime.now().isoformat(sep=' ', timespec='seconds')
                conn = get_conn()
                c = conn.cursor()
                c.execute("""INSERT INTO ordens (empresa_id, tipo_servico_id, titulo, descricao, situacao, data_abertura, data_atualizacao)
                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (int(empresa_id), int(servico_id), titulo.strip(), descricao.strip(), "Aberta", now, now))
                conn.commit()
                conn.close()
                st.success("✅ Ordem de Serviço criada com sucesso!")

# -------------------------
# UI: Consultar OS
# -------------------------
def consultar_os_ui():
    st.header("🔎 Consultar Ordens de Serviço")

    # filtros iniciam vazios
    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Em andamento", "Finalizada"])
    empresas = list_empresas()
    empresa_sel = st.selectbox("Filtrar por Empresa", [""] + empresas["nome"].tolist())

    empresa_id = None
    if empresa_sel:
        empresa_id = int(empresas.loc[empresas["nome"]==empresa_sel, "id"].values[0])

    df = query_ordens(situacao if situacao else None, empresa_id)

    if df.empty:
        st.info("Nenhuma Ordem de Serviço encontrada com os filtros aplicados.")
        return

    # mostrar tabela com cabeçalhos corretos e sem coluna 0,1,2...
    display_df = df[["CODIGO", "EMPRESA", "TITULO", "SITUACAO"]].copy()
    st.dataframe(display_df, use_container_width=True)

    # exibir edição/exclusão inline por linha (botões na mesma linha)
    st.markdown("**Ações rápidas:**")
    for _, row in df.iterrows():
        cols = st.columns([1,3,3,2,1,1])
        cols[0].write(row["CODIGO"])
        cols[1].write(row["EMPRESA"])
        cols[2].write(row["TITULO"])
        cols[3].write(row["SITUACAO"])

        # editar
        if cols[4].button("✏️", key=f"edit_{row['CODIGO']}"):
            # abrir modal-like (expander) para editar
            with st.form(f"edit_form_{row['CODIGO']}"):
                novo_titulo = st.text_input("Título", value=row["TITULO"], key=f"t_{row['CODIGO']}")
                nova_descricao = st.text_area("Descrição", value=row["DESCRICAO"], key=f"d_{row['CODIGO']}")
                nova_situ = st.selectbox("Situação", ["Aberta", "Em andamento", "Finalizada"],
                                         index=0 if row["SITUACAO"]=="Aberta" else (1 if row["SITUACAO"]=="Em andamento" else 2),
                                         key=f"s_{row['CODIGO']}")
                if st.form_submit_button("Salvar alterações", key=f"save_{row['CODIGO']}"):
                    update_ordem(row["CODIGO"], novo_titulo.strip(), nova_descricao.strip(), nova_situ)
                    st.success("✅ OS atualizada.")
                    st.rerun()

        # excluir
        if cols[5].button("❌", key=f"del_{row['CODIGO']}"):
            delete_ordem(row["CODIGO"])
            st.warning("🗑 OS excluída.")
            st.rerun()

# -------------------------
# App principal / menu
# -------------------------
def main_app():
    st.sidebar.title("📌 Menu")
    if st.session_state.get("is_admin", False):
        escolha = st.sidebar.selectbox("Menu Principal", ["", "CADASTRO", "ORDEM DE SERVIÇO"])
        if escolha == "CADASTRO":
            submenu = st.sidebar.selectbox("Cadastros", ["", "Cadastro Empresa", "Cadastro Tipo de Serviço", "Cadastro Usuário"])
            if submenu == "Cadastro Empresa":
                cadastro_empresa_ui()
            elif submenu == "Cadastro Tipo de Serviço":
                cadastro_servico_ui()
            elif submenu == "Cadastro Usuário":
                cadastro_usuario_ui()
        elif escolha == "ORDEM DE SERVIÇO":
            sub = st.sidebar.selectbox("Ordem de Serviço", ["", "Abrir OS", "Consultar OS"])
            if sub == "Abrir OS":
                abrir_os_ui()
            elif sub == "Consultar OS":
                consultar_os_ui()
    else:
        # usuário comum
        escolha = st.sidebar.selectbox("Menu Principal", ["", "Abrir OS", "Consultar OS"])
        if escolha == "Abrir OS":
            abrir_os_ui()
        elif escolha == "Consultar OS":
            consultar_os_ui()

    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 {st.session_state.get('usuario_name', 'Usuário')}")
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    # admin - reset DB (opcional)
    if st.session_state.get("is_admin", False):
        st.sidebar.markdown("---")
        if st.sidebar.button("⚠️ Reset DB (apaga tudo)"):
            reset_db()
            st.success("Banco resetado. Recarregando...")
            st.rerun()

# -------------------------
# Entrypoint
# -------------------------
def main():
    init_db()
    # garantir chaves de sessão
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        tela_login()
        return
    main_app()

if __name__ == "__main__":
    main()
