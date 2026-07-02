from dotenv import load_dotenv
import os
import json
import requests
from datetime import date

load_dotenv()
token = os.getenv("ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {token}"
}

# Endpoint do ZARC
url = "https://api.cnptia.embrapa.br/agritec/v2/zoneamento"
parametros = {
    "idCultura": 60,
    "codigoIBGE": 5211909,
    "risco": 20
}

def qual_decendio(data):
    day = data.day
    month = data.month
    if day <=10:
        dec_mes = 1 
    elif day <=20:    
        dec_mes = 2 
    else:
        dec_mes = 3
    dec_ano = (month - 1)* 3 + dec_mes

    return dec_ano

def janela_para_decendios(dia_ini, mes_ini, dia_fim, mes_fim, ano=2026):
    data_ini = date(ano, mes_ini, dia_ini)
    data_fim = date(ano, mes_fim, dia_fim)

    dec_ini = qual_decendio(data_ini)
    dec_fim = qual_decendio(data_fim)

    return list(range(dec_ini, dec_fim + 1))

def pega_zarc_jatai():
    traducao = {
    "GRUPO I": "precoce",
    "GRUPO II": "medio",
    "GRUPO III": "tardio"
}

    arquivo_cache = "cache_zarc.json"
    
    # CAMINHO 1: Cache existe → lê e retorna
    if os.path.exists(arquivo_cache):
        print("📂 Lendo do cache local")
        with open(arquivo_cache, "r") as f:
            return json.load(f)
    
    # CAMINHO 2: Cache NÃO existe → chama API
    print("🌐 Chamando API (gastando 1 requisição)")
    
    resposta = requests.get(url, headers=headers, params=parametros)
    dados = resposta.json()
    zarc = dados["data"]
    
    # Monta o dicionário
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
    
    # Salva no cache pra próxima vez
    with open(arquivo_cache, "w") as f:
        json.dump(janelas_por_ciclo, f)
    
    return janelas_por_ciclo


# ===== TESTE =====
print(janela_para_decendios(1, 10, 31, 12))   # teste função auxiliar
print(janela_para_decendios(1, 1, 10, 1))     # teste função auxiliar

resultado = pega_zarc_jatai()
print(resultado)

