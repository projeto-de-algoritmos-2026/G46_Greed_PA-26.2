"""Leitura dos dados VRA da ANAC e geração dos intervalos de ocupação por dia.

Cada chegada em SBBR ocupa um portão por um tempo de solo fixo a partir do
pouso: intervalo semiaberto [pouso, pouso + solo). O dia do voo é o dia do
pouso.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
ARQUIVOS = ["VRA_20261.json", "VRA_20262.json", "VRA_20263.json"]

AEROPORTO = "SBBR"
FORMATO = "%Y-%m-%d %H:%M:%S"


def ler_voos(arquivos=None):
    """Lê os JSON e devolve só os voos REALIZADOS com destino SBBR.

    Os arquivos vêm com BOM, por isso o encoding "utf-8-sig".
    """
    if arquivos is None:
        arquivos = [PASTA_DADOS / nome for nome in ARQUIVOS]

    voos = []
    for caminho in arquivos:
        with open(caminho, encoding="utf-8-sig") as f:
            for voo in json.load(f):
                if (voo.get("ICAOAeródromoDestino") == AEROPORTO
                        and voo.get("SituaçãoVoo") == "REALIZADO"):
                    voos.append(voo)
    return voos


def ler_horario(texto):
    """Converte "AAAA-MM-DD HH:MM:SS" em datetime; None se for inválido.

    Alguns horários têm fração de segundo ("... 00:25:00.100000000"); nesses
    casos usamos só os 19 primeiros caracteres.
    """
    if not isinstance(texto, str):
        return None  # null no JSON
    try:
        return datetime.strptime(texto[:19], FORMATO)
    except ValueError:
        return None  # "N/A" ou qualquer formato inesperado


def intervalos_por_dia(voos, campo, tempo_solo):
    """Gera os intervalos de ocupação de portão, agrupados pelo dia do pouso.

    campo: "ChegadaPrevista" ou "ChegadaReal".
    tempo_solo: minutos que cada voo fica no portão.

    Retorna (dias, descartados):
      dias = {date: [(inicio, fim, id_voo), ...]}
      descartados = nº de voos sem horário válido nesse campo.
    """
    solo = timedelta(minutes=tempo_solo)
    dias = {}
    descartados = 0

    for i, voo in enumerate(voos):
        pouso = ler_horario(voo.get(campo))
        if pouso is None:
            descartados += 1
            continue
        # O mesmo número de voo pode aparecer mais de uma vez; o índice
        # garante um id único (e igual nos dois cenários).
        id_voo = f"{voo['ICAOEmpresaAérea']}{voo['NúmeroVoo']}#{i}"
        dias.setdefault(pouso.date(), []).append((pouso, pouso + solo, id_voo))

    return dias, descartados
