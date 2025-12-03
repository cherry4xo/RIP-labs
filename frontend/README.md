# Frontend для лабораторных работ №5-6

React SPA приложение для работы с API оценки уязвимостей с поддержкой PWA и Tauri.

## Лабораторная работа 6 - Новые возможности

### ✅ Выполненные задачи

#### 1. Redux Toolkit для управления состоянием
- Установлен @reduxjs/toolkit и react-redux
- Создан store с slice для фильтров
- Фильтры сохраняются при навигации между страницами
- Используйте Redux DevTools для отладки

#### 2. Адаптивный дизайн
Полная адаптивность для всех страниц:
- **Desktop** (>992px): 3 колонки карточек
- **Tablet** (768px-992px): 2 колонки карточек
- **Mobile** (<768px): 1 колонка
- **Small mobile** (<576px): оптимизированные размеры

#### 3. PWA (Progressive Web App)
- Настроен vite-plugin-pwa
- Web App Manifest
- Service Worker с кешированием
- Офлайн режим
- Установка на домашний экран
- **ВАЖНО**: Необходимо добавить файлы `public/logo192.png` и `public/logo512.png` для полноценной работы PWA

#### 4. Tauri Desktop приложение
- Инициализирован Tauri проект
- Окно приложения 1280x800
- Настроена работа с API через IP локальной сети

#### 5. GitHub Pages
- GitHub Actions workflow для автоматического деплоя
- Правильная конфигурация base path
- Поддержка SPA routing

## Технологии

- **React 19** с **TypeScript**
- **Vite 7** - быстрая сборка и dev-сервер
- **React Router v7** - клиентская маршрутизация
- **React Bootstrap** - UI компоненты
- **Redux Toolkit** - управление состоянием
- **Axios** - AJAX запросы с fallback на mock данные
- **PWA** - vite-plugin-pwa (Workbox)
- **Tauri 2** - desktop приложение
- **gh-pages** - развертывание на GitHub Pages

## Установка и запуск

### 1. Установка зависимостей

```bash
npm install
```

### 2. Запуск dev-сервера

```bash
npm run dev
```

Приложение будет доступно по адресу `http://localhost:5173`

### 3. Сборка для продакшена

```bash
npm run build
```

Собранные файлы будут в директории `dist/`

### 4. PWA Preview

```bash
npm run preview
```

### 5. Tauri режим разработки

```bash
npm run tauri:dev
```

### 6. Сборка Tauri приложения

```bash
npm run tauri:build
```

## Настройка API для Tauri

Для работы Tauri с API через IP локальной сети:

1. Узнайте IP вашего компьютера:
   - Windows: `ipconfig`
   - Mac/Linux: `ifconfig`

2. Отредактируйте `.env`:
```env
VITE_API_BASE_URL=http://192.168.1.100:8080/api
```

3. Перезапустите приложение

## Тестирование PWA

### На компьютере:
1. `npm run build && npm run preview`
2. Откройте DevTools (F12)
3. Application → Service Workers
4. Проверьте регистрацию SW
5. Иконка установки PWA в адресной строке

### На мобильном:
1. Откройте GitHub Pages на телефоне
2. "Добавить на главный экран"
3. PWA установится как нативное приложение

## Развертывание на GitHub Pages

### Метод 1: gh-pages (рекомендуется для этой лабы)

1. Убедитесь, что все изменения закоммичены

2. Соберите и разверните приложение:
```bash
npm run build
npm run deploy
```

3. Приложение будет доступно по адресу:
   `https://cherry4xo.github.io/RIP-frontend/`

4. Ссылка появится во вкладке **Deployments** вашего репозитория

**Важно**: При развертывании через GitHub Pages AJAX запросы будут идти по http, в то время как приложение доступно по https. Это будет работать только при использовании localhost в запросах или при настройке HTTPS на бэкенде.

### Метод 2: GitHub Actions (автоматический)

Альтернативно, можно использовать GitHub Actions workflow (`.github/workflows/deploy.yml`):

1. Push в ветку main
```bash
git push
```

2. Включите GitHub Pages в настройках:
   - Settings → Pages → Source: GitHub Actions

3. Приложение будет автоматически деплоиться при каждом push

## Структура проекта

```
src/
├── components/         # Переиспользуемые компоненты
│   └── layout/        # Компоненты layout (Navbar, Breadcrumbs)
├── config/            # Конфигурация (API URL)
├── pages/             # Страницы приложения
│   ├── Home.tsx       # Главная страница
│   ├── ServicesList.tsx    # Список услуг с фильтрами
│   └── ServiceDetail.tsx   # Детальный просмотр услуги
├── services/          # API service layer
│   ├── api.ts         # Функции для работы с API
│   └── mockData.ts    # Mock данные
├── store/             # Redux store
│   ├── store.ts       # Конфигурация store
│   ├── filtersSlice.ts # Slice для фильтров
│   └── hooks.ts       # Типизированные хуки
├── types/             # TypeScript типы
│   └── api.ts         # Типы для API
├── styles/            # Глобальные стили
│   └── global.css
├── App.tsx            # Главный компонент с роутингом
└── main.tsx           # Точка входа
src-tauri/             # Tauri конфигурация
.github/workflows/     # GitHub Actions
```

## Особенности реализации

