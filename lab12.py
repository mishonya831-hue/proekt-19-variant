import asyncio
import time
from typing import Any

SENTINEL = object()

SAMPLE_PAYMENTS: list[dict[str, Any]] = [
    {"payment_id": "PAY-101", "student": "Алия", "amount": 15000, "purpose": "Обучение"},
    {"payment_id": "PAY-102", "student": "Дамир", "amount": 5000, "purpose": "Общежитие"},
    {"payment_id": "PAY-101", "student": "Алия", "amount": 15000, "purpose": "Обучение"},  # дубликат по ID
    {"payment_id": "PAY-103", "student": "   ", "amount": 3000, "purpose": "Справка"},    # ошибка имени
    {"payment_id": "PAY-104", "student": "Руслан", "amount": -200, "purpose": "Обучение"}, # ошибка суммы
    {"payment_id": "PAY-105", "student": "Мадина", "amount": 12000, "purpose": ""},       # ошибка назначения
    {"payment_id": "PAY-106", "student": "Тимур", "amount": 8500, "purpose": "Курсы"},
]


def validate_payment(payment: dict[str, Any]) -> tuple[str, str, float, str]:
    """Проверяет корректность полей платежа."""
    payment_id = str(payment.get("payment_id", "")).strip()
    student = str(payment.get("student", "")).strip()
    purpose = str(payment.get("purpose", "")).strip()
    amount = payment.get("amount")

    if not payment_id:
        raise ValueError("Не указан ID платежа")
    if not student:
        raise ValueError("Не указан студент")
    if not purpose:
        raise ValueError("Не указано назначение платежа")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("Сумма платежа должна быть больше 0")

    return payment_id, student, float(amount), purpose


async def charge_gateway(payment_id: str, student: str, amount: float) -> str:
    """Имитирует обращение к платежному шлюзу."""
    await asyncio.sleep(0.2)
    return f"TX-{payment_id}-{student[:2].upper()}-{int(amount)}"


async def process_payment_with_retry(
    payment: dict[str, Any],
    seen_ids: set[str],
    processed_results: dict[str, dict[str, Any]],
    lock: asyncio.Lock,
    max_retries: int = 2,
    timeout_sec: float = 0.6,
) -> tuple[str, dict[str, Any] | None]:
    """Обрабатывает платёж с тайм-аутом, повторами и проверкой идемпотентности по ID."""
    payment_id, student, amount, purpose = validate_payment(payment)

    async with lock:
        if payment_id in seen_ids:
            cached = processed_results[payment_id]
            return "idempotent", {
                **cached,
                "note": f"Идемпотентный повтор по ID {payment_id} (повторного списания нет)",
            }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 2):
        try:
            async with asyncio.timeout(timeout_sec):
                tx_code = await charge_gateway(payment_id, student, amount)

            record = {
                "payment_id": payment_id,
                "student": student,
                "amount": amount,
                "purpose": purpose,
                "tx_code": tx_code,
                "attempts": attempt,
            }

            async with lock:
                if payment_id in seen_ids:
                    cached = processed_results[payment_id]
                    return "idempotent", {
                        **cached,
                        "note": f"Идемпотентный повтор по ID {payment_id} (повторного списания нет)",
                    }
                seen_ids.add(payment_id)
                processed_results[payment_id] = record

            return "confirmed", record

        except (TimeoutError, ConnectionError) as err:
            last_error = err
            if attempt <= max_retries:
                await asyncio.sleep(0.05 * attempt)

    raise RuntimeError(f"Сбой проведения платежа после повторов: {last_error}")


async def producer(queue: asyncio.Queue, payments: list[dict[str, Any]], num_consumers: int) -> None:
    """Помещает платежи в очередь и отправляет SENTINEL для каждого потребителя."""
    for payment in payments:
        await asyncio.sleep(0.1)
        await queue.put(payment)
        print(f"[Producer] В очереди: {payment}")

    for _ in range(num_consumers):
        await queue.put(SENTINEL)


async def consumer(
    name: str,
    queue: asyncio.Queue,
    confirmations: list[dict[str, Any]],
    idempotent_hits: list[dict[str, Any]],
    errors: list[str],
    seen_ids: set[str],
    processed_results: dict[str, dict[str, Any]],
    lock: asyncio.Lock,
) -> None:
    """Извлекает платежи из очереди, обрабатывает их и вызывает task_done."""
    while True:
        item = await queue.get()
        try:
            if item is SENTINEL:
                print(f"[{name}] Получен SENTINEL, завершение работы.")
                return

            try:
                status, payload = await process_payment_with_retry(
                    payment=item,
                    seen_ids=seen_ids,
                    processed_results=processed_results,
                    lock=lock,
                )
                if status == "confirmed" and payload is not None:
                    confirmations.append(payload)
                    print(f"[{name}] Подтвержден: {payload}")
                elif status == "idempotent" and payload is not None:
                    idempotent_hits.append(payload)
                    print(f"[{name}] {payload['note']}")
            except (ValueError, RuntimeError) as exc:
                msg = f"{item}: {exc}"
                errors.append(msg)
                print(f"[{name}] Ошибка: {msg}")
        finally:
            queue.task_done()


