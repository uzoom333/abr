"""Interface web do ABR. Usa as mesmas funções da CLI; só troca o input()/print() por JSON.

Rodar da raiz do projeto:  python web/servidor.py     e abrir http://localhost:8000
Só a biblioteca padrão no servidor. A aba Documentos precisa do índice do RAG
(rag/indexar.py) e de `ollama serve` rodando; o resto funciona sem eles.
"""
import csv
import io
import json
import os
import sys
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_WEB = os.path.join(RAIZ, "web")
PASTA_RAG = os.path.join(RAIZ, "rag")
os.chdir(RAIZ)  # os caches e o historico.csv da CLI são relativos à raiz
sys.path.insert(0, RAIZ)

import api
import otimizacao
from financeiro import CICLOS
from historico import salvar_consulta
from zarc import nome_decendio, para_ano_safra, para_calendario, qual_decendio, situacao_na_janela

PORTA = 8000
LIMITE_CIDADES = 10


class Erro(Exception):
    """Erro para mostrar ao usuário (entrada inválida, cidade sem dado...)."""


# ============================================
# ENTRADA
# ============================================

def nomes_municipios():
    return {m["codigoIBGE"]: m["nome"].title() for m in api.busca_municipios_go()}


def le_data(texto):
    try:
        data = date.fromisoformat(texto)
    except (TypeError, ValueError):
        raise Erro("Data inválida.")
    if not 2024 <= data.year <= 2030:
        raise Erro("O ano precisa estar entre 2024 e 2030.")
    return data


def le_ciclo(ciclo):
    if ciclo not in CICLOS:
        raise Erro("Ciclo inválido.")
    return ciclo


def le_positivo(valor, nome):
    try:
        numero = float(str(valor).replace(",", "."))
    except ValueError:
        raise Erro(f"{nome}: digite um número.")
    if numero <= 0:
        raise Erro(f"{nome}: precisa ser maior que zero.")
    return numero


def le_codigos(codigos):
    codigos = [int(c) for c in codigos]
    if not codigos:
        raise Erro("Escolha pelo menos uma cidade.")
    if len(codigos) > LIMITE_CIDADES:
        raise Erro(f"Escolha no máximo {LIMITE_CIDADES} cidades.")
    return codigos


def janela_em_safra(janela):
    """Decêndios do calendário -> decêndios do ano-safra, em ordem (é o que a tela desenha)."""
    return sorted(para_ano_safra(d) for d in janela)


# ============================================
# TELAS
# ============================================

def inicio(_):
    return {
        "demo": api.MODO_DEMO,
        "municipios": [{"codigo": c, "nome": n} for c, n in sorted(nomes_municipios().items(), key=lambda x: x[1])],
        "ciclos": CICLOS,
        "plantadeira": otimizacao.PLANTADEIRA_PADRAO,
        "hipoteses": {
            "duracao": otimizacao.DURACAO_CICLO,
            "intervalo": otimizacao.INTERVALO_COLHEITA_MILHO,
            "perda_milho": otimizacao.PERDA_MILHO_POR_DECENDIO,
        },
        "rag_indexado": os.path.exists(os.path.join(PASTA_RAG, "indice", "vetores.npy")),
    }


def janela(d):
    """Opção 1 da CLI: a data cai na janela do ZARC?"""
    codigo, ciclo, data = int(d["codigo"]), le_ciclo(d["ciclo"]), le_data(d["data"])
    janelas = api.pega_zarc(codigo)
    if janelas is None:
        raise Erro("Não foi possível obter o zoneamento dessa cidade.")
    if ciclo not in janelas:
        raise Erro(f"O ZARC não tem o ciclo {ciclo} para essa cidade.")

    status, decendios = situacao_na_janela(data, janelas[ciclo])
    salvar_consulta(codigo, ciclo, data, status == "dentro")
    decendio = qual_decendio(data)
    return {
        "cidade": nomes_municipios().get(codigo, "?"),
        "ciclo": ciclo,
        "decendio": decendio,
        "nome_decendio": nome_decendio(decendio),
        "t": para_ano_safra(decendio),
        "janela": janela_em_safra(janelas[ciclo]),
        "status": status,
        "decendios": decendios,
    }


