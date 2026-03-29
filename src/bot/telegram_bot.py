import logging
from datetime import datetime
import sqlite3
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'vacancies.db')


class Database:
    @staticmethod
    def get_stats():
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vacancies")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT company) FROM vacancies")
            companies = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT city) FROM vacancies")
            cities = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM vacancies WHERE salary_from IS NOT NULL")
            with_salary = cursor.fetchone()[0]
            conn.close()
            return {'total': total, 'companies': companies, 'cities': cities, 'with_salary': with_salary}
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return None

    @staticmethod
    def get_recent(limit=5):
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
            logger.error(f"Ошибка получения вакансий: {e}")
            return []