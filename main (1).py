import tkinter as tk
from tkinter import messagebox, ttk

root = tk.Tk()
root.title("Заявка на печать")
root.geometry("640x440")

# Переменные состояния интерфейса
file_var = tk.StringVar()
format_var = tk.StringVar(value="A4")
copies_var = tk.StringVar(value="1")
status_var = tk.StringVar(value="Готово")
count_var = tk.StringVar(value="Заявок: 0")

# Модель данных предметной области: список кортежей (файл, формат, копии)
print_requests = []
status_timer_id = None

# Основной контейнер (используем только grid внутри frame)
frame = ttk.Frame(root, padding=16)
frame.pack(fill="both", expand=True)
frame.columnconfigure(1, weight=1)
frame.rowconfigure(4, weight=1)

# Поле ввода названия файла
ttk.Label(frame, text="Файл").grid(row=0, column=0, sticky="w", pady=5)
file_entry = ttk.Entry(frame, textvariable=file_var)
file_entry.grid(
    row=0, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=5
)

# Выбор формата
ttk.Label(frame, text="Формат").grid(row=1, column=0, sticky="w", pady=5)
format_box = ttk.Combobox(
    frame,
    textvariable=format_var,
    state="readonly",
    values=["A4", "A3", "A5", "PDF / A4"],
)
format_box.grid(
    row=1, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=5
)

# Дополнительная функция варианта 9: количество копий через Spinbox
ttk.Label(frame, text="Количество копий").grid(
    row=2, column=0, sticky="w", pady=5
)
copies_spinbox = ttk.Spinbox(
    frame,
    from_=1,
    to=50,
    textvariable=copies_var,
    width=10,
)
copies_spinbox.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=5)

# Кнопки управления
add_button = ttk.Button(frame, text="Добавить заявку")
add_button.grid(row=3, column=1, sticky="ew", padx=(8, 4), pady=8)

clear_button = ttk.Button(frame, text="Очистить список")
clear_button.grid(row=3, column=2, sticky="ew", padx=(4, 0), pady=8)

# Список заявок
result_list = tk.Listbox(frame, height=10)
result_list.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=8)

# Счетчик и строка состояния
ttk.Label(frame, textvariable=count_var).grid(row=5, column=0, sticky="w")
ttk.Label(frame, textvariable=status_var).grid(
    row=5, column=1, columnspan=2, sticky="e"
)


def reset_status():
  """Возвращает строку состояния в значение 'Готово' по таймеру."""
  global status_timer_id
  status_timer_id = None
  status_var.set("Готово")


def set_status(text, delay_ms=2500):
  """Обновляет строку состояния и планирует возврат к 'Готово' через root.after."""
  global status_timer_id
  status_var.set(text)
  if status_timer_id is not None:
    root.after_cancel(status_timer_id)
  status_timer_id = root.after(delay_ms, reset_status)


def parse_copies():
  """Проверяет корректность количества копий из Spinbox."""
  raw_copies = copies_var.get().strip()
  if not raw_copies.isdigit():
    return None
  copies = int(raw_copies)
  if copies < 1 or copies > 50:
    return None
  return copies


def add_request():
  """Основной обработчик добавления заявки на печать."""
  filename = file_var.get().strip()
  fmt = format_var.get()
  copies = parse_copies()

  if not filename:
    messagebox.showwarning("Проверка", "Введите название файла")
    file_entry.focus_set()
    return

  if copies is None:
    messagebox.showwarning(
        "Проверка", "Укажите количество копий числом от 1 до 50"
    )
    copies_var.set("1")
    copies_spinbox.focus_set()
    return

  item = (filename, fmt, copies)
  if item in print_requests:
    set_status("Такая заявка уже добавлена")
    return

  print_requests.append(item)
  result_list.insert(tk.END, f"{filename} | {fmt} | копий: {copies}")
  count_var.set(f"Заявок: {len(print_requests)}")
  set_status("Заявка добавлена")

  file_var.set("")
  copies_var.set("1")
  file_entry.focus_set()


def add_request_from_event(event):
  """Адаптер для вызова добавления заявки по нажатию Enter."""
  add_request()
  return "break"


def clear_all():
  """Очищает список заявок после подтверждения пользователя."""
  if not print_requests:
    set_status("Список уже пуст")
    return

  if not messagebox.askyesno("Подтверждение", "Удалить все заявки на печать?"):
    return

  print_requests.clear()
  result_list.delete(0, tk.END)
  count_var.set("Заявок: 0")
  set_status("Список очищен")


# Регистрация обработчиков событий (без круглых скобок)
add_button.config(command=add_request)
clear_button.config(command=clear_all)
root.bind("<Return>", add_request_from_event)

file_entry.focus_set()
root.mainloop()