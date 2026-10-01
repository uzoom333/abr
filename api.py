from dotenv import load_dotenv
import os
import json
import requests

from zarc import janela_para_decendios, qual_decendio, decendios_entre
from datetime import date


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
# MODO DEMO
# ============================================

# Diretório onde este arquivo mora. Usado pros arquivos de demo, assim o
# programa roda de qualquer lugar, não só de dentro da pasta do projeto.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_DEMO = os.path.join(BASE_DIR, "demo")

DEMO_MUNICIPIOS = os.path.join(PASTA_DEMO, "demo_municipios.json")
DEMO_ZARC = os.path.join(PASTA_DEMO, "demo_zarc.json")
DEMO_ZARC_MILHO = os.path.join(PASTA_DEMO, "demo_zarc_milho.json")

# Valores que aparecem em .env.example e não valem como token de verdade
PLACEHOLDERS = {"", "seu_token_aqui", "coloque_seu_token_aqui", "changeme"}


def token_valido():
    """True se existe um ACCESS_TOKEN utilizável no ambiente."""
    if token is None:
        return False
    return token.strip() not in PLACEHOLDERS


MODO_DEMO = not token_valido()


def aviso_modo_demo():
    """Imprime o aviso de modo demo. Chamado uma vez, na inicialização."""
    if not MODO_DEMO:
        return
    print("=" * 60)
    print("⚠️  MODO DEMO ATIVO — usando dados de exemplo.")
    print("   Para dados completos e atualizados, configure o .env")
    print("   com seu ACCESS_TOKEN da AgroAPI (veja o README).")
    print("=" * 60)
    print()


def carrega_json_demo(caminho):
    """Lê um arquivo de dados da pasta demo/. Erro claro se estiver faltando."""
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Arquivo de demo não encontrado: {caminho}\n"
            "A pasta demo/ faz parte do repositório — recupere com 'git checkout demo/'."
        )
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================
# BUSCA DE MUNICÍPIOS
# ============================================

def busca_municipios_go():
    """Retorna lista dos municipios de GO, usando cache local"""
    if MODO_DEMO:
        return carrega_json_demo(DEMO_MUNICIPIOS)

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

    if MODO_DEMO:
        dados_demo = carrega_json_demo(DEMO_ZARC)
        if str(codigo_ibge) not in dados_demo:
            print(f"⚠️ Cidade {codigo_ibge} não está incluída nos dados de demo")
            return None
        print(f"🎭 Demo: cidade {codigo_ibge}")
        return dados_demo[str(codigo_ibge)]

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

    if resposta.status_code != 200:
        print(f"⚠️ API não retornou dados pra cidade {codigo_ibge} (status {resposta.status_code})")
        return None

    dados = resposta.json()
    zarc = dados.get("data", [])

    if not zarc:
        print(f"⚠️ Cidade {codigo_ibge} não tem zoneamento cadastrado")
        return None

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

# ============================================
# ZARC POR SOLO (usado pela otimização)
# ============================================

ID_CULTURA_SOJA = 60

# O id do milho 2ª safra na AgroAPI ainda não foi conferido. Enquanto não estiver
# no .env (ID_CULTURA_MILHO=...), a otimização só roda em modo demo.
ID_CULTURA_MILHO = os.getenv("ID_CULTURA_MILHO")

TRADUCAO_CICLOS = {
    "GRUPO I": "precoce",
    "GRUPO II": "medio",
    "GRUPO III": "tardio"
}


def _zarc_bruto(codigo_ibge, id_cultura):
    """Registros do /zoneamento como a API devolve, com cache próprio.
    Retorna lista (vazia se a cidade não tem zoneamento) ou None se a API falhar."""
    arquivo_cache = "cache_zarc_bruto.json"
    chave = f"{id_cultura}:{codigo_ibge}"

    if os.path.exists(arquivo_cache):
        with open(arquivo_cache, "r") as f:
            cache_completo = json.load(f)
    else:
        cache_completo = {}

    if chave in cache_completo:
        return cache_completo[chave]

    print(f"🌐 API: zoneamento da cultura {id_cultura} pra cidade {codigo_ibge}")
    parametros = {"idCultura": id_cultura, "codigoIBGE": codigo_ibge, "risco": 20}
    resposta = requests.get(url, headers=headers, params=parametros)
    if resposta.status_code != 200:
        print(f"⚠️ API não retornou dados (status {resposta.status_code})")
        return None

    registros = resposta.json().get("data", [])
    cache_completo[chave] = registros
    with open(arquivo_cache, "w") as f:
        json.dump(cache_completo, f)
    return registros


def _decendios_do_registro(registro):
    """Janela de um registro da API em decêndios do calendário. Aceita janela que atravessa o ano.
    O ano 2024 é só para a data existir em 29/02; o decêndio não depende do ano."""
    dec_ini = qual_decendio(date(2024, registro["mesIni"], registro["diaIni"]))
    dec_fim = qual_decendio(date(2024, registro["mesFim"], registro["diaFim"]))
    return decendios_entre(dec_ini, dec_fim)


def zarc_soja_por_solo(codigo_ibge):
    """{solo: {ciclo: [decêndios]}}. Diferente de pega_zarc, guarda todos os solos, não só o AD2."""
    if MODO_DEMO:
        dados_demo = carrega_json_demo(DEMO_ZARC)
        if str(codigo_ibge) not in dados_demo:
            return None
        return {"AD2": dados_demo[str(codigo_ibge)]}  # o demo só tem AD2

    registros = _zarc_bruto(codigo_ibge, ID_CULTURA_SOJA)
    if not registros:
        return None

    por_solo = {}
    for registro in registros:
        ciclo = TRADUCAO_CICLOS.get(registro["ciclo"])
        if ciclo is None:
            continue
        janelas = por_solo.setdefault(registro["solo"], {})
        janelas.setdefault(ciclo, [])
        for d in _decendios_do_registro(registro):
            if d not in janelas[ciclo]:
                janelas[ciclo].append(d)
    return por_solo


def zarc_milho_por_solo(codigo_ibge):
    """{solo: [decêndios]} do milho 2ª safra. Junta os ciclos do milho numa janela só."""
    if MODO_DEMO:
        dados_demo = carrega_json_demo(DEMO_ZARC_MILHO)
        return dados_demo["cidades"].get(str(codigo_ibge))

    if ID_CULTURA_MILHO is None:
        print("⚠️ Falta ID_CULTURA_MILHO no .env (id do milho 2ª safra na AgroAPI).")
        return None

    registros = _zarc_bruto(codigo_ibge, ID_CULTURA_MILHO)
    if not registros:
        return None

    por_solo = {}
    for registro in registros:
        janela = por_solo.setdefault(registro["solo"], [])
        for d in _decendios_do_registro(registro):
            if d not in janela:
                janela.append(d)
    return por_solo
