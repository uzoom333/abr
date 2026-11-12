"""Passo 4 do RAG: pergunta -> 5 chunks -> LLM responde citando o bloco -> o código troca o bloco por arquivo e página.

LLM local pelo Ollama (precisa de `ollama serve` rodando).
Rodar da raiz do projeto:  python rag/responder.py "quantos anos de dados o ZARC do milho usa?"

O modelo só cita [Bloco N]. Quem escreve arquivo e página é o código, para o modelo não inventar a fonte.
"""
import gc
import re
import sys

import requests
from sentence_transformers import SentenceTransformer

from buscar import MODELO, busca_vetorial, carrega_indice

URL_OLLAMA = "http://localhost:11434/api/chat"
LLM = "qwen-livre"

REGRAS = """Responda somente com base nos trechos. Se a resposta nao estiver neles, diga que nao achou. \
Depois de cada informacao, cite o bloco de onde ela saiu, no formato [Bloco N]. \
Nao cite arquivo nem pagina e nao use bloco que nao esta nos trechos."""


def monta_contexto(indices, chunks):
    """Um bloco por chunk, no formato:  [Bloco 1] texto do chunk"""
    partes = []
    for n, i in enumerate(indices, 1):  # n = 1, 2, 3...
        c = chunks[i]
        partes.append(f"[Bloco {n}] {c['texto']}")  # sem arquivo nem página
    return "\n\n".join(partes)


def troca_citacoes(resposta, indices, chunks):
    """Troca cada [Bloco N] da resposta pela etiqueta real do bloco."""
    def etiqueta(m):
        n = int(m.group(1))  # o número que o modelo citou
        if n < 1 or n > len(indices):  # o modelo citou um bloco que não existe
            return "[bloco inexistente]"
        c = chunks[indices[n - 1]]  # n começa em 1, a lista em 0
        return f"[{c['arquivo']} p.{c['pagina']}]"
    return re.sub(r"\[?Bloco (\d+)\]?", etiqueta, resposta)


def pergunta_ao_llm(pergunta, contexto):
    mensagens = [
        {"role": "system", "content": REGRAS},
        {"role": "user", "content":f"Trechos:\n{contexto}\n \nPergunta: {pergunta}" },
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

    indices = busca_vetorial(pergunta, modelo, vetores, 5)  # a busca que ganhou o placar (28/31)

    del modelo, vetores  # libera a RAM antes de o LLM carregar
    gc.collect()

    contexto = monta_contexto(indices, chunks)
    print(contexto)
    print("\n--- resposta do modelo ---")
    try:
        resposta = pergunta_ao_llm(pergunta, contexto)
    except requests.ConnectionError:
        sys.exit("⚠️ O Ollama não está rodando. Em outro terminal, rode: ollama serve")
    print(resposta)
    print("\n--- resposta com a etiqueta posta pelo código ---")
    print(troca_citacoes(resposta, indices, chunks))
    print("\n--- trechos enviados ao modelo ---")
    for i in indices:
        print(f"[{chunks[i]['arquivo']} p.{chunks[i]['pagina']}]")


if __name__ == "__main__":
    main()
