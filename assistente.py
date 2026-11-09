"""Classe Assistente: conversa com o cidadão, guarda o histórico e calcula os indicadores."""

import csv
import json
import os
import time
from datetime import datetime

import passe_livre
from base_conhecimento import confianca
from orientacao import AVISO_OFICIAL

CAMPOS_CSV = [
    "data", "origem", "pergunta", "id_orientacao", "encontrou",
    "ajudou", "tentativas", "tempo_segundos",
]

MINIMO_DIGITOS_DADO_PESSOAL = 8  # 8 dígitos ou mais parece CPF, RG ou telefone


def contem_dado_pessoal(texto):
    """True se o texto parece ter CPF, RG, telefone (8+ dígitos) ou e-mail (@)."""
    digitos = sum(1 for caractere in texto if caractere.isdigit())
    return digitos >= MINIMO_DIGITOS_DADO_PESSOAL or "@" in texto


def ler_opcao(mensagem, minimo, maximo):
    """Pede um número entre minimo e maximo até a pessoa digitar um válido.

    Entrada vazia, letras ou número fora da faixa nunca encerram o programa.
    """
    while True:
        texto = input(mensagem).strip()
        if texto == "":
            print(f"Resposta vazia. Digite um número de {minimo} a {maximo}.")
            continue
        if not texto.isdigit():
            print(f"Digite só o número da opção, de {minimo} a {maximo}.")
            continue
        numero = int(texto)
        if numero < minimo or numero > maximo:
            print(f"Opção fora da lista. Digite um número de {minimo} a {maximo}.")
            continue
        return numero


def ler_sim_nao(mensagem):
    """Pede 's' ou 'n' até a pessoa responder um dos dois. Devolve True para sim."""
    while True:
        texto = input(mensagem).strip().lower()
        if texto in ("s", "sim"):
            return True
        if texto in ("n", "nao", "não"):
            return False
        print("Responda com s (sim) ou n (não).")


def ler_json_lista(caminho):
    """Lê uma lista de um arquivo JSON. Arquivo ausente vira lista vazia.

    Arquivo corrompido é renomeado para .corrompido (para não perder nada) e vira lista vazia.
    """
    if not os.path.exists(caminho):
        return []
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if isinstance(dados, list):
            return dados
        raise ValueError("não é uma lista")
    except (json.JSONDecodeError, ValueError, OSError):
        reserva = caminho + ".corrompido"
        try:
            os.replace(caminho, reserva)
            print(f"Atenção: {caminho} estava corrompido. Guardei uma cópia em {reserva} e comecei um novo.")
        except OSError:
            print(f"Atenção: {caminho} estava corrompido e não consegui guardar uma cópia.")
        return []


def gravar_json(caminho, dados):
    """Grava os dados em JSON. Devolve False (sem travar) se não conseguir."""
    try:
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        return True
    except OSError as erro:
        print(f"Atenção: não consegui salvar {caminho} ({erro}).")
        return False


