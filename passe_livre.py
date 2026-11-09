"""Módulo de decisão lógica (Computer Science): "Posso pedir o Passe Livre Interestadual?"

Roda sozinho (python passe_livre.py) ou pela opção 6 do assistente (python main.py).

Variáveis (1 = sim, 0 = não):
    A = recebe o BPC (Benefício de Prestação Continuada)
    B = está no Cadastro Único com renda de até 1 salário mínimo por pessoa
    C = consta no Cadastro-Inclusão
    D = tem o atestado de deficiência registrado pelo médico no site do Passe Livre

Saída S: 1 = pode pedir pelo site da ANTT; 0 = ainda não (o programa explica o que falta).

Expressões feitas à mão pela dupla (tabela-verdade, álgebra e mapa de Karnaugh):
    canônica:     S = Σm(5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
    simplificada: S = A + BC + BD
    De Morgan:    S' = A'(B' + C'D')
"""

import sys

FONTE = "https://www.gov.br/pt-br/servicos/obter-passe-livre-interestadual-digital"
VERIFICADO_EM = "2026-11-09"

AVISO = ("Aviso: este assistente NÃO é um canal oficial e NÃO confirma a concessão do Passe Livre. "
         "Quem analisa o pedido é a ANTT.")

LIMITACOES = [
    "Responde só com as 4 perguntas abaixo, como você respondeu. Não confere nenhum cadastro.",
    "Não vê o seu pedido, não decide se você tem direito e não substitui a ANTT.",
    "Vale para viagens entre estados, não para o ônibus da cidade.",
    "Regra conferida na fonte oficial na data indicada. Ela pode mudar: confirme no gov.br.",
    "Suas respostas não são guardadas em nenhum arquivo.",
]

# (letra, pergunta feita à pessoa, significado do 1, significado do 0)
VARIAVEIS = [
    ("A", "Você recebe o BPC (Benefício de Prestação Continuada)?",
     "recebe o BPC", "não recebe o BPC"),
    ("B", "Você está no Cadastro Único (CadÚnico) com renda de até 1 salário mínimo por pessoa da família?",
     "está no CadÚnico com essa renda", "não está no CadÚnico com essa renda"),
    ("C", "Você consta no Cadastro-Inclusão?",
     "consta no Cadastro-Inclusão", "não consta no Cadastro-Inclusão"),
    ("D", "Você tem o atestado de deficiência registrado pelo médico no site do Passe Livre?",
     "tem o atestado registrado", "não tem o atestado registrado"),
]

# Tabela-verdade feita à mão pela dupla: (A, B, C, D) -> S
TABELA_VERDADE = {
    (0, 0, 0, 0): 0, (0, 0, 0, 1): 0, (0, 0, 1, 0): 0, (0, 0, 1, 1): 0,
    (0, 1, 0, 0): 0, (0, 1, 0, 1): 1, (0, 1, 1, 0): 1, (0, 1, 1, 1): 1,
    (1, 0, 0, 0): 1, (1, 0, 0, 1): 1, (1, 0, 1, 0): 1, (1, 0, 1, 1): 1,
    (1, 1, 0, 0): 1, (1, 1, 0, 1): 1, (1, 1, 1, 0): 1, (1, 1, 1, 1): 1,
}

MINTERMOS = (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)


# ------------------------------------------------------------------ as 4 representações

def regra_original(a, b, c, d):
    """A regra como está escrita na fonte oficial: BPC, ou (CadÚnico e Cadastro-Inclusão),
    ou (CadÚnico e atestado)."""
    recebe_bpc = a == 1
    cadunico_e_inclusao = b == 1 and c == 1
    cadunico_e_atestado = b == 1 and d == 1
    return 1 if (recebe_bpc or cadunico_e_inclusao or cadunico_e_atestado) else 0


