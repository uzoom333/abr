"""Passo 5 do RAG: avaliação das respostas do LLM (o avaliar.py só mede a busca).

Para cada pergunta do avaliacao.csv, gera a resposta e confere duas coisas:
  citou   a resposta cita um (arquivo, página) do gabarito
  numeros todos os números da resposta do gabarito aparecem na resposta do modelo
Os números são uma conferência grosseira; o respostas.csv fica para ler e julgar no olho.
Precisa de `ollama serve` rodando. Leva uns 20 minutos.
Rodar da raiz do projeto:  python rag/avaliar_respostas.py
"""
import csv
import os
import re

from sentence_transformers import SentenceTransformer

from avaliar import carrega_avaliacao
from buscar import MODELO, carrega_indice
from responder import busca_trechos, monta_contexto, pergunta_ao_llm, troca_citacoes

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "respostas.csv")


def numeros(texto):
    """Conjunto dos números do texto, com vírgula decimal: '0,80 a 1,06' -> {'0,80', '1,06'}"""
    return set(re.findall(r"\d+(?:,\d+)?", texto.replace(".", "")))


def citou_certo(resposta, locais):
    citados = re.findall(r"\[(\S+\.pdf) p\.(\d+)\]", resposta)
    return any((arquivo, int(pagina)) in locais for arquivo, pagina in citados)


def main():
    vetores, chunks = carrega_indice()
    modelo = SentenceTransformer(MODELO)
    perguntas = carrega_avaliacao()

    # busca tudo primeiro e solta o modelo de embedding antes de o LLM carregar
    todos_indices = [busca_trechos(linha["pergunta"], modelo, vetores) for linha in perguntas]
    del modelo, vetores

    n_citou = n_numeros = 0
    with open(SAIDA, "w", encoding="utf-8", newline="") as f:
        saida = csv.writer(f)
        saida.writerow(["pergunta", "esperado", "resposta", "citou", "numeros"])
        for linha, indices in zip(perguntas, todos_indices):
            bruta = pergunta_ao_llm(linha["pergunta"], monta_contexto(indices, chunks))
            resposta = troca_citacoes(bruta, indices, chunks)
            citou = citou_certo(resposta, linha["locais"])
            tem_numeros = numeros(linha["resposta"]) <= numeros(bruta)
            n_citou += citou
            n_numeros += tem_numeros
            saida.writerow([linha["pergunta"], linha["resposta"], resposta,
                            "sim" if citou else "nao", "sim" if tem_numeros else "nao"])
            f.flush()
            print(f"citou {'sim' if citou else 'NAO'}  numeros {'sim' if tem_numeros else 'NAO'}  {linha['pergunta']}", flush=True)

    print(f"\ncitou a página certa   {n_citou}/{len(perguntas)}")
    print(f"números do gabarito    {n_numeros}/{len(perguntas)}")


if __name__ == "__main__":
    main()
