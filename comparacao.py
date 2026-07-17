from api import escolher_municipio, pega_zarc
from zarc import qual_decendio
from datetime import date

def comparar_cidades():
    """Compara janela ZARC de várias cidades pra uma data e ciclo."""
    
    print()
    print("="*40)
    print(">> Comparação entre cidades")
    print("="*40)
    print()
    
    # 1. VALIDAR CICLO
    ciclos_validos = ["precoce", "medio", "tardio"]

    while True:
        ciclo = input("Qual ciclo da soja (precoce,medio,tardio) ? ").lower()
        if ciclo in ciclos_validos:
            break
        else:
            print("Invalido, tente novamente")
    
    # 2. VALIDAR DIA
    while True:
        try:
            dia = int(input("Qual dia você quer plantar? "))
            break
        except ValueError:
            print("Dia invalido")
    
    # 3. VLIDAR MÊS
    while True:
        try:
            mes = int(input("Qual mes? (1-12) "))
            if 1 <= mes <= 12:
                break
            print("Mes fora do intervalo")
        except ValueError:
            print("Digite um numero")
    
    # 4. VALIDAR ANO
    while True:
        try:
            ano = int(input("Qual ano voce deseja plantar?(2024-2030) "))
            if ano < 2024 or ano > 2030:
                print("Ano fora do ciclo do Zarc")
                continue
            break
        except ValueError:
            print("Data inválida")
    
    # 5. CRIAR data_plantio com try/except
    try:
        data_plantio = date(ano, mes, dia)
    except ValueError:
        print("Data inválida ")
        return
    
    # 6. LOOP DE ESCOLHA DE CIDADES
    codigos_escolhidos = []                          # ← 4 espaços
    LIMITE_CIDADES = 10                              # ← 4 espaços
    
    while len(codigos_escolhidos) < LIMITE_CIDADES:  # ← 4 espaços
        codigo = escolher_municipio()                 # ← 8 espaços
        if codigo is None:
            continuar = input("Nenhuma...").lower()            
            if continuar == "n":
                break
            continue
        
        if codigo in codigos_escolhidos:
            print("Você já escolheu essa cidade.")
            continue
        
        codigos_escolhidos.append(codigo)
        print(f"✓ Adicionada. Total: {len(codigos_escolhidos)}")
        
        if len(codigos_escolhidos) >= LIMITE_CIDADES:
            print("Limite de 10 cidades atingido.")
            break
        
        mais = input("Adicionar mais uma cidade? (s/n) ").lower()
        if mais != "s":
            break
    
    # DEPOIS DO WHILE (fora), verificação de vazio
    if not codigos_escolhidos:
        print("Nenhuma cidade escolhida. Voltando ao menu.")
        return
    
    # TESTE TEMPORÁRIO
    print(codigos_escolhidos)
    