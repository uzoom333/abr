from dotenv import load_dotenv
import os
import json
import requests

from zarc import qual_decendio, decendios_entre
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

# Código IBGE do estado (os dois primeiros dígitos do código do município) -> sigla
UFS = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}
UF_PADRAO = "GO"


def ufs_disponiveis():
    """Siglas dos estados que dá para consultar. No modo demo, só GO."""
    if MODO_DEMO:
        return [UF_PADRAO]
    return sorted(UFS.values())


def busca_municipios(uf=UF_PADRAO):
    """Lista dos municípios de um estado, usando cache local (um pedido à API por estado)."""
    uf = uf.upper()
    if MODO_DEMO:
        return carrega_json_demo(DEMO_MUNICIPIOS) if uf == UF_PADRAO else []

    arquivo_cache = "cache_municipios_uf.json"

    if os.path.exists(arquivo_cache):
        with open(arquivo_cache, "r") as f:
            cache_completo = json.load(f)
    else:
        cache_completo = {}

    if uf in cache_completo:
        return cache_completo[uf]

    print(f"🌐 API: buscando municípios de {uf}")

    url_municipios = "https://api.cnptia.embrapa.br/agritec/v2/municipios"
    try:
        resposta = requests.get(url_municipios, headers=headers, params={"uf": uf}, timeout=30)
    except requests.RequestException as e:
        print(f"⚠️ Não consegui falar com a API ({e})")
        return []
    if resposta.status_code != 200:
        print(f"⚠️ API não retornou os municípios de {uf} (status {resposta.status_code})")
        return []

    municipios = resposta.json().get("data", [])
    cache_completo[uf] = municipios
    with open(arquivo_cache, "w") as f:
        json.dump(cache_completo, f)

    return municipios


def busca_municipios_go():
    """Lista dos municípios de GO. Mantida para o código que ainda só olha Goiás."""
    return busca_municipios("GO")


def uf_do_codigo(codigo_ibge):
    """Sigla do estado a partir do código IBGE do município."""
    return UFS.get(int(str(codigo_ibge)[:2]))


def nome_municipio(codigo_ibge):
    """Nome do município em qualquer estado, ou None se o código não existir."""
    uf = uf_do_codigo(codigo_ibge)
    if uf is None:
        return None
    for municipio in busca_municipios(uf):
        if municipio["codigoIBGE"] == int(codigo_ibge):
            return municipio["nome"]
    return None


def buscar_municipios(termo, uf=UF_PADRAO):
    """Busca municípios de um estado pelo termo, caso exista"""
    municipios = busca_municipios(uf)
    resultados = []

    for municipio in municipios:
        if termo.lower() in municipio["nome"].lower():
            resultados.append(municipio)
    return resultados


def escolher_uf():
    """Pergunta o estado. Enter fica com Goiás. No modo demo nem pergunta."""
    disponiveis = ufs_disponiveis()
    if len(disponiveis) == 1:
        return disponiveis[0]
    while True:
        uf = input(f"Estado (sigla, Enter = {UF_PADRAO}): ").strip().upper() or UF_PADRAO
        if uf in disponiveis:
            return uf
        print("Sigla inválida. Exemplos: GO, MT, PR, BA")


def escolher_municipio():
    """Fluxo iterativo para usuario escolher um municipio. Retorna o codigoIBGE ou None"""
    uf = escolher_uf()
    termo = input("Digite parte do nome do municipio: ")

    resultados = buscar_municipios(termo, uf)

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
# CULTURAS
# ============================================

# As culturas que o ABR consulta. "id" é o idCultura da Agritec (conferido em /culturas).
# "produtividade_api" marca as que a Agritec também estima a produtividade; nas outras
# a produtividade é digitada pelo produtor.
CULTURAS = {
    "soja":    {"id": 60,    "nome": "Soja",           "produtividade_api": True},
    "milho":   {"id": 56,    "nome": "Milho 1ª safra", "produtividade_api": True},
    "milho2":  {"id": 57,    "nome": "Milho 2ª safra", "produtividade_api": False},
    "arroz":   {"id": 61,    "nome": "Arroz",          "produtividade_api": True},
    "feijao":  {"id": 62,    "nome": "Feijão",         "produtividade_api": True},
    "trigo":   {"id": 32533, "nome": "Trigo",          "produtividade_api": True},
    "algodao": {"id": 103,   "nome": "Algodão",        "produtividade_api": False},
    "cana":    {"id": 169,   "nome": "Cana-de-açúcar", "produtividade_api": False},
    "cafe":    {"id": 115,   "nome": "Café arábica",   "produtividade_api": False},
}
CULTURA_PADRAO = "soja"
SOLO_PADRAO = "AD2"

