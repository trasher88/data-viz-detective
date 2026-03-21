import requests
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HHParser:
    """Парсер вакансий с hh.ru через официальное API"""

    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        # Добавить email, это хороший тон для API
        self.headers = {
            'User-Agent': 'DataVizDetective/1.0 (trasher6@mail.ru)'
        }
        logger.info("Инициализирован HHParser")

    def search_vacancies(self, text: str = "Data Analyst", area: int = 1, page: int = 0) -> Optional[Dict]:
        """
        Поиск вакансий через API hh.ru

        Args:
            text: Поисковый запрос
            area: 1 - Москва, 2 - СПб, 113 - Россия (можно расширить)
            page: Номер страницы (0-19)

        Returns:
            Dict с результатами или None при ошибке
        """
        params = {
            'text': text,
            'area': area,
            'page': page,
            'per_page': 100  # Максимум на одной странице
        }

        try:
            logger.info(f"Поиск: '{text}', страница {page}")
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            return None

    def get_vacancy_detail(self, vacancy_id: str) -> Optional[Dict]:
        """
        Получение детальной информации по конкретной вакансии

        Args:
            vacancy_id: ID вакансии с hh.ru
        """
        url = f"{self.base_url}/{vacancy_id}"

        try:
            logger.debug(f"Загрузка деталей вакансии {vacancy_id}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Ошибка загрузки вакансии {vacancy_id}: {e}")
            return None

    def extract_salary(self, salary_data: Optional[Dict]) -> tuple:
        """
        Извлечение зарплаты из ответа API

        Returns:
            (salary_from, salary_to, currency)
        """
        if not salary_data:
            return None, None, None

        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        currency = salary_data.get('currency')

        return salary_from, salary_to, currency

    def process_vacancy(self, item: Dict) -> Optional[Dict]:
        """
        Обработка одной вакансии (получение деталей и форматирование)
        """
        # Получаем детальную информацию
        detail = self.get_vacancy_detail(item['id'])
        if not detail:
            return None

        # Извлекаем зарплату
        salary_from, salary_to, currency = self.extract_salary(detail.get('salary'))

        # Извлекаем ключевые навыки
        skills = []
        if detail.get('key_skills'):
            skills = [skill['name'] for skill in detail['key_skills']]

        # Конвертируем published_at в правильный формат
        published_at = item['published_at']
        # Преобразуем '2026-03-21T12:24:15+0300' в '2026-03-21T12:24:15+03:00'
        if published_at and '+' in published_at:
            # Добавляем двоеточие в часовой пояс
            published_at = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', published_at)

        # Формируем структурированные данные
        vacancy_data = {
            'vacancy_id': item['id'],
            'title': item['name'],
            'company': item['employer']['name'] if item.get('employer') else None,
            'city': item['area']['name'] if item.get('area') else None,
            'salary_from': salary_from,
            'salary_to': salary_to,
            'salary_currency': currency,
            'description': detail.get('description'),
            'key_skills': json.dumps(skills, ensure_ascii=False),
            'published_at': published_at,
            'url': item['alternate_url']
        }

        return vacancy_data

    def run_parser(self, search_queries: List[str], max_pages: int = 5) -> List[Dict]:
        """
        Основной метод запуска парсера

        Args:
            search_queries: Список поисковых запросов
            max_pages: Сколько страниц парсить для каждого запроса

        Returns:
            Список обработанных вакансий
        """
        all_vacancies = []
        total_found = 0

        for query in search_queries:
            logger.info(f"\n=== Поиск по запросу: {query} ===")

            for page in range(max_pages):
                logger.info(f"Страница {page + 1}/{max_pages}")

                # Поиск вакансий
                search_result = self.search_vacancies(text=query, page=page)

                if not search_result:
                    logger.warning(f"Не удалось получить страницу {page}")
                    break

                # Общее количество найденных вакансий (для инфо)
                if page == 0:
                    found = search_result.get('found', 0)
                    total_found += found
                    logger.info(f"Всего найдено: {found} вакансий")

                # Обрабатываем каждую вакансию на странице
                items = search_result.get('items', [])
                if not items:
                    logger.info("Вакансий на странице нет")
                    break

                for item in items:
                    vacancy_data = self.process_vacancy(item)
                    if vacancy_data:
                        all_vacancies.append(vacancy_data)
                        self._save_raw_data(vacancy_data, item['id'])

                        # Маленькая задержка, чтобы не нагружать сервер
                        time.sleep(0.3)

                # Пауза между страницами
                time.sleep(0.5)

                # Проверяем, есть ли следующие страницы
                if page >= search_result.get('pages', 1) - 1:
                    break

            # Пауза между разными запросами
            time.sleep(1)

        logger.info(f"\n✅ Всего обработано: {len(all_vacancies)} вакансий")
        return all_vacancies

    def _save_raw_data(self, data: Dict, filename: str):
        """
        Сохранение сырых данных в JSON файл
        """
        try:
            # Создаем имя файла с датой
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"{date_str}_{filename}.json"
            filepath = f"data/raw/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Ошибка сохранения файла {filename}: {e}")