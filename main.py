from datetime import date, datetime
import os
from dotenv import load_dotenv
import json
import requests

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

meses = {
    1 : "janeiro", 2 : "fevereiro", 3 : "março", 4 : "abril", 5 : "maio", 6 : "junho", 7 : "julho", 8 : "agosto", 9 : "setembro", 10 : "outubro", 11 :"novembro", 12 : "dezembro"
}

meses_para_numero = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12
}

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

janelas_zarc_jatai = pega_zarc_jatai()

def esta_na_janela(data, ciclo):
    """Verifica se uma data está dentro da janela ZARC do ciclo informado."""
    
    # 1. Descobre o decêndio da data
    decendio = qual_decendio(data)
    
    # 2. Pega a lista de decêndios verdes desse ciclo no dicionário
    janela = janelas_zarc_jatai[ciclo]
    
    # 3. Verifica se o decêndio está na janela
    if decendio in janela :
        return True
    else:
        return False
    
    
def salvar_consulta(ciclo, data_plantio, resultado):
    """Salva uma consulta no arquivo historico.csv."""
    
    arquivo = "historico.csv"
    
    # 1. Data/hora atual SEM microssegundos
    data_consulta = datetime.now().replace(microsecond=0)
    
    # 2. Converte True/False em texto
    if resultado:
        status = "dentro"
    else:
        status = "fora"
    
    # 3. Verifica se o arquivo já existe
    arquivo_existe = os.path.exists(arquivo)
    
    # 4. Abre o arquivo em modo append
    with open(arquivo, "a") as f:
        # 4a. Se o arquivo NÃO existe, escreve o cabeçalho primeiro
        if not arquivo_existe:
            f.write("data_consulta,ciclo,data_plantio,resultado\n")
        
        # 4b. Sempre escreve a linha de dados
        f.write(f"{data_consulta},{ciclo},{data_plantio},{status}\n") 
    
def main():
    print("Boas vindas a ABR - CONSULTOR DE CICLOS PREDITIVO")
    print()
    print("="*40)
    print(">> Nova consulta de plantio  ")
    print("="*40)
    print()
    while True:
        ciclo = input("Qual ciclo da soja (precoce,medio,tardio) ? ").lower()
        if ciclo in janelas_zarc_jatai:
            break
        else:
            print("Invalido, tente novamente")
    while True:
        try:
            dia = int(input("Qual dia você quer plantar? "))
            break
        except ValueError:
            print("Dia invalido")
    while True:
        mes_texto = input("Qual mes voce quer plantar? ").strip().lower()
        try:    
            mes = int(mes_texto)
            if mes < 1 or mes > 12:
                print("Mes fora do intervalo")
                continue
            break
        except ValueError:
            if mes_texto in meses_para_numero:
                mes = meses_para_numero[mes_texto]
                break
            else:
                print("Mes invalido")
    while True:
        try:
            ano = int(input("Qual ano voce deseja plantar?(2024-2030) "))
            if ano < 2024 or ano > 2030:
                print("Ano fora do ciclo do Zarc")
                continue
            break
        except ValueError:
            print("Data inválida")
    
    try:
        data_plantio = date(ano, mes, dia)
    except ValueError:
        print("Data inválida ")
        return           
    print()
    print("="*40)
    print()

    resultado = esta_na_janela(data_plantio, ciclo)

    nome_mes = meses[mes]

    decendio_ciclo = qual_decendio(data_plantio)

    janelas_ciclos = janelas_zarc_jatai[ciclo]

    primeiro_decendio = janelas_ciclos[0]

    ultimo_decendio = janelas_ciclos[-1]

    if resultado:
        print(f"✅ Plantio em {dia} de {nome_mes} de {ano} (decêndio {decendio_ciclo}) dentro da janela do Zarc !\n Ciclo {ciclo} aceitos: {janelas_ciclos}")

        faltam = ultimo_decendio - decendio_ciclo

        if faltam == 0:
            print("⚠️ Você está no ÚLTIMO decêndio da janela!")
        else:
            print(f"⏳ Faltam {faltam} decêndios para o fim da janela")

    else:
        print(f"❌ Plantio em {dia} de {nome_mes} de {ano} (decêndio {decendio_ciclo}) fora da janela do Zarc {ciclo}!\n Ciclo {ciclo} aceitos: {janelas_ciclos}")

        inicio = primeiro_decendio - decendio_ciclo

        if inicio > 0:
            print(f"A janela abre em {inicio} decendios")
        else:
            print("O ciclo desse ano ja passou")    

    salvar_consulta(ciclo, data_plantio, resultado)
    
    resposta = input("Quer fazer outra consulta? (s/n)")
    if resposta == "s":
        main()

    print()
    print("="*40)
    print()  

def mostrar_historico():
    print()
    print("="*40)
    print(">> Histórico de consultas: ")
    print("="*40)
    print()
    arquivo = "historico.csv"

    arquivo_existe = os.path.exists(arquivo)


    if not arquivo_existe:
        print("Nenhuma consulta no historico")
    else:
        with open (arquivo, "r") as f:
            for linha in f:
                print(linha.strip())

def menu():
    while True:
        escolha = input("Escolha qual opçao deseja (1-> Nova Consulta,2-> Ver historico,3-> Sair)!")
        if escolha  == "1":
            main()
        elif escolha == "2":
            mostrar_historico()
        elif escolha == "3":
            print("Saindo do menu")
            break    
        else:
            print("Opçao invalida")

if __name__ == "__main__":
    menu()
