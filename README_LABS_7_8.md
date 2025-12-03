# Лабораторные работы 7 и 8 - Полная реализация

## Что реализовано

### Лабораторная работа 7 - Redux Toolkit и авторизация

✅ **Redux Toolkit интеграция:**
- `authSlice` - управление авторизацией с localStorage
- `cartSlice` - управление корзиной (черновик заявки)
- `filtersSlice` - управление фильтрами
- Redux-thunk middleware для асинхронных операций
- Типизация RootState и AppDispatch

✅ **Страницы авторизации:**
- `/login` - авторизация пользователя
- `/register` - регистрация нового пользователя
- Валидация форм
- Обработка ошибок

✅ **Личный кабинет:**
- `/profile` - просмотр и редактирование профиля
- Отображение роли (пользователь/модератор)

✅ **Navbar с состоянием:**
- Отображение имени пользователя
- Badge с количеством элементов в корзине
- Выпадающее меню профиля
- Разные ссылки для гостя и авторизованного пользователя
- Сброс фильтров и корзины при выходе

✅ **Корзина и заявки:**
- `/cart` - управление черновиком заявки
- Добавление/удаление услуг
- Изменение уровня защиты и комментариев
- Формирование заявки с информацией о целевой системе
- `/my-reports` - список заявок пользователя
- Кнопка "Добавить в корзину" на странице услуги

### Лабораторная работа 8 - Асинхронность и межсервисное взаимодействие

✅ **Go-сервис (async-service/):**
- HTTP сервер на порту 8082
- Endpoint `/calculate-risk` для расчета risk_score
- Задержка 5-10 секунд
- Случайность в результатах (+0-2 к базовому значению)
- Callback в основной сервис с токеном

✅ **Python backend (FastAPI):**
- Endpoint `PUT /api/reports/{id}/risk-result` с проверкой токена
- Интеграция с httpx для вызова Go-сервиса
- Автоматический вызов при формировании заявки

✅ **React интерфейс модератора:**
- `/reports` - список всех заявок (для модератора)
- Фильтрация по статусу и датам (бэкенд)
- Фильтрация по создателю (фронтенд)
- **Short Polling** - автообновление каждые 5 секунд
- Кнопки управления статусами (Завершить/Отклонить)
- Badge с визуализацией risk_score (низкий/средний/высокий)

## Структура проекта

```
RIP-labs/
├── app/                      # Python FastAPI backend
│   ├── api/                  # API endpoints
│   ├── auth/                 # Аутентификация
│   ├── store/                # Redux slices
│   └── use_cases/            # Бизнес-логика
├── async-service/            # Go асинхронный сервис
│   ├── main.go               # Основной код
│   ├── Dockerfile            # Docker образ
│   └── go.mod                # Go модули
├── frontend/                 # React приложение
│   └── src/
│       ├── components/       # React компоненты
│       ├── pages/            # Страницы
│       │   ├── Login.tsx
│       │   ├── Register.tsx
│       │   ├── Profile.tsx
│       │   ├── Cart.tsx
│       │   ├── MyReports.tsx
│       │   └── ReportsList.tsx
│       ├── store/            # Redux
│       │   ├── authSlice.ts
│       │   ├── cartSlice.ts
│       │   └── store.ts
│       ├── services/         # API calls
│       └── types/            # TypeScript типы
├── docker-compose.yml        # Все сервисы
├── insomnia_lab8.json        # Запросы для тестирования
└── LAB8_README.md            # Детальная документация Lab 8
```

## Быстрый старт

### 1. Установка зависимостей

#### Backend (Python):
```bash
pip install -r requirements.txt
```

#### Frontend (React):
```bash
cd frontend
npm install
```

#### Go-сервис:
```bash
cd async-service
go mod download
```

### 2. Настройка переменных окружения

Файл `.env` уже настроен:
```env
POSTGRES_USER=rip_user
POSTGRES_PASSWORD=rip_password
POSTGRES_DB=rip_db
DATABASE_URL=postgresql+asyncpg://rip_user:rip_password@localhost:5434/rip_db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ASYNC_SERVICE_URL=http://localhost:8082
```

### 3. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d --build

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f async-service
```

### 4. Локальный запуск для разработки

#### Терминал 1 - PostgreSQL и Redis:
```bash
docker-compose up postgres redis
```

#### Терминал 2 - Go-сервис:
```bash
cd async-service
PORT=8082 MAIN_SERVICE_URL=http://localhost:8000 go run main.go
```

#### Терминал 3 - Python Backend:
```bash
# Миграции (если нужно)
alembic upgrade head

# Запуск сервера
uvicorn main:app --reload --port 8000
```

#### Терминал 4 - React Frontend:
```bash
cd frontend
npm run dev
```

## Тестирование

### Полный сценарий тестирования:

#### 1. Регистрация и вход
1. Откройте `http://localhost:5173`
2. Нажмите "Регистрация"
3. Создайте пользователя (логин: `testuser`, пароль: `test1234`)
4. Войдите с этими данными

#### 2. Добавление в корзину
1. Перейдите в "Услуги"
2. Выберите любую услугу
3. Нажмите "Добавить в корзину"
4. Увидите Badge с количеством в Navbar

