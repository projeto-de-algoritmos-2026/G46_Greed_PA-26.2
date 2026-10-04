"""Gráficos dos resultados (salvos em results/ como PNG).

Precisa rodar antes `python -m src.analise`, que gera os CSV lidos aqui.

  1. serie_diaria.png: portões por dia, previsto x real (solo de 45 min);
  2. tempo_solo.png: mínimo, média e máximo de portões por tempo de solo;
  3. pico.png: alocação voo -> portão no dia de pico (real, 45 min) e o nº
     de aviões em solo ao longo desse dia.
"""

import csv
from datetime import date, datetime, timedelta

import matplotlib

matplotlib.use("Agg")  # só gera arquivos, sem abrir janela
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from src.absioso import particionar
from src.analise import PASTA_RESULTADOS, TEMPOS_SOLO
from src.carregar import intervalos_por_dia, ler_voos

# Cores: uma por cenário, sempre a mesma em todos os gráficos.
COR = {"previsto": "#2a78d6", "real": "#eb6834"}
NOME = {"previsto": "Previsto", "real": "Real"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
FUNDO = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": FUNDO,
    "axes.facecolor": FUNDO,
    "axes.edgecolor": EIXO,
    "axes.labelcolor": TINTA_SECUNDARIA,
    "axes.titlecolor": TINTA,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRADE,
    "grid.linewidth": 0.8,
    "xtick.color": TINTA_SECUNDARIA,
    "ytick.color": TINTA_SECUNDARIA,
    "legend.frameon": False,
    "font.size": 10,
})


def ler_csv(nome):
    with open(PASTA_RESULTADOS / nome, newline="") as f:
        return list(csv.DictReader(f))


def serie_diaria(por_dia, tempo_solo=45):
    """Portões necessários em cada dia, previsto x real."""
    fig, ax = plt.subplots(figsize=(11, 4.5))

    for cenario in ("previsto", "real"):
        linhas = [l for l in por_dia
                  if l["cenario"] == cenario and int(l["tempo_solo"]) == tempo_solo]
        dias = [date.fromisoformat(l["dia"]) for l in linhas]
        portoes = [int(l["portoes"]) for l in linhas]
        ax.plot(dias, portoes, color=COR[cenario], linewidth=2,
                marker="o", markersize=3, label=NOME[cenario])

        # Rótulo direto só no máximo de cada série.
        i = portoes.index(max(portoes))
        ax.annotate(f"{NOME[cenario]}: {portoes[i]}", (dias[i], portoes[i]),
                    xytext=(0, 8), textcoords="offset points", ha="center",
                    color=TINTA_SECUNDARIA, fontsize=9)

    ax.set_title(f"Portões necessários por dia em SBBR (tempo de solo {tempo_solo} min)")
    ax.set_ylabel("portões")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    # Nome do mês em português sem depender do locale do sistema.
    ax.xaxis.set_major_formatter(
        lambda x, _: f"{MESES[mdates.num2date(x).month - 1]}/{mdates.num2date(x).year}")
    ax.grid(axis="x", which="both", visible=False)
    ax.margins(y=0.15)
    ax.legend(loc="lower right", ncols=2)

    fig.tight_layout()
    fig.savefig(PASTA_RESULTADOS / "serie_diaria.png", dpi=150)
    plt.close(fig)