def expressao_canonica(a, b, c, d):
    """Soma de mintermos: S = A'BC'D + A'BCD' + A'BCD + AB'C'D' + AB'C'D + AB'CD'
    + AB'CD + ABC'D' + ABC'D + ABCD' + ABCD."""
    na, nb, nc, nd = 1 - a, 1 - b, 1 - c, 1 - d  # as portas NOT
    termos = [
        na & b & nc & d,    # m5
        na & b & c & nd,    # m6
        na & b & c & d,     # m7
        a & nb & nc & nd,   # m8
        a & nb & nc & d,    # m9
        a & nb & c & nd,    # m10
        a & nb & c & d,     # m11
        a & b & nc & nd,    # m12
        a & b & nc & d,     # m13
        a & b & c & nd,     # m14
        a & b & c & d,      # m15
    ]
    resultado = 0
    for termo in termos:
        resultado |= termo
    return resultado


def expressao_simplificada(a, b, c, d):
    """S = A + BC + BD (resultado igual na álgebra booleana e no mapa de Karnaugh)."""
    return a | (b & c) | (b & d)


def negacao_de_morgan(a, b, c, d):
    """S' = A'(B' + C'D'), obtida com os teoremas de De Morgan. Vale 1 quando S = 0."""
    na, nb, nc, nd = 1 - a, 1 - b, 1 - c, 1 - d
    return na & (nb | (nc & nd))


def avaliar(a, b, c, d):
    """Saída usada pelo programa: a expressão simplificada."""
    for valor in (a, b, c, d):
        if valor not in (0, 1):
            raise ValueError("cada entrada precisa ser 0 ou 1")
    return expressao_simplificada(a, b, c, d)


# ------------------------------------------------------------------ explicações

def motivos(a, b, c, d):
    """Lista quais dos 3 casos da regra valem (pode ser mais de um)."""
    casos = []
    if a:
        casos.append("você recebe o BPC")
    if b and c:
        casos.append("você está no CadÚnico com essa renda e consta no Cadastro-Inclusão")
    if b and d:
        casos.append("você está no CadÚnico com essa renda e tem o atestado registrado")
    return casos


def o_que_falta(a, b, c, d):
    """Explica o que falta quando S = 0, seguindo S' = A'(B' + C'D')."""
    if not negacao_de_morgan(a, b, c, d):
        return []
    if not b:  # A' e B'
        return [
            "Você não recebe o BPC e não está no CadÚnico com renda de até 1 salário mínimo por pessoa.",
            "Para pedir, é preciso uma destas coisas: receber o BPC, ou estar no CadÚnico com essa renda "
            "(e ter o Cadastro-Inclusão ou o atestado registrado).",
            "O CadÚnico é feito no CRAS da sua região. O BPC é pedido pelo Meu INSS ou pelo telefone 135.",
        ]
    # A', B e C'D'
    return [
        "Você está no CadÚnico, mas ainda falta uma destas coisas:",
        "  - constar no Cadastro-Inclusão; ou",
        "  - ter o atestado de deficiência registrado pelo médico no site do Passe Livre.",
        "Com uma das duas, você já pode fazer o pedido.",
    ]


# ------------------------------------------------------------------ entrada e tela

def ler_resposta(pergunta):
    """Pergunta até receber sim ou não. Aceita s, sim, 1, n, nao, não, 0. Devolve 1 ou 0."""
    while True:
        texto = input(pergunta + " (s/n): ").strip().lower()
        if texto in ("s", "sim", "1"):
            return 1
        if texto in ("n", "nao", "não", "0"):
            return 0
        if texto == "":
            print("Resposta vazia. Responda com s (sim) ou n (não).")
        else:
            print(f'"{texto}" não é uma resposta válida. Responda com s (sim) ou n (não).')


def mostrar_resultado(a, b, c, d):
    """Mostra as entradas, a saída S e a orientação correspondente."""
    s = avaliar(a, b, c, d)
    print()
    print(f"Entradas: A={a}  B={b}  C={c}  D={d}")
    print(f"Expressão: S = A + BC + BD = {a} + {b}·{c} + {b}·{d} = {s}")
    print()
    if s == 1:
        print(">> Você pode pedir o Passe Livre Interestadual pelo site da ANTT.")
        print("Porque " + "; e ".join(motivos(a, b, c, d)) + ".")
        print("Onde: passelivre.antt.gov.br, com a sua conta gov.br.")
        print("Isso não garante a aprovação: quem confirma é a ANTT, no próprio pedido.")
    else:
        print(">> Ainda não dá para pedir. Veja o que falta:")
        for linha in o_que_falta(a, b, c, d):
            print(linha)
    print()
    print(f"Fonte: {FONTE} (verificado em {VERIFICADO_EM})")
    print(AVISO)
    return s


