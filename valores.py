"""Produtividade, preço e custo de cada cultura, tirados dos dados abertos da Conab.

Os arquivos vêm do Portal de Informações Agropecuárias da Conab (não é a AgroAPI: não gasta
o limite de chamadas). Este módulo baixa, resume por cultura e por estado e grava
`valores_conab.json`, que é o que o ABR lê. Para atualizar na mão:  python valores.py

O que cada valor é:
  produtividade: produção / área do último levantamento de safra (grãos, café ou cana);
  preço: preço recebido pelo produtor no último mês publicado;
  custo: custo variável + custo fixo por hectare (o custo operacional da Conab) do último
         mês publicado, na média dos municípios que a Conab acompanha no estado.
Quando o estado não tem o dado, vale o do Brasil (produtividade) ou a média dos estados que
têm (preço e custo), e o texto da fonte diz isso.
"""
import csv
import io
import json
import os
from datetime import date

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = os.path.join(BASE_DIR, "valores_conab.json")
URL = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/{}.txt"
VALIDADE_DIAS = 30  # depois disso o servidor web tenta baixar de novo

KG_POR_UNIDADE = {"sc": 60, "@": 15, "t": 1000}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Como cada cultura do ABR aparece nos arquivos da Conab.
# safra: a linha do levantamento de grãos (None = soma todas as safras do produto).
# classe: começo do texto da classificação no arquivo de preços.
# ufs_custo: o arquivo de custo do café não separa arábica de conilon; ficam os estados de arábica.
CULTURAS = {
    "soja":    {"unidade": "sc", "produto": "SOJA", "safra": "UNICA", "classe": "EM GR", "custo": ("SOJA", None)},
    "milho":   {"unidade": "sc", "produto": "MILHO", "safra": "1ª SAFRA", "classe": "EM GR", "custo": ("MILHO", "1ª SAFRA")},
    "milho2":  {"unidade": "sc", "produto": "MILHO", "safra": "2ª SAFRA", "classe": "EM GR", "custo": ("MILHO", "2ª SAFRA")},
    "arroz":   {"unidade": "sc", "produto": "ARROZ", "safra": None, "classe": "LONGO FINO EM CASCA", "custo": ("ARROZ", None)},
    "feijao":  {"unidade": "sc", "produto": "FEIJAO", "safra": None, "classe": "COMUM CORES", "custo": ("FEIJAO COMUM CORES", None)},
    "trigo":   {"unidade": "sc", "produto": "TRIGO", "safra": None, "classe": "PÃO", "custo": ("TRIGO", None)},
    "algodao": {"unidade": "@", "produto": "ALGODAO EM PLUMA", "safra": None, "classe": "", "custo": ("ALGODAO EM PLUMA", None)},
    "cana":    {"unidade": "t", "produto": "CANA DE ACUCAR", "safra": None, "classe": "", "custo": ("CANA DE ACUCAR", None)},
    "cafe":    {"unidade": "sc", "produto": "CAFE", "safra": None, "classe": "ARÁBICA", "custo": ("CAFE", None),
                "ufs_custo": {"MG", "SP", "PR", "GO"}},
}
ID_CAFE_ARABICA = "7498"  # no levantamento de café; o outro id (7090) é o conilon


# ============================================
# LEITURA DOS ARQUIVOS DA CONAB
# ============================================

