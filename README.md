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


[//]: # (---)

[//]: # ()
[//]: # (## 7. README_REGRU.md &#40;для хостинга REG.RU&#41;)

[//]: # ()
[//]: # (```markdown)

[//]: # (# Деплой на REG.RU &#40;VPS/VDS&#41;)

[//]: # ()
[//]: # (## Требования к серверу)

[//]: # ()
[//]: # (- Ubuntu 22.04+)

[//]: # (- RAM: 1 GB минимум)

[//]: # (- Disk: 10 GB+)

[//]: # (- Docker + Docker Compose установлены)

[//]: # ()
[//]: # (## Шаги деплоя)

[//]: # ()
[//]: # (### 1. Подключение к серверу)

[//]: # ()
[//]: # (```bash)

[//]: # (ssh root@YOUR_SERVER_IP)