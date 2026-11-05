% ==============================================================================
% ЛАБОРАТОРНАЯ РАБОТА №10 + ИНДИВИДУАЛЬНЫЙ ВАРИАНТ №8 (ЭКЗАМЕН)
% ==============================================================================

% ------------------------------------------------------------------------------
% 1. ФАКТЫ ОСНОВНОЙ БАЗЫ ЗНАНИЙ (Задания 1-8)
% ------------------------------------------------------------------------------

% Студенты
student(aida).
student(miras).
student(dana).
student(timur).
student(aliya).

% Курсы
course(programming_1).
course(programming_2).
course(data_structures).
course(databases).
course(artificial_intelligence).
course(machine_learning).

% Освоенные дисциплины completed(Student, Course)
completed(aida, programming_1).
completed(aida, programming_2).
completed(aida, data_structures).
completed(aida, databases).
completed(miras, programming_1).
completed(miras, databases).
completed(dana, programming_1).
completed(dana, programming_2).
completed(dana, data_structures).
completed(timur, programming_1).
completed(aliya, programming_1).
completed(aliya, programming_2).

% Непосредственные пререквизиты requires(Course, Prerequisite)
requires(programming_2, programming_1).
requires(data_structures, programming_2).
requires(artificial_intelligence, data_structures).
requires(artificial_intelligence, databases).
requires(machine_learning, artificial_intelligence).


% ------------------------------------------------------------------------------
% 2. ПРАВИЛА ОСНОВНОЙ ЧАСТИ (Задания 2-8)
% ------------------------------------------------------------------------------

% Задание 2: Составные цели
ai_candidate(Student) :-
    completed(Student, data_structures),
    completed(Student, databases).

strong_student(Student) :-
    completed(Student, programming_2),
    completed(Student, data_structures).

% Задание 4: Непосредственный допуск
missing_direct(Student, Course, Prerequisite) :-
    student(Student),
    requires(Course, Prerequisite),
    \+ completed(Student, Prerequisite).

immediate_eligible(Student, Course) :-
    student(Student),
    course(Course),
    \+ missing_direct(Student, Course, _).

% Задание 5: Транзитивные пререквизиты (Рекурсия)
prerequisite(Course, Prerequisite) :-
    requires(Course, Prerequisite).

prerequisite(Course, Prerequisite) :-
    requires(Course, Intermediate),
    prerequisite(Intermediate, Prerequisite).

% Задание 6: Полный допуск и список недостающих курсов
missing_all(Student, Course, Missing) :-
    setof(P, (prerequisite(Course, P), \+ completed(Student, P)), Missing), !.
missing_all(_, _, []).

eligible(Student, Course) :-
    student(Student),
    course(Course),
    missing_all(Student, Course, []).

% Задание 7: Безопасность рекурсии
safe_prerequisite(Course, Prerequisite) :-
    safe_prerequisite(Course, Prerequisite, [Course]).

safe_prerequisite(Course, Prerequisite, _) :-
    requires(Course, Prerequisite).

safe_prerequisite(Course, Prerequisite, Visited) :-
    requires(Course, Next),
    \+ memberchk(Next, Visited),
    safe_prerequisite(Next, Prerequisite, [Next | Visited]).

% Задание 8: Интегрированные рекомендации
recommendation(Student, Course, eligible, []) :-
    eligible(Student, Course).

recommendation(Student, Course, missing, Missing) :-
    missing_all(Student, Course, Missing),
    Missing \= [].


% ------------------------------------------------------------------------------
% 3. ИНДИВИДУАЛЬНЫЙ ВАРИАНТ №8: ЭКЗАМЕН (exam_admission/2)
% ------------------------------------------------------------------------------

% Студенты варианта №8
exam_student(ivan).
exam_student(petr).
exam_student(olga).
exam_student(anna).

% Дисциплина
course_exam(math).

% Посещаемость (%)
attendance(ivan, math, 85).
attendance(petr, math, 60).
attendance(olga, math, 90).
attendance(anna, math, 95).

% Зависимости лабораторных работ
lab_depends(lab2, lab1).
lab_depends(lab3, lab2).

% Обязательные лабораторные работы
required_lab(math, lab1).
required_lab(math, lab2).
required_lab(math, lab3).

% Сданные лабораторные
lab_done(ivan, math, lab1).
lab_done(ivan, math, lab2).
lab_done(ivan, math, lab3).

lab_done(petr, math, lab1).

lab_done(olga, math, lab1).
lab_done(olga, math, lab2).
lab_done(olga, math, lab3).

lab_done(anna, math, lab1).

% Порог посещаемости (%)
min_attendance(math, 75).

% Правила варианта №8
prereq_lab(Lab, Prereq) :-
    lab_depends(Lab, Prereq).
prereq_lab(Lab, Prereq) :-
    lab_depends(Lab, Interm),
    prereq_lab(Interm, Prereq).

has_attendance(Student, Course) :-
    attendance(Student, Course, Percent),
    min_attendance(Course, Min),
    Percent >= Min.

missing_lab(Student, Course, Lab) :-
    required_lab(Course, Lab),
    \+ lab_done(Student, Course, Lab).

all_labs_done(Student, Course) :-
    exam_student(Student),
    course_exam(Course),
    \+ missing_lab(Student, Course, _).

exam_admission(Student, Course) :-
    exam_student(Student),
    has_attendance(Student, Course),
    all_labs_done(Student, Course).


% ------------------------------------------------------------------------------
% 4. ПРИМЕРЫ ЗАПРОСОВ ДЛЯ SWISH (Появятся кнопками снизу справа)
% ------------------------------------------------------------------------------
/** <examples>
?- exam_admission(ivan, math).
?- exam_admission(petr, math).
?- exam_admission(anna, math).
?- exam_admission(Student, math).
?- missing_lab(anna, math, Lab).
?- recommendation(miras, artificial_intelligence, Status, Missing).
*/
