from datetime import date


def qual_decendio(data):
    day = data.day
    month = data.month
    if day <= 10:
        dec_mes = 1
    elif day <= 20:
        dec_mes = 2
    else:
        dec_mes = 3
    dec_ano = (month - 1) * 3 + dec_mes
    return dec_ano


def janela_para_decendios(dia_ini, mes_ini, dia_fim, mes_fim, ano=2026):
    data_ini = date(ano, mes_ini, dia_ini)
    data_fim = date(ano, mes_fim, dia_fim)

    dec_ini = qual_decendio(data_ini)
    dec_fim = qual_decendio(data_fim)

    return list(range(dec_ini, dec_fim + 1))

def proximo_decendio_valido(decendio_data, janela):
    """Retorna o menor decêndio da janela que é >= decendio_data.
    Se nenhum decêndio da janela for >= data, retorna None (janela passou)."""
    
    for decendio_novo in janela:                           # ← itera na janela
        if decendio_novo >= decendio_data:                  # ← condição
            return decendio_novo                # ← retorna o decêndio atual
    
    return None


def esta_na_janela(data_plantio, ciclo, janelas):
    """Verifica se uma data está dentro da janela ZARC do ciclo informado."""
    decendio = qual_decendio(data_plantio)
    janela = janelas[ciclo]
    if decendio in janela:
        return True
    else:
        return False