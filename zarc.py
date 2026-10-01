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

# ============================================
# ANO-SAFRA (usado pela otimização)
# ============================================

# O ZARC numera os decêndios de 1 a 36 a partir de janeiro, mas a safra atravessa
# a virada do ano (soja em out–nov, milho em jan–mar). Na otimização o tempo corre
# pelo ano-safra: t = 1 é o 1º decêndio de setembro, que é o decêndio 25 do calendário.
INICIO_ANO_SAFRA = 25

MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun",
               "jul", "ago", "set", "out", "nov", "dez"]


def para_ano_safra(decendio):
    """Decêndio do calendário (1 = 1º de janeiro) -> decêndio do ano-safra (1 = 1º de setembro)."""
    return (decendio - INICIO_ANO_SAFRA) % 36 + 1


def para_calendario(t):
    """Inverso de para_ano_safra."""
    return (t + INICIO_ANO_SAFRA - 2) % 36 + 1


def nome_decendio(decendio):
    """Decêndio do calendário -> texto, ex.: 28 -> '1º dec. out'."""
    mes = (decendio - 1) // 3
    parte = (decendio - 1) % 3 + 1
    return f"{parte}º dec. {MESES_ABREV[mes]}"


def decendios_entre(dec_ini, dec_fim):
    """Decêndios de dec_ini a dec_fim, dando a volta em dezembro se a janela atravessar o ano."""
    if dec_ini <= dec_fim:
        return list(range(dec_ini, dec_fim + 1))
    return list(range(dec_ini, 37)) + list(range(1, dec_fim + 1))
