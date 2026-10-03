"""Testes da análise por dia (src/analise.py)."""

from datetime import date

from src.analise import analisar


def voo(numero, real):
    return {
        "ICAOEmpresaAérea": "TAM",
        "NúmeroVoo": numero,
        "ICAOAeródromoDestino": "SBBR",
        "ChegadaPrevista": None,
        "ChegadaReal": real,
        "SituaçãoVoo": "REALIZADO",
    }


def test_analisar_conta_portoes_e_ignora_fora_do_periodo():
    voos = [
        voo("1", "2026-01-01 10:00:00"),
        voo("2", "2026-01-01 10:20:00"),  # sobrepõe o 1 -> 2 portões
        voo("3", "2026-01-01 10:45:00"),  # reaproveita o portão do 1
        voo("4", "2026-03-31 12:00:00"),
        voo("5", "2026-04-01 00:30:00"),  # dia incompleto, fica de fora
    ]

    linhas, descartados, fora = analisar(voos, "ChegadaReal", 45)

    assert linhas == [(date(2026, 1, 1), 3, 2), (date(2026, 3, 31), 1, 1)]
    assert descartados == 0
    assert fora == 1


def test_analisar_conta_descartados():
    voos = [voo("1", "2026-01-01 10:00:00")]

    linhas, descartados, _ = analisar(voos, "ChegadaPrevista", 45)

    assert linhas == []
    assert descartados == 1