def comparar(d):
    """Opção 3 da CLI: a mesma data e ciclo em várias cidades."""
    codigos, ciclo, data = le_codigos(d["codigos"]), le_ciclo(d["ciclo"]), le_data(d["data"])
    nomes = nomes_municipios()
    linhas, sem_zarc, sem_ciclo = [], [], []
    for codigo in codigos:
        nome = nomes.get(codigo, "?")
        janelas = api.pega_zarc(codigo)
        if janelas is None:
            sem_zarc.append(nome)
        elif ciclo not in janelas:
            sem_ciclo.append(nome)
        else:
            status, decendios = situacao_na_janela(data, janelas[ciclo])
            linhas.append({"cidade": nome, "status": status, "decendios": decendios,
                           "janela": janela_em_safra(janelas[ciclo])})

    ordem = {"dentro": 0, "antes": 1, "passou": 2}
    # dentro: quem tem mais janela pela frente primeiro; antes: quem abre mais cedo primeiro
    linhas.sort(key=lambda l: (ordem[l["status"]], -l["decendios"] if l["status"] == "dentro" else l["decendios"]))
    return {"t": para_ano_safra(qual_decendio(data)), "linhas": linhas,
            "sem_zarc": sem_zarc, "sem_ciclo": sem_ciclo}


def financeiro(d):
    """Opção 6 da CLI: cidades e ciclos ordenados pelo lucro líquido estimado."""
    codigos, data = le_codigos(d["codigos"]), le_data(d["data"])
    custo = le_positivo(d["custo_ha"], "Custo por hectare")
    preco = le_positivo(d["preco_saca"], "Preço da saca")
    produtividade = {c: le_positivo(d["produtividade"][c], f"Produtividade {c}") for c in CICLOS}

    nomes = nomes_municipios()
    linhas, sem_zarc = [], []
    for codigo in codigos:
        janelas = api.pega_zarc(codigo)
        if janelas is None:
            sem_zarc.append(nomes.get(codigo, "?"))
            continue
        for ciclo in CICLOS:
            if ciclo not in janelas:
                continue
            status, decendios = situacao_na_janela(data, janelas[ciclo])
            bruto = produtividade[ciclo] * preco
            linhas.append({"cidade": nomes.get(codigo, "?"), "ciclo": ciclo, "status": status,
                           "decendios": decendios, "produtividade": produtividade[ciclo],
                           "lucro_bruto": bruto, "lucro_liquido": bruto - custo})

    ordem = {"dentro": 0, "antes": 1}
    viaveis = [l for l in linhas if l["status"] != "passou"]
    viaveis.sort(key=lambda l: (-l["lucro_liquido"], ordem[l["status"]], l["decendios"]))
    return {"viaveis": viaveis, "passadas": [l for l in linhas if l["status"] == "passou"],
            "sem_zarc": sem_zarc}


def le_solos(texto, disponiveis, cidade):
    """'AD2:60 AD4:40' -> {'AD2': 0.6, 'AD4': 0.4}. Vazio = tudo no primeiro solo disponível."""
    texto = (texto or "").strip()
    if not texto:
        return {"AD2" if "AD2" in disponiveis else disponiveis[0]: 1.0}
    try:
        partes = {}
        for pedaco in texto.split():
            solo, pct = pedaco.split(":")
            partes[solo.upper()] = float(pct.replace(",", ".")) / 100
    except ValueError:
        raise Erro(f"{cidade}: escreva os solos assim: AD2:60 AD4:40")
    fora = [s for s in partes if s not in disponiveis]
    if fora:
        raise Erro(f"{cidade}: o ZARC não tem janela para {', '.join(fora)}. Disponíveis: {', '.join(disponiveis)}.")
    if abs(sum(partes.values()) - 1) > 0.001:
        raise Erro(f"{cidade}: as porcentagens dos solos precisam somar 100.")
    return partes


