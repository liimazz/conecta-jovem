"""Modelos SQLAlchemy do Conecta Jovem."""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

STATUS_CANDIDATURA = ["Enviada", "Em análise", "Entrevista", "Aprovada", "Não selecionada"]
TIPOS_OPORTUNIDADE = ["Emprego", "Estágio", "Jovem Aprendiz"]
MODALIDADES = ["Presencial", "Remoto", "Híbrido"]


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="comum")  # comum | admin
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    candidaturas = db.relationship(
        "Candidatura", back_populates="usuario", cascade="all, delete-orphan"
    )

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.tipo == "admin"


class Oportunidade(db.Model):
    __tablename__ = "oportunidades"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    empresa = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(60), nullable=False)
    modalidade = db.Column(db.String(20), nullable=False)
    localizacao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    candidaturas = db.relationship(
        "Candidatura", back_populates="oportunidade", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "empresa": self.empresa,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "modalidade": self.modalidade,
            "localizacao": self.localizacao,
            "tipo": self.tipo,
            "ativa": self.ativa,
            "data_criacao": self.data_criacao.isoformat(),
        }


class Candidatura(db.Model):
    __tablename__ = "candidaturas"
    __table_args__ = (
        db.UniqueConstraint("usuario_id", "oportunidade_id", name="uq_candidatura_usuario_oportunidade"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    oportunidade_id = db.Column(
        db.Integer, db.ForeignKey("oportunidades.id", ondelete="CASCADE"), nullable=False
    )
    status = db.Column(db.String(20), nullable=False, default="Enviada")
    data_candidatura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    usuario = db.relationship("Usuario", back_populates="candidaturas")
    oportunidade = db.relationship("Oportunidade", back_populates="candidaturas")


class Curso(db.Model):
    __tablename__ = "cursos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    instituicao = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(60), nullable=False)
    carga_horaria = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(300), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "instituicao": self.instituicao,
            "categoria": self.categoria,
            "carga_horaria": self.carga_horaria,
            "link": self.link,
        }
