"""Passo 3a do RAG: texto -> chunks -> embeddings -> índice em disco.

Lê rag/texto/*.txt (saída do extrair.py) e grava em rag/indice/:
  vetores.npy   matriz (n_chunks × 384), uma linha por chunk
  chunks.json   texto, arquivo e página de cada chunk (mesma ordem das linhas)
Rodar da raiz do projeto: python rag/indexar.py

ESQUELETO: preencha os ???. Tudo que não tem ??? já está pronto.
"""
import json
import os
import re

import numpy as np
from sentence_transformers import SentenceTransformer

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_TEXTO = os.path.join(PASTA, "texto")
PASTA_INDICE = os.path.join(PASTA, "indice")

MODELO = "intfloat/multilingual-e5-small"
TAMANHO_CHUNK = 250   # palavras (~375 tokens; o e5-small corta em 512)
SOBREPOSICAO = 40     # palavras repetidas entre um chunk e o seguinte


def carrega_paginas():
    """[(arquivo, página, texto)] de todos os .txt. Já pronto: é só parsing."""
    paginas = []
    for nome in sorted(os.listdir(PASTA_TEXTO)):
        with open(os.path.join(PASTA_TEXTO, nome), encoding="utf-8") as f:
            conteudo = f.read()
        partes = re.split(r"=== página (\d+) ===\n", conteudo)
        # partes = ['', '1', texto_p1, '2', texto_p2, ...]
        for i in range(1, len(partes), 2):
            paginas.append((nome.replace(".txt", ".pdf"), int(partes[i]), partes[i + 1]))
    return paginas


def divide_em_chunks(texto, tamanho, sobreposicao):
    """Janela deslizante de palavras. Cada chunk tem até `tamanho` palavras e
    começa `tamanho - sobreposicao` palavras depois do anterior."""
    palavras = texto.split()
    passo = tamanho - sobreposicao
    chunks = []
    for inicio in range(0, len(palavras), passo):
        pedaco = palavras[inicio:inicio + tamanho]
        chunks.append(" ".join(pedaco))
        if inicio + tamanho >= len(palavras):      # o último chunk já chegou ao fim do texto
            break
    return chunks


def main():
    chunks = []
    for arquivo, pagina, texto in carrega_paginas():
        for pedaco in divide_em_chunks(texto, TAMANHO_CHUNK, SOBREPOSICAO):
            if len(pedaco.split()) >= 20:   # descarta cabeçalho/rodapé solto
                chunks.append({"arquivo": arquivo, "pagina": pagina, "texto": pedaco})

    modelo = SentenceTransformer(MODELO)
    # O e5 exige um prefixo diferente para documento e para pergunta (veja o model card)
    vetores = modelo.encode(["passage: " + c["texto"] for c in chunks],
                            normalize_embeddings=True, show_progress_bar=True)

    os.makedirs(PASTA_INDICE, exist_ok=True)
    np.save(os.path.join(PASTA_INDICE, "vetores.npy"), vetores)
    with open(os.path.join(PASTA_INDICE, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    print(f"{len(chunks)} chunks, matriz {vetores.shape}")


if __name__ == "__main__":
    main()