def otimizar(d):
    """Opção 7 da CLI: plano de soja + milho safrinha por programação linear."""
    soja_in, milho_in = d["soja"], d["milho"]
    custo_soja = le_positivo(soja_in["custo_ha"], "Custo da soja")
    preco_soja = le_positivo(soja_in["preco_saca"], "Preço da soja")
    lucro_soja = {c: le_positivo(soja_in["produtividade"][c], f"Produtividade da soja {c}") * preco_soja - custo_soja
                  for c in CICLOS}
    custo_milho = le_positivo(milho_in["custo_ha"], "Custo do milho")
    preco_milho = le_positivo(milho_in["preco_saca"], "Preço do milho")
    prod_milho = le_positivo(milho_in["produtividade"], "Produtividade do milho")

    maquina = {campo: le_positivo(d["plantadeira"][campo], campo) for campo in otimizacao.PLANTADEIRA_PADRAO}
    cap = otimizacao.capacidade_plantadeira(**maquina)

    cidades = d["cidades"]
    if not cidades:
        raise Erro("Adicione pelo menos uma cidade.")
    if len(cidades) > LIMITE_CIDADES:
        raise Erro(f"No máximo {LIMITE_CIDADES} cidades.")
    if len({int(c["codigo"]) for c in cidades}) < len(cidades):
        raise Erro("A mesma cidade aparece duas vezes.")

    nomes = nomes_municipios()
    talhoes = []
    for cidade in cidades:
        codigo = int(cidade["codigo"])
        nome = nomes.get(codigo, "?")
        soja = api.zarc_soja_por_solo(codigo)
        if not soja:
            raise Erro(f"{nome}: sem zoneamento de soja.")
        milho = api.zarc_milho_por_solo(codigo)
        area = le_positivo(cidade["area"], f"Área em {nome}")
        divisao = le_solos(cidade.get("solos"), sorted(soja), nome)
        talhoes += otimizacao.talhoes_da_cidade(nome, area, divisao, soja, milho, lucro_soja,
                                                prod_milho, preco_milho, custo_milho)

    resultado = otimizacao.resolve(talhoes, cap)
    if resultado["status"] != "Optimal":
        raise Erro(f"O solver não achou solução ótima (status: {resultado['status']}).")

    # junta em cada talhão as janelas que o ZARC permite, para a tela desenhar o plano dentro delas
    for item, talhao in zip(resultado["plano"], talhoes):
        item["janela_soja"] = sorted({t for ts in talhao["janelas_soja"].values() for t in ts})
        item["janela_milho"] = sorted(talhao["lucro_milho"])
    resultado["milho_ilustrativo"] = api.MODO_DEMO
    return resultado


