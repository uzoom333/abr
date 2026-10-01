"""Planejamento de soja + milho safrinha por Programação Linear (ABR V3).

Modelo, com o tempo no ano-safra (t = 1 é o 1º decêndio de setembro):

  Índices   p = talhão (cidade, solo)   c = ciclo da soja   t = decêndio, 1..36

  Variáveis (contínuas, >= 0)
    xs[p,c,t]  ha de soja do ciclo c plantados em t   (só existe onde o ZARC permite)
    xm[p,t]    ha de milho safrinha plantados em t     (só existe onde o ZARC permite)
    e[p,t]     ha de soja já colhida e ainda sem milho, no fim de t

  max  Σ ls[c]·xs[p,c,t]  +  Σ lm[p,t]·xm[p,t]

  s.a. Σ_c Σ_t xs[p,c,t] <= area[p]                          para cada p   (área)
       Σ_p Σ_c xs[p,c,t] + Σ_p xm[p,t] <= cap                para cada t   (plantadeira)
       e[p,t] = e[p,t-1] + Σ_c xs[p,c,t-L[c]-k] - xm[p,t]    para cada p,t (sucessão)
       e[p,0] = 0

O ZARC entra fixando quais variáveis existem (bloco 3, ex. 4), então não vira restrição.
Colheita e plantio usam equipes diferentes, por isso há uma só restrição de capacidade.
"""

import pulp

from api import escolher_municipio, busca_municipios_go, zarc_soja_por_solo, zarc_milho_por_solo
from financeiro import pede_valor_positivo, CICLOS
from zarc import para_ano_safra, para_calendario, nome_decendio


# ============================================
# HIPÓTESES (conferir e ajustar)
# ============================================

# Duração do plantio à colheita, em decêndios. A portaria do ZARC da soja em GO
# (SPA/MAPA 198/2026, item 1.9.2) simula ciclos de 100, 115 e 130 dias; 115 dias
# arredonda para cima porque a área só libera depois da colheita.
DURACAO_CICLO = {"precoce": 10, "medio": 12, "tardio": 13}

# k: decêndios entre colher a soja e a área estar pronta para o milho.
INTERVALO_COLHEITA_MILHO = 1

# Produtividade do milho cai a cada decêndio de atraso em relação ao início da janela.
# A Embrapa cita ~38 kg/ha por dia de atraso em Rio Verde a partir de 15/01, perto de
# 6% por decêndio para 110 sc/ha. Ficou 5% até conferir na fonte.
PERDA_MILHO_POR_DECENDIO = 0.05

# Plantadeira padrão: 12 linhas a 0,5 m, 6 km/h, 70% de eficiência de campo,
# 10 h por dia, 8 dias úteis por decêndio (2 perdidos para chuva).
PLANTADEIRA_PADRAO = {"largura_m": 6, "velocidade_kmh": 6, "eficiencia": 0.70,
                      "horas_dia": 10, "dias_uteis": 8}


def capacidade_plantadeira(largura_m, velocidade_kmh, eficiencia, horas_dia, dias_uteis):
    """Hectares que a plantadeira planta num decêndio."""
    ha_por_hora = largura_m * velocidade_kmh * eficiencia / 10
    return ha_por_hora * horas_dia * dias_uteis


def lucro_milho_por_decendio(janela, produtividade, preco_saca, custo_ha):
    """{t: lucro/ha}. Quanto mais longe do início da janela, menor a produtividade."""
    inicio = min(janela)
    lucros = {}
    for t in janela:
        atraso = t - inicio
        produtividade_t = produtividade * max(0, 1 - PERDA_MILHO_POR_DECENDIO * atraso)
        lucros[t] = produtividade_t * preco_saca - custo_ha
    return lucros


# ============================================
# MODELO
# ============================================

