# ════════════════════════════════════════════════════════════════════════════════
# EC2 Instance + Security Group + AMI
# ════════════════════════════════════════════════════════════════════════════════
# A EC2 é usada como máquina de uso geral (comandos /vm no bot Telegram).
# t3.nano, 20 GB gp3, Ubuntu, IP público (fixo via Elastic IP após criação).
#
# ⚠️ O Security Group ATUAL tem regra de inbound ALL TRAFFIC (0.0.0.0/0)
#    que foi mantida por compatibilidade. Ideal restringir a IPs conhecidos.
# ════════════════════════════════════════════════════════════════════════════════

# ── Security Group ─────────────────────────────────────────────────────────────

resource "aws_security_group" "ec2" {
  name        = "dieta-ec2-sg"
  description = "Security group da EC2 do diet-lambda (bot /vm)"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "WireGuard VPN"
    from_port   = 51820
    to_port     = 51820
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App custom port"
    from_port   = 5678
    to_port     = 5678
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── EC2 Instance ───────────────────────────────────────────────────────────────

resource "aws_instance" "vm" {
  # AMI da EC2 atual (backup 2026-08-11). Se precisar recriar, a AMI tem o disco
  # completo. Para criar nova AMI: aws ec2 create-image --instance-id <id> --name "..."
  ami           = "ami-02fdd9833f229beab"
  instance_type = "t3.nano"

  availability_zone = "us-east-1f"
  key_name          = "cont"

  vpc_security_group_ids = [aws_security_group.ec2.id]

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    iops        = 3000
    encrypted   = false

    # Mantém o disco ao destruir a instância (preserva dados)
    delete_on_termination = false
  }

  # Impede que 'terraform destroy' mate a instância acidentalmente
  lifecycle {
    prevent_destroy = true
  }
}

# ── Elastic IP (IP fixo — opcional, descomente se quiser) ──────────────────────
# resource "aws_eip" "vm" {
#   instance = aws_instance.vm.id
# }
