variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "sellia"
}

variable "environment" {
  description = "Ambiente (dev, staging, production)"
  type        = string
}
