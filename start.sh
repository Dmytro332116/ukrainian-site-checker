#!/bin/bash

# Ukrainian Site Checker - Start Script

echo "🇺🇦 Ukrainian Site Checker - Запуск..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не встановлено. Завантажте з https://www.docker.com/get-started"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не встановлено."
    exit 1
fi

echo "✅ Docker встановлено"

# Build and start services
echo ""
echo "📦 Збираємо Docker images..."
docker-compose build

echo ""
echo "🚀 Запускаємо сервіси..."
docker-compose up -d

echo ""
echo "⏳ Чекаємо на запуск БД..."
sleep 5

# Run migrations
echo ""
echo "🔄 Виконуємо міграції БД..."
docker-compose exec -T backend alembic revision --autogenerate -m "Initial migration" 2>/dev/null || true
docker-compose exec -T backend alembic upgrade head

echo ""
echo "✅ Все готово!"
echo ""
echo "🌐 Відкрийте в браузері:"
echo "   Frontend:  http://localhost:8080"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📋 Корисні команди:"
echo "   Переглянути логи:  docker-compose logs -f"
echo "   Зупинити:          docker-compose down"
echo "   Перезапустити:     docker-compose restart"
echo ""