def baixa(nome):
    """Linhas de um arquivo da Conab, cada uma como dicionário, sem os espaços de enchimento."""
    resposta = requests.get(URL.format(nome), timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    resposta.raise_for_status()
    texto = resposta.content.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    return [{k.strip(): (v or "").strip() for k, v in linha.items()} for linha in leitor]


def numero(texto):
    return float(texto.replace(",", ".") or 0)


def media_de(ufs):
    """Texto de onde veio o valor usado nos estados sem dado: 'AL' ou 'média de BA e MT'."""
    ufs = sorted(ufs)
    return ufs[0] if len(ufs) == 1 else "média de " + ", ".join(ufs[:-1]) + " e " + ufs[-1]


def produtividade_da_safra(linhas, por_kg, rotulo):
    """{uf: {valor, fonte}} com produção/área do último levantamento da última safra.
    linhas: já filtradas para um produto. por_kg: função (producao, area) -> kg/ha (ou a unidade final)."""
    linhas = [l for l in linhas if numero(l["area_plantada_mil_ha"]) > 0]
    if not linhas:
        return {}
    ano = max(l["ano_agricola"] for l in linhas)
    linhas = [l for l in linhas if l["ano_agricola"] == ano]
    lev = max(int(l["id_levantamento"]) for l in linhas)
    linhas = [l for l in linhas if int(l["id_levantamento"]) == lev]
    nome_lev = "levantamento final" if lev == 99 else f"{lev}º levantamento"

    somas = {}  # uf -> [produção, área]; "BR" soma tudo
    for l in linhas:
        for uf in (l["uf"], "BR"):
            soma = somas.setdefault(uf, [0.0, 0.0])
            soma[0] += numero(l["producao_mil_t"])
            soma[1] += numero(l["area_plantada_mil_ha"])
    return {uf: {"valor": por_kg(producao, area),
                 "fonte": f"{'Brasil' if uf == 'BR' else uf}, {rotulo} {ano}, {nome_lev}"}
            for uf, (producao, area) in somas.items() if uf != "NI"}


def precos(linhas, cultura):
    """{uf: {valor, fonte}} com o preço recebido pelo produtor no último mês de cada estado, em R$/unidade."""
    c = CULTURAS[cultura]
    linhas = [l for l in linhas if l["produto"] == c["produto"] and "PRODUTOR" in l["dsc_nivel_comercializacao"]
              and l["classificao_produto"].startswith(c["classe"]) and numero(l["valor_produto_kg"]) > 0]
    if not linhas:
        return {}
    kg = KG_POR_UNIDADE[c["unidade"]]
    mes = lambda l: (int(l["ano"]), int(l["mes"]))
    texto_mes = lambda m: f"{MESES[m[1] - 1]}/{m[0]}"

    por_uf = {}
    for uf in {l["uf"] for l in linhas}:
        do_estado = [l for l in linhas if l["uf"] == uf]
        ultimo = max(mes(l) for l in do_estado)
        valores = [numero(l["valor_produto_kg"]) for l in do_estado if mes(l) == ultimo]
        por_uf[uf] = {"valor": round(sum(valores) / len(valores) * kg, 2), "fonte": f"{uf}, {texto_mes(ultimo)}", "mes": ultimo}

    # para os estados sem preço: a média dos estados no mês mais recente
    ultimo = max(v["mes"] for v in por_uf.values())
    recentes = {uf: v["valor"] for uf, v in por_uf.items() if v["mes"] == ultimo}
    resultado = {uf: {"valor": v["valor"], "fonte": v["fonte"]} for uf, v in por_uf.items()}
    resultado["BR"] = {"valor": round(sum(recentes.values()) / len(recentes), 2),
                       "fonte": f"{media_de(recentes)}, {texto_mes(ultimo)}"}
    return resultado


def custos(linhas, cultura):
    """{uf: {valor, fonte}} com custo variável + fixo por hectare no último mês de cada estado."""
    c = CULTURAS[cultura]
    produto, safra = c["custo"]
    linhas = [l for l in linhas if l["produto"] == produto and (safra is None or l["safra"] == safra)
              and (not c.get("ufs_custo") or l["uf"] in c["ufs_custo"])]
    if not linhas:
        return {}
    custo_ha = lambda l: numero(l["vlr_custo_variavel_ha"]) + numero(l["vlr_custo_fixo_ha"])
    texto_mes = lambda am: f"{MESES[int(am[4:]) - 1]}/{am[:4]}"

    por_uf = {}
    for uf in {l["uf"] for l in linhas}:
        do_estado = [l for l in linhas if l["uf"] == uf]
        ultimo = max(l["ano_mes"] for l in do_estado)
        do_mes = [l for l in do_estado if l["ano_mes"] == ultimo]
        municipios = sorted({l["municipio"].title().replace(f"-{uf.title()}", f"-{uf}") for l in do_mes})
        onde = municipios[0] if len(municipios) == 1 else f"{uf} ({len(municipios)} municípios)"
        por_uf[uf] = {"valor": round(sum(custo_ha(l) for l in do_mes) / len(do_mes)),
                      "fonte": f"{onde}, {texto_mes(ultimo)}", "mes": ultimo}

    ultimo = max(v["mes"] for v in por_uf.values())
    recentes = {uf: v["valor"] for uf, v in por_uf.items() if v["mes"] == ultimo}
    resultado = {uf: {"valor": v["valor"], "fonte": v["fonte"]} for uf, v in por_uf.items()}
    resultado["BR"] = {"valor": round(sum(recentes.values()) / len(recentes)),
                       "fonte": f"{media_de(recentes)}, {texto_mes(ultimo)}"}
    return resultado


# ============================================
# ATUALIZAÇÃO
# ============================================

def atualiza():
    """Baixa os arquivos da Conab e grava valores_conab.json. Devolve o que gravou."""
    graos, cafe, cana = baixa("LevantamentoGraos"), baixa("LevantamentoCafe"), baixa("LevantamentoCana")
    tabela_precos, tabela_custos = baixa("PrecosMensalUF"), baixa("CustoProducao")

    culturas = {}
    for cultura, c in CULTURAS.items():
        kg = KG_POR_UNIDADE[c["unidade"]]
        if cultura == "cafe":  # área em ha, produção em mil sacas de 60 kg
            linhas = [l for l in cafe if l["id_produto"] == ID_CAFE_ARABICA]
            produtividade = produtividade_da_safra(linhas, lambda p, a: round(p * 1000 / a, 1), "safra")
        elif cultura == "cana":  # área em mil ha, produção em mil t
            produtividade = produtividade_da_safra(cana, lambda p, a: round(p / a, 1), "safra")
        else:  # grãos e algodão: área em mil ha, produção em mil t
            linhas = [l for l in graos if l["produto"] == c["produto"] and (c["safra"] is None or l["safra"] == c["safra"])]
            produtividade = produtividade_da_safra(linhas, lambda p, a: round(p * 1000 / a / kg, 1), "safra")
        culturas[cultura] = {"unidade": c["unidade"], "produtividade": produtividade,
                             "preco": precos(tabela_precos, cultura), "custo": custos(tabela_custos, cultura)}

    dados = {"baixado_em": date.today().isoformat(),
             "fonte": "Conab, Portal de Informações Agropecuárias (portaldeinformacoes.conab.gov.br)",
             "culturas": culturas}
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1, sort_keys=True)
    return dados


