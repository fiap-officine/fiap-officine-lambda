import logging
import os

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Configurações do Banco de Dados via Variáveis de Ambiente
DB_HOST = os.getenv("DB_HOST", os.getenv("DATABASE_HOST", "localhost"))
DB_PORT = int(os.getenv("DB_PORT", os.getenv("DATABASE_PORT", "5432")))
DB_NAME = os.getenv("DB_NAME", os.getenv("DATABASE_NAME", "officine"))
DB_USER = os.getenv("DB_USER", os.getenv("DATABASE_USER", "postgres"))
DB_PASSWORD = os.getenv("DB_PASSWORD", os.getenv("DATABASE_PASSWORD", "postgres"))
DATABASE_URL = os.getenv("DATABASE_URL")

_connection = None


def inicializar_schema() -> dict:
    """Cria e atualiza o schema de banco de dados compatível com o ecossistema e insere clientes de teste."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf VARCHAR(14),
                cpf_cnpj VARCHAR(14),
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco VARCHAR(500),
                status VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
                ativo BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS uq_clientes_cpf_cnpj ON clientes (cpf_cnpj);
            CREATE INDEX IF NOT EXISTS idx_clientes_cpf ON clientes (cpf);
            CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes (status);

            INSERT INTO clientes (nome, cpf, cpf_cnpj, email, telefone, status, ativo)
            VALUES ('Carlos Eduardo Ferreira', '52998224725', '52998224725', 'carlos.ferreira@email.com', '11988887777', 'ATIVO', true)
            ON CONFLICT (cpf_cnpj) DO NOTHING;

            INSERT INTO clientes (nome, cpf, cpf_cnpj, email, telefone, status, ativo)
            VALUES ('Mariana Souza Santos', '11144477735', '11144477735', 'mariana.santos@email.com', '11977776666', 'ATIVO', true)
            ON CONFLICT (cpf_cnpj) DO NOTHING;
        """)
    return {"status": "ok", "message": "Tabelas e clientes de teste inicializados com sucesso no RDS"}


def get_connection():
    """Obtém ou reutiliza uma conexão ativa com o PostgreSQL (otimizado para AWS Lambda)."""
    global _connection

    if _connection is not None:
        try:
            # Testa se a conexão ainda está viva
            _connection.execute("SELECT 1")
            return _connection
        except Exception:
            try:
                _connection.close()
            except Exception:
                pass
            _connection = None

    if DATABASE_URL:
        _connection = psycopg.connect(
            DATABASE_URL, row_factory=dict_row, autocommit=True
        )
    else:
        _connection = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            row_factory=dict_row,
            autocommit=True,
        )

    return _connection


def consultar_cliente_por_cpf(cpf_limpo: str) -> dict | None:
    """Consulta a existência e o status do cliente pelo CPF no banco de dados.

    Compatível tanto com a tabela 'clientes' do fiap-officine-database (cpf, status)
    quanto com o schema do fiap-officine-api (coluna 'cpf_cnpj' e 'ativo').
    """
    conn = get_connection()

    with conn.cursor() as cur:
        # 1. Tenta consulta padrão do schema fiap-officine-database (cpf, status)
        try:
            cur.execute(
                """
                SELECT id, nome, cpf, status
                FROM clientes
                WHERE cpf = %s
                LIMIT 1
                """,
                (cpf_limpo,),
            )
            row = cur.fetchone()
            if row:
                status_str = str(row.get("status", "ATIVO")).upper()
                return {
                    "id": str(row["id"]),
                    "nome": row["nome"],
                    "cpf": row.get("cpf", cpf_limpo),
                    "status": status_str,
                    "ativo": status_str == "ATIVO",
                }
        except psycopg.errors.UndefinedColumn:
            # Caso a coluna seja 'cpf_cnpj' (schema da aplicação)
            pass

        # 2. Fallback para schema com cpf_cnpj e ativo
        try:
            cur.execute(
                """
                SELECT id, nome, cpf_cnpj, ativo
                FROM clientes
                WHERE cpf_cnpj = %s
                LIMIT 1
                """,
                (cpf_limpo,),
            )
            row = cur.fetchone()
            if row:
                is_ativo = bool(row.get("ativo", True))
                return {
                    "id": str(row["id"]),
                    "nome": row["nome"],
                    "cpf": row.get("cpf_cnpj", cpf_limpo),
                    "status": "ATIVO" if is_ativo else "INATIVO",
                    "ativo": is_ativo,
                }
        except Exception as e:
            logger.error(f"Erro ao consultar cliente por cpf_cnpj: {e}")
            raise

    return None
