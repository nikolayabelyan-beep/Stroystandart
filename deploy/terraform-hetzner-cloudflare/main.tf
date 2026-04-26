locals {
  fqdn = "${var.subdomain}.${var.domain_name}"
}

resource "hcloud_ssh_key" "default" {
  name       = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

resource "hcloud_firewall" "default" {
  name = "${var.project_name}-fw"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

resource "hcloud_server" "app" {
  name        = "${var.project_name}-app"
  server_type = var.server_type
  image       = var.image
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  firewall_ids = [hcloud_firewall.default.id]

  user_data = templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
    app_dir    = var.app_dir
    repo_url   = var.repo_url
    repo_branch = var.repo_branch
  })
}

resource "cloudflare_dns_record" "office" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  type    = "A"
  content = hcloud_server.app.ipv4_address
  ttl     = 1
  proxied = false
}

output "server_ip" {
  value = hcloud_server.app.ipv4_address
}

output "office_domain" {
  value = local.fqdn
}

output "ssh_command" {
  value = "ssh root@${hcloud_server.app.ipv4_address}"
}

output "app_url" {
  value = "https://${local.fqdn}"
}

