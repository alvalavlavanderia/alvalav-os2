import streamlit as st
import sqlite3
import os
from datetime import datetime

# ================================
# Conexão com banco de dados
# ================================
DB_FILE = "alvalav_os.db"

# ================================
# Funções de Banco de Dados e Auxiliares
# ================================

def get_db_connection():
    """Cria e retorna uma nova conexão com o banco de dados."""
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = get_db_connection()
    c = conn.cursor()
    
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
                empresa TEXT, servico TEXT, titulo TEXT, descricao TEXT, status TEXT DEFAULT 'Aberta',
                data_abertura TEXT, data_atualizacao TEXT)''')

    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, is_admin) VALUES (?, ?, ?)",
              ("admin", "Alv32324@", 1))
    
    conn.commit()
    conn.close()

def reiniciar_db():
    """Remove o arquivo DB existente e o recria."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        st.success("Banco de dados existente removido com sucesso.")
    
    init_db()
    st.success("Banco de dados reiniciado e recriado com sucesso!")
    st.rerun()

def autenticar(usuario, senha):
    """Verifica as credenciais do usuário no banco de dados."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    user_data = c.fetchone()
    conn.close()
    return user_data

def is_admin(usuario):
    """Verifica se o usuário tem permissões de administrador."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_admin FROM usuarios WHERE usuario=?", (usuario,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def get_all_
