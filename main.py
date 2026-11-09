"""Ponto de entrada: python main.py"""

import os
import sys

from assistente import Assistente
from base_conhecimento import BaseConhecimento

# Roda a partir de qualquer pasta: os caminhos são relativos a este arquivo
PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA, "data")


def main():
    # Garante acentos no terminal do Windows (na saída e na entrada redirecionada)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        if not sys.stdin.isatty():
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    base = BaseConhecimento(os.path.join(PASTA_DADOS, "base_conhecimento.json"))
    carregou = base.carregar()  # lê o JSON e cria os objetos Orientacao
    for erro in base.erros:
        print("Aviso:", erro)
    if not carregou:
        print("Não foi possível carregar a base de conhecimento. Confira o arquivo e tente de novo.")
        return

    assistente = Assistente("Mapiii no terminal (Citizen Assist AI)", base, PASTA_DADOS)
    try:
        assistente.iniciar()
    except (KeyboardInterrupt, EOFError):
        print("\nAtendimento encerrado. Até logo!")


if __name__ == "__main__":
    main()
