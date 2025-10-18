# VPC for Batch Processing
resource "aws_vpc" "batch_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-batch-vpc"
  }
}

resource "aws_subnet" "batch_subnet" {
  vpc_id                  = aws_vpc.batch_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-batch-subnet"
  }
}

resource "aws_internet_gateway" "batch_igw" {
  vpc_id = aws_vpc.batch_vpc.id

  tags = {
    Name = "${var.project_name}-batch-igw"
  }
}

resource "aws_route_table" "batch_rt" {
  vpc_id = aws_vpc.batch_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.batch_igw.id
  }

  tags = {
    Name = "${var.project_name}-batch-rt"
  }
}

resource "aws_route_table_association" "batch_rta" {
  subnet_id      = aws_subnet.batch_subnet.id
  route_table_id = aws_route_table.batch_rt.id
}

resource "aws_security_group" "batch_sg" {
  name_prefix = "${var.project_name}-batch-sg"
  vpc_id      = aws_vpc.batch_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-batch-sg"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}
