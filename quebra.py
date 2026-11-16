"""Quanto a produção cai num ano ruim, tirado da série de produtividade do IBGE por município.

O ZARC diz a chance de haver perda (o nível de risco), não o tamanho dela. O tamanho vem daqui:
a Produção Agrícola Municipal do IBGE (tabela 5457 do SIDRA) traz o rendimento médio de cada
cultura em cada município, ano a ano, desde 1974. Não é a AgroAPI: não gasta o limite de chamadas.

A conta, por cultura e município:
  1. cada ano é comparado com a média dos 5 anos anteriores (a produtividade sobe com o tempo,
     então comparar com a série toda faria os anos antigos parecerem ruins);
  2. ficam as últimas 30 comparações;
  3. a quebra é a queda média nos 20% piores anos (20% é o nível de risco base do ZARC).

Limites: a média do município esconde a perda de cada fazenda, que pode ser maior; a série
junta todas as datas de plantio; o IBGE não separa milho 1ª de 2ª safra nem, antes de 2012,
café arábica de conilon. Por isso o valor é só o ponto de partida e quem usa pode trocar.
Município sem série suficiente usa a do estado.
"""
import json
import os

import requests

import api

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CACHE = os.path.join(BASE_DIR, "cache_quebra_ibge.json")
URL = "https://apisidra.ibge.gov.br/values/t/5457/{nivel}/{codigo}/v/112/p/all/c782/{produtos}"

# Vale quando nem o município nem o estado têm série suficiente no IBGE. É HIPÓTESE do ABR, sem fonte.
QUEBRA_PADRAO = 50

ANOS_DE_REFERENCIA = 5   # cada ano é comparado com a média dos 5 anteriores
MINIMO_DE_REFERENCIA = 3 # ...desde que pelo menos 3 deles tenham dado
JANELA = 30              # últimas 30 comparações
PIORES = 0.20            # ano ruim = os 20% piores
MINIMO_DE_ANOS = 10      # com menos comparações que isso, não calcula

# Cultura do ABR -> código do produto na tabela 5457 e como o IBGE o agrupa (para o texto da fonte).
PRODUTOS = {
    "soja":    ("40124", ""),
    "milho":   ("40122", "milho total, sem separar a safra"),
    "milho2":  ("40122", "milho total, sem separar a safra"),
    "arroz":   ("40102", ""),
    "feijao":  ("40112", "feijão total"),
    "trigo":   ("40127", ""),
    "algodao": ("40099", ""),
    "cana":    ("40106", ""),
    "cafe":    ("40139", "café total, arábica e conilon"),
}


def quebra_da_serie(serie):
    """serie: {ano: produtividade}. Devolve {valor (%), piores, anos, de, ate} ou None se a
    série é curta. valor nunca é negativo: se nem os piores anos caíram, a quebra é zero."""
    anos = sorted(serie)
    desvios = []  # (quanto o ano ficou acima ou abaixo da referência, ano)
    for i, ano in enumerate(anos):
        anteriores = [serie[a] for a in anos[:i] if ano - a <= ANOS_DE_REFERENCIA]
        if len(anteriores) < MINIMO_DE_REFERENCIA:
            continue
        referencia = sum(anteriores) / len(anteriores)
        desvios.append((serie[ano] / referencia - 1, ano))
    desvios = desvios[-JANELA:]
    if len(desvios) < MINIMO_DE_ANOS:
        return None
    quantos = max(1, round(len(desvios) * PIORES))
    piores = sorted(desvios)[:quantos]
    queda = -100 * sum(desvio for desvio, _ in piores) / quantos
    return {"valor": max(0.0, round(queda, 1)), "piores": quantos, "anos": len(desvios),
            "de": desvios[0][1], "ate": desvios[-1][1]}


def baixa_series(nivel, codigo):
    """{código do produto: {ano: kg/ha}} de um município (nivel "n6") ou de um estado ("n3"),
    direto do SIDRA. Um pedido só."""
    produtos = ",".join(sorted({produto for produto, _ in PRODUTOS.values()}))
    resposta = requests.get(URL.format(nivel=nivel, codigo=codigo, produtos=produtos), timeout=90,
                            headers={"User-Agent": "Mozilla/5.0"})
    resposta.raise_for_status()
    series = {}
    for linha in resposta.json()[1:]:  # a primeira linha é o cabeçalho
        try:
            valor = float(linha["V"])
        except ValueError:  # "-", "..", "...": sem dado no ano
            continue
        if valor > 0:
            series.setdefault(linha["D4C"], {})[int(linha["D3C"])] = valor
    return series


def _quebras_do_lugar(nivel, codigo, cache):
    """{código do produto: quebra ou None} de um município ou estado, pelo cache ou pelo IBGE.
    {} se o IBGE não respondeu (aí não guarda, para tentar de novo depois)."""
    chave = f"{nivel}:{codigo}"
    if chave not in cache:
        print(f"🌐 IBGE: série de produtividade de {'cidade' if nivel == 'n6' else 'estado'} {codigo}")
        try:
            series = baixa_series(nivel, codigo)
        except (requests.RequestException, ValueError, KeyError) as erro:
            print(f"⚠️ Não consegui a série do IBGE ({erro}).")
            return {}
        cache[chave] = {produto: quebra_da_serie(serie) for produto, serie in series.items()}
        with open(ARQUIVO_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    return cache[chave]


def quebras_do_municipio(codigo_ibge):
    """{cultura: {valor, fonte}} com a quebra em ano ruim de cada cultura no município.
    Onde o município não tem série suficiente, vale a do estado (que cai menos, por ser média de
    mais lavouras); sem nenhuma das duas, ou sem internet, QUEBRA_PADRAO. A fonte diz qual foi."""
    cache = {}
    if os.path.exists(ARQUIVO_CACHE):
        with open(ARQUIVO_CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    do_municipio = _quebras_do_lugar("n6", codigo_ibge, cache)
    do_estado = None  # só busca o estado se faltar alguma cultura no município
    nome = (api.nome_municipio(codigo_ibge) or str(codigo_ibge)).title()
    uf = api.uf_do_codigo(codigo_ibge)

    resultado = {}
    for cultura, (produto, agrupado) in PRODUTOS.items():
        q, onde = do_municipio.get(produto), nome
        if not q:
            if do_estado is None:
                do_estado = _quebras_do_lugar("n3", str(codigo_ibge)[:2], cache)
            q, onde = do_estado.get(produto), f"{uf}, porque {nome} não tem série"
        if q:
            fonte = (f"IBGE/PAM, {onde}: queda média nos {q['piores']} piores de {q['anos']} anos "
                     f"({q['de']} a {q['ate']})" + (f"; {agrupado}" if agrupado else ""))
            resultado[cultura] = {"valor": q["valor"], "fonte": fonte}
        else:
            resultado[cultura] = {"valor": QUEBRA_PADRAO, "fonte": "hipótese, sem série do IBGE na cidade nem no estado"}
    return resultado


if __name__ == "__main__":
    import sys
    for cultura, q in quebras_do_municipio(sys.argv[1] if len(sys.argv) > 1 else 5218805).items():
        print(f"{cultura:8} {q['valor']:>5}%  {q['fonte']}")
