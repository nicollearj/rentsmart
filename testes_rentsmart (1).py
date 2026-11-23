"""Testes das regras comerciais do RentSmart. Execute: python testes_rentsmart.py"""

import csv
import os
import tempfile
import unittest

from rentsmart import Apartamento, Casa, Estudio, Orcamento


class TestAluguel(unittest.TestCase):
    def test_apartamento_basico_com_criancas(self):
        self.assertEqual(Apartamento(1, False, True).calcular_aluguel(), 700.00)

    def test_apartamento_dois_quartos_garagem_sem_criancas(self):
        # (700 + 200 + 300) - 5% = 1140
        self.assertEqual(Apartamento(2, True, False).calcular_aluguel(), 1140.00)

    def test_apartamento_um_quarto_sem_criancas(self):
        self.assertEqual(Apartamento(1, False, False).calcular_aluguel(), 665.00)

    def test_casa_basica(self):
        self.assertEqual(Casa(1, False).calcular_aluguel(), 900.00)

    def test_casa_dois_quartos_com_garagem(self):
        self.assertEqual(Casa(2, True).calcular_aluguel(), 1450.00)

    def test_casa_nao_recebe_desconto_de_criancas(self):
        self.assertEqual(Casa(1, True).calcular_aluguel(), 1200.00)

    def test_estudio_sem_vagas(self):
        self.assertEqual(Estudio(0).calcular_aluguel(), 1200.00)

    def test_estudio_pacote_de_duas_vagas(self):
        self.assertEqual(Estudio(2).calcular_aluguel(), 1450.00)

    def test_estudio_com_vagas_adicionais(self):
        # 1200 + 250 + 3 * 60 = 1630
        self.assertEqual(Estudio(5).calcular_aluguel(), 1630.00)


class TestOrcamento(unittest.TestCase):
    def test_parcelas_somam_a_taxa(self):
        for n in range(1, 6):
            valores = Orcamento(Casa(1, False), n).valores_parcelas()
            self.assertEqual(len(valores), n)
            self.assertEqual(round(sum(valores), 2), 2000.00)

    def test_projecao_tem_12_meses(self):
        linhas = Orcamento(Casa(1, False), 3).projecao_mensal()
        self.assertEqual(len(linhas), 12)
        self.assertEqual(linhas[2][2], 666.66)  # última parcela ajustada
        self.assertEqual(linhas[3][2], 0.0)     # sem parcela após a 3ª

    def test_csv_gerado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "teste.csv")
            Orcamento(Estudio(2), 2).gerar_csv(caminho)
            with open(caminho, encoding="utf-8-sig") as arquivo:
                linhas = list(csv.reader(arquivo, delimiter=";"))
        self.assertEqual(len(linhas), 14)  # cabeçalho + 12 meses + total
        self.assertEqual(linhas[1][3], "2450,00")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
