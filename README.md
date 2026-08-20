# 🥩 Мясной Склад — Система управления заявками

Веб-приложение для автоматизации работы мясного склада: создание заявок клиентами, сборка и выдача менеджером, учёт остатков.

## Стек технологий

- **Backend:** Django 5.1, Celery, Django REST (planned)
- **Database:** PostgreSQL 15
- **Cache/Broker:** Redis 7
- **Frontend:** Bootstrap 5, Django Templates
- **Deploy:** Docker, Docker Compose

## Быстрый старт

```bash
git clone https://github.com/your-repo/dj_meat_warehouse.git
cd dj_meat_warehouse
cp .env.example .env  # Настроить переменные
docker compose up --build