def tempo_solo(resumo):
    """Faixa mínimo-máximo e média de portões para cada tempo de solo."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    deslocamento = {"previsto": -2, "real": 2}  # separa os cenários no eixo x

    for cenario in ("previsto", "real"):
        linhas = [l for l in resumo if l["cenario"] == cenario]
        x = [int(l["tempo_solo"]) + deslocamento[cenario] for l in linhas]
        minimo = [int(l["min"]) for l in linhas]
        media = [float(l["media"]) for l in linhas]
        maximo = [int(l["max"]) for l in linhas]

        ax.vlines(x, minimo, maximo, color=COR[cenario], linewidth=2)
        ax.scatter(x, media, color=COR[cenario], s=50, zorder=3,
                   edgecolors=FUNDO, linewidths=2, label=NOME[cenario])
        for xi, mx in zip(x, maximo):
            ax.annotate(str(mx), (xi, mx), xytext=(0, 4), textcoords="offset points",
                        ha="center", color=TINTA_SECUNDARIA, fontsize=9)

    ax.set_title("Efeito do tempo de solo")
    ax.set_xlabel("tempo de solo (min)")
    ax.set_ylabel("portões por dia")
    ax.set_xticks(TEMPOS_SOLO)
    ax.set_xlim(TEMPOS_SOLO[0] - 8, TEMPOS_SOLO[-1] + 8)
    ax.grid(axis="x", visible=False)
    ax.margins(y=0.1)
    ax.legend(loc="upper left", title="ponto = média, traço = mín-máx",
              title_fontsize=9, alignment="left")

    fig.tight_layout()
    fig.savefig(PASTA_RESULTADOS / "tempo_solo.png", dpi=150)
    plt.close(fig)


def pico(resumo, cenario="real", solo=45):
    """Alocação dos voos nos portões no dia de pico + aviões em solo no dia."""
    linha = next(l for l in resumo
                 if l["cenario"] == cenario and int(l["tempo_solo"]) == solo)
    dia = date.fromisoformat(linha["dia_pico"])
    campo = "ChegadaReal" if cenario == "real" else "ChegadaPrevista"

    dias, _ = intervalos_por_dia(ler_voos(), campo, solo)
    intervalos = dias[dia]
    num_portoes, alocacao = particionar(intervalos)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

    # Gantt: uma linha por portão, uma barra por voo.
    for inicio, fim, id_voo in intervalos:
        ax1.barh(alocacao[id_voo], fim - inicio, left=inicio, height=0.7,
                 color=COR[cenario], edgecolor=FUNDO, linewidth=1)
    ax1.set_title(f"Alocação gulosa no dia de pico: {dia:%d/%m/%Y} "
                  f"({len(intervalos)} voos, {num_portoes} portões, "
                  f"{NOME[cenario].lower()}, solo {solo} min)")
    ax1.set_ylabel("portão")
    ax1.set_ylim(num_portoes + 0.8, 0.2)  # portão 1 em cima
    ax1.set_yticks(range(1, num_portoes + 1, 2))
    ax1.grid(axis="y", visible=False)

    # Aviões em solo a cada minuto (o máximo é o nº de portões).
    inicio_dia = datetime.combine(dia, datetime.min.time())
    fim_dia = max(fim for _, fim, _ in intervalos)
    minutos, em_solo = [], []
    t = inicio_dia
    while t <= fim_dia:
        minutos.append(t)
        em_solo.append(sum(1 for i, f, _ in intervalos if i <= t < f))
        t += timedelta(minutes=1)
    ax2.fill_between(minutos, em_solo, step="post", color=COR[cenario], alpha=0.25,
                     linewidth=0)
    ax2.step(minutos, em_solo, where="post", color=COR[cenario], linewidth=1.5)
    ax2.axhline(num_portoes, color=TINTA_SECUNDARIA, linewidth=1, linestyle="--")
    ax2.annotate(f"máximo = {num_portoes}", (inicio_dia, num_portoes),
                 xytext=(4, 4), textcoords="offset points",
                 color=TINTA_SECUNDARIA, fontsize=9)
    ax2.set_ylabel("aviões em solo")
    ax2.set_ylim(0, num_portoes * 1.25)
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.grid(axis="x", visible=False)

    fig.tight_layout()
    fig.savefig(PASTA_RESULTADOS / "pico.png", dpi=150)
    plt.close(fig)


def main():
    por_dia = ler_csv("portoes_por_dia.csv")
    resumo = ler_csv("resumo.csv")
    serie_diaria(por_dia)
    tempo_solo(resumo)
    pico(resumo)
    print(f"Gráficos salvos em {PASTA_RESULTADOS}/")


if __name__ == "__main__":
    main()
