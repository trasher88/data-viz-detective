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

    @staticmethod
    def get_top_companies(limit=10):
        """Топ компаний по количеству вакансий"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT company, COUNT(*) as cnt 
                FROM vacancies 
                WHERE company IS NOT NULL 
                GROUP BY company 
                ORDER BY cnt DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Ошибка топ компаний: {e}")
            return []

    @staticmethod
    def get_top_cities(limit=10):
        """Топ городов"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT city, COUNT(*) as cnt 
                FROM vacancies 
                WHERE city IS NOT NULL 
                GROUP BY city 
                ORDER BY cnt DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Ошибка топ городов: {e}")
            return []

    @staticmethod
    def get_top_skills(limit=15):
        """Топ навыков"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # В key_skills хранится JSON массив
            cursor.execute("""
                SELECT key_skills FROM vacancies 
                WHERE key_skills IS NOT NULL AND key_skills != '[]'
            """)
            rows = cursor.fetchall()
            conn.close()

            # Собираем частоту навыков
            from collections import Counter
            import json
            skill_counter = Counter()
            for (skills_json,) in rows:
                try:
                    skills = json.loads(skills_json)
                    for skill in skills:
                        skill_counter[skill] += 1
                except:
                    continue

            return skill_counter.most_common(limit)
        except Exception as e:
            logger.error(f"Ошибка топ навыков: {e}")
            return []

    @staticmethod
    def get_salary_by_city(city_name):
        """Средняя зарплата по городу"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG((salary_from + salary_to)/2) 
                FROM vacancies 
                WHERE city = ? AND salary_from IS NOT NULL AND salary_to IS NOT NULL
            """, (city_name,))
            avg_salary = cursor.fetchone()[0]
            conn.close()
            return int(avg_salary) if avg_salary else None
        except Exception as e:
            logger.error(f"Ошибка зарплаты по городу: {e}")
            return None

    @staticmethod
    def get_salary_by_level(level):
        """Средняя зарплата по уровню"""
        level_keywords = {
            'Junior': ['junior', 'начинающий', 'стажер'],
            'Middle': ['middle', 'мидл'],
            'Senior': ['senior', 'ведущий', 'главный']
        }

        keywords = level_keywords.get(level, [])
        if not keywords:
            return None

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Строим условие LIKE для каждого ключевого слова
            conditions = ' OR '.join(['title LIKE ?'] * len(keywords))
            params = [f'%{kw}%' for kw in keywords]

            cursor.execute(f"""
                SELECT AVG((salary_from + salary_to)/2) 
                FROM vacancies 
                WHERE ({conditions}) AND salary_from IS NOT NULL AND salary_to IS NOT NULL
            """, params)
            avg_salary = cursor.fetchone()[0]
            conn.close()
            return int(avg_salary) if avg_salary else None
        except Exception as e:
            logger.error(f"Ошибка зарплаты по уровню: {e}")
            return None

    @staticmethod
    def get_trends(days=30):
        """Динамика вакансий за N дней"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date(published_at), COUNT(*) 
                FROM vacancies 
                WHERE published_at >= date('now', ?)
                GROUP BY date(published_at)
                ORDER BY date(published_at)
            """, (f'-{days} days',))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Ошибка трендов: {e}")
            return []

    @staticmethod
    def search_vacancies(keyword, limit=5):
        """Поиск вакансий по ключевому слову"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, company, city, salary_from, salary_to, url 
                FROM vacancies 
                WHERE title LIKE ? OR description LIKE ?
                LIMIT ?
            """, (f'%{keyword}%', f'%{keyword}%', limit))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []