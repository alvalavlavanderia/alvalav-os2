import streamlit as st
import sqlite3
import bcrypt

# ======================
# CONFIGURAÇÃO
# ======================
DB_NAME = "sistema_os.db"
ADMIN_PASSWORD = "1234" 

# ======================
# BANCO DE DADOS - Operações Centralizadas
# ======================
def conectar_bd():
    """Retorna uma única conexão e um cursor para o banco de dados.
    Aumenta o timeout para 15 segundos para evitar 'database is locked'."""
    # A correção está aqui: abre a conexão UMA vez e usa o timeout
    conn = sqlite3.connect(DB_NAME, timeout=15) 
    c = conn.cursor()
    return conn, c

def criar_banco():
    """Cria as tabelas e o usuário administrador inicial."""
    conn, c = conectar_bd()

    # Criação das tabelas
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
            cnpj TEXT UNIQUE NOT NULL, 
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
            nome TEXT UNIQUE NOT NULL
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
            FOREIGN KEY (empresa_id) REFERENCES empresas (id) ON DELETE CASCADE,
            FOREIGN KEY (tipo_servico_id) REFERENCES servicos (id) ON DELETE RESTRICT
        )
    """)

    # Criação do usuário admin
    senha_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt())
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
              ("admin", senha_hash, "admin"))

    conn.commit()
    conn.close()

def db_fetch(query, params=()):
    """Executa SELECT e retorna todos os resultados, fechando a conexão."""
    conn, c = conectar_bd()
    c.execute(query, params)
    data = c.fetchall()
    conn.close() # Fechamento imediato
    return data

def db_execute(query, params=()):
    """Executa INSERT/UPDATE/DELETE e retorna True em sucesso, fechando a conexão."""
    conn, c = conectar_bd()
    try:
        c.execute(query, params)
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        return str(e)
    except Exception as e:
        return str(e)
    finally:
        # Garante que a conexão SEMPRE seja fechada
        conn.close()


# ======================
# AUTENTICAÇÃO
# ======================
def autenticar_usuario(usuario, senha):
    """Verifica se o usuário e a senha estão corretos."""
    user = db_fetch("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    if user and bcrypt.checkpw(senha.encode("utf-8"), user[0][2]):
        return user[0]
    return None

def logout():
    """Executa o logout e limpa os estados da sessão de navegação de OS."""
    if "usuario" in st.session_state:
        del st.session_state["usuario"]
    if "editando_os" in st.session_state:
        del st.session_state["editando_os"]
    st.rerun()


# ======================
# FUNÇÕES DE UTILIDADE
# ======================
def get_options_from_db(table_name):
    """Busca ID e NOME para SelectBox."""
    return db_fetch(f"SELECT id, nome FROM {table_name}")

def formatar_opcao_select(item):
    """Formata (ID, NOME) para SelectBox (ex: '1 - Nome')."""
    return f"{item[0]} - {item[1]}"

def parse_opcao_select(opcao_formatada):
    """Extrai o ID de uma opção formatada (ex: '1 - Nome' -> 1)."""
    if not opcao_formatada:
        return None
    return int(opcao_formatada.split(" - ")[0])

def validar_campos(campos):
    """Verifica se todos os campos na lista são não vazios."""
    return all(campos)


# ======================
# CADASTRO EMPRESA
# ======================
def cadastro_empresa():
    st.subheader("🏢 Cadastro de Empresa")

    with st.form("form_empresa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Empresa*").strip()
            cnpj = st.text_input("CNPJ*").strip()
            telefone = st.text_input("Telefone*").strip()
        with col2:
            rua = st.text_input("Rua*").strip()
            cep = st.text_input("CEP*").strip()
            numero = st.text_input("Número*").strip()
        cidade = st.text_input("Cidade*").strip()
        estado = st.selectbox("Estado*", ["SP", "RJ", "MG", "PR", "SC", "RS", "Outro"], index=0).strip()

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            dados = [nome, cnpj, telefone, rua, cep, numero, cidade, estado]
            if not validar_campos(dados):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                query = """
                    INSERT INTO empresas (nome, cnpj, telefone, rua, cep, numero, cidade, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                resultado = db_execute(query, dados)
                if resultado is True:
                    st.success("✅ Empresa cadastrada com sucesso!")
                elif "UNIQUE constraint failed: empresas.cnpj" in resultado:
                    st.error("⚠️ Erro: CNPJ já cadastrado!")
                else:
                    st.error(f"❌ Erro ao cadastrar empresa: {resultado}")


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
                resultado = db_execute("INSERT INTO servicos (nome) VALUES (?)", (nome,))
                if resultado is True:
                    st.success("✅ Serviço cadastrado com sucesso!")
                elif "UNIQUE constraint failed: servicos.nome" in resultado:
                    st.error("⚠️ Erro: Tipo de Serviço já existe!")
                else:
                    st.error(f"❌ Erro ao cadastrar serviço: {resultado}")


# ======================
# CADASTRO USUÁRIO
# ======================
def cadastro_usuario():
    st.subheader("👤 Cadastro de Usuário (apenas Admin)")
    if st.session_state["usuario"][3] != "admin":
        st.warning("🔒 Apenas usuários administradores podem cadastrar outros usuários.")
        return

    with st.form("form_usuario", clear_on_submit=True):
        usuario = st.text_input("Usuário*").strip()
        senha = st.text_input("Senha*", type="password").strip()
        tipo = "admin"

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not usuario or not senha:
                st.error("⚠️ Usuário e senha são obrigatórios.")
            else:
                senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
                resultado = db_execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                                       (usuario, senha_hash, tipo))

                if resultado is True:
                    st.success("✅ Usuário cadastrado com sucesso!")
                elif "UNIQUE constraint failed: usuarios.usuario" in resultado:
                    st.error("⚠️ Usuário já existe!")
                else:
                    st.error(f"❌ Erro ao cadastrar usuário: {resultado}")


