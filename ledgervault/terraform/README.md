# Terraform (local Docker provider)

This is Infrastructure-as-Code that stands up the **same** local lab as
`docker-compose.yml`, using the [`kreuzwerker/docker`](https://registry.terraform.io/providers/kreuzwerker/docker/latest)
provider. No cloud account and no cost — everything runs against the local
Docker daemon. It exists so a static/IaC review (e.g. AWS Continuum code
review over the GitHub repo) has idiomatic IaC to analyse in addition to the
application source.

## Usage

```bash
cd terraform
terraform init
terraform apply      # builds images and starts containers
# ... run your assessment against http://localhost:8080 and :8000 ...
terraform destroy    # tear everything down
```

> The IaC deliberately mirrors the compose file's weak posture (hardcoded
> default secrets, debug mode on, broad env injection). Those are in scope
> for the IaC review — see `../GROUND_TRUTH.md`, the "IaC / configuration"
> findings.
