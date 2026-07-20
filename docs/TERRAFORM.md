# Terraform — Infraestructura como Código (AWS)

Este directorio contiene la infraestructura completa de SellIA desplegable en AWS mediante Terraform.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        CloudFront CDN                        │
│                   (Static Assets + Cache)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Application Load Balancer                  │
│              (SSL Termination, Health Checks)               │
└───────────┬───────────────────────────────┬─────────────────┘
            │                               │
┌───────────▼──────────┐        ┌───────────▼──────────┐
│    EKS Cluster       │        │    S3 Buckets        │
│  ┌──────────────┐   │        │  • Logs (ALB/CDN)   │
│  │ Backend Pods │   │        │  • Static Assets    │
│  │ Frontend Pods│   │        └─────────────────────┘
│  │ Nginx Pods   │   │
│  │ ClamAV Pods  │   │
│  └──────────────┘   │
└─────────────────────┘
         │
┌────────┴────────────────┐
│      Data Layer          │
│  ┌──────────────────┐   │
│  │ RDS PostgreSQL 16│   │
│  │ (Multi-AZ, enc)  │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │ ElastiCache Redis│   │
│  │ (Cluster, enc)   │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

## Estructura

```
infra/terraform/
├── main.tf              # Entry point, integra todos los módulos
├── variables.tf         # Variables configurables
├── outputs.tf           # Outputs del stack
├── backend.tfvars.example # Ejemplo de variables sensibles
└── modules/
    ├── vpc/             # VPC, subnets públicas/privadas/DB/ElastiCache
    ├── eks/             # Cluster EKS 1.29, node groups, Fargate, IRSA
    ├── rds/             # PostgreSQL 16, Multi-AZ, backups
    ├── redis/           # ElastiCache Redis 7, cluster mode
    ├── alb/             # ALB, target groups, listeners HTTPS
    ├── s3/              # Buckets para logs y assets
    ├── cloudfront/      # CDN con S3 + ALB origins
    └── iam/             # Roles EKS cluster y nodos
```

## Prerrequisitos

- Terraform >= 1.5.0
- AWS CLI configurado
- ACM certificate en `us-east-1` (para ALB y CloudFront)

## Uso

```bash
cd infra/terraform

# Inicializar backend S3 (una sola vez)
terraform init

# Plan
terraform plan -var="db_password=$(openssl rand -base64 32)" \
  -var="acm_certificate_arn=arn:aws:acm:us-east-1:..." \
  -var="acm_certificate_arn_cloudfront=arn:aws:acm:us-east-1:..."

# Aplicar
terraform apply -var-file="backend.tfvars"

# Destruir (cuidado!)
terraform destroy
```

## Variables importantes

| Variable | Descripción | Default |
|----------|-------------|---------|
| `aws_region` | Región AWS | `us-east-1` |
| `environment` | Ambiente | `production` |
| `cluster_name` | Nombre del cluster EKS | `sellia-cluster` |
| `db_password` | Contraseña RDS | **requerido** |
| `acm_certificate_arn` | Cert ACM para ALB | **requerido** |
| `acm_certificate_arn_cloudfront` | Cert ACM para CloudFront | **requerido** |

## State remoto

El estado se almacena en S3 con bloqueo DynamoDB. Crear primero:

```bash
aws s3 mb s3://sellia-terraform-state
aws dynamodb create-table \
  --table-name sellia-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```