def monta_modelo(talhoes, cap, duracao=DURACAO_CICLO, k=INTERVALO_COLHEITA_MILHO):
    """Monta a PL. Cada talhão é um dict com:
         nome, area, janelas_soja {ciclo: [t]}, lucro_soja {ciclo: R$/ha}, lucro_milho {t: R$/ha}
       Retorna o modelo e as variáveis/restrições que o relatório precisa."""
    modelo = pulp.LpProblem("abr_soja_safrinha", pulp.LpMaximize)
    T = range(1, 37)

    xs, xm, e = {}, {}, {}
    for p, talhao in enumerate(talhoes):
        for c, janela in talhao["janelas_soja"].items():
            for t in janela:
                xs[p, c, t] = pulp.LpVariable(f"xs_{p}_{c}_{t}", lowBound=0)
        for t in talhao["lucro_milho"]:
            xm[p, t] = pulp.LpVariable(f"xm_{p}_{t}", lowBound=0)
        for t in T:
            e[p, t] = pulp.LpVariable(f"e_{p}_{t}", lowBound=0)

    # Objetivo: lucro da soja + lucro do milho
    modelo += (
        pulp.lpSum(talhoes[p]["lucro_soja"][c] * x for (p, c, t), x in xs.items())
        + pulp.lpSum(talhoes[p]["lucro_milho"][t] * x for (p, t), x in xm.items())
    )

    # Área: não planto mais soja do que o talhão tem
    restricoes_area = {}
    for p, talhao in enumerate(talhoes):
        r = pulp.lpSum(x for (q, c, t), x in xs.items() if q == p) <= talhao["area"]
        modelo += r, f"area_{p}"
        restricoes_area[p] = f"area_{p}"

    # Plantadeira: em cada decêndio, soja + milho plantados cabem na capacidade
    restricoes_cap = {}
    for t in T:
        plantado = ([x for (p, c, s), x in xs.items() if s == t]
                    + [x for (p, s), x in xm.items() if s == t])
        if plantado:
            modelo += pulp.lpSum(plantado) <= cap, f"cap_{t}"
            restricoes_cap[t] = f"cap_{t}"

    # Sucessão: só planto milho em área de soja já colhida (e >= 0 garante isso)
    for p in range(len(talhoes)):
        for t in T:
            liberada = pulp.lpSum(xs[p, c, t - duracao[c] - k] for c in duracao
                                  if (p, c, t - duracao[c] - k) in xs)
            anterior = e[p, t - 1] if t > 1 else 0
            milho = xm.get((p, t), 0)
            modelo += e[p, t] == anterior + liberada - milho, f"sucessao_{p}_{t}"

    return modelo, xs, xm, e, restricoes_area, restricoes_cap


def resolve(talhoes, cap):
    """Resolve e devolve o plano num dict simples (fácil de imprimir ou salvar em JSON)."""
    modelo, xs, xm, e, restricoes_area, restricoes_cap = monta_modelo(talhoes, cap)
    modelo.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[modelo.status]
    if status != "Optimal":
        return {"status": status}

    plano = []
    for p, talhao in enumerate(talhoes):
        soja = [(c, t, x.value()) for (q, c, t), x in xs.items() if q == p and x.value() > 1e-6]
        milho = [(t, x.value()) for (q, t), x in xm.items() if q == p and x.value() > 1e-6]
        area_soja = sum(ha for _, _, ha in soja)
        plano.append({
            "talhao": talhao["nome"],
            "area": talhao["area"],
            "soja": sorted(soja, key=lambda s: s[1]),
            "milho": sorted(milho),
            "sem_milho": e[p, 36].value(),
            "parada": talhao["area"] - area_soja,
            "preco_sombra_area": modelo.constraints[restricoes_area[p]].pi,
        })

    gargalos = []
    for t, nome in restricoes_cap.items():
        pi = modelo.constraints[nome].pi
        if pi and pi > 1e-6:
            gargalos.append((t, pi))

    return {
        "status": status,
        "lucro_total": pulp.value(modelo.objective),
        "cap": cap,
        "plano": plano,
        "gargalos_plantadeira": gargalos,
    }


# ============================================
# RELATÓRIO
# ============================================

def texto_t(t):
    return nome_decendio(para_calendario(t))


def mostra_resultado(resultado):
    print()
    print("=" * 40)
    if resultado["status"] != "Optimal":
        print(f"O solver não achou solução ótima (status: {resultado['status']}).")
        print("=" * 40)
        return

    print(f"PLANO ÓTIMO — lucro total R$ {resultado['lucro_total']:,.2f}")
    print(f"Plantadeira: {resultado['cap']:.0f} ha por decêndio")
    print("=" * 40)

    for item in resultado["plano"]:
        print(f"\n🌱 {item['talhao']} — {item['area']:.0f} ha")
        if not item["soja"]:
            print("   Soja: não compensa plantar aqui")
        for c, t, ha in item["soja"]:
            print(f"   Soja {c}: {ha:.0f} ha no {texto_t(t)}")
        for t, ha in item["milho"]:
            print(f"   Milho safrinha: {ha:.0f} ha no {texto_t(t)}")
        if item["sem_milho"] > 0.5:
            print(f"   Colhida sem milho depois: {item['sem_milho']:.0f} ha")
        if item["parada"] > 0.5:
            print(f"   Área sem plantio: {item['parada']:.0f} ha")

    print("\n" + "-" * 40)
    print("PREÇOS-SOMBRA (quanto vale afrouxar cada limite)")
    print("-" * 40)
    for item in resultado["plano"]:
        print(f"Área em {item['talhao']}: +1 ha valeria R$ {item['preco_sombra_area']:.2f}")
    if resultado["gargalos_plantadeira"]:
        for t, pi in resultado["gargalos_plantadeira"]:
            print(f"Plantadeira no {texto_t(t)}: +1 ha de capacidade valeria R$ {pi:.2f}")
    else:
        print("A plantadeira não é gargalo em nenhum decêndio.")

    print()
    print("Nota: com empates de lucro o solver escolhe um dos planos ótimos (bloco 3, 3.5),")
    print("e num vértice degenerado o preço-sombra vale só para um lado.")
    print("=" * 40)
    print()


