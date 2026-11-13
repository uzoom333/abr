from datetime import datetime
import os


CABECALHO = "data_consulta,cidade,ciclo,data_plantio,resultado,cultura,solo"


def atualiza_cabecalho(arquivo):
    """O histórico antigo não tinha cultura nem solo (era sempre soja em AD2).
    Se o arquivo ainda estiver no formato antigo, completa as linhas."""
    with open(arquivo, "r") as f:
        linhas = f.read().splitlines()
    if not linhas or linhas[0] == CABECALHO:
        return
    with open(arquivo, "w") as f:
        f.write(CABECALHO + "\n")
        for linha in linhas[1:]:
            if linha.strip():
                f.write(linha + ",soja,AD2\n")


def salvar_consulta(codigo_ibge, ciclo, data_plantio, resultado, cultura="soja", solo="AD2"):
    """Salva uma consulta no arquivo historico.csv."""
    arquivo = "historico.csv"

    data_consulta = datetime.now().replace(microsecond=0)

    if resultado:
        status = "dentro"
    else:
        status = "fora"

    arquivo_existe = os.path.exists(arquivo)
    if arquivo_existe:
        atualiza_cabecalho(arquivo)

    with open(arquivo, "a") as f:
        if not arquivo_existe:
            f.write(CABECALHO + "\n")
        f.write(f"{data_consulta},{codigo_ibge},{ciclo},{data_plantio},{status},{cultura},{solo}\n")


def mostrar_historico():
    """Mostra o histórico completo de consultas do arquivo historico.csv."""
    print()
    print("=" * 40)
    print(">> Histórico de consultas: ")
    print("=" * 40)
    print()

    arquivo = "historico.csv"
    arquivo_existe = os.path.exists(arquivo)

    if not arquivo_existe:
        print("Nenhuma consulta no historico")
    else:
        with open(arquivo, "r") as f:
            for linha in f:
                print(linha.strip())