async def run_pipeline(payments: list[dict[str, Any]], maxsize: int = 3, num_consumers: int = 2) -> dict[str, Any]:
    """Запускает конвейер обработки платежей и возвращает статистику."""
    if not 2 <= maxsize <= 5:
        raise ValueError("maxsize должен быть в диапазоне от 2 до 5")
    if num_consumers < 2:
        raise ValueError("Требуется минимум 2 потребителя")

    queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
    confirmations: list[dict[str, Any]] = []
    idempotent_hits: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    processed_results: dict[str, dict[str, Any]] = {}
    lock = asyncio.Lock()

    started = time.perf_counter()
    workers = [
        asyncio.create_task(
            consumer(
                name=f"worker-{i}",
                queue=queue,
                confirmations=confirmations,
                idempotent_hits=idempotent_hits,
                errors=errors,
                seen_ids=seen_ids,
                processed_results=processed_results,
                lock=lock,
            )
        )
        for i in range(1, num_consumers + 1)
    ]

    await producer(queue, payments, num_consumers)
    await queue.join()
    await asyncio.gather(*workers)

    elapsed = time.perf_counter() - started
    total_amount = sum(item["amount"] for item in confirmations)
    avg_amount = total_amount / len(confirmations) if confirmations else 0.0

    return {
        "confirmed_count": len(confirmations),
        "idempotent_count": len(idempotent_hits),
        "errors_count": len(errors),
        "total_amount": total_amount,
        "avg_amount": avg_amount,
        "elapsed_sec": elapsed,
        "confirmations": confirmations,
        "idempotent_hits": idempotent_hits,
        "errors": errors,
    }


async def main() -> None:
    stats = await run_pipeline(SAMPLE_PAYMENTS, maxsize=3, num_consumers=2)
    print("\n--- ИТОГОВАЯ СТАТИСТИКА ---")
    print(f"Подтверждено платежей: {stats['confirmed_count']}")
    print(f"Идемпотентных повторов: {stats['idempotent_count']}")
    print(f"Ошибок: {stats['errors_count']}")
    print(f"Сумма подтвержденных платежей: {stats['total_amount']:.2f}")
    print(f"Средний платеж: {stats['avg_amount']:.2f}")
    print(f"Время выполнения: {stats['elapsed_sec']:.2f} c")
    for err in stats["errors"]:
        print("Ошибка:", err)


async def run_tests() -> None:
    """7 тестовых сценариев по плану лабораторной работы."""
    print("\n=== ТЕСТИРОВАНИЕ (7 СЦЕНАРИЕВ) ===")

    # 1. Все платежи корректны
    t1 = await run_pipeline([
        {"payment_id": "T1-1", "student": "Алия", "amount": 1000, "purpose": "Обучение"},
        {"payment_id": "T1-2", "student": "Дамир", "amount": 2000, "purpose": "Общежитие"},
    ])
    assert t1["confirmed_count"] == 2 and t1["errors_count"] == 0

    # 2. Пустое имя / пустое назначение
    t2 = await run_pipeline([
        {"payment_id": "T2-1", "student": "", "amount": 1000, "purpose": "Обучение"},
        {"payment_id": "T2-2", "student": "Алия", "amount": 1000, "purpose": "  "},
    ])
    assert t2["confirmed_count"] == 0 and t2["errors_count"] == 2

    # 3. Некорректная сумма (<= 0)
    t3 = await run_pipeline([
        {"payment_id": "T3-1", "student": "Алия", "amount": 0, "purpose": "Обучение"},
        {"payment_id": "T3-2", "student": "Алия", "amount": -500, "purpose": "Обучение"},
    ])
    assert t3["confirmed_count"] == 0 and t3["errors_count"] == 2

    # 4. Очередь maxsize=2 (обратное давление, данные не теряются)
    t4 = await run_pipeline([
        {"payment_id": "T4-1", "student": "Алия", "amount": 100, "purpose": "A"},
        {"payment_id": "T4-2", "student": "Дамир", "amount": 200, "purpose": "B"},
        {"payment_id": "T4-3", "student": "Руслан", "amount": 300, "purpose": "C"},
    ], maxsize=2)
    assert t4["confirmed_count"] == 3

    # 5. Идемпотентность по ID (повторный платёж не списывается повторно)
    t5 = await run_pipeline([
        {"payment_id": "T5-DUP", "student": "Алия", "amount": 4000, "purpose": "Обучение"},
        {"payment_id": "T5-DUP", "student": "Алия", "amount": 4000, "purpose": "Обучение"},
    ])
    assert t5["confirmed_count"] == 1 and t5["idempotent_count"] == 1 and t5["total_amount"] == 4000

    # 6. Тайм-аут и повторная попытка (retry)
    slow_payment = [{"payment_id": "T6-SLOW", "student": "Алия", "amount": 1500, "purpose": "Обучение"}]
    orig_charge = globals()["charge_gateway"]
    calls = 0

    async def flaky_charge(payment_id: str, student: str, amount: float) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            await asyncio.sleep(1.0)  # превысит timeout_sec=0.6 на 1-й попытке
        return await orig_charge(payment_id, student, amount)

    globals()["charge_gateway"] = flaky_charge
    try:
        t6 = await run_pipeline(slow_payment)
        assert t6["confirmed_count"] == 1 and calls >= 2
    finally:
        globals()["charge_gateway"] = orig_charge

    # 7. Пустой входной список (нет деления на ноль)
    t7 = await run_pipeline([])
    assert t7["confirmed_count"] == 0 and t7["avg_amount"] == 0.0 and t7["errors_count"] == 0

    print("Все 7 тестовых сценариев пройдены успешно.")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(run_tests())