ID_CULTURA_SOJA = CULTURAS["soja"]["id"]
ID_CULTURA_MILHO = int(os.getenv("ID_CULTURA_MILHO", CULTURAS["milho2"]["id"]))

# Como a Agritec chama o ciclo -> como o ABR chama
TRADUCAO_CICLOS = {
    "GRUPO I": "precoce",
    "GRUPO II": "medio",
    "GRUPO III": "tardio",
    "PERENE": "perene",
    "SEMIPERENE": "semiperene",
}
ORDEM_CICLOS = ["precoce", "medio", "tardio", "semiperene", "perene"]

# Os solos vêm em duas classificações, conforme a cultura: AD1..AD6 (água disponível)
# ou a textura. Esta é a ordem em que aparecem na tela.
ORDEM_SOLOS = ["AD1", "AD2", "AD3", "AD4", "AD5", "AD6", "ARENOSO", "TEXTURA MEDIA", "ARGILOSO"]


def _posicao(lista, item):
    return lista.index(item) if item in lista else len(lista)


def ordena_solos(solos):
    return sorted(solos, key=lambda s: (_posicao(ORDEM_SOLOS, s), s))


def ordena_ciclos(ciclos):
    return sorted(ciclos, key=lambda c: (_posicao(ORDEM_CICLOS, c), c))


# ============================================
# ZARC
# ============================================

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
    try:
        resposta = requests.get(url, headers=headers, params=parametros, timeout=30)
    except requests.RequestException as e:
        print(f"⚠️ Não consegui falar com a API ({e})")
        return None
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


def zarc_por_solo(codigo_ibge, cultura=CULTURA_PADRAO):
    """{solo: {ciclo: [decêndios do calendário, em ordem]}} de uma cultura numa cidade.
    None se a cidade não tem zoneamento para a cultura ou se a API falhar."""
    if MODO_DEMO:
        if cultura != "soja":
            return None  # o demo só traz a soja
        dados_demo = carrega_json_demo(DEMO_ZARC)
        if str(codigo_ibge) not in dados_demo:
            return None
        return {SOLO_PADRAO: dados_demo[str(codigo_ibge)]}  # e só o solo AD2

    registros = _zarc_bruto(codigo_ibge, CULTURAS[cultura]["id"])
    if not registros:
        return None

    por_solo = {}
    for registro in registros:
        ciclo = TRADUCAO_CICLOS.get(registro["ciclo"], registro["ciclo"].lower())
        janela = por_solo.setdefault(registro["solo"], {}).setdefault(ciclo, [])
        for d in _decendios_do_registro(registro):
            if d not in janela:
                janela.append(d)

    for janelas in por_solo.values():
        for janela in janelas.values():
            janela.sort()
    return por_solo


def portaria_do_zarc(codigo_ibge, cultura=CULTURA_PADRAO):
    """Portaria do Ministério de onde veio a janela (ex.: 'Port. 198 de 03/07/2026'), ou None."""
    if MODO_DEMO:
        return None
    registros = _zarc_bruto(codigo_ibge, CULTURAS[cultura]["id"])
    return registros[0].get("portaria") if registros else None


def pega_zarc(codigo_ibge, cultura=CULTURA_PADRAO, solo=SOLO_PADRAO):
    """{ciclo: [decêndios]} de UMA cidade, para uma cultura e um solo. Sem argumentos
    a mais, é a soja em solo AD2, como o ABR sempre consultou."""
    por_solo = zarc_por_solo(codigo_ibge, cultura)
    if por_solo is None:
        print(f"⚠️ Cidade {codigo_ibge} sem zoneamento de {CULTURAS[cultura]['nome'].lower()}")
        return None
    if solo not in por_solo:
        print(f"⚠️ Cidade {codigo_ibge} sem zoneamento de {CULTURAS[cultura]['nome'].lower()} no solo {solo}")
        return None
    return por_solo[solo]


def zarc_soja_por_solo(codigo_ibge):
    """{solo: {ciclo: [decêndios]}} da soja (usado pela otimização)."""
    return zarc_por_solo(codigo_ibge, "soja")


def zarc_milho_por_solo(codigo_ibge):
    """{solo: [decêndios]} do milho 2ª safra. Junta os ciclos do milho numa janela só."""
    if MODO_DEMO:
        dados_demo = carrega_json_demo(DEMO_ZARC_MILHO)
        return dados_demo["cidades"].get(str(codigo_ibge))

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
