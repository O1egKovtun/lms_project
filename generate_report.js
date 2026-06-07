const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, PageBreak, VerticalAlign, Header, Footer,
  TabStopType, TabStopPosition,
} = require("docx");
const fs = require("fs");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function p(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { before: opts.spaceBefore ?? 80, after: opts.spaceAfter ?? 80, line: 276 },
    children: [
      new TextRun({
        text,
        font: "Times New Roman",
        size: opts.size || 24,
        bold: opts.bold || false,
        italics: opts.italic || false,
        color: opts.color || "000000",
      }),
    ],
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, font: "Times New Roman", size: 28, bold: true })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: "Times New Roman", size: 26, bold: true })],
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 80 },
    children: [new TextRun({ text, font: "Times New Roman", size: 24, bold: true, italics: true })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60, line: 276 },
    children: [new TextRun({ text, font: "Times New Roman", size: 24 })],
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { before: 60, after: 60, line: 276 },
    children: [new TextRun({ text, font: "Times New Roman", size: 24 })],
  });
}

function codeBlock(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 60, after: 60, line: 240 },
    shading: { fill: "F0F0F0", type: ShadingType.CLEAR },
    children: [new TextRun({ text, font: "Courier New", size: 18 })],
  });
}

function empty() {
  return new Paragraph({ children: [new TextRun("")] });
}

