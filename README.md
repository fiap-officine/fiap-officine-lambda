# ⚡ fiap-officine-lambda — Function Serverless de Autenticação (AWS Lambda)

Repositório responsável pela **Function Serverless (AWS Lambda)** do ecossistema **fiap-officine** (Tech Challenge FIAP).

---

## 🎯 Objetivo e Responsabilidades

Esta função serverless provê o serviço centralizado e desacoplado de identificação e autenticação de clientes:
1. **Validar o CPF do cliente**: Aplicação rigorosa do algoritmo oficial dos dígitos verificadores (módulo 11) e bloqueio de sequências com dígitos repetidos.
2. **Consultar existência e status do cliente**: Conexão com o banco de dados **AWS RDS PostgreSQL** (gerenciado no repositório `fiap-officine-database`) para verificar se o cliente existe e possui status `ATIVO`.
3. **Gerar e devolver token JWT**: Assinatura criptográfica do token de acesso contendo os claims necessários (`sub`, `role: cliente`, `cliente_id`, `nome`) para consumo das APIs protegidas.
4. **Lambda Authorizer**: Handler para autorização de requisições no **AWS API Gateway HTTP API v2** (provisionado no repositório `fiap-officine-kubernets`).

---

## 🏗️ Arquitetura e Integração com a Infraestrutura

```
                    ┌───────────────────────────┐
                    │    CLIENTE (App / Web)    │
                    └─────────────┬─────────────┘
                                  │ 1. POST /auth/login (CPF)
                                  ▼
                    ┌───────────────────────────┐
                    │  AWS API Gateway HTTP v2  │
                    │ (fiap-officine-kubernets) │
                    └─────────────┬─────────────┘
                                  │ Rota Pública /auth/*
                                  ▼
      ┌───────────────────────────────────────────────────────┐
      │         fiap-officine-lambda (ESTE REPOSITÓRIO)       │
      │                                                       │
      │  1. Valida CPF (Módulo 11)                           │
      │  2. Consulta status no RDS PostgreSQL (clientes)      │
      │  3. Emite token JWT (HS256)                           │
      └───────────────────────────┬───────────────────────────┘
                                  │ Conexão privada (Porta 5432)
                                  ▼
                    ┌───────────────────────────┐
                    │    AWS RDS PostgreSQL     │
                    │  (fiap-officine-database) │
                    └───────────────────────────┘
```

---

## 🚀 Tecnologias Utilizadas

* **Python 3.12** (Runtime oficial AWS Lambda)
* **uv**: Gerenciador de pacotes e ambientes virtuais de altíssima performance
* **psycopg 3 (`psycopg[binary]`)**: Driver PostgreSQL moderno e nativo
* **python-jose**: Geração e validação de tokens JWT
* **pytest & pytest-cov**: Testes unitários com cobertura de código
* **Terraform**: Infraestrutura como Código (IaC) para provisionamento da Lambda, IAM Roles e CloudWatch
* **GitHub Actions**: Pipeline de CI/CD para lint, testes e deploy contínuo

---

## 📦 Estrutura do Repositório

```
fiap-officine-lambda/
├── src/
│   ├── __init__.py
│   ├── validators.py      # Algoritmo matemático oficial de validação de CPF
│   ├── database.py        # Conexão e queries com PostgreSQL usando psycopg 3
│   ├── token_service.py   # Emissão e validação de tokens JWT
│   ├── handler.py         # Entry point principal para o API Gateway (POST /auth/login)
│   └── authorizer.py      # Entry point do Lambda Authorizer (validação de JWT)
├── tests/
│   ├── __init__.py
│   ├── test_validators.py # Testes de validação de CPF
│   ├── test_handler.py    # Testes do fluxo de autenticação e status do cliente
│   └── test_authorizer.py # Testes do authorizer JWT
├── terraform/
│   ├── main.tf            # Recursos da Lambda, IAM Roles, CloudWatch e VPC
│   ├── variables.tf       # Parâmetros configuráveis
│   ├── outputs.tf         # ARNs e identificadores exportados
│   └── terraform.tfvars.example
├── .github/workflows/
│   ├── pr-check.yml       # Testes e lint no PR
│   └── deploy.yml         # Deploy automatizado na AWS
├── pyproject.toml         # Configuração do projeto e dependências gerenciadas pelo uv
└── README.md
```

---

## 🛠️ Como Executar e Testar Localmente

### Pré-requisitos
* Python 3.12+ instalado
* [uv](https://docs.astral.sh/uv/) instalado (`pip install uv` ou `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Instalação das Dependências
```bash
uv sync
```

### Executar os Testes Unitários
```bash
uv run pytest -v
```

### Executar Verificação de Lint com Ruff
```bash
uv run ruff check .
```

---

## ⚙️ Variáveis de Ambiente da Lambda

| Variável | Descrição | Valor Padrão |
|---|---|---|
| `DB_HOST` | Host do banco PostgreSQL (RDS) | `localhost` |
| `DB_PORT` | Porta de conexão | `5432` |
| `DB_NAME` | Nome do banco de dados | `officine` |
| `DB_USER` | Usuário do banco | `postgres` |
| `DB_PASSWORD` | Senha do banco | - |
| `JWT_SECRET_KEY` | Chave secreta compartilhada para assinatura do JWT | - |
| `JWT_ALGORITHM` | Algoritmo de assinatura | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Tempo de expiração do token | `60` |

---

## 🌐 Integração com os Demais Repositórios

1. **`fiap-officine-kubernets`**:
   - O API Gateway HTTP v2 consome o output `auth_lambda_arn` e `authorizer_lambda_arn` para rotear requisições em `/auth/*` e proteger as rotas da aplicação no cluster Kubernetes.
2. **`fiap-officine-database`**:
   - A Lambda conecta-se diretamente ao RDS PostgreSQL através das subnets privadas da VPC na porta `5432`.
3. **`Pos-Tech-Fiap`**:
   - A aplicação de Ordens de Serviço valida os tokens JWT gerados por esta Lambda utilizando a mesma `JWT_SECRET_KEY` e pode delegar chamadas de login para o endpoint da Lambda via variável `AUTH_LAMBDA_URL`.

---

## 🛰️ Endpoint Ativo e Testes em Homologação (AWS sa-east-1)

A Function Serverless está ativa e integrada ao API Gateway no endpoint público:

**URL:** `POST https://kai652jumh.execute-api.sa-east-1.amazonaws.com/auth/login`

### Exemplo de Autenticação com Sucesso:
```powershell
$body = @{ cpf = "52998224725" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "https://kai652jumh.execute-api.sa-east-1.amazonaws.com/auth/login" -Method Post -Body $body -ContentType "application/json"
$response | ConvertTo-Json
```

**Retorno HTTP 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 7200,
  "cliente": {
    "id": "1",
    "nome": "Carlos Eduardo Ferreira",
    "cpf": "52998224725",
    "status": "ATIVO"
  }
}
```

---

## 🔒 Governança de Branches e CI/CD

* **Branches Protegidas**: `main` (Produção) e `develop` (Homologação).
* **Bloqueio de Commits Diretos**: Obrigatório abertura de **Pull Requests (PR)**.
* **Status Checks**: Execução de linter (`ruff`), testes unitários (`pytest`) e empacotamento.
* **Deploy Automático**:
  - Push/Merge em `develop` ➔ Deploy automático para **Homologação** (`sa-east-1`).
  - Push/Merge em `main` ➔ Deploy automático para **Produção**.


