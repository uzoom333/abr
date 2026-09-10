from datetime import date
from comparacao import comparar_cidades
from zarc import qual_decendio, esta_na_janela, proximo_decendio_valido
from api import escolher_municipio, pega_zarc, aviso_modo_demo
from zarc import qual_decendio, esta_na_janela
from historico import salvar_consulta, mostrar_historico
from estatistica import mostrar_estatisticas

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

    janelas = pega_zarc(codigo_ibge)
    if janelas is None:
        print("Não foi possível obter os dados dessa cidade. Escolha outra.")
        return

    while True:
        ciclo = input("Qual ciclo da soja (precoce,medio,tardio) ? ").lower()
        if ciclo in janelas:
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

        faltam = ultimo_decendio - decendio_ciclo
        if faltam == 0:
            print("⚠️ Você está no ÚLTIMO decêndio da janela!")
        else:
            print(f"⏳ Faltam {faltam} decêndios para o fim da janela")

    else:
        print(f"❌ Plantio em {dia} de {nome_mes} de {ano} (decêndio {decendio_ciclo}) fora da janela do Zarc {ciclo}!\n Ciclo {ciclo} aceitos: {janelas_ciclos}")
    
        proximo = proximo_decendio_valido(decendio_ciclo, janelas_ciclos)
        if proximo is not None:
            faltam = proximo - decendio_ciclo
            print(f"⏳ A janela abre em {faltam} decêndios")
        else:
            print("O ciclo desse ano ja passou")

    salvar_consulta(codigo_ibge, ciclo, data_plantio, resultado)

    resposta = input("Quer fazer outra consulta? (s/n)")
    if resposta == "s":
        main()

    print()
    print("=" * 40)
    print()


def menu():
    while True:
        escolha = input("Escolha qual opçao deseja (1-> Nova Consulta,2-> Ver historico,3-> Comparar,4-> Ver estatisticas 5-> Saindo do menu)!")
        if escolha == "1":
            main()
        elif escolha == "2":
            mostrar_historico()
        elif escolha == "3":
            comparar_cidades()   
        elif escolha == "4":     
            mostrar_estatisticas()
        elif escolha == "5":
            print("Saindo do menu")
            break
        else:
            print("Opçao invalida")


if __name__ == "__main__":
    aviso_modo_demo()
    menu()