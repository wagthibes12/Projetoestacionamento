"""Teste automático de tudo que a API faz hoje: login, cadastros, entrada e saída de veículos e painel de vagas.

Uso (a API precisa estar rodando em outro terminal):
    cd backend
    python testar_tudo.py

O script faz login, executa as chamadas e imprime OK ou FALHOU em cada uma.
Os dados de teste usam valores sorteados (CPF, placas e código de vaga) e são
excluídos no final, então o script pode ser repetido. Se já existir um preço de
horista ativo, ele é usado e NÃO é alterado.
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
    """Garante um dicionário, mesmo quando a API devolve texto ou lista."""
    return conteudo if isinstance(conteudo, dict) else {}


def conferir(descricao: str, condicao: bool, detalhe=None) -> None:
    resultados.append(bool(condicao))
    print(("OK      " if condicao else "FALHOU  ") + descricao)
    if not condicao and detalhe is not None:
        print(f"        recebido: {detalhe}")


def gerar_cpf_valido() -> str:
    """Sorteia um CPF com dígitos verificadores corretos (para o teste ser repetível)."""
    digitos = [random.randint(0, 9) for _ in range(9)]
    for posicao in (9, 10):
        soma = sum(digitos[n] * (posicao + 1 - n) for n in range(posicao))
        digitos.append((soma * 10 % 11) % 10)
    return "".join(str(d) for d in digitos)


def secao(titulo: str) -> None:
    print(f"\n--- {titulo}")


def main() -> None:
    print("Faça login com o operador cadastrado.")
    login = input("Login: ").strip()
    senha = getpass("Senha (não aparece enquanto você digita): ")

    # ------------------------------------------------------------------ login
    secao("Login")
    try:
        status, corpo = chamar("POST", "/auth/login", {"login": login, "senha": senha})
    except urllib.error.URLError:
        print("Não consegui falar com a API em", URL)
        print("Confira se ela está rodando (uvicorn app.main:app --reload) em outro terminal.")
        return
    conferir("login devolve o token (200)", status == 200 and "access_token" in dicionario(corpo), (status, corpo))
    if status != 200:
        return
    token = corpo["access_token"]

    status, corpo = chamar("POST", "/auth/login", {"login": login, "senha": senha + "x"})
    conferir("senha errada é recusada (401)", status == 401, (status, corpo))
    status, corpo = chamar("GET", "/auth/eu")
    conferir("rota protegida sem token é recusada (401)", status == 401, status)
    status, corpo = chamar("GET", "/auth/eu", token=token)
    conferir("rota protegida com token devolve o operador (200)", status == 200 and "nome" in dicionario(corpo), (status, corpo))

    # --------------------------------------------------------------- clientes
    secao("Clientes")
    cpf = gerar_cpf_valido()
    cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    novo_cliente = {"nome": "Cliente Teste", "cpf_cnpj": cpf_formatado}

    status, cliente = chamar("POST", "/clientes", novo_cliente, token)
    cliente = dicionario(cliente)
    cliente_ok = status == 201 and cliente.get("cpf_cnpj") == cpf
    conferir("cliente é criado e o CPF fica sem pontuação (201)", cliente_ok, (status, cliente))
    conferir("cliente guarda quem o criou (criado_por)", cliente_ok and cliente.get("criado_por") is not None, cliente)
    cliente_id = cliente.get("id") if cliente_ok else None

    status, corpo = chamar("POST", "/clientes", novo_cliente, token)
    conferir("CPF repetido é recusado (409)", status == 409, (status, corpo))
    status, corpo = chamar("POST", "/clientes", {"nome": "X", "cpf_cnpj": "111.111.111-11"}, token)
    conferir("CPF inválido é recusado (422)", status == 422, (status, corpo))

    if cliente_id:
        status, lista = chamar("GET", "/clientes", token=token)
        conferir(
            "cliente aparece na listagem",
            status == 200 and isinstance(lista, list) and any(c["id"] == cliente_id for c in lista),
            status,
        )
        status, corpo = chamar("PATCH", f"/clientes/{cliente_id}", {"telefone": "49999990000"}, token)
        conferir(
            "cliente é editado e guarda quem editou (atualizado_por)",
            status == 200 and dicionario(corpo).get("atualizado_por") is not None,
            (status, corpo),
        )

    # -------------------------------------------------------------- veículos
    secao("Veículos")
    placa_cadastro = "ABC" + str(random.randint(1000, 9999))
    status, veiculo = chamar(
        "POST",
        "/veiculos",
        {"placa": placa_cadastro.lower()[:3] + "-" + placa_cadastro[3:], "cliente_id": cliente_id},
        token,
    )
    veiculo = dicionario(veiculo)
    veiculo_ok = status == 201 and veiculo.get("placa") == placa_cadastro
    conferir("veículo é criado e a placa é padronizada (201)", veiculo_ok, (status, veiculo))
    status, corpo = chamar("POST", "/veiculos", {"placa": "12-ABCDE"}, token)
    conferir("placa inválida é recusada (422)", status == 422, (status, corpo))
    if veiculo_ok:
        status, lista = chamar("GET", "/veiculos", token=token)
        conferir(
            "veículo aparece na listagem",
            status == 200 and isinstance(lista, list) and any(v["id"] == veiculo["id"] for v in lista),
            status,
        )

    # ------------------------------------------------------------------ vagas
    secao("Vagas")
    codigo = "T" + str(random.randint(100, 999))
    status, vaga = chamar("POST", "/vagas", {"codigo": codigo.lower()}, token)
    vaga = dicionario(vaga)
    vaga_ok = status == 201 and vaga.get("codigo") == codigo
    conferir("vaga é criada e o código fica em maiúsculas (201)", vaga_ok, (status, vaga))
    if vaga_ok:
        status, corpo = chamar("POST", "/vagas", {"codigo": codigo}, token)
        conferir("código de vaga repetido é recusado (409)", status == 409, (status, corpo))

    # ----------------------------------------------------------------- preços
    secao("Preços")
    preco_teste_id = None
    status, precos = chamar("GET", "/precos", token=token)
    precos = precos if status == 200 and isinstance(precos, list) else []
    horista = next((p for p in precos if p["tipo"] == "HORISTA" and p["ativo"]), None)
    if horista is not None:
        valor_hora = Decimal(str(horista["valor"]))
        print("AVISO   já existe preço de horista ativo: ele será usado e não será alterado.")
    else:
        status, corpo = chamar("POST", "/precos", {"tipo": "HORISTA", "valor": 5.00}, token)
        conferir("preço de horista é criado (201)", status == 201, (status, corpo))
        status, corpo = chamar("POST", "/precos", {"tipo": "HORISTA", "valor": 6.00}, token)
        conferir("novo preço substitui o anterior (201)", status == 201, (status, corpo))
        preco_teste_id = dicionario(corpo).get("id") if status == 201 else None
        status, precos = chamar("GET", "/precos", token=token)
        vigentes = [p for p in precos if p["tipo"] == "HORISTA"] if status == 200 else []
        conferir(
            "só o preço novo (6,00) continua vigente",
            len(vigentes) == 1 and Decimal(str(vigentes[0]["valor"])) == Decimal("6"),
            vigentes,
        )
        valor_hora = Decimal("6")

    # ----------------------------------------------- entrada, cobrança e saída
    secao("Entrada e saída de veículos")
    status, painel = chamar("GET", "/painel", token=token)
    painel = dicionario(painel)
    if status != 200 or painel.get("livres", 0) < 1:
        print("Sem vaga livre para testar a entrada. Pulando esta parte.")
        mov_id = veiculo_b1_id = None
    else:
        livres_antes, ocupadas_antes = painel["livres"], painel["ocupadas"]
        placa = "TST" + str(random.randint(1000, 9999))
        status, entrada = chamar("POST", "/movimentacoes/entrada", {"placa": placa.lower()}, token)
        entrada = dicionario(entrada)
        entrada_ok = status == 201 and entrada.get("tipo") == "HORISTA" and entrada.get("status") == "ABERTA"
        conferir("entrada do horista é registrada em uma vaga livre (201)", entrada_ok, (status, entrada))
        mov_id = entrada.get("id") if entrada_ok else None
        veiculo_b1_id = entrada.get("veiculo_id") if entrada_ok else None

        if entrada_ok:
            vaga_id = entrada["vaga_id"]
            conferir("a placa é padronizada em maiúsculas", entrada["placa"] == placa, entrada)

            status, corpo = chamar("POST", "/movimentacoes/entrada", {"placa": placa}, token)
            conferir("o mesmo veículo não entra duas vezes (409)", status == 409, (status, corpo))
            status, corpo = chamar("POST", "/movimentacoes/entrada", {"placa": "TST9999", "vaga_id": vaga_id}, token)
            conferir("vaga já ocupada é recusada (409)", status == 409, (status, corpo))
            status, corpo = chamar("POST", "/movimentacoes/entrada", {"placa": "12-ABCDE"}, token)
            conferir("placa inválida na entrada é recusada (422)", status == 422, (status, corpo))

            status, abertas = chamar("GET", "/movimentacoes/abertas", token=token)
            conferir(
                "o veículo aparece entre os estacionados agora",
                status == 200 and isinstance(abertas, list) and any(m["id"] == mov_id for m in abertas),
                status,
            )

            status, painel = chamar("GET", "/painel", token=token)
            painel = dicionario(painel)
            conferir(
                "painel: uma vaga a menos livre e uma a mais ocupada",
                status == 200
                and painel.get("livres") == livres_antes - 1
                and painel.get("ocupadas") == ocupadas_antes + 1,
                (status, painel.get("livres"), painel.get("ocupadas")),
            )
            vaga_painel = next((v for v in painel.get("vagas", []) if v["vaga_id"] == vaga_id), {})
            conferir(
                "painel: a vaga mostra OCUPADA com a placa",
                vaga_painel.get("situacao") == "OCUPADA" and vaga_painel.get("placa") == placa,
                vaga_painel,
            )

            status, cobranca = chamar("GET", f"/movimentacoes/{mov_id}/cobranca", token=token)
            cobranca = dicionario(cobranca)
            conferir(
                "cobrança de quem acabou de entrar: 1 hora (mínimo) ao valor da hora",
                status == 200
                and cobranca.get("horas_cobradas") == 1
                and Decimal(str(cobranca.get("valor_total", "-1"))) == valor_hora,
                (status, cobranca),
            )

            status, corpo = chamar("POST", f"/movimentacoes/{mov_id}/saida", {}, token)
            conferir("saída sem forma de pagamento é recusada (422)", status == 422, (status, corpo))

            status, saida = chamar("POST", f"/movimentacoes/{mov_id}/saida", {"forma_pagamento": "DINHEIRO"}, token)
            saida = dicionario(saida)
            conferir(
                "saída é registrada e o valor cobrado é gravado (200)",
                status == 200
                and saida.get("status") == "FINALIZADA"
                and Decimal(str(saida.get("valor_cobrado", "-1"))) == valor_hora,
                (status, saida),
            )

            status, corpo = chamar("POST", f"/movimentacoes/{mov_id}/saida", {"forma_pagamento": "PIX"}, token)
            conferir("a mesma saída não pode ser registrada de novo (404)", status == 404, (status, corpo))

            status, painel = chamar("GET", "/painel", token=token)
            conferir(
                "painel: a vaga ficou livre de novo",
                status == 200 and dicionario(painel).get("livres") == livres_antes,
                (status, dicionario(painel).get("livres")),
            )

    # ---------------------------------------------------------------- limpeza
    secao("Limpeza dos dados de teste")
    itens = (
        (f"/movimentacoes/{mov_id}", mov_id),
        (f"/veiculos/{veiculo_b1_id}", veiculo_b1_id),
        (f"/veiculos/{veiculo.get('id')}", veiculo_ok),
        (f"/clientes/{cliente_id}", cliente_id),
        (f"/vagas/{vaga.get('id')}", vaga_ok),
        (f"/precos/{preco_teste_id}", preco_teste_id),
    )
    for caminho, existe in itens:
        if existe:
            status, _ = chamar("DELETE", caminho, token=token)
            conferir(f"exclusão lógica de {caminho} (204)", status == 204, status)
    if cliente_id:
        status, _ = chamar("GET", f"/clientes/{cliente_id}", token=token)
        conferir("cliente excluído deixa de aparecer (404)", status == 404, status)

    print(f"\n{sum(resultados)} de {len(resultados)} verificações passaram.")
    if not all(resultados):
        print("Procure as linhas FALHOU acima: logo abaixo de cada uma está o que a API respondeu.")


if __name__ == "__main__":
    main()