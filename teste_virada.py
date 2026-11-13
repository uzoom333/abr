"""Confere a contagem de decêndios quando a janela atravessa a virada do ano.

Janela de out a jan: no calendário ela chega como [1, 29, 30, ..., 36], e janeiro
(decêndio 1) é o fim da janela, não o começo.  Rodar: python teste_virada.py
"""
from datetime import date

from financeiro import status_janela

JANELAS = {"medio": [1] + list(range(29, 37))}

CASOS = [
    (date(2026, 10, 15), ("dentro", 8)),   # 2º decêndio da janela: restam 8
    (date(2026, 12, 25), ("dentro", 1)),   # ainda falta o de janeiro
    (date(2026, 1, 5), ("dentro", 0)),     # último decêndio da janela
    (date(2026, 9, 5), ("antes", 4)),      # abre no 1º decêndio de outubro
    (date(2026, 2, 15), ("passou", None)), # a janela fechou em janeiro
]

erros = 0
for data, esperado in CASOS:
    obtido = status_janela(data, "medio", JANELAS)
    if obtido != esperado:
        erros += 1
        print(f"{data:%d/%m}: esperado {esperado}, veio {obtido}")

print("ok" if erros == 0 else f"{erros} de {len(CASOS)} errados")
