# Architecture: In-Memory LMS

## Шари архітектури
- **models/** — чисті доменні об'єкти (dataclass, enum)
- **storage/** — In-Memory репозиторії, що реалізують IRepository[T]
- **services/** — бізнес-логіка, отримує репозиторії через DI
- **utils/** — виключення, EventBus (Observer)

## Патерни GoF
- **Strategy** — IGradingStrategy (Strict / Partial)
- **Observer** — EventBus.publish/subscribe

## SOLID
- SRP: кожен клас — одна відповідальність
- OCP: нові стратегії без зміни QuizService
- LSP: всі репозиторії взаємозамінні через IRepository
- ISP: IRepository — мінімальний інтерфейс
- DIP: сервіси залежать від абстракцій
