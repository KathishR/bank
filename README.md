# 🏦 Bank Transaction System

> **A Production-Ready Banking System** with secure money transfers, real-time validation, and comprehensive monitoring

![Banking System Demo](docs/demo.gif)

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green?logo=django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue?logo=postgresql)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5.3+-orange?logo=celery)](https://docs.celeryproject.org/)
[![Redis](https://img.shields.io/badge/Redis-6.0+-red?logo=redis)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table of Contents
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Detailed Setup](#-detailed-setup)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Production Deployment](#-production-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## ⭐ Features
- **Secure Money Transfers**: Real-time account-to-account transfers
- **Transaction Validation**: Automatic balance & limit verification
- **Daily Limits**: Configurable transfer limits with monitoring
- **Scheduled Transfers**: Future-dated transactions using Celery
- **Audit Logging**: Comprehensive transaction history
- **High Security**: Authentication, encryption, and validation
- **API First**: Complete REST API with documentation
- **Production Ready**: Includes monitoring, logging, and deployment configs

## 🏗 System Architecture
![Architecture Diagram](docs/architecture.png)

```mermaid
flowchart TD
    A[Client] -->|API Request| B[Load Balancer]
    B --> C[Django API Server]
    C --> D[PostgreSQL]
    C --> E[Redis Cache]
    C --> F[Celery Workers]
    F --> D
    F --> E
```

## 🚀 Quick Start

1. **Clone & Setup**
```bash
# Clone repository
git clone https://github.com/yourusername/bank-system.git
cd bank-system

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Database Setup**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
createdb bank_system

# Run migrations
python manage.py migrate
```

5. **Start Services**
```bash
# Start Redis
sudo systemctl start redis

# Start Celery Worker
celery -A bank worker --beat --scheduler django -l info

# Run Development Server
python manage.py runserver
```

## 📦 Detailed Setup

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+
- Node.js 14+ (for frontend)

### Installation Steps

1. **System Dependencies (Ubuntu/Debian)**
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib redis-server
```

2. **PostgreSQL Setup**
```bash
# Create database user
sudo -u postgres createuser --interactive

# Create database
sudo -u postgres createdb bank_system
```

3. **Environment Configuration**
```bash
# Required environment variables
export DJANGO_SETTINGS_MODULE=bank.settings.production
export DATABASE_URL=postgres://user:password@localhost:5432/bank_system
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key
```

## 📚 API Documentation

### Base URL
`https://api.yourbank.com/v1/`

### Authentication
```bash
# Get access token
curl -X POST /api/token/ \
    -H "Content-Type: application/json" \
    -d '{"username": "user", "password": "pass"}'
```

### Example Endpoints

1. **Create Transfer**
```bash
curl -X POST /api/v1/transfers/ \
    -H "Authorization: Bearer {token}" \
    -H "Content-Type: application/json" \
    -d '{
        "from_account": "ACC123",
        "to_account": "ACC456",
        "amount": 1000.00
    }'
```

## 🛠 Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bank
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8

# Type checking
mypy .
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t bank-system .

# Run container
docker-compose up -d
```

### Manual Deployment
See [deployment guide](docs/deployment.md) for detailed instructions.

## 🤝 Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/xyz`)
3. Commit changes (`git commit -am 'Add xyz'`)
4. Push branch (`git push origin feature/xyz`)
5. Create Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Django Community
- PostgreSQL Team
- All contributors