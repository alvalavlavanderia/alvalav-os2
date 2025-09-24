import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

# -------------------------------
# CONFIGURAÇÕES BÁSICAS DO APP
# -------------------------------
st.set_page_config(
    page_title="ALVALAV - Controle de OS",
    page_icon="🧺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Logo (trocar o link pela logo real)
LOGO_URL = "https://i.ibb.co/J3cm4Dq/logo-alvalav.png"

st.markdown("""
    <style>
        .stApp > header {visibility: hidden;}
        .css-18e3th9 {padding-top: 0rem;}
        h1, h2, h3, h4 {
            color: #004aad;
        }
        .stButton>button {
            background-color: #004aad;
            color: white;
            border-radius: 8px;
            height: 40px;
        }
        .stButton>button:hover {
            background-color: #003580;
            color: #e6e6e6;
        }
        .stDownloadButton>button {
            background-color: #0066cc;
            color: white;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.title("📋 ALVALAV — Sistema de Ordens de Serviço")

# -------------------------------
# BANCO DE DADOS - Inicialização
# -------------------------------
def get_connection():
    return sqlite3.connect("alvalav_os.db", check_same_thread=False)

conn = get_connection()
c = conn.cursor()

def init_db():
    # Tabelas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE, cnpj TEXT, endereco TEXT, telefone TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE, senha TEXT, is_admin INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT,
                    servico TEXT,
                    descricao TEXT,
                    status TEXT DEFAULT 'Aberta',
                    data_abertura TEXT,
                    data_atualizacao TEXT)''')
    conn.commit()

    # Garantir que o admin exista (credenciais fixas conforme solicitado)
    admin_user = c.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone()
    if not admin_user:
        c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
                  ("admin", "Alv32324@", 1))
        conn.commit()

init_db()

# -------------------------------
# Utilitários
# -------------------------------
def authenticate(username, password):
    row = c.execute("SELECT usuario, senha, is_admin FROM usuarios WHERE usuario=?", (username,)).fetchone()
    if row and row[1] == password:
        return {"usuario": row[0], "is_admin": bool(row[2])}
    # also allow admin fixed credentials even if DB changed (ensures admin always can log)
    if username == "admin" and password == "Alv32324@":
        return {"usuario": "admin", "is_admin": True}
    return None

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="OS")
        writer.save()
    return output.getvalue()

# -------------------------------
# Login (sempre que abrir o app)
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.is_admin = False

def do_login():
    username = st.session_state.login_user.strip()
    password = st.session_state.login_pass
    auth = authenticate(username, password)
    if auth:
        st.session_state.logged_in = True
        st.session_state.user = auth["usuario"]
        st.session_state.is_admin = auth["is_admin"]
        st.success(f"Bem-vindo(a), {st.session_state.user}!")
    else:
        st.error("Usuário ou senha inválidos.")

def do_logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.is_admin = False
    st.experimental_rerun()

if not st.session_state.logged_in:
    st.subheader("🔒 Login")
    with st.form("login_form", clear_on_submit=False):
        st.text_input("Usuário", key="login_user")
        st.text_input("Senha", type="password", key="login_pass")
        submitted = st.form_submit_button("Entrar", on_click=do_login)
    st.info("Digite seu usuário e senha para acessar o sistema. (Admin padrão: admin / Alv32324@)")
    st.stop()  # Não executar mais até login

# -------------------------------
# Após login - barra lateral com menu suspenso
# -------------------------------
st.sidebar.markdown(f"**Usuário:** {st.session_state.user} {'(admin)' if st.session_state.is_admin else ''}")
if st.sidebar.button("Sair"):
    do_logout()

main_menu = st.sidebar.selectbox("Menu Principal", ["CADASTRO", "ORDEM DE SERVIÇO"])

# Submenu dinâmico
if main_menu == "CADASTRO":
    # Mostrar opções - usuário comum não vê 'Cadastro Usuário'
    options = ["Cadastro Empresa", "Cadastro Tipo de Serviço"]
    if st.session_state.is_admin:
        options.insert(1, "Cadastro Usuário")
    submenu = st.sidebar.selectbox("Cadastros", options)
elif main_menu == "ORDEM DE SERVIÇO":
    submenu = st.sidebar.selectbox("ORDEM DE SERVIÇO", ["Abrir OS", "Consultar OS"])
else:
    submenu = None

# -------------------------------
# Implementação das telas
# -------------------------------
# CADASTRO -> Empresa
if main_menu == "CADASTRO" and submenu == "Cadastro Empresa":
    st.header("🏢 Cadastro de Empresa")
    nome = st.text_input("Nome da empresa")
    cnpj = st.text_input("CNPJ")
    endereco = st.text_input("Endereço")
    telefone = st.text_input("Telefone")
    if st.button("Salvar Empresa"):
        if not nome.strip():
            st.error("Nome da empresa é obrigatório.")
        else:
            try:
                c.execute("INSERT INTO empresas (nome, cnpj, endereco, telefone) VALUES (?,?,?,?)",
                          (nome.strip(), cnpj.strip(), endereco.strip(), telefone.strip()))
                conn.commit()
                st.success("✅ Empresa cadastrada com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Empresa com esse nome já existe.")

# CADASTRO -> Usuário (apenas admin)
elif main_menu == "CADASTRO" and submenu == "Cadastro Usuário":
    st.header("👤 Cadastro de Usuário (Admin)")
    st.write("Apenas o administrador pode criar novos usuários.")
    novo_user = st.text_input("Nome de usuário")
    nova_senha = st.text_input("Senha", type="password")
    is_admin_flag = st.checkbox("É administrador?", value=False)
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
                st.error("Já existe um usuário com esse nome.")

# CADASTRO -> Tipo de Serviço
elif main_menu == "CADASTRO" and submenu == "Cadastro Tipo de Serviço":
    st.header("⚙️ Cadastro de Tipo de Serviço")
    descricao = st.text_input("Descrição do serviço")
    if st.button("Salvar Serviço"):
        if not descricao.strip():
            st.error("Descrição é obrigatória.")
        else:
            try:
                c.execute("INSERT INTO tipos_servico (descricao) VALUES (?)", (descricao.strip(),))
                conn.commit()
                st.success("✅ Tipo de serviço cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Esse tipo de serviço já existe.")

# ORDEM DE SERVIÇO -> Abrir OS
elif main_menu == "ORDEM DE SERVIÇO" and submenu == "Abrir OS":
    st.header("📝 Abrir Nova Ordem de Serviço")
    empresas = [row[0] for row in c.execute("SELECT nome FROM empresas ORDER BY nome").fetchall()]
    servicos = [row[0] for row in c.execute("SELECT descricao FROM tipos_servico ORDER BY descricao").fetchall()]

    if not empresas:
        st.warning("Nenhuma empresa cadastrada. Cadastre empresas em CADASTRO > Cadastro Empresa.")
    if not servicos:
        st.warning("Nenhum tipo de serviço cadastrado. Cadastre em CADASTRO > Cadastro Tipo de Serviço.")

    empresa = st.selectbox("Empresa", empresas) if empresas else None
    servico = st.selectbox("Serviço", servicos) if servicos else None
    descricao_os = st.text_area("Descrição da OS (informe instruções ou observações)")

    if st.button("Abrir OS"):
        if not empresa or not servico:
            st.error("É necessário selecionar empresa e serviço.")
        else:
            from datetime import datetime
            now = datetime.now().isoformat(sep=' ', timespec='seconds')
            c.execute("""INSERT INTO ordens_servico (empresa, servico, descricao, status, data_abertura, data_atualizacao)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (empresa, servico, descricao_os.strip(), "Aberta", now, now))
            conn.commit()
            st.success("✅ Ordem de Serviço criada com sucesso!")

# ORDEM DE SERVIÇO -> Consultar OS
elif main_menu == "ORDEM DE SERVIÇO" and submenu == "Consultar OS":
    st.header("🔍 Consultar Ordens de Serviço")

    # Ao abrir, listar automaticamente as OS pendentes
    st.subheader("OS Pendentes (padrão)")
    pendentes = c.execute("SELECT * FROM ordens_servico WHERE status IN ('Aberta', 'Em andamento') ORDER BY id DESC").fetchall()
    if pendentes:
        df_pend = pd.DataFrame(pendentes, columns=["ID", "Empresa", "Serviço", "Descrição", "Status", "Data Abertura", "Data Atualização"])
        st.dataframe(df_pend)
    else:
        st.info("Nenhuma OS pendente no momento.")

    st.markdown("---")
    st.subheader("Filtros e busca")

    filtro_tipo = st.radio("Mostrar", ["Pendentes", "Finalizadas", "Todas"], index=0)

    if filtro_tipo == "Pendentes":
        base_query = "SELECT * FROM ordens_servico WHERE status IN ('Aberta','Em andamento')"
        base_params = ()
    elif filtro_tipo == "Finalizadas":
        base_query = "SELECT * FROM ordens_servico WHERE status = 'Concluída'"
        base_params = ()
    else:
        base_query = "SELECT * FROM ordens_servico"
        base_params = ()

    modo_busca = st.selectbox("Filtrar por", ["Nenhum", "Empresa", "Código da OS"])
    ordens = []
    if modo_busca == "Nenhum":
        ordens = c.execute(base_query + " ORDER BY id DESC", base_params).fetchall()
    elif modo_busca == "Empresa":
        empresas = [row[0] for row in c.execute("SELECT nome FROM empresas ORDER BY nome").fetchall()]
        empresa_filtro = st.selectbox("Selecione a empresa", ["-- Escolher --"] + empresas)
        if empresa_filtro != "-- Escolher --":
            ordens = c.execute(base_query + " AND empresa = ? ORDER BY id DESC", (empresa_filtro,)).fetchall()
    elif modo_busca == "Código da OS":
        codigo = st.number_input("Digite o código da OS", min_value=1, step=1)
        if codigo:
            ordens = c.execute(base_query + " AND id = ? ORDER BY id DESC", (codigo,)).fetchall()

    if ordens:
        df = pd.DataFrame(ordens, columns=["ID", "Empresa", "Serviço", "Descrição", "Status", "Data Abertura", "Data Atualização"])
        st.write(f"Resultados: {len(df)} OS(s)")
        st.dataframe(df)

        # Exportar
        excel_bytes = to_excel_bytes(df)
        st.download_button(
            label="📥 Exportar resultados para Excel",
            data=excel_bytes,
            file_name="ordens_servico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("---")
        st.subheader("Alterar status e detalhes")
        # Exibir cada OS com opção de alterar status
        for ordem in ordens:
            os_id = ordem[0]
            os_empresa = ordem[1]
            os_servico = ordem[2]
            os_desc = ordem[3]
            os_status = ordem[4]
            os_data_ab = ordem[5]
            os_data_up = ordem[6]

            st.markdown(f"**OS {os_id}** — Empresa: {os_empresa} — Serviço: {os_servico}")
            st.write(f"Descrição: {os_desc}")
            st.write(f"Status atual: **{os_status}**")
            if os_data_ab:
                st.write(f"Data abertura: {os_data_ab}  |  Última atualização: {os_data_up if os_data_up else '-'}")

            novo_status = st.selectbox(
                f"Alterar status da OS {os_id}",
                ["Aberta", "Em andamento", "Concluída"],
                index=["Aberta", "Em andamento", "Concluída"].index(os_status) if os_status in ["Aberta", "Em andamento", "Concluída"] else 0,
                key=f"status_{os_id}"
            )
            if st.button(f"Salvar status OS {os_id}", key=f"btn_save_{os_id}"):
                from datetime import datetime
                now = datetime.now().isoformat(sep=' ', timespec='seconds')
                c.execute("UPDATE ordens_servico SET status=?, data_atualizacao=? WHERE id=?", (novo_status, now, os_id))
                conn.commit()
                st.success(f"✅ Status da OS {os_id} atualizado para {novo_status}")
                st.experimental_rerun()
            st.markdown("---")
    else:
        st.info("Nenhuma OS encontrada com esse filtro.")

# -------------------------------
# Rodar conexao: fechar em final do app
# -------------------------------
# (Não fechar explicitamente a conexão pois Streamlit reaproveita; se desejar, fechar pode ser feito aqui)
# conn.close()
