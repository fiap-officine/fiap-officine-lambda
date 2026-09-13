import json
from unittest.mock import patch

from src.handler import lambda_handler
from src.token_service import verificar_token_jwt


class TestHandler:
    def test_cors_options_preflight(self):
        event = {"httpMethod": "OPTIONS"}
        response = lambda_handler(event)
        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]

    def test_cpf_ausente_retorna_400(self):
        event = {"body": json.dumps({})}
        response = lambda_handler(event)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "obrigatório" in body["detail"].lower()

    def test_cpf_invalido_retorna_422(self):
        event = {"body": json.dumps({"cpf": "111.111.111-11"})}
        response = lambda_handler(event)
        assert response["statusCode"] == 422
        body = json.loads(response["body"])
        assert "inválido" in body["detail"].lower()

    @patch("src.handler.consultar_cliente_por_cpf")
    def test_cliente_nao_encontrado_retorna_404(self, mock_consultar):
        mock_consultar.return_value = None

        event = {"body": json.dumps({"cpf": "529.982.247-25"})}
        response = lambda_handler(event)
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "não encontrado" in body["detail"].lower()
        mock_consultar.assert_called_once_with("52998224725")

    @patch("src.handler.consultar_cliente_por_cpf")
    def test_cliente_inativo_retorna_400(self, mock_consultar):
        mock_consultar.return_value = {
            "id": "cli-123",
            "nome": "Cliente Inativo",
            "cpf": "52998224725",
            "status": "INATIVO",
            "ativo": False,
        }

        event = {"body": json.dumps({"cpf": "529.982.247-25"})}
        response = lambda_handler(event)
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "inativo" in body["detail"].lower()

    @patch("src.handler.consultar_cliente_por_cpf")
    def test_cliente_ativo_gera_jwt_com_sucesso(self, mock_consultar):
        mock_consultar.return_value = {
            "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            "nome": "Carlos Silva",
            "cpf": "52998224725",
            "status": "ATIVO",
            "ativo": True,
        }

        event = {"body": json.dumps({"cpf": "529.982.247-25"})}
        response = lambda_handler(event)
        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] == 3600
        assert body["cliente"]["id"] == "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        assert body["cliente"]["status"] == "ATIVO"

        # Valida o token gerado
        payload = verificar_token_jwt(body["access_token"])
        assert payload["sub"] == "52998224725"
        assert payload["role"] == "cliente"
        assert payload["cliente_id"] == "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        assert payload["nome"] == "Carlos Silva"

    @patch("src.handler.consultar_cliente_por_cpf")
    def test_invocacao_direta_e_query_param(self, mock_consultar):
        mock_consultar.return_value = {
            "id": "1",
            "nome": "Carlos Silva",
            "cpf": "52998224725",
            "status": "ATIVO",
            "ativo": True,
        }

        # Via query parameters
        event_query = {"queryStringParameters": {"cpf": "529.982.247-25"}}
        resp_query = lambda_handler(event_query)
        assert resp_query["statusCode"] == 200

        # Invocação direta
        event_direct = {"cpf": "529.982.247-25"}
        resp_direct = lambda_handler(event_direct)
        assert resp_direct["statusCode"] == 200

    @patch("src.handler.consultar_cliente_por_cpf")
    def test_erro_interno_banco_retorna_500(self, mock_consultar):
        mock_consultar.side_effect = Exception("Falha de conexão com PostgreSQL RDS")

        event = {"body": json.dumps({"cpf": "529.982.247-25"})}
        response = lambda_handler(event)
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "erro interno" in body["detail"].lower()
