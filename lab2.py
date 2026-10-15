# Анализ продаж за 7 дней

sales = [12000, 15000, 9000, 18000, 20000, 14000, 16000]

# Сумма продаж
total = sum(sales)

# Средние продажи за день
average = total / len(sales)

# Количество дней, когда продажи выше среднего
days_above_average = 0

for sale in sales:
    if sale > average:
        days_above_average += 1

# Вывод результатов
print("Продажи за 7 дней:", sales)
print("Общая сумма продаж:", total, "тг")
print("Средние продажи за день:", round(average, 2), "тг")
print("Количество дней выше среднего:", days_above_average)