def le_historico():
    if not os.path.exists("historico.csv"):
        return []
    with open("historico.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def historico(_):
    """Opções 2 e 4 da CLI: as consultas feitas e a contagem delas."""
    linhas = le_historico()
    nomes = nomes_municipios()
    for linha in linhas:
        if linha["cidade"].isdigit():
            linha["cidade"] = nomes.get(int(linha["cidade"]), linha["cidade"])
    por_ciclo = {c: sum(1 for l in linhas if l["ciclo"] == c) for c in CICLOS}
    dentro = sum(1 for l in linhas if l["resultado"] == "dentro")
    return {"linhas": linhas[::-1], "total": len(linhas), "por_ciclo": por_ciclo,
            "dentro": dentro, "fora": len(linhas) - dentro}


def planilha_historico():
    """Opção 5 da CLI: o histórico em .xlsx, devolvido como bytes para o navegador baixar."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Historico"
    ws.append(["data_consulta", "cidade", "ciclo", "data_plantio", "resultado"])
    for linha in le_historico():
        ws.append([linha[c] for c in ("data_consulta", "cidade", "ciclo", "data_plantio", "resultado")])
    for celula in ws[1]:
        celula.font = Font(bold=True)
    saida = io.BytesIO()
    wb.save(saida)
    return saida.getvalue()


# ============================================
# DOCUMENTOS (RAG)
# ============================================

class Rag:
    """Carrega o índice e o modelo de embedding na primeira pergunta e deixa na memória (~900 MB)."""
    trava = threading.Lock()
    pronto = None

    @classmethod
    def carrega(cls):
        if cls.pronto is None:
            if PASTA_RAG not in sys.path:
                sys.path.insert(0, PASTA_RAG)
            import buscar
            import responder
            from sentence_transformers import SentenceTransformer
            vetores, chunks = buscar.carrega_indice()
            with open(os.path.join(PASTA_RAG, "fontes.csv"), encoding="utf-8") as f:
                fontes = {linha["arquivo"]: linha for linha in csv.DictReader(f)}
            cls.pronto = (responder, SentenceTransformer(buscar.MODELO), vetores, chunks, fontes)
        return cls.pronto


def perguntar(d):
    """Gera linhas JSON: primeiro os trechos achados, depois o texto da resposta conforme o modelo escreve.
    O texto vai com [Bloco N]; a tela troca cada um pelo trecho N da lista (mesma regra do responder.py)."""
    import requests

    pergunta = (d.get("pergunta") or "").strip()
    if not pergunta:
        yield {"erro": "Escreva uma pergunta."}
        return
    with Rag.trava:  # uma pergunta por vez: o modelo local não aguenta duas
        try:
            responder, modelo, vetores, chunks, fontes = Rag.carrega()
        except FileNotFoundError:
            yield {"erro": "O índice dos documentos não existe. Rode: python rag/baixar.py, rag/extrair.py e rag/indexar.py"}
            return
        indices = responder.busca_trechos(pergunta, modelo, vetores)
        trechos = []
        for i in indices:
            c = chunks[i]
            fonte = fontes.get(c["arquivo"], {})
            trechos.append({"arquivo": c["arquivo"], "pagina": c["pagina"], "texto": c["texto"],
                            "titulo": fonte.get("titulo", c["arquivo"]), "url": fonte.get("url", "")})
        yield {"trechos": trechos}

        texto = ""
        try:
            for pedaco in responder.pergunta_ao_llm_aos_poucos(pergunta, responder.monta_contexto(indices, chunks)):
                texto += pedaco
                yield {"texto": texto}
        except requests.ConnectionError:
            yield {"erro": "O Ollama não está rodando. Em outro terminal, rode: ollama serve"}
            return
        except requests.HTTPError as e:
            yield {"erro": f"O Ollama recusou o pedido ({e.response.status_code}). O modelo {responder.LLM} está instalado?"}
            return
        yield {"fim": True}


# ============================================
# HTTP
# ============================================

ROTAS = {"/api/inicio": inicio, "/api/janela": janela, "/api/comparar": comparar,
         "/api/financeiro": financeiro, "/api/otimizar": otimizar, "/api/historico": historico}


class Pedido(BaseHTTPRequestHandler):
    def envia(self, status, corpo, tipo="application/json; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        for nome, valor in (extra or {}).items():
            self.send_header(nome, valor)
        self.end_headers()
        self.wfile.write(corpo)

    def envia_json(self, status, dados):
        self.envia(status, json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def responde(self, dados):
        funcao = ROTAS.get(self.path)
        if funcao is None:
            return self.envia_json(404, {"erro": "Não existe."})
        try:
            self.envia_json(200, funcao(dados))
        except Erro as e:
            self.envia_json(400, {"erro": str(e)})
        except (KeyError, TypeError, ValueError) as e:
            self.envia_json(400, {"erro": f"Pedido incompleto ou inválido ({e})."})

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(PASTA_WEB, "index.html"), "rb") as f:
                return self.envia(200, f.read(), "text/html; charset=utf-8")
        if self.path == "/api/historico.xlsx":
            return self.envia(200, planilha_historico(),
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              {"Content-Disposition": 'attachment; filename="historico_abr.xlsx"'})
        self.responde({})

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        try:
            dados = json.loads(self.rfile.read(tamanho) or b"{}")
        except ValueError:
            return self.envia_json(400, {"erro": "JSON inválido."})
        if self.path == "/api/perguntar":
            return self.responde_aos_poucos(perguntar(dados))
        self.responde(dados)

    def responde_aos_poucos(self, linhas):
        """Uma linha JSON por vez, sem Content-Length: o navegador lê conforme chega."""
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            for linha in linhas:
                self.wfile.write(json.dumps(linha, ensure_ascii=False).encode("utf-8") + b"\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # a pessoa fechou a aba no meio da resposta

    def log_message(self, formato, *args):
        pass  # o terminal fica só com os avisos da api.py (cache, demo...)


def main():
    api.aviso_modo_demo()
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Pedido)
    print(f"ABR aberto em http://localhost:{PORTA}  (Ctrl+C para fechar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nFechado.")


if __name__ == "__main__":
    main()
