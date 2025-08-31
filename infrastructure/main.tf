terraform {
  required_version = ">= 1.0"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# Configure the DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# Create a VPS droplet
resource "digitalocean_droplet" "data_platform" {
  name     = "foss-data-platform"
  size     = var.droplet_size
  image    = "debian-12-x64"
  region   = var.region
  ssh_keys = [var.ssh_key_id]
  
  tags = ["data-platform", "foss", "production"]
  
  user_data = templatefile("${path.module}/cloud-init.yml", {
    admin_user = var.admin_user
    admin_ssh_key = var.admin_ssh_key
  })
}

# Create a floating IP for the droplet
resource "digitalocean_floating_ip" "data_platform_ip" {
  droplet_id = digitalocean_droplet.data_platform.id
  region     = digitalocean_droplet.data_platform.region
}

# Create firewall rules
resource "digitalocean_firewall" "data_platform_fw" {
  name = "data-platform-firewall"
  
  droplet_ids = [digitalocean_droplet.data_platform.id]
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # JupyterLab
  inbound_rule {
    protocol         = "tcp"
    port_range       = "8888"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Dagster
  inbound_rule {
    protocol         = "tcp"
    port_range       = "3000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Grafana
  inbound_rule {
    protocol         = "tcp"
    port_range       = "3001"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Trino
  inbound_rule {
    protocol         = "tcp"
    port_range       = "8080"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Prometheus
  inbound_rule {
    protocol         = "tcp"
    port_range       = "9090"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Output the public IP
output "public_ip" {
  value = digitalocean_floating_ip.data_platform_ip.ip_address
}

output "droplet_id" {
  value = digitalocean_droplet.data_platform.id
}
