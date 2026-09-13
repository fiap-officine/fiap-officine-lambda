import base64
import json
import logging

from src.database import consultar_cliente_por_cpf
from src.token_service import gerar_token_jwt
from src.validators import formatar_cpf, validar_cpf

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}


def _response(status_code: int, body: dict) -> dict:
    """Monta a resposta formatada para o API Gateway HTTP API v2."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


def _extrair_dados(event: dict) -> dict:
    """Extrai os dados de entrada tratando invocações diretas ou via API Gateway."""
    if not isinstance(event, dict):
        return {}

    # Trata requisição OPTIONS para CORS pre-flight
    http_method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
    )
    if http_method == "OPTIONS":
        return {"__is_options__": True}

    body = event.get("body")
    if body:
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        if isinstance(body, str):
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {}
        if isinstance(body, dict):
            return body

    # Fallback para query parameters
    query_params = event.get("queryStringParameters")
    if query_params and isinstance(query_params, dict):
        return query_params

    # Fallback para invocação direta (payload no próprio evento)
    return event


def lambda_handler(event: dict, context=None) -> dict:
    """Handler principal da Function Serverless (AWS Lambda).

    Fluxo:
    1. Extrai o CPF do payload ou query param.
    2. Valida matematicamente o CPF (dígitos verificadores - módulo 11).
    3. Consulta a existência e o status do cliente no PostgreSQL (RDS).
    4. Gera e devolve um token JWT válido para consumo das APIs protegidas.
    """
    logger.info("Iniciando processamento de autenticação na Lambda")

    dados = _extrair_dados(event)

    # Resposta para CORS pre-flight
    if dados.get("__is_options__"):
        return _response(200, {"message": "OK"})

    # Inicialização / migração automática de schema
    if dados.get("action") == "migrate" or dados.get("migrate") is True:
        try:
            from src.database import inicializar_schema
            resultado = inicializar_schema()
            return _response(200, resultado)
        except Exception as e:
            logger.error(f"Erro ao inicializar schema: {e}")
            return _response(500, {"error": "Internal Server Error", "detail": str(e)})

    cpf = dados.get("cpf") or dados.get("cpf_cnpj")
    if not cpf:
        return _response(
            400,
            {
                "error": "Bad Request",
                "detail": "O campo 'cpf' é obrigatório no corpo da requisição.",
            },
        )

    # 1. Validar CPF matematicamente
    if not validar_cpf(str(cpf)):
        return _response(
            422,
            {
                "error": "Unprocessable Entity",
                "detail": "CPF inválido ou dígitos verificadores incorretos.",
            },
        )

    cpf_limpo = formatar_cpf(str(cpf))

    # 2. Consultar existência e status na base de dados
    try:
        cliente = consultar_cliente_por_cpf(cpf_limpo)
    except Exception as e:
        logger.error(f"Erro ao conectar ou consultar o banco de dados: {e}")
        return _response(
            500,
            {
                "error": "Internal Server Error",
                "detail": "Erro interno ao consultar a base de dados de clientes.",
            },
        )

    if not cliente:
        return _response(
            404,
            {
                "error": "Not Found",
                "detail": "Cliente não encontrado na base de dados.",
            },
        )

    if not cliente.get("ativo"):
        return _response(
            400,
            {
                "error": "Bad Request",
                "detail": f"Cliente inativo no sistema (status: {cliente.get('status', 'INATIVO')}).",
            },
        )

    # 3. Gerar e devolver token JWT válido
    token_data = gerar_token_jwt(
        cliente_id=cliente["id"],
        cpf=cliente["cpf"],
        nome=cliente["nome"],
    )

    response_body = {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"],
        "cliente": {
            "id": cliente["id"],
            "nome": cliente["nome"],
            "cpf": cliente["cpf"],
            "status": cliente["status"],
        },
    }

    logger.info(f"Token gerado com sucesso para o cliente ID={cliente['id']}")
    return _response(200, response_body)
