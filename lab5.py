# ==========================================
# Система проверки допуска к регистрации
# ==========================================

class Course:
    def __init__(self, code, name, prerequisites=None):
        self.code = code
        self.name = name
        self.prerequisites = prerequisites or []


class StudyPlan:
    def __init__(self, courses, completed_courses=None):
        self.courses = {course.code: course for course in courses}
        self.completed_courses = set(completed_courses or [])

    # Проверка недостающих пререквизитов
    def missing_prerequisites(self, course_code):
        if course_code not in self.courses:
            raise ValueError(
                f"Дисциплина {course_code} не найдена в учебном плане."
            )

        course = self.courses[course_code]

        return [
            code for code in course.prerequisites
            if code not in self.completed_courses
        ]

    # Проверка возможности регистрации
    def can_enroll(self, course_code):
        missing = self.missing_prerequisites(course_code)

        return len(missing) == 0

    # Поиск циклических зависимостей
    def find_cycles(self):
        visited = set()
        active = set()
        path = []
        cycles = []

        def dfs(code):
            if code in active:
                start = path.index(code)
                cycle = path[start:] + [code]

                if cycle not in cycles:
                    cycles.append(cycle)

                return

            if code in visited:
                return

            visited.add(code)
            active.add(code)
            path.append(code)

            course = self.courses.get(code)

            if course:
                for prerequisite in course.prerequisites:
                    dfs(prerequisite)

            path.pop()
            active.remove(code)

        for code in self.courses:
            dfs(code)

        return cycles

    # Вывод отчёта
    def print_report(self, course_code):
        if course_code not in self.courses:
            print(f"Ошибка: курс {course_code} не найден.")
            return

        course = self.courses[course_code]

        print("\n========== РЕЗУЛЬТАТ ПРОВЕРКИ ==========")
        print(f"Дисциплина: {course.name} ({course.code})")

        cycles = self.find_cycles()

        if cycles:
            print("\nВНИМАНИЕ: обнаружены циклические зависимости!")

            for cycle in cycles:
                print(" -> ".join(cycle))

            print("Регистрацию следует проверить после исправления плана.")
            return

        missing = self.missing_prerequisites(course_code)

        if not missing:
            print("Решение: ДОПУСК РАЗРЕШЁН.")
            print("Все необходимые курсы завершены.")
        else:
            print("Решение: ДОПУСК ЗАПРЕЩЁН.")
            print("Недостающие курсы:")

            for code in missing:
                if code in self.courses:
                    name = self.courses[code].name
                    print(f"- {code}: {name}")
                else:
                    print(f"- {code}: курс отсутствует в учебном плане")

        print("========================================")


# ==========================================
# Основная программа
# ==========================================

def main():
    courses = [
        Course("CS101", "Основы программирования"),
        Course("CS102", "Алгоритмы", ["CS101"]),
        Course("CS201", "Структуры данных", ["CS102"]),
        Course("CS301", "Искусственный интеллект", ["CS201"]),
        Course("CS401", "Машинное обучение", ["CS301", "MATH101"]),
        Course("MATH101", "Математика"),
    ]

    # Курсы, которые студент уже завершил
    completed = ["CS101", "CS102", "MATH101"]

    plan = StudyPlan(courses, completed)

    # Курс, на который студент хочет зарегистрироваться
    target_course = "CS401"

    plan.print_report(target_course)


if __name__ == "__main__":
    main()
