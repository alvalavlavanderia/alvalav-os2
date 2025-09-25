import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ===============================
# BANCO DE DADOS
# ===============================
def init_db():
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()

    # Usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE,
                    senha TEXT
                )''')

    # Empresas
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    rua TEXT,
                    numero TEXT,
                    cep TEXT,
                    cidade TEXT,
                    estado TEXT,
                    telefone TEXT NOT NULL,
                    cnpj TEXT NOT NULL
                )''')

    # Ordens de Serviço
    c.execute('''CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    tipo_servico TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    situacao TEXT DEFAULT 'Aberta',
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )''')

    # Usuário admin padrão
    c.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))

    conn.commit()
    conn.close()

# ===============================
# FUNÇÕES DE BANCO
# ===============================
def get_empresas():
    conn = sqlite3.connect("sistema.db")
    df = pd.read_sql("SELECT id, nome FROM empresas", conn)
    conn.close()
    return df

def add_empresa(nome, rua, numero, cep, cidade, estado, telefone, cnpj):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""INSERT INTO empresas (nome, rua, numero, cep, cidade, estado, telefone, cnpj)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (nome, rua, numero, cep, cidade, estado, telefone, cnpj))
    conn.commit()
    conn.close()

def add_ordem_servico(empresa_id, tipo_servico, titulo, descricao):
    conn = sqlite3.connect("sistema.db")
    c = conn.cursor()
    c.execute("""INSERT INTO ordens_servico (empresa_id, tipo_servico, titulo, descricao, situacao)
                 VALUES (?, ?, ?, ?, 'Aberta')""",
              (empresa_id, tipo_servico, titulo, descricao))
    conn.commit()
    conn.close()

def query_ordens(situacao=None, empresa_id=None):
    conn = sqlite3.connect("sistema.db")
    query = """SELECT os.id AS Codigo, e.nome AS Empresa, os.titulo AS Titulo, 
                      os.descricao AS Descricao, os.situacao AS Situacao
               FROM ordens_servico os
               JOIN empresas e ON os.empresa_id = e.id
               WHERE 1=1 """
    params = []

    if situacao:
        query += " AND os.situacao = ?"
        params.app
