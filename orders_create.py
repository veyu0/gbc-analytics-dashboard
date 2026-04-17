import time
import requests
import json
import os

API_KEY=os.environ.get("RETAILCRM_API_KEY")

if not API_KEY:
    raise ValueError("Переменная окружения RETAILCRM_API_KEY не задана!")

# URL для создания заказа
url = "https://duartefaith408.retailcrm.ru/api/v5/orders/create"

# Заголовки запроса
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-API-KEY": API_KEY
}

# Читаем содержимое файла mock_orders.json
with open("mock_orders.json", "r", encoding="UTF-8") as file:
    order_data = json.load(file)

for order in order_data:
    data = {
        'site': 'simple-site',
        'order': json.dumps(order)
    }
    response = requests.post(url, headers=headers, data=data)
    print("Статус ответа:", response.status_code)
    try:
        result = response.json()
        print("Ответ API:", result)
        time.sleep(3)
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON:", response.text)
