# ABR

ABR is an agricultural decision-support application (command line and web page) that uses official Brazilian Agricultural Climate Risk Zoning (ZARC) data to evaluate planting windows for nine crops in any Brazilian state.

## Project Overview

The application connects to Embrapa's AgroAPI, searches the municipalities of a state, and checks a proposed planting date against the ZARC window for a crop, a soil class and a cycle. Planting inside the window is the Ministry of Agriculture's condition for Proagro and for subsidized rural insurance. It is an educational software project: its output supports exploration of public zoning data and does not replace professional agronomic advice.

Current features (V3):

- nine crops: soybean, first- and second-crop corn, rice, beans, wheat, cotton, sugarcane and arabica coffee;
- municipalities of every state with an API token (five municipalities in Goiás, soybean only, in demo mode);
- planting-window checks by crop, soil class, cycle and date;
- "what to plant": the farm (municipality, soil, area) entered once and a date checked across all crops, with the ZARC risk level (20%, 30% or 40%) of each crop on that date and the expected profit per hectare and for the whole area;
- comparison between cities, up to ten at a time;
- financial analysis: profit per hectare by cycle, with the cities where each cycle can still be planted;
- a linear program that plans soybean and second-crop corn planting (see below);
- a RAG over public agricultural documents, with retrieval measured against a 31-question answer key (see below);
- a web interface with the same features (see below);
- local query history, usage statistics with ASCII charts, and export to Excel (`.xlsx`);
- local caching to reduce API calls.

In the command line, city comparison and financial analysis still use soybean on AD2 soil only; in the web interface they take any crop and soil.

## Motivation

In 2026, curiosity about agriculture in Goiás led me to connect a new area of interest with my Python studies and undergraduate research. ABR began as a small planting-cycle checker and became a practical exercise in API integration, data interpretation, command-line design, and decision-support software.

The project is intentionally evolving alongside my studies in Linear Algebra, mathematical optimization, scientific computing, and data analysis.

## Data and Decision Logic

ABR requests zoning records from the AgroAPI Agritec v2 `/zoneamento` endpoint. Each record carries a soil class (AD1–AD6, or sandy / medium / clay texture, depending on the crop) and a cycle (early, medium, late, semi-perennial or perennial). Calendar dates are mapped to ten-day periods (*decêndios*) before being compared with the zoning windows returned by the API. Every answer is cached in `cache_zarc_bruto.json`, so the same request is made only once; the free AgroAPI plan allows 1,000 requests per month.

ZARC classifies each ten-day period by the probability of yield loss from adverse weather: below 20%, 30% or 40%. The API returns one level per request. Planting-window checks, city comparison, financial analysis and the optimization use the 20% level (one request per municipality and crop). "What to plant" uses the three levels (three requests per municipality and crop, 27 for a municipality seen for the first time).

