"""
RentSmart - Sistema de orçamento de locação da R.M Imóveis.

O programa recebe as características da locação, aplica as regras comerciais
da imobiliária, mostra um resumo detalhado do orçamento e gera um arquivo CSV
com a projeção dos 12 primeiros meses de contrato.

Estrutura (Programação Orientada a Objetos):
    Imovel                  -> classe base (regras comuns a todo imóvel)
    ImovelResidencial       -> quartos e garagem (comum a casa e apartamento)
    Apartamento / Casa      -> valores e regras próprios de cada tipo
    Estudio                 -> regra de estacionamento por pacote de vagas
    Orcamento               -> taxa contratual, parcelas, resumo e CSV
"""

import csv

TAXA_CONTRATUAL = 2000.00
PARCELAS_MAXIMAS = 5
MESES_PROJECAO = 12
ARQUIVO_CSV = "projecao_12_meses.csv"


def formatar_moeda(valor):
    """Formata um número no padrão brasileiro: R$ 1.140,00."""
    texto = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sinal = "-" if valor < 0 else ""
    return f"{sinal}R$ {texto}"


def numero_csv(valor):
    """Número com 2 casas e vírgula decimal, para o Excel em português abrir certo."""
    return f"{valor:.2f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Imóveis
# ---------------------------------------------------------------------------
class Imovel:
    """Classe base: todo imóvel tem um aluguel-base e uma lista de itens.

    O aluguel mensal é sempre a soma dos itens devolvidos por
    detalhar_aluguel(). Cada subclasse acrescenta os seus próprios itens,
    então o cálculo e o detalhamento do orçamento usam a mesma fonte.
    """

    nome = "imóvel"
    rotulo_base = "Aluguel-base"
    aluguel_base = 0.0

    def detalhar_aluguel(self):
        """Devolve a composição do aluguel: lista de (descrição, valor)."""
        return [(self.rotulo_base, self.aluguel_base)]

    def calcular_aluguel(self):
        return round(sum(valor for _, valor in self.detalhar_aluguel()), 2)

    def descrever(self):
        """Características informadas pelo cliente: lista de (rótulo, texto)."""
        return []


class ImovelResidencial(Imovel):
    """Comportamento comum de casas e apartamentos: quartos e garagem."""

    adicional_dois_quartos = 0.0
    valor_garagem = 300.0

    def __init__(self, quartos, garagem):
        self.quartos = quartos
        self.garagem = garagem

    def detalhar_aluguel(self):
        itens = super().detalhar_aluguel()
        if self.quartos == 2:
            itens.append(("Adicional de 2 quartos", self.adicional_dois_quartos))
        if self.garagem:
            itens.append(("Vaga de garagem", self.valor_garagem))
        return itens

    def descrever(self):
        return [
            ("Quartos", str(self.quartos)),
            ("Garagem", "Sim" if self.garagem else "Não"),
        ]


class Apartamento(ImovelResidencial):
    nome = "apartamento"
    rotulo_base = "Aluguel-base (apartamento de 1 quarto)"
    aluguel_base = 700.00
    adicional_dois_quartos = 200.00
    desconto_sem_criancas = 0.05

    def __init__(self, quartos, garagem, criancas):
        super().__init__(quartos, garagem)
        self.criancas = criancas

    def detalhar_aluguel(self):
        itens = super().detalhar_aluguel()
        if not self.criancas:
            # O desconto incide sobre o valor já acrescido dos adicionais.
            subtotal = sum(valor for _, valor in itens)
            desconto = round(subtotal * self.desconto_sem_criancas, 2)
            rotulo = f"Desconto de {self.desconto_sem_criancas:.0%} (sem crianças)"
            itens.append((rotulo, -desconto))
        return itens

    def descrever(self):
        return super().descrever() + [
            ("Possui crianças", "Sim" if self.criancas else "Não")
        ]


class Casa(ImovelResidencial):
    nome = "casa"
    rotulo_base = "Aluguel-base (casa de 1 quarto)"
    aluguel_base = 900.00
    adicional_dois_quartos = 250.00


class Estudio(Imovel):
    nome = "estúdio"
    rotulo_base = "Aluguel-base (estúdio)"
    aluguel_base = 1200.00
    vagas_do_pacote = 2
    valor_pacote = 250.00
    valor_vaga_extra = 60.00

    def __init__(self, vagas):
        self.vagas = vagas

    def detalhar_aluguel(self):
        itens = super().detalhar_aluguel()
        if self.vagas >= self.vagas_do_pacote:
            itens.append((f"Pacote de {self.vagas_do_pacote} vagas", self.valor_pacote))
            extras = self.vagas - self.vagas_do_pacote
            if extras > 0:
                rotulo = f"{extras} vaga(s) adicional(is) x {formatar_moeda(self.valor_vaga_extra)}"
                itens.append((rotulo, extras * self.valor_vaga_extra))
        return itens

    def descrever(self):
        return [("Vagas de estacionamento", str(self.vagas))]


