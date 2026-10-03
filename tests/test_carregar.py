"""Testes da leitura e filtragem dos dados (src/carregar.py)."""

import json
from datetime import date, datetime

from src.carregar import intervalos_por_dia, ler_horario, ler_voos


def voo(numero, destino="SBBR", situacao="REALIZADO",
        prevista="2026-01-01 10:00:00", real="2026-01-01 10:05:00"):
    return {
        "ICAOEmpresaAérea": "TAM",
        "NúmeroVoo": numero,
        "ICAOAeródromoDestino": destino,
        "ChegadaPrevista": prevista,
        "ChegadaReal": real,
        "SituaçãoVoo": situacao,
    }


def test_ler_horario():
    assert ler_horario("2026-01-08 00:25:00") == datetime(2026, 1, 8, 0, 25)
    # Fração de segundo: usa só os 19 primeiros caracteres.
    assert ler_horario("2026-01-08 00:25:00.100000000") == datetime(2026, 1, 8, 0, 25)
    assert ler_horario(None) is None
    assert ler_horario("N/A") is None
    assert ler_horario("") is None
    assert ler_horario("lixo") is None


def test_ler_voos_filtra_destino_e_situacao(tmp_path):
    dados = [
        voo("1"),
        voo("2", destino="SBGR"),
        voo("3", situacao="CANCELADO"),
        voo("4"),
    ]
    arquivo = tmp_path / "vra.json"
    # Grava com BOM, como os arquivos da ANAC.
    arquivo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8-sig")

    voos = ler_voos([arquivo])

    assert [v["NúmeroVoo"] for v in voos] == ["1", "4"]


def test_intervalos_por_dia():
    voos = [
        voo("1", prevista="2026-01-01 10:00:00"),
        voo("2", prevista="2026-01-01 23:50:00"),  # passa da meia-noite
        voo("3", prevista="2026-01-02 08:00:00.100000000"),
        voo("4", prevista=None),
        voo("5", prevista="N/A"),
    ]

    dias, descartados = intervalos_por_dia(voos, "ChegadaPrevista", 45)

    assert descartados == 2
    assert sorted(dias) == [date(2026, 1, 1), date(2026, 1, 2)]
    # O voo das 23:50 fica no dia do pouso, mesmo terminando no dia seguinte.
    inicio, fim, id_voo = dias[date(2026, 1, 1)][1]
    assert inicio == datetime(2026, 1, 1, 23, 50)
    assert fim == datetime(2026, 1, 2, 0, 35)
    assert id_voo.startswith("TAM2")


def test_cada_cenario_descarta_so_os_seus():
    voos = [voo("1", prevista=None), voo("2")]

    _, desc_previsto = intervalos_por_dia(voos, "ChegadaPrevista", 45)
    dias_real, desc_real = intervalos_por_dia(voos, "ChegadaReal", 45)

    assert desc_previsto == 1
    assert desc_real == 0
    assert len(dias_real[date(2026, 1, 1)]) == 2


def test_ids_unicos_com_numero_repetido():
    voos = [voo("1"), voo("1")]
    dias, _ = intervalos_por_dia(voos, "ChegadaReal", 45)
    ids = [i for _, _, i in dias[date(2026, 1, 1)]]
    assert len(set(ids)) == 2
