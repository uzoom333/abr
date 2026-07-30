# ABR

ABR is an agricultural decision-support command-line application that uses official Brazilian Agricultural Climate Risk Zoning (ZARC) data to evaluate soybean planting windows in Goiás.

## Project Overview

The application connects to Embrapa's AgroAPI, searches municipalities in Goiás, and checks a proposed planting date against the available ZARC windows for early-, medium-, or late-cycle soybeans. It is an educational software project: its output supports exploration of public zoning data and does not replace professional agronomic advice.

Current features include:

- municipality search across Goiás;
- planting-window checks by soybean cycle and date;
- comparison of up to ten municipalities;
- local query history;
- history statistics with ASCII charts;
- local caching to reduce API calls.

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
- [AgroAPI Agritec v2](https://www.agroapi.cnptia.embrapa.br/) for ZARC data

## Installation

```bash
git clone https://github.com/uzoom333/abr.git
cd abr

python3 -m venv .venv
source .venv/bin/activate

python -m pip install requests python-dotenv
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

The interactive menu provides a new planting-window query, query history, municipality comparison, and history statistics.

## Repository Structure

```text
abr/
├── main.py           # Interactive menu and planting-window workflow
├── api.py            # Municipality and ZARC API integration
├── zarc.py           # Date and ten-day-period calculations
├── comparacao.py     # Municipality comparison workflow
├── historico.py      # Local query history
├── estatistica.py    # Summary statistics and ASCII charts
├── teste.api.py      # Standalone API exploration script
├── bugs.md           # Maintainer notes for known issues
└── README.md
```

Runtime files such as `.env`, API caches, and query-history CSV files are excluded from version control.

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
