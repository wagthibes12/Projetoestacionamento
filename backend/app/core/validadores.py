"""Validações e normalizações de documentos e placas (sem dependências externas)."""
import re

_PLACA_ANTIGA = re.compile(r"[A-Z]{3}\d{4}")
_PLACA_MERCOSUL = re.compile(r"[A-Z]{3}\d[A-Z]\d{2}")


def _cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(cpf[n]) * (posicao + 1 - n) for n in range(posicao))
        if (soma * 10 % 11) % 10 != int(cpf[posicao]):
            return False
    return True


def _digito_cnpj(base: str, pesos: list[int]) -> int:
    # O valor de cada caractere é o código ASCII menos 48: letras e números
    # entram no mesmo cálculo. Isso atende o CNPJ alfanumérico, adotado a partir
    # de julho de 2026, e continua igual para os CNPJs só com números.
    soma = sum((ord(caractere) - 48) * peso for caractere, peso in zip(base, pesos))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def _cnpj_valido(cnpj: str) -> bool:
    if not re.fullmatch(r"[0-9A-Z]{12}\d{2}", cnpj) or cnpj == cnpj[0] * 14:
        return False
    pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digito1 = _digito_cnpj(cnpj[:12], pesos)
    digito2 = _digito_cnpj(cnpj[:12] + str(digito1), [6] + pesos)
    return cnpj[12:] == f"{digito1}{digito2}"


def normalizar_cpf_cnpj(valor: str) -> str:
    """Remove pontuação, valida os dígitos verificadores e devolve só os caracteres."""
    limpo = re.sub(r"[^0-9A-Za-z]", "", valor).upper()
    if len(limpo) == 11 and _cpf_valido(limpo):
        return limpo
    if len(limpo) == 14 and _cnpj_valido(limpo):
        return limpo
    raise ValueError("CPF ou CNPJ inválido.")


def normalizar_placa(valor: str) -> str:
    """Deixa a placa em maiúsculas e sem hífen/espaço, e confere o formato."""
    placa = re.sub(r"[\s-]", "", valor).upper()
    if not (_PLACA_ANTIGA.fullmatch(placa) or _PLACA_MERCOSUL.fullmatch(placa)):
        raise ValueError("Placa inválida. Use o formato ABC1234 ou ABC1D23.")
    return placa