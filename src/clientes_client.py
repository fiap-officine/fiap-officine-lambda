"""Consulta do status do cliente no OS Service (dono da base de clientes).

Fase 4: a Lambda não acessa mais o banco do OS Service. Ela chama
`GET {OS_SERVICE_URL}/internal/clientes/status/{cpf}` com o header
`x-internal-token` (token service-to-service).
"""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = float(os.getenv("OS_SERVICE_TIMEOUT_SECONDS", "5"))


class ClienteServiceError(Exception):
    """Falha ao consultar o OS Service (rede, 5xx ou resposta inesperada)."""


def consultar_cliente_por_cpf(cpf_limpo: str) -> dict | None:
    """Retorna {id, nome, cpf, status, ativo} ou None se o cliente não existe."""
    base_url = os.getenv("OS_SERVICE_URL", "").rstrip("/")
    token = os.getenv("INTERNAL_API_TOKEN", "")
    if not base_url:
        raise ClienteServiceError("OS_SERVICE_URL não configurada")

    request = urllib.request.Request(
        f"{base_url}/internal/clientes/status/{cpf_limpo}",
        headers={"x-internal-token": token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise ClienteServiceError(f"OS Service respondeu {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ClienteServiceError(f"Falha ao consultar o OS Service: {exc}") from exc

    ativo = bool(body.get("ativo"))
    return {
        "id": str(body["id"]),
        "nome": body["nome"],
        "cpf": body.get("cpf_cnpj", cpf_limpo),
        "status": "ATIVO" if ativo else "INATIVO",
        "ativo": ativo,
    }
