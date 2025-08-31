variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "ssh_key_id" {
  description = "ID of the SSH key to use for the droplet"
  type        = string
}

variable "droplet_size" {
  description = "Size of the droplet"
  type        = string
  default     = "s-2vcpu-4gb"  # 2 vCPU, 4GB RAM - good starting point
}

variable "region" {
  description = "Region for the droplet"
  type        = string
  default     = "nyc1"  # New York 1
}

variable "admin_user" {
  description = "Admin username for the server"
  type        = string
  default     = "admin"
}

variable "admin_ssh_key" {
  description = "SSH public key for admin user"
  type        = string
}
