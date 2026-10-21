# Destaques dos documentos do RAG

O que cada documento tem de mais importante, com a página do `.txt` (o `=== página N ===`).
É daqui que saíram as perguntas do `avaliacao.csv`. Lido em 21/10/2026.

## portaria_soja_go_2026 (Portaria SPA/MAPA 198/2026)

- p.1: soja precisa de 450 a 800 mm por ciclo, pico de 7 a 8 mm/dia na floração; não cresce abaixo de 10 °C, ideal perto de 30 °C.
- p.1: balanço hídrico com no mínimo 15 anos de dados diários de 3.750 estações.
- p.2: ciclos simulados de 100, 115 e 130 dias, em 4 fases (estabelecimento, vegetativo, floração/enchimento, maturação).
- p.2: CAD por classe: AD1 24 mm, AD2 32, AD3 42, AD4 55, AD5 72, AD6 95 mm, com raiz efetiva de 60 cm.
- p.2: ISNA mínimo de 0,50 no estabelecimento e 0,55 na floração; risco de frio = mínima de 3 °C ou menos.
- p.2: município apto se pelo menos 20% da área cumpre os critérios; lavoura irrigada não fica presa às datas.
- p.2: não indicados: solos com menos de 0,5 m de profundidade e solos com mais de 15% de pedras.
- p.3: emergência esperada entre 5 e 10 dias; com 11 dias ou mais de atraso, vale o risco do decêndio anterior ao da emergência.

## portaria_milho2safra_go_2026 (Portaria SPA/MAPA 322/2026)

- p.1: ideal de 30 a 33 °C de dia e 17 a 23 °C à noite; noite acima de 24 °C prejudica o enchimento; acima de 700 m de altitude rende mais.
- p.2: modelo de balanço hídrico SARRA; 30 anos de dados (1992 a 2022); 3.935 séries de chuva + 193 do CHIRPS.
- p.2: grupos de ciclo: I até 110 dias, II de 110 a 130, III acima de 130.
- p.2: CAD por classe: 24; 31,8; 41,4; 54,6; 72,6 e 95,4 mm (quase igual à da soja, mas não igual).
- p.2: risco de frio = média abaixo de 18 °C no florescimento ou mínima abaixo de 2 °C; excesso de água = ISNA de 0,90 ou mais na maturação.

## classes_agua_disponivel_zarc (Embrapa)

- p.2: o ZARC entra em mais de 500 mil contratos de Proagro e PSR por ano; a seca é o principal risco.
- p.2: até 2021 eram só três "tipos" de solo, o que subestimava ou superestimava o risco.
- p.3: cada classe é 40% maior que a anterior, AD(n+1) = 1,40 × AD(n), para manter constante a diferença de risco.
- p.4: acima de 1,84 mm/cm vira AD6; abaixo de 0,34 mm/cm é AD0, área inapta.
- p.5: tabela com os limites das seis classes.

## nota_classes_solo_zarc_2023 (MAPA)

- p.1: classificação antiga por argila: tipo 1 de 10 a 15%, tipo 2 de 15 a 35%, tipo 3 com 35% ou mais.
- p.2: limites novos das seis classes (AD4 de 0,80 a 1,06 mm/cm); amostra de 0 a 40 cm (antes 0 a 50 cm).
- p.2: primeiras portarias com seis classes saíram em abril de 2023, para a soja 2023/2024.
- p.4: seguro (PSR) e Proagro da soja têm de seguir as seis classes.

## metodologia_zarc_milho (ZarcPro-Milho, Embrapa)

- p.6: considera 6 classes de AD, 3 ciclos, 3 níveis de risco e 10 níveis de produtividade esperada.
- p.10 e p.11: modelo CSM-CERES-Maize, da plataforma DSSAT; ponto de crescimento abaixo do solo até cerca de V3.
- p.13: o ZARC antigo usava 3 tipos de solo, com 30, 47 e 72 mm de água para raiz de 0,50 m.
- p.14: tabela das seis classes de AD (AD4 de 0,80 a 1,06); 80 genótipos em 20 municípios.
- p.18: só semeia se a umidade até 0,30 m passar de 80% (AD1) a 50% (AD6) da CAD; mínima de 3 °C mata a planta no modelo.
- p.19: 3 cultivares × 6 solos × 36 decêndios = 648 cenários, × 34 anos = 22.032 produtividades simuladas.
- p.20: risco = chance de produzir menos que o nível esperado; município apto se 20% da área cumpre o risco.

## ecofisiologia_milho_2safra (Embrapa, Doc. 273)

