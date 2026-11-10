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
  description = "Subnets (opcional). Sem NAT, a Lambda em VPC não alcança o OS Service"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security Groups associados à Lambda"
  type        = list(string)
  default     = []
}

variable "os_service_url" {
  description = "URL base do OS Service (ex.: https://<api-gateway>), dono da base de clientes"
  type        = string
  default     = ""
}

variable "internal_api_token" {
  description = "Token service-to-service aceito em /internal/* do OS Service"
  type        = string
  sensitive   = true
  default     = ""
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
