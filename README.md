# 🎓 LMS Platform — Learning Management System

![CI](https://github.com/O1egKovtun/lms_project/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-206%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![SonarCloud](https://img.shields.io/badge/SonarCloud-Quality%20Gate%20A-brightgreen)

> Проєкт з дисципліни «Аналіз та рефакторинг коду» — Платформа онлайн-навчання  
> Студент ФеП-32, Ковтун Олег

---

## 📐 Архітектура

```
src/
├── models/        # Доменні моделі (User, Course, Quiz, Progress)
├── storage/       # IRepository[T] + In-Memory реалізації
├── services/      # Бізнес-логіка (4 сервіси)
└── utils/         # Exceptions, EventBus (Observer)
```

**GoF-патерни:**
- **Strategy** — `IGradingStrategy` (StrictGradingStrategy, PartialGradingStrategy)
- **Observer** — `EventBus` з подіями: `UserRegisteredEvent`, `StudentEnrolledEvent`, `CourseCompletedEvent`

## 🚀 Швидкий старт

```bash
# Локально
pip install -r requirements.txt
python main.py

# Docker
docker build -t lms:latest --target runtime .
docker run -p 5000:5000 lms:latest
```

## 🧪 Тести

```bash
pytest tests/ -v \
  --cov=src \
  --cov-report=html:htmlcov \
  --cov-report=xml:coverage.xml \
  --junitxml=junit.xml

# Результат: 206 passed, coverage 94%
```

## 🔌 API Ендпоінти

| Метод | URL | Опис |
|-------|-----|------|
| GET | `/health` | Health check |
| POST | `/users` | Реєстрація |
| POST | `/users/authenticate` | Автентифікація |
| GET | `/users/<id>` | Профіль |
| POST | `/users/<id>/block` | Блокування |
| GET | `/courses` | Список курсів |
| POST | `/courses` | Створення курсу |
| POST | `/courses/<id>/publish` | Публікація |
| POST | `/courses/<id>/lessons` | Додати урок |
| GET | `/courses/<id>/lessons` | Уроки курсу |
| POST | `/enrollments` | Запис на курс |
| DELETE | `/enrollments/<uid>/<cid>` | Відпис |
| GET | `/enrollments/<uid>/<cid>/progress` | Прогрес |
| GET | `/enrollments/<uid>/courses` | Курси студента |
| POST | `/lessons/<id>/complete` | Пройти урок |
| POST | `/quizzes` | Створити тест |
| POST | `/quizzes/<id>/questions` | Додати питання |
| POST | `/quizzes/<id>/attempts` | Почати спробу |
| POST | `/attempts/<id>/submit` | Здати тест |
| GET | `/quizzes/<id>/results/<uid>` | Результати |

## 🧾 curl-приклади

```bash
# Реєстрація студента
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Олег Ковтун","email":"oleg@t.com","password":"pass123","role":"student"}'

# Реєстрація викладача
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Проф. Гура","email":"gura@t.com","password":"pass123","role":"teacher"}'

# Створення курсу
curl -X POST http://localhost:5000/courses \
  -H "Content-Type: application/json" \
  -d '{"title":"Python від нуля","description":"Базовий курс Python для початківців","teacher_id":2,"category":"programming","difficulty":"beginner"}'

# Публікація курсу
curl -X POST http://localhost:5000/courses/1/publish

# Запис на курс
curl -X POST http://localhost:5000/enrollments \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"course_id":1}'

# Прогрес студента
curl http://localhost:5000/enrollments/1/1/progress
```

## 🏗️ CI/CD Pipeline (GitHub Actions)

```
lint ──────────────────────────────────┐
  ├──► test ──────────────┐            │
  │    └──► sonarcloud    ├──► build ──► integration ──► publish
  └──► security ──────────┘                              (main only)
```

Artifacts після кожного run: `coverage.xml`, `junit.xml`, `htmlcov/`

## 📊 Quality Metrics

| Метрика | Значення |
|---------|---------|
| Тести | 206 passed |
| Coverage | 94% |
| Bugs | 0 |
| Code Smells | A |
| Дублювання | < 3% |
