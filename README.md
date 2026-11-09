# ABR

ABR is an agricultural decision-support command-line application that uses official Brazilian Agricultural Climate Risk Zoning (ZARC) data to evaluate soybean planting windows in Goiás.

## Project Overview

The application connects to Embrapa's AgroAPI, searches municipalities in Goiás, and checks a proposed planting date against the available ZARC windows for early-, medium-, or late-cycle soybeans. It is an educational software project: its output supports exploration of public zoning data and does not replace professional agronomic advice.

Current features (V2) include:

- support for every municipality in Goiás (245 with an API token; five bundled in demo mode);
- planting-window checks by soybean cycle and date;
- comparison between cities, up to ten at a time;
- local query history;
- usage statistics over the history, with ASCII charts;
- export of the history to Excel (`.xlsx`);
- local caching to reduce API calls.

In progress (V3):

- a linear program that plans soybean and second-crop corn planting (see below);
- a RAG over public agricultural documents, with retrieval measured against a 31-question answer key (see below).

## Motivation

In 2026, curiosity about agriculture in Goiás led me to connect a new area of interest with my Python studies and undergraduate research. ABR began as a small planting-cycle checker and became a practical exercise in API integration, data interpretation, command-line design, and decision-support software.

The project is intentionally evolving alongside my studies in Linear Algebra, mathematical optimization, scientific computing, and data analysis.

## Data and Decision Logic

ABR requests zoning records from the AgroAPI Agritec v2 `/zoneamento` endpoint. The current query uses soybeans (`idCultura=60`), a maximum risk level of 20%, and AD2 soil records. Calendar dates are mapped to ten-day periods (*decêndios*) before being compared with the zoning windows returned by the API.

The underlying records come from an external public service and may be unavailable, revised, or incomplete. Always consult the official ZARC publications for decisions with real agricultural consequences.

## Technologies

