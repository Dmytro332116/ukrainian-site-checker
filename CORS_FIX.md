# 🔧 Виправлення CORS проблеми

## ❌ Проблема

Кнопка "Додати і сканувати" не працювала через CORS помилку.

### Помилка в логах:
```
INFO: 192.168.65.1:19805 - "OPTIONS /api/v1/websites/ HTTP/1.1" 405 Method Not Allowed
```

### Причина:
CORS preflight запити (OPTIONS) не були правильно налаштовані в FastAPI backend.

---

## ✅ Рішення

### Що було зроблено:

1. **Виправлено CORS в `backend/app/main.py`:**

```python
# CORS - Allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

2. **Перезапущено сервіси:**
```bash
docker-compose restart backend
docker-compose restart frontend
```

---

## 🧪 Тестування

### Перевірка CORS:
```bash
curl -X OPTIONS -i http://localhost:8000/api/v1/websites/ \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST"
```

**Очікуваний результат:**
```
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:8080
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
access-control-allow-credentials: true
```

### Перевірка в браузері:
1. Відкрити http://localhost:8080
2. Натиснути "Новий сайт"
3. Ввести URL (наприклад: `https://example.com`)
4. Натиснути "Додати і сканувати"

**Очікуваний результат:**
- ✅ Діалог закривається
- ✅ З'являється новий запис у таблиці
- ✅ Статус: `pending` -> `running` -> `completed`

---

## 📝 Технічні деталі

### CORS Preflight

Браузер автоматично відправляє OPTIONS запит перед POST/PUT/DELETE запитами для перевірки дозволів.

**Без CORS:**
```
Browser -> OPTIONS /api/v1/websites/ -> 405 Method Not Allowed ❌
Browser -> POST /api/v1/websites/ -> Blocked by CORS ❌
```

**З правильним CORS:**
```
Browser -> OPTIONS /api/v1/websites/ -> 200 OK ✅
Browser -> POST /api/v1/websites/ -> 201 Created ✅
```

### Важливо:

- `allow_origins=["*"]` **НЕ працює** з `allow_credentials=True`
- Потрібно явно вказати origins: `["http://localhost:8080"]`
- OPTIONS метод має бути в списку `allow_methods`

---

## 🚀 Статус

✅ **Проблему виправлено**  
✅ **Backend працює**  
✅ **Frontend працює**  
✅ **CORS налаштовано правильно**

Дата виправлення: 2025-10-17

