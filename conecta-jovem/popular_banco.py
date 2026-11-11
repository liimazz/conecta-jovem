
import os
import re

from app import app
from models import db, Usuario, Oportunidade, Curso, Candidatura
import seed_data


def popular_banco():
    senha_admin = os.environ.get("ADMIN_PASSWORD", "")

    if (
        len(senha_admin) < 8
        or not re.search(r"[A-Za-z]", senha_admin)
        or not re.search(r"\d", senha_admin)
    ):
        raise RuntimeError(
            "Configure ADMIN_PASSWORD com pelo menos 8 caracteres, "
            "incluindo letras e números."
        )

    with app.app_context():
        db.create_all()

        try:
            # Administrador: cria ou atualiza a conta com a senha nova.
            admin = Usuario.query.filter_by(
                email=seed_data.ADMIN["email"]
            ).first()

            if admin is None:
                admin = Usuario(
                    nome=seed_data.ADMIN["nome"],
                    email=seed_data.ADMIN["email"],
                    tipo="admin"
                )
                db.session.add(admin)

            admin.tipo = "admin"
            admin.definir_senha(senha_admin)

            # Usuários demonstrativos.
            usuarios = []

            for dados in seed_data.USUARIOS:
                usuario = Usuario.query.filter_by(
                    email=dados["email"]
                ).first()

                if usuario is None:
                    usuario = Usuario(
                        nome=dados["nome"],
                        email=dados["email"],
                        tipo=dados["tipo"]
                    )
                    usuario.definir_senha(dados["senha"])
                    db.session.add(usuario)

                usuarios.append(usuario)

            db.session.flush()

            # Oportunidades demonstrativas.
            oportunidades = []

            for dados in seed_data.OPORTUNIDADES:
                titulo, empresa, descricao, categoria, modalidade, localizacao, tipo = dados

                oportunidade = Oportunidade.query.filter_by(
                    titulo=titulo,
                    empresa=empresa
                ).first()

                if oportunidade is None:
                    oportunidade = Oportunidade(
                        titulo=titulo,
                        empresa=empresa,
                        descricao=descricao,
                        categoria=categoria,
                        modalidade=modalidade,
                        localizacao=localizacao,
                        tipo=tipo,
                        ativa=True
                    )
                    db.session.add(oportunidade)

                oportunidades.append(oportunidade)

            db.session.flush()

            # Cursos demonstrativos.
            for dados in seed_data.CURSOS:
                titulo, descricao, instituicao, categoria, horas, link = dados

                curso = Curso.query.filter_by(titulo=titulo).first()

                if curso is None:
                    curso = Curso(
                        titulo=titulo,
                        descricao=descricao,
                        instituicao=instituicao,
                        categoria=categoria,
                        carga_horaria=horas,
                        link=link
                    )
                    db.session.add(curso)

            db.session.flush()

            # Candidaturas demonstrativas.
            for indice_usuario, indice_oportunidade, status in seed_data.CANDIDATURAS:
                usuario = usuarios[indice_usuario]
                oportunidade = oportunidades[indice_oportunidade]

                candidatura = Candidatura.query.filter_by(
                    usuario_id=usuario.id,
                    oportunidade_id=oportunidade.id
                ).first()

                if candidatura is None:
                    candidatura = Candidatura(
                        usuario_id=usuario.id,
                        oportunidade_id=oportunidade.id,
                        status=status
                    )
                    db.session.add(candidatura)

            db.session.commit()

            print("Dados demonstrativos preparados com sucesso!")
            print("Usuários:", Usuario.query.count())
            print("Oportunidades:", Oportunidade.query.count())
            print("Cursos:", Curso.query.count())
            print("Candidaturas:", Candidatura.query.count())
            print("Administrador:", admin.email)

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    popular_banco()
