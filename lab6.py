import csv
import json
from io import StringIO
from dataclasses import dataclass
from abc import ABC, abstractmethod


# ==========================================
# 1. Модель студента
# ==========================================

@dataclass
class Student:
    student_id: int
    name: str
    group: str
    average_grade: float


# ==========================================
# 2. Ошибка импорта
# ==========================================

@dataclass
class ImportErrorInfo:
    row: int
    message: str

    def __str__(self):
        return f"Строка {self.row}: {self.message}"


# ==========================================
# 3. Интерфейс парсера
# ==========================================

class StudentParser(ABC):

    @abstractmethod
    def parse(self, data):
        """Преобразует исходные данные в список студентов."""
        pass


# ==========================================
# 4. Общая проверка данных
# ==========================================

def validate_student(record, row_number):
    errors = []

    required = ["student_id", "name", "group", "average_grade"]

    for field in required:
        if field not in record or str(record[field]).strip() == "":
            errors.append(f"отсутствует поле '{field}'")

    if errors:
        return None, errors

    try:
        student_id = int(record["student_id"])
    except (ValueError, TypeError):
        student_id = None
        errors.append("student_id должен быть целым числом")

    name = str(record["name"]).strip()
    group = str(record["group"]).strip()

    try:
        average_grade = float(record["average_grade"])
        if not 0 <= average_grade <= 100:
            errors.append("average_grade должен быть от 0 до 100")
    except (ValueError, TypeError):
        average_grade = None
        errors.append("average_grade должен быть числом")

    if not name:
        errors.append("имя не должно быть пустым")

    if not group:
        errors.append("группа не должна быть пустой")

    if errors:
        return None, errors

    return Student(
        student_id=student_id,
        name=name,
        group=group,
        average_grade=average_grade
    ), []


# ==========================================
# 5. CSV-парсер
# ==========================================

class CsvParser(StudentParser):

    def parse(self, data):
        students = []
        errors = []

        try:
            reader = csv.DictReader(StringIO(data))

            required = {
                "student_id", "name", "group", "average_grade"
            }

            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                return [], [
                    ImportErrorInfo(
                        1,
                        "CSV должен содержать столбцы: "
                        "student_id, name, group, average_grade"
                    )
                ]

            for row_number, record in enumerate(reader, start=2):
                student, row_errors = validate_student(
                    record, row_number
                )

                if row_errors:
                    for error in row_errors:
                        errors.append(
                            ImportErrorInfo(row_number, error)
                        )
                else:
                    students.append(student)

        except csv.Error as error:
            errors.append(ImportErrorInfo(1, f"Ошибка CSV: {error}"))

        return students, errors


# ==========================================
# 6. JSON-парсер
# ==========================================

class JsonParser(StudentParser):

    def parse(self, data):
        students = []
        errors = []

        try:
            records = json.loads(data)
        except json.JSONDecodeError as error:
            return [], [
                ImportErrorInfo(
                    error.lineno,
                    f"Некорректный JSON: {error.msg}"
                )
            ]

        if not isinstance(records, list):
            return [], [
                ImportErrorInfo(
                    1, "JSON должен содержать список студентов"
                )
            ]

        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                errors.append(
                    ImportErrorInfo(
                        index, "Запись должна быть JSON-объектом"
                    )
                )
                continue

            student, row_errors = validate_student(record, index)

            if row_errors:
                for error in row_errors:
                    errors.append(ImportErrorInfo(index, error))
            else:
                students.append(student)

        return students, errors


# ==========================================
# 7. Парсер из памяти
# ==========================================

class MemoryParser(StudentParser):

    def parse(self, data):
        students = []
        errors = []

        for index, record in enumerate(data, start=1):
            if not isinstance(record, dict):
                errors.append(
                    ImportErrorInfo(
                        index, "Запись должна быть словарём"
                    )
                )
                continue

            student, row_errors = validate_student(record, index)

            if row_errors:
                for error in row_errors:
                    errors.append(ImportErrorInfo(index, error))
            else:
                students.append(student)

        return students, errors


# ==========================================
# 8. Сервис импорта
# ==========================================

class ImportService:

    def __init__(self, parser: StudentParser):
        self.parser = parser

    def import_students(self, data):
        students, errors = self.parser.parse(data)

        print("\n========== ОТЧЁТ ИМПОРТА ==========")
        print(f"Успешно импортировано студентов: {len(students)}")
        print(f"Количество ошибок: {len(errors)}")

        if errors:
            print("\nНайденные ошибки:")

            for error in errors:
                print(f"- {error}")
        else:
            print("Ошибок нет.")

        return students, errors


# ==========================================
# 9. Демонстрация работы
# ==========================================

def main():
    csv_data = """student_id,name,group,average_grade
1,Миша,ИС-23,85
2,Данил,ИС-23,72
abc,Илья,ИС-24,90
4,,ИС-23,110
5,Алия,ИС-24,88
"""

    json_data = """
    [
        {
            "student_id": 1,
            "name": "Миша",
            "group": "ИС-23",
            "average_grade": 85
        },
        {
            "student_id": "abc",
            "name": "Данил",
            "group": "ИС-23",
            "average_grade": 72
        },
        {
            "student_id": 3,
            "name": "Илья",
            "group": "ИС-24",
            "average_grade": 95
        }
    ]
    """

    memory_data = [
        {
            "student_id": 10,
            "name": "Алия",
            "group": "ИС-23",
            "average_grade": 90
        },
        {
            "student_id": 11,
            "name": "Арман",
            "group": "ИС-24",
            "average_grade": 75
        }
    ]

    # Выбери нужный парсер:
    parser = CsvParser()
    data = csv_data

    # Для JSON используй:
    # parser = JsonParser()
    # data = json_data

    # Для данных в памяти используй:
    # parser = MemoryParser()
    # data = memory_data

    service = ImportService(parser)
    students, errors = service.import_students(data)

    print("\nКорректные студенты:")

    for student in students:
        print(student)


if __name__ == "__main__":
    main()
