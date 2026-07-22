import csv
import os


def mostrar_estatisticas():
    """Lê o histórico.csv e mostra estatísticas de uso."""
    
    arquivo = "historico.csv"
    
    # 1. Verifica se arquivo existe
    if not os.path.exists(arquivo):
        print("Nenhuma consulta no historico ainda")
        return
    
    # 2. Contadores iniciais
    total = 0
    ciclos = {"precoce": 0, "medio": 0, "tardio": 0}
    dentro = 0
    fora = 0
    
    # 3. LÊ O CSV
    with open(arquivo, "r") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            total += 1
            
            # 3a. Conta por ciclo
            ciclo_atual = linha["ciclo"]
            if ciclo_atual in ciclos:
                ciclos[ciclo_atual] += 1
            
            # 3b. Conta dentro/fora
            if linha["resultado"] == "dentro":
                dentro += 1
            else:
                fora += 1
    
    # 4. SE SEM DADOS, PARA
    if total == 0:
        print("Nenhuma consulta no historico")
        return
    
    # 5. APRESENTAÇÃO (você preenche)
    print()
    print("="*40)
    print("📊 ESTATÍSTICAS DO HISTÓRICO")
    print("="*40)
    
    # 5a. Total
    print(f"\nTotal de consultas: {total}")
    
    # 5b. Ciclos com barras ASCII
    print("\n📈 Por ciclo:")
    for nome_ciclo, quantidade in ciclos.items():
        blocos = int((quantidade/total)*30)
        barra = "█" * blocos
        percentual = (quantidade / total) * 100
        print(f"{nome_ciclo:<10} {barra} {quantidade} ({percentual:.1f}%)")                                           # ← preenche aqui
    
    # 5c. Dentro/Fora com barras ASCII
    print("\n🎯 Resultado dos plantios:")
    # Bloco pro DENTRO
    blocos_dentro = int((dentro/total)*30)
    barra_dentro = "█" * blocos_dentro
    percentual_dentro = (dentro/total)*100
    print(f"dentro  {barra_dentro} {dentro} ({percentual_dentro:.1f}%)")
    # Bloco pro FORA
    blocos_fora = int((fora/total)*30)
    barra_fora = "█" * blocos_fora
    percentual_fora = (fora/total)*100
    print(f"fora    {barra_fora} {fora} ({percentual_fora:.1f}%)")                                             # ← preenche aqui
    
    print()
    print("="*40)