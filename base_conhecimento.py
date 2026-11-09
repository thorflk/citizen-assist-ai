"""Classe BaseConhecimento: lê o JSON, lista categorias e busca a melhor orientação."""

import json

from orientacao import Orientacao

# Pesos e limites da busca (explicados no README)
PONTOS_PALAVRA_CHAVE = 3   # palavra-chave da orientação que aparece na pergunta
PONTOS_TITULO = 1          # palavra da pergunta (4 letras ou mais) que aparece no título
TAMANHO_MINIMO_PALAVRA = 4
LIMITE_ALTA = 6            # 6 pontos ou mais: confiança ALTA
LIMITE_MEDIA = 3           # 3 a 5 pontos: confiança MÉDIA; abaixo disso: "não encontrei"

ACENTOS = {
    "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "ç": "c",
}

SINAIS = "?!.,;:()\"'/-"


def normalizar(texto):
    """Deixa o texto em minúsculas, sem acentos e sem pontuação.

    Devolve com um espaço no começo e no fim, para comparar palavras inteiras:
    " sus " está em " cartao do sus ", mas não em " susto ".
    """
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in SINAIS:
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


def confianca(pontos):
    """Traduz a pontuação em nível de confiança: 'ALTA', 'MÉDIA' ou None (não encontrou)."""
    if pontos >= LIMITE_ALTA:
        return "ALTA"
    if pontos >= LIMITE_MEDIA:
        return "MÉDIA"
    return None


class BaseConhecimento:
    """O conjunto de todas as orientações, lido de um arquivo JSON."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []  # lista de objetos Orientacao (composição)
        self.erros = []        # problemas encontrados ao carregar, para mostrar ao usuário

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao. Nunca trava o programa.

        Devolve True se carregou pelo menos uma orientação.
        """
        self.orientacoes = []
        self.erros = []
        try:
            with open(self.caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            self.erros.append(f"Arquivo não encontrado: {self.caminho}")
            return False
        except json.JSONDecodeError as erro:
            self.erros.append(f"JSON corrompido em {self.caminho} (linha {erro.lineno})")
            return False
        except OSError as erro:
            self.erros.append(f"Não consegui ler {self.caminho}: {erro}")
            return False

        if not isinstance(dados, list):
            self.erros.append("A base precisa ser uma lista de orientações.")
            return False

        for posicao, registro in enumerate(dados, start=1):
            if not isinstance(registro, dict):
                self.erros.append(f"Registro {posicao} ignorado: não é um dicionário.")
                continue
            try:
                self.orientacoes.append(Orientacao.de_dicionario(registro))
            except ValueError as erro:
                self.erros.append(f"Registro {posicao} ignorado: {erro}.")
        return len(self.orientacoes) > 0

    def categorias(self):
        """Lista as categorias sem repetir, na ordem em que aparecem no JSON."""
        lista = []
        for orientacao in self.orientacoes:
            if orientacao.categoria not in lista:
                lista.append(orientacao.categoria)
        return lista

    def por_categoria(self, categoria):
        """Devolve as orientações de uma categoria."""
        return [o for o in self.orientacoes if o.categoria == categoria]

    def buscar_id(self, id_orientacao):
        """Devolve a orientação com esse id, ou None."""
        for orientacao in self.orientacoes:
            if orientacao.id == id_orientacao:
                return orientacao
        return None

    def pontuar(self, pergunta, orientacao):
        """Calcula os pontos de uma orientação para uma pergunta.

        +3 para cada palavra-chave que aparece na pergunta;
        +1 para cada palavra da pergunta (4 letras ou mais) que aparece no título.
        """
        pergunta_norm = normalizar(pergunta)
        pontos = 0
        for chave in orientacao.palavras_chave:
            if normalizar(chave) in pergunta_norm:
                pontos += PONTOS_PALAVRA_CHAVE

        palavras_titulo = set(normalizar(orientacao.titulo).split())
        palavras_pergunta = set(pergunta_norm.split())  # set: cada palavra conta uma vez
        for palavra in palavras_pergunta:
            if len(palavra) >= TAMANHO_MINIMO_PALAVRA and palavra in palavras_titulo:
                pontos += PONTOS_TITULO
        return pontos

    def buscar(self, pergunta):
        """Devolve uma lista de tuplas (pontos, orientacao), da maior para a menor pontuação.

        Orientações com 0 pontos ficam de fora. Em empate, vale a ordem do JSON.
        """
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: tupla[0], reverse=True)
        return resultados
