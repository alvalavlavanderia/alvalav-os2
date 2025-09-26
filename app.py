import streamlit as st
import sqlite3
import bcrypt

# ======================
# CONFIGURAÇÃO
# ======================
DB_NAME = "sistema_os.db"
ADMIN_PASSWORD = "1234" # Senha inicial para o admin

# ======================
# BANCO DE DADOS - Operações Centralizadas
# ======================
def conectar_bd():
    """Retorna uma conexão e um cursor para o banco de dados."""
    # O timeout pode ajudar em ambientes de rede mais lentos
    return sqlite3.connect(DB_NAME, timeout=10), sqlite3.connect(DB_NAME, timeout=10).cursor()

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
    """Executa SELECT e retorna todos os resultados."""
    conn, c = conectar_bd()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

def db_execute(query, params=()):
    """Executa INSERT/UPDATE/DELETE e retorna True em sucesso."""
    conn, c = conectar_bd()
    try:
        c.execute(query, params)
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.close()
        return str(e)
    except Exception as e:
        conn.close()
        return str(e)
    finally:
        conn.close()


# ======================
# AUTENTICAÇÃO
# ======================
def autenticar_usuario(usuario, senha):
    """Verifica se o usuário e a senha estão corretos."""
    user = db
