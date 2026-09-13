from src.authorizer import authorizer_handler
from src.token_service import gerar_token_jwt


class TestAuthorizer:
    def test_header_ausente_retorna_nao_autorizado(self):
        event = {"headers": {}}
        res = authorizer_handler(event)
        assert res["isAuthorized"] is False

    def test_formato_header_invalido_retorna_nao_autorizado(self):
        event = {"headers": {"authorization": "Basic 12345"}}
        res = authorizer_handler(event)
        assert res["isAuthorized"] is False

    def test_token_invalido_retorna_nao_autorizado(self):
        event = {"headers": {"authorization": "Bearer token.invalido.123"}}
        res = authorizer_handler(event)
        assert res["isAuthorized"] is False

    def test_token_valido_retorna_autorizado_com_contexto(self):
        token_info = gerar_token_jwt(
            cliente_id="cli-123",
            cpf="52998224725",
            nome="Carlos Silva",
        )
        token = token_info["access_token"]

        event = {"headers": {"authorization": f"Bearer {token}"}}
        res = authorizer_handler(event)

        assert res["isAuthorized"] is True
        assert res["context"]["sub"] == "52998224725"
        assert res["context"]["role"] == "cliente"
        assert res["context"]["cliente_id"] == "cli-123"
        assert res["context"]["nome"] == "Carlos Silva"
