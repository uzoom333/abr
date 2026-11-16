"""Confere a conta do lucro com risco e a escolha do solo da fazenda.

Não chama a API.  Rodar: python teste_risco.py
"""
from seguro import lucro_com_risco, ranking_com_risco, solos_da_cultura

erros = 0


def confere(nome, obtido, esperado):
    global erros
    if obtido != esperado:
        erros += 1
        print(f"{nome}: esperado {esperado}, veio {obtido}")


# 60 sc/ha a R$ 100 com custo de R$ 4.000: sobra 2.000 no ano normal; com quebra de 50%
# a receita cai para 3.000 e o ano ruim dá -1.000. Com risco de 20%: 0,8*2000 + 0,2*(-1000).
soja = {"produtividade": 60, "preco": 100, "custo": 4000}
confere("risco 20", lucro_com_risco(soja, 20, 50),
        {"receita": 6000, "normal": 2000, "ruim": -1000.0, "esperado": 1400.0})
confere("risco 40", lucro_com_risco(soja, 40, 50)["esperado"], 800.0)
confere("sem quebra", lucro_com_risco(soja, 40, 0)["esperado"], 2000.0)

# quem dá mais no ano normal pode perder a frente por causa do risco
linhas = [{"cultura": "soja", "nome": "Soja", "status": "dentro", "risco": 20},
          {"cultura": "feijao", "nome": "Feijão", "status": "dentro", "risco": 40},
          {"cultura": "trigo", "nome": "Trigo", "status": "antes", "risco": None}]
economia = {"soja": soja, "feijao": {"produtividade": 21, "preco": 300, "custo": 4000}, "trigo": soja}
ranking = ranking_com_risco(linhas, economia, 50, area=10)
confere("ordem", [r["cultura"] for r in ranking], ["soja", "feijao"])
confere("total", ranking[0]["total"], 14000.0)

# solo da fazenda: cada cultura usa o da sua classificação
por_ad = {"AD3": {}, "AD4": {}}
por_textura = {"ARGILOSO": {}, "ARENOSO": {}}
confere("sem solo", solos_da_cultura(por_ad, []), (["AD3", "AD4"], None))
confere("AD da fazenda", solos_da_cultura(por_ad, ["AD4", "ARGILOSO"]), (["AD4"], "AD4"))
confere("textura da fazenda", solos_da_cultura(por_textura, ["AD4", "ARGILOSO"]), (["ARGILOSO"], "ARGILOSO"))
confere("solo sem zoneamento", solos_da_cultura(por_ad, ["AD1"]), ([], "AD1"))
confere("só AD informado", solos_da_cultura(por_textura, ["AD1"]), (["ARENOSO", "ARGILOSO"], None))

print("ok" if erros == 0 else f"{erros} errados")
