import csv
import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font


def exportar_excel():
    """Lê o historico.csv e exporta para um arquivo .xlsx com timestamp."""

    arquivo_csv = "historico.csv"

    if not os.path.exists(arquivo_csv):
        print("Nenhuma consulta no historico ainda")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Historico"

    with open(arquivo_csv, "r", encoding="utf-8", newline="") as f:
        leitor = csv.reader(f)
        for linha in leitor:
            ws.append(linha)

    if ws.max_row == 0:
        print("Historico vazio, nada para exportar")
        return

    for celula in ws[1]:
        celula.font = Font(bold=True)

    agora = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nome_arquivo = f"historico_{agora}.xlsx"

    wb.save(nome_arquivo)

    print(f"✅ Exportado para {nome_arquivo}")
