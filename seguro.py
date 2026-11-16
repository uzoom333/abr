"""O que plantar: a mesma data olhada em todas as culturas do ABR, com o risco e o lucro.

Para cada cultura: se a data está dentro da janela do ZARC, em qual nível de risco (20%, 30%
ou 40%) e quanto ela deixa por hectare num ano normal, num ano ruim e na média dos dois
pesada pelo risco. A fazenda (cidade, solo, área) é informada uma vez e vale para tudo.
"""
from datetime import date

import api
import valores
from quebra import QUEBRA_PADRAO, quebras_do_municipio
from zarc import nome_decendio, qual_decendio, situacao_na_janela

ORDEM_STATUS = {"dentro": 0, "antes": 1, "passou": 2, "sem_solo": 3, "sem_zarc": 4}

# Produtividade, preço e custo de cada cultura que já vêm preenchidos, para a tela não começar
# vazia. Quem usa troca pelos seus. Os valores vêm da Conab, por estado (valores.py, que grava
# valores_conab.json e diz de onde saiu cada número); a Agritec só estima produtividade de
# lavoura já plantada.
# unidade: em que a produção é vendida. produtividade em unidade/ha, preco em R$/unidade,
# custo em R$/ha.
#
# ECONOMIA_EXEMPLO só vale quando valores_conab.json não existe ou não tem a cultura.
# Nele a produtividade é a média nacional da Conab (safra 2025/26, 11º levantamento; cana
# 2026/27, 2º; café 2026, 3º) e PREÇO e CUSTO são exemplos SEM FONTE.
ECONOMIA_EXEMPLO = {
    "soja":    {"unidade": "sc", "produtividade": 62,  "preco": 125,  "custo": 4500},
    "milho":   {"unidade": "sc", "produtividade": 120, "preco": 60,   "custo": 5000},
    "milho2":  {"unidade": "sc", "produtividade": 104, "preco": 55,   "custo": 4000},
    "arroz":   {"unidade": "sc", "produtividade": 42,  "preco": 90,   "custo": 3000},
    "feijao":  {"unidade": "sc", "produtividade": 20,  "preco": 220,  "custo": 4500},
    "trigo":   {"unidade": "sc", "produtividade": 50,  "preco": 75,   "custo": 3200},
    "algodao": {"unidade": "@",  "produtividade": 135, "preco": 130,  "custo": 13000},
    "cana":    {"unidade": "t",  "produtividade": 78,  "preco": 150,  "custo": 9000},
    "cafe":    {"unidade": "sc", "produtividade": 31,  "preco": 1800, "custo": 25000},
}
NOME_UNIDADE = {"sc": "saca de 60 kg", "@": "arroba de pluma (15 kg)", "t": "tonelada"}


def economia_do_estado(uf):
    """Os valores que já vêm preenchidos para um estado: da Conab, ou o exemplo onde ela não tem."""
    return valores.economia(uf, ECONOMIA_EXEMPLO)


# Quanto da produção se perde num ano ruim (a quebra, em %): o ZARC diz a chance de haver perda
# (o nível de risco), não o tamanho dela. O valor que já vem preenchido sai da série de
# produtividade do IBGE no município (quebra.py); quem usa troca.


def lucro_com_risco(valores, risco, quebra=QUEBRA_PADRAO):
    """Lucro por hectare num ano normal, num ano ruim e o esperado entre os dois.

    valores: {produtividade, preco, custo}. risco: o nível do ZARC na data (20, 30 ou 40), lido
    como a chance de o ano ser ruim; como o ZARC garante "até" esse nível, é o pior caso.
    quebra: % da produção perdida no ano ruim. O custo é gasto inteiro nos dois casos."""
    receita = valores["produtividade"] * valores["preco"]
    normal = receita - valores["custo"]
    ruim = receita * (1 - quebra / 100) - valores["custo"]
    chance = risco / 100
    return {"receita": receita, "normal": normal, "ruim": ruim,
            "esperado": (1 - chance) * normal + chance * ruim}


