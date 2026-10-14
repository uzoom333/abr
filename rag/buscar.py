"""Passo 3b do RAG: pergunta -> k chunks mais relevantes (ainda sem LLM).

Três buscas, para comparar: vetorial (embedding), lexical (BM25) e híbrida (as duas juntas).
Rodar da raiz do projeto:  python rag/buscar.py "qual a duração dos ciclos da soja no ZARC?"

ESQUELETO: preencha os ???. Tudo que não tem ??? já está pronto.
"""
import json
import os
import re
import sys

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

PASTA_INDICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indice")
MODELO = "intfloat/multilingual-e5-small"


def carrega_indice():
    vetores = np.load(os.path.join(PASTA_INDICE, "vetores.npy"))
    with open(os.path.join(PASTA_INDICE, "chunks.json"), encoding="utf-8") as f:
        chunks = json.load(f)
    return vetores, chunks


def tokeniza(texto):
    """Minúsculas, só letras e números. Usado pelo BM25."""
    return re.findall(r"\w+", texto.lower())


def busca_vetorial(pergunta, modelo, vetores, k):
    """Índices dos k chunks com maior similaridade de cosseno com a pergunta."""
    q = modelo.encode("query: " + pergunta, normalize_embeddings=True)
    similaridades = vetores @ q             # uma similaridade por chunk; dica: por que normalizamos?
    return list(np.argsort(-similaridades)[:k]) # argsort ordena do menor para o maior


def busca_bm25(pergunta, bm25, k):
    """Índices dos k chunks com maior pontuação BM25."""
    pontuacoes = bm25.get_scores(tokeniza(pergunta))
    return list(np.argsort(-pontuacoes)[:k])


def funde(listas, k, c=60):
    """Reciprocal Rank Fusion: cada lista dá 1/(c + posição) a cada chunk; soma e ordena."""
    pontos = {}
    for lista in listas:
        for posicao, indice in enumerate(lista, start=1):
            pontos[indice] = pontos.get(indice, 0) + 1/(c + posicao)
    return sorted(pontos, key=pontos.get, reverse=True)[:k]


def busca_hibrida(pergunta, modelo, vetores, bm25, k):
    candidatos = 20
    return funde([busca_vetorial(pergunta, modelo, vetores, candidatos),
                  busca_bm25(pergunta, bm25, candidatos)], k)


def mostra(titulo, indices, chunks):
    print(f"\n--- {titulo} ---")
    for i in indices:
        c = chunks[i]
        print(f"[{c['arquivo']} p.{c['pagina']}] {c['texto'][:160]}...")


def main():
    pergunta = " ".join(sys.argv[1:]) or "qual a duração dos ciclos da soja no ZARC?"
    vetores, chunks = carrega_indice()
    modelo = SentenceTransformer(MODELO)
    bm25 = BM25Okapi([tokeniza(c["texto"]) for c in chunks])

    k = 5
    mostra("vetorial", busca_vetorial(pergunta, modelo, vetores, k), chunks)
    mostra("BM25", busca_bm25(pergunta, bm25, k), chunks)
    mostra("híbrida", busca_hibrida(pergunta, modelo, vetores, bm25, k), chunks)


if __name__ == "__main__":
    main()
