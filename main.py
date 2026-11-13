from datetime import date
from comparacao import comparar_cidades
from zarc import qual_decendio, esta_na_janela, situacao_na_janela
import api
from api import escolher_municipio, aviso_modo_demo
from historico import salvar_consulta, mostrar_historico
from estatistica import mostrar_estatisticas
from exportacao import exportar_excel
from financeiro import analisar_financeiro
from otimizacao import analisar_otimizacao
from seguro import o_que_plantar

meses = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}

meses_para_numero = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12
}


def escolhe_da_lista(titulo, opcoes, nomes=None, padrao=None):
    """Mostra as opções numeradas e devolve a escolhida. Com uma opção só, nem pergunta.
    Enter fica com o padrão, quando ele está na lista."""
    nomes = nomes or {}
    if len(opcoes) == 1:
        print(f"{titulo}: {nomes.get(opcoes[0], opcoes[0])}")
        return opcoes[0]
    print(f"\n{titulo}:")
    for i, opcao in enumerate(opcoes, start=1):
        print(f"{i} - {nomes.get(opcao, opcao)}")
    dica = f" (Enter = {nomes.get(padrao, padrao)})" if padrao in opcoes else ""
    while True:
        texto = input(f"Escolha o numero{dica}: ").strip()
        if not texto and padrao in opcoes:
            return padrao
        try:
            escolha = int(texto)
            if 1 <= escolha <= len(opcoes):
                return opcoes[escolha - 1]
            print("Numero fora do intervalo")
        except ValueError:
            print("Digite um numero valido")


def main():
    print("Boas vindas a ABR - CONSULTOR DE CICLOS PREDITIVO")
    print()
    print("=" * 40)
    print(">> Nova consulta de plantio  ")
    print("=" * 40)
    print()

    codigo_ibge = escolher_municipio()
    if codigo_ibge is None:
        return

    nomes_culturas = {chave: c["nome"] for chave, c in api.CULTURAS.items()}
    culturas = ["soja"] if api.MODO_DEMO else list(api.CULTURAS)
    cultura = escolhe_da_lista("Cultura", culturas, nomes_culturas, padrao=api.CULTURA_PADRAO)

    por_solo = api.zarc_por_solo(codigo_ibge, cultura)
    if por_solo is None:
        print(f"Essa cidade não tem zoneamento de {nomes_culturas[cultura].lower()}. Escolha outra cidade ou cultura.")
        return

    solo = escolhe_da_lista("Solo", api.ordena_solos(por_solo), padrao=api.SOLO_PADRAO)
    janelas = por_solo[solo]
    ciclo = escolhe_da_lista("Ciclo", api.ordena_ciclos(janelas))

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
    print("=" * 40)
    print()

    resultado = esta_na_janela(data_plantio, ciclo, janelas)

    nome_mes = meses[mes]
    decendio_ciclo = qual_decendio(data_plantio)
    janelas_ciclos = janelas[ciclo]
    primeiro_decendio = janelas_ciclos[0]
    ultimo_decendio = janelas_ciclos[-1]

    if resultado:
        print(f"✅ Plantio em {dia} de {nome_mes} de {ano} (decêndio {decendio_ciclo}) dentro da janela do Zarc !\n Ciclo {ciclo} aceitos: {janelas_ciclos}")

        _, faltam = situacao_na_janela(data_plantio, janelas_ciclos)
        if faltam == 0:
            print("⚠️ Você está no ÚLTIMO decêndio da janela!")
        else:
            print(f"⏳ Faltam {faltam} decêndios para o fim da janela")

    else:
        print(f"❌ Plantio em {dia} de {nome_mes} de {ano} (decêndio {decendio_ciclo}) fora da janela do Zarc {ciclo}!\n Ciclo {ciclo} aceitos: {janelas_ciclos}")
    
        status, faltam = situacao_na_janela(data_plantio, janelas_ciclos)
        if status == "antes":
            print(f"⏳ A janela abre em {faltam} decêndios")
        else:
            print("O ciclo desse ano ja passou")

    salvar_consulta(codigo_ibge, ciclo, data_plantio, resultado, cultura, solo)

    resposta = input("Quer fazer outra consulta? (s/n)")
    if resposta == "s":
        main()

    print()
    print("=" * 40)
    print()


def menu():
    while True:
        escolha = input("Escolha qual opçao deseja (1-> Nova Consulta,2-> Ver historico,3-> Comparar,4-> Ver estatisticas,5-> Exportar historico para Excel,6-> Analise financeira,7-> Otimizacao soja + safrinha,8-> O que e seguro plantar,9-> Saindo do menu)!")
        if escolha == "1":
            main()
        elif escolha == "2":
            mostrar_historico()
        elif escolha == "3":
            comparar_cidades()
        elif escolha == "4":
            mostrar_estatisticas()
        elif escolha == "5":
            exportar_excel()
        elif escolha == "6":
            analisar_financeiro()
        elif escolha == "7":
            analisar_otimizacao()
        elif escolha == "8":
            o_que_plantar()
        elif escolha == "9":
            print("Saindo do menu")
            break
        else:
            print("Opçao invalida")


if __name__ == "__main__":
    aviso_modo_demo()
    menu()