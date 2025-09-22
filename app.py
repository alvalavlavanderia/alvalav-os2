import streamlit as st
import sqlite3

# -------------------------------
# CONFIGURAÇÕES BÁSICAS DO APP
# -------------------------------
st.set_page_config(
    page_title="ALVALAV - Controle de OS",
    page_icon="🧺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo com cores da ALVALAV (azul e branco)
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
        }
        .main {
            background-color: #f8fbff;
        }
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
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# LOGO
# -------------------------------
st.image("https://i.ibb.co/J3cm4Dq/logo-alvalav.png", width=200)  # 👉 Troque esse link pela logo oficial

st.title("📋 Sistema de Controle de Ordens de Serviço - ALVALAV")

# -------------------------------
# BANCO DE DADOS
# -------------------------------
conn = sqlite3.connect('alvalav_os.db')
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT, cnpj TEXT, endereco TEXT, telefone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT, senha TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT, servico TEXT, descricao TEXT)''')

conn.commit()

# -------------------------------
# MENU
# -------------------------------
menu = ["Cadastrar Empresa", "Cadastrar Usuário", "Cadastrar Tipo de Serviço", "Abrir OS", "Consultar OS"]
escolha = st.sidebar.radio("Menu", menu)

# -------------------------------
# TELAS
# -------------------------------
if escolha == "Cadastrar Empresa":
    st.subheader("🏢 Cadastro de Empresa")
    nome = st.text_input("Nome da empresa")
    cnpj = st.text_input("CNPJ")
    endereco = st.text_input("Endereço")
    telefone = st.text_input("Telefone")
    if st.button("Salvar Empresa"):
        c.execute("INSERT INTO empresas (nome, cnpj, endereco, telefone) VALUES (?,?,?,?)",
                  (nome, cnpj, endereco, telefone))
        conn.commit()
        st.success("✅ Empresa cadastrada com sucesso!")

elif escolha == "Cadastrar Usuário":
    st.subheader("👤 Cadastro de Usuário")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Salvar Usuário"):
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?,?)", (usuario, senha))
        conn.commit()
        st.success("✅ Usuário cadastrado com sucesso!")

elif escolha == "Cadastrar Tipo de Serviço":
    st.subheader("⚙️ Cadastro de Tipo de Serviço")
    descricao = st.text_input("Descrição do serviço")
    if st.button("Salvar Serviço"):
        c.execute("INSERT INTO tipos_servico (descricao) VALUES (?)", (descricao,))
        conn.commit()
        st.success("✅ Tipo de serviço cadastrado com sucesso!")

elif escolha == "Abrir OS":
    st.subheader("📝 Abrir Ordem de Serviço")
    empresas = [row[0] for row in c.execute("SELECT nome FROM empresas").fetchall()]
    servicos = [row[0] for row in c.execute("SELECT descricao FROM tipos_servico").fetchall()]
    
    empresa = st.selectbox("Selecione a empresa", empresas if empresas else ["Nenhuma empresa cadastrada"])
    servico = st.selectbox("Selecione o serviço", servicos if servicos else ["Nenhum serviço cadastrado"])
    descricao = st.text_area("Descrição da OS")
    
    if st.button("Abrir OS"):
        c.execute("INSERT INTO ordens_servico (empresa, servico, descricao) VALUES (?,?,?)",
                  (empresa, servico, descricao))
        conn.commit()
        st.success("✅ Ordem de Serviço criada com sucesso!")

elif escolha == "Consultar OS":
    st.subheader("🔍 Consultar Ordens de Serviço")
    ordens = c.execute("SELECT * FROM ordens_servico").fetchall()
    if ordens:
        for ordem in ordens:
            st.markdown(f"**OS {ordem[0]}** | Empresa: {ordem[1]} | Serviço: {ordem[2]}")
            st.write(f"Descrição: {ordem[3]}")
            st.markdown("---")
    else:
        st.info("Nenhuma OS cadastrada ainda.")