def consultar():
    """Faz as 4 perguntas, mostra a orientação e não guarda nada."""
    print()
    print("POSSO PEDIR O PASSE LIVRE INTERESTADUAL?")
    print("Responda 4 perguntas de sim ou não. Nada do que você responder é guardado.")
    respostas = []
    for letra, pergunta, _, _ in VARIAVEIS:
        respostas.append(ler_resposta(f"{letra}) {pergunta}"))
    return mostrar_resultado(*respostas)


def combinacoes():
    """As 16 combinações na ordem da tabela-verdade (linha 0 a 15)."""
    for linha in range(16):
        yield linha, ((linha >> 3) & 1, (linha >> 2) & 1, (linha >> 1) & 1, linha & 1)


def validar():
    """Compara as 4 representações nas 16 combinações. Devolve a lista de linhas com diferença."""
    print()
    print("VALIDAÇÃO: AS 16 COMBINAÇÕES DA TABELA-VERDADE")
    print("Linha  A B C D | Tabela  Regra  Canônica  Simplificada  De Morgan(S') | OK")
    erros = []
    for linha, (a, b, c, d) in combinacoes():
        tabela = TABELA_VERDADE[(a, b, c, d)]
        regra = regra_original(a, b, c, d)
        canonica = expressao_canonica(a, b, c, d)
        simplificada = avaliar(a, b, c, d)
        negada = negacao_de_morgan(a, b, c, d)
        no_mintermo = 1 if linha in MINTERMOS else 0
        ok = tabela == regra == canonica == simplificada == no_mintermo == 1 - negada
        if not ok:
            erros.append(linha)
        print(f"{linha:>5}  {a} {b} {c} {d} | {tabela:>6}  {regra:>5}  {canonica:>8}  "
              f"{simplificada:>12}  {negada:>13} | {'sim' if ok else 'NÃO'}")
    if erros:
        print(f"Diferença nas linhas: {erros}")
    else:
        print("As 16 combinações deram o mesmo resultado nas 4 representações, e S' é sempre o contrário de S.")
    return erros


def sobre():
    print()
    print("SOBRE ESTE MÓDULO")
    print("Módulo de decisão lógica do trabalho de Computer Science (FIAP, GS 2026.2).")
    print("Variáveis (1 = sim, 0 = não):")
    for letra, _, um, zero in VARIAVEIS:
        print(f"  {letra}: 1 = {um}; 0 = {zero}")
    print("Saída S: 1 = pode pedir pelo site da ANTT; 0 = ainda não (mostra o que falta).")
    print("Expressão simplificada: S = A + BC + BD")
    print(f"Fonte: {FONTE} (verificado em {VERIFICADO_EM})")
    print("Limitações:")
    for limitacao in LIMITACOES:
        print(f"  - {limitacao}")
    print(AVISO)


def menu():
    """Menu do módulo. Usado sozinho e pela opção 6 do assistente."""
    while True:
        print()
        print("PASSE LIVRE INTERESTADUAL (módulo de Computer Science)")
        print("1 - Descobrir se posso pedir")
        print("2 - Ver a validação das 16 combinações")
        print("3 - Variáveis, fonte e limitações")
        print("0 - Voltar")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "1":
            consultar()
        elif opcao == "2":
            validar()
        elif opcao == "3":
            sobre()
        elif opcao == "0":
            return
        elif opcao == "":
            print("Resposta vazia. Digite 1, 2, 3 ou 0.")
        else:
            print(f'"{opcao}" não é uma opção. Digite 1, 2, 3 ou 0.')


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        if not sys.stdin.isatty():
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print(AVISO)
    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print()
    print("Até logo! Confirme sempre no gov.br.")
