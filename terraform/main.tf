terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "fiap-officine-lambda"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  use_vpc     = length(var.subnet_ids) > 0 && length(var.security_group_ids) > 0
}

# ──────────────────────────────────────────────
# IAM Role para Execução da Lambda
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name_prefix        = "${local.name_prefix}-role-"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Permissões básicas de CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permissões de rede VPC (se subnets forem informadas)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count      = local.use_vpc ? 1 : 0
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# ──────────────────────────────────────────────
# Empacotamento do Código Python
# ──────────────────────────────────────────────
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/package"
  output_path = "${path.module}/build/lambda.zip"
}

# ──────────────────────────────────────────────
# Function Serverless de Autenticação
# ──────────────────────────────────────────────
resource "aws_lambda_function" "auth" {
  function_name    = "${local.name_prefix}-auth-lambda"
  description      = "Valida CPF, consulta cliente no RDS PostgreSQL e devolve token JWT"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 15
  memory_size      = 256

  environment {
    variables = {
      DB_HOST                         = var.db_host
      DB_PORT                         = tostring(var.db_port)
      DB_NAME                         = var.db_name
      DB_USER                         = var.db_user
      DB_PASSWORD                     = var.db_password
      JWT_SECRET_KEY                  = var.jwt_secret_key
      JWT_ALGORITHM                   = var.jwt_algorithm
      JWT_ACCESS_TOKEN_EXPIRE_MINUTES = tostring(var.jwt_expire_minutes)
    }
  }

  dynamic "vpc_config" {
    for_each = local.use_vpc ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }
}

resource "aws_cloudwatch_log_group" "auth" {
  name              = "/aws/lambda/${aws_lambda_function.auth.function_name}"
  retention_in_days = 7
}

# ──────────────────────────────────────────────
# Lambda Authorizer (para API Gateway HTTP API v2)
# ──────────────────────────────────────────────
resource "aws_lambda_function" "authorizer" {
  function_name    = "${local.name_prefix}-lambda-authorizer"
  description      = "Valida token JWT de clientes para autorização em APIs protegidas"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "authorizer.authorizer_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      JWT_SECRET_KEY = var.jwt_secret_key
      JWT_ALGORITHM  = var.jwt_algorithm
    }
  }
}

resource "aws_cloudwatch_log_group" "authorizer" {
  name              = "/aws/lambda/${aws_lambda_function.authorizer.function_name}"
  retention_in_days = 7
}
