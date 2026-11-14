import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.clientes_client import ClienteServiceError, consultar_cliente_por_cpf


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("OS_SERVICE_URL", "https://api.exemplo.com/")
    monkeypatch.setenv("INTERNAL_API_TOKEN", "token-interno")


def _resposta(body: dict):
    response = MagicMock()
    response.read.return_value = json.dumps(body).encode()
    response.__enter__.return_value = response
    return response


def test_cliente_ativo():
    body = {"id": 7, "nome": "Maria", "cpf_cnpj": "52998224725", "ativo": True}
    with patch("urllib.request.urlopen", return_value=_resposta(body)) as urlopen:
        cliente = consultar_cliente_por_cpf("52998224725")
    assert cliente == {
        "id": "7",
        "nome": "Maria",
        "cpf": "52998224725",
        "status": "ATIVO",
        "ativo": True,
    }
    request = urlopen.call_args.args[0]
    assert (
        request.full_url
        == "https://api.exemplo.com/internal/clientes/status/52998224725"
    )
    assert request.get_header("X-internal-token") == "token-interno"


def test_cliente_inativo():
    body = {"id": 7, "nome": "Maria", "cpf_cnpj": "52998224725", "ativo": False}
    with patch("urllib.request.urlopen", return_value=_resposta(body)):
        assert consultar_cliente_por_cpf("52998224725")["status"] == "INATIVO"


def _http_error(code: int):
    return urllib.error.HTTPError("url", code, "erro", {}, io.BytesIO(b"{}"))


def test_cliente_inexistente_retorna_none():
    with patch("urllib.request.urlopen", side_effect=_http_error(404)):
        assert consultar_cliente_por_cpf("52998224725") is None


@pytest.mark.parametrize(
    "erro",
    [_http_error(500), _http_error(401), urllib.error.URLError("dns"), TimeoutError()],
)
def test_falhas_viram_cliente_service_error(erro):
    with (
        patch("urllib.request.urlopen", side_effect=erro),
        pytest.raises(ClienteServiceError),
    ):
        consultar_cliente_por_cpf("52998224725")


def test_sem_url_configurada(monkeypatch):
    monkeypatch.delenv("OS_SERVICE_URL")
    with pytest.raises(ClienteServiceError):
        consultar_cliente_por_cpf("52998224725")
