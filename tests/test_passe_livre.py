"""Testes do módulo de Computer Science. Rodar: python -m unittest tests.test_passe_livre"""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA)

import passe_livre as pl  # noqa: E402


def silencioso(funcao, *args):
    """Roda a função sem imprimir na tela e devolve (resultado, texto impresso)."""
    saida = io.StringIO()
    with redirect_stdout(saida):
        resultado = funcao(*args)
    return resultado, saida.getvalue()


class TestEquivalencia(unittest.TestCase):
    def test_16_combinacoes_iguais_nas_4_representacoes(self):
        combinacoes = list(pl.combinacoes())
        self.assertEqual(len(combinacoes), 16)
        for linha, entradas in combinacoes:
            esperado = pl.TABELA_VERDADE[entradas]
            with self.subTest(linha=linha, entradas=entradas):
                self.assertEqual(pl.regra_original(*entradas), esperado)
                self.assertEqual(pl.expressao_canonica(*entradas), esperado)
                self.assertEqual(pl.expressao_simplificada(*entradas), esperado)
                self.assertEqual(pl.avaliar(*entradas), esperado)
                self.assertEqual(pl.negacao_de_morgan(*entradas), 1 - esperado)

    def test_mintermos_sao_as_linhas_com_s_igual_a_1(self):
        linhas_com_1 = tuple(linha for linha, e in pl.combinacoes() if pl.TABELA_VERDADE[e] == 1)
        self.assertEqual(linhas_com_1, pl.MINTERMOS)

    def test_validar_nao_acha_diferenca(self):
        erros, texto = silencioso(pl.validar)
        self.assertEqual(erros, [])
        self.assertIn("16 combinações", texto)


class TestEntradas(unittest.TestCase):
    def test_avaliar_recusa_valor_que_nao_e_0_ou_1(self):
        with self.assertRaises(ValueError):
            pl.avaliar(2, 0, 0, 0)

    def test_respostas_invalidas_repetem_a_pergunta(self):
        with mock.patch("builtins.input", side_effect=["", "talvez", "5", "SIM"]):
            valor, texto = silencioso(pl.ler_resposta, "Pergunta?")
        self.assertEqual(valor, 1)
        self.assertIn("Resposta vazia", texto)
        self.assertIn('"talvez" não é uma resposta válida', texto)

    def test_aceita_nao_com_e_sem_acento_e_zero(self):
        for resposta in ("n", "nao", "não", "0", " N "):
            with mock.patch("builtins.input", return_value=resposta):
                valor, _ = silencioso(pl.ler_resposta, "Pergunta?")
            self.assertEqual(valor, 0, resposta)

    def test_menu_opcao_invalida_nao_encerra(self):
        with mock.patch("builtins.input", side_effect=["9", "abc", "", "0"]):
            _, texto = silencioso(pl.menu)
        self.assertIn('"9" não é uma opção', texto)
        self.assertIn("Resposta vazia", texto)


class TestOrientacao(unittest.TestCase):
    def consultar(self, respostas):
        with mock.patch("builtins.input", side_effect=respostas):
            return silencioso(pl.consultar)

    def test_quem_recebe_bpc_pode_pedir(self):
        s, texto = self.consultar(["s", "n", "n", "n"])
        self.assertEqual(s, 1)
        self.assertIn("pode pedir", texto)
        self.assertIn("recebe o BPC", texto)

    def test_cadunico_e_atestado_pode_pedir(self):
        s, texto = self.consultar(["n", "s", "n", "s"])
        self.assertEqual(s, 1)
        self.assertIn("tem o atestado registrado", texto)

    def test_sem_bpc_e_sem_cadunico_explica_o_que_falta(self):
        s, texto = self.consultar(["n", "n", "s", "s"])
        self.assertEqual(s, 0)
        self.assertIn("não está no CadÚnico", texto)

    def test_so_cadunico_explica_que_falta_inclusao_ou_atestado(self):
        s, texto = self.consultar(["n", "s", "n", "n"])
        self.assertEqual(s, 0)
        self.assertIn("Cadastro-Inclusão", texto)
        self.assertIn("atestado", texto)

    def test_toda_resposta_tem_fonte_data_e_aviso(self):
        for respostas in (["s", "s", "s", "s"], ["n", "n", "n", "n"]):
            _, texto = self.consultar(respostas)
            self.assertIn(pl.FONTE, texto)
            self.assertIn(pl.VERIFICADO_EM, texto)
            self.assertIn("NÃO é um canal oficial", texto)

    def test_o_que_falta_so_quando_s_e_zero(self):
        for _, entradas in pl.combinacoes():
            tem_explicacao = bool(pl.o_que_falta(*entradas))
            self.assertEqual(tem_explicacao, pl.avaliar(*entradas) == 0, entradas)


if __name__ == "__main__":
    unittest.main()
