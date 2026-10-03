"""Roda o interval partitioning para cada dia, cenário e tempo de solo.

Cenários: horário previsto (ChegadaPrevista) e real (ChegadaReal).
Tempos de solo: 30, 45 e 60 minutos.

Saídas em results/:
  - portoes_por_dia.csv: nº de portões de cada dia em cada combinação;
  - resumo.csv: mínimo, média e máximo de portões por combinação, mais o
    relatório de voos descartados.
"""

import csv
from datetime import date
from pathlib import Path
from statistics import mean

from src.absioso import max_simultaneos, particionar
from src.carregar import intervalos_por_dia, ler_voos

PASTA_RESULTADOS = Path(__file__).resolve().parent.parent / "results"

CENARIOS = {"previsto": "ChegadaPrevista", "real": "ChegadaReal"}
TEMPOS_SOLO = [30, 45, 60]

# O VRA agrupa os voos pelo dia da partida, então o arquivo de março traz
# alguns pousos já em 01/04 (decolaram em 31/03). Esse dia está incompleto e
# fica de fora.
INICIO = date(2026, 1, 1)
FIM = date(2026, 3, 31)


def analisar(voos, campo, tempo_solo):
    """Resolve todos os dias de um cenário com um tempo de solo.

    Retorna (linhas, descartados, fora_periodo), com linhas = [(dia, voos,
    portões)] ordenadas por dia.
    """
    dias, descartados = intervalos_por_dia(voos, campo, tempo_solo)

    linhas = []
    fora_periodo = 0
    for dia in sorted(dias):
        intervalos = dias[dia]
        if not INICIO <= dia <= FIM:
            fora_periodo += len(intervalos)
            continue
        portoes, _ = particionar(intervalos)
        # Conferência: o guloso tem que bater com o limite inferior.
        assert portoes == max_simultaneos(intervalos), dia
        linhas.append((dia, len(intervalos), portoes))

    return linhas, descartados, fora_periodo


def main():
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    voos = ler_voos()
    print(f"{len(voos)} chegadas realizadas em SBBR lidas\n")

    por_dia = []
    resumo = []
    for cenario, campo in CENARIOS.items():
        for tempo_solo in TEMPOS_SOLO:
            linhas, descartados, fora = analisar(voos, campo, tempo_solo)
            for dia, n_voos, portoes in linhas:
                por_dia.append([dia.isoformat(), cenario, tempo_solo, n_voos, portoes])

            portoes = [p for _, _, p in linhas]
            dia_pico = max(linhas, key=lambda l: l[2])[0]
            resumo.append([
                cenario, tempo_solo, len(linhas), sum(n for _, n, _ in linhas),
                descartados, fora, min(portoes), round(mean(portoes), 2),
                max(portoes), dia_pico.isoformat(),
            ])

    with open(PASTA_RESULTADOS / "portoes_por_dia.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dia", "cenario", "tempo_solo", "voos", "portoes"])
        w.writerows(por_dia)

    cabecalho = ["cenario", "tempo_solo", "dias", "voos", "descartados",
                 "fora_periodo", "min", "media", "max", "dia_pico"]
    with open(PASTA_RESULTADOS / "resumo.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(resumo)

    # Tabela no terminal.
    print("  ".join(f"{c:>12}" for c in cabecalho))
    for linha in resumo:
        print("  ".join(f"{str(c):>12}" for c in linha))
    print(f"\nResultados salvos em {PASTA_RESULTADOS}/")


if __name__ == "__main__":
    main()
