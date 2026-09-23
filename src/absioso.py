"""Interval partitioning guloso: número mínimo de portões para um dia de voos.

Cada intervalo é uma tupla (inicio, fim, id_voo), semiaberta [inicio, fim):
um portão que libera às 10:00 pode receber um voo que pousa às 10:00.
inicio e fim podem ser qualquer coisa comparável (datetime, minutos, ...).
"""

import heapq


def particionar(intervalos):
    """Aloca cada voo em um portão usando o mínimo de portões.

    Estratégia gulosa:
      1. ordena os voos pelo horário de início (pouso);
      2. mantém um heap com (fim, portão) dos portões ocupados, de modo que o
         topo é sempre o portão que libera mais cedo;
      3. para cada voo, se o portão do topo já liberou, reaproveita esse
         portão; senão, nenhum outro liberou também, então abre um novo.

    Complexidade: O(n log n) (ordenação + operações no heap).

    Retorna (num_portoes, alocacao), com alocacao = {id_voo: portão},
    portões numerados a partir de 1.
    """
    ocupados = []  # heap de (fim, portão)
    alocacao = {}
    num_portoes = 0

    for inicio, fim, id_voo in sorted(intervalos, key=lambda x: x[0]):
        if ocupados and ocupados[0][0] <= inicio:
            # O portão que libera mais cedo já está livre: reaproveita.
            _, portao = ocupados[0]
            heapq.heapreplace(ocupados, (fim, portao))
        else:
            # Todos os portões estão ocupados neste instante: abre um novo.
            num_portoes += 1
            portao = num_portoes
            heapq.heappush(ocupados, (fim, portao))
        alocacao[id_voo] = portao

    return num_portoes, alocacao


def max_simultaneos(intervalos):
    """Maior número de intervalos ativos ao mesmo tempo (varredura de eventos).

    É o limite inferior para qualquer solução: se k voos estão em solo ao mesmo
    tempo, são necessários pelo menos k portões. Serve para conferir o guloso.

    Cada voo gera um evento +1 no início e -1 no fim. Em empate de horário o
    -1 vem antes (intervalo semiaberto), por isso a ordenação por (tempo, delta).
    """
    eventos = []
    for inicio, fim, _ in intervalos:
        eventos.append((inicio, +1))
        eventos.append((fim, -1))
    eventos.sort()

    ativos = 0
    maximo = 0
    for _, delta in eventos:
        ativos += delta
        maximo = max(maximo, ativos)
    return maximo
