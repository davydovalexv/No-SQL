# База данных университета (MongoDB, шардинг)

Проект базы данных студентов университета с горизонтальным масштабированием (шардингом): схема, шардированный кластер, консольный клиент и сравнительное нагрузочное тестирование «до» и «после» шардинга-файл REPORT.md

## Порядок запуска

### Шаг 1. Запуск кластеров и импорт данных

Одна команда поднимает оба кластера (одиночный MongoDB и шардированный), ждёт инициализации и импортирует данные в оба:

`sudo bash docker-import-all.sh`

Данной командой:

1. Создаются каталоги `data/db`, `data/json`, JSON-файлы копируются в `data/json`.
2. Выполняется `docker compose down` и `docker compose up -d` — запускаются сервисы:
   - **mongodb_single** (порт 27019) — один инстанс MongoDB без шардинга;
   - **configsvr**, **shard1**, **shard2**, **mongos-router** (порт 27018), **mongo-setup**, **app**.
3. Ожидание ~40 секунд (инициализация реплика-сетов и шардинга).
4. Запуск `import_data.sh`: импорт одних и тех же данных сначала в шардированный кластер через `mongos_router`, затем в `mongodb_single`.

### Шаг 2. (Опционально) Проверка данных

Cтатус шардинга (должны быть оба шарда):

`sudo docker exec mongos_router mongosh --eval "sh.status()`

Подключиться к шардированному кластеру и посчитать документы:

`sudo docker exec mongos_router mongosh --eval "db.getSiblingDB('university_grades').students.countDocuments()`

Аналогично для одиночного инстанса:

`sudo docker exec mongodb_single mongosh --eval "db.getSiblingDB('university_grades').students.countDocuments()"`

### Шаг 3. Запуск консольного клиента

Клиент по умолчанию подключается к **шардированному** кластеру (mongos на порту 27018).

**Вариант A — с хоста:** 

`python client.py`

**Вариант B — из контейнера приложения:**

`sudo docker exec -it university_app python client.py`

В меню: **1** — список студентов, **2** — информация и оценки по `student_id`, **3** — добавить оценку, **0** — выход.

### Шаг 4. Сравнительное нагрузочное тестирование

Скрипт последовательно гоняет один и тот же сценарий нагрузки против одиночного инстанса и шардированного кластера, записывает результаты в DataFrame и строит сравнительные графики (bar-диаграмма задержек, bar-диаграмма ops/sec).

**Вариант A — с хоста:** 

`python load_test.py --threads 8 --ops-per-thread 2000`

**Вариант B — из контейнера приложения:**

В контейнере `app` уже заданы переменные `MONGO_URI_SINGLE` и `MONGO_URI_SHARDED`, поэтому сравнительный тест можно запускать без дополнительных настроек:

`sudo docker exec -it university_app python load_test.py --threads 8 --ops-per-thread 2000`

При запуске с хоста используются значения по умолчанию: single — `localhost:27019`, sharded — `localhost:27018`.

**Параметры:**

- `--threads` — число потоков (по умолчанию 8).
- `--ops-per-thread` — операций на поток (по умолчанию 1000).

В консоли выводятся сводки по каждому прогону и итоговая таблица пропускной способности (single vs sharded). Открываются два окна: столбчатая диаграмма задержек по кластерам и столбчатая диаграмма ops/sec.

### 5.Архитектура проекта

Nosql_final/
├── README.md                 # Документация и инструкция по запуску
├── REPORT.md                 # Отчёт: схема БД, шардинг, тестирование, выводы
├── comparison_latency.png, 
comparison_throughput.png     # Графики
├── docker-compose.yml        # Конфигурация Docker Compose (single MongoDB, configsvr, shard1, shard2, mongos, mongo-setup, app)
├── Dockerfile.app            # Образ приложения (Python: client, load_test, pymongo, pandas, matplotlib)
├── docker-import-all.sh      # Запуск кластеров и импорт данных в оба
├── import_data.sh            # Импорт JSON в шардированный кластер и в одиночный инстанс
├── requirements.txt          # Зависимости Python (pymongo, matplotlib, pandas)
├── client.py                 # Консольный клиент для работы с БД университета
├── load_test.py              # Сравнительное нагрузочное тестирование (single vs sharded), 
├── students.json             # Исходные данные (и копии в data/json/)
├── lecturers.json
├── courses.json
├── grades.json
├── enrollments.json
├── init-mongo.js             # Инициализация БД (для одиночного Mongo)
├── docker-run.sh             # Запуск одного контейнера MongoDB (альтернатива)
├── scripts/                  # Инициализация шардированного кластера
│   ├── init-configrs.js      # Реплика-сет config server (cfgRS)
│   ├── init-shard1rs.js      # Реплика-сет первого шарда (shard1RS)
│   ├── init-shard2rs.js      # Реплика-сет второго шарда (shard2RS)
│   └── init-router.js        # Добавление шардов в mongos, шардирование коллекций
└── data/
    └── json/                 # Копии JSON для импорта в контейнеры (создаётся docker-import-all.sh)
        ├── students.json
        ├── lecturers.json
        ├── courses.json
        ├── grades.json
        └── enrollments.json.