Profit figures use yield, price and cost typed by the user. The form starts with CONAB values for the selected state (`valores.py` downloads CONAB's open data files and writes `valores_conab.json`): yield from the latest crop survey, price received by the producer in the latest published month, and variable plus fixed cost per hectare. The source of each number is shown next to it. Where CONAB has no figure for the state, the national yield or the average of the states that have one is used, and the source text says so. Coverage is uneven: sugarcane cost, for instance, exists for a single municipality in Alagoas.

"What to plant" combines the two: the risk level on the planting date is read as the chance of a bad year, and expected profit is the average of a normal year and a bad year weighted by that chance. ZARC gives the probability of a loss, not its size, so the yield lost in a bad year (50% by default) **is an assumption typed by the user, not ZARC data**. Since each level is an upper bound, the result is the worst case within the level.

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
checks, comparison, history, statistics, and Excel export — but the data is limited to soybean
on AD2 soil in the municipalities bundled in `demo/`:

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

### Full installation (all crops and states)

For live data on every crop and state, provide an AgroAPI token as described below.
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

The interactive menu has nine options: new planting-window query (state, municipality, crop, soil, cycle and date), query history, municipality comparison, history statistics, Excel export, financial analysis, soybean + second-crop corn optimization, what to plant (farm, risk and expected profit), and exit.

### Soybean + second-crop corn optimization

Menu option 7 builds a linear program (`otimizacao.py`, solved with PuLP/CBC) that plans soybean
planting by cycle and ten-day period and the second-crop corn (*milho safrinha*) that follows it,
over one crop year, maximizing profit. It covers several cities and soil classes (AD1–AD6), a
planter-capacity limit per ten-day period, and soybean → corn succession modelled as a flow balance.
The report shows the plan and the shadow prices of each binding limit.

Assumptions still to be checked are grouped at the top of `otimizacao.py` (cycle lengths, the
harvest-to-planting gap, corn yield loss per ten-day delay, default planter). In demo mode the corn
windows in `demo/demo_zarc_milho.json` are **illustrative, written by hand, not AgroAPI records**.
With a token, the corn windows come from the AgroAPI (`idCultura=57`, second-crop corn; `ID_CULTURA_MILHO`
in `.env` overrides it).

`python teste_otimizacao.py` checks the model against a small instance solvable by hand, and
`python teste_virada.py` checks windows that cross the turn of the year, and `python teste_risco.py`
checks the expected-profit arithmetic and the choice of the farm's soil.

### Document search and answers with citations — RAG

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
5. `responder.py` sends the question and the retrieved chunks to a local LLM through Ollama. The
   model cites only the block number (`[Bloco 2]`); the code replaces it with the document and page.
6. `avaliar_respostas.py` generates an answer for each of the 31 questions, writes them to
   `respostas.csv` and checks whether the answer cites a page from the answer key.

Retrieval results (hit@5, 31 questions):

| Search  | hit@5 |
|---------|-------|
| Vector  | 28/31 |
| BM25    | 25/31 |
| Hybrid  | 26/31 |

Adding the document title to each chunk was the change that brought vector search to 28/31.

Answer results (vector search, top 5 chunks, Qwen3 4B running locally, 31 questions):

| Check                                  | Result |
|----------------------------------------|--------|
| Answer cites a page from the answer key | 24/31  |

Citing the right page does not mean the answer is right. Reading `respostas.csv`, the model still
gets the content wrong in some answers that retrieval got right: it gave the limits of another
soil class for AD3 and AD4, gave the wrong yield for a corn hybrid, and said irrigated crops must
follow the ZARC planting dates when the document says the opposite. Retrieval finds the page in
28 of 31 questions, so the weak part is the 4B model, not the search.

Run from the repository root:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU-only torch, much smaller
python rag/baixar.py     # download the PDFs listed in rag/fontes.csv
python rag/extrair.py    # PDF -> text, one block per page (needs poppler's pdftotext)
python rag/indexar.py    # chunks + embeddings
python rag/buscar.py "qual a duração dos ciclos da soja no ZARC?"
python rag/avaliar.py    # hit@5 of the three searches
python rag/responder.py "quantos anos de dados o ZARC do milho usa?"   # needs `ollama serve`
python rag/avaliar_respostas.py   # answers for the 31 questions, needs `ollama serve`
```

Exporting writes a `historico_YYYY-MM-DD_HH-MM.xlsx` file in the repository root. These files are generated artefacts and are not tracked by Git.

## Web interface

`web/` has the same features as the CLI in a browser page: what to plant, planting window, city
comparison, financial analysis, the soybean + corn optimization, the query history, and a tab that
asks the RAG. A selector in the sidebar changes the state. It calls the same functions the CLI uses
and adds no dependencies (Python's `http.server` and one HTML file, no build step).

```bash
python web/servidor.py     # then open http://localhost:8000
```

Planting windows are drawn on a strip of 36 ten-day periods running from September to August (the
crop year), and the optimization plan is drawn inside those windows. The Documents tab needs the
RAG index and `ollama serve`; the other tabs work without them.

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
├── seguro.py         # What to plant: one date across all crops, with ZARC risk and expected profit
├── valores.py        # Yield, price and cost per crop and state from CONAB open data
├── otimizacao.py     # Linear program: soybean + second-crop corn plan
├── teste_otimizacao.py # Hand-checkable test of the linear program
├── teste_virada.py   # Test of windows that cross the turn of the year
├── teste_risco.py    # Test of expected profit and farm soil selection
├── web/              # Web interface: servidor.py (JSON over http.server) and index.html
├── rag/              # RAG: download, extraction, index, three searches, hit@5 evaluation, answers via Ollama
├── demo/             # Bundled sample data used when no API token is present
├── teste.api.py      # Standalone API exploration script
├── requirements.txt  # Python dependencies
├── bugs.md           # Maintainer notes for known issues
└── README.md
```

Runtime files such as `.env`, API caches, query-history CSV files, and generated `.xlsx` exports are excluded from version control.

## Roadmap

- sourced prices and production costs for the nine crops, in place of the placeholder values;
- crop and soil choice in the command-line comparison and financial analysis, as in the web interface;
- an agent in which a language model picks among the planting-window, financial, optimization and RAG functions to answer a question written in plain text;
- other risk levels besides 20%;
- improve automated testing and error handling around the external API;
- validate the decision-support assumptions with domain specialists.

These are directions for future study, not completed features.

## Data Sources

- [ZARC portal — Brazilian Ministry of Agriculture](https://mapa-indicadores.agricultura.gov.br/publico/extensions/Zarc/Zarc.html)
- [AgroAPI Agritec — Embrapa](https://www.agroapi.cnptia.embrapa.br/)
- [CONAB crop surveys](https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/safras) — national average yields used as example values

## Author

Renato Morais Mundim Filho — Computer Science student.

- [GitHub](https://github.com/uzoom333)
- [LinkedIn](https://www.linkedin.com/in/renato-morais-mundim-filho-88919238b/)

## License

This project is distributed under the MIT License.