def carrega():
    """O que está em valores_conab.json, ou None se o arquivo não existe."""
    if not os.path.exists(ARQUIVO):
        return None
    with open(ARQUIVO, encoding="utf-8") as f:
        return json.load(f)


def atualiza_se_velho():
    """Baixa de novo se o arquivo não existe ou passou da validade. Sem internet, fica o que tem."""
    dados = carrega()
    if dados and (date.today() - date.fromisoformat(dados["baixado_em"])).days < VALIDADE_DIAS:
        return
    try:
        atualiza()
        print("Valores da Conab atualizados.")
    except (requests.RequestException, KeyError, ValueError) as erro:
        print(f"⚠️ Não consegui atualizar os valores da Conab ({erro}); fico com os que já tenho.")


# ============================================
# O QUE O ABR USA
# ============================================

def economia(uf, exemplo):
    """{cultura: {unidade, produtividade, preco, custo, fonte: {produtividade, preco, custo}}} para um estado.

    exemplo: os valores fixos do ABR ({cultura: {unidade, produtividade, preco, custo}}), que
    valem quando a Conab não tem o dado; nesse caso a fonte fica "exemplo, sem fonte"."""
    dados = carrega() or {"culturas": {}}
    resultado = {}
    for cultura, fixo in exemplo.items():
        conab = dados["culturas"].get(cultura, {})
        linha = {"unidade": fixo["unidade"], "fonte": {}}
        for campo in ("produtividade", "preco", "custo"):
            achado = conab.get(campo, {}).get(uf) or conab.get(campo, {}).get("BR")
            linha[campo] = achado["valor"] if achado else fixo[campo]
            linha["fonte"][campo] = achado["fonte"] if achado else "exemplo, sem fonte"
        resultado[cultura] = linha
    return resultado


def atualizado_em():
    """Data em que os valores foram baixados (dd/mm/aaaa), ou None."""
    dados = carrega()
    return date.fromisoformat(dados["baixado_em"]).strftime("%d/%m/%Y") if dados else None


if __name__ == "__main__":
    dados = atualiza()
    print(f"Gravado em {ARQUIVO}")
    for cultura, valores in dados["culturas"].items():
        print(cultura, {campo: len(valores[campo]) - 1 for campo in ("produtividade", "preco", "custo")}, "estados com dado")
