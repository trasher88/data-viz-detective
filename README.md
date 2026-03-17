src/parser/hh_parser.py — сам класс парсера
Простыми словами: Это как пульт управления для общения с сайтом hh.ru.

Представь, что ты каждый раз открываешь браузер, вводишь поиск, копируешь вакансии — это делаешь руками. Класс HHParser делает то же самое, только автоматически и очень быстро.

Технически: Это "обертка" над API hh.ru. Внутри него есть методы (функции), которые умеют:

search_vacancies() — искать вакансии

get_vacancy_detail() — заходить внутрь каждой вакансии и читать детали

extract_salary() — вытаскивать зарплату

run_parser() — запускать всё вместе

Когда ты пишешь parser = HHParser() — ты создаешь такой пульт в памяти компьютера.

Как API это понимает?
HH.ru ищет точное вхождение слов в названии вакансии.

"Data Analyst" найдет: "Data Analyst", "Junior Data Analyst", "Senior Data Analyst"

"Аналитик" найдет всё подряд (и data, и системных, и бизнес)

src/parser/utils.py — вспомогательные функции

run_parser.py — в корне проекта (скрипт запуска)

запуск run_parser.py:
- Начнется парсинг (будет видно в консоли)
- Создастся папка data/raw/
- В ней появятся JSON файлы с вакансиями
- Создастся файл parser.log
- Проверить содержимое data/raw/ (должны быть файлы вида 20231225_123456.json)

parser.log - не работает!

models.py - Модель вакансии для SQLAlchemy
db_manager.py - Менеджер для работы с базой данных SQLite

load_to_db.py - скрипт для загрузки JSON в БД


запуск load_to_db.py (Загрузка вакансий в базу данных)

app.py - дашборд

запуск - streamlit run src/dashboard/app.py

Если что-то пошло не так
Удали файл data/vacancies.db и запусти load_to_db.py заново



run_parser_auto.py - нужно сделать так, чтобы парсер мог работать без ручного вмешательства

daily_parser.yml - Настройка GitHub Actions
telegram_bot.py - Telegram-бот для уведомлений


🚀 ПОРЯДОК ЗАПУСКА
1. Первый запуск (если база пустая)
bash
# Активировать окружение
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac

# Запустить парсер (соберет вакансии)
python run_parser.py

# Загрузить JSON в базу данных
python load_to_db.py

# Запустить дашборд
streamlit run src/dashboard/app.py
2. Обычный запуск (когда данные уже есть)
bash
# Активировать окружение
venv\Scripts\activate  # Windows

# Сразу запустить дашборд
streamlit run src/dashboard/app.py
3. Автоматический режим (новые вакансии)
bash
# Запустить авто-парсер (добавит только новые вакансии)
python run_parser_auto.py
4. Makefile (если настроил)
bash
make parse      # парсинг
make dashboard  # дашборд
make load-db    # загрузка в БД




проверка работы http://localhost:8502