#### 3. Формирование заявки
1. Перейдите в "Корзину"
2. Измените уровень защиты для услуг
3. Нажмите "Сформировать заявку"
4. Введите информацию о целевой системе
5. Нажмите "Сформировать"

#### 4. Асинхронный расчет
1. Сразу после формирования заявка будет в статусе "Сформирована"
2. `risk_score` будет "Не рассчитан"
3. Через 5-10 секунд Go-сервис рассчитает и обновит `risk_score`
4. Обновите страницу "Мои заявки" или подождите auto-refresh

#### 5. Модерация (если вы модератор)
1. Перейдите в "Все заявки (Модератор)"
2. Увидите Short Polling в действии (обновление каждые 5 секунд)
3. Используйте фильтры по статусу и датам
4. Нажмите "Завершить" или "Отклонить" для заявки

### Тестирование через Insomnia/Postman:

1. Импортируйте `insomnia_lab8.json`
2. Получите токен через `POST /auth/token`
3. Сохраните токен в переменные окружения
4. Выполните последовательность:
   - `POST /report/draft/assessments` - добавить услуги
   - `PUT /reports/{id}/form` - сформировать заявку
   - `GET /reports` - проверить через 5-10 секунд появление risk_score
   - `PUT /reports/{id}/complete` - завершить (модератор)

### Прямое тестирование Go-сервиса:

```bash
# Health check
curl http://localhost:8082/health

# Запуск расчета
curl -X POST http://localhost:8082/calculate-risk \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 1,
    "components": [
      {"protection_level": "none", "impact_level": 3},
      {"protection_level": "basic", "impact_level": 2}
    ]
  }'
```

## Демонстрация Redux

### Просмотр Redux состояния в DevTools:

1. Установите [Redux DevTools Extension](https://github.com/reduxjs/redux-devtools)
2. Откройте приложение в браузере
3. Откройте Redux DevTools (F12 → Redux tab)
4. Наблюдайте за изменениями state при:
   - Авторизации (auth.user, auth.token)
   - Добавлении в корзину (cart.basketInfo)
   - Применении фильтров (filters.searchQuery)

### Проверка localStorage:

1. Откройте DevTools (F12)
2. Перейдите в Application → Local Storage
3. Увидите `token` после авторизации
4. Скопируйте токен и используйте в Insomnia для API запросов

## Архитектура Redux

### Store структура:
```typescript
{
  auth: {
    user: User | null,
    token: string | null,
    isAuthenticated: boolean,
    loading: boolean,
    error: string | null
  },
  cart: {
    cart: AssessmentReportDetails | null,
    basketInfo: AssessmentBasketInfo | null,
    loading: boolean,
    error: string | null
  },
  filters: {
    searchQuery: string
  }
}
```

### Redux Thunks (асинхронные action creators):
- `login` - авторизация пользователя
- `register` - регистрация
- `loadUser` - загрузка данных пользователя
- `updateProfile` - обновление профиля
- `fetchBasketInfo` - информация о корзине
- `addToCart` - добавление в корзину
- `removeFromCart` - удаление из корзины
- `updateCartItem` - обновление элемента
- `submitCart` - формирование заявки

## Особенности реализации

### Безопасность:
- JWT токены хранятся в localStorage
- API токен `lab8secret` для межсервисного взаимодействия
- Проверка прав модератора на бэкенде
- Защита роутов (редирект на /login)

### UX:
- Loading состояния с spinner
- Уведомления об успехе/ошибке
- Автоматическое обновление badge корзины
- Визуальная индикация risk_score (цветные badge)
- Short Polling без перегрузки страницы

### Производительность:
- Go-сервис использует горутины для параллельной обработки
- React memo и useCallback где необходимо
- Debounce для фильтров (можно добавить)
- Оптимизированные запросы к API

## Troubleshooting

### Frontend не подключается к backend:

Проверьте `frontend/src/config/api.config.ts`:
```typescript
export const API_BASE_URL = 'http://localhost:8000/api';
```

### Токен не сохраняется:

1. Проверьте localStorage в DevTools
2. Проверьте что запрос `/auth/token` возвращает `access_token`
3. Проверьте что `authSlice` правильно сохраняет токен

### Go-сервис не отправляет результаты:

1. Проверьте логи: `docker-compose logs async-service`
2. Проверьте что `MAIN_SERVICE_URL` правильный
3. Проверьте что токен `lab8secret` совпадает в обоих сервисах

### Short Polling не работает:

1. Откройте Network tab в DevTools
2. Должны видеть запросы к `/api/reports` каждые 5 секунд
3. Проверьте консоль на ошибки

## Следующие шаги (опционально)

- [ ] WebSocket для real-time обновлений вместо Short Polling
- [ ] Кэширование на уровне Redux (RTK Query)
- [ ] Pagination для списка заявок
- [ ] Экспорт отчетов в PDF
- [ ] Графики и статистика по заявкам
- [ ] Unit тесты для Redux slices
- [ ] E2E тесты с Cypress/Playwright

## Контакты и помощь

Если что-то не работает:
1. Проверьте логи: `docker-compose logs`
2. Проверьте что все порты свободны (8000, 8082, 5173, 5434)
3. Проверьте что в `.env` правильные данные
4. Пересоберите контейнеры: `docker-compose up --build -d`

Успешного тестирования! 🚀