def ranking_com_risco(linhas, economia, area=None):
    """Entre as culturas dentro da janela, qual dá mais lucro esperado por hectare.

    linhas: o que culturas_na_data devolve.
    economia: {cultura: {produtividade, preco, custo, quebra}}; sem quebra, vale QUEBRA_PADRAO.
    area: hectares da fazenda; com ela vem também o lucro esperado da área toda."""
    ranking = []
    for linha in linhas:
        valores = economia.get(linha["cultura"])
        if linha["status"] != "dentro" or valores is None:
            continue
        quebra = valores.get("quebra", QUEBRA_PADRAO)
        r = {"cultura": linha["cultura"], "nome": linha["nome"], "risco": linha["risco"],
             "unidade": ECONOMIA_EXEMPLO[linha["cultura"]]["unidade"],
             "produtividade": valores["produtividade"], "preco": valores["preco"], "custo": valores["custo"],
             "quebra": quebra, **lucro_com_risco(valores, linha["risco"], quebra)}
        r["total"] = r["esperado"] * area if area else None
        ranking.append(r)
    ranking.sort(key=lambda r: -r["esperado"])
    return ranking


def solos_da_cultura(por_solo, solos):
    """Quais solos do zoneamento da cultura valem para a fazenda, e qual solo da fazenda foi usado.

    O ZARC classifica o solo de dois jeitos, conforme a cultura: classe de água disponível
    (AD1..AD6) ou textura. solos traz o que a fazenda informou, no máximo um de cada jeito.
    Devolve (lista de solos, solo da fazenda): todos e None se a fazenda não informou o solo
    desse jeito; lista vazia se informou e a cultura não tem zoneamento nele."""
    por_ad = any(s.startswith("AD") for s in por_solo)
    da_fazenda = next((s for s in solos if s.startswith("AD") == por_ad), None)
    if da_fazenda is None:
        return api.ordena_solos(por_solo), None
    return ([da_fazenda] if da_fazenda in por_solo else []), da_fazenda


def culturas_na_data(codigo_ibge, data, solos=()):
    """Uma linha por cultura, com a situação e o risco do ZARC na data.

    solos: os solos da fazenda (ex.: ["AD3", "ARGILOSO"]); vazio = olha todos os solos.
    status da cultura: 'dentro' se a data cai na janela de pelo menos um solo e ciclo, em
    qualquer nível de risco (risco = o menor entre eles; decendios = o maior tempo que ainda
    resta de janela); senão 'antes' (decendios = em quanto abre a
    primeira janela), 'passou' (em quanto reabre), 'sem_solo' (a cultura não tem zoneamento no
    solo da fazenda) ou 'sem_zarc'.
    ciclos: [{ciclo, risco}] só com os ciclos em que a data está dentro.
    calendario: {decêndio do calendário: menor risco} juntando os solos e ciclos olhados."""
    decendio = qual_decendio(data)
    linhas = []
    for chave, cultura in api.CULTURAS.items():
        linha = {"cultura": chave, "nome": cultura["nome"], "decendios": None, "risco": None,
                 "solo": None, "ciclos": [], "calendario": {}}
        por_solo = api.riscos_por_solo(codigo_ibge, chave)
        if not por_solo:
            linha["status"] = "sem_zarc"
            linhas.append(linha)
            continue
        usados, linha["solo"] = solos_da_cultura(por_solo, solos)
        if not usados:
            linha["status"] = "sem_solo"
            linhas.append(linha)
            continue

        combinacoes, risco_do_ciclo = [], {}
        for solo in usados:
            for ciclo, mapa in por_solo[solo].items():
                status, decendios = situacao_na_janela(data, list(mapa))
                combinacoes.append({"status": status, "decendios": decendios})
                if decendio in mapa:
                    risco_do_ciclo[ciclo] = min(mapa[decendio], risco_do_ciclo.get(ciclo, 100))
                for d, risco in mapa.items():
                    linha["calendario"][d] = min(risco, linha["calendario"].get(d, 100))

        dentro = [c for c in combinacoes if c["status"] == "dentro"]
        antes = [c for c in combinacoes if c["status"] == "antes"]
        if dentro:
            linha.update(status="dentro", decendios=max(c["decendios"] for c in dentro),
                         risco=min(risco_do_ciclo.values()),
                         ciclos=[{"ciclo": c, "risco": risco_do_ciclo[c]} for c in api.ordena_ciclos(risco_do_ciclo)])
        elif antes:
            linha.update(status="antes", decendios=min(c["decendios"] for c in antes))
        else:
            linha.update(status="passou", decendios=min(c["decendios"] for c in combinacoes))
        linhas.append(linha)

    linhas.sort(key=lambda l: ORDEM_STATUS[l["status"]])  # sort estável: mantém a ordem das culturas
    return linhas


