#!/usr/bin/env python
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import sqlite3

# Загружаем токен
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env")
    sys.exit(1)

from telegram.ext import Application, CommandHandler
from telegram.request import HTTPXRequest

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = 'data/vacancies.db'


def get_stats():
    """Получить статистику из базы"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vacancies")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT company) FROM vacancies")
        companies = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT city) FROM vacancies")
        cities = cursor.fetchone()[0]
        conn.close()
        return {'total': total, 'companies': companies, 'cities': cities}
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        return None


def get_recent(limit=5):
    """Получить последние вакансии"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, company, city, salary_from, salary_to, url 
            FROM vacancies 
            ORDER BY published_at DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        return []


# Обработчики команд
async def start(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я бот DataViz Detective.\n"
        f"Доступные команды:\n"
        f"/stats - статистика\n"
        f"/recent - последние 5 вакансий\n"
        f"/help - помощь"
    )


async def help_command(update, context):
    await update.message.reply_text(
        "📋 Команды:\n"
        "/stats - общая статистика\n"
        "/recent - последние 5 вакансий\n"
        "/help - это сообщение"
    )


async def stats(update, context):
    await update.message.reply_text("🔍 Получаю статистику...")
    stats = get_stats()
    if not stats:
        await update.message.reply_text("❌ Ошибка получения статистики")
        return
    message = (
        f"📊 *Статистика вакансий*\n\n"
        f"• Всего: {stats['total']}\n"
        f"• Компаний: {stats['companies']}\n"
        f"• Городов: {stats['cities']}\n\n"
        f"🔗 [Дашборд](http://localhost:8502)"
    )
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def recent(update, context):
    await update.message.reply_text("🔍 Загружаю последние вакансии...")
    rows = get_recent(5)
    if not rows:
        await update.message.reply_text("❌ Нет данных")
        return
    message = "📋 *Последние 5 вакансий:*\n\n"
    for i, (title, company, city, salary_from, salary_to, url) in enumerate(rows, 1):
        salary = f"{salary_from} - {salary_to}" if salary_from or salary_to else "не указана"
        message += f"{i}. *{title}*\n   • {company}\n   • {city}\n   • Зарплата: {salary}\n\n"
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


def main():
    print("🚀 Запуск Telegram-бота...")

    # Создаём приложение с увеличенными таймаутами
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(TOKEN).request(request).build()

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("recent", recent))

    print("✅ Бот запущен! Напиши /start в Telegram")
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")