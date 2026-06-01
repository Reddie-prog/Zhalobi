# ЖКХ.Онлайн — платформа для жалоб ЖКХ

Веб-платформа для приёма, учёта и контроля обращений граждан по вопросам жилищно-коммунального хозяйства. Позволяет жителям подавать жалобы, отслеживать их статус, а администраторам — управлять ими и видеть аналитику.

---

## Возможности

**Для пользователей:**
- подача жалобы с выбором категории, адреса и приоритета
- отслеживание статуса по номеру обращения
- просмотр тайм-лайна событий по своей жалобе
- личный кабинет с историей обращений и уведомлениями

**Для администраторов:**
- управление статусами всех обращений
- ручная эскалация, назначение исполнителей
- экспорт обращений в CSV
- KPI-дашборд: всего, в работе, решено, эскалировано

**На карте:**
- интерактивная карта обращений (Leaflet + CARTO)
- фильтрация по статусу и категории
- панель «Проблемные районы» с рейтингом по нерешённым жалобам

---

## Стек

| Компонент   | Технология                          |
|-------------|-------------------------------------|
| Backend     | Python 3, FastAPI (async)           |
| База данных | SQLite (локально) / PostgreSQL (Docker) |
| ORM         | SQLAlchemy 2.0 (asyncio)            |
| Frontend    | Vanilla JS, CSS                     |
| Карта       | Leaflet.js + CARTO Positron         |
| Графики     | Chart.js                            |
| Деплой      | Docker Compose                      |

---

## Паттерны

- **Facade** — единая точка входа для всех операций с жалобами
- **Observer** — событийная шина для уведомлений и логирования
- **Command** — инкапсуляция операций (подать, изменить статус, эскалировать)

---

## Быстрый старт (локально)

```bash
git clone https://github.com/Maksim99003/Zhalobi.git
cd Zhalobi

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-local.txt

python local_main.py
```

Открыть в браузере: http://localhost:8000  
API docs: http://localhost:8000/docs  
Демо-admin: `admin@zhalobi.ru` / `admin123`

---

## Деплой через Docker

```bash
docker-compose up --build
```

- Frontend: http://localhost:80
- Backend API: http://localhost:8000

---

## Структура репозитория

```
Zhalobi/
├── backend/
│   └── app/
│       ├── api/          # роуты: auth, complaints, admin, stats
│       ├── patterns/     # facade.py, observer.py, command.py
│       ├── services/     # complaint_service.py, notification_service.py
│       ├── background/   # эскалация, обработчики событий
│       ├── models.py
│       ├── schemas.py
│       └── main.py
├── frontend/
│   ├── css/style.css
│   ├── js/               # config.js, api.js, auth.js, app.js
│   ├── index.html
│   └── nginx.conf
├── docker-compose.yml
├── local_main.py         # локальный запуск с SQLite
└── requirements-local.txt
```

---

## Статусы обращений

| Статус       | Описание                              |
|--------------|---------------------------------------|
| `new`        | Только что подано                     |
| `in_progress`| Принято в работу                     |
| `escalated`  | Эскалировано (нет ответа 72+ часов)  |
| `resolved`   | Решено                                |
| `closed`     | Закрыто                               |
