variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "sa-east-1"
}

variable "environment" {
  description = "Ambiente (homolog, prod)"
  type        = string
  default     = "homolog"
}

variable "project" {
  description = "Nome do projeto"
  type        = string
  default     = "fiap-officine"
}

variable "vpc_id" {
  description = "ID da VPC (gerada pelo repo fiap-officine-kubernets)"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnets privadas para a Lambda acessar o RDS"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security Groups associados à Lambda"
  type        = list(string)
  default     = []
}

variable "db_host" {
  description = "Host do PostgreSQL RDS"
  type        = string
  default     = "localhost"
}

variable "db_port" {
  description = "Porta do PostgreSQL RDS"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Nome do banco de dados"
  type        = string
  default     = "officine"
}

variable "db_user" {
  description = "Usuário do banco de dados"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Senha do banco de dados"
  type        = string
  sensitive   = true
  default     = "postgres"
}

variable "jwt_secret_key" {
  description = "Chave secreta para assinatura dos tokens JWT"
  type        = string
  sensitive   = true
  default     = "fiap-officine-secret-key-change-in-production"
}

variable "jwt_algorithm" {
  description = "Algoritmo de criptografia do token JWT"
  type        = string
  default     = "HS256"
}

variable "jwt_expire_minutes" {
  description = "Tempo de expiração do token JWT em minutos"
  type        = number
  default     = 60
}
