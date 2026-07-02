# ABR 

Sistema em linha de comando para consulta e validação de janelas de plantio de soja em Jataí (GO), com base nos dados oficiais do Zoneamento Agrícola de Risco Climático (ZARC) da Embrapa.

**Versão atual:** V1 — CLI com integração à AgroAPI (Embrapa)

---

## Motivação

Por volta de maio de 2026 acabei me inserindo, por diversão, no universo do agronegócio do meu estado — festas locais, feiras, conversas — e fui gostando do estilo de vida e da forma como as coisas funcionam ali. A partir disso, decidi conectar essa curiosidade nova com os estudos em Python e minha iniciação científica, colocando a mão na massa em algo funcional.

No começo, o ABR era apenas um preditor de ciclos de plantio. Mas ao longo do desenvolvimento surgiram muitas ideias novas — o roadmap abaixo dá uma noção do potencial que enxergo daqui pra frente, especialmente ao combinar Álgebra Linear, Programação Linear e IA aplicada a decisões agrícolas reais.

---

## Como funciona

O ABR permite ao usuário:

- Consultar a janela de plantio recomendada por ciclo (precoce, médio, tardio)
- Verificar se uma data específica está dentro da janela ZARC
- Consultar o histórico de todas as consultas realizadas
- Usar cache local para economizar chamadas à API (limite de 100 requisições/dia)

Os dados são buscados diretamente do endpoint `/zoneamento` da AgroAPI da Embrapa, filtrados para o município de Jataí (GO), cultura soja (id 60), solo AD2 e risco máximo de 20%.

---

## Tecnologias

- Python 3.12
- [requests](https://pypi.org/project/requests/) — chamadas HTTP à API
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variáveis de ambiente
- [AgroAPI Agritec v2](https://www.agroapi.cnptia.embrapa.br/) — dados oficiais do ZARC

---

## Como rodar localmente

```bash
# 1. Clonar o repositório
git clone https://github.com/uzoom333/abr.git
cd abr

# 2. Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install requests python-dotenv

# 4. Criar arquivo .env com seu Access Token da AgroAPI
echo "ACCESS_TOKEN=seu_token_aqui" > .env

# 5. Executar
python main.py
```

Para obter um token, é necessário se cadastrar no [portal da AgroAPI](https://www.agroapi.cnptia.embrapa.br/portal/).

---

## Estrutura do projeto

```
abr/
├── main.py              # CLI principal (menu, validações, histórico)
├── teste.api.py         # Script de testes da integração com a API
├── .gitignore
└── README.md
```

Arquivos gerados em tempo de execução (não versionados):
- `cache_zarc.json` — cache local dos dados da API
- `historico.csv` — registro das consultas do usuário
- `.env` — credenciais da API

---

## Roadmap

- **V2** — Expandir a cobertura para outras cidades de Goiás e incluir novas safras
- **V3** — Adicionar módulo de previsão de custos, integrando com o PPL da IC para recomendar qual safra plantar de acordo com as variáveis de decisão do produtor (maximizar lucro)
- **V4+** — Substituir consultas por modelos treinados de IA para tarefas de predição mais precisas, evoluindo de consultas de API para modelagem própria
- **Longo prazo** — Interface web, validação com produtores reais e possível aplicação de otimização quântica em problemas de escala maior

O ritmo dessas versões depende diretamente do aprofundamento dos meus estudos em Álgebra Linear, Programação Linear e IA — o projeto cresce conforme a base teórica avança.

---

## Fontes de dados

- [Portal ZARC — Ministério da Agricultura](https://mapa-indicadores.agricultura.gov.br/publico/extensions/Zarc/Zarc.html)
- [AgroAPI Agritec — Embrapa](https://www.agroapi.cnptia.embrapa.br/)

---

## Autor

**Renato Morais Mundim Filho**

Estudante de Ciência da Computação na PUC-GO (6º período), com foco em Computação Quântica — atualmente minha área de maior interesse. Em paralelo, estudo Álgebra Linear e Programação Linear através de um projeto de iniciação científica na faculdade, aplicando esses conceitos em Python. Também estudo IA, ainda em nível básico.

Próximos objetivos técnicos: aprofundar em Django, APIs e banco de dados.

- [LinkedIn](https://www.linkedin.com/in/renato-morais-mundim-filho-88919238b/)
- [GitHub](https://github.com/uzoom333)

---

## Licença

MIT