# ---------------------------------------------------------------------------
# Orçamento
# ---------------------------------------------------------------------------
class Orcamento:
    """Une um imóvel à taxa contratual parcelada e produz as saídas."""

    def __init__(self, imovel, parcelas, taxa=TAXA_CONTRATUAL):
        self.imovel = imovel
        self.parcelas = parcelas
        self.taxa = taxa

    def valores_parcelas(self):
        """Divide a taxa em parcelas; a última absorve o arredondamento."""
        valor = round(self.taxa / self.parcelas, 2)
        valores = [valor] * self.parcelas
        valores[-1] = round(self.taxa - valor * (self.parcelas - 1), 2)
        return valores

    def projecao_mensal(self):
        """Lista de (mês, aluguel, parcela do contrato, total do mês)."""
        aluguel = self.imovel.calcular_aluguel()
        parcelas = self.valores_parcelas()
        linhas = []
        for mes in range(1, MESES_PROJECAO + 1):
            parcela = parcelas[mes - 1] if mes <= len(parcelas) else 0.0
            linhas.append((mes, aluguel, parcela, round(aluguel + parcela, 2)))
        return linhas

    def _texto_parcelamento(self):
        valores = self.valores_parcelas()
        if valores[0] == valores[-1]:
            return f"{len(valores)}x de {formatar_moeda(valores[0])}"
        return (
            f"{len(valores) - 1}x de {formatar_moeda(valores[0])} "
            f"+ 1x de {formatar_moeda(valores[-1])} (ajuste de arredondamento)"
        )

    def mostrar_resumo(self):
        print("\n========== RESUMO DO ORÇAMENTO ==========")
        print(f"Imóvel: {self.imovel.nome.capitalize()}")
        for rotulo, texto in self.imovel.descrever():
            print(f"{rotulo}: {texto}")

        print("\n--- Composição do aluguel mensal ---")
        for descricao, valor in self.imovel.detalhar_aluguel():
            print(f"  {descricao:<42}{formatar_moeda(valor):>14}")
        print(f"  {'ALUGUEL MENSAL':<42}{formatar_moeda(self.imovel.calcular_aluguel()):>14}")

        print("\n--- Taxa contratual (cobrada à parte do aluguel) ---")
        print(f"  Valor total da taxa: {formatar_moeda(self.taxa)}")
        print(f"  Parcelamento: {self._texto_parcelamento()}")

        total_ano = sum(linha[3] for linha in self.projecao_mensal())
        print(f"\nTotal previsto nos {MESES_PROJECAO} primeiros meses: {formatar_moeda(total_ano)}")

    def gerar_csv(self, caminho=ARQUIVO_CSV):
        """Grava a projeção em CSV no padrão brasileiro (separador ; e decimal com vírgula)."""
        linhas = self.projecao_mensal()
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(
                ["Mês", "Aluguel (R$)", "Parcela do contrato (R$)", "Total do mês (R$)"]
            )
            for mes, aluguel, parcela, total in linhas:
                escritor.writerow([mes, numero_csv(aluguel), numero_csv(parcela), numero_csv(total)])
            escritor.writerow([
                "Total",
                numero_csv(sum(l[1] for l in linhas)),
                numero_csv(sum(l[2] for l in linhas)),
                numero_csv(sum(l[3] for l in linhas)),
            ])
        return caminho


# ---------------------------------------------------------------------------
# Entrada de dados com validação
# ---------------------------------------------------------------------------
def ler_inteiro(mensagem, validos):
    """Repete a pergunta até o usuário digitar um número entre os válidos."""
    while True:
        texto = input(mensagem).strip()
        try:
            numero = int(texto)
        except ValueError:
            print("Entrada inválida: digite apenas números.")
            continue
        if numero in validos:
            return numero
        print("Opção inválida. Tente novamente.")


def ler_sim_nao(mensagem):
    """Repete a pergunta até receber sim/não; devolve True ou False."""
    while True:
        texto = input(mensagem).strip().lower()
        if texto in ("sim", "s"):
            return True
        if texto in ("nao", "não", "n"):
            return False
        print("Digite sim ou não.")


def criar_imovel():
    """Pergunta o tipo e as características e devolve o objeto correto."""
    print("1 - Apartamento")
    print("2 - Casa")
    print("3 - Estúdio")
    tipo = ler_inteiro("Escolha o tipo de imóvel (1, 2 ou 3): ", (1, 2, 3))

    if tipo == 3:
        vagas_validas = [0] + list(range(2, 11))
        vagas = ler_inteiro(
            "Vagas de estacionamento (0 para nenhuma, ou de 2 a 10): ", vagas_validas
        )
        return Estudio(vagas)

    quartos = ler_inteiro("Número de quartos (1 ou 2): ", (1, 2))
    garagem = ler_sim_nao("Deseja vaga de garagem? (sim/não): ")
    if tipo == 1:
        criancas = ler_sim_nao("Possui crianças? (sim/não): ")
        return Apartamento(quartos, garagem, criancas)
    return Casa(quartos, garagem)


def main():
    print("=== RentSmart - Orçamento de locação | R.M Imóveis ===")
    imovel = criar_imovel()
    parcelas = ler_inteiro(
        f"Parcelas da taxa contratual (1 a {PARCELAS_MAXIMAS}): ",
        range(1, PARCELAS_MAXIMAS + 1),
    )

    orcamento = Orcamento(imovel, parcelas)
    orcamento.mostrar_resumo()
    caminho = orcamento.gerar_csv()
    print(f"\nArquivo '{caminho}' gerado com a projeção dos {MESES_PROJECAO} meses.")


if __name__ == "__main__":
    main()
