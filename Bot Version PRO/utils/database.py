# 📥 Importações
import sqlite3
import os

# 🛢️ Inicializar Banco de Dados
def init_db():
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()

    # Tabela de Produtos
    c.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            nome TEXT,
            categoria TEXT,
            preco REAL,
            estoque INTEGER
        )
    ''')

    # Tabela de Contas
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            produto_id INTEGER,
            email_senha TEXT
        )
    ''')

    # Tabela de Canais
    c.execute('''
        CREATE TABLE IF NOT EXISTS canais (
            guild_id INTEGER,
            categoria TEXT,
            canal_id INTEGER
        )
    ''')

    # Tabela de Access Tokens do MercadoPago
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            guild_id INTEGER PRIMARY KEY,
            token TEXT
        )
    ''')

    # Tabela de Admins
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            guild_id INTEGER,
            user_id INTEGER
        )
    ''')

    # Tabela de Webhooks (para Pix)
    c.execute('''
        CREATE TABLE IF NOT EXISTS webhooks (
            guild_id INTEGER PRIMARY KEY,
            url TEXT
        )
    ''')

    conn.commit()
    conn.close()

# 🛠️ Gerenciar Admins
def add_admin(guild_id, user_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('INSERT INTO admins (guild_id, user_id) VALUES (?, ?)', (guild_id, user_id))
    conn.commit()
    conn.close()

def is_admin(guild_id, user_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            guild_id INTEGER,
            user_id INTEGER
        )
    ''')
    c.execute('SELECT * FROM admins WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))
    result = c.fetchone()
    conn.close()
    return result is not None

# 🛠️ Gerenciar Webhooks
def set_webhook_url(guild_id, url):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS webhooks (
            guild_id INTEGER PRIMARY KEY,
            url TEXT
        )
    ''')
    c.execute('''
        INSERT OR REPLACE INTO webhooks (guild_id, url)
        VALUES (?, ?)
    ''', (guild_id, url))
    conn.commit()
    conn.close()

def get_webhook_url(guild_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT url FROM webhooks WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

# 🛠️ Gerenciar Access Tokens do MercadoPago
def set_mercadopago_token(guild_id, token):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO tokens (guild_id, token) VALUES (?, ?)', (guild_id, token))
    conn.commit()
    conn.close()

def get_mercadopago_token(guild_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT token FROM tokens WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

# 🛒 Gerenciar Produtos e Contas
def add_produto(guild_id, nome, categoria, preco, estoque):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('INSERT INTO produtos (guild_id, nome, categoria, preco, estoque) VALUES (?, ?, ?, ?, ?)', (guild_id, nome, categoria, preco, estoque))
    produto_id = c.lastrowid
    conn.commit()
    conn.close()
    return produto_id

def add_contas(guild_id, produto_id, contas):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    for conta in contas:
        c.execute('INSERT INTO contas (guild_id, produto_id, email_senha) VALUES (?, ?, ?)', (guild_id, produto_id, conta))
    conn.commit()
    conn.close()

def get_all_produtos(guild_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT id, nome, categoria, preco, estoque FROM produtos WHERE guild_id = ?', (guild_id,))
    produtos = c.fetchall()
    conn.close()
    return produtos

def get_produtos_por_categoria(guild_id, categoria):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT id, nome, preco, estoque FROM produtos WHERE guild_id = ? AND categoria = ?', (guild_id, categoria))
    produtos = c.fetchall()
    conn.close()
    return produtos

def vender_conta(guild_id, produto_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT id, email_senha FROM contas WHERE guild_id = ? AND produto_id = ? LIMIT 1', (guild_id, produto_id))
    conta = c.fetchone()

    if conta:
        conta_id, email_senha = conta
        c.execute('DELETE FROM contas WHERE id = ?', (conta_id,))
        c.execute('UPDATE produtos SET estoque = estoque - 1 WHERE id = ?', (produto_id,))
        conn.commit()
        conn.close()
        return email_senha
    conn.close()
    return None

def get_contas_do_produto(guild_id, produto_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT id, email_senha FROM contas WHERE guild_id = ? AND produto_id = ?', (guild_id, produto_id))
    contas = c.fetchall()
    conn.close()
    return contas

def remover_conta(guild_id, conta_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT produto_id FROM contas WHERE id = ?', (conta_id,))
    produto_id = c.fetchone()
    if produto_id:
        produto_id = produto_id[0]
        c.execute('DELETE FROM contas WHERE id = ?', (conta_id,))
        c.execute('UPDATE produtos SET estoque = estoque - 1 WHERE id = ?', (produto_id,))
        conn.commit()
    conn.close()
    return produto_id

# 🛠️ Gerenciar Canais
def set_canal(guild_id, categoria, canal_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO canais (guild_id, categoria, canal_id) VALUES (?, ?, ?)', (guild_id, categoria, canal_id))
    conn.commit()
    conn.close()

def get_canal(guild_id, categoria):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT canal_id FROM canais WHERE guild_id = ? AND categoria = ?', (guild_id, categoria))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def get_todas_categorias(guild_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('SELECT categoria, canal_id FROM canais WHERE guild_id = ?', (guild_id,))
    categorias = c.fetchall()
    conn.close()
    return categorias

# 🛠️ Limpar Estoque ZERADO
def limpar_estoque(guild_id):
    conn = sqlite3.connect('database/loja.db')
    c = conn.cursor()
    c.execute('DELETE FROM produtos WHERE guild_id = ? AND estoque <= 0', (guild_id,))
    conn.commit()
    conn.close()