# ============================================
# FLUXO DA CLI
# ============================================

def pede_valor_com_padrao(mensagem, padrao):
    """Como pede_valor_positivo, mas Enter aceita o padrão."""
    while True:
        texto = input(f"{mensagem} [{padrao}]: ").strip().replace(",", ".")
        if texto == "":
            return padrao
        try:
            valor = float(texto)
            if valor > 0:
                return valor
            print("Digite um valor maior que zero")
        except ValueError:
            print("Valor inválido")


def pede_solos(solos_disponiveis):
    """Divide a área entre os solos. Ex.: 'AD2:60 AD4:40'. Enter = tudo no primeiro solo."""
    padrao = "AD2" if "AD2" in solos_disponiveis else solos_disponiveis[0]
    while True:
        texto = input(f"  Solos em % (disponíveis: {', '.join(solos_disponiveis)}) [{padrao}:100]: ").strip()
        if texto == "":
            return {padrao: 1.0}
        try:
            partes = {}
            for pedaco in texto.split():
                solo, pct = pedaco.split(":")
                partes[solo.upper()] = float(pct) / 100
        except ValueError:
            print("  Formato: AD2:60 AD4:40")
            continue
        fora = [s for s in partes if s not in solos_disponiveis]
        if fora:
            print(f"  O ZARC não tem janela para {', '.join(fora)} nessa cidade")
            continue
        if abs(sum(partes.values()) - 1) > 0.001:
            print("  As porcentagens precisam somar 100")
            continue
        return partes


def analisar_otimizacao():
    """Plano de soja + milho safrinha que maximiza o lucro do ano-safra."""
    print()
    print("=" * 40)
    print(">> Otimização soja + milho safrinha (PL)")
    print("=" * 40)
    print()
    print("Valores são estimativas suas; o ABR não busca preço nem custo real.")
    print()

    print("SOJA")
    custo_soja = pede_valor_positivo("  Custo por hectare (R$/ha): ")
    preco_soja = pede_valor_positivo("  Preço da saca de 60 kg (R$/saca): ")
    prod_soja = {}
    for c in CICLOS:
        prod_soja[c] = pede_valor_positivo(f"  Produtividade {c} (sc/ha): ")
    lucro_soja = {c: prod_soja[c] * preco_soja - custo_soja for c in CICLOS}

    print("\nMILHO SAFRINHA")
    custo_milho = pede_valor_positivo("  Custo por hectare (R$/ha): ")
    preco_milho = pede_valor_positivo("  Preço da saca de 60 kg (R$/saca): ")
    prod_milho = pede_valor_positivo("  Produtividade no início da janela (sc/ha): ")

    print("\nPLANTADEIRA (Enter aceita o padrão)")
    maquina = {}
    for campo, rotulo in [("largura_m", "Largura de trabalho (m)"),
                          ("velocidade_kmh", "Velocidade (km/h)"),
                          ("eficiencia", "Eficiência de campo (0 a 1)"),
                          ("horas_dia", "Horas por dia"),
                          ("dias_uteis", "Dias úteis por decêndio")]:
        maquina[campo] = pede_valor_com_padrao(f"  {rotulo}", PLANTADEIRA_PADRAO[campo])
    cap = capacidade_plantadeira(**maquina)
    print(f"  → {cap:.0f} ha por decêndio")

    nomes = {m["codigoIBGE"]: m["nome"] for m in busca_municipios_go()}
    talhoes = []
    codigos = []
    print("\nCIDADES (até 10)")
    while len(codigos) < 10:
        codigo = escolher_municipio()
        if codigo is None or codigo in codigos:
            if input("Tentar outra cidade? (s/n) ").lower() != "s":
                break
            continue

        soja = zarc_soja_por_solo(codigo)
        milho = zarc_milho_por_solo(codigo)
        if not soja:
            print(f"⚠️ {nomes[codigo]}: sem zoneamento de soja, pulando.")
            continue
        codigos.append(codigo)

        area = pede_valor_positivo(f"  Área total em {nomes[codigo]} (ha): ")
        divisao = pede_solos(sorted(soja))
        for solo, fracao in divisao.items():
            janela_milho = [para_ano_safra(d) for d in (milho or {}).get(solo, [])]
            if not janela_milho:
                print(f"  ⚠️ Sem janela de milho para {solo}: esse talhão fica só com soja.")
            talhoes.append({
                "nome": f"{nomes[codigo]} ({solo})",
                "area": area * fracao,
                "janelas_soja": {c: [para_ano_safra(d) for d in ds] for c, ds in soja[solo].items()},
                "lucro_soja": lucro_soja,
                "lucro_milho": lucro_milho_por_decendio(janela_milho, prod_milho, preco_milho, custo_milho)
                               if janela_milho else {},
            })

        if input("Adicionar mais uma cidade? (s/n) ").lower() != "s":
            break

    if not talhoes:
        print("Nenhuma cidade escolhida. Voltando ao menu.")
        return

    mostra_resultado(resolve(talhoes, cap))