# ======================
# ABRIR ORDEM DE SERVIÇO
# ======================
def abrir_os():
    st.subheader("📌 Abrir Ordem de Serviço")

    empresas = get_options_from_db("empresas")
    servicos = get_options_from_db("servicos")

    if not empresas or not servicos:
        st.warning("⚠️ É necessário cadastrar pelo menos uma **Empresa** e um **Tipo de Serviço** antes de abrir uma OS.")
        return

    empresa_opcoes = [formatar_opcao_select(e) for e in empresas]
    servico_opcoes = [formatar_opcao_select(s) for s in servicos]

    with st.form("form_os", clear_on_submit=True):
        empresa = st.selectbox("Empresa*", empresa_opcoes)
        titulo = st.text_input("Título*").strip()
        descricao = st.text_area("Descrição*").strip()
        tipo_servico = st.selectbox("Tipo de Serviço*", servico_opcoes)
        situacao = "Aberta"

        submitted = st.form_submit_button("Abrir OS")

        if submitted:
            if not validar_campos([empresa, titulo, descricao, tipo_servico]):
                st.error("⚠️ Todos os campos são obrigatórios.")
            else:
                empresa_id = parse_opcao_select(empresa)
                servico_id = parse_opcao_select(tipo_servico)

                query = """
                    INSERT INTO ordens (empresa_id, titulo, descricao, tipo_servico_id, situacao)
                    VALUES (?, ?, ?, ?, ?)
                """
                resultado = db_execute(query, (empresa_id, titulo, descricao, servico_id, situacao))

                if resultado is True:
                    st.success("✅ Ordem de Serviço aberta com sucesso!")
                else:
                    st.error(f"❌ Erro ao abrir OS: {resultado}")


# ======================
# EDITAR ORDEM DE SERVIÇO
# ======================
def editar_os(ordem_id):
    st.subheader(f"✏️ Editar OS **#{ordem_id}**")

    ordem = db_fetch("SELECT empresa_id, titulo, descricao, tipo_servico_id, situacao FROM ordens WHERE id=?",
                     (ordem_id,))
    empresas = get_options_from_db("empresas")
    servicos = get_options_from_db("servicos")

    if not ordem:
        st.error("⚠️ OS não encontrada!")
        return

    ordem = ordem[0]

    empresa_opcoes = [formatar_opcao_select(e) for e in empresas]
    servico_opcoes = [formatar_opcao_select(s) for s in servicos]

    try:
        empresa_inicial = next(formatar_opcao_select(e) for e in empresas if e[0] == ordem[0])
        servico_inicial = next(formatar_opcao_select(s) for s in servicos if s[0] == ordem[3])
        situacao_inicial = ordem[4]

        empresa_index = empresa_opcoes.index(empresa_inicial)
        servico_index = servico_opcoes.index(servico_inicial)
        situacao_opcoes = ["Aberta", "Finalizada"]
        situacao_index = situacao_opcoes.index(situacao_inicial)

    except (StopIteration, ValueError):
        st.error("⚠️ Dados de referência (Empresa ou Serviço) não encontrados para esta OS. Verifique os cadastros.")
        return


    with st.form(f"form_edit_os_{ordem_id}"):
        empresa = st.selectbox("Empresa*", empresa_opcoes, index=empresa_index)
        titulo = st.text_input("Título*", ordem[1])
        descricao = st.text_area("Descrição*", ordem[2])
        tipo_servico = st.selectbox("Tipo de Serviço*", servico_opcoes, index=servico_index)
        situacao = st.selectbox("Situação*", situacao_opcoes, index=situacao_index)

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("✅ Salvar Alterações", type="primary", use_container_width=True)
        with col_cancel:
            if st.button("↩️ Cancelar Edição", use_container_width=True):
                del st.session_state["editando_os"]
                st.rerun()

        if submitted:
            empresa_id = parse_opcao_select(empresa)
            servico_id = parse_opcao_select(tipo_servico)

            query = """
                UPDATE ordens
                SET empresa_id=?, titulo=?, descricao=?, tipo_servico_id=?, situacao=?
                WHERE id=?
            """
            resultado = db_execute(query, (empresa_id, titulo, descricao, servico_id, situacao, ordem_id))

            if resultado is True:
                st.success("✅ OS atualizada com sucesso!")
                del st.session_state["editando_os"]
                st.rerun()
            else:
                 st.error(f"❌ Erro ao atualizar OS: {resultado}")


