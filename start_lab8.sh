#!/bin/bash

echo "🚀 Запуск лабораторной работы 8..."
echo ""

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    exit 1
fi

echo "✅ Docker и Docker Compose обнаружены"
echo ""

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск контейнеров
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up -d --build

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
echo ""
echo "📊 Статус сервисов:"
docker-compose ps

echo ""
echo "✅ Лабораторная работа 8 запущена!"
echo ""
echo "🌐 Доступные сервисы:"
echo "  - Основной API: http://localhost:8000/api"
echo "  - Async Go-сервис: http://localhost:8082"
echo "  - PostgreSQL: localhost:5434"
echo "  - Redis: localhost:6379"
echo "  - MinIO Console: http://localhost:9003"
echo "  - Adminer (DB): http://localhost:8081"
echo ""
echo "📝 Для тестирования импортируйте insomnia_lab8.json в Insomnia"
echo "📖 Подробная документация: LAB8_README.md"
echo ""
echo "🔍 Просмотр логов Go-сервиса:"
echo "  docker-compose logs -f async-service"
echo ""
echo "🛑 Остановка всех сервисов:"
echo "  docker-compose down"
