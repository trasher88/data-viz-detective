#!/usr/bin/env python
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import sqlite3

from src.bot.telegram_bot import Database

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
        "/stats — общая статистика\n"
        "/recent — последние 5 вакансий\n"
        "/top_companies [N] — топ N компаний\n"
        "/top_cities [N] — топ N городов\n"
        "/top_skills [N] — топ N навыков\n"
        "/salary_by_city [город] — средняя зарплата по городу\n"
        "/salary_by_level [Junior|Middle|Senior] — зарплата по уровню\n"
        "/trends — динамика за 30 дней\n"
        "/search [слово] — поиск вакансий\n"
        "/help — это сообщение",
        parse_mode='Markdown'
    )


async def help_command(update, context):
    await update.message.reply_text(
        "📋 *Доступные команды:*\n\n"
        "/stats — общая статистика\n"
        "/recent — последние 5 вакансий\n"
        "/top_companies [N] — топ N компаний\n"
        "/top_cities [N] — топ N городов\n"
        "/top_skills [N] — топ N навыков\n"
        "/salary_by_city [город] — средняя зарплата по городу\n"
        "/salary_by_level [Junior|Middle|Senior] — зарплата по уровню\n"
        "/trends — динамика за 30 дней\n"
        "/search [слово] — поиск вакансий\n"
        "/help — это сообщение",
        parse_mode='Markdown'
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


async def top_companies(update, context):
    """Топ компаний"""
    args = context.args
    limit = int(args[0]) if args and args[0].isdigit() else 10
    limit = min(limit, 20)  # Ограничим 20

    await update.message.reply_text(f"🔍 Загружаю топ-{limit} компаний...")
    rows = Database.get_top_companies(limit)

    if not rows:
        await update.message.reply_text("❌ Нет данных")
        return

    message = f"🏢 *Топ-{limit} компаний:*\n\n"
    for i, (company, count) in enumerate(rows, 1):
        message += f"{i}. {company} — {count} вакансий\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def top_cities(update, context):
    """Топ городов"""
    args = context.args
    limit = int(args[0]) if args and args[0].isdigit() else 10
    limit = min(limit, 20)

    await update.message.reply_text(f"🔍 Загружаю топ-{limit} городов...")
    rows = Database.get_top_cities(limit)

    if not rows:
        await update.message.reply_text("❌ Нет данных")
        return

    message = f"🌍 *Топ-{limit} городов:*\n\n"
    for i, (city, count) in enumerate(rows, 1):
        message += f"{i}. {city} — {count} вакансий\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def top_skills(update, context):
    """Топ навыков"""
    args = context.args
    limit = int(args[0]) if args and args[0].isdigit() else 15
    limit = min(limit, 30)

    await update.message.reply_text(f"🔍 Загружаю топ-{limit} навыков...")
    rows = Database.get_top_skills(limit)

    if not rows:
        await update.message.reply_text("❌ Нет данных")
        return

    message = f"🔧 *Топ-{limit} навыков:*\n\n"
    for i, (skill, count) in enumerate(rows, 1):
        message += f"{i}. {skill} — {count} упоминаний\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def salary_by_city(update, context):
    """Зарплата по городу"""
    if not context.args:
        await update.message.reply_text("❌ Укажите город: `/salary_by_city Москва`", parse_mode='Markdown')
        return

    city = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Ищу зарплаты в {city}...")

    avg = Database.get_salary_by_city(city)
    if not avg:
        await update.message.reply_text(f"❌ Нет данных по городу {city}")
        return

    await update.message.reply_text(f"💰 *Средняя зарплата в {city}:* {avg:,} ₽", parse_mode='Markdown')


async def salary_by_level(update, context):
    """Зарплата по уровню"""
    if not context.args:
        await update.message.reply_text("❌ Укажите уровень: `/salary_by_level Junior` (Junior/Middle/Senior)",
                                        parse_mode='Markdown')
        return

    level = context.args[0].capitalize()
    if level not in ['Junior', 'Middle', 'Senior']:
        await update.message.reply_text("❌ Уровень должен быть: Junior, Middle или Senior")
        return

    await update.message.reply_text(f"🔍 Ищу зарплаты для уровня {level}...")

    avg = Database.get_salary_by_level(level)
    if not avg:
        await update.message.reply_text(f"❌ Нет данных для уровня {level}")
        return

    await update.message.reply_text(f"💰 *Средняя зарплата {level}:* {avg:,} ₽", parse_mode='Markdown')


async def trends(update, context):
    """Динамика за 30 дней"""
    await update.message.reply_text("📈 Загружаю динамику за 30 дней...")
    rows = Database.get_trends(30)

    if not rows:
        await update.message.reply_text("❌ Нет данных")
        return

    # Берём последние 10 дней для краткости
    rows = rows[-10:]

    message = "📊 *Динамика вакансий (последние 10 дней):*\n\n"
    for date, count in rows:
        message += f"• {date}: {count} вакансий\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def search(update, context):
    """Поиск вакансий"""
    if not context.args:
        await update.message.reply_text("❌ Укажите слово для поиска: `/search Python`", parse_mode='Markdown')
        return

    keyword = ' '.join(context.args)
    await update.message.reply_text(f"🔍 Ищу вакансии по слову '{keyword}'...")

    rows = Database.search_vacancies(keyword, 5)
    if not rows:
        await update.message.reply_text(f"❌ Ничего не найдено по '{keyword}'")
        return

    message = f"📋 *Результаты поиска по '{keyword}':*\n\n"
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
    app.add_handler(CommandHandler("top_companies", top_companies))
    app.add_handler(CommandHandler("top_cities", top_cities))
    app.add_handler(CommandHandler("top_skills", top_skills))
    app.add_handler(CommandHandler("salary_by_city", salary_by_city))
    app.add_handler(CommandHandler("salary_by_level", salary_by_level))
    app.add_handler(CommandHandler("trends", trends))
    app.add_handler(CommandHandler("search", search))

    print("✅ Бот запущен! Напиши /start в Telegram")
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")