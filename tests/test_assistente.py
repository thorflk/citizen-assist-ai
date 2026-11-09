"""Testes automáticos. Rodar na pasta do projeto: python -m unittest discover tests"""

import csv
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA)

from assistente import Assistente, contem_dado_pessoal  # noqa: E402
from base_conhecimento import BaseConhecimento, confianca, normalizar  # noqa: E402

BASE_REAL = os.path.join(PASTA, "data", "base_conhecimento.json")


def nova_base(caminho=BASE_REAL):
    base = BaseConhecimento(caminho)
    base.carregar()
    return base


class TestNormalizar(unittest.TestCase):
    def test_acentos_pontuacao_minusculas(self):
        self.assertEqual(normalizar("Como faço o Cartão do SUS?"), " como faco o cartao do sus ")

    def test_espacos_extras(self):
        self.assertEqual(normalizar("  BPC,,  LOAS!! "), " bpc loas ")


class TestBase(unittest.TestCase):
    def test_base_real_tem_campos_e_regras_minimas(self):
        base = nova_base()
        self.assertEqual(base.erros, [])
        self.assertGreaterEqual(len(base.categorias()), 3)
        for orientacao in base.orientacoes:
            self.assertGreaterEqual(len(orientacao.palavras_chave), 3, orientacao.titulo)
            self.assertTrue(orientacao.fonte.startswith("https://"), orientacao.titulo)
            self.assertRegex(orientacao.verificado_em, r"^\d{4}-\d{2}-\d{2}$")

    def test_ids_unicos(self):
        ids = [o.id for o in nova_base().orientacoes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_json_ausente_nao_trava(self):
        base = BaseConhecimento("nao_existe.json")
        self.assertFalse(base.carregar())
        self.assertIn("não encontrado", base.erros[0])

    def test_json_corrompido_nao_trava(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("[{ isso não é json")
        try:
            base = BaseConhecimento(f.name)
            self.assertFalse(base.carregar())
            self.assertIn("corrompido", base.erros[0])
        finally:
            os.remove(f.name)

    def test_registro_incompleto_e_ignorado(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump([{"id": 1, "titulo": "sem campos"}], f)
        try:
            base = BaseConhecimento(f.name)
            self.assertFalse(base.carregar())
            self.assertIn("campos faltando", base.erros[0])
        finally:
            os.remove(f.name)


class TestBusca(unittest.TestCase):
    def setUp(self):
        self.base = nova_base()

    def test_buscar_devolve_tuplas_ordenadas(self):
        resultados = self.base.buscar("passe livre para viajar de graça para outro estado")
        self.assertIsInstance(resultados[0], tuple)
        pontos = [p for p, _ in resultados]
        self.assertEqual(pontos, sorted(pontos, reverse=True))
        self.assertIn("Passe Livre", resultados[0][1].titulo)

    def test_calculo_de_pontos(self):
        # "bpc" (+3) e "inss" (+3); nenhuma palavra de 4+ letras está no título
        bpc = self.base.buscar_id(4)
        self.assertEqual(self.base.pontuar("o inss negou o bpc", bpc), 6)

    def test_palavra_do_titulo_vale_um_ponto(self):
        bilhete = self.base.buscar_id(1)
        # "bilhete unico" (+3) + "bilhete" e "unico" no título (+1 +1)
        self.assertEqual(self.base.pontuar("bilhete único", bilhete), 5)

    def test_palavra_inteira(self):
        # "ipi" não pode casar dentro de outra palavra
        ipi = self.base.buscar_id(5)
        self.assertEqual(self.base.pontuar("municipio", ipi), 0)

    def test_niveis_de_confianca(self):
        self.assertEqual(confianca(7), "ALTA")
        self.assertEqual(confianca(6), "ALTA")
        self.assertEqual(confianca(5), "MÉDIA")
        self.assertEqual(confianca(3), "MÉDIA")
        self.assertIsNone(confianca(2))

    def test_nao_encontra(self):
        self.assertEqual(self.base.buscar("previsão do tempo amanhã"), [])

    def test_categorias(self):
        self.assertEqual(self.base.categorias(),
                         ["Transporte", "Benefícios", "Carro e direção", "Calçadas", "Canais da Prefeitura"])
        self.assertEqual(len(self.base.por_categoria("Transporte")), 5)

    def test_minimo_do_enunciado(self):
        self.assertGreaterEqual(len(self.base.orientacoes), 10)
        self.assertGreaterEqual(len(self.base.categorias()), 3)


class TestDadosPessoais(unittest.TestCase):
    def test_bloqueia(self):
        self.assertTrue(contem_dado_pessoal("meu cpf é 123.456.789-00"))
        self.assertTrue(contem_dado_pessoal("liga 11 98765-4321"))
        self.assertTrue(contem_dado_pessoal("fulano@email.com"))

    def test_permite(self):
        self.assertFalse(contem_dado_pessoal("lei 8.899 de 94"))  # 6 dígitos
        # limitação conhecida: "lei 8.899/1994" tem 8 dígitos e é recusada (regra do enunciado)
        self.assertFalse(contem_dado_pessoal("como peço o BPC?"))


class TestAtendimento(unittest.TestCase):
    """Simula a pessoa digitando no terminal."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.assistente = Assistente("Teste", nova_base(), self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def rodar(self, entradas):
        with mock.patch("builtins.input", side_effect=entradas), mock.patch("builtins.print"):
            self.assistente.iniciar()

    def test_fluxo_completo(self):
        self.rodar([
            "1",                                   # fazer pergunta
            "",                                    # vazio: não trava
            "meu cpf é 123.456.789-00",            # bloqueado, não registra
            "previsão do tempo",                   # não encontrou (tentativa 1)
            "como peço o bilhete único especial",  # encontrou (tentativa 2)
            "talvez",                              # s/n inválido: não trava
            "s",
            "0",
            "2", "abc", "9", "1", "2", "n", "0", "0",  # categoria Transporte > Atende+
            "4",                                   # exportar CSV
            "0", "5",                              # sair com nota 5
        ])
        historico = self.assistente.historico
        self.assertEqual(len(historico), 2)
        self.assertEqual(historico[0]["tentativas"], 2)
        self.assertTrue(historico[0]["encontrou"])
        self.assertEqual(historico[0]["id_orientacao"], 1)
        self.assertEqual(historico[1]["origem"], "categoria")
        self.assertFalse(historico[1]["ajudou"])
        self.assertNotIn("123", json.dumps(historico))  # dado pessoal nunca registrado

        with open(os.path.join(self.pasta, "historico.json"), encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)), 2)
        with open(os.path.join(self.pasta, "atendimentos.csv"), encoding="utf-8-sig") as f:
            linhas = list(csv.DictReader(f))
        self.assertEqual(len(linhas), 2)

        ind = self.assistente.indicadores()
        self.assertEqual(ind["encontrada_pct"], 100.0)
        self.assertEqual(ind["ajudou_pct"], 50.0)
        self.assertEqual(ind["facilidade_media"], 5.0)
        self.assertEqual(ind["tentativas_media"], 1.5)

    def test_desistir_registra_duvida_sem_solucao(self):
        self.rodar(["1", "previsão do tempo", "0", "0", "0"])
        ind = self.assistente.indicadores()
        self.assertEqual(ind["encontrada_pct"], 0.0)
        self.assertEqual(ind["sem_solucao"], ["previsão do tempo"])

    def test_alternativa(self):
        # "isenção" e "passe livre" -> mostra a melhor, depois oferece a outra
        self.rodar(["1", "isenção no carro ou passe livre", "n", "1", "s", "0", "0", "0"])
        self.assertTrue(self.assistente.historico[0]["ajudou"])

    def test_alternativas_aparecem_mesmo_quando_ajudou(self):
        # o enunciado pede a melhor orientação e até duas alternativas em toda resposta
        saida = []
        with mock.patch("builtins.input", side_effect=["1", "isenção no carro ou passe livre", "s",
                                                       "0", "0", "0"]), \
                mock.patch("builtins.print", side_effect=lambda *a, **k: saida.append(" ".join(map(str, a)))):
            self.assistente.iniciar()
        texto = "\n".join(saida)
        self.assertIn("Outras orientações que podem servir:", texto)
        self.assertIn("  1 - ", texto)
        self.assertTrue(self.assistente.historico[0]["ajudou"])

    def test_historico_corrompido_nao_trava(self):
        caminho = os.path.join(self.pasta, "historico.json")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("{quebrado")
        with mock.patch("builtins.print"):
            assistente = Assistente("Teste", nova_base(), self.pasta)
        self.assertEqual(assistente.historico, [])
        self.assertTrue(os.path.exists(caminho + ".corrompido"))


if __name__ == "__main__":
    unittest.main()
