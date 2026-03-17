#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime

import os
os.makedirs('logs', exist_ok=True)

# Добавляем путь к проекту для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.parser.hh_parser import HHParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parser.log', encoding='utf-8', mode='w'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Переопределяет предыдущие настройки
)

logger = logging.getLogger(__name__)


def print_banner():
    """Красивый баннер при запуске"""
    banner = """
    ╔════════════════════════════════════════╗
    ║     DataViz Detective - Парсер         ║
    ║         hh.ru Vacancy Parser           ║
    ╚════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Основная функция запуска парсера"""

    print_banner()
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    # Инициализация парсера
    logger.info("Инициализация парсера...")
    parser = HHParser()

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

    print("\n📊 Поисковые запросы:")
    for q in queries:
        print(f"   • {q}")

    print(f"\n🔄 Начинаем парсинг...\n")

    try:
        # Запуск парсера
        vacancies = parser.run_parser(
            search_queries=queries,
            max_pages=3  # Для теста 3 страницы
        )

        # Итоги
        print("\n" + "=" * 50)
        print(f"✅ Парсинг завершен!")
        print("=" * 50)
        print(f"📊 Всего собрано вакансий: {len(vacancies)}")

        # Покажем несколько примеров
        if vacancies:
            print("\n📋 Примеры вакансий:")
            for i, v in enumerate(vacancies[:5], 1):
                print(f"   {i}. {v['title']} - {v['company']} ({v['city']})")

        print(f"\n📁 Сырые данные сохранены в: data/raw/")
        print(f"📝 Лог сохранен в: parser.log")

    except KeyboardInterrupt:
        print("\n\n⚠️ Парсинг прерван пользователем")
        return 1
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        return 1

    print("\n🎉 Готово!")
    return 0


if __name__ == "__main__":
    sys.exit(main())