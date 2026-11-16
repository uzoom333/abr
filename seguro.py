"""O que é seguro plantar: a mesma data olhada em todas as culturas do ABR.

"Seguro" aqui é estar dentro da janela do ZARC (risco de até 20%), que é a condição
do Ministério da Agricultura para o Proagro e para o seguro rural com subvenção.
"""
from datetime import date

import api
import valores
from zarc import nome_decendio, qual_decendio, situacao_na_janela

ORDEM_STATUS = {"dentro": 0, "antes": 1, "passou": 2, "sem_zarc": 3}

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


def ranking_das_seguras(linhas, economia):
    """Entre as culturas dentro da janela, qual dá mais lucro por hectare.

    linhas: o que culturas_na_data devolve. economia: {cultura: {produtividade, preco, custo}}.
    Devolve as culturas 'dentro' com receita e lucro por hectare, do maior lucro para o menor."""
    ranking = []
    for linha in linhas:
        valores = economia.get(linha["cultura"])
        if linha["status"] != "dentro" or valores is None:
            continue
        receita = valores["produtividade"] * valores["preco"]
        ranking.append({"cultura": linha["cultura"], "nome": linha["nome"],
                        "unidade": ECONOMIA_EXEMPLO[linha["cultura"]]["unidade"],
                        "produtividade": valores["produtividade"], "preco": valores["preco"],
                        "custo": valores["custo"], "receita": receita, "lucro": receita - valores["custo"]})
    ranking.sort(key=lambda r: -r["lucro"])
    return ranking


def culturas_na_data(codigo_ibge, data):
    """Uma linha por cultura, com a situação da data em cada solo e ciclo.

    status da cultura: 'dentro' se a data cai na janela de pelo menos um solo e ciclo
    (decendios = o maior tempo que ainda resta); senão 'antes' (decendios = em quanto
    abre a primeira janela), 'passou' (em quanto reabre) ou 'sem_zarc'.
    onde: {ciclo: [solos]} só com as combinações em que a data está dentro."""
    linhas = []
    for chave, cultura in api.CULTURAS.items():
        linha = {"cultura": chave, "nome": cultura["nome"]}
        por_solo = api.zarc_por_solo(codigo_ibge, chave)
        if not por_solo:
            linha.update(status="sem_zarc", decendios=None, onde={}, combinacoes=[], todas=False)
            linhas.append(linha)
            continue

        combinacoes = []
        for solo in api.ordena_solos(por_solo):
            for ciclo in api.ordena_ciclos(por_solo[solo]):
                status, decendios = situacao_na_janela(data, por_solo[solo][ciclo])
                combinacoes.append({"solo": solo, "ciclo": ciclo, "status": status, "decendios": decendios})

        dentro = [c for c in combinacoes if c["status"] == "dentro"]
        antes = [c for c in combinacoes if c["status"] == "antes"]
        if dentro:
            status, decendios = "dentro", max(c["decendios"] for c in dentro)
        elif antes:
            status, decendios = "antes", min(c["decendios"] for c in antes)
        else:
            status, decendios = "passou", min(c["decendios"] for c in combinacoes)

        onde = {}
        for ciclo in api.ordena_ciclos({c["ciclo"] for c in dentro}):
            onde[ciclo] = [c["solo"] for c in dentro if c["ciclo"] == ciclo]

        linha.update(status=status, decendios=decendios, onde=onde, combinacoes=combinacoes,
                     todas=len(dentro) == len(combinacoes))
        linhas.append(linha)

    linhas.sort(key=lambda l: ORDEM_STATUS[l["status"]])  # sort estável: mantém a ordem das culturas
    return linhas


def texto_onde(linha):
    """'todos os solos e ciclos' ou 'precoce: AD3, AD4; medio: AD4'."""
    if linha["todas"]:
        return "todos os solos e ciclos"
    return "; ".join(f"{ciclo}: {', '.join(solos)}" for ciclo, solos in linha["onde"].items())


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


def compara_lucro(linhas, uf):
    """Pergunta produtividade, preço e custo das culturas seguras e mostra da mais lucrativa para a menos."""
    seguras = [l for l in linhas if l["status"] == "dentro"]
    print("Informe os valores de cada cultura (Enter fica com o valor entre colchetes).")
    print("Os valores entre colchetes são da Conab; a fonte de cada um aparece ao lado da cultura.")
    do_estado = economia_do_estado(uf)
    economia = {}
    for linha in seguras:
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

    print()
    print("LUCRO POR HECTARE, só entre as culturas dentro da janela")
    for i, r in enumerate(ranking_das_seguras(linhas, economia), start=1):
        print(f"{i}. {r['nome']}: {reais(r['lucro'])}  (receita {reais(r['receita'])} - custo {reais(r['custo'])})")
    print()
    print("Não entram frete, impostos, financiamento nem arrendamento. Cana e café são culturas de")
    print("vários anos: o valor é de um ano de lavoura já formada, não do ano do plantio.")
    print()


def o_que_plantar():
    """Opção do menu: escolhe a cidade e a data e mostra a situação de cada cultura."""
    print()
    print("=" * 40)
    print(">> O que é seguro plantar")
    print("=" * 40)
    print()

    codigo = api.escolher_municipio()
    if codigo is None:
        return
    data = pede_data()
    linhas = culturas_na_data(codigo, data)

    decendio = qual_decendio(data)
    print()
    print(f"{api.nome_municipio(codigo)} ({api.uf_do_codigo(codigo)}), {data:%d/%m/%Y} ({nome_decendio(decendio)})")
    print()
    for linha in linhas:
        nome, n = linha["nome"], linha["decendios"]
        if linha["status"] == "dentro":
            print(f"✅ {nome}: dentro da janela (restam até {n} decêndios)")
            print(f"     onde vale -> {texto_onde(linha)}")
        elif linha["status"] == "antes":
            print(f"⏳ {nome}: a janela abre em {n} decêndios")
        elif linha["status"] == "passou":
            print(f"❌ {nome}: a janela já fechou (reabre em {n} decêndios)")
        else:
            print(f"➖ {nome}: sem zoneamento nessa cidade")
    print()
    print("Dentro da janela = plantio dentro do ZARC (risco de até 20%), condição do Proagro e do seguro rural.")
    print()
    if any(l["status"] == "dentro" for l in linhas):
        if input("Comparar o lucro por hectare entre as culturas seguras? (s/n) ").strip().lower() == "s":
            print()
            compara_lucro(linhas, api.uf_do_codigo(codigo))
