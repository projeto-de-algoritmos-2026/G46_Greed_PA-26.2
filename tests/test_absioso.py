"""Testes do interval partitioning guloso (src/absioso.py)."""

import random
from datetime import datetime, timedelta

import pytest

from src.absioso import max_simultaneos, particionar


def conferir_alocacao(intervalos, num_portoes, alocacao):
    """Verifica que a alocação é válida.

    - todo voo recebeu um portão entre 1 e num_portoes;
    - nenhum portão tem dois voos sobrepostos.
    """
    assert set(alocacao) == {id_voo for _, _, id_voo in intervalos}
    assert all(1 <= p <= num_portoes for p in alocacao.values())

    # Agrupa os intervalos por portão e confere que não se sobrepõem.
    por_portao = {}
    for inicio, fim, id_voo in intervalos:
        por_portao.setdefault(alocacao[id_voo], []).append((inicio, fim))
    for lista in por_portao.values():
        lista.sort()
        for (_, fim_anterior), (inicio, _) in zip(lista, lista[1:]):
            assert fim_anterior <= inicio  # semiaberto: encostar pode


# ---------------------------------------------------------------------------
# Casos pequenos feitos à mão: (intervalos, portões esperados)
# ---------------------------------------------------------------------------

CASOS = {
    "vazio": ([], 0),
    "um_voo": ([(0, 45, "A")], 1),
    "disjuntos": ([(0, 10, "A"), (20, 30, "B"), (40, 50, "C")], 1),
    "todos_sobrepostos": ([(0, 50, "A"), (10, 60, "B"), (20, 70, "C"), (30, 80, "D")], 4),
    # Fim de um == início do outro: o portão pode ser reaproveitado.
    "encostados": ([(0, 45, "A"), (45, 90, "B"), (90, 135, "C")], 1),
    "mesmo_horario": ([(10, 55, "A"), (10, 55, "B"), (10, 55, "C")], 3),
    # Um voo longo com dois curtos dentro, um depois do outro.
    "aninhados": ([(0, 100, "A"), (10, 20, "B"), (30, 40, "C")], 2),
    # Exemplo misto: em t=50 estão B, C e D ao mesmo tempo.
    "misto": ([(0, 45, "A"), (10, 55, "B"), (45, 90, "C"), (50, 95, "D"), (100, 145, "E")], 3),
    # Mesma coisa do misto, mas fora de ordem: o algoritmo tem que ordenar.
    "fora_de_ordem": ([(100, 145, "E"), (50, 95, "D"), (0, 45, "A"), (45, 90, "C"), (10, 55, "B")], 3),
}


@pytest.mark.parametrize("nome", CASOS)
def test_casos_a_mao(nome):
    intervalos, esperado = CASOS[nome]
    num_portoes, alocacao = particionar(intervalos)

    assert num_portoes == esperado
    assert max_simultaneos(intervalos) == esperado
    conferir_alocacao(intervalos, num_portoes, alocacao)


def test_alocacao_reaproveita_portao_liberado():
    # A libera às 45 e C pousa às 45: C deve ir para o portão de A.
    _, alocacao = particionar([(0, 45, "A"), (10, 55, "B"), (45, 90, "C")])
    assert alocacao["C"] == alocacao["A"]
    assert alocacao["B"] != alocacao["A"]


def test_funciona_com_datetime():
    # Os dados reais usam datetime, não inteiros.
    base = datetime(2026, 1, 1, 10, 0)
    solo = timedelta(minutes=45)
    pousos = [base, base + timedelta(minutes=20), base + timedelta(minutes=45)]
    intervalos = [(p, p + solo, f"V{i}") for i, p in enumerate(pousos)]

    num_portoes, alocacao = particionar(intervalos)

    assert num_portoes == 2
    conferir_alocacao(intervalos, num_portoes, alocacao)


# ---------------------------------------------------------------------------
# Evidência empírica de otimalidade: guloso == máximo de simultâneos
# ---------------------------------------------------------------------------

def gerar_aleatorios(rng, duracao_fixa=None):
    """Gera um dia aleatório de voos em minutos (0 a 1440).

    Com duracao_fixa imita o modelo real (tempo de solo fixo); sem ela, cada
    voo tem uma duração qualquer. Pousos em minutos inteiros para forçar
    empates, que são os casos mais delicados.
    """
    n = rng.randint(0, 200)
    intervalos = []
    for i in range(n):
        inicio = rng.randint(0, 1440)
        duracao = duracao_fixa or rng.randint(1, 180)
        intervalos.append((inicio, inicio + duracao, i))
    return intervalos


@pytest.mark.parametrize("semente", range(500))
def test_guloso_igual_max_simultaneos_duracao_variavel(semente):
    rng = random.Random(semente)
    intervalos = gerar_aleatorios(rng)

    num_portoes, alocacao = particionar(intervalos)

    assert num_portoes == max_simultaneos(intervalos)
    conferir_alocacao(intervalos, num_portoes, alocacao)


@pytest.mark.parametrize("tempo_solo", [30, 45, 60])
@pytest.mark.parametrize("semente", range(100))
def test_guloso_igual_max_simultaneos_tempo_solo_fixo(semente, tempo_solo):
    rng = random.Random(semente)
    intervalos = gerar_aleatorios(rng, duracao_fixa=tempo_solo)

    num_portoes, alocacao = particionar(intervalos)

    assert num_portoes == max_simultaneos(intervalos)
    conferir_alocacao(intervalos, num_portoes, alocacao)
