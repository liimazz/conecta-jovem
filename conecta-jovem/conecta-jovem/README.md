# Conecta Jovem

Plataforma web que conecta jovens a **empregos, estágios, vagas de jovem aprendiz e cursos de capacitação**.
Projeto alinhado à **ODS 8 da ONU (Trabalho Decente e Crescimento Econômico)**.

> Todas as empresas, vagas, instituições, cursos e pessoas do banco de exemplo são **fictícios** e identificados como demonstrativos.

## Tecnologias
HTML5, CSS3, JavaScript (sem frameworks), Python 3, Flask, SQLite e SQLAlchemy (Flask-SQLAlchemy). Produção com Gunicorn.

## Funcionalidades
- Página inicial, oportunidades (busca por palavra-chave e filtros por tipo, modalidade e categoria), detalhes, cursos, dicas e página sobre a ODS 8
- Cadastro, login e logout, com hash de senha, sessões, validação no servidor e mensagens de erro e sucesso
- Perfil com edição de dados e acompanhamento das candidaturas (também é possível cancelar)
- Candidatura com bloqueio de duplicidade (regra no código e restrição `UNIQUE` no banco), data e status
- Painel administrativo com dashboard e CRUD completo de oportunidades, cursos, usuários e candidaturas
- API JSON: `GET /api/oportunidades` e `GET /api/cursos`
- Proteção CSRF em todos os formulários, rotas privadas e administrativas validadas no backend

## Instalação e execução local
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # abre em http://localhost:5000
```
O arquivo `banco.db` já acompanha o projeto com dados de exemplo. Se ele não existir, o app o cria e popula sozinho na primeira execução. A inicialização **nunca apaga dados existentes**.

Variáveis de ambiente (opcionais localmente):
| Variável | Função |
|---|---|
| `SECRET_KEY` | Chave das sessões. Em produção, defina sempre. Sem ela, o app gera uma chave temporária. |
| `DATABASE_PATH` | Caminho do arquivo SQLite (padrão: `banco.db` na pasta do projeto). |
| `FLASK_DEBUG` | `1` ativa o modo de depuração local. |

## Credenciais de demonstração
| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | admin@conectajovem.demo | Admin@2026 |
| Usuário comum | ana@exemplo.demo | Jovem@2026 |

**Troque ou apague essas contas antes de qualquer uso real.**

## Teste rápido
```bash
python testes_rapidos.py
```

## Publicação no Render
1. Suba o projeto para um repositório no GitHub.
2. No Render, escolha **New > Blueprint** e aponte para o repositório (o `render.yaml` configura tudo), ou crie um **Web Service** manualmente:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. Variáveis de ambiente: `SECRET_KEY` (gerada automaticamente pelo blueprint) e `DATABASE_PATH=/var/data/banco.db`.
4. **Disco persistente**: adicione um disco com mount path `/var/data` (exige plano pago). Sem disco, o banco volta ao estado inicial a cada deploy.
5. Na primeira execução, como `/var/data/banco.db` ainda não existe, o app cria as tabelas e os dados de exemplo automaticamente. Para começar com o `banco.db` do repositório, copie-o para `/var/data` pelo Shell do Render.
6. Health check: `/saude`.

## Estrutura
```
app.py            rotas, validações, CRUD administrativo e inicialização
models.py         modelos SQLAlchemy
seed_data.py      dados de exemplo (fictícios)
gerar_banco.py    gera o banco.db de exemplo
banco.db          banco SQLite com dados demonstrativos
templates/        páginas Jinja (admin/ para o painel)
static/           css, js e img
relatorio/        relatório técnico, DER, dicionário de dados e rotas
```

## Rotas e API
Veja `relatorio/relatorio.md`.
