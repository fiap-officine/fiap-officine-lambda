import os
from datetime import UTC, datetime, timedelta

from jose import jwt

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "fiap-officine-secret-key-default-change-me"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)


def gerar_token_jwt(cliente_id: str | int, cpf: str, nome: str) -> dict:
    """Gera e assina um token JWT com claims padronizados para autenticação de clientes."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": cpf,
        "cpf": cpf,
        "role": "cliente",
        "cliente_id": str(cliente_id),
        "nome": nome,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def verificar_token_jwt(token: str) -> dict:
    """Decodifica e valida o token JWT. Levanta JWTError se inválido ou expirado."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
