"""Passo 2 do RAG: PDF -> texto, uma página por bloco.

Lê rag/pdfs/*.pdf e grava rag/texto/<nome>.txt. Cada página começa com
'=== página N ===', para a resposta do RAG poder citar a página.
Usa o pdftotext (pacote poppler), que separa as palavras melhor que o pypdf.
Rodar da raiz do projeto: python rag/extrair.py
"""
import os
import re
import subprocess

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_PDFS = os.path.join(PASTA, "pdfs")
PASTA_TEXTO = os.path.join(PASTA, "texto")


def limpa(texto):
    """Tira espaços e linhas em branco repetidos."""
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extrai(caminho_pdf):
    saida = subprocess.run(["pdftotext", caminho_pdf, "-"], capture_output=True, text=True, check=True)
    paginas = saida.stdout.split("\f")  # o pdftotext separa páginas com form feed
    blocos = []
    for n, pagina in enumerate(paginas, start=1):
        if pagina.strip():
            blocos.append(f"=== página {n} ===\n{limpa(pagina)}")
    return "\n\n".join(blocos)


def main():
    os.makedirs(PASTA_TEXTO, exist_ok=True)
    for nome in sorted(os.listdir(PASTA_PDFS)):
        if not nome.endswith(".pdf"):
            continue
        texto = extrai(os.path.join(PASTA_PDFS, nome))
        saida = os.path.join(PASTA_TEXTO, nome.replace(".pdf", ".txt"))
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"{len(texto.split()):>6} palavras  {nome}")


if __name__ == "__main__":
    main()
