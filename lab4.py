from dataclasses import dataclass
import unittest


# =====================================
# 1. Модель студента
# =====================================

@dataclass
class Student:
    name: str
    average_grade: float
    debts: int = 0

    def is_admitted(self) -> bool:
        """Проверяет, допущен ли студент к экзамену."""
        return self.average_grade >= 50 and self.debts == 0


# =====================================
# 2. Расчёты (вариант 13)
# =====================================

def count_admitted(students: list[Student]) -> int:
    """Подсчитывает количество допущенных студентов."""
    return sum(1 for student in students if student.is_admitted())


def calculate_admission_percentage(students: list[Student]) -> float:
    """Рассчитывает процент допущенных студентов."""
    if not students:
        return 0.0

    admitted = count_admitted(students)
    return round(admitted / len(students) * 100, 2)


# =====================================
# 3. Формирование отчёта
# =====================================

def generate_report(students: list[Student]) -> str:
    total = len(students)
    admitted = count_admitted(students)
    not_admitted = total - admitted
    percentage = calculate_admission_percentage(students)

    lines = [
        "========== ОТЧЁТ О ДОПУСКЕ ==========",
        f"Всего студентов: {total}",
        f"Допущено: {admitted}",
        f"Не допущено: {not_admitted}",
        f"Процент допуска: {percentage:.2f}%",
        "",
        "Список студентов:"
    ]

    for student in students:
        status = "Допущен" if student.is_admitted() else "Не допущен"

        lines.append(
            f"{student.name} | "
            f"Средний балл: {student.average_grade} | "
            f"Задолженности: {student.debts} | "
            f"Статус: {status}"
        )

    return "\n".join(lines)


# =====================================
# 4. Автоматические тесты
# =====================================

class TestAdmissionCalculations(unittest.TestCase):

    def test_normal_calculation(self):
        students = [
            Student("Студент 1", 80, 0),
            Student("Студент 2", 40, 0),
            Student("Студент 3", 70, 1),
            Student("Студент 4", 60, 0)
        ]

        self.assertEqual(count_admitted(students), 2)
        self.assertEqual(
            calculate_admission_percentage(students), 50.0
        )

    def test_empty_list(self):
        self.assertEqual(
            calculate_admission_percentage([]), 0.0
        )

    def test_no_admitted_students(self):
        students = [
            Student("Студент 1", 30, 0),
            Student("Студент 2", 80, 1)
        ]

        self.assertEqual(count_admitted(students), 0)
        self.assertEqual(
            calculate_admission_percentage(students), 0.0
        )

    def test_minimum_passing_grade(self):
        students = [
            Student("Студент 1", 50, 0),
            Student("Студент 2", 49, 0)
        ]

        self.assertEqual(count_admitted(students), 1)
        self.assertEqual(
            calculate_admission_percentage(students), 50.0
        )


# =====================================
# 5. Запуск программы
# =====================================

def main():
    students = [
        Student("Миша", 85, 0),
        Student("Данил", 72, 0),
        Student("Илья", 45, 0),
        Student("Алия", 90, 1),
        Student("Арман", 60, 0),
        Student("Диана", 48, 2),
        Student("Азамат", 55, 0),
        Student("Аружан", 80, 0)
    ]

    print(generate_report(students))


if __name__ == "__main__":
    main()
