# CLAUDE.md

## Contexto

Trabalho da disciplina Projeto de Algoritmos (UnB) sobre **algoritmos gulosos**.
Requisito: usar dados reais de um portal de dados abertos.

**Tema:** número mínimo de portões necessários por dia no aeroporto de Brasília
(SBBR), resolvido com **interval partitioning guloso** sobre os dados VRA
(Voo Regular Ativo) da ANAC de janeiro, fevereiro e março de 2026.

## Dados

- `data/VRA_20261.json`, `VRA_20262.json`, `VRA_20263.json` (fora do git).
- Cada arquivo é uma lista JSON com BOM (ler com `encoding="utf-8-sig"`).
- Campos usados: `ICAOEmpresaAérea`, `NúmeroVoo`, `ICAOAeródromoDestino`,
  `ChegadaPrevista`, `ChegadaReal`, `SituaçãoVoo`.
- Horários no formato `AAAA-MM-DD HH:MM:SS`. Observado nos dados:
  - `ChegadaPrevista` às vezes é `null` (voos sem horário previsto);
  - alguns têm fração de segundo (`2026-01-08 00:25:00.100000000`), são válidos
    e são lidos usando os 19 primeiros caracteres.

## Premissas do modelo

- Só entram voos com `SituaçãoVoo == "REALIZADO"` e destino `SBBR`.
- O VRA não tem matrícula da aeronave, então não dá para parear chegada com
  partida. Cada chegada ocupa um portão por um **tempo de solo fixo**
  (parâmetro, padrão 45 min) a partir do pouso.
- Intervalo semiaberto `[pouso, pouso + solo)`: um portão liberado às 10:00
  pode receber um voo que pousa às 10:00.
- O dia do voo é o dia do pouso; cada dia é resolvido de forma independente.
- Horários `"N/A"`, `null` ou inválidos são descartados e contados num relatório.
- Tudo roda duas vezes: com `ChegadaPrevista` e com `ChegadaReal`
  (cada cenário descarta só os seus horários inválidos).
- Sensibilidade: tempos de solo de 30, 45 e 60 min.

## Estrutura

- `src/carregar.py`: lê os JSON, filtra e gera intervalos por dia.
- `src/guloso.py`: interval partitioning com heap; devolve nº de portões e a
  alocação voo -> portão.
- `src/analise.py`: roda previsto vs real × tempos de solo, salva CSV em `results/`.
- `src/graficos.py`: gráficos (matplotlib) em `results/`.
- `tests/`: pytest. Casos feitos à mão + teste aleatório comparando o guloso com
  o máximo de intervalos simultâneos (varredura de eventos). Os dois têm que
  bater sempre: é a evidência empírica de que o guloso é ótimo.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.analise
python -m src.graficos
pytest
```

## Convenções

- Código simples, comentado em português, sem over-engineering.
- Só biblioteca padrão + matplotlib + pytest (sem pandas).
- Sem interface web.
- Trabalho feito passo a passo. **Não rodar `git add`/`commit`/`push`**: o
  usuário revisa e commita cada etapa.
