"""Teste de fumaça: python testes_rapidos.py  (usa um banco temporário, não toca no banco.db)."""
import os
import re
import tempfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "teste.db")
os.environ["SECRET_KEY"] = "teste"

from app import app  # noqa: E402
from models import Candidatura, Usuario  # noqa: E402


def csrf(html):
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def logar(c, email, senha):
    t = csrf(c.get("/login").get_data(as_text=True))
    return c.post("/login", data={"csrf_token": t, "email": email, "senha": senha})


def main():
    c = app.test_client()
    for rota in ("/", "/oportunidades", "/cursos", "/dicas", "/ods", "/login", "/cadastro", "/saude"):
        assert c.get(rota).status_code == 200, rota
    r = c.get("/api/oportunidades").get_json()
    assert r["sucesso"] and r["total"] == 10, r
    assert c.get("/api/cursos").get_json()["total"] == 6
    assert c.get("/api/inexistente").status_code == 404
    assert c.get("/api/inexistente").get_json()["sucesso"] is False
    assert c.get("/oportunidades?q=dados").get_data(as_text=True).count("Análise de Dados") >= 1
    assert c.get("/oportunidades?tipo=Estágio&modalidade=Remoto").status_code == 200
    # CSRF e proteção de rotas
    assert c.post("/login", data={"email": "x", "senha": "y"}).status_code == 400
    assert c.get("/admin").status_code == 302 and c.get("/perfil").status_code == 302
    # cadastro + login + candidatura + duplicidade
    t = csrf(c.get("/cadastro").get_data(as_text=True))
    dados = {"csrf_token": t, "nome": "Teste Demo", "email": "teste@exemplo.demo", "senha": "Senha123", "confirmar_senha": "Senha123"}
    assert c.post("/cadastro", data=dados).status_code == 302
    assert c.post("/cadastro", data=dados).status_code == 400  # e-mail duplicado
    assert logar(c, "teste@exemplo.demo", "Senha123").status_code == 302
    t = csrf(c.get("/oportunidades/5").get_data(as_text=True))
    c.post("/oportunidades/5/candidatar", data={"csrf_token": t})
    c.post("/oportunidades/5/candidatar", data={"csrf_token": t})
    with app.app_context():
        u = Usuario.query.filter_by(email="teste@exemplo.demo").first()
        assert Candidatura.query.filter_by(usuario_id=u.id).count() == 1
        assert u.senha_hash != "Senha123"
    assert c.get("/admin").status_code == 403  # usuário comum não acessa
    assert c.get("/admin/usuarios").status_code == 403
    # admin: CRUD
    a = app.test_client()
    assert logar(a, "admin@conectajovem.demo", "Admin@2026").status_code == 302
    for rota in ("/admin", "/admin/oportunidades", "/admin/cursos", "/admin/usuarios", "/admin/candidaturas"):
        assert a.get(rota).status_code == 200, rota
    t = csrf(a.get("/admin/cursos/novo").get_data(as_text=True))
    novo = {"csrf_token": t, "titulo": "Curso Teste", "instituicao": "Inst. Teste", "descricao": "Descrição de teste longa",
            "categoria": "Teste", "carga_horaria": "10", "link": "https://example.com/x"}
    assert a.post("/admin/cursos/novo", data=novo).status_code == 302
    assert a.get("/api/cursos").get_json()["total"] == 7
    assert a.post("/admin/cursos/7/editar", data={**novo, "titulo": "Curso Editado"}).status_code == 302
    assert a.post("/admin/cursos/7/excluir", data={"csrf_token": t}).status_code == 302
    assert a.get("/api/cursos").get_json()["total"] == 6
    assert a.post("/admin/cursos/novo", data={**novo, "carga_horaria": "abc"}).status_code == 400
    print("Todos os testes passaram.")


if __name__ == "__main__":
    main()