class Assistente:
    """Quem conversa com o cidadão. Tem uma BaseConhecimento (composição)."""

    def __init__(self, nome, base, pasta_dados="data"):
        self.nome = nome
        self.base = base
        self.caminho_historico = os.path.join(pasta_dados, "historico.json")
        self.caminho_avaliacoes = os.path.join(pasta_dados, "avaliacoes.json")
        self.caminho_csv = os.path.join(pasta_dados, "atendimentos.csv")
        self.historico = ler_json_lista(self.caminho_historico)    # lista de dicionários
        self.avaliacoes = ler_json_lista(self.caminho_avaliacoes)  # notas de facilidade (1 a 5)

    # ------------------------------------------------------------------ menu

    def iniciar(self):
        """Mostra o menu principal até a pessoa escolher sair."""
        print("=" * 60)
        print(f" {self.nome}")
        print(" Direitos e serviços para pessoas com deficiência em São Paulo")
        print("=" * 60)
        print(AVISO_OFICIAL)
        print("Privacidade: não digite nome, CPF, telefone ou e-mail. Não guardo quem você é.")

        while True:
            print()
            print("MENU PRINCIPAL")
            print("1 - Fazer uma pergunta")
            print("2 - Navegar por categorias")
            print("3 - Ver indicadores de atendimento")
            print("4 - Exportar atendimentos para CSV")
            print("5 - Sobre, fontes e limitações")
            print("6 - Posso pedir o Passe Livre Interestadual? (4 perguntas de sim ou não)")
            print("0 - Sair")
            opcao = ler_opcao("Escolha uma opção: ", 0, 6)
            if opcao == 1:
                self.perguntar()
            elif opcao == 2:
                self.navegar()
            elif opcao == 3:
                self.mostrar_indicadores()
            elif opcao == 4:
                self.exportar_csv()
            elif opcao == 5:
                self.sobre()
            elif opcao == 6:
                passe_livre.menu()  # módulo de Computer Science (não guarda as respostas)
            else:
                self.encerrar()
                return

    # ------------------------------------------------------- pergunta livre

    def perguntar(self):
        """Atendimento por pergunta em texto livre, usando a busca com pontuação."""
        print()
        print("Escreva sua dúvida com suas palavras. Exemplo: como peço o bilhete único especial?")
        inicio = time.time()
        tentativas = 0
        ultima_pergunta = ""

        while True:
            texto = input("Digite sua dúvida (0 para voltar): ").strip()

            if texto == "0":
                if tentativas > 0:  # desistiu sem achar: entra como dúvida sem solução
                    self.registrar("pergunta", ultima_pergunta, None, False, False,
                                   tentativas, round(time.time() - inicio, 1))
                return
            if texto == "":
                print("Você não escreveu nada. Digite sua dúvida ou 0 para voltar.")
                continue
            if contem_dado_pessoal(texto):
                print("Atenção: não digite CPF, telefone ou e-mail. Reescreva sem dados pessoais.")
                continue  # recusada: não conta tentativa e não é registrada

            tentativas += 1
            ultima_pergunta = texto
            resultados = self.base.buscar(texto)
            pontos = resultados[0][0] if resultados else 0
            nivel = confianca(pontos)

            if nivel is None:
                self.sugerir()
                continue

            tempo = round(time.time() - inicio, 1)
            melhor = resultados[0][1]
            print(f"\nConfiança da resposta: {nivel} ({pontos} pontos)")
            melhor.exibir()

            # até duas alternativas que também passaram do limite mínimo
            alternativas = [(p, o) for p, o in resultados[1:3] if confianca(p) is not None]
            escolhida = melhor
            ajudou = ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): ")
            if not ajudou and alternativas:
                print("Talvez seja uma destas:")
                for numero, (p, orientacao) in enumerate(alternativas, start=1):
                    print(f"{numero} - {orientacao.titulo} ({p} pontos)")
                print("0 - Nenhuma destas")
                opcao = ler_opcao("Escolha: ", 0, len(alternativas))
                if opcao > 0:
                    escolhida = alternativas[opcao - 1][1]
                    escolhida.exibir()
                    ajudou = ler_sim_nao("E essa, respondeu sua dúvida? (s/n): ")

            self.registrar("pergunta", texto, escolhida.id, True, ajudou, tentativas, tempo)

            # novo atendimento
            print("\nTem outra dúvida? Digite abaixo, ou 0 para voltar ao menu.")
            inicio = time.time()
            tentativas = 0
            ultima_pergunta = ""

    def sugerir(self):
        """Resposta de 'não encontrei': sugere outras palavras e as categorias."""
        print("\nNão encontrei uma orientação para isso na minha base.")
        print("Tente outras palavras, por exemplo: bilhete especial, passe livre, BPC, isenção do carro.")
        print("Categorias disponíveis: " + ", ".join(self.base.categorias()) + ".")
        print("Você também pode usar a opção 2 do menu para navegar por categorias.")
        print("Para assuntos fora da base, procure a Central 156 (Prefeitura de SP) ou o gov.br.\n")

    # ---------------------------------------------------- navegação por categoria

    def navegar(self):
        """Atendimento por escolhas: categoria -> orientação. Sempre com 0 para voltar."""
        while True:
            categorias = self.base.categorias()
            print("\nCATEGORIAS")
            for numero, categoria in enumerate(categorias, start=1):
                quantidade = len(self.base.por_categoria(categoria))
                print(f"{numero} - {categoria} ({quantidade})")
            print("0 - Voltar")
            opcao = ler_opcao("Escolha uma categoria: ", 0, len(categorias))
            if opcao == 0:
                return
            categoria = categorias[opcao - 1]
            self.navegar_categoria(categoria)

    def navegar_categoria(self, categoria):
        """Lista as orientações de uma categoria e mostra a escolhida."""
        inicio = time.time()
        while True:
            orientacoes = self.base.por_categoria(categoria)
            print(f"\n{categoria.upper()}")
            for numero, orientacao in enumerate(orientacoes, start=1):
                print(f"{numero} - {orientacao.titulo}")
            print("0 - Voltar")
            opcao = ler_opcao("Escolha uma orientação: ", 0, len(orientacoes))
            if opcao == 0:
                return
            escolhida = orientacoes[opcao - 1]
            tempo = round(time.time() - inicio, 1)
            escolhida.exibir()
            ajudou = ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("categoria", f"{categoria} > {escolhida.titulo}", escolhida.id,
                           True, ajudou, 1, tempo)
            inicio = time.time()

    # ------------------------------------------------- histórico e indicadores

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou, tentativas, tempo):
        """Guarda um atendimento no histórico (memória e data/historico.json)."""
        atendimento = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origem": origem,
            "pergunta": pergunta,
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_segundos": tempo,
        }
        self.historico.append(atendimento)
        gravar_json(self.caminho_historico, self.historico)
        return atendimento

    def indicadores(self):
        """Calcula os indicadores a partir do histórico e das notas. Devolve um dicionário."""
        total = len(self.historico)
        encontrados = [a for a in self.historico if a.get("encontrou")]
        ajudaram = [a for a in self.historico if a.get("ajudou")]
        notas = [a["nota"] for a in self.avaliacoes if isinstance(a, dict) and "nota" in a]

        sem_solucao = []
        for atendimento in self.historico:
            if not atendimento.get("ajudou") and atendimento.get("pergunta") not in sem_solucao:
                sem_solucao.append(atendimento.get("pergunta"))

        def media(valores):
            return round(sum(valores) / len(valores), 1) if valores else 0.0

        def porcentagem(parte):
            return round(100 * len(parte) / total, 1) if total else 0.0

        return {
            "total": total,
            "encontrada_pct": porcentagem(encontrados),
            "ajudou_pct": porcentagem(ajudaram),
            "tempo_medio": media([a.get("tempo_segundos", 0) for a in encontrados]),
            "tentativas_media": media([a.get("tentativas", 0) for a in self.historico]),
            "facilidade_media": media(notas),
            "avaliacoes": len(notas),
            "sem_solucao": sem_solucao,
        }

    def mostrar_indicadores(self):
        """Exibe os indicadores na tela."""
        dados = self.indicadores()
        print("\nINDICADORES DE ATENDIMENTO")
        if dados["total"] == 0:
            print("Ainda não há atendimentos registrados.")
            return
        print(f"Atendimentos registrados ....... {dados['total']}")
        print(f"Resposta encontrada ............ {dados['encontrada_pct']}%")
        print(f"Taxa de acerto (ajudou) ........ {dados['ajudou_pct']}%")
        print(f"Tempo médio para encontrar ..... {dados['tempo_medio']} s")
        print(f"Tentativas por atendimento ..... {dados['tentativas_media']}")
        if dados["avaliacoes"]:
            print(f"Facilidade de uso (1 a 5) ...... {dados['facilidade_media']} ({dados['avaliacoes']} notas)")
        else:
            print("Facilidade de uso (1 a 5) ...... sem notas ainda")
        print("Dúvidas sem solução:")
        if dados["sem_solucao"]:
            for pergunta in dados["sem_solucao"]:
                print(f"  - {pergunta}")
        else:
            print("  (nenhuma)")

    def exportar_csv(self):
        """Exporta o histórico para data/atendimentos.csv com csv.DictWriter."""
        try:
            with open(self.caminho_csv, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV, extrasaction="ignore")
                escritor.writeheader()
                for atendimento in self.historico:
                    escritor.writerow(atendimento)
        except OSError as erro:
            print(f"Não consegui exportar o CSV ({erro}). Se ele estiver aberto no Excel, feche e tente de novo.")
            return False
        print(f"{len(self.historico)} atendimento(s) exportado(s) para {self.caminho_csv}")
        return True

    # ------------------------------------------------------------- outros

    def sobre(self):
        """Explica o que o assistente faz, o que não faz e de onde vêm as informações."""
        print("\nSOBRE O ASSISTENTE")
        print("Protótipo de estudo da FIAP (Global Solution CitizenTech), parte do projeto Mapiii.")
        print("Responde só com o que está na base de conhecimento, conferida pela equipe.")
        print(AVISO_OFICIAL)
        print("Não vê seus pedidos, não decide se você tem direito e não substitui o órgão responsável.")
        print("Não pede nem guarda nome, CPF, telefone ou e-mail.")
        print("\nFontes consultadas:")
        for orientacao in self.base.orientacoes:
            print(f"  - {orientacao.titulo}: {orientacao.fonte} (verificado em {orientacao.verificado_em})")

    def encerrar(self):
        """Pede a nota de facilidade (1 a 5) e se despede."""
        print("\nAntes de sair: de 1 a 5, quão fácil foi usar o assistente?")
        print("(1 = muito difícil, 5 = muito fácil, 0 = prefiro não responder)")
        nota = ler_opcao("Sua nota: ", 0, 5)
        if nota > 0:
            self.avaliacoes.append({"data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "nota": nota})
            gravar_json(self.caminho_avaliacoes, self.avaliacoes)
        print("Obrigado! Lembre-se: confirme sempre nas fontes oficiais.")
