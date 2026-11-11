"""Dados demonstrativos. Todos fictícios: nenhuma empresa, vaga ou pessoa é real."""

ADMIN = {"nome": "Administrador Demo", "email": "admin@conectajovem.demo", "senha": "Admin@2026", "tipo": "admin"}

USUARIOS = [
    {"nome": "Ana Exemplo", "email": "ana@exemplo.demo", "senha": "Jovem@2026", "tipo": "comum"},
    {"nome": "Bruno Exemplo", "email": "bruno@exemplo.demo", "senha": "Jovem@2026", "tipo": "comum"},
    {"nome": "Carla Exemplo", "email": "carla@exemplo.demo", "senha": "Jovem@2026", "tipo": "comum"},
]

# (titulo, empresa, descricao, categoria, modalidade, localizacao, tipo)
OPORTUNIDADES = [
    ("Auxiliar administrativo júnior", "Empresa Exemplo A (demo)", "Apoio em rotinas de escritório, organização de documentos e atendimento interno. Vaga demonstrativa.", "Administração", "Presencial", "Natal - RN", "Emprego"),
    ("Estágio em desenvolvimento web", "Empresa Exemplo B (demo)", "Estágio para estudantes de TI: HTML, CSS, JavaScript e noções de Python, com mentoria. Vaga demonstrativa.", "Tecnologia", "Remoto", "Remoto - Brasil", "Estágio"),
    ("Jovem Aprendiz - Atendimento", "Empresa Exemplo C (demo)", "Programa de aprendizagem com formação teórica e prática em atendimento ao cliente. Vaga demonstrativa.", "Atendimento", "Presencial", "Parnamirim - RN", "Jovem Aprendiz"),
    ("Estágio em Marketing Digital", "Empresa Exemplo D (demo)", "Apoio na criação de conteúdo, calendário editorial e análise básica de métricas. Vaga demonstrativa.", "Marketing", "Híbrido", "Natal - RN", "Estágio"),
    ("Assistente de suporte técnico", "Empresa Exemplo E (demo)", "Suporte a usuários, instalação de softwares e registro de chamados. Vaga demonstrativa.", "Tecnologia", "Híbrido", "Recife - PE", "Emprego"),
    ("Jovem Aprendiz - Logística", "Empresa Exemplo F (demo)", "Aprendizagem em controle de estoque, conferência de mercadorias e expedição. Vaga demonstrativa.", "Logística", "Presencial", "Mossoró - RN", "Jovem Aprendiz"),
    ("Estágio em Design Gráfico", "Empresa Exemplo G (demo)", "Criação de peças digitais e apoio à identidade visual da equipe. Vaga demonstrativa.", "Design", "Remoto", "Remoto - Brasil", "Estágio"),
    ("Auxiliar financeiro", "Empresa Exemplo H (demo)", "Conciliação simples, lançamentos e apoio ao contas a pagar. Vaga demonstrativa.", "Finanças", "Presencial", "Fortaleza - CE", "Emprego"),
    ("Jovem Aprendiz - Administrativo", "Empresa Exemplo I (demo)", "Rotinas administrativas, planilhas e arquivo, com acompanhamento de um tutor. Vaga demonstrativa.", "Administração", "Híbrido", "Natal - RN", "Jovem Aprendiz"),
    ("Estágio em Análise de Dados", "Empresa Exemplo J (demo)", "Organização de bases, gráficos e relatórios simples em planilhas e Python. Vaga demonstrativa.", "Tecnologia", "Remoto", "Remoto - Brasil", "Estágio"),
]

# (titulo, descricao, instituicao, categoria, carga_horaria, link)
CURSOS = [
    ("Introdução à Programação (demo)", "Lógica de programação e primeiros passos com Python. Curso demonstrativo.", "Instituição Exemplo 1 (demo)", "Tecnologia", 40, "https://example.com/cursos/programacao"),
    ("Excel para o Trabalho (demo)", "Planilhas, fórmulas e gráficos para a rotina profissional. Curso demonstrativo.", "Instituição Exemplo 2 (demo)", "Administração", 30, "https://example.com/cursos/excel"),
    ("Comunicação e Entrevistas (demo)", "Como se expressar bem e se preparar para processos seletivos. Curso demonstrativo.", "Instituição Exemplo 3 (demo)", "Desenvolvimento pessoal", 20, "https://example.com/cursos/comunicacao"),
    ("Marketing Digital Básico (demo)", "Redes sociais, conteúdo e métricas para iniciantes. Curso demonstrativo.", "Instituição Exemplo 4 (demo)", "Marketing", 36, "https://example.com/cursos/marketing"),
    ("Educação Financeira Pessoal (demo)", "Orçamento, reserva de emergência e primeiros investimentos. Curso demonstrativo.", "Instituição Exemplo 5 (demo)", "Finanças", 24, "https://example.com/cursos/financas"),
    ("Design com Ferramentas Gratuitas (demo)", "Princípios de design e criação de peças digitais. Curso demonstrativo.", "Instituição Exemplo 6 (demo)", "Design", 32, "https://example.com/cursos/design"),
]

# (indice_usuario, indice_oportunidade, status)
CANDIDATURAS = [(0, 1, "Em análise"), (0, 3, "Enviada"), (1, 2, "Entrevista"), (2, 0, "Enviada")]
