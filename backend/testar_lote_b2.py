"""Teste automático do lote B2: mensalistas, mensalidades e operadores.

Uso (a API precisa estar rodando em outro terminal):
    cd backend
    python testar_lote_b2.py

Cria clientes, veículo, vaga, contrato e operador de teste, executa as chamadas
e exclui tudo no final. As mensalidades de teste usam os meses 2099-11 e 2099-12,
para não se misturarem com as mensalidades reais.
"""
import json
import random
import urllib.error
import urllib.request
from decimal import Decimal
from getpass import getpass

URL = "http://127.0.0.1:8000"
resultados: list[bool] = []


def chamar(metodo: str, caminho: str, corpo=None, token: str | None = None):
    """Faz uma chamada HTTP e devolve (status, conteúdo). Não usa bibliotecas extras."""
    dados = json.dumps(corpo).encode() if corpo is not None else None
    requisicao = urllib.request.Request(URL + caminho, data=dados, method=metodo)
    requisicao.add_header("Content-Type", "application/json")
    if token:
        requisicao.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(requisicao) as resposta:
            texto = resposta.read().decode()
            return resposta.status, (json.loads(texto) if texto else None)
    except urllib.error.HTTPError as erro:
        texto = erro.read().decode()
        try:
            return erro.code, json.loads(texto)
        except ValueError:
            return erro.code, texto


def dicionario(conteudo) -> dict:
    return conteudo if isinstance(conteudo, dict) else {}


def conferir(descricao: str, condicao: bool, detalhe=None) -> None:
    resultados.append(bool(condicao))
    print(("OK      " if condicao else "FALHOU  ") + descricao)
    if not condicao and detalhe is not None:
        print(f"        recebido: {detalhe}")


def secao(titulo: str) -> None:
    print(f"\n--- {titulo}")


def gerar_cpf_valido() -> str:
    digitos = [random.randint(0, 9) for _ in range(9)]
    for posicao in (9, 10):
        soma = sum(digitos[n] * (posicao + 1 - n) for n in range(posicao))
        digitos.append((soma * 10 % 11) % 10)
    return "".join(str(d) for d in digitos)


def entrar(login: str, senha: str):
    return chamar("POST", "/auth/login", {"login": login, "senha": senha})


def mensalidade_da_placa(token: str, competencia: str, placa: str):
    status, lista = chamar("GET", f"/mensalidades?competencia={competencia}", token=token)
    if status != 200 or not isinstance(lista, list):
        return None
    return next((m for m in lista if m["placa"] == placa), None)