def texto_ciclos(linha):
    """'precoce 20%, medio 30%'."""
    return ", ".join(f"{c['ciclo']} {c['risco']}%" for c in linha["ciclos"])


def pede_data():
    while True:
        texto = input("Data do plantio (dd/mm/aaaa, Enter = hoje): ").strip()
        if not texto:
            return date.today()
        try:
            dia, mes, ano = (int(p) for p in texto.split("/"))
            return date(ano, mes, dia)
        except ValueError:
            print("Data inválida. Exemplo: 15/10/2026")


def pede_com_exemplo(mensagem, exemplo):
    """Pede um número positivo; Enter fica com o valor de exemplo."""
    while True:
        texto = input(f"  {mensagem} [{exemplo}]: ").strip().replace(",", ".")
        if not texto:
            return float(exemplo)
        try:
            valor = float(texto)
            if valor > 0:
                return valor
            print("  O valor precisa ser maior que zero.")
        except ValueError:
            print("  Digite um número.")


def reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pede_solo(mensagem, opcoes):
    """Pergunta um solo da lista; Enter devolve None (não sei / todos)."""
    while True:
        texto = input(f"{mensagem} ({', '.join(opcoes)}; Enter = não sei): ").strip().upper()
        if not texto:
            return None
        if texto in opcoes:
            return texto
        print("Opção inválida.")


def pede_area():
    """Área da fazenda em hectares; Enter devolve None (só mostra por hectare)."""
    while True:
        texto = input("Área a plantar, em hectares (Enter = só por hectare): ").strip().replace(",", ".")
        if not texto:
            return None
        try:
            if float(texto) > 0:
                return float(texto)
        except ValueError:
            pass
        print("Digite um número maior que zero.")


def pede_quebra(exemplo):
    """Quebra da produção num ano ruim, de 0 a 100; Enter fica com o valor de exemplo."""
    while True:
        texto = input(f"  Quebra da produção num ano ruim (%) [{exemplo}]: ").strip().replace(",", ".")
        if not texto:
            return float(exemplo)
        try:
            if 0 <= float(texto) <= 100:
                return float(texto)
        except ValueError:
            pass
        print("  Digite um número de 0 a 100.")


