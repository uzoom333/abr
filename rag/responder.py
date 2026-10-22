"""Passo 4 do RAG: pergunta -> 5 chunks -> LLM responde citando arquivo e página.

LLM local pelo Ollama (precisa de `ollama serve` rodando).
Rodar da raiz do projeto:  python rag/responder.py "quantos anos de dados o ZARC do milho usa?"

ESQUELETO: preencha os 4 ???. Tudo que não tem ??? já está pronto.
"""
import gc
import sys

import requests
from sentence_transformers import SentenceTransformer

from buscar import MODELO, busca_vetorial, carrega_indice

URL_OLLAMA = "http://localhost:11434/api/chat"
LLM = "qwen-livre"

# 1. As regras do jogo para o modelo. Pense: o que ele NÃO pode fazer?
REGRAS = """Responder somente com base nos trechos, caso nao ache informar que nao achou nada, e sempre informar arquivo e pagina senao estara inventando resposta"""


def monta_contexto(indices, chunks):
    """Um bloco por chunk, no formato:  [arquivo.pdf p.3] texto do chunk"""
    partes = []
    for i in indices:
        c = chunks[i]
        partes.append(f"[{c['arquivo']} p.{c['pagina']}] {c['texto']}")  # 2. use c['arquivo'], c['pagina'] e c['texto']
    return "\n\n".join(partes)


def pergunta_ao_llm(pergunta, contexto):
    mensagens = [
        {"role": "system", "content": REGRAS},
        {"role": "user", "content":f"Trechos:\n{contexto}\n \nPergunta: {pergunta}" },  # 3. o modelo precisa ver duas coisas
    ]
    r = requests.post(URL_OLLAMA, json={"model": LLM, "messages": mensagens,
                                        "stream": False, "think": False,
                                        "options": {"temperature": 0, "num_ctx": 4096}},
                      timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"]


def main():
    pergunta = " ".join(sys.argv[1:]) or "quantos anos de dados o ZARC do milho usa?"
    vetores, chunks = carrega_indice()
    modelo = SentenceTransformer(MODELO)

    indices = busca_vetorial(pergunta, modelo, vetores, 5)  # 4. os 5 melhores chunks — use a busca que ganhou o placar (28/31)

    del modelo, vetores  # libera a RAM antes de o LLM carregar
    gc.collect()

    print(pergunta_ao_llm(pergunta, monta_contexto(indices, chunks)))
    print("\n--- trechos enviados ao modelo ---")
    for i in indices:
        print(f"[{chunks[i]['arquivo']} p.{chunks[i]['pagina']}]")


if __name__ == "__main__":
    main()
