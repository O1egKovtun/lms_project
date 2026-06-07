# Testing Strategy

## Фреймворк: pytest + pytest-cov

## Генерація звітів
```bash
pytest tests/ -v \
  --cov=src \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  --junitxml=junit.xml
```

## Мінімальне покриття: 70%
## Кількість тестів: 200+

## Структура тестів
- `test_user_service.py` — ~50 unit-тестів
- `test_course_service.py` — ~50 unit-тестів
- `test_enrollment_service.py` — ~45 unit-тестів
- `test_quiz_service.py` — ~50 unit-тестів
- `test_observers_and_repos.py` — ~30 unit-тестів
- `test_api.py` — ~35 integration-тестів

## Правила для AI
- Кожна нова функція → мінімум 3 тести (success, edge case, failure)
- Mock тільки зовнішні залежності
- Fixtures — в conftest.py
