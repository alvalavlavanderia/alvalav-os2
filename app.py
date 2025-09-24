import streamlit as st
import sqlite3
import pandas as pd

# -------------------------------
# BANCO DE DADOS
# -------------------------------
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE,
                    senha TEXT,
                    is_admin INTEGER DEFAULT 0
                )''')

    # Tabela de empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    endereco TEXT,
                    numero TEXT,
                    cep TEXT,
                    cidade TEXT,
                    estado TEXT,
                    telefone TEXT NOT NULL,
                    cnpj TEXT NOT NULL
                )''')

    # Tabela de Ordens de Serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    situacao TEXT DEFAULT 'Aberta',
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )''')

    # Criar usuário admin
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))

    conn.commit()
    conn.close()

init_db()

# -------------------------------
# FUNÇÕES DE BANCO
# -------------------------------
def get_empresas():
    conn = sqlite3.connect("sistema.db")
    df = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()
    return df

def get_ordens(situacao=None, empresa_id=None):
    conn = sqlite3.connect("sistema.db")
    query = """SELECT os.id, e.nome as empresa, os.titulo, os.descricao, os.situacao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id
               WHERE 1=1"""
    params = []
    if situacao:
        query += " AND os.situacao = ?"
        params.append(situacao)
    if empresa_id:
        query += " AND os.empresa_id = ?"
        params.append(empresa_id)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def delete_ordem(os_id):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("DELETE FROM ordens_servico WHERE id = ?", (os_id,))
    conn.commit()
    conn.close()

def update_ordem(os_id, titulo, descricao, situacao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("UPDATE ordens_servico SET titulo=?, descricao=?, situacao=? WHERE id=?",
              (titulo, descricao, situacao, os_id))
    conn.commit()
    conn.close()

# -------------------------------
# INTERFACE STREAMLIT
# -------------------------------
st.set_page_config(page_title="Sistema OS", page_icon="🛠", layout="centered")

menu = st.sidebar.selectbox("Menu", ["Cadastrar Empresa", "Abrir OS", "Consultar OS"])

# -------------------------------
# CADASTRAR EMPRESA
# -------------------------------
if menu == "Cadastrar Empresa":
    st.title("🏢 Cadastrar Empresa")

    with st.form("form_empresa"):
        nome = st.text_input("Empresa *")
        endereco = st.text_input("Endereço")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        telefone = st.text_input("Telefone *")
        cnpj = st.text_input("CNPJ *")

        submitted = st.form_submit_button("Salvar")

        if submitted:
            if not nome or not telefone or not cnpj:
                st.error("⚠️ Campos obrigatórios não preenchidos: Empresa, Telefone e CNPJ.")
            else:
                conn = sqlite3.connect("sistema.db")
                c = conn.cursor()
                c.execute("""INSERT INTO empresas (nome, endereco, numero, cep, cidade, estado, telefone, cnpj)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                          (nome, endereco, numero, cep, cidade, estado, telefone, cnpj))
                conn.commit()
                conn.close()
                st.success("✅ Empresa cadastrada com sucesso!")

# -------------------------------
# ABRIR ORDEM DE SERVIÇO
# -------------------------------
elif menu == "Abrir OS":
    st.title("📝 Abrir Ordem de Serviço")

    empresas = get_empresas()

    with st.form("form_os"):
        empresa = st.selectbox("Empresa *", [""] + empresas["nome"].tolist())
        titulo = st.text_input("Título *")
        descricao = st.text_area("Descrição *")
        situacao = "Aberta"  # sempre começa aberta

        submitted = st.form_submit_button("Salvar")

        if submitted:
            if not empresa or not titulo or not descricao:
                st.error("⚠️ Todos os campos são obrigatórios!")
            else:
                empresa_id = empresas.loc[empresas["nome"] == empresa, "id"].values[0]
                conn = sqlite3.connect("sistema.db")
                c = conn.cursor()
                c.execute("INSERT INTO ordens_servico (empresa_id, titulo, descricao, situacao) VALUES (?, ?, ?, ?)",
                          (empresa_id, titulo, descricao, situacao))
                conn.commit()
                conn.close()
                st.success("✅ Ordem de Serviço aberta com sucesso!")

# -------------------------------
# CONSULTAR ORDEM DE SERVIÇO
# -------------------------------
elif menu == "Consultar OS":
    st.title("🔎 Consultar Ordens de Serviço")

    situacao = st.selectbox("Filtrar por Situação", ["", "Aberta", "Finalizada"])
    empresas = get_empresas()
    empresa = st.selectbox("Filtrar por Empresa", [""] + empresas["nome"].tolist())

    empresa_id = None
    if empresa:
        empresa_id = empresas.loc[empresas["nome"] == empresa, "id"].values[0]

    df = get_ordens(situacao if situacao else None, empresa_id)

    if not df.empty:
        df = df.rename(columns={"id": "CÓDIGO", "empresa": "EMPRESA", "titulo": "TÍTULO", "descricao": "DESCRIÇÃO", "situacao": "SITUAÇÃO"})
        for i, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1,2,2,3,2,2])
            col1.write(row["CÓDIGO"])
            col2.write(row["EMPRESA"])
            col3.write(row["TÍTULO"])
            col4.write(row["DESCRIÇÃO"])
            col5.write(row["SITUAÇÃO"])

            if col6.button("✏️", key=f"edit_{row['CÓDIGO']}"):
                with st.form(f"edit_form_{row['CÓDIGO']}"):
                    new_titulo = st.text_input("Título", row["TÍTULO"])
                    new_desc = st.text_area("Descrição", row["DESCRIÇÃO"])
                    new_sit = st.selectbox("Situação", ["Aberta", "Finalizada"], index=0 if row["SITUAÇÃO"] == "Aberta" else 1)
                    save_btn = st.form_submit_button("Salvar alterações")
                    if save_btn:
                        update_ordem(row["CÓDIGO"], new_titulo, new_desc, new_sit)
                        st.success("✅ Ordem de Serviço atualizada com sucesso!")
                        st.rerun()

            if col6.button("❌", key=f"del_{row['CÓDIGO']}"):
                delete_ordem(row["CÓDIGO"])
                st.warning("🗑️ Ordem de Serviço excluída!")
                st.rerun()
    else:
        st.info("Nenhuma Ordem de Serviço encontrada.")
