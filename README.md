# 📊 DataViz Detective - Аналитик рынка вакансий для Data-специалистов

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red)](https://streamlit.io/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)](https://core.telegram.org/bots)

Автоматизированная система для сбора, анализа и визуализации вакансий для Data-специалистов (Analyst, Scientist, Engineer) с hh.ru.

**🌐 Демо дашборда:** [http://109.73.202.131:8502](http://109.73.202.131:8502)
### Работа дашборда
![Дашборд](screenshots/dataviz1.gif)

---

**🤖 Telegram-бот:** [@Datavizdetectivebot](https://t.me/Datavizdetectivebot) — команды: `/stats`, `/recent`, `/top_companies`, `/search`, `/trends` и другие.
### Работа бота
![Telegram](screenshots/dataviz2.gif)

---

## ✨ Возможности

### 🔍 Парсер вакансий
- Ежедневный автоматический сбор вакансий с hh.ru
- Инкрементальное обновление (только новые вакансии)
- Сохранение в SQLite и JSON
- Автоматический запуск через cron / GitHub Actions

### 📊 Дашборд (Streamlit)
- **Фильтрация:** по профессии, уровню (Junior/Middle/Senior), городу, дате, зарплате
- **Ключевые метрики:** количество вакансий, средняя зарплата, компании, города
- **Графики:** топ-20 компаний, распределение зарплат, динамика по дням/неделям/месяцам
- **Анализ навыков:** топ-20 требуемых навыков, частота упоминаний
- **Таблица последних вакансий** с прямыми ссылками

### 🤖 Telegram-бот
| Команда | Описание |
|---------|----------|
| `/stats` | Общая статистика |
| `/recent` | Последние 5 вакансий |
| `/top_companies [N]` | Топ N компаний |
| `/top_cities [N]` | Топ N городов |
| `/top_skills [N]` | Топ N навыков |
| `/salary_by_city [город]` | Средняя зарплата по городу |
| `/salary_by_level [уровень]` | Зарплата по уровню (Junior/Middle/Senior) |
| `/trends` | Динамика за 30 дней |
| `/search [слово]` | Поиск вакансий |

### ⚙️ Автоматизация
- **systemd:** автозапуск дашборда и бота при старте сервера
- **cron:** ежедневный парсинг новых вакансий в 4:00
- **GitHub Actions:** резервное копирование данных

---

## 🛠️ Технологии

| Компонент | Технологии |
|-----------|------------|
| Парсер | Python, requests, BeautifulSoup4 |
| База данных | SQLite, SQLAlchemy |
| Дашборд | Streamlit, Plotly, Pandas |
| Telegram-бот | python-telegram-bot, httpx |
| Деплой | VPS (Timeweb), systemd, Nginx |
| CI/CD | GitHub Actions |

---

📁 СТРУКТУРА ПРОЕКТА
```markdown
/data-viz-detective
├── src/
│   ├── parser/hh_parser.py
│   ├── database/db_manager.py
│   ├── dashboard/app.py
│   └── bot/telegram_bot.py
├── data/
│   ├── raw/               # JSON-файлы с вакансиями
│   └── vacancies.db       # SQLite база данных
├── logs/                  # Логи парсера
├── venv/                  # Виртуальное окружение
├── bot.py                 # Telegram-бот
├── run_parser_auto.py     # Инкрементальный парсер
├── .env                   # Токен Telegram
└── requirements.txt
```

```markdown
src/parser/hh_parser.py - класс парсера (общение с сайтом hh.ru)
Класс HHParser автоматически собирает информацию о вакансиях.
Технически: Это "обертка" над API hh.ru. Внутри него есть методы (функции), которые умеют:
 - search_vacancies() - искать вакансии
 - get_vacancy_detail() - заходить внутрь каждой вакансии и читать детали
 - extract_salary() - вытаскивать зарплату
 - run_parser() - запускать всё вместе

Как API это понимает?
HH.ru ищет точное вхождение слов в названии вакансии.
"Data Analyst" найдет: "Data Analyst", "Junior Data Analyst", "Senior Data Analyst"
"Аналитик" найдет всё подряд (и data, и системных, и бизнес)

src/parser/utils.py - вспомогательные функции

run_parser.py - в корне проекта (скрипт запуска)
запуск run_parser.py:
- начнется парсинг
- создастся папка data/raw/
- в data/raw/ появятся JSON файлы с вакансиями
- создастся файл parser.log
- проверить содержимое data/raw/ (должны быть файлы вида 20231225_123456.json)

models.py - модель вакансии для SQLAlchemy
db_manager.py - менеджер для работы с базой данных SQLite
load_to_db.py - скрипт для загрузки JSON из data/raw/ в БД

app.py - дашборд
run_parser_auto.py - нужно сделать так, чтобы парсер мог работать без ручного вмешательства
daily_parser.yml - настройка GitHub Actions
```




---

## 🚀 Быстрый старт
### Локальный запуск

```bash
# Клонирование репозитория
git clone https://github.com/trasher88/data-viz-detective.git
cd data-viz-detective

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Парсинг вакансий
python run_parser.py

# Загрузка в базу данных
python load_to_db.py

# Запуск дашборда
streamlit run src/dashboard/app.py

# Запуск Telegram-бота (нужен .env с токеном)
python bot.py
```

---

ДЕПЛОЙ НА СЕРВЕР
```bash
# Копирование файлов
scp -r ./* root@YOUR_SERVER:/root/data-viz-detective/

# На сервере: установка зависимостей
cd /root/data-viz-detective
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка systemd сервисов
cp deploy/dataviz_detective.service /etc/systemd/system/
cp deploy/dataviz_detective_bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now dataviz_detective
systemctl enable --now dataviz_detective_bot

# Настройка cron для ежедневного парсинга
crontab -e
# Добавить: 0 4 * * * cd /root/data-viz-detective && ./venv/bin/python run_parser_auto.py >> logs/parser_cron.log 2>&1
```

---

### 🔧 Конфигурация
Переменные окружения (файл .env)
```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
TELEGRAM_CHAT_ID=ваш_chat_id
```

---

### Настройка поисковых запросов

В файле run_parser_auto.py можно изменить список профессий:
```python
queries = [
    "Data Analyst",
    "Data Scientist", 
    "Data Engineer",
    "BI Analyst",
    "Аналитик данных",
    "Python разработчик",
    "Аналитик"
]
```

---

🛠️ ПОЛЕЗНЫЕ КОМАНДЫ ДЛЯ ОБСЛУЖИВАНИЯ
```bash
# Статус сервисов
systemctl status dataviz_detective
systemctl status dataviz_detective_bot

# Перезапуск
systemctl restart dataviz_detective
systemctl restart dataviz_detective_bot

# Логи
journalctl -u dataviz_detective -f
journalctl -u dataviz_detective_bot -f
tail -50 /data-viz-detective/logs/parser_cron.log

# Ручной запуск парсера
cd /data-viz-detective && ./venv/bin/python run_parser_auto.py

# Количество вакансий в базе
sqlite3 /data-viz-detective/data/vacancies.db "SELECT COUNT(*) FROM vacancies;"
```
