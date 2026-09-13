output "auth_lambda_arn" {
  description = "ARN da Function Serverless de Autenticação"
  value       = aws_lambda_function.auth.arn
}

output "auth_lambda_invoke_arn" {
  description = "Invoke ARN para integração com o API Gateway"
  value       = aws_lambda_function.auth.invoke_arn
}

output "auth_lambda_name" {
  description = "Nome da função Lambda de Autenticação"
  value       = aws_lambda_function.auth.function_name
}

output "authorizer_lambda_arn" {
  description = "ARN do Lambda Authorizer"
  value       = aws_lambda_function.authorizer.arn
}

output "authorizer_lambda_invoke_arn" {
  description = "Invoke ARN do Lambda Authorizer"
  value       = aws_lambda_function.authorizer.invoke_arn
}
