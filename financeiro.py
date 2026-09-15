from datetime import date

from api import escolher_municipio, pega_zarc, busca_municipios_go
from zarc import qual_decendio, esta_na_janela, proximo_decendio_valido

CICLOS = ["precoce", "medio", "tardio"]


def pede_valor_positivo(mensagem):
    """Pede um número (aceita vírgula decimal) maior que zero."""
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
            if valor <= 0:
                print("Digite um valor maior que zero")
                continue
            return valor
        except ValueError:
            print("Valor inválido")


def pede_data_referencia():
    while True:
        try:
            dia = int(input("Dia de referência para o plantio? "))
            break
        except ValueError:
            print("Dia inválido")

    while True:
        try:
            mes = int(input("Mês? (1-12) "))
            if 1 <= mes <= 12:
                break
            print("Mês fora do intervalo")
        except ValueError:
            print("Digite um número")

    while True:
        try:
            ano = int(input("Ano? (2024-2030) "))
            if ano < 2024 or ano > 2030:
                print("Ano fora do ciclo do Zarc")
                continue
            break
        except ValueError:
            print("Data inválida")

    try:
        return date(ano, mes, dia)
    except ValueError:
        print("Data inválida")
        return None


def status_janela(data_ref, ciclo, janelas):
    """Status da janela pro ciclo numa data: 'dentro', 'antes' ou 'passou'."""
    janela_ciclo = janelas.get(ciclo)
    if not janela_ciclo:
        return None, None

    decendio_data = qual_decendio(data_ref)

    if esta_na_janela(data_ref, ciclo, janelas):
        restantes = janela_ciclo[-1] - decendio_data
        return "dentro", restantes

    proximo = proximo_decendio_valido(decendio_data, janela_ciclo)
    if proximo is not None:
        return "antes", proximo - decendio_data

    return "passou", None


def calcula_opcoes_cidade(codigo, nome, data_ref, custo_ha, preco_saca, produtividade_por_ciclo):
    """Retorna uma linha de análise financeira por ciclo disponível na cidade."""
    janelas = pega_zarc(codigo)
    if janelas is None:
        return []

    opcoes = []
    for ciclo in CICLOS:
        if ciclo not in janelas:
            continue

        status, decendios = status_janela(data_ref, ciclo, janelas)
        produtividade = produtividade_por_ciclo[ciclo]
        lucro_bruto = produtividade * preco_saca
        lucro_liquido = lucro_bruto - custo_ha

        opcoes.append({
            "codigo": codigo,
            "cidade": nome,
            "ciclo": ciclo,
            "status": status,
            "decendios": decendios,
            "produtividade": produtividade,
            "lucro_bruto": lucro_bruto,
            "lucro_liquido": lucro_liquido,
        })

    return opcoes


def analisar_financeiro():
    """Compara cidades e ciclos de plantio pelo lucro líquido estimado."""

    print()
    print("=" * 40)
    print(">> Análise financeira de plantio")
    print("=" * 40)
    print()
    print("Informe os custos e a produtividade esperada.")
    print("Esses valores são estimativas suas — o ABR não busca preço de mercado nem custo real.")
    print()

    custo_ha = pede_valor_positivo("Custo de produção por hectare (R$/ha): ")
    preco_saca = pede_valor_positivo("Preço de venda da saca de 60kg (R$/saca): ")

    print()
    print("Produtividade esperada por ciclo (sc/ha) — varia porque cada ciclo tem potencial diferente:")
    produtividade_por_ciclo = {}
    for ciclo in CICLOS:
        produtividade_por_ciclo[ciclo] = pede_valor_positivo(f"  {ciclo}: ")

    print()
    data_ref = pede_data_referencia()
    if data_ref is None:
        return

    codigos_escolhidos = []
    LIMITE_CIDADES = 10

    print()
    print("Escolha as cidades para comparar (até 10).")
    while len(codigos_escolhidos) < LIMITE_CIDADES:
        codigo = escolher_municipio()
        if codigo is None:
            continuar = input("Nenhuma cidade encontrada. Tentar de novo? (s/n) ").lower()
            if continuar != "s":
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

    if not codigos_escolhidos:
        print("Nenhuma cidade escolhida. Voltando ao menu.")
        return

    todos_municipios = busca_municipios_go()

    def nome_por_codigo(codigo):
        for m in todos_municipios:
            if m["codigoIBGE"] == codigo:
                return m["nome"]
        return "?"

    todas_opcoes = []
    for codigo in codigos_escolhidos:
        nome = nome_por_codigo(codigo)
        opcoes = calcula_opcoes_cidade(codigo, nome, data_ref, custo_ha, preco_saca, produtividade_por_ciclo)
        if not opcoes:
            print(f"⚠️ {nome}: sem zoneamento disponível, pulando.")
        todas_opcoes.extend(opcoes)

    if not todas_opcoes:
        print("Nenhuma opção encontrada pras cidades escolhidas.")
        return

    viaveis = [o for o in todas_opcoes if o["status"] != "passou"]
    passadas = [o for o in todas_opcoes if o["status"] == "passou"]

    prioridade_status = {"dentro": 0, "antes": 1}
    viaveis.sort(key=lambda o: (
        -o["lucro_liquido"],
        prioridade_status.get(o["status"], 2),
        o["decendios"] if o["decendios"] is not None else 999,
    ))

    print()
    print("=" * 40)
    print(f"RANKING FINANCEIRO — data de referência {data_ref}")
    print(f"Custo: R$ {custo_ha:.2f}/ha | Saca: R$ {preco_saca:.2f}")
    print("=" * 40)

    if viaveis:
        print("\n💰 OPÇÕES VIÁVEIS (melhor lucro líquido primeiro)")
        print("-" * 40)
        for i, o in enumerate(viaveis, start=1):
            emoji = "🟢" if o["status"] == "dentro" else "🟡"
            situacao = "janela aberta agora" if o["status"] == "dentro" else f"abre em {o['decendios']} decêndios"
            print(
                f"{i}. {emoji} {o['cidade']} — ciclo {o['ciclo']} "
                f"({situacao})\n"
                f"   Produtividade: {o['produtividade']:.1f} sc/ha | "
                f"Lucro bruto: R$ {o['lucro_bruto']:.2f}/ha | "
                f"Lucro líquido: R$ {o['lucro_liquido']:.2f}/ha"
            )

    if passadas:
        print("\n🔴 JANELA JÁ PASSOU (não recomendado para este ciclo/ano)")
        print("-" * 40)
        for o in passadas:
            print(f"- {o['cidade']} — ciclo {o['ciclo']}")

    print()
    print("=" * 40)
    print("Nota: o lucro considera só custo/ha e preço informados — não inclui frete,")
    print("impostos, financiamento nem risco climático além do que o Zarc já filtra.")
    print("=" * 40)
    print()
