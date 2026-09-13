import logging

from jose import JWTError

from src.token_service import verificar_token_jwt

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def authorizer_handler(event: dict, context=None) -> dict:
    """Lambda Authorizer para API Gateway HTTP API v2 (Simple Response).

    Valida o token Bearer JWT enviado no header Authorization e devolve
    isAuthorized: True/False e o contexto decodificado.
    """
    logger.info("Executando Lambda Authorizer")

    headers = event.get("headers", {}) or {}
    auth_header = headers.get("authorization") or headers.get("Authorization")

    if not auth_header:
        logger.warning("Cabeçalho Authorization ausente")
        return {"isAuthorized": False}

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Formato do cabeçalho Authorization inválido (esperado: Bearer <token>)")
        return {"isAuthorized": False}

    token = parts[1].strip()

    try:
        payload = verificar_token_jwt(token)
        sub = payload.get("sub")
        if not sub:
            return {"isAuthorized": False}

        logger.info(f"Token JWT validado com sucesso para subject: {sub}")
        return {
            "isAuthorized": True,
            "context": {
                "sub": str(sub),
                "role": str(payload.get("role", "cliente")),
                "cliente_id": str(payload.get("cliente_id", "")),
                "nome": str(payload.get("nome", "")),
            },
        }
    except JWTError as e:
        logger.warning(f"Falha na validação do token JWT: {e}")
        return {"isAuthorized": False}
    except Exception as e:
        logger.error(f"Erro inesperado no authorizer: {e}")
        return {"isAuthorized": False}
