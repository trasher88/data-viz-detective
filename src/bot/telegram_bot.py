import telegram
import asyncio
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not self.token or not self.chat_id:
            logger.warning("Telebot не настроен: нет токена или chat_id")
            self.bot = None
        else:
            self.bot = telegram.Bot(token=self.token)

    async def send_message(self, text):
        """Отправка сообщения"""
        if not self.bot:
            logger.info(f"[TELEGRAM] {text}")
            return

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
            logger.info("Сообщение отправлено в Telegram")
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")

    def send_sync(self, text):
        """Синхронная обертка для отправки"""
        if not self.bot:
            print(f"[TELEGRAM] {text}")
            return

        try:
            asyncio.run(self.send_message(text))
        except RuntimeError:
            # Если уже есть цикл событий
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_message(text))

    def format_stats(self, stats, new_count):
        """Форматирование статистики для отправки"""
        today = datetime.now().strftime('%d.%m.%Y')

        message = f"""
🤖 *DataViz Detective - Ежедневный отчет*
📅 {today}

✅ *Добавлено новых:* {new_count} вакансий

📊 *Общая статистика:*
• Всего вакансий: {stats['total']}
• Компаний: {stats['companies']}

🔗 Дашборд: http://109.73.202.131:8502
        """
        return message