def main() -> None:
    print("Faça login com o operador cadastrado.")
    login = input("Login: ").strip()
    senha = getpass("Senha (não aparece enquanto você digita): ")
    try:
        status, corpo = entrar(login, senha)
    except urllib.error.URLError:
        print("Não consegui falar com a API em", URL)
        print("Confira se ela está rodando (uvicorn app.main:app --reload) em outro terminal.")
        return
    if status != 200:
        print("Login recusado. Confira o login e a senha.")
        return
    token = corpo["access_token"]
    status, eu = chamar("GET", "/auth/eu", token=token)
    meu_id = dicionario(eu).get("id")

    # ---------------------------------------------------------- dados de apoio
    secao("Preparando dados de teste")
    cpf = gerar_cpf_valido()
    _, cliente = chamar("POST", "/clientes", {"nome": "Mensalista Teste", "cpf_cnpj": cpf}, token)
    cliente_id = dicionario(cliente).get("id")
    placa = "MEN" + str(random.randint(1000, 9999))
    _, veiculo = chamar("POST", "/veiculos", {"placa": placa, "cliente_id": cliente_id}, token)
    veiculo_id = dicionario(veiculo).get("id")
    codigo = "M" + str(random.randint(100, 999))
    _, vaga = chamar("POST", "/vagas", {"codigo": codigo}, token)
    vaga_id = dicionario(vaga).get("id")
    conferir("cliente, veículo e vaga de teste foram criados", all([cliente_id, veiculo_id, vaga_id]), (cliente, veiculo, vaga))
    if not all([cliente_id, veiculo_id, vaga_id]):
        return

    contrato_id = mov_id = None
    operador_id = None

    # ------------------------------------------------------------ mensalistas
    secao("Mensalistas (contratos)")
    pedido = {
        "cliente_id": cliente_id,
        "veiculo_id": veiculo_id,
        "vaga_id": vaga_id,
        "valor_mensal": 150.00,
        "dia_vencimento": 10,
    }
    status, contrato = chamar("POST", "/mensalistas", pedido, token)
    contrato = dicionario(contrato)
    contrato_ok = status == 201 and Decimal(str(contrato.get("valor_mensal", "-1"))) == Decimal("150")
    conferir("contrato é criado com o valor mensal informado (201)", contrato_ok, (status, contrato))
    contrato_id = contrato.get("id") if contrato_ok else None

    status, corpo = chamar("POST", "/mensalistas", pedido, token)
    conferir("a mesma vaga não aceita um segundo contrato ativo (409)", status == 409, (status, corpo))
    status, corpo = chamar("POST", "/mensalistas", {**pedido, "cliente_id": 999999}, token)
    conferir("cliente inexistente é recusado (422)", status == 422, (status, corpo))
    status, corpo = chamar("POST", "/mensalistas", {**pedido, "dia_vencimento": 31}, token)
    conferir("vencimento acima do dia 28 é recusado (422)", status == 422, (status, corpo))

    status, painel = chamar("GET", "/painel", token=token)
    vaga_painel = next((v for v in dicionario(painel).get("vagas", []) if v["vaga_id"] == vaga_id), {})
    conferir(
        "painel: a vaga do contrato aparece como RESERVADA com a placa",
        vaga_painel.get("situacao") == "RESERVADA" and vaga_painel.get("placa") == placa,
        vaga_painel,
    )

    status, entrada = chamar("POST", "/movimentacoes/entrada", {"placa": placa}, token)
    entrada = dicionario(entrada)
    conferir(
        "mensalista entra na vaga do próprio contrato (201)",
        status == 201 and entrada.get("tipo") == "MENSALISTA" and entrada.get("vaga_id") == vaga_id,
        (status, entrada),
    )
    mov_id = entrada.get("id")
    if mov_id:
        status, saida = chamar("POST", f"/movimentacoes/{mov_id}/saida", {}, token)
        saida = dicionario(saida)
        conferir(
            "saída do mensalista não cobra nada e dispensa forma de pagamento (200)",
            status == 200 and Decimal(str(saida.get("valor_cobrado", "-1"))) == 0,
            (status, saida),
        )

    # ------------------------------------------------------------ mensalidades
    secao("Mensalidades")
    status, geradas = chamar("POST", "/mensalidades/gerar", {"competencia": "2099-12"}, token)
    geradas = dicionario(geradas)
    conferir("mensalidades do mês são geradas (200)", status == 200 and geradas.get("criadas", 0) >= 1, (status, geradas))

    mensalidade = mensalidade_da_placa(token, "2099-12", placa)
    conferir(
        "mensalidade do contrato está pendente, com o valor e o vencimento certos",
        mensalidade is not None
        and mensalidade["status"] == "PENDENTE"
        and Decimal(str(mensalidade["valor"])) == Decimal("150")
        and mensalidade["vencimento"] == "2099-12-10",
        mensalidade,
    )

    status, de_novo = chamar("POST", "/mensalidades/gerar", {"competencia": "2099-12"}, token)
    de_novo = dicionario(de_novo)
    conferir(
        "gerar de novo não duplica nada",
        status == 200 and de_novo.get("criadas") == 0 and de_novo.get("ja_existiam", 0) >= 1,
        (status, de_novo),
    )
    status, corpo = chamar("POST", "/mensalidades/gerar", {"competencia": "2099-13"}, token)
    conferir("competência inválida é recusada (422)", status == 422, (status, corpo))

    if mensalidade:
        mid = mensalidade["id"]
        status, paga = chamar("POST", f"/mensalidades/{mid}/pagar", {"forma_pagamento": "PIX"}, token)
        paga = dicionario(paga)
        conferir(
            "pagamento é registrado com a forma e a data (200)",
            status == 200 and paga.get("status") == "PAGA" and paga.get("forma_pagamento") == "PIX" and paga.get("pago_em"),
            (status, paga),
        )
        status, corpo = chamar("POST", f"/mensalidades/{mid}/pagar", {"forma_pagamento": "PIX"}, token)
        conferir("mensalidade já paga não é paga de novo (409)", status == 409, (status, corpo))
        status, corpo = chamar("POST", f"/mensalidades/{mid}/cancelar", token=token)
        conferir("mensalidade paga não pode ser cancelada (409)", status == 409, (status, corpo))

    chamar("POST", "/mensalidades/gerar", {"competencia": "2099-11"}, token)
    outra = mensalidade_da_placa(token, "2099-11", placa)
    if outra:
        oid = outra["id"]
        status, cancelada = chamar("POST", f"/mensalidades/{oid}/cancelar", token=token)
        conferir("mensalidade pendente é cancelada (200)", status == 200 and dicionario(cancelada).get("status") == "CANCELADA", (status, cancelada))
        status, corpo = chamar("POST", f"/mensalidades/{oid}/pagar", {"forma_pagamento": "DINHEIRO"}, token)
        conferir("mensalidade cancelada não pode ser paga (409)", status == 409, (status, corpo))

    # --------------------------------------------------------------- operadores
    secao("Operadores")
    login_novo = "teste" + str(random.randint(10000, 99999))
    novo = {"nome": "Operador Teste", "login": login_novo, "senha": "SenhaTeste123"}
    status, operador = chamar("POST", "/operadores", novo, token)
    operador = dicionario(operador)
    conferir(
        "operador é criado e a resposta não traz senha nem hash (201)",
        status == 201 and "senha" not in operador and "senha_hash" not in operador,
        (status, operador),
    )
    operador_id = operador.get("id")

    status, corpo = entrar(login_novo, "SenhaTeste123")
    conferir("o operador novo consegue entrar (200)", status == 200, (status, corpo))
    status, corpo = chamar("POST", "/operadores", novo, token)
    conferir("login repetido é recusado (409)", status == 409, (status, corpo))
    status, corpo = chamar("POST", "/operadores", {**novo, "login": "outro" + login_novo, "senha": "curta"}, token)
    conferir("senha com menos de 8 caracteres é recusada (422)", status == 422, (status, corpo))

    if operador_id:
        status, corpo = chamar("PATCH", f"/operadores/{operador_id}", {"senha": "OutraSenha456"}, token)
        conferir("senha do operador é trocada (200)", status == 200, (status, corpo))
        status, _ = entrar(login_novo, "SenhaTeste123")
        conferir("a senha antiga deixa de funcionar (401)", status == 401, status)
        status, _ = entrar(login_novo, "OutraSenha456")
        conferir("a senha nova funciona (200)", status == 200, status)

        status, corpo = chamar("PATCH", f"/operadores/{operador_id}", {"ativo": False}, token)
        conferir("operador é desativado (200)", status == 200, (status, corpo))
        status, _ = entrar(login_novo, "OutraSenha456")
        conferir("operador desativado não consegue entrar (401)", status == 401, status)

    if meu_id:
        status, corpo = chamar("DELETE", f"/operadores/{meu_id}", token=token)
        conferir("não dá para excluir o próprio acesso (409)", status == 409, (status, corpo))

    # ------------------------------------------------------------------ limpeza
    secao("Limpeza dos dados de teste")
    for competencia in ("2099-11", "2099-12"):
        status, lista = chamar("GET", f"/mensalidades?competencia={competencia}", token=token)
        if status == 200 and isinstance(lista, list):
            apagadas = [chamar("DELETE", f"/mensalidades/{m['id']}", token=token)[0] for m in lista]
            conferir(f"mensalidades de {competencia} excluídas", all(s == 204 for s in apagadas), apagadas)
    for caminho, existe in (
        (f"/operadores/{operador_id}", operador_id),
        (f"/movimentacoes/{mov_id}", mov_id),
        (f"/mensalistas/{contrato_id}", contrato_id),
        (f"/veiculos/{veiculo_id}", veiculo_id),
        (f"/clientes/{cliente_id}", cliente_id),
        (f"/vagas/{vaga_id}", vaga_id),
    ):
        if existe:
            status, _ = chamar("DELETE", caminho, token=token)
            conferir(f"exclusão lógica de {caminho} (204)", status == 204, status)

    print(f"\n{sum(resultados)} de {len(resultados)} verificações passaram.")
    if not all(resultados):
        print("Procure as linhas FALHOU acima: logo abaixo de cada uma está o que a API respondeu.")


if __name__ == "__main__":
    main()