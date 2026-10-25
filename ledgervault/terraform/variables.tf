variable "jwt_secret" {
  type        = string
  description = "HMAC secret for signing JWTs"
  default     = "devsecret123"
}

variable "bootstrap_token" {
  type        = string
  description = "Provisioning bootstrap token served by the metadata mock"
  default     = "bootstrap-provisioning-7f3a"
}

variable "s3_access_key" {
  type    = string
  default = "minioadmin"
}

variable "s3_secret_key" {
  type    = string
  default = "minioadmin"
}
