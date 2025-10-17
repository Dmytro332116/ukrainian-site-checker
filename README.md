# 🇺🇦 Ukrainian Site Checker

Автоматизована система для перевірки українських веб-сайтів на наявність помилок, включаючи орфографію, формат адрес, битi посилання, телефонні номери та SEO.

## ✨ Основні можливості

- ✅ **Перевірка орфографії українською мовою** - використовує LanguageTool
- ✅ **Валідація адрес** - перевіряє відповідність формату "м. Місто, вул. Назва, 123"
- ✅ **Перевірка посилань** - знаходить биті та недоступні посилання
- ✅ **Перевірка телефонів** - валідація формату та клікабельності
- ✅ **SEO аудит** - favicon, robots.txt, meta-теги
- ✅ **Веб-інтерфейс** - зручний дашборд для управління перевірками
- ✅ **Звіти HTML/PDF** - детальні звіти для команди
- ✅ **Фонові задачі** - асинхронне сканування через Celery

## 🏗️ Архітектура

- **Backend:** Python 3.11 + FastAPI
- **Frontend:** Vue.js 3 + Vuetify
- **Database:** PostgreSQL 15
- **Queue:** Redis + Celery
- **Crawler:** BeautifulSoup4 + httpx
- **Deploy:** Docker + Docker Compose

## 📋 Вимоги

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM (рекомендовано)
- 10GB вільного місця на диску

## 🚀 Швидкий старт

### 1. Клонування репозиторію

```bash
git clone <repository-url>
cd ukrainian-site-checker
```

### 2. Налаштування змінних середовища

Скопіюйте `.env.example` в `.env` (вже створений з налаштуваннями за замовчуванням):

```bash
cp .env.example .env
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

Це запустить всі необхідні сервіси:
- PostgreSQL (порт 5432)
- Redis (порт 6379)
- Backend API (порт 8000)
- Celery Worker
- Frontend (порт 8080)

### 4. Виконання міграцій бази даних

```bash
docker-compose exec backend alembic upgrade head
```

Або створіть початкову міграцію:

```bash
docker-compose exec backend alembic revision --autogenerate -m "Initial migration"
docker-compose exec backend alembic upgrade head
```

### 5. Відкрийте додаток

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 📖 Використання

### Через веб-інтерфейс

1. Відкрийте http://localhost:8080
2. Натисніть "Новий сайт" на дашборді
3. Введіть URL сайту для перевірки
4. Дочекайтесь завершення сканування
5. Перегляньте детальний звіт з помилками

### Через API

```bash
# Створити сайт
curl -X POST http://localhost:8000/api/v1/websites/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "name": "Мій сайт"}'

# Запустити сканування
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Content-Type: application/json" \
  -d '{"website_id": 1}'

# Отримати статус сканування
curl http://localhost:8000/api/v1/scans/1/status

# Завантажити PDF звіт
curl http://localhost:8000/api/v1/reports/1/pdf -o report.pdf
```

## 🎯 Типи перевірок

### 1. Орфографія та граматика
- Перевіряє текст на сторінках українською мовою
- Виявляє орфографічні та граматичні помилки
- Надає контекст та пропозиції для виправлення
- Підтримує whitelist слів (технічні терміни, бренди)

### 2. Формат адрес
Перевіряє відповідність шаблонам:
- `м. [місто], вул. [вулиця], [номер]`
- `м. [місто], пров. [провулок], [номер]`
- `м. [місто], проспект [назва], [номер]`
- `м. [місто], бульвар [назва], [номер]`

### 3. Посилання
- Перевіряє доступність усіх посилань (HTTP статус)
- Виявляє 404, 500 та інші помилки
- Перевіряє як внутрішні, так і зовнішні посилання

### 4. Телефонні номери
- Перевіряє формат українських номерів (+380XXXXXXXXX)
- Валідує клікабельність (наявність `tel:` посилань)
- Знаходить неклікабельні номери в тексті

### 5. SEO
- Наявність favicon
- Перевірка robots.txt
- Meta-теги (title, description)
- Open Graph теги
- Mobile-friendly (viewport)

## ⚙️ Налаштування

### Налаштування сканування для сайту

При створенні/редагуванні сайту можна встановити:

```json
{
  "url": "https://example.com",
  "name": "Мій сайт",
  "preferences": {
    "check_spelling": true,
    "check_addresses": true,
    "check_links": true,
    "check_phones": true,
    "check_seo": true,
    "max_pages": 100,
    "max_depth": 5,
    "exclude_paths": ["/admin", "/api"],
    "whitelist_words": ["WordPress", "JavaScript"]
  }
}
```

### Змінні середовища

Основні налаштування в `.env`:

```env
# Ліміти сканування
MAX_PAGES_PER_SCAN=100  # Максимум сторінок за одне сканування
MAX_DEPTH=5             # Максимальна глибина обходу
REQUEST_TIMEOUT=10      # Таймаут запиту в секундах

# LanguageTool
LANGUAGETOOL_ENABLED=True  # Увімкнути перевірку орфографії
```

## 🔧 Розробка

### Локальна розробка без Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Запуск
uvicorn app.main:app --reload

# Celery worker
celery -A app.core.celery_app worker --loglevel=info
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Структура проекту

```
ukrainian-site-checker/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Конфігурація, БД
│   │   ├── models/           # SQLAlchemy моделі
│   │   ├── schemas/          # Pydantic схеми
│   │   ├── services/         # Бізнес-логіка
│   │   │   ├── crawler.py
│   │   │   ├── spell_checker.py
│   │   │   ├── address_validator.py
│   │   │   ├── link_checker.py
│   │   │   └── seo_checker.py
│   │   ├── tasks/            # Celery задачі
│   │   └── main.py
│   ├── alembic/              # Міграції БД
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── services/
│   │   └── main.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 📊 API Документація

Swagger UI доступний за адресою: http://localhost:8000/docs

### Основні ендпоінти:

**Websites:**
- `GET /api/v1/websites/` - список сайтів
- `POST /api/v1/websites/` - створити сайт
- `GET /api/v1/websites/{id}` - отримати сайт
- `PATCH /api/v1/websites/{id}` - оновити сайт
- `DELETE /api/v1/websites/{id}` - видалити сайт

**Scans:**
- `GET /api/v1/scans/` - список сканувань
- `POST /api/v1/scans/` - запустити сканування
- `GET /api/v1/scans/{id}` - детальна інформація
- `GET /api/v1/scans/{id}/status` - статус сканування

**Reports:**
- `GET /api/v1/reports/{scan_id}/html` - HTML звіт
- `GET /api/v1/reports/{scan_id}/pdf` - PDF звіт

## 🐛 Відладка

### Перегляд логів

```bash
# Всі сервіси
docker-compose logs -f

# Тільки backend
docker-compose logs -f backend

# Тільки celery worker
docker-compose logs -f celery-worker
```

### Підключення до БД

```bash
docker-compose exec db psql -U postgres -d site_checker
```

### Підключення до Redis

```bash
docker-compose exec redis redis-cli
```

## 🧪 Тестування

```bash
# Backend тести
docker-compose exec backend pytest

# З покриттям коду
docker-compose exec backend pytest --cov=app
```

## 📝 Ліцензія

MIT License

## 🤝 Підтримка

Для питань та пропозицій створіть issue в репозиторії.

## 🎉 Готово!

Тепер ваша команда може автоматично перевіряти сайти на помилки. Успіхів! 🚀

