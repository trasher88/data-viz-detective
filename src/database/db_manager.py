import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from .models import Base, Vacancy

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных SQLite"""

    def __init__(self, db_path: str = "data/vacancies.db"):
        """
        Инициализация подключения к SQLite

        Args:
            db_path: Путь к файлу базы данных
        """
        # Создаем папку data, если её нет
        os.makedirs('data', exist_ok=True)

        # SQLite connection string
        db_url = f"sqlite:///{db_path}"

        # Для SQLite важно добавить check_same_thread=False для Streamlit
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False  # Поставь True, если хочешь видеть все SQL запросы
        )

        # Создаем таблицы
        Base.metadata.create_all(self.engine)

        # Создаем фабрику сессий
        self.Session = sessionmaker(bind=self.engine)

        logger.info(f"✅ Database initialized at {db_path}")

    def save_vacancy(self, vacancy_data: Dict) -> bool:
        """
        Сохранение одной вакансии в БД

        Returns:
            True если сохранено, False если уже существует
        """
        session = self.Session()
        try:
            # Проверяем, есть ли уже такая вакансия
            existing = session.query(Vacancy).filter_by(
                vacancy_id=vacancy_data['vacancy_id']
            ).first()

            if not existing:
                vacancy = Vacancy(**vacancy_data)
                session.add(vacancy)
                session.commit()
                return True
            return False

        except IntegrityError:
            session.rollback()
            logger.warning(f"Vacancy {vacancy_data['vacancy_id']} already exists")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving vacancy: {e}")
            return False
        finally:
            session.close()

    def save_vacancies_bulk(self, vacancies_data: List[Dict]) -> tuple:
        """
        Массовое сохранение вакансий

        Returns:
            (saved_count, skipped_count)
        """
        session = self.Session()
        saved = 0
        skipped = 0

        try:
            for data in vacancies_data:
                # Проверяем, есть ли уже такая вакансия
                existing = session.query(Vacancy).filter_by(
                    vacancy_id=data['vacancy_id']
                ).first()

                if not existing:
                    # Конвертируем published_at в datetime если нужно
                    if isinstance(data.get('published_at'), str):
                        data['published_at'] = datetime.fromisoformat(
                            data['published_at'].replace('Z', '+00:00')
                        )

                    vacancy = Vacancy(**data)
                    session.add(vacancy)
                    saved += 1
                else:
                    skipped += 1

            session.commit()
            logger.info(f"Bulk save: {saved} saved, {skipped} skipped")
            return saved, skipped

        except Exception as e:
            session.rollback()
            logger.error(f"Error in bulk save: {e}")
            return 0, 0
        finally:
            session.close()

    def load_json_to_db(self, json_dir: str = "data/raw") -> tuple:
        """
        Загрузка всех JSON файлов из папки в базу данных

        Returns:
            (total_files, total_saved, total_skipped)
        """
        import glob

        json_files = glob.glob(f"{json_dir}/*.json")
        logger.info(f"Found {len(json_files)} JSON files")

        total_saved = 0
        total_skipped = 0

        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Конвертируем published_at в datetime
                if data.get('published_at'):
                    data['published_at'] = datetime.fromisoformat(
                        data['published_at'].replace('Z', '+00:00')
                    )

                saved, skipped = self.save_vacancies_bulk([data])
                total_saved += saved
                total_skipped += skipped

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

        logger.info(f"✅ Loaded {total_saved} vacancies to DB ({total_skipped} duplicates)")
        return len(json_files), total_saved, total_skipped

    def get_stats(self) -> Dict:
        """Получение общей статистики"""
        session = self.Session()
        try:
            stats = {
                'total': session.query(Vacancy).count(),
                'companies': session.query(Vacancy.company).distinct().count(),
                'cities': session.query(Vacancy.city).distinct().count(),
                'with_salary': session.query(Vacancy).filter(
                    Vacancy.salary_from.isnot(None)
                ).count(),
                'avg_salary': session.query(func.avg(Vacancy.salary_from)).scalar() or 0
            }
            return stats
        finally:
            session.close()

    def get_recent_vacancies(self, limit: int = 100) -> list[type[Vacancy]]:
        """Получение последних вакансий"""
        session = self.Session()
        try:
            return session.query(Vacancy).order_by(Vacancy.published_at.desc()).limit(limit).all()
        finally:
            session.close()

    def search_vacancies(self,
                         title_contains: str = None,
                         city: str = None,
                         company: str = None,
                         salary_min: float = None,
                         limit: int = 100) -> list[type[Vacancy]]:
        """Поиск вакансий с фильтрами"""
        session = self.Session()
        try:
            query = session.query(Vacancy)

            if title_contains:
                query = query.filter(Vacancy.title.contains(title_contains))
            if city:
                query = query.filter(Vacancy.city == city)
            if company:
                query = query.filter(Vacancy.company.contains(company))
            if salary_min:
                query = query.filter(
                    or_(
                        Vacancy.salary_from >= salary_min,
                        Vacancy.salary_to >= salary_min
                    )
                )

            return query.order_by(Vacancy.published_at.desc()).limit(limit).all()
        finally:
            session.close()