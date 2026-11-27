"""
Лабораторная работа №13
Дисциплина: «Парадигмы программирования»
Вариант 17: «Электронные заявки»

Запуск:
    python lab13_variant17.py

Внешние библиотеки не требуются. Python 3.11+
"""
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from random import Random
from statistics import median
from threading import Lock
from time import perf_counter, sleep
from typing import Iterable

WORKERS_TO_TEST = (1, 2, 4)
SEED = 17


@dataclass(frozen=True)
class Request:
    """Одна электронная заявка."""
    request_id: int
    category: str
    start_time: float
    end_time: float


def duration_of(request: Request) -> float:
    """Возвращает длительность заявки; некорректный интервал отклоняется."""
    if request.start_time < 0 or request.end_time < 0:
        raise ValueError("Время не может быть отрицательным")
    if request.end_time < request.start_time:
        raise ValueError("Время окончания раньше времени начала")
    return request.end_time - request.start_time


def generate_requests(size: int, seed: int = SEED) -> list[Request]:
    """Создаёт воспроизводимый набор заявок, включая небольшую долю ошибок."""
    rng = Random(seed + size)
    categories = ("Техническая", "Учебная", "Финансовая", "Административная")
    requests = []
    for request_id in range(size):
        start = rng.uniform(0, 10000)
        duration = rng.uniform(0.1, 120)
        # Примерно 2% записей имеют ошибочный интервал.
        if request_id % 50 == 0:
            end = start - rng.uniform(0.1, 5)
        else:
            end = start + duration
        requests.append(Request(
            request_id=request_id,
            category=rng.choice(categories),
            start_time=round(start, 3),
            end_time=round(end, 3),
        ))
    return requests


def analyze_block(block: list[Request]) -> tuple[int, int, list[float], dict[str, int]]:
    """
    Обрабатывает блок заявок.
    Возвращает: количество корректных, количество ошибочных,
    список длительностей и число заявок по категориям.
    """
    valid_count = 0
    invalid_count = 0
    durations = []
    categories: dict[str, int] = {}
    for request in block:
        try:
            duration = duration_of(request)
        except ValueError:
            invalid_count += 1
            continue
        valid_count += 1
        durations.append(duration)
        categories[request.category] = categories.get(request.category, 0) + 1
    return valid_count, invalid_count, durations, categories


def analyze_block_with_wait(block: list[Request]):
    """Поточная версия с имитацией ожидания ввода-вывода."""
    sleep(0.002)
    return analyze_block(block)