- Python 3.12
- [Requests](https://pypi.org/project/requests/) for HTTP requests
- [python-dotenv](https://pypi.org/project/python-dotenv/) for local environment configuration
- [openpyxl](https://pypi.org/project/openpyxl/) for Excel export
- [AgroAPI Agritec v2](https://www.agroapi.cnptia.embrapa.br/) for ZARC data

## Installation

### Quick start — demo mode (no credentials needed)

ABR ships with a small set of real ZARC records under `demo/`, so the application
runs immediately after cloning. No `.env`, no API token, no registration:

```bash
git clone https://github.com/uzoom333/abr.git
cd abr

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python main.py
```

When no valid `ACCESS_TOKEN` is found, ABR starts in **demo mode** and prints a
notice at startup. Every feature works — municipality search, planting-window
checks, comparison, history, statistics, and Excel export — but the data is limited to the
municipalities bundled in `demo/`:

| IBGE code | Municipality |
|-----------|--------------|
| 5208509   | Goiandira    |
| 5208707   | Goiânia      |
| 5209705   | Hidrolândia  |
| 5211909   | Jataí        |
| 5218805   | Rio Verde    |

These are real records retrieved from the AgroAPI, not synthetic values, and they
are a frozen snapshot: they are not refreshed and may fall behind the official
publications. Searching for any other municipality returns no results in demo mode.

### Full installation (all 245 municipalities in Goiás)

For live data across the whole state, provide an AgroAPI token as described below.
As soon as a valid `ACCESS_TOKEN` is present, ABR leaves demo mode automatically
and queries the API — no flags or code changes required.

```bash
git clone https://github.com/uzoom333/abr.git
cd abr

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Create a `.env` file in the repository root:

```text
ACCESS_TOKEN=your_agroapi_token
```

An access token is available after registration in the [AgroAPI portal](https://www.agroapi.cnptia.embrapa.br/portal/). Never commit this token.

## Running the CLI

```bash
python main.py
```

The interactive menu provides a new planting-window query, query history, municipality comparison, history statistics, and Excel export.

### Soybean + second-crop corn optimization (in progress)

Menu option 7 builds a linear program (`otimizacao.py`, solved with PuLP/CBC) that plans soybean
planting by cycle and ten-day period and the second-crop corn (*milho safrinha*) that follows it,
over one crop year, maximizing profit. It covers several cities and soil classes (AD1–AD6), a
planter-capacity limit per ten-day period, and soybean → corn succession modelled as a flow balance.
The report shows the plan and the shadow prices of each binding limit.

Assumptions still to be checked are grouped at the top of `otimizacao.py` (cycle lengths, the
harvest-to-planting gap, corn yield loss per ten-day delay, default planter). In demo mode the corn
windows in `demo/demo_zarc_milho.json` are **illustrative, written by hand, not AgroAPI records**.
With a token, set `ID_CULTURA_MILHO` in `.env` to the AgroAPI id for second-crop corn.

`python teste_otimizacao.py` checks the model against a small instance solvable by hand.

### Document search and answers with citations — RAG (in progress)

`rag/` is a RAG over 10 public documents: the ZARC ordinances for soybean and second-crop corn in
Goiás, Embrapa and MAPA notes on the six soil classes, the ZarcPro-Milho methodology, CONAB's
production-cost methodology, and planter performance studies. The goal is to explain the
optimizer's output with citations to the document and page. The sources are listed in
`rag/fontes.csv`.

How it works:

1. `baixar.py` downloads the PDFs and `extrair.py` turns them into text, one block per page.
2. `indexar.py` splits each page into 150-word chunks, adds the document title to each chunk and
   computes embeddings with `intfloat/multilingual-e5-small`.
3. `buscar.py` has three searches: vector (cosine similarity), BM25 (`rank_bm25`) and hybrid
   (reciprocal rank fusion of the two).
4. `avaliar.py` measures hit@5 against `avaliacao.csv`: 31 questions, each with the file and page
   where the answer is. A hit means one of the five chunks returned is from one of those pages.
5. `responder.py` sends the question and the retrieved chunks to a local LLM through Ollama and asks
   for an answer citing document and page.

Retrieval results (hit@5, 31 questions):

| Search  | hit@5 |
|---------|-------|
| Vector  | 28/31 |
| BM25    | 25/31 |
| Hybrid  | 26/31 |

Adding the document title to each chunk was the change that brought vector search to 28/31.
Answer generation works end to end but has not been evaluated yet: in early tests the model
sometimes cites the wrong page.

Run from the repository root:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU-only torch, much smaller
python rag/baixar.py     # download the PDFs listed in rag/fontes.csv
python rag/extrair.py    # PDF -> text, one block per page (needs poppler's pdftotext)
python rag/indexar.py    # chunks + embeddings
python rag/buscar.py "qual a duração dos ciclos da soja no ZARC?"
python rag/avaliar.py    # hit@5 of the three searches
python rag/responder.py "quantos anos de dados o ZARC do milho usa?"   # needs `ollama serve`
```

Exporting writes a `historico_YYYY-MM-DD_HH-MM.xlsx` file in the repository root. These files are generated artefacts and are not tracked by Git.

## Repository Structure

```text
abr/
├── main.py           # Interactive menu and planting-window workflow
├── api.py            # Municipality and ZARC API integration
├── zarc.py           # Date and ten-day-period calculations
├── comparacao.py     # Municipality comparison workflow
├── historico.py      # Local query history
├── estatistica.py    # Summary statistics and ASCII charts
├── exportacao.py     # Excel export of the query history
├── financeiro.py     # Profit comparison by city and cycle
├── otimizacao.py     # Linear program: soybean + second-crop corn plan
├── teste_otimizacao.py # Hand-checkable test of the linear program
├── rag/              # RAG: download, extraction, index, three searches, hit@5 evaluation, answers via Ollama
├── demo/             # Bundled sample data used when no API token is present
├── teste.api.py      # Standalone API exploration script
├── requirements.txt  # Python dependencies
├── bugs.md           # Maintainer notes for known issues
└── README.md
```

Runtime files such as `.env`, API caches, query-history CSV files, and generated `.xlsx` exports are excluded from version control.

## Roadmap

- broaden crop, harvest-season, soil, and risk-level support;
- improve automated testing and error handling around the external API;
- explore cost models and mathematical optimization for agricultural decisions;
- consider a web interface after the command-line workflow is stable;
- validate future decision-support assumptions with domain specialists.

These are directions for future study, not completed features.

## Data Sources

- [ZARC portal — Brazilian Ministry of Agriculture](https://mapa-indicadores.agricultura.gov.br/publico/extensions/Zarc/Zarc.html)
- [AgroAPI Agritec — Embrapa](https://www.agroapi.cnptia.embrapa.br/)

## Author

Renato Morais Mundim Filho — Computer Science student and undergraduate researcher at PUC Goiás.

- [GitHub](https://github.com/uzoom333)
- [LinkedIn](https://www.linkedin.com/in/renato-morais-mundim-filho-88919238b/)

## License

This project is distributed under the MIT License.
