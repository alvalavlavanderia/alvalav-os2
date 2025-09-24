# app.py
import streamlit as st
import sqlite3
from datetime import datetime
import os

DB_FILE = "alvalav_os.db"

# ----------------------
# Conexão e utilitários
# ----------------------
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

conn = get_conn()
c = conn.cursor()

def ensure_column(table_name, column_name, column_def):
    """Adiciona coluna se não existir (migração segura)."""
    cols = [row[1] for row in c.execute(f"PRAGMA table_info({table_name})").fetchall()]
    if column_name not in cols:
        c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        conn.commit()

# ----------------------
# Inicialização / Migração do banco
# ----------------------
def init_db():
    # tabelas básicas (criadas se não existirem)
    c.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            endereco TEXT,
            telefone TEXT,
            cnpj TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tipos_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            titulo TEXT,
            descricao TEXT,
            status TEXT DEFAULT 'Aberta',
            data_abertura TEXT,
            data_atualizacao TEXT
        )
    """)
    conn.commit()

    # migrar/garantir colunas de empresas: rua, numero, cep, cidade, estado (mantemos endereco também)
    ensure_column("empresas", "rua", "TEXT")
    ensure_column("empresas", "numero", "TEXT")
    ensure_column("empresas", "cep", "TEXT")
    ensure_column("empresas", "cidade", "TEXT")
    ensure_column("empresas", "estado", "TEXT")
    ensure_column("empresas", "telefone", "TEXT")  # já criado na DDL acima, fica seguro

    # migrar usuarios: is_admin
    ensure_column("usuarios", "is_admin", "INTEGER DEFAULT 0")

    # migrar ordens_servico: datas (já na DDL, mas garantimos)
    ensure_column("ordens_servico", "data_abertura", "TEXT")
    ensure_column("ordens_servico", "data_atualizacao", "TEXT")

    # criar admin padrão de forma segura
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))
    conn.commit()

init_db()

# ----------------------
# Streamlit config e estilo
# ----------------------
st.set_page_config(page_title="ALVALAV — Sistema de OS", page_icon="🧺", layout="wide")
st.markdown("""
    <style>
        h1, h2, h3, h4 { color: #004aad; }
        .stButton>button { background-color: #004aad; color: white; border-radius: 8px; height:34px; }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 6])
with col1:
    # placeholder para logo (substitua com URL/hosted image se quiser)
    st.image("https://i.ibb.co/J3cm4Dq/logo-alvalav.png", width=110)
with col2:
    st.title("📋 ALVALAV — Sistema de Ordens de Serviço")

# ----------------------
# Autenticação
# ----------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None
    st.session_state.is_admin = False

def autenticar(usuario, senha):
    row = c.execute("SELECT usuario, senha, is_admin FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha)).fetchone()
    if row:
        return {"usuario": row[0], "is_admin": bool(row[2] if len(row) > 2 and row[2] is not None else 0)}
    # fallback: garantir login admin mesmo se DB corrompido (redundância)
    if usuario == "admin" and senha == "Alv32324@":
        return {"usuario": "admin", "is_admin": True}
    return None

if not st.session_state.usuario:
    st.subheader("🔐 Login")
    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        auth = autenticar(user_input.strip(), pass_input)
        if auth:
            st.session_state.usuario = auth["usuario"]
            st.session_state.is_admin = auth["is_admin"]
            st.success(f"Bem-vindo(a), {st.session_state.usuario}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# ----------------------
# Barra lateral - menu e logout
# ----------------------
st.sidebar.markdown(f"**Usuário:** {st.session_state.usuario} {'(admin)' if st.session_state.is_admin else ''}")
if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.session_state.is_admin = False
    st.rerun()

main_menu = st.sidebar.selectbox("Menu Principal", ["-- Selecionar --", "CADASTRO", "ORDEM DE SERVIÇO"])

# ----------------------
# Função utilitária: lista de empresas / serviços
# ----------------------
def listar_empresas():
    return [row[0] for row in c.execute("SELECT nome FROM empresas ORDER BY nome").fetchall()]

def listar_servicos():
    return [row[0] for row in c.execute("SELECT descricao FROM tipos_servico ORDER BY descricao").fetchall()]

# ----------------------
# CADASTRO
# ----------------------
if main_menu == "CADASTRO":
    st.header("📂 CADASTROS")
    cad_opt = ["-- Selecionar --", "Cadastro Empresa", "Cadastro Tipo de Serviço"]
    if st.session_state.is_admin:
        cad_opt.insert(2, "Cadastro Usuário")
    submenu = st.selectbox("Escolha", cad_opt, index=0)

    if submenu == "Cadastro Empresa":
        st.subheader("🏢 Cadastro de Empresa")
        # Campos solicitados: Empresa, Rua, Número, CEP, Cidade, Estado, Telefone, CNPJ
        nome = st.text_input("Nome da Empresa")
        rua = st.text_input("Rua")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        telefone = st.text_input("Telefone")
        cnpj = st.text_input("CNPJ")
        if st.button("Salvar Empresa"):
            if not nome.strip():
                st.error("Nome da empresa é obrigatório.")
            else:
                try:
                    # salvamos também um campo endereco concatenado (compatibilidade)
                    endereco_full = f"{rua} {numero}, {cep}, {cidade} - {estado}"
                    c.execute("""INSERT INTO empresas (nome, endereco, telefone, cnpj, rua, numero, cep, cidade, estado)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (nome.strip(), endereco_full.strip(), telefone.strip(), cnpj.strip(),
                               rua.strip(), numero.strip(), cep.strip(), cidade.strip(), estado.strip()))
                    conn.commit()
                    st.success("✅ Empresa cadastrada com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Já existe uma empresa com esse nome.")

    elif submenu == "Cadastro Tipo de Serviço":
        st.subheader("⚙️ Cadastro de Tipo de Serviço")
        desc = st.text_input("Descrição do serviço")
        if st.button("Salvar Serviço"):
            if not desc.strip():
                st.error("Descrição obrigatória.")
            else:
                try:
                    c.execute("INSERT INTO tipos_servico (descricao) VALUES (?)", (desc.strip(),))
                    conn.commit()
                    st.success("✅ Tipo de serviço cadastrado.")
                except sqlite3.IntegrityError:
                    st.error("Esse tipo de serviço já existe.")

    elif submenu == "Cadastro Usuário" and st.session_state.is_admin:
        st.subheader("👤 Cadastro de Usuário (Admin)")
        novo_user = st.text_input("Nome de usuário")
        nova_senha = st.text_input("Senha", type="password")
        is_admin_flag = st.checkbox("Dar permissão de admin?")
        if st.button("Salvar Usuário"):
            if not novo_user.strip() or not nova_senha:
                st.error("Preencha usuário e senha.")
            else:
                try:
                    c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                              (novo_user.strip(), nova_senha, 1 if is_admin_flag else 0))
                    conn.commit()
                    st.success("✅ Usuário criado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Usuário já existe.")

    # botão de reset disponível somente para admin
    st.markdown("---")
    if st.session_state.is_admin:
        st.warning("⚠️ Admin: o botão abaixo reseta o banco (remove todos os dados).")
        if st.button("⚠️ Resetar banco (apagar todos os dados)"):
            # apagar DB e recriar
            try:
                if os.path.exists(DB_FILE):
                    os.remove(DB_FILE)
                # reinicializar conexão e DB
                global conn, c
                conn = get_conn()
                c = conn.cursor()
                init_db()
                st.success("✅ Banco resetado com sucesso. O app irá reiniciar a sessão.")
                st.rerun()
            except Exception as e:
                st.error("Erro ao resetar o banco. Ver logs.")
                print("reset error:", e)

# ----------------------
# ORDEM DE SERVIÇO
# ----------------------
elif main_menu == "ORDEM DE SERVIÇO":
    st.header("📑 ORDEM DE SERVIÇO")
    ordem_opts = ["-- Selecionar --", "Abrir OS", "Consultar OS"]
    ordem_sub = st.selectbox("Escolha ação", ordem_opts, index=0)

    # Abrir OS: campos em branco, situação padrão aberta
    if ordem_sub == "Abrir OS":
        st.subheader("📝 Abrir Nova Ordem de Serviço")
        empresas = listar_empresas()
        servicos = listar_servicos()
        if not empresas:
            st.warning("Nenhuma empresa cadastrada. Vá em CADASTRO > Cadastro Empresa.")
        if not servicos:
            st.warning("Nenhum tipo de serviço cadastrado. Vá em CADASTRO > Cadastro Tipo de Serviço.")

        empresa = st.selectbox("Empresa", ["-- Selecionar --"] + empresas)
        tipo_servico = st.selectbox("Tipo de Serviço", ["-- Selecionar --"] + servicos)
        titulo = st.text_input("Título da OS")
        descricao = st.text_area("Descrição / Observações")
        situacao = "Aberta"  # situação pré-definida

        if st.button("Abrir OS"):
            if empresa == "-- Selecionar --" or tipo_servico == "-- Selecionar --" or not titulo.strip():
                st.error("Preencha Empresa, Tipo de Serviço e Título.")
            else:
                now = datetime.now().isoformat(sep=' ', timespec='seconds')
                c.execute("""INSERT INTO ordens_servico
                             (empresa, titulo, descricao, status, data_abertura, data_atualizacao)
                             VALUES (?, ?, ?, ?, ?, ?)""",
                          (empresa, titulo.strip(), descricao.strip(), situacao, now, now))
                conn.commit()
                st.success("✅ Ordem de Serviço criada com sucesso!")

    # Consultar OS: mostra todas as abertas e oferece busca por situação e por empresa
    elif ordem_sub == "Consultar OS":
        st.subheader("🔍 Consultar Ordens de Serviço")
        # por padrão mostrar todas as abertas (status = 'Aberta')
        st.markdown("**OS abertas (por padrão)**")
        rows_open = c.execute("SELECT id, empresa, titulo, status FROM ordens_servico WHERE status='Aberta' ORDER BY id DESC").fetchall()
        if rows_open:
            st.table(rows_open)
        else:
            st.info("Sem OS abertas no momento.")

        st.markdown("---")
        st.subheader("Filtros")
        situ_filter = st.selectbox("Situação", ["Todas", "Aberta", "Em andamento", "Concluída"])
        empresas = ["-- Todas --"] + listar_empresas()
        empresa_filter = st.selectbox("Empresa", empresas)

        # construir query dinamicamente
        query = "SELECT id, empresa, titulo, status FROM ordens_servico WHERE 1=1"
        params = []
        if situ_filter != "Todas":
            query += " AND status = ?"
            params.append(situ_filter)
        if empresa_filter and empresa_filter != "-- Todas --":
            query += " AND empresa = ?"
            params.append(empresa_filter)
        query += " ORDER BY id DESC"

        resultados = c.execute(query, tuple(params)).fetchall()
        st.write(f"Resultados: {len(resultados)} OS(s)")
        if resultados:
            st.table(resultados)
        else:
            st.info("Nenhuma OS encontrada com os filtros aplicados.")

# ----------------------
# Caso nenhuma opção selecionada
# ----------------------
else:
    st.info("Selecione uma opção no menu lateral para começar.")
