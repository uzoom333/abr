from api import escolher_municipio, pega_zarc, busca_municipios_go
from zarc import qual_decendio, esta_na_janela, proximo_decendio_valido
from zarc import qual_decendio, esta_na_janela
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
    
    # 7. PROCESSAMENTO — pra cada cidade escolhida
    resultados = []
    cidades_sem_zarc = []
    cidades_sem_ciclo = []

    decendio_data = qual_decendio(data_plantio)

    for codigo in codigos_escolhidos:
        janelas = pega_zarc(codigo)

        # 7a. Se pega_zarc retornou None → cidade sem ZARC
        if janelas is None:
            cidades_sem_zarc.append(codigo)
            continue

        # 7b. Se o ciclo escolhido não existe pra essa cidade
        if ciclo not in janelas:
            cidades_sem_ciclo.append(codigo)   # ← adiciona em cidades_sem_ciclo
            continue

        # 7c. Extrai a janela do ciclo
        janela_ciclo = janelas[ciclo]
        primeiro = janela_ciclo[0]
        ultimo = janela_ciclo[-1]

        # 7d. Descobre status + restantes
        if esta_na_janela(data_plantio, ciclo, janelas):
            status = "dentro"
            restantes = ultimo - decendio_data
        else:
            proximo = proximo_decendio_valido(decendio_data, janela_ciclo)
            if proximo is not None:
                status = "antes"
                restantes = proximo - decendio_data
            else:
                status = "passou"
                restantes = None

        # 7e. Adiciona ao resultado
        resultados.append({
            "codigo": codigo,
            "status": status,       # ← qual variável?""
            "restantes": restantes,    # ← qual variável?
        })
    # 8. BUSCAR NOMES DAS CIDADES
    todos_municipios = busca_municipios_go()
    
    def nome_por_codigo(codigo):
        for m in todos_municipios:
            if m["codigoIBGE"] == codigo:
                return m["nome"]
        return "?"
    
    # 9. SEPARAR POR STATUS
    dentro = [r for r in resultados if r["status"] == "dentro"]
    antes = [r for r in resultados if r["status"] == "antes"]
    passou = [r for r in resultados if r["status"] == "passou"]
    
    # 10. ORDENAR
    dentro.sort(key=lambda x: x["restantes"], reverse=True)   # mais tempo primeiro
    antes.sort(key=lambda x: x["restantes"])                   # menos tempo pra abrir primeiro
    
    # 11. APRESENTAR
    print()
    print("="*40)
    print(f"RESULTADO DA COMPARAÇÃO")
    print(f"Ciclo: {ciclo} | Data: {data_plantio}")
    print("="*40)
    
    if dentro:
        print("\n🟢 DENTRO DA JANELA")
        print("-"*40)
        for r in dentro:
            nome = nome_por_codigo(r["codigo"])                                          # ← usa nome_por_codigo
            print(f"- {nome} (restam {r['restantes']} decêndios)")
    
    if antes:
        print("\n🟡 JANELA AINDA VAI ABRIR")
        print("-"*40)
        for r in antes:
            nome = nome_por_codigo(r["codigo"])
            print(f"- {nome} (abre em {r['restantes']} decêndios)")
    
    if passou:
        print("\n🔴 JANELA JÁ PASSOU")
        print("-"*40)
        for r in passou:
            nome = nome_por_codigo(r["codigo"])
            print(f"- {nome}")
    
    if cidades_sem_zarc:
        print("\n⚠️ SEM ZONEAMENTO DISPONÍVEL")
        print("-"*40)
        for codigo in cidades_sem_zarc:
            nome = nome_por_codigo(codigo)
            print(f"- {nome} ({codigo})")
    
    if cidades_sem_ciclo:
        print(f"\n⚠️ SEM O CICLO '{ciclo}' DISPONÍVEL")
        print("-"*40)
        for codigo in cidades_sem_ciclo:
            nome = nome_por_codigo(codigo)
            print(f"- {nome} ({codigo})")
    
    print()
    print("="*40)
    