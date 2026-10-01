"""Confere a PL na instância de brinquedo do bloco 3, ex. 2 (dá para resolver de cabeça).

1 cidade, 100 ha, um ciclo com L = 3, k = 1; soja em t ∈ {1, 2}, milho em t ∈ {5, 6, 7}.
Lucro: soja R$ 10/ha, milho R$ 5/ha.  Rodar: python teste_otimizacao.py
"""
import pulp

from otimizacao import monta_modelo

TALHAO = [{"nome": "brinquedo", "area": 100,
           "janelas_soja": {"precoce": [1, 2]},
           "lucro_soja": {"precoce": 10},
           "lucro_milho": {5: 5, 6: 5, 7: 5}}]


def lucro_com_capacidade(cap):
    modelo, *_ = monta_modelo(TALHAO, cap, duracao={"precoce": 3}, k=1)
    modelo.solve(pulp.PULP_CBC_CMD(msg=False))
    return pulp.value(modelo.objective)


# Plantadeira folgada: 100 ha de soja e 100 de milho
assert lucro_com_capacidade(1000) == 1500
# 60 ha/decêndio ainda dá: a soja se divide em t = 1 e 2, e o milho vem atrás
assert lucro_com_capacidade(60) == 1500
# 30 ha/decêndio: só cabem 60 ha de soja, e o milho fica limitado ao que foi colhido
assert lucro_com_capacidade(30) == 900
print("ok")
