# Лабораторная работа 8 - Межсервисное взаимодействие, асинхронность

## Описание

Реализация асинхронного Go-сервиса для расчета risk_score в системе оценки уязвимостей.

## Архитектура

### Компоненты системы

1. **Основной сервис (Python/FastAPI)** - порт 8000
   - Управление заявками на оценку уязвимостей
   - API для создания и управления отчетами
   - Интеграция с асинхронным сервисом

2. **Асинхронный сервис (Go)** - порт 8082
   - Расчет risk_score с задержкой 5-10 секунд
   - Возврат результатов через HTTP callback
   - Элемент случайности в расчетах

3. **Frontend (React)** - интерфейс модератора
   - Список заявок с фильтрацией
   - Short polling для обновления данных
   - Управление статусами заявок

### Поток работы

1. Пользователь формирует заявку через `PUT /api/reports/{id}/form`
2. Основной сервис вызывает Go-сервис `POST /calculate-risk`
3. Go-сервис выполняет задержку 5-10 секунд
4. Go-сервис рассчитывает risk_score по формуле:
   ```
   risk_score = max(likelihood * impact) + random(0-2)
   где:
   - likelihood: none=3, basic=2, full=1
   - impact: impact_level из vulnerability_assessment
   ```
5. Go-сервис отправляет результат в `PUT /api/reports/{id}/risk-result` с токеном
6. React интерфейс обновляется через short polling (каждые 5 секунд)

## Запуск проекта

### Предварительные требования

- Docker и Docker Compose
- Go 1.21+ (для локальной разработки)
- Python 3.12+ (для локальной разработки)
- Node.js 18+ (для локальной разработки)

### Запуск через Docker Compose

```bash
# Клонировать репозиторий
cd RIP-labs

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps

# Просмотр логов Go-сервиса
docker-compose logs -f async-service
```

### Локальный запуск (для разработки)

#### Асинхронный Go-сервис

```bash
cd async-service
go run main.go
# Запустится на порту 8080 (или из переменной PORT)
```

#### Основной Python сервис

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn main:app --reload --port 8000
```

#### React Frontend

```bash
cd frontend
npm install
npm run dev
```

## Тестирование

### 1. Тестирование через Insomnia

Импортируйте файл `insomnia_lab8.json` в Insomnia.

Последовательность тестирования:

1. **Health Check Go-сервиса**
   ```
   GET http://localhost:8082/health
   ```

2. **Создайте заявку** (если еще нет)
   ```
   POST /api/report/draft/assessments
   ```

3. **Сформируйте заявку**
   ```
   PUT /api/reports/1/form
   ```
   После этого автоматически запустится асинхронный расчет

4. **Проверьте список заявок** (через 5-10 секунд)
   ```
   GET /api/reports
   ```
   В ответе должен появиться `risk_score`

5. **Завершите заявку** (модератором)
   ```
   PUT /api/reports/1/complete
   ```

### 2. Тестирование через React интерфейс

1. Откройте `http://localhost:5173/reports`
2. Наблюдайте за обновлением списка (Short Polling)
3. Используйте фильтры:
   - По статусу (бэкенд)
   - По датам (бэкенд)
   - По создателю (фронтенд)
4. Используйте кнопки управления заявками (если вы модератор)

### 3. Прямое тестирование Go-сервиса

```bash
curl -X POST http://localhost:8082/calculate-risk \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 1,
    "components": [
      {
        "protection_level": "none",
        "impact_level": 3
      }
    ]
  }'
```

## Endpoint API

### Основной сервис (Python)

- `GET /api/reports` - список заявок с фильтрацией
  - Query params: `status`, `date_from`, `date_to`
- `GET /api/reports/{id}` - детали заявки
- `PUT /api/reports/{id}/form` - формирование заявки (запускает async расчет)
- `PUT /api/reports/{id}/risk-result` - обновление risk_score (требует токен `lab8secret`)
- `PUT /api/reports/{id}/complete` - завершение заявки (модератор)
- `PUT /api/reports/{id}/cancel` - отклонение заявки (модератор)

### Асинхронный сервис (Go)

- `GET /health` - проверка работоспособности
- `POST /calculate-risk` - запуск асинхронного расчета risk_score

## Безопасность

Асинхронный сервис использует токен `lab8secret` для авторизации callback запросов к основному сервису. В production следует использовать более сложный токен и HTTPS.

## Особенности реализации

1. **Асинхронность**: Go-сервис использует горутины для параллельной обработки запросов
2. **Short Polling**: React обновляет список заявок каждые 5 секунд
3. **Фильтрация**: Сочетание серверной и клиентской фильтрации
4. **Случайность**: К базовому risk_score добавляется случайное значение 0-2
5. **Graceful degradation**: Если Go-сервис недоступен, формирование заявки все равно проходит

## Диаграммы

### Диаграмма последовательности

```
Пользователь -> Backend: PUT /reports/1/form
Backend -> Go-service: POST /calculate-risk (async)
Backend -> Пользователь: 200 OK (formed)
Go-service: delay 5-10s + calculate
Go-service -> Backend: PUT /reports/1/risk-result
Backend: update risk_score
Frontend (polling): GET /reports
Backend -> Frontend: updated list with risk_score
```

### Статусы заявок

```
DRAFT -> FORMED -> COMPLETED
              |
              └-> CANCELLED
```

## Troubleshooting

### Go-сервис не запускается

```bash
# Проверить логи
docker-compose logs async-service

# Пересобрать контейнер
docker-compose build async-service
docker-compose up -d async-service
```

### Risk_score не обновляется

1. Проверьте что Go-сервис доступен: `curl http://localhost:8082/health`
2. Проверьте логи Go-сервиса на наличие ошибок
3. Проверьте что токен `lab8secret` правильный
4. Проверьте что основной сервис доступен из Docker контейнера

### Short Polling не работает

1. Откройте DevTools в браузере
2. Проверьте вкладку Network - должны быть запросы к `/api/reports` каждые 5 секунд
3. Проверьте консоль на наличие ошибок