def compara_lucro(linhas, codigo, area=None):
    """Pergunta produtividade, preço, custo e quebra das culturas dentro da janela e mostra do
    maior lucro esperado para o menor, com o risco de cada uma."""
    dentro = [l for l in linhas if l["status"] == "dentro"]
    print("Informe os valores de cada cultura (Enter fica com o valor entre colchetes).")
    print("Produtividade, preço e custo entre colchetes são da Conab; a quebra em ano ruim é do IBGE.")
    print("A fonte de cada um aparece ao lado da cultura.")
    do_estado = economia_do_estado(api.uf_do_codigo(codigo))
    quebras = quebras_do_municipio(codigo)
    economia = {}
    for linha in dentro:
        exemplo = do_estado[linha["cultura"]]
        unidade = exemplo["unidade"]
        print(f"\n{linha['nome']} (vendida por {NOME_UNIDADE[unidade]})")
        fonte = exemplo["fonte"]
        print(f"  Conab -> produtividade: {fonte['produtividade']}; preço: {fonte['preco']}; custo: {fonte['custo']}")
        economia[linha["cultura"]] = {
            "produtividade": pede_com_exemplo(f"Produtividade ({unidade}/ha)", exemplo["produtividade"]),
            "preco": pede_com_exemplo(f"Preço (R$/{unidade})", exemplo["preco"]),
            "custo": pede_com_exemplo("Custo de produção (R$/ha)", exemplo["custo"]),
        }
        print(f"  Quebra -> {quebras[linha['cultura']]['fonte']}")
        economia[linha["cultura"]]["quebra"] = pede_quebra(quebras[linha["cultura"]]["valor"])

    print()
    print("LUCRO POR HECTARE, só entre as culturas dentro da janela, do maior lucro esperado para o menor")
    for i, r in enumerate(ranking_com_risco(linhas, economia, area), start=1):
        print(f"{i}. {r['nome']} (risco de até {r['risco']}%, quebra de {r['quebra']:g}%): esperado {reais(r['esperado'])}")
        print(f"     ano normal {reais(r['normal'])} | ano ruim {reais(r['ruim'])}"
              + (f" | esperado em {area:g} ha: {reais(r['total'])}" if area else ""))
    print()
    print("Ano ruim = a produção cai o tanto da quebra, com o custo inteiro. Lucro esperado = a média")
    print("dos dois anos, pesada pelo risco do ZARC na data. A quebra do IBGE é a média do município,")
    print("que esconde a perda de cada fazenda. Não entram frete, impostos, financiamento nem")
    print("arrendamento. Cana e café são culturas de vários anos: o valor é de um ano de lavoura já")
    print("formada, não do ano do plantio.")
    print()


def o_que_plantar():
    """Opção do menu: a fazenda (cidade, solo, área) e a data; mostra a situação e o risco de cada cultura."""
    print()
    print("=" * 40)
    print(">> O que plantar")
    print("=" * 40)
    print()

    codigo = api.escolher_municipio()
    if codigo is None:
        return
    data = pede_data()
    solos, area = [], None
    if not api.MODO_DEMO:  # o demo só tem a soja em solo AD2
        print("Solo da fazenda. O ZARC usa a classe de água disponível em umas culturas e a textura em outras.")
        solos = [s for s in (pede_solo("Classe de água disponível", api.ORDEM_SOLOS[:6]),
                             pede_solo("Textura", api.ORDEM_SOLOS[6:])) if s]
    area = pede_area()
    linhas = culturas_na_data(codigo, data, solos)

    decendio = qual_decendio(data)
    print()
    print(f"{api.nome_municipio(codigo)} ({api.uf_do_codigo(codigo)}), {data:%d/%m/%Y} ({nome_decendio(decendio)})")
    print()
    for linha in linhas:
        nome, n = linha["nome"], linha["decendios"]
        if linha["status"] == "dentro":
            print(f"✅ {nome}: dentro da janela, risco de até {linha['risco']}% (restam até {n} decêndios)")
            print(f"     ciclos -> {texto_ciclos(linha)}")
        elif linha["status"] == "antes":
            print(f"⏳ {nome}: a janela abre em {n} decêndios")
        elif linha["status"] == "passou":
            print(f"❌ {nome}: a janela já fechou (reabre em {n} decêndios)")
        elif linha["status"] == "sem_solo":
            print(f"➖ {nome}: sem zoneamento no solo {linha['solo']} nessa cidade")
        else:
            print(f"➖ {nome}: sem zoneamento nessa cidade")
    print()
    print("Risco = chance de perda de rendimento por clima, segundo o ZARC: até 20%, 30% ou 40%.")
    print()
    if any(l["status"] == "dentro" for l in linhas):
        if input("Comparar o lucro por hectare entre as culturas dentro da janela? (s/n) ").strip().lower() == "s":
            print()
            compara_lucro(linhas, codigo, area)
