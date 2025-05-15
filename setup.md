# Development Setup Guide

This guide walks you through setting up the Bluelabel AIOS v2 project for local development.

---

## 🔧 Requirements

- Python 3.10+
- Docker + Docker Compose
- Redis (or Docker version)
- PostgreSQL (or Docker)
- Node.js + npm (for React UI)

---

## 🏁 Getting Started

1. **Clone the Repository**

```bash
git clone https://github.com/your-org/bluelabel-aios-v2.git
cd bluelabel-aios-v2
```

2. **Create a Virtual Environment**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Set Up Environment Variables**

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

4. **Start Docker Services**

```bash
docker-compose up -d
```

5. **Apply Database Migrations**

```bash
alembic upgrade head  # Or your preferred migration tool
```

6. **Run the API**

```bash
uvicorn apps.api.main:app --reload
```

7. **Run Tests**

```bash
pytest
```

---

## 🧪 Linting & Formatting

```bash
black .
isort .
flake8
```

---

## 🧠 Notes

- Redis Streams must be available on `localhost:6379`
- PostgreSQL must be seeded before use (`init.sql` script coming soon)
- Ollama models may need to be installed manually
