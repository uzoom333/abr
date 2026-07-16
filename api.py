from dotenv import load_dotenv
import os
import json
import requests

from zarc import janela_para_decendios


# ============================================
# CONFIGURAÇÃO GLOBAL DA API
# ============================================

load_dotenv()
token = os.getenv("ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {token}"
}

url = "https://api.cnptia.embrapa.br/agritec/v2/zoneamento"


# ============================================
# BUSCA DE MUNICÍPIOS
# ============================================

def busca_municipios_go():
    """Retorna lista dos municipios de GO, usando cache local"""
    arquivo_cache = "cache_municipios.json"

    if os.path.exists(arquivo_cache):
        with open(arquivo_cache, "r") as f:
            cache_completo = json.load(f)
            return cache_completo

    print("🌐 API: buscando municípios de GO")

    url_municipios = "https://api.cnptia.embrapa.br/agritec/v2/municipios"
    parametros = {"uf": "GO"}

    resposta = requests.get(url_municipios, headers=headers, params=parametros)
    dados = resposta.json()
    municipios = dados["data"]

    with open(arquivo_cache, "w") as f:
        json.dump(municipios, f)

    return municipios


def buscar_municipios(termo):
    """Busca municipios do estado de GO pelo termo, caso exista"""
    municipios = busca_municipios_go()
    resultados = []

    for municipio in municipios:
        if termo.lower() in municipio["nome"].lower():
            resultados.append(municipio)
    return resultados


def escolher_municipio():
    """Fluxo iterativo para usuario escolher um municipio. Retorna o codigoIBGE ou None"""
    termo = input("Digite parte do nome do municipio: ")

    resultados = buscar_municipios(termo)

    if not resultados:
        print("Nenhuma cidade encontrada")
        return None

    print("\nEncontrados: ")
    for i, municipio in enumerate(resultados, start=1):
        print(f"{i} - {municipio['nome']} ")

    while True:
        try:
            escolha = int(input("\nEscolha o numero: "))
            if 1 <= escolha <= len(resultados):
                break
            else:
                print("Numero fora do intervalo")
        except ValueError:
            print("Digite um numero valido")

    municipio_escolhido = resultados[escolha - 1]
    return municipio_escolhido['codigoIBGE']


# ============================================
# ZARC POR CIDADE
# ============================================

def pega_zarc(codigo_ibge):
    """Retorna o dicionário ZARC de UMA cidade, usando cache se disponível."""
    traducao = {
        "GRUPO I": "precoce",
        "GRUPO II": "medio",
        "GRUPO III": "tardio"
    }

    arquivo_cache = "cache_zarc.json"

    if os.path.exists(arquivo_cache):
        with open(arquivo_cache, "r") as f:
            cache_completo = json.load(f)
    else:
        cache_completo = {}

    if str(codigo_ibge) in cache_completo:
        print(f"📂 Cache: cidade {codigo_ibge}")
        return cache_completo[str(codigo_ibge)]

    print(f"🌐 API: chamando pra cidade {codigo_ibge}")

    parametros = {
        "idCultura": 60,
        "codigoIBGE": codigo_ibge,
        "risco": 20
    }

    resposta = requests.get(url, headers=headers, params=parametros)
    dados = resposta.json()
    zarc = dados["data"]

    janelas_por_ciclo = {}
    for janela in zarc:
        if janela["solo"] == "AD2":
            decendios = janela_para_decendios(
                janela["diaIni"], janela["mesIni"],
                janela["diaFim"], janela["mesFim"]
            )
            ciclo = traducao[janela["ciclo"]]
            if ciclo in janelas_por_ciclo:
                janelas_por_ciclo[ciclo].extend(decendios)
            else:
                janelas_por_ciclo[ciclo] = decendios

    cache_completo[str(codigo_ibge)] = janelas_por_ciclo

    with open(arquivo_cache, "w") as f:
        json.dump(cache_completo, f)

    return janelas_por_ciclo