import re


def formatar_cpf(documento: str) -> str:
    """Remove pontuação e caracteres não-numéricos do documento."""
    if not documento:
        return ""
    return re.sub(r"\D", "", documento)


def validar_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro utilizando o algoritmo oficial dos dígitos verificadores (módulo 11).

    Regras:
    1. Remove caracteres não numéricos.
    2. Deve possuir exatamente 11 dígitos.
    3. Rejeita números com todos os dígitos iguais (ex: 111.111.111-11).
    4. Calcula e valida o primeiro dígito verificador.
    5. Calcula e valida o segundo dígito verificador.
    """
    numeros = formatar_cpf(cpf)

    if len(numeros) != 11:
        return False

    # Bloqueia números com todos os dígitos repetidos
    if numeros == numeros[0] * 11:
        return False

    # Primeiro dígito verificador
    soma = sum(int(numeros[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(numeros[9]) != digito1:
        return False

    # Segundo dígito verificador
    soma = sum(int(numeros[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    return int(numeros[10]) == digito2
