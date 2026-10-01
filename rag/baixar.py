"""Passo 1 do RAG: baixa os PDFs listados em fontes.csv para rag/pdfs/.

Os PDFs não vão para o git (são públicos, mas pesam); quem clonar roda este script.
Rodar da raiz do projeto: python rag/baixar.py
"""
import csv
import os

import requests

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_PDFS = os.path.join(PASTA, "pdfs")


def main():
    os.makedirs(PASTA_PDFS, exist_ok=True)
    with open(os.path.join(PASTA, "fontes.csv"), encoding="utf-8") as f:
        for fonte in csv.DictReader(f):
            destino = os.path.join(PASTA_PDFS, fonte["arquivo"])
            if os.path.exists(destino):
                print(f"já existe  {fonte['arquivo']}")
                continue
            resposta = requests.get(fonte["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            if resposta.status_code != 200 or not resposta.content.startswith(b"%PDF"):
                print(f"⚠️ falhou  {fonte['arquivo']} (status {resposta.status_code})")
                continue
            with open(destino, "wb") as saida:
                saida.write(resposta.content)
            print(f"baixado   {fonte['arquivo']}")


if __name__ == "__main__":
    main()
