import streamlit as st
import sqlite3
import pandas as pd

# -------------------------------
# CONFIGURAÇÕES BÁSICAS
# -------------------------------
st.set_page_config(
    page_title="ALVALAV - Sistema de OS",
    page_icon="🧺",
    layout="wide"
)

st.markdown("""
    <style>
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
# BANCO DE DADOS
# -------------------------------
conn = sqlite3.connect("alvalav_os.db")
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT, cnpj TEXT, endereco TEXT, telefone TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE, senha TEXT, is_admin INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tipos_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT, servico TEXT, descricao TEXT,
                    status TEXT DEFAULT 'Aberta')''')

    # Garante que o usuário admin sempre exista
    c.execute("""
        INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin)
        VALUES ('admin', 'Alv32324@', 1)
    """)
    conn.commit()

init_db()

# -------------------------------
# LOGIN
# -------------------------------
st.title("ALVALAV — Sistema de Ordens de Serviço")

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
    st.session_state.is_admin = False

if not st.session_state.usuario_logado:
    st.subheader("🔑 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha)).fetchone()
        if user:
            st.session_state.usuario_logado = user[1]
            st.session_state.is_admin = bool(user[3])
            st.success(f"✅ Bem-vindo, {st.session_state.usuario_logado}!")
            st.experimental_rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# -------------------------------
# MENU PRINCIPAL
# -------------------------------
menu_principal = st.selectbox("📌 Selecione o Menu", ["Cadastro", "Ordem de Serviço"])

# -------------------------------
# CADASTROS
# -------------------------------
if menu_principal == "Cadastro":
    submenu = st.radio("Cadastros", ["Empresa", "Tipo de Serviço"] + (["Usuário"] if st.session_state.is_admin else []))

    if submenu == "Empresa":
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

    elif submenu == "Tipo de Serviço":
        st.subheader("⚙️ Cadastro de Tipo de Serviço")
        descricao = st.text_input("Descrição do serviço")
        if st.button("Salvar Serviço"):
            c.execute("INSERT INTO tipos_servico (descricao) VALUES (?)", (descricao,))
            conn.commit()
            st.success("✅ Tipo de serviço cadastrado com sucesso!")

    elif submenu == "Usuário":
        st.subheader("👤 Cadastro de Usuário (apenas admin)")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Salvar Usuário"):
            try:
                c.execute("INSERT INTO usuarios (usuario, senha, is_admin) VALUES (?,?,0)", (usuario, senha))
                conn.commit()
                st.success("✅ Usuário cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("⚠️ Esse usuário já existe!")

# -------------------------------
# ORDEM DE SERVIÇO
# -------------------------------
elif menu_principal == "Ordem de Serviço":
    submenu = st.radio("Ordem de Serviço", ["Abrir OS", "Consultar OS"])

    if submenu == "Abrir OS":
        st.subheader("📝 Abrir Ordem de Serviço")
        empresas = [row[0] for row in c.execute("SELECT nome FROM empresas").fetchall()]
        servicos = [row[0] for row in c.execute("SELECT descricao FROM tipos_servico").fetchall()]

        empresa = st.selectbox("Selecione a empresa", empresas if empresas else ["Nenhuma empresa cadastrada"])
        servico = st.selectbox("Selecione o serviço", servicos if servicos else ["Nenhum serviço cadastrado"])
        descricao = st.text_area("Descrição da OS")

        if st.button("Abrir OS"):
            c.execute("INSERT INTO ordens_servico (empresa, servico, descricao, status) VALUES (?,?,?,?)",
                      (empresa, servico, descricao, "Aberta"))
            conn.commit()
            st.success("✅ Ordem de Serviço criada com sucesso!")

    elif submenu == "Consultar OS":
        st.subheader("🔍 Consultar Ordens de Serviço")

        # Sempre mostra pendentes primeiro
        st.write("📌 **OS Pendentes:**")
        pendentes = c.execute("SELECT * FROM ordens_servico WHERE status!='Concluída'").fetchall()
        if pendentes:
            df_pend = pd.DataFrame(pendentes, columns=["ID", "Empresa", "Serviço", "Descrição", "Status"])
            df_pend["Situação"] = df_pend["Status"].apply(lambda x: "Pendente" if x != "Concluída" else "Finalizada")
            st.dataframe(df_pend)

        st.write("---")
        opcao_consulta = st.radio("Consultar por:", ["Todas", "Empresa", "Código da OS"])

        if opcao_consulta == "Todas":
            ordens = c.execute("SELECT * FROM ordens_servico").fetchall()
        elif opcao_consulta == "Empresa":
            empresas = [row[0] for row in c.execute("SELECT nome FROM empresas").fetchall()]
            empresa_filtro = st.selectbox("Selecione a empresa", empresas)
            ordens = c.execute("SELECT * FROM ordens_servico WHERE empresa=?", (empresa_filtro,)).fetchall()
        elif opcao_consulta == "Código da OS":
            codigo = st.number_input("Digite o código da OS", min_value=1, step=1)
            ordens = c.execute("SELECT * FROM ordens_servico WHERE id=?", (codigo,)).fetchall()

        if ordens:
            df = pd.DataFrame(ordens, columns=["ID", "Empresa", "Serviço", "Descrição", "Status"])
            df["Situação"] = df["Status"].apply(lambda x: "Pendente" if x != "Concluída" else "Finalizada")
            st.dataframe(df)

            # Exportar para Excel
            st.download_button(
                label="📥 Exportar para Excel",
                data=df.to_excel("ordens_servico.xlsx", index=False),
                file_name="ordens_servico.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Alterar status
            for ordem in ordens:
                st.markdown(f"### OS {ordem[0]} - {ordem[1]}")
                st.write(f"Serviço: {ordem[2]} | Status atual: **{ordem[4]}**")
                novo_status = st.selectbox(
                    f"Alterar status da OS {ordem[0]}",
                    ["Aberta", "Em andamento", "Concluída"],
                    index=["Aberta", "Em andamento", "Concluída"].index(ordem[4]) if ordem[4] else 0,
                    key=f"status_{ordem[0]}"
                )
                if st.button(f"Salvar Status OS {ordem[0]}", key=f"btn_status_{ordem[0]}"):
                    c.execute("UPDATE ordens_servico SET status=? WHERE id=?", (novo_status, ordem[0]))
                    conn.commit()
                    st.success(f"✅ Status da OS {ordem[0]} atualizado para {novo_status}")
                    st.experimental_rerun()
        else:
            st.info("Nenhuma OS encontrada com o filtro aplicado.")