### Проксирование API

В `vite.config.ts` настроено проксирование для решения проблем с CORS в dev режиме:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
    },
  },
}
```

Все запросы к `/api/*` будут проксироваться на бэкенд `http://localhost:8080`

### AJAX запросы с Axios

API service layer (`src/services/api.ts`) использует axios для AJAX запросов с автоматическим fallback на mock данные при недоступности бэкенда. Axios предоставляет более удобный интерфейс по сравнению с fetch и автоматически обрабатывает JSON.

### Фильтрация

Страница списка услуг (`ServicesList.tsx`) поддерживает фильтрацию:
- По названию (title)
- По типу анализа (assessment_type)

Фильтрация происходит на стороне бэкенда через query параметры.

### Breadcrumbs

Самописный компонент навигационных хлебных крошек (`Breadcrumbs.tsx`) автоматически строит путь навигации на основе текущего URL.

### Хуки и жизненный цикл

Используются стандартные React хуки:
- `useState` - для управления локальным состоянием (данные, фильтры, loading, error)
- `useEffect` - для загрузки данных при монтировании компонента и изменении фильтров
- `useParams` - для получения параметров из URL
- `useLocation` - для работы с текущим location

### Props и передача данных

Компоненты используют props для конфигурации и передачи данных:
- `Layout` принимает `showBreadcrumbs` для управления отображением breadcrumbs
- `Breadcrumbs` принимает опциональный `items` для кастомных breadcrumbs

Все компоненты типизированы с помощью TypeScript интерфейсов.

## API endpoints

Приложение использует следующие endpoints:

- `GET /api/vulnerabilities` - список оценок уязвимостей
  - Query параметры: `title`, `assessment_type`
- `GET /api/vulnerabilities/:id` - детали одной оценки

## Стилизация

Проект использует:
- **Bootstrap** для базовых компонентов
- **Custom CSS** для кастомной стилизации в стиле Positive Technologies
- CSS переменные для цветовой схемы:
  - `--primary-red: #E4002B` - основной красный
  - `--background-dark: #0A0A0A` - темный фон
  - `--text-primary: #FFFFFF` - основной текст
  - `--text-secondary: #a0a0a0` - вторичный текст

## Контрольные вопросы

### React
React - JavaScript библиотека для построения пользовательских интерфейсов. Использует компонентный подход и виртуальный DOM для эффективного обновления UI.

### Props и состояние
- **Props** - данные, передаваемые от родительского компонента к дочернему (read-only)
- **State** - внутреннее состояние компонента, которое может изменяться

### Компонент и элемент
- **Компонент** - функция или класс, возвращающий React элементы
- **Элемент** - объект, описывающий то, что должно появиться на экране

### useState и useEffect
- **useState** - хук для добавления состояния в функциональный компонент
- **useEffect** - хук для выполнения побочных эффектов (запросы, подписки, таймеры)

### Жизненный цикл компонента
1. **Mounting** - компонент добавляется в DOM
2. **Updating** - компонент перерисовывается при изменении props/state
3. **Unmounting** - компонент удаляется из DOM

### CORS и обратный прокси
- **CORS** - механизм безопасности браузера, ограничивающий cross-origin запросы
- **Обратный прокси** - сервер, перенаправляющий запросы к другому серверу (решает проблему CORS в dev режиме)

### Vite и Babel
- **Vite** - современный build tool с быстрым HMR
- **Babel** - транспилятор JavaScript (Vite использует esbuild вместо Babel для большей скорости)

### BFF и GraphQL
- **BFF (Backend For Frontend)** - отдельный backend слой для каждого frontend
- **GraphQL** - язык запросов для API, позволяющий клиенту запрашивать только нужные данные

### Next.js и SSG
- **Next.js** - React framework с SSR/SSG
- **SSG (Static Site Generation)** - генерация статических HTML страниц на этапе сборки

### FSD (Feature-Sliced Design)
Архитектурная методология для фронтенд проектов, основанная на разделении по фичам и слоям.

### Flux и Redux (Лаба 6)
- **Flux**: Архитектурный паттерн (Action → Dispatcher → Store → View)
- **Redux**:
  - Store - единое хранилище состояния
  - Reducer - чистые функции обработки actions
  - Action - объекты с типом и payload
  - Dispatch - отправка action в store

### PWA и Tauri (Лаба 6)
- **PWA**: Web-приложение с нативными возможностями (Service Worker, manifest)
- **Tauri**: Desktop приложение с Rust backend и Web frontend
- **Electron**: Desktop с Node.js и Chromium
- **React Native**: iOS/Android приложения

### GitHub Pages (Лаба 6)
Бесплатный хостинг статических сайтов:
- Автоматический деплой через GitHub Actions
- Custom domains
- HTTPS из коробки
- CDN

## Демонстрация лабораторной работы

### PWA:
1. Открыть GitHub Pages на телефоне
2. Сохранить как PWA
3. Показать работу офлайн

### Redux:
1. Применить фильтр
2. Перейти на главную
3. Вернуться - фильтр сохранился

### Адаптивность:
1. Открыть DevTools
2. Менять ширину экрана
3. Показать breakpoints и количество колонок

### Tauri:
1. Показать подключение к API по IP
2. Отредактировать услугу в БД
3. Показать изменение в Tauri
