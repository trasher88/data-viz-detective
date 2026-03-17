#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.parser.hh_parser import HHParser
from src.database.db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_last_run_date():
    """Получить дату последнего запуска из файла"""
    try:
        with open('last_run.txt', 'r') as f:
            last_date = f.read().strip()
            return datetime.strptime(last_date, '%Y-%m-%d').date()
    except:
        # Если файла нет, берем дату 7 дней назад
        return (datetime.now() - timedelta(days=7)).date()


def save_last_run_date():
    """Сохранить дату последнего запуска"""
    with open('last_run.txt', 'w') as f:
        f.write(datetime.now().strftime('%Y-%m-%d'))


def main():
    """Автоматический запуск парсера"""

    print("=" * 50)
    print("🤖 DataViz Detective - Автоматический парсер")
    print("=" * 50)

    # Инициализация
    parser = HHParser()
    db = DatabaseManager("data/vacancies.db")

    # Поисковые запросы
    queries = [
        "Data Analyst",
        "Data Scientist",
        "Data Engineer",
        "BI Analyst",
        "Инженер данных",
        "Аналитик данных",
        "Бизнес-аналитик",
        "Продуктовый аналитик",
        "Системный аналитик",
        "ML инженер",
        "Аналитик"
    ]

    # Получаем дату последнего запуска
    last_run = get_last_run_date()
    today = datetime.now().date()

    print(f"\n📅 Последний запуск: {last_run}")
    print(f"📅 Текущая дата: {today}")
    print(f"📊 Парсим новые вакансии за последние {(today - last_run).days} дней")

    # Запускаем парсер (только 1 страницу, чтобы не нагружать)
    vacancies = parser.run_parser(
        search_queries=queries,
        max_pages=2  # Для автоматического режима достаточно 2 страниц
    )

    # Сохраняем в базу
    if vacancies:
        saved, skipped = db.save_vacancies_bulk(vacancies)
        print(f"\n✅ Результат:")
        print(f"   Новых вакансий: {saved}")
        print(f"   Дубликатов: {skipped}")

        # Отправляем уведомление (пока просто в лог)
        if saved > 0:
            # Отправляем уведомление в Telegram
            try:
                from src.bot.telegram_bot import TelegramNotifier
                bot = TelegramNotifier()
                stats = db.get_stats()
                message = bot.format_stats(stats, saved)
                bot.send_sync(message)
            except Exception as e:
                logger.error(f"Ошибка отправки в Telegram: {e}")

    # Сохраняем дату запуска
    save_last_run_date()
    print(f"\n💾 Дата запуска сохранена")

    return 0


if __name__ == "__main__":
    sys.exit(main())