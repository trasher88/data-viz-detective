#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_load.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Загрузка JSON файлов в базу данных"""

    print("=" * 50)
    print("📦 Загрузка вакансий в базу данных")
    print("=" * 50)

    # Инициализация БД
    db = DatabaseManager("data/vacancies.db")

    # Получаем статистику до загрузки
    stats_before = db.get_stats()
    print(f"\n📊 До загрузки:")
    print(f"   Вакансий в БД: {stats_before['total']}")

    # Загружаем JSON
    print(f"\n🔄 Загрузка JSON файлов из data/raw/...")
    files, saved, skipped = db.load_json_to_db()

    # Получаем статистику после загрузки
    stats_after = db.get_stats()

    print(f"\n✅ Результат:")
    print(f"   Обработано файлов: {files}")
    print(f"   Добавлено новых: {saved}")
    print(f"   Пропущено (дубликаты): {skipped}")
    print(f"\n📊 После загрузки:")
    print(f"   Всего вакансий: {stats_after['total']}")
    print(f"   Уникальных компаний: {stats_after['companies']}")
    print(f"   Городов: {stats_after['cities']}")
    print(f"   С указанной зарплатой: {stats_after['with_salary']}")

    print(f"\n📁 База данных: data/vacancies.db")
    print(f"📝 Лог: db_load.log")

    return 0


if __name__ == "__main__":
    sys.exit(main())