def percentile_95(values: list[float]) -> float:
    """Вычисляет 95-й процентиль методом ближайшего ранга."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, int(0.95 * len(ordered) + 0.999999) - 1)
    return ordered[index]


def combine_results(parts: Iterable[tuple]) -> dict:
    """Объединяет частичные результаты в главном потоке."""
    valid_count = 0
    invalid_count = 0
    durations: list[float] = []
    categories: dict[str, int] = {}
    for part_valid, part_invalid, part_durations, part_categories in parts:
        valid_count += part_valid
        invalid_count += part_invalid
        durations.extend(part_durations)
        for category, count in part_categories.items():
            categories[category] = categories.get(category, 0) + count

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "median_duration": median(durations) if durations else 0.0,
        "p95_duration": percentile_95(durations),
        "categories": dict(sorted(categories.items())),
        "durations": durations,
    }


def split_into_blocks(items: list[Request], block_size: int = 500) -> list[list[Request]]:
    """Разбивает заявки на независимые блоки."""
    return [items[i:i + block_size] for i in range(0, len(items), block_size)]


def run_analysis(blocks, worker_function, executor_class=None, max_workers=1):
    """Запускает обработку последовательно или через пул исполнителей."""
    if executor_class is None:
        parts = map(worker_function, blocks)
        return combine_results(parts)

    with executor_class(max_workers=max_workers) as executor:
        parts = list(executor.map(worker_function, blocks))
    return combine_results(parts)


def measure(blocks, worker_function, executor_class=None, max_workers=1):
    """Выполняет три замера и возвращает результат и медиану времени."""
    times = []
    result = None
    for _ in range(3):
        started = perf_counter()
        result = run_analysis(
            blocks, worker_function, executor_class, max_workers
        )
        times.append(perf_counter() - started)
    return result, median(times), times


def assign_requests_to_executors(requests: list[Request], executor_count: int = 4):
    """
    Распределяет корректные заявки между исполнителями.
    Выбор исполнителя и обновление его нагрузки выполняются под Lock.
    Заявка направляется исполнителю с минимальной суммарной длительностью.
    """
    lock = Lock()
    loads = [0.0] * executor_count
    assigned: list[tuple[int, int]] = []

    def assign(request: Request):
        try:
            duration = duration_of(request)
        except ValueError:
            return request.request_id, None

        with lock:
            executor_id = min(range(executor_count), key=lambda i: (loads[i], i))
            loads[executor_id] += duration
            assigned.append((request.request_id, executor_id))
            return request.request_id, executor_id

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(assign, requests))

    assigned_ids = [request_id for request_id, executor_id in results
                    if executor_id is not None]
    invalid_ids = [request_id for request_id, executor_id in results
                   if executor_id is None]

    # Инварианты корректного распределения.
    assert len(assigned_ids) == len(set(assigned_ids))
    assert len(assigned_ids) + len(invalid_ids) == len(requests)
    assert all(load >= 0 for load in loads)
    return assigned, loads, invalid_ids


def run_tests():
    """Проверяет граничные случаи и корректность распределения."""
    valid = Request(1, "Учебная", 10.0, 20.0)
    invalid = Request(2, "Техническая", 20.0, 10.0)
    negative = Request(3, "Финансовая", -1.0, 5.0)

    assert duration_of(valid) == 10.0

    for item in (invalid, negative):
        try:
            duration_of(item)
        except ValueError:
            pass
        else:
            raise AssertionError("Некорректный интервал не был отклонён")

    empty_result = combine_results([])
    assert empty_result["valid_count"] == 0
    assert empty_result["median_duration"] == 0.0

    sample = [
        Request(10, "Учебная", 0, 10),
        Request(11, "Учебная", 0, 20),
        Request(12, "Техническая", 0, 30),
        Request(13, "Финансовая", 0, 40),
    ]
    result = run_analysis([sample], analyze_block)
    assert result["valid_count"] == 4
    assert result["median_duration"] == 25.0
    assert result["p95_duration"] == 40.0

    test_requests = [
        Request(i, "Учебная", 0, 5) for i in range(15)
    ] + [Request(100, "Ошибка", 10, 5)]
    assigned, loads, invalid_ids = assign_requests_to_executors(test_requests)
    assert len(assigned) == 15
    assert len(invalid_ids) == 1
    assert sum(loads) == 75.0
    print("Тесты: успешно пройдены (6 проверок).")


def main():
    print("=" * 68)
    print("ЛАБОРАТОРНАЯ РАБОТА №13 — ВАРИАНТ 17: ЭЛЕКТРОННЫЕ ЗАЯВКИ")
    print("=" * 68)

    run_tests()

    # Набор данных для основного сравнения моделей.
    requests = generate_requests(4000)
    blocks = split_into_blocks(requests, 500)

    expected = run_analysis(blocks, analyze_block)
    print("\nИтоговая статистика:")
    print(f"Всего заявок: {len(requests)}")
    print(f"Корректных заявок: {expected['valid_count']}")
    print(f"Ошибочных интервалов: {expected['invalid_count']}")
    print(f"Медиана длительности: {expected['median_duration']:.3f}")
    print(f"95-й процентиль: {expected['p95_duration']:.3f}")
    print(f"По категориям: {expected['categories']}")

    print("\nСРАВНЕНИЕ МОДЕЛЕЙ (3 запуска, выводится медиана времени)")
    print("Модель                         Работники   Медиана, сек.")
    print("-" * 68)

    # Последовательная вычислительная модель.
    seq_result, seq_time, seq_runs = measure(blocks, analyze_block)
    assert seq_result == expected
    print(f"{'Последовательно (CPU)':<30} {1:>8}   {seq_time:.6f}")
    print("  Замеры:", ", ".join(f"{x:.6f}" for x in seq_runs))

    # Потоки с имитацией ожидания ввода-вывода.
    for workers in WORKERS_TO_TEST:
        thread_result, thread_time, thread_runs = measure(
            blocks, analyze_block_with_wait, ThreadPoolExecutor, workers
        )
        assert thread_result == expected
        print(f"{'Потоки (I/O)':<30} {workers:>8}   {thread_time:.6f}")
        print("  Замеры:", ", ".join(f"{x:.6f}" for x in thread_runs))

    # Процессы для независимых вычислений.
    for workers in WORKERS_TO_TEST:
        process_result, process_time, process_runs = measure(
            blocks, analyze_block, ProcessPoolExecutor, workers
        )
        assert process_result == expected
        print(f"{'Процессы (CPU)':<30} {workers:>8}   {process_time:.6f}")
        print("  Замеры:", ", ".join(f"{x:.6f}" for x in process_runs))

    # Сценарий назначения исполнителей с защитой общего состояния.
    assigned, loads, invalid_ids = assign_requests_to_executors(requests, 4)
    print("\nНАЗНАЧЕНИЕ ИСПОЛНИТЕЛЕЙ (Lock)")
    print(f"Назначено корректных заявок: {len(assigned)}")
    print(f"Отклонено ошибочных заявок: {len(invalid_ids)}")
    for index, load in enumerate(loads, start=1):
        print(f"Исполнитель {index}: суммарная нагрузка {load:.3f}")

    print("\nПроверка совпадения результатов всех моделей: успешно.")
    print("Работа программы завершена.")


if __name__ == "__main__":
    main()
