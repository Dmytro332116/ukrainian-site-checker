#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "🧪 ТЕСТУВАННЯ API"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 1: Health check
echo "1️⃣ Перевірка Backend Health..."
HEALTH=$(curl -s http://localhost:8000/health)
if [[ $HEALTH == *"healthy"* ]]; then
    echo "   ✅ Backend працює"
else
    echo "   ❌ Backend не працює"
    exit 1
fi
echo ""

# Test 2: CORS preflight
echo "2️⃣ Перевірка CORS (OPTIONS)..."
CORS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
    http://localhost:8000/api/v1/websites/ \
    -H "Origin: http://localhost:8080" \
    -H "Access-Control-Request-Method: POST")

if [[ $CORS == "200" ]]; then
    echo "   ✅ CORS працює правильно (200 OK)"
else
    echo "   ❌ CORS помилка (код: $CORS)"
    exit 1
fi
echo ""

# Test 3: Create website
echo "3️⃣ Створення тестового сайту..."
CREATE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/websites/ \
    -H "Content-Type: application/json" \
    -d '{
        "url": "https://example.com",
        "name": "Тестовий сайт"
    }')

WEBSITE_ID=$(echo $CREATE_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

if [[ -n $WEBSITE_ID ]]; then
    echo "   ✅ Сайт створено (ID: $WEBSITE_ID)"
else
    echo "   ❌ Помилка створення сайту"
    echo "   Відповідь: $CREATE_RESPONSE"
    exit 1
fi
echo ""

# Test 4: Start scan
echo "4️⃣ Запуск сканування..."
SCAN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/scans/ \
    -H "Content-Type: application/json" \
    -d "{\"website_id\": $WEBSITE_ID}")

SCAN_ID=$(echo $SCAN_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

if [[ -n $SCAN_ID ]]; then
    echo "   ✅ Сканування запущено (ID: $SCAN_ID)"
else
    echo "   ❌ Помилка запуску сканування"
    echo "   Відповідь: $SCAN_RESPONSE"
    exit 1
fi
echo ""

# Test 5: Check scan status
echo "5️⃣ Перевірка статусу сканування..."
sleep 2
STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/scans/$SCAN_ID/status)
STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

echo "   📊 Статус: $STATUS"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "✅ ВСІ ТЕСТИ ПРОЙДЕНО УСПІШНО!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Відкрийте в браузері: http://localhost:8080"
echo "📊 Перегляд сканування: http://localhost:8080/scan/$SCAN_ID"
echo ""
echo "Створений сайт ID: $WEBSITE_ID"
echo "Створене сканування ID: $SCAN_ID"
echo ""

