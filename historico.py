from datetime import datetime
import os


def salvar_consulta(codigo_ibge, ciclo, data_plantio, resultado):
    """Salva uma consulta no arquivo historico.csv."""
    arquivo = "historico.csv"

    data_consulta = datetime.now().replace(microsecond=0)

    if resultado:
        status = "dentro"
    else:
        status = "fora"

    arquivo_existe = os.path.exists(arquivo)

    with open(arquivo, "a") as f:
        if not arquivo_existe:
            f.write("data_consulta,cidade,ciclo,data_plantio,resultado\n")
        f.write(f"{data_consulta},{codigo_ibge},{ciclo},{data_plantio},{status}\n")


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