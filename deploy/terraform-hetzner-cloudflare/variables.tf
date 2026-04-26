variable "project_name" {
  type        = string
  description = "Short infrastructure prefix."
  default     = "stroystandart"
}

variable "hcloud_token" {
  type        = string
  description = "Hetzner Cloud API token."
  sensitive   = true
}

variable "cloudflare_api_token" {
  type        = string
  description = "Cloudflare API token with DNS edit access."
  sensitive   = true
}

variable "cloudflare_zone_id" {
  type        = string
  description = "Cloudflare zone ID for the domain."
}

variable "domain_name" {
  type        = string
  description = "Base domain name, e.g. example.com."
}

variable "subdomain" {
  type        = string
  description = "Subdomain for the office app."
  default     = "office"
}

variable "server_type" {
  type        = string
  description = "Hetzner server type."
  default     = "cx22"
}

variable "location" {
  type        = string
  description = "Hetzner location."
  default     = "fsn1"
}

variable "image" {
  type        = string
  description = "Hetzner OS image."
  default     = "ubuntu-24.04"
}

variable "ssh_public_key" {
  type        = string
  description = "Public SSH key that will be installed on the VPS."
}

variable "ssh_private_key_path" {
  type        = string
  description = "Local private key path used after provisioning."
  default     = "~/.ssh/stroystandart_cloud"
}

variable "repo_url" {
  type        = string
  description = "Git repository URL to deploy."
  default     = "https://github.com/nikolayabelyan-beep/Stroystandart.git"
}

variable "repo_branch" {
  type        = string
  description = "Git branch to deploy."
  default     = "main"
}

variable "app_dir" {
  type        = string
  description = "Deployment directory on the server."
  default     = "/opt/stroystandart"
}

