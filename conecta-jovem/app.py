"""Conecta Jovem: plataforma de oportunidades para jovens (ODS 8).

Execução local:  python app.py
Produção (Render): gunicorn app:app
"""
import os
import re
import secrets
import sqlite3
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import event, func
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import seed_data
from models import (MODALIDADES, STATUS_CANDIDATURA, TIPOS_OPORTUNIDADE,
                    Candidatura, Curso, Oportunidade, Usuario, db)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def criar_app():
    app = Flask(__name__)

    secret = os.environ.get("SECRET_KEY")
    if not secret:
        # Sem SECRET_KEY definida, gera uma chave temporária (sessões expiram ao reiniciar).
        secret = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY não definida: usando chave temporária.")
    caminho_banco = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "banco.db"))
    os.makedirs(os.path.dirname(os.path.abspath(caminho_banco)), exist_ok=True)

    app.config.update(
        SECRET_KEY=secret,
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.abspath(caminho_banco),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    db.init_app(app)
    with app.app_context():
        inicializar_banco()
    registrar_rotas(app)
    return app


@event.listens_for(Engine, "connect")
def ativar_chaves_estrangeiras(conexao, _):
    if isinstance(conexao, sqlite3.Connection):
        cur = conexao.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def inicializar_banco():
    """Cria tabelas e dados de exemplo somente se ainda não existirem. Nunca apaga dados."""
    db.create_all()
    if Usuario.query.count() == 0:
        admin = Usuario(nome=seed_data.ADMIN["nome"], email=seed_data.ADMIN["email"], tipo="admin")
        admin.definir_senha(seed_data.ADMIN["senha"])
        db.session.add(admin)
        usuarios = []
        for u in seed_data.USUARIOS:
            novo = Usuario(nome=u["nome"], email=u["email"], tipo=u["tipo"])
            novo.definir_senha(u["senha"])
            usuarios.append(novo)
            db.session.add(novo)
        db.session.flush()
        if Oportunidade.query.count() == 0:
            ops = [Oportunidade(titulo=t, empresa=e, descricao=d, categoria=c, modalidade=m,
                                localizacao=l, tipo=tp) for t, e, d, c, m, l, tp in seed_data.OPORTUNIDADES]
            db.session.add_all(ops)
            db.session.flush()
            for ui, oi, st in seed_data.CANDIDATURAS:
                db.session.add(Candidatura(usuario_id=usuarios[ui].id, oportunidade_id=ops[oi].id, status=st))
        if Curso.query.count() == 0:
            db.session.add_all([Curso(titulo=t, descricao=d, instituicao=i, categoria=c,
                                      carga_horaria=h, link=l) for t, d, i, c, h, l in seed_data.CURSOS])
        db.session.commit()


# ---------- Validação ----------
def validar_senha(senha):
    if len(senha) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        return "A senha deve conter letras e números."
    return None


def validar_nome_email(nome, email, ignorar_id=None):
    erros = []
    if not 2 <= len(nome) <= 100:
        erros.append("Informe um nome com 2 a 100 caracteres.")
    if len(email) > 120 or not EMAIL_RE.match(email):
        erros.append("Informe um e-mail válido.")
    else:
        existente = Usuario.query.filter(func.lower(Usuario.email) == email).first()
        if existente and existente.id != ignorar_id:
            erros.append("Este e-mail já está cadastrado.")
    return erros


def url_segura(destino):
    """Aceita apenas caminhos internos no parâmetro next (evita open redirect)."""
    if not destino:
        return None
    p = urlparse(destino)
    if p.scheme or p.netloc or not destino.startswith("/") or destino.startswith("//"):
        return None
    return destino


def escapar_like(texto):
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def filtrar_oportunidades(args):
    q = Oportunidade.query.filter_by(ativa=True)
    busca = (args.get("q") or "").strip()[:100]
    if busca:
        termo = f"%{escapar_like(busca)}%"
        q = q.filter(db.or_(Oportunidade.titulo.ilike(termo, escape="\\"),
                            Oportunidade.empresa.ilike(termo, escape="\\"),
                            Oportunidade.descricao.ilike(termo, escape="\\")))
    for campo in ("tipo", "modalidade", "categoria"):
        valor = (args.get(campo) or "").strip()
        if valor:
            q = q.filter(getattr(Oportunidade, campo) == valor)
    return q.order_by(Oportunidade.data_criacao.desc(), Oportunidade.id.desc())


# ---------- Administração genérica (CRUD) ----------
def opcoes_usuarios():
    return [(u.id, f"{u.nome} ({u.email})") for u in Usuario.query.order_by(Usuario.nome)]


def opcoes_oportunidades():
    return [(o.id, f"{o.titulo} - {o.empresa}") for o in Oportunidade.query.order_by(Oportunidade.titulo)]


def campo(nome, rotulo, tipo="text", obrigatorio=True, maximo=None, minimo=None, opcoes=None):
    return dict(nome=nome, rotulo=rotulo, tipo=tipo, obrigatorio=obrigatorio,
                maximo=maximo, minimo=minimo, opcoes=opcoes)


ENTIDADES = {
    "oportunidades": dict(
        modelo=Oportunidade, singular="oportunidade", plural="Oportunidades",
        colunas=[("titulo", "Título"), ("empresa", "Empresa"), ("tipo", "Tipo"), ("modalidade", "Modalidade"), ("ativa", "Ativa")],
        campos=lambda: [
            campo("titulo", "Título", maximo=150), campo("empresa", "Empresa", maximo=120),
            campo("descricao", "Descrição", "textarea", maximo=2000, minimo=10),
            campo("categoria", "Categoria", maximo=60),
            campo("modalidade", "Modalidade", "select", opcoes=[(m, m) for m in MODALIDADES]),
            campo("localizacao", "Localização", maximo=100),
            campo("tipo", "Tipo", "select", opcoes=[(t, t) for t in TIPOS_OPORTUNIDADE]),
            campo("ativa", "Vaga ativa (visível ao público)", "checkbox", obrigatorio=False)]),
    "cursos": dict(
        modelo=Curso, singular="curso", plural="Cursos",
        colunas=[("titulo", "Título"), ("instituicao", "Instituição"), ("categoria", "Categoria"), ("carga_horaria", "Horas")],
        campos=lambda: [
            campo("titulo", "Título", maximo=150), campo("instituicao", "Instituição", maximo=120),
            campo("descricao", "Descrição", "textarea", maximo=2000, minimo=10),
            campo("categoria", "Categoria", maximo=60),
            campo("carga_horaria", "Carga horária (horas)", "number", minimo=1, maximo=2000),
            campo("link", "Link do curso (https://...)", "url", maximo=300)]),
    "usuarios": dict(
        modelo=Usuario, singular="usuário", plural="Usuários",
        colunas=[("nome", "Nome"), ("email", "E-mail"), ("tipo", "Tipo"), ("data_criacao", "Criado em")],
        campos=lambda: [
            campo("nome", "Nome", maximo=100), campo("email", "E-mail", "email", maximo=120),
            campo("senha", "Senha (deixe em branco para manter)", "password", obrigatorio=False),
            campo("tipo", "Tipo de conta", "select", opcoes=[("comum", "Usuário comum"), ("admin", "Administrador")])]),
    "candidaturas": dict(
        modelo=Candidatura, singular="candidatura", plural="Candidaturas",
        colunas=[("usuario", "Usuário"), ("oportunidade", "Oportunidade"), ("status", "Status"), ("data_candidatura", "Data")],
        campos=lambda: [
            campo("usuario_id", "Usuário", "select", opcoes=opcoes_usuarios()),
            campo("oportunidade_id", "Oportunidade", "select", opcoes=opcoes_oportunidades()),
            campo("status", "Status", "select", opcoes=[(s, s) for s in STATUS_CANDIDATURA])]),
}


def ler_formulario(chave, form, obj=None):
    """Valida o formulário no servidor e devolve (dados, erros)."""
    dados, erros = {}, []
    for c in ENTIDADES[chave]["campos"]():
        n, rot = c["nome"], c["rotulo"]
        bruto = form.get(n, "")
        if c["tipo"] == "checkbox":
            dados[n] = n in form
            continue
        valor = bruto.strip()
        if not valor:
            if c["obrigatorio"]:
                erros.append(f"Preencha o campo: {rot}.")
            dados[n] = None if c["tipo"] == "password" else valor
            continue
        if c["tipo"] == "number" or n.endswith("_id"):
            if not valor.isdigit():
                erros.append(f"Valor inválido em: {rot}.")
                continue
            valor = int(valor)
            if c["tipo"] == "number" and not (c["minimo"] <= valor <= c["maximo"]):
                erros.append(f"{rot} deve estar entre {c['minimo']} e {c['maximo']}.")
        else:
            if c["maximo"] and len(valor) > c["maximo"]:
                erros.append(f"{rot} aceita até {c['maximo']} caracteres.")
            if c["minimo"] and len(valor) < c["minimo"]:
                erros.append(f"{rot} deve ter ao menos {c['minimo']} caracteres.")
        if c["tipo"] == "select":
            validos = [str(o[0]) for o in c["opcoes"]]
            if str(valor) not in validos:
                erros.append(f"Opção inválida em: {rot}.")
        if c["tipo"] == "url" and not re.match(r"^https?://[^\s]+$", str(valor)):
            erros.append("O link deve começar com http:// ou https://.")
        dados[n] = valor
    if chave == "usuarios":
        dados["email"] = (dados.get("email") or "").lower()
        erros += validar_nome_email(dados.get("nome") or "", dados["email"], obj.id if obj else None)
        if dados.get("senha"):
            e = validar_senha(dados["senha"])
            erros += [e] if e else []
        elif obj is None:
            erros.append("Defina uma senha para o novo usuário.")
    if chave == "candidaturas" and not erros:
        existente = Candidatura.query.filter_by(usuario_id=dados["usuario_id"],
                                                oportunidade_id=dados["oportunidade_id"]).first()
        if existente and (obj is None or existente.id != obj.id):
            erros.append("Este usuário já possui candidatura para essa oportunidade.")
    return dados, erros


# ---------- Rotas ----------
def registrar_rotas(app):
    @app.before_request
    def preparar_requisicao():
        g.usuario = db.session.get(Usuario, session["uid"]) if "uid" in session else None
        if "uid" in session and g.usuario is None:
            session.clear()
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        if request.method == "POST" and not request.path.startswith("/api/"):
            enviado = request.form.get("csrf_token", "")
            if not secrets.compare_digest(enviado, session.get("csrf", "")):
                abort(400, "Sessão expirada ou formulário inválido. Recarregue a página e tente de novo.")

    @app.context_processor
    def contexto():
        return dict(usuario=g.get("usuario"), csrf_token=session.get("csrf", ""),
                    TIPOS=TIPOS_OPORTUNIDADE, MODALIDADES=MODALIDADES, STATUS=STATUS_CANDIDATURA)

    @app.after_request
    def cabecalhos(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        return resp

    def login_obrigatorio(f):
        @wraps(f)
        def interno(*a, **kw):
            if g.usuario is None:
                flash("Entre na sua conta para continuar.", "erro")
                return redirect(url_for("login", next=request.full_path.rstrip("?")))
            return f(*a, **kw)
        return interno

    def admin_obrigatorio(f):
        @wraps(f)
        @login_obrigatorio
        def interno(*a, **kw):
            if not g.usuario.is_admin:
                abort(403)
            return f(*a, **kw)
        return interno

    @app.get("/saude")
    def saude():
        return jsonify(sucesso=True, status="ok")

    # --- Público ---
    @app.get("/")
    def inicio():
        destaques = Oportunidade.query.filter_by(ativa=True).order_by(Oportunidade.data_criacao.desc(), Oportunidade.id.desc()).limit(3).all()
        numeros = dict(vagas=Oportunidade.query.filter_by(ativa=True).count(), cursos=Curso.query.count(),
                       jovens=Usuario.query.filter_by(tipo="comum").count(), candidaturas=Candidatura.query.count())
        return render_template("index.html", destaques=destaques, numeros=numeros)

    @app.get("/oportunidades")
    def oportunidades():
        itens = filtrar_oportunidades(request.args).all()
        categorias = [c[0] for c in db.session.query(Oportunidade.categoria).filter(Oportunidade.ativa.is_(True)).distinct().order_by(Oportunidade.categoria)]
        candidatadas = set()
        if g.usuario:
            candidatadas = {c.oportunidade_id for c in g.usuario.candidaturas}
        return render_template("oportunidades.html", itens=itens, categorias=categorias,
                               filtros=request.args, candidatadas=candidatadas)

    @app.get("/oportunidades/<int:oid>")
    def oportunidade_detalhe(oid):
        op = db.get_or_404(Oportunidade, oid)
        if not op.ativa and not (g.usuario and g.usuario.is_admin):
            abort(404)
        ja = bool(g.usuario and Candidatura.query.filter_by(usuario_id=g.usuario.id, oportunidade_id=oid).first())
        return render_template("oportunidade_detalhe.html", op=op, ja_candidatou=ja)

    @app.post("/oportunidades/<int:oid>/candidatar")
    @login_obrigatorio
    def candidatar(oid):
        op = db.get_or_404(Oportunidade, oid)
        if not op.ativa:
            flash("Esta oportunidade não está mais ativa.", "erro")
        elif Candidatura.query.filter_by(usuario_id=g.usuario.id, oportunidade_id=oid).first():
            flash("Você já se candidatou a esta oportunidade.", "erro")
        else:
            try:
                db.session.add(Candidatura(usuario_id=g.usuario.id, oportunidade_id=oid))
                db.session.commit()
                flash("Candidatura enviada! Acompanhe o status no seu perfil.", "sucesso")
            except IntegrityError:
                db.session.rollback()
                flash("Você já se candidatou a esta oportunidade.", "erro")
        return redirect(url_for("oportunidade_detalhe", oid=oid))

    @app.get("/cursos")
    def cursos():
        categoria = (request.args.get("categoria") or "").strip()
        q = Curso.query
        if categoria:
            q = q.filter_by(categoria=categoria)
        categorias = [c[0] for c in db.session.query(Curso.categoria).distinct().order_by(Curso.categoria)]
        return render_template("cursos.html", itens=q.order_by(Curso.titulo).all(), categorias=categorias, categoria=categoria)

    @app.get("/dicas")
    def dicas():
        return render_template("dicas.html")

    @app.get("/ods")
    def ods():
        return render_template("ods.html")

    # --- Autenticação ---
    @app.route("/cadastro", methods=["GET", "POST"])
    def cadastro():
        if g.usuario:
            return redirect(url_for("perfil"))
        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            email = request.form.get("email", "").strip().lower()
            senha = request.form.get("senha", "")
            erros = validar_nome_email(nome, email)
            erro_senha = validar_senha(senha)
            if erro_senha:
                erros.append(erro_senha)
            if senha != request.form.get("confirmar_senha", ""):
                erros.append("As senhas não conferem.")
            if erros:
                for e in erros:
                    flash(e, "erro")
                return render_template("cadastro.html", nome=nome, email=email), 400
            novo = Usuario(nome=nome, email=email, tipo="comum")
            novo.definir_senha(senha)
            try:
                db.session.add(novo)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Este e-mail já está cadastrado.", "erro")
                return render_template("cadastro.html", nome=nome, email=email), 400
            flash("Conta criada com sucesso! Entre para continuar.", "sucesso")
            return redirect(url_for("login"))
        return render_template("cadastro.html", nome="", email="")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.usuario:
            return redirect(url_for("perfil"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            u = Usuario.query.filter(func.lower(Usuario.email) == email).first()
            if u and u.verificar_senha(request.form.get("senha", "")):
                session.clear()
                session["uid"] = u.id
                session["csrf"] = secrets.token_hex(16)
                flash(f"Bem-vindo(a), {u.nome.split()[0]}!", "sucesso")
                return redirect(url_safe_next() or url_for("painel_admin" if u.is_admin else "perfil"))
            flash("E-mail ou senha incorretos.", "erro")
            return render_template("login.html", email=email), 401
        return render_template("login.html", email="")

    def url_safe_next():
        return url_segura(request.args.get("next") or request.form.get("next"))

    @app.post("/logout")
    def logout():
        session.clear()
        flash("Você saiu da sua conta.", "sucesso")
        return redirect(url_for("inicio"))

    # --- Perfil ---
    @app.route("/perfil", methods=["GET", "POST"])
    @login_obrigatorio
    def perfil():
        u = g.usuario
        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            email = request.form.get("email", "").strip().lower()
            nova = request.form.get("nova_senha", "")
            erros = validar_nome_email(nome, email, u.id)
            if nova:
                if not u.verificar_senha(request.form.get("senha_atual", "")):
                    erros.append("A senha atual está incorreta.")
                e = validar_senha(nova)
                if e:
                    erros.append(e)
            if erros:
                for e in erros:
                    flash(e, "erro")
            else:
                u.nome, u.email = nome, email
                if nova:
                    u.definir_senha(nova)
                try:
                    db.session.commit()
                    flash("Dados atualizados com sucesso.", "sucesso")
                except IntegrityError:
                    db.session.rollback()
                    flash("Este e-mail já está cadastrado.", "erro")
            return redirect(url_for("perfil"))
        cands = Candidatura.query.filter_by(usuario_id=u.id).order_by(Candidatura.data_candidatura.desc()).all()
        return render_template("perfil.html", candidaturas=cands)

    @app.post("/perfil/candidaturas/<int:cid>/cancelar")
    @login_obrigatorio
    def cancelar_candidatura(cid):
        c = db.get_or_404(Candidatura, cid)
        if c.usuario_id != g.usuario.id:
            abort(403)
        db.session.delete(c)
        db.session.commit()
        flash("Candidatura cancelada.", "sucesso")
        return redirect(url_for("perfil"))

    # --- API JSON ---
    @app.get("/api/oportunidades")
    def api_oportunidades():
        itens = filtrar_oportunidades(request.args).all()
        return jsonify(sucesso=True, total=len(itens), oportunidades=[o.to_dict() for o in itens])

    @app.get("/api/cursos")
    def api_cursos():
        itens = Curso.query.order_by(Curso.titulo).all()
        return jsonify(sucesso=True, total=len(itens), cursos=[c.to_dict() for c in itens])

    # --- Painel administrativo ---
    @app.get("/admin")
    @admin_obrigatorio
    def painel_admin():
        por_status = dict(db.session.query(Candidatura.status, func.count(Candidatura.id)).group_by(Candidatura.status).all())
        recentes = Candidatura.query.order_by(Candidatura.data_candidatura.desc()).limit(5).all()
        totais = dict(usuarios=Usuario.query.count(), oportunidades=Oportunidade.query.count(),
                      cursos=Curso.query.count(), candidaturas=Candidatura.query.count())
        return render_template("admin/dashboard.html", totais=totais, por_status=por_status, recentes=recentes)

    def entidade_ou_404(chave):
        if chave not in ENTIDADES:
            abort(404)
        return ENTIDADES[chave]

    @app.get("/admin/<chave>")
    @admin_obrigatorio
    def admin_lista(chave):
        ent = entidade_ou_404(chave)
        itens = ent["modelo"].query.order_by(ent["modelo"].id.desc()).all()
        return render_template("admin/lista.html", chave=chave, ent=ent, itens=itens)

    def salvar(chave, obj=None):
        ent = ENTIDADES[chave]
        novo = obj is None
        dados, erros = ler_formulario(chave, request.form, obj)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("admin/form.html", chave=chave, ent=ent, campos=ent["campos"](),
                                   obj=obj, valores=request.form), 400
        if novo:
            obj = ent["modelo"]()
            db.session.add(obj)
        senha = dados.pop("senha", None) if chave == "usuarios" else None
        if chave == "usuarios" and obj is not None and obj.id == g.usuario.id and dados["tipo"] != "admin":
            db.session.rollback()
            flash("Você não pode remover o seu próprio acesso de administrador.", "erro")
            return redirect(url_for("admin_lista", chave=chave))
        for k, v in dados.items():
            setattr(obj, k, v)
        if senha:
            obj.definir_senha(senha)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Registro duplicado ou inconsistente. Verifique os dados.", "erro")
            return render_template("admin/form.html", chave=chave, ent=ent, campos=ent["campos"](),
                                   obj=obj, valores=request.form), 400
        flash(f"{ent['singular'].capitalize()} {'criado(a)' if novo else 'atualizado(a)'} com sucesso.", "sucesso")
        return redirect(url_for("admin_lista", chave=chave))

    @app.route("/admin/<chave>/novo", methods=["GET", "POST"])
    @admin_obrigatorio
    def admin_novo(chave):
        ent = entidade_ou_404(chave)
        if request.method == "POST":
            return salvar(chave)
        padrao = {"ativa": "on"} if chave == "oportunidades" else {}
        return render_template("admin/form.html", chave=chave, ent=ent, campos=ent["campos"](), obj=None, valores=padrao)

    @app.route("/admin/<chave>/<int:rid>/editar", methods=["GET", "POST"])
    @admin_obrigatorio
    def admin_editar(chave, rid):
        ent = entidade_ou_404(chave)
        obj = db.get_or_404(ent["modelo"], rid)
        if request.method == "POST":
            return salvar(chave, obj)
        valores = {c["nome"]: getattr(obj, c["nome"], "") for c in ent["campos"]() if c["nome"] != "senha"}
        if chave == "oportunidades":
            valores["ativa"] = "on" if obj.ativa else ""
        return render_template("admin/form.html", chave=chave, ent=ent, campos=ent["campos"](), obj=obj, valores=valores)

    @app.post("/admin/<chave>/<int:rid>/excluir")
    @admin_obrigatorio
    def admin_excluir(chave, rid):
        ent = entidade_ou_404(chave)
        obj = db.get_or_404(ent["modelo"], rid)
        if chave == "usuarios":
            if obj.id == g.usuario.id:
                flash("Você não pode excluir a sua própria conta.", "erro")
                return redirect(url_for("admin_lista", chave=chave))
            if obj.is_admin and Usuario.query.filter_by(tipo="admin").count() <= 1:
                flash("Não é possível excluir o último administrador.", "erro")
                return redirect(url_for("admin_lista", chave=chave))
        try:
            db.session.delete(obj)
            db.session.commit()
            flash(f"{ent['singular'].capitalize()} excluído(a) com sucesso.", "sucesso")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível excluir o registro.", "erro")
        return redirect(url_for("admin_lista", chave=chave))

    # --- Erros ---
    def e_api():
        return request.path.startswith("/api/")

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(413)
    def erro_http(e):
        if e_api():
            return jsonify(sucesso=False, erro=e.name, codigo=e.code), e.code
        return render_template("erro.html", codigo=e.code, titulo=e.name, mensagem=e.description), e.code

    @app.errorhandler(500)
    def erro_interno(e):
        db.session.rollback()
        if e_api():
            return jsonify(sucesso=False, erro="Erro interno do servidor", codigo=500), 500
        return render_template("erro.html", codigo=500, titulo="Erro interno",
                               mensagem="Algo deu errado do nosso lado. Tente novamente em instantes."), 500


app = criar_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 5000)))