# ======================
# CONSULTAR OS
# ======================
def consultar_os():
    st.subheader("🔎 Consultar Ordens de Serviço")

    if "editando_os" in st.session_state:
        editar_os(st.session_state["editando_os"])
        return

    # Limpa o estado de confirmação de exclusão ao recarregar a lista
    for key in list(st.session_state.keys()):
        if key.startswith("confirm_delete_"):
            del st.session_state[key]


    filtro = st.radio("Filtrar por situação:", ["Aberta", "Finalizada"], horizontal=True)

    ordens = db_fetch("""
        SELECT o.id, e.nome, o.titulo, s.nome, o.situacao
        FROM ordens o
        JOIN empresas e ON o.empresa_id = e.id
        JOIN servicos s ON o.tipo_servico_id = s.id
        WHERE o.situacao=?
        ORDER BY o.id DESC
    """, (filtro,))

    if not ordens:
        st.info(f"Nenhuma Ordem de Serviço com a situação **{filtro}** encontrada.")
        return

    st.markdown("---")

    for ordem in ordens:
        os_id, empresa_nome, titulo, servico_nome, situacao = ordem

        with st.container(border=True):
            st.markdown(f"**OS #{os_id}** | **Situação:** `{situacao}`")
            st.markdown(f"**Empresa:** {empresa_nome}")
            st.markdown(f"**Título:** {titulo}")
            st.markdown(f"**Serviço:** {servico_nome}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Editar", key=f"edit_{os_id}", use_container_width=True):
                    st.session_state["editando_os"] = os_id
                    st.rerun()
            with col2:
                # Lógica de confirmação de exclusão
                confirm_key = f"confirm_delete_{os_id}"
                if st.session_state.get(confirm_key):
                    st.warning(f"Confirma exclusão da OS **#{os_id}**?")
                    if st.button("✅ Confirmar Exclusão", key=f"confirm_{os_id}", use_container_width=True, type="primary"):
                        resultado = db_execute("DELETE FROM ordens WHERE id=?", (os_id,))
                        if resultado is True:
                            st.success(f"✅ OS #{os_id} excluída!")
                            del st.session_state[confirm_key]
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao excluir OS: {resultado}")
                else:
                    if st.button("🗑️ Excluir", key=f"delete_{os_id}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun() # Força o rerun para exibir a confirmação


# ======================
# INICIALIZAÇÃO DO BANCO DE DADOS
# Executado UMA ÚNICA VEZ ao iniciar o app.
# ======================
criar_banco()


# ======================
# APP PRINCIPAL
# ======================
def main():
    st.set_page_config(page_title="Sistema de OS", layout="wide")
    st.title("📂 Sistema de Ordens de Serviço")

    # --- Lógica de Login ---
    if "usuario" not in st.session_state:
        st.subheader("🔐 Login")
        usuario = st.text_input("Usuário").strip()
        senha = st.text_input("Senha", type="password").strip()

        if st.button("Entrar", use_container_width=True, type="primary"):
            user = autenticar_usuario(usuario, senha)
            if user:
                st.session_state["usuario"] = user
                st.session_state["menu_selecionado"] = "consultar_os"
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
        return 

    # --- Lógica do Menu (Após Login) ---
    with st.sidebar:
        st.header("📋 Menu Principal")
        st.markdown(f"**Usuário:** `{st.session_state['usuario'][1]}`")
        st.markdown(f"**Tipo:** `{st.session_state['usuario'][3]}`")
        st.write("---")

        with st.expander("➕ Cadastro", expanded=False):
            if st.button("Empresa", key="btn_cad_empresa", use_container_width=True):
                st.session_state["menu_selecionado"] = "cad_empresa"
            if st.button("Tipo de Serviço", key="btn_cad_servico", use_container_width=True):
                st.session_state["menu_selecionado"] = "cad_servico"
            if st.button("Usuário", key="btn_cad_usuario", use_container_width=True):
                 st.session_state["menu_selecionado"] = "cad_usuario"

        with st.expander("📄 Ordens de Serviço", expanded=True):
            if st.button("Abrir OS", key="btn_abrir_os", use_container_width=True):
                st.session_state["menu_selecionado"] = "abrir_os"
            if st.button("Consultar/Gerenciar OS", key="btn_consultar_os", type="primary", use_container_width=True):
                st.session_state["menu_selecionado"] = "consultar_os"

        st.write("---")

        if st.button("🚪 Logout", use_container_width=True):
            logout()


    # 2. Roteamento de Páginas
    menu = st.session_state.get("menu_selecionado", "consultar_os")

    if menu != "consultar_os" and "editando_os" in st.session_state:
        del st.session_state["editando_os"]

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
        st.info("👈 Selecione uma opção no menu ao lado para começar a gerenciar Ordens de Serviço.")


if __name__ == "__main__":
    main()
