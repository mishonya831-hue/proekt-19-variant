# Заказы печати: стоимость, фильтрация и рекурсивный подсчёт страниц

# Список заказов
orders = [
    {"id": 1, "name": "Доклад", "pages": 15, "copies": 2, "price": 20, "status": "новый"},
    {"id": 2, "name": "Реферат", "pages": 25, "copies": 1, "price": 20, "status": "выполнен"},
    {"id": 3, "name": "Курсовая", "pages": 40, "copies": 3, "price": 20, "status": "новый"},
    {"id": 4, "name": "Презентация", "pages": 10, "copies": 5, "price": 20, "status": "выполнен"}
]


# Расчёт стоимости заказа
def calculate_cost(order):
    return order["pages"] * order["copies"] * order["price"]


# Фильтрация заказов по статусу
def filter_orders(orders, status):
    return [order for order in orders if order["status"] == status]


# Рекурсивный подсчёт общего количества страниц
def count_pages(orders, index=0):
    if index >= len(orders):
        return 0

    current_pages = orders[index]["pages"] * orders[index]["copies"]
    return current_pages + count_pages(orders, index + 1)


# Вывод всех заказов и их стоимости
print("=== Все заказы ===")

for order in orders:
    cost = calculate_cost(order)
    print(
        f"Заказ №{order['id']}: {order['name']}, "
        f"стоимость: {cost} тг, статус: {order['status']}"
    )


# Фильтрация новых заказов
print("\n=== Новые заказы ===")

new_orders = filter_orders(orders, "новый")

for order in new_orders:
    print(f"Заказ №{order['id']}: {order['name']}")


# Рекурсивный подсчёт страниц
total_pages = count_pages(orders)

print("\nОбщее количество напечатанных страниц:", total_pages)


# Общая стоимость всех заказов
total_cost = sum(calculate_cost(order) for order in orders)

print("Общая стоимость всех заказов:", total_cost, "тг")
