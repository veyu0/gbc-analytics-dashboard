import requests
import os
from supabase import create_client, Client

RETAIL_CRM_API_KEY = os.environ.get("RETAILCRM_API_KEY")
RETAIL_CRM_URL = "https://duartefaith408.retailcrm.ru"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_all_orders():
    """Получает все заказы из RetailCRM с учетом пагинации"""
    all_orders = []
    page = 1

    while True:
        url = f"{RETAIL_CRM_URL}/api/v5/orders"
        headers = {
            "X-API-KEY": RETAIL_CRM_API_KEY,
            "Content-Type": "application/json"
        }
        params = {"page": page}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Ошибка при получении данных: {response.status_code} - {response.text}")
            break

        data = response.json()
        orders = data.get("orders", [])
        all_orders.extend(orders)

        pagination = data.get("pagination", {})
        total_pages = pagination.get("totalPageCount", 1)

        print(f"Загружено страница {page} из {total_pages}")

        if page >= total_pages:
            break
        page += 1

    return all_orders
        
def insert_orders_to_supabase(orders):
    for order in orders:
        # Подготовка данных для вставки
        order_data = {
            "order_id": order.get("id"),
            "customer_id": order.get("customer", {}).get("id"),
            "status": order.get("status"),
            "total_sum": order.get("summ"),
            "created_at": order.get("createdAt"),
            "first_name": order.get("firstName"),
            "last_name": order.get("lastName"),
            "phone": order.get("phone"),
            "email": order.get("email"),
            "city": order.get("delivery", {}).get("address", {}).get("city"),
            "address": order.get("delivery", {}).get("address", {}).get("text")
        }

        # Вставка данных в таблицу 'orders'
        try:
            response = supabase.table("orders").insert(order_data).execute()
            if response:
                print(f"Заказ {order.get('id')} успешно вставлен.")
            else:
                print(f"Ошибка при вставке заказа {order.get('id')}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Исключение при вставке заказа {order.get('id')}: {e}")
            
def main():
    orders = fetch_all_orders()
    insert_orders_to_supabase(orders=orders)
    
    
if __name__ == "__main__":
    main()