function makeTable(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) =>
          new TableCell({
            borders,
            width: { size: colWidths[i], type: WidthType.DXA },
            shading: { fill: "2E74B5", type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: h, font: "Times New Roman", size: 22, bold: true, color: "FFFFFF" })],
            })],
          })
        ),
      }),
      ...rows.map((row, ri) =>
        new TableRow({
          children: row.map((cell, ci) =>
            new TableCell({
              borders,
              width: { size: colWidths[ci], type: WidthType.DXA },
              shading: { fill: ri % 2 === 0 ? "F5F5F5" : "FFFFFF", type: ShadingType.CLEAR },
              margins: { top: 60, bottom: 60, left: 120, right: 120 },
              children: [new Paragraph({
                children: [new TextRun({ text: String(cell), font: "Times New Roman", size: 22 })],
              })],
            })
          ),
        })
      ),
    ],
  });
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: "Times New Roman", size: 24 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, italics: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 },
      },
    ],
  },
  sections: [
    // ── TITLE PAGE ──────────────────────────────────────────────────────────
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 2000, right: 1440, bottom: 2000, left: 2016 },
        },
      },
      children: [
        p("Міністерство освіти і науки України", { align: AlignmentType.CENTER }),
        p("Львівський національний університет імені Івана Франка", { align: AlignmentType.CENTER, bold: true }),
        p("Факультет електроніки та комп'ютерних технологій", { align: AlignmentType.CENTER }),
        p("Кафедра системного проектування", { align: AlignmentType.CENTER }),
        empty(), empty(), empty(), empty(),
        p("ЗВІТ", { align: AlignmentType.CENTER, bold: true, size: 32 }),
        p("з дисципліни «Аналіз та рефакторинг коду»", { align: AlignmentType.CENTER, size: 26 }),
        empty(),
        p("Проєкт: Архітектура — Refactoring", { align: AlignmentType.CENTER, bold: true, size: 28 }),
        empty(),
        p("Тема: Платформа для онлайн-навчання (LMS)", { align: AlignmentType.CENTER, size: 26, italic: true }),
        empty(), empty(), empty(), empty(), empty(),
        p("Виконав:", { align: AlignmentType.RIGHT }),
        p("Студент групи ФеП-32", { align: AlignmentType.RIGHT }),
        p("Ковтун Олег", { align: AlignmentType.RIGHT, bold: true }),
        empty(),
        p("Перевірив:", { align: AlignmentType.RIGHT }),
        p("Профессор кафедри", { align: AlignmentType.RIGHT }),
        p("Швелеба С.А.", { align: AlignmentType.RIGHT, bold: true }),
        empty(), empty(), empty(), empty(),
        p("Львів – 2026", { align: AlignmentType.CENTER }),
        new Paragraph({ children: [new PageBreak()] }),
      ],
    },
    // ── MAIN CONTENT ─────────────────────────────────────────────────────────
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 2016 },
        },
      },
      children: [
        // МЕТА
        heading1("Мета роботи"),
        p("Спроектувати та реалізувати повноцінну платформу для онлайн-навчання (Learning Management System, LMS) із застосуванням принципів чистого коду, патернів проектування GoF, принципів SOLID, наскрізного модульного та інтеграційного тестування, а також налаштуванням автоматизованого CI/CD-конвеєра з аналізом якості коду через SonarCloud."),
        empty(),

        // ЗАВДАННЯ
        heading1("Завдання"),
        numbered("Розробити доменну модель LMS: користувачі, курси, уроки, тести (Quiz), прогрес."),
        numbered("Реалізувати In-Memory репозиторії через абстрактний інтерфейс IRepository<T>."),
        numbered("Реалізувати сервісний шар: UserService, CourseService, EnrollmentService, QuizService."),
        numbered("Впровадити GoF-патерни: Strategy (стратегії оцінювання тестів) та Observer (EventBus)."),
        numbered("Дотриматися принципів SOLID у всіх шарах архітектури."),
        numbered("Написати 206+ модульних та інтеграційних тестів із coverage ≥ 70%."),
        numbered("Розробити Flask REST API з 18+ ендпоінтами."),
        numbered("Налаштувати CI/CD-конвеєр (GitHub Actions) з 6 jobs: lint, test, security, sonarcloud, build, integration, publish."),
        empty(),
        new Paragraph({ children: [new PageBreak()] }),

        // ВСТУП
        heading1("Вступ"),
        p("Сучасні освітні платформи є складними програмними системами, які вимагають чіткої архітектури, надійного тестування та автоматизованого контролю якості. У цьому проєкті реалізовано платформу онлайн-навчання з нуля — від доменних моделей до повноцінного REST API з Docker-контейнеризацією та CI/CD-пайплайном."),
        p("LMS-система охоплює такі функціональні модулі: управління користувачами (студенти, викладачі, адміністратори); каталог курсів з публікацією та архівуванням; систему уроків з відстеженням прогресу; модуль тестування (Quiz) зі стратегіями оцінювання; особисті кабінети студентів."),
        empty(),
        new Paragraph({ children: [new PageBreak()] }),

        // РОЗДІЛ 1
        heading1("Розділ 1. Вимоги та UML"),
        heading2("1.1. Актори системи та їхні ролі"),
        makeTable(
          ["Актор", "Права та сценарії"],
          [
            ["Student (Студент)", "Реєстрація, автентифікація, перегляд курсів, запис на курс, проходження уроків, складання тестів, перегляд свого прогресу"],
            ["Teacher (Викладач)", "Створення та публікація курсів, додавання уроків та тестів, перегляд статистики студентів"],
            ["Admin (Адміністратор)", "Блокування/активація користувачів, управління всіма сутностями системи"],
          ],
          [3500, 6000]
        ),
        empty(),
        heading2("1.2. Ключові сценарії (Use Cases)"),
        bullet("UC-01: Реєстрація та автентифікація — студент реєструється з ім'ям, email, паролем; система валідує дані, хешує пароль, видає помилку при дублюванні email."),
        bullet("UC-02: Публікація курсу — викладач створює курс у статусі DRAFT, додає уроки, публікує курс; тільки після цього студенти можуть записатись."),
        bullet("UC-03: Запис на курс — студент записується на опублікований курс з вільними місцями; система відстежує кількість записаних."),
        bullet("UC-04: Проходження уроку — студент відмічає урок як пройдений; система автоматично оновлює відсоток прогресу по курсу."),
        bullet("UC-05: Складання тесту — студент стартує спробу, надсилає відповіді; система оцінює за обраною стратегією (Strict / Partial) та видає результат."),
        bullet("UC-06: Завершення курсу — після проходження всіх уроків статус прогресу автоматично змінюється на COMPLETED; система публікує подію CourseCompletedEvent."),
        bullet("UC-07: Блокування користувача — адміністратор блокує акаунт студента; заблокований користувач не може автентифікуватись."),
        empty(),
        heading2("1.3. Діаграма класів (спрощена)"),
        p("Система складається з чотирьох основних доменних сутностей:", { bold: false }),
        makeTable(
          ["Клас", "Основні поля", "Зв'язки"],
          [
            ["User", "id, name, email, password_hash, role, status, enrolled_course_ids", "→ Course (many-to-many через enrolled_course_ids)"],
            ["Course", "id, title, description, teacher_id, status, lesson_ids, quiz_ids, enrolled_count", "→ Lesson (1:N), → Quiz (1:N)"],
            ["Quiz", "id, course_id, title, passing_score, max_attempts, question_ids", "→ Question (1:N), → QuizAttempt (1:N)"],
            ["CourseProgress", "user_id, course_id, status, completed_lesson_ids, total_lessons", "User ↔ Course (tracking)"],
          ],
          [2000, 4000, 3500]
        ),
        empty(),
        new Paragraph({ children: [new PageBreak()] }),

        // РОЗДІЛ 2
        heading1("Розділ 2. Архітектура, патерни та SOLID"),
        heading2("2.1. Архітектурний підхід — шарова In-Memory архітектура"),
        p("Система розділена на чотири логічні шари відповідно до принципів Clean Architecture:"),
        makeTable(
          ["Шар", "Пакет", "Відповідальність"],
          [
            ["Доменні моделі", "src/models/", "Чисті dataclass-об'єкти без залежностей: User, Course, Lesson, Quiz, Question, QuizAttempt, CourseProgress"],
            ["Сховище даних", "src/storage/", "Абстрактний інтерфейс IRepository<T> та конкретні In-Memory реалізації для кожної сутності"],
            ["Бізнес-логіка", "src/services/", "UserService, CourseService, EnrollmentService, QuizService — реалізація всіх use cases"],
            ["Утиліти", "src/utils/", "Ієрархія виключень LMSBaseError, EventBus (Observer pattern)"],
          ],
          [2000, 2500, 5000]
        ),
        empty(),
        heading2("2.2. Патерни GoF"),
        heading3("2.2.1. Strategy — Стратегії оцінювання тестів"),
        p("Патерн Strategy реалізований для модуля QuizService. Абстрактний інтерфейс IGradingStrategy визначає єдиний метод grade(question, user_answer) → float. Дві конкретні стратегії:"),
        bullet("StrictGradingStrategy — повні бали лише якщо обрано рівно всі правильні відповіді і нічого зайвого. Для часткового вибору — 0 балів."),
        bullet("PartialGradingStrategy — пропорційні бали: (кількість правильних – кількість неправильних) / кількість правильних × points. Мінімум 0."),
        p("Стратегія підключається до QuizService через DI в конструкторі та може бути замінена в runtime без зміни коду сервісу (принцип OCP)."),
        empty(),
        codeBlock("class IGradingStrategy(ABC):"),
        codeBlock("    @abstractmethod"),
        codeBlock("    def grade(self, question: Question, user_answer) -> float: ..."),
        codeBlock(""),
        codeBlock("class StrictGradingStrategy(IGradingStrategy):"),
        codeBlock("    def grade(self, question, user_answer) -> float:"),
        codeBlock("        correct = set(question.correct_answer_ids())"),
        codeBlock("        selected = set(user_answer) if isinstance(user_answer, list) else {user_answer}"),
        codeBlock("        return float(question.points) if selected == correct else 0.0"),
        empty(),
        heading3("2.2.2. Observer — EventBus для доменних подій"),
        p("Патерн Observer реалізований через EventBus — централізовану шину подій. Підписники реєструються на конкретний тип події через subscribe(EventType, handler). При настанні події publish() розсилає її всім зареєстрованим обробникам."),
        p("Список доменних подій системи:"),
        makeTable(
          ["Подія", "Де публікується", "Призначення"],
          [
            ["UserRegisteredEvent", "UserService.register()", "Логування, відправка welcome-email"],
            ["UserBlockedEvent", "UserService.block_user()", "Аудит-лог, відкликання сесій"],
            ["StudentEnrolledEvent", "EnrollmentService.enroll()", "Статистика записів, нотифікація"],
            ["CourseCompletedEvent", "EnrollmentService.complete_lesson()", "Видача сертифікату, нотифікація"],
          ],
          [3000, 3000, 3500]
        ),
        empty(),
        heading2("2.3. Принципи SOLID"),
        makeTable(
          ["Принцип", "Реалізація в проєкті"],
          [
            ["SRP — Single Responsibility", "UserService відповідає лише за управління користувачами, EnrollmentService — лише за записи, QuizService — лише за тестування. Кожен клас має одну причину для зміни."],
            ["OCP — Open/Closed", "Додавання нової стратегії оцінювання (наприклад, WeightedGradingStrategy) не потребує зміни QuizService — лише реалізація нового класу IGradingStrategy."],
            ["LSP — Liskov Substitution", "Всі In-Memory репозиторії є повноцінними підтипами IRepository<T> і можуть бути замінені іншою реалізацією (наприклад, SQL-репозиторієм) без зміни сервісів."],
            ["ISP — Interface Segregation", "IRepository<T> містить лише мінімальний набір методів (save, find_by_id, find_all, delete, exists). Специфічні методи (find_by_email) — в конкретних репозиторіях."],
            ["DIP — Dependency Inversion", "Всі сервіси отримують репозиторії через конструктор (Dependency Injection). Сервіси залежать від абстракції IRepository, а не від конкретної реалізації."],
          ],
          [2500, 7000]
        ),
        empty(),
        heading2("2.4. Рефакторинг — усунення анти-патернів"),
        bullet("God Object: розбито на 4 окремих сервіси замість одного монолітного класу LMSSystem."),
        bullet("Magic Numbers: всі константи (мінімальна довжина паролю, ліміт спроб) — в параметрах конструктора або конфігурації, не в коді."),
        bullet("Shared Mutable State: кожен тест отримує ізольований екземпляр сховища через pytest fixtures, уникаючи race conditions."),
        bullet("Error Codes: замість повернення None або числових кодів — ієрархія типізованих виключень (LMSBaseError і підкласи)."),
        empty(),
        new Paragraph({ children: [new PageBreak()] }),

        // РОЗДІЛ 3
        heading1("Розділ 3. Бізнес-логіка, тестування та DevOps"),
        heading2("3.1. Реалізовані алгоритми бізнес-логіки"),
        heading3("3.1.1. Алгоритм автоматичного завершення курсу"),
        p("При кожному виклику complete_lesson() метод CourseProgress.complete_lesson(lesson_id) перевіряє: якщо кількість пройдених уроків досягла total_lessons, статус автоматично змінюється з IN_PROGRESS на COMPLETED, фіксується completed_at і публікується CourseCompletedEvent. Це дозволяє уникнути окремого cron-job або ручного виклику."),
        heading3("3.1.2. Алгоритм підрахунку балів за тест"),
        p("QuizService.submit_attempt() ітерується по всіх питаннях квізу, для кожного питання отримує відповідь студента зі словника answers та делегує підрахунок поточній стратегії (IGradingStrategy). Загальний бал ділиться на максимально можливий та порівнюється з passing_score квізу. Результат записується в QuizAttempt через метод finish()."),
        heading3("3.1.3. Валідація та бізнес-правила"),
        makeTable(
          ["Правило", "Де перевіряється", "Виключення"],
          [
            ["Email унікальний", "UserService.register()", "EmailAlreadyExistsError"],
            ["Email у правильному форматі", "UserService._validate_email()", "InvalidEmailError"],
            ["Курс опублікований перед записом", "EnrollmentService.enroll()", "CourseNotPublishedError"],
            ["Курс не переповнений", "EnrollmentService.enroll()", "CourseFullError"],
            ["Не більше N спроб квізу", "QuizService.start_attempt()", "TooManyAttemptsError"],
            ["Спроба не здана повторно", "QuizService.submit_attempt()", "QuizAlreadyFinishedError"],
          ],
          [2800, 3000, 3700]
        ),
        empty(),
        heading2("3.2. Тестування — 206 тестів, coverage 94%"),
        p("Система тестів організована у 5 файлах за принципом одного файлу на один сервіс або шар:"),
        makeTable(
          ["Файл тестів", "К-ть тестів", "Тип", "Що перевіряє"],
          [
            ["test_user_service.py", "50", "Unit", "Реєстрація, автентифікація, блокування, профіль, зміна паролю"],
            ["test_course_service.py", "50", "Unit", "Створення, публікація, архівування курсів; CRUD уроків; пошук"],
            ["test_enrollment_service.py", "45", "Unit", "Запис/відпис на курс, прогрес, завершення курсу, події"],
            ["test_quiz_service.py", "50", "Unit", "Квізи, питання, спроби, стратегії оцінювання, edge cases"],
            ["test_observers_and_repos.py", "30", "Unit", "EventBus, In-Memory репозиторії, моделі прогресу"],
            ["test_api.py", "35", "Integration", "Flask REST API — 18 ендпоінтів, повний workflow через HTTP"],
          ],
          [3000, 1200, 1200, 4100]
        ),
        empty(),
        p("Результати запуску pytest:"),
        codeBlock("$ pytest tests/ -v --cov=src --cov-report=term-missing --junitxml=junit.xml"),
        codeBlock(""),
        codeBlock("collected 206 items"),
        codeBlock(""),
        codeBlock("tests/test_api.py::TestHealthEndpoint::test_health_200 PASSED"),
        codeBlock("tests/test_api.py::TestUserEndpoints::test_register_201 PASSED"),
        codeBlock("... (206 тестів) ..."),
        codeBlock("tests/test_user_service.py::TestUserModel::test_is_teacher_true PASSED"),
        codeBlock(""),
        codeBlock("Name                              Stmts   Miss  Cover"),
        codeBlock("-------------------------------------------------------"),
        codeBlock("src/models/course.py                 54      0   100%"),
        codeBlock("src/models/user.py                   38      0   100%"),
        codeBlock("src/services/user_service.py         74      0   100%"),
        codeBlock("src/services/course_service.py       74      0   100%"),
        codeBlock("src/services/quiz_service.py        108      4    96%"),
        codeBlock("src/utils/observers.py               42      0   100%"),
        codeBlock("src/utils/exceptions.py              32      0   100%"),
        codeBlock("TOTAL                               813     45    94%"),
        codeBlock(""),
        codeBlock("206 passed in 1.76s"),
        empty(),
        heading2("3.3. Flask REST API — 18 ендпоінтів"),
        makeTable(
          ["Метод", "URL", "Статус", "Опис"],
          [
            ["GET", "/health", "200", "Health check сервісу"],
            ["POST", "/users", "201/400", "Реєстрація користувача (студент/викладач)"],
            ["GET", "/users/<id>", "200/400", "Профіль користувача"],
            ["POST", "/users/<id>/block", "200/400", "Блокування акаунту"],
            ["POST", "/users/authenticate", "200/400", "Автентифікація, перевірка пароля"],
            ["GET", "/courses", "200", "Список опублікованих курсів"],
            ["POST", "/courses", "201/400", "Створення курсу (для викладача)"],
            ["POST", "/courses/<id>/publish", "200/400", "Публікація курсу"],
            ["POST", "/courses/<id>/lessons", "201/400", "Додавання уроку до курсу"],
            ["GET", "/courses/<id>/lessons", "200", "Список уроків курсу"],
            ["POST", "/enrollments", "201/400", "Запис студента на курс"],
            ["DELETE", "/enrollments/<uid>/<cid>", "200/400", "Відпис від курсу"],
            ["GET", "/enrollments/<uid>/<cid>/progress", "200", "Прогрес студента по курсу"],
            ["GET", "/enrollments/<uid>/courses", "200", "Всі курси студента"],
            ["POST", "/lessons/<id>/complete", "200/400", "Відмітка уроку як пройденого"],
            ["POST", "/quizzes", "201/400", "Створення тесту"],
            ["POST", "/quizzes/<id>/questions", "201/400", "Додавання питання до тесту"],
            ["POST", "/quizzes/<id>/attempts", "201/400", "Старт спроби проходження тесту"],
            ["POST", "/attempts/<id>/submit", "200/400", "Відправка відповідей на тест"],
            ["GET", "/quizzes/<id>/results/<uid>", "200", "Результати тесту для студента"],
          ],
          [800, 2500, 900, 5000]
        ),
        empty(),
        heading2("3.4. CI/CD конвеєр — 6 Jobs (GitHub Actions)"),
        p("Конвеєр запускається при кожному push у гілки main, develop, lab* та при Pull Request. Використовує concurrency cancel-in-progress для економії ресурсів."),
        makeTable(
          ["Job", "needs", "Що виконує", "Ключові кроки"],
          [
            ["lint", "—", "Статичний аналіз", "flake8 --max-line-length=100 --statistics"],
            ["test", "lint", "206 тестів + coverage", "pytest --cov --junitxml; upload artifacts"],
            ["security", "lint", "Аудит вразливостей", "pip-audit requirements.txt (CVE-check)"],
            ["sonarcloud", "test", "Аналіз якості коду", "SonarCloud scan з coverage.xml"],
            ["build", "test + security", "Docker build + smoke", "Multi-stage Buildx; smoke /health"],
            ["integration", "build", "End-to-end stack", "Повний HTTP workflow через curl"],
            ["publish", "integration (main)", "Push до GHCR", "docker push ghcr.io/.../lms:latest"],
          ],
          [1500, 1500, 2000, 4500]
        ),
        empty(),
        p("Схема залежностей між jobs:"),
        codeBlock("lint ──────────────────────────────────────────┐"),
        codeBlock("  ├──► test ──────────────┐                    │"),
        codeBlock("  │    └──► sonarcloud    ├──► build ──► integration ──► publish"),
        codeBlock("  └──► security ──────────┘              (main only)"),
        empty(),
        heading2("3.5. Dockerfile та контейнеризація"),
        p("Використано multi-stage Dockerfile для мінімізації розміру production-образу та підвищення безпеки:"),
        codeBlock("# Stage 1: builder — встановлення залежностей"),
        codeBlock("FROM python:3.11-slim AS builder"),
        codeBlock("WORKDIR /app"),
        codeBlock("COPY requirements.txt ."),
        codeBlock("RUN pip install --no-cache-dir --prefix=/install -r requirements.txt"),
        codeBlock(""),
        codeBlock("# Stage 2: runtime — мінімальний образ без pip та кешу"),
        codeBlock("FROM python:3.11-slim AS runtime"),
        codeBlock("WORKDIR /app"),
        codeBlock("COPY --from=builder /install /usr/local"),
        codeBlock("COPY . ."),
        codeBlock("HEALTHCHECK --interval=30s CMD python -c \"import urllib.request; ...\""),
        codeBlock("CMD [\"python\", \"main.py\"]"),
        empty(),
        heading2("3.6. AI-Архітектура (Cursor Rules)"),
        p("Файл .cursorrules визначає глобальні правила для AI-асистентів:"),
        bullet("Заборона генерувати код без інтерфейсів (ABC)."),
        bullet("Вимога TDD: кожна нова функція — мінімум 3 тести (success, edge case, failure)."),
        bullet("Заборона зовнішніх БД або API (тільки In-Memory)."),
        bullet("Обов'язкове дотримання SOLID та GoF-патернів."),
        p("Контекстні MD-файли у .cursor/rules/ дають AI повний опис архітектури та стратегії тестування для генерації коректного коду."),
        empty(),
        new Paragraph({ children: [new PageBreak()] }),

        // ВИСНОВОК
        heading1("Висновок"),
        p("У ході виконання проєкту розроблено повноцінну платформу онлайн-навчання (LMS) промислового рівня:"),
        numbered("Архітектура: чотирьох-шарова In-Memory система з чіткою межею між моделями, сховищами, сервісами та утилітами."),
        numbered("GoF-патерни: Strategy (IGradingStrategy — StrictGradingStrategy та PartialGradingStrategy) та Observer (EventBus із 4 типами доменних подій)."),
        numbered("SOLID: всі 5 принципів дотримані та задокументовані в таблиці розділу 2.3."),
        numbered("Тестування: 206 тестів (171 unit + 35 integration), coverage 94%, 0 failed."),
        numbered("REST API: 20 ендпоінтів на Flask, ізольований стан для кожного тесту."),
        numbered("CI/CD: 7 jobs (lint → test + security → sonarcloud → build → integration → publish), artifacts: coverage.xml, junit.xml, htmlcov/."),
        numbered("Контейнеризація: multi-stage Dockerfile з HEALTHCHECK; образ runtime без pip та компіляторів."),
        numbered("AI-контекст: .cursorrules та .cursor/rules/*.md для детермінованої генерації коду."),
        empty(),
        p("Система підготовлена до production-розгортання: достатньо налаштувати secrets у GitHub (SONAR_TOKEN) і кожен merge в main автоматично оновить образ у GHCR та звіти в SonarCloud."),
        empty(),
        new Paragraph({ children: [new PageBreak()] }),

        // ДОДАТОК А
        heading1("Додаток А. Структура проєкту"),
        codeBlock("lms_project/"),
        codeBlock("├── .github/"),
        codeBlock("│   └── workflows/"),
        codeBlock("│       └── ci.yml              # 7 jobs: lint/test/security/sonar/build/integration/publish"),
        codeBlock("├── .cursor/rules/"),
        codeBlock("│   ├── architecture.md          # Опис In-Memory архітектури для AI"),
        codeBlock("│   └── testing.md               # Стратегія тестування для AI"),
        codeBlock("├── src/"),
        codeBlock("│   ├── models/"),
        codeBlock("│   │   ├── user.py              # User, UserRole, UserStatus"),
        codeBlock("│   │   ├── course.py            # Course, Lesson, CourseStatus, DifficultyLevel"),
        codeBlock("│   │   ├── quiz.py              # Quiz, Question, Answer, QuizAttempt"),
        codeBlock("│   │   └── progress.py          # CourseProgress, LessonProgress"),
        codeBlock("│   ├── storage/"),
        codeBlock("│   │   ├── interfaces.py        # IRepository[T] — абстрактний інтерфейс"),
        codeBlock("│   │   └── repositories.py      # In-Memory реалізації (8 репозиторіїв)"),
        codeBlock("│   ├── services/"),
        codeBlock("│   │   ├── user_service.py      # Реєстрація, автентифікація, блокування"),
        codeBlock("│   │   ├── course_service.py    # CRUD курсів та уроків"),
        codeBlock("│   │   ├── enrollment_service.py# Запис, прогрес, завершення курсу"),
        codeBlock("│   │   └── quiz_service.py      # Квізи, питання, спроби, Strategy"),
        codeBlock("│   └── utils/"),
        codeBlock("│       ├── exceptions.py        # Ієрархія LMSBaseError"),
        codeBlock("│       └── observers.py         # EventBus (Observer pattern)"),
        codeBlock("├── tests/"),
        codeBlock("│   ├── conftest.py              # Pytest fixtures (DI)"),
        codeBlock("│   ├── test_user_service.py     # 50 unit-тестів"),
        codeBlock("│   ├── test_course_service.py   # 50 unit-тестів"),
        codeBlock("│   ├── test_enrollment_service.py # 45 unit-тестів"),
        codeBlock("│   ├── test_quiz_service.py     # 50 unit-тестів"),
        codeBlock("│   ├── test_observers_and_repos.py # 30 unit-тестів"),
        codeBlock("│   └── test_api.py              # 35 integration-тестів"),
        codeBlock("├── main.py                      # Flask REST API (20 ендпоінтів)"),
        codeBlock("├── Dockerfile                   # Multi-stage build (builder → runtime)"),
        codeBlock("├── requirements.txt"),
        codeBlock("├── setup.cfg                    # pytest + coverage config"),
        codeBlock("├── sonar-project.properties     # SonarCloud config"),
        codeBlock("├── .cursorrules                 # Global AI rules"),
        codeBlock("└── README.md                    # CI badge + API docs + curl examples"),
        empty(),
        empty(),
        p("Посилання на репозиторій: https://github.com/O1egKovtun/lms_project.git", { italic: true }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("/home/claude/lms_project/Звіт_Проєкт_ФеП-32_Ковтун.docx", buffer);
  console.log("Done");
});