- p.5: 75% do milho do país vem da safrinha.
- p.7: milho de 120 dias consome de 400 a 600 mm.
- p.10: 2 dias de seca no florescimento tiram mais de 20%; 4 a 8 dias tiram mais de 50%.
- p.12: ideal de 25 a 28 °C de dia e 18 a 19 °C à noite; acima de 30 °C o pólen perde viabilidade.
- p.13: superprecoce abaixo de 825 graus-dia, precoce de 830 a 900, normal acima de 900.
- p.16: tabela de produtividade de 3 híbridos em 6 datas de semeadura (Sete Lagoas, 2016/17).
- p.17 e p.19: Sistema Antecipe semeia o milho até 20 dias antes de colher a soja; em Rio Verde, +86,5 kg/ha por dia antecipado.

## desenvolvimento_milho_2safra (Embrapa, Doc. 258)

- p.13: ponto de crescimento abaixo do solo em V3 e V4; em V6 já está acima, e dano ali não tem recuperação.
- p.14: maturidade fisiológica com 30 a 38% de umidade; colher com 18 a 25% (com secagem); armazenar com 13 a 15%.
- p.15: V3 cerca de 9 dias após a emergência, V4 12, V5 15, V6 18.
- p.24: graus-dia = ((máx + mín) / 2) − 10, com teto de 32 °C e piso de 10 °C; ciclos de 780 a 830, 831 a 890 e acima de 890.
- p.24: no ZARC, risco de 20/30/40% equivale a 80/70/60% de chance de boa safra.
- p.26: Antecipe começa no R5 da soja e antecipa o milho em até 20 dias.
- p.29: área de safrinha passou de 256 mil ha (1989/90) para 13,73 milhões ha (2019/20).

## conab_metodologia_custo (Norma CONAB 30.302)

- p.8: custo variável, custo fixo, custo operacional, renda de fatores e custo total.
- p.11: diesel = 12% da potência em CV (litros/h); filtros e lubrificantes = 10% do combustível.
- p.12: hora do operador = salário mensal / 220; manutenção = 1% do valor da máquina nova.
- p.17: custo = matriz de coeficientes técnicos × vetor de preços.
- p.27: renda de fatores usa a poupança como taxa de retorno; p.28: a terra própria rende metade dela.

## desempenho_semeadura_safrinha (Energia na Agricultura, 2021)

- p.1: semeadora de 28 linhas com 12 ha/h e 65,66% de eficiência (literatura: 50 a 75%).
- p.4: capacidade teórica = largura (m) × velocidade (km/h) / 10; eficiência = operacional / efetiva.
- p.5: o maior tempo perdido foi com manutenção.

## plantabilidade_embrapa (UFSM/Embrapa)

- p.5 e p.11: falha = espaço maior que 1,5 vez o ideal; duplo = menor que 0,5 vez.
- p.7: subir de 4 para 12 km/h não muda a população, mas reduz os espaçamentos aceitáveis.
- p.9 e p.10: perder perto de 25% das plantas não reduz a produtividade se solo e clima forem bons.
- p.12: semeadora atual não passa de 8 km/h com precisão; mecânica de 4 a 6 km/h, pneumática até 8.
- p.14 e p.15: até 4,8 km/h deu as maiores produtividades.

## Onde os documentos discordam

Servem para testar a geração: o certo é a resposta mostrar as duas fontes, não escolher uma.

| Assunto | Uma fonte diz | Outra diz |
|---|---|---|
| Soma térmica dos ciclos do milho | <825 / 830–900 / >900 GD (ecofisiologia p.13) | 780–830 / 831–890 / >890 GD (desenvolvimento p.24) |
| Temperatura ideal do milho | 25–28 °C dia, 18–19 °C noite (ecofisiologia p.12) | 30–33 °C dia, 17–23 °C noite (portaria milho p.1) |
| Ponto de crescimento abaixo do solo | até V5 (desenvolvimento p.13, p.26) | até V6 (ecofisiologia p.19); até ~V3 (ZarcPro p.10) |
| Anos de clima no ZARC | 15 anos no mínimo (portaria soja p.1) | 30 anos (portaria milho p.2); 34 anos (ZarcPro p.12) |

## Fora do avaliacao.csv

O `avaliar.py` não aceita pergunta sem local, então estas ficam anotadas aqui:

- **Fora da base (tipo 6):** "qual o preço da saca de soja em Rio Verde hoje?"; "qual a produtividade média de soja em Goiás em 2025?"
- **Dado da AgroAPI, não do RAG (tipo 7):** "posso plantar soja de ciclo médio em Jataí no dia 10/11?"; "em que decêndio abre a janela da soja em Rio Verde para solo AD3?"
