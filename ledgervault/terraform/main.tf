terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "ledgervault" {
  name = "ledgervault-net"
}

# --- Data stores -----------------------------------------------------------

resource "docker_image" "postgres" {
  name = "postgres:16-alpine"
}

resource "docker_container" "db" {
  name  = "ledgervault-db"
  image = docker_image.postgres.image_id
  env = [
    "POSTGRES_USER=ledger",
    "POSTGRES_PASSWORD=ledger",
    "POSTGRES_DB=ledgervault",
  ]
  networks_advanced {
    name = docker_network.ledgervault.name
    aliases = ["db"]
  }
  ports {
    internal = 5432
    external = 5432
    ip       = "127.0.0.1"
  }
}

resource "docker_image" "redis" {
  name = "redis:7-alpine"
}

resource "docker_container" "redis" {
  name  = "ledgervault-redis"
  image = docker_image.redis.image_id
  networks_advanced {
    name    = docker_network.ledgervault.name
    aliases = ["redis"]
  }
}

resource "docker_image" "minio" {
  name = "minio/minio:latest"
}

resource "docker_container" "minio" {
  name    = "ledgervault-minio"
  image   = docker_image.minio.image_id
  command = ["server", "/data", "--console-address", ":9001"]
  env = [
    "MINIO_ROOT_USER=${var.s3_access_key}",
    "MINIO_ROOT_PASSWORD=${var.s3_secret_key}",
  ]
  networks_advanced {
    name    = docker_network.ledgervault.name
    aliases = ["minio"]
  }
  ports {
    internal = 9000
    external = 9000
    ip       = "127.0.0.1"
  }
}

# --- SSRF target (internal only) ------------------------------------------

resource "docker_image" "metadata_mock" {
  name = "ledgervault/metadata-mock:local"
  build {
    context = "${path.module}/../metadata-mock"
  }
}

resource "docker_container" "metadata_mock" {
  name  = "ledgervault-metadata-mock"
  image = docker_image.metadata_mock.image_id
  env   = ["BOOTSTRAP_TOKEN=${var.bootstrap_token}"]
  networks_advanced {
    name    = docker_network.ledgervault.name
    aliases = ["metadata-mock"]
  }
  # No host port mapping: only reachable from within the network.
}

# --- Application -----------------------------------------------------------

resource "docker_image" "backend" {
  name = "ledgervault/backend:local"
  build {
    context = "${path.module}/../backend"
  }
}

resource "docker_container" "backend" {
  name  = "ledgervault-backend"
  image = docker_image.backend.image_id
  env = [
    "DATABASE_URL=postgresql+psycopg2://ledger:ledger@db:5432/ledgervault",
    "REDIS_URL=redis://redis:6379/0",
    "S3_ENDPOINT=http://minio:9000",
    "S3_BUCKET=ledgervault",
    "S3_ACCESS_KEY=${var.s3_access_key}",
    "S3_SECRET_KEY=${var.s3_secret_key}",
    "JWT_SECRET=${var.jwt_secret}",
    "BOOTSTRAP_TOKEN=${var.bootstrap_token}",
    "DEBUG=true",
    "SEED_ON_START=true",
  ]
  networks_advanced {
    name    = docker_network.ledgervault.name
    aliases = ["backend"]
  }
  ports {
    internal = 8000
    external = 8000
    ip       = "127.0.0.1"
  }
  depends_on = [
    docker_container.db,
    docker_container.redis,
    docker_container.minio,
    docker_container.metadata_mock,
  ]
}

resource "docker_image" "frontend" {
  name = "ledgervault/frontend:local"
  build {
    context = "${path.module}/../frontend"
  }
}

resource "docker_container" "frontend" {
  name  = "ledgervault-frontend"
  image = docker_image.frontend.image_id
  networks_advanced {
    name    = docker_network.ledgervault.name
    aliases = ["frontend"]
  }
  ports {
    internal = 80
    external = 8080
    ip       = "127.0.0.1"
  }
  depends_on = [docker_container.backend]
}
