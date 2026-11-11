"""Gera o banco.db com dados demonstrativos usando apenas sqlite3 + werkzeug.

O esquema espelha exatamente models.py. Uso:  python gerar_banco.py
Não é necessário em produção: o app cria e popula o banco sozinho se ele não existir.
"""
import os
import sqlite3
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

import seed_data

CAMINHO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco.db")

ESQUEMA = """
CREATE TABLE usuarios (
    id INTEGER NOT NULL, nome VARCHAR(100) NOT NULL, email VARCHAR(120) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL, tipo VARCHAR(10) NOT NULL, data_criacao DATETIME NOT NULL,
    PRIMARY KEY (id));
CREATE UNIQUE INDEX ix_usuarios_email ON usuarios (email);
CREATE TABLE oportunidades (
    id INTEGER NOT NULL, titulo VARCHAR(150) NOT NULL, empresa VARCHAR(120) NOT NULL,
    descricao TEXT NOT NULL, categoria VARCHAR(60) NOT NULL, modalidade VARCHAR(20) NOT NULL,
    localizacao VARCHAR(100) NOT NULL, tipo VARCHAR(20) NOT NULL, ativa BOOLEAN NOT NULL,
    data_criacao DATETIME NOT NULL, PRIMARY KEY (id));
CREATE TABLE cursos (
    id INTEGER NOT NULL, titulo VARCHAR(150) NOT NULL, descricao TEXT NOT NULL,
    instituicao VARCHAR(120) NOT NULL, categoria VARCHAR(60) NOT NULL, carga_horaria INTEGER NOT NULL,
    link VARCHAR(300) NOT NULL, PRIMARY KEY (id));
CREATE TABLE candidaturas (
    id INTEGER NOT NULL, usuario_id INTEGER NOT NULL, oportunidade_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, data_candidatura DATETIME NOT NULL, PRIMARY KEY (id),
    CONSTRAINT uq_candidatura_usuario_oportunidade UNIQUE (usuario_id, oportunidade_id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY(oportunidade_id) REFERENCES oportunidades (id) ON DELETE CASCADE);
"""


def agora(dias_atras=0):
    return (datetime.utcnow() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S.%f")


def main():
    if os.path.exists(CAMINHO):
        raise SystemExit("banco.db já existe; apague-o manualmente antes de gerar de novo.")
    con = sqlite3.connect(CAMINHO)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(ESQUEMA)
    a = seed_data.ADMIN
    con.execute("INSERT INTO usuarios (nome,email,senha_hash,tipo,data_criacao) VALUES (?,?,?,?,?)",
                (a["nome"], a["email"], generate_password_hash(a["senha"]), "admin", agora(30)))
    for i, u in enumerate(seed_data.USUARIOS):
        con.execute("INSERT INTO usuarios (nome,email,senha_hash,tipo,data_criacao) VALUES (?,?,?,?,?)",
                    (u["nome"], u["email"], generate_password_hash(u["senha"]), u["tipo"], agora(20 - i)))
    for i, o in enumerate(seed_data.OPORTUNIDADES):
        con.execute("INSERT INTO oportunidades (titulo,empresa,descricao,categoria,modalidade,localizacao,tipo,ativa,data_criacao) VALUES (?,?,?,?,?,?,?,1,?)",
                    (*o, agora(len(seed_data.OPORTUNIDADES) - i)))
    for c in seed_data.CURSOS:
        con.execute("INSERT INTO cursos (titulo,descricao,instituicao,categoria,carga_horaria,link) VALUES (?,?,?,?,?,?)", c)
    for k, (ui, oi, st) in enumerate(seed_data.CANDIDATURAS):
        con.execute("INSERT INTO candidaturas (usuario_id,oportunidade_id,status,data_candidatura) VALUES (?,?,?,?)",
                    (ui + 2, oi + 1, st, agora(5 - k)))  # admin tem id 1; jovens começam no 2
    con.commit()
    con.close()
    print("banco.db criado em", CAMINHO)


if __name__ == "__main__":
    main()
