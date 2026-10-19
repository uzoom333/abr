"""Passo 4 do RAG: avaliação da busca (hit@k), ainda sem LLM.

Para cada pergunta do avaliacao.csv, roda as três buscas e confere se algum dos
k chunks devolvidos é do arquivo e da página onde a resposta está.
Rodar da raiz do projeto:  python rag/avaliar.py

ESQUELETO: preencha os ???. Tudo que não tem ??? já está pronto.
"""
import csv
import os

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from buscar import MODELO, busca_bm25, busca_hibrida, busca_vetorial, carrega_indice, tokeniza

ARQUIVO_AVALIACAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avaliacao.csv")


def carrega_avaliacao():
    """Lista de dicts, um por linha: {'pergunta': ..., 'arquivo': ..., 'pagina': ..., 'resposta': ...}"""
    with open(ARQUIVO_AVALIACAO, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def acertou(indices, chunks, arquivo, pagina):
    """True se algum dos chunks devolvidos é do arquivo e da página certos."""
    for i in indices:
        c = chunks[i]
        if c["arquivo"] == arquivo and c["pagina"] == pagina :                              # dica: confira o tipo de cada lado com print(repr(...))
            return True
    return False
    


def main():
    vetores, chunks = carrega_indice()
    modelo = SentenceTransformer(MODELO)
    bm25 = BM25Okapi([tokeniza(c["texto"]) for c in chunks])
    perguntas = carrega_avaliacao()

    k = 5
    buscas = {
        "vetorial": lambda p: busca_vetorial(p, modelo, vetores, k),
        "BM25": lambda p: busca_bm25(p, bm25, k),
        "híbrida": lambda p: busca_hibrida(p, modelo, vetores, bm25, k),
    }

    acertos = {nome: 0 for nome in buscas}
    for linha in perguntas:
        print(f"\n{linha['pergunta']}  ->  {linha['arquivo']} p.{linha['pagina']}")
        for nome, busca in buscas.items():
            indices = busca(linha['pergunta'])
            ok = acertou(indices, chunks, linha['arquivo'], int(linha['pagina']))
            if ok:
                acertos[nome] += 1
            print(f"  {nome:9} {'ACERTOU' if ok else 'errou'}")

    print(f"\n--- hit@{k} ---")
    for nome, n in acertos.items():
        print(f"{nome:9} {n}/{len(perguntas)}")


if __name__ == "__main__":
    main()
