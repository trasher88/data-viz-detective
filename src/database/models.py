from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Vacancy(Base):
    """Модель вакансии для SQLAlchemy"""

    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True)
    vacancy_id = Column(String(50), unique=True, index=True)  # ID с hh.ru
    title = Column(String(200), index=True)  # Название вакансии
    company = Column(String(200), index=True)  # Компания
    city = Column(String(100), index=True)  # Город
    salary_from = Column(Float, nullable=True)  # Зарплата от
    salary_to = Column(Float, nullable=True)  # Зарплата до
    salary_currency = Column(String(10))  # Валюта
    description = Column(Text)  # Полное описание
    key_skills = Column(Text)  # JSON со списком навыков
    published_at = Column(DateTime, index=True)  # Дата публикации
    parsed_at = Column(DateTime, default=datetime.now)  # Когда спарсили
    url = Column(String(500))  # Ссылка на вакансию

    def __repr__(self):
        return f"<Vacancy {self.title} at {self.company}>"

    def to_dict(self):
        """Конвертация в словарь (удобно для JSON)"""
        return {
            'id': self.id,
            'vacancy_id': self.vacancy_id,
            'title': self.title,
            'company': self.company,
            'city': self.city,
            'salary_from': self.salary_from,
            'salary_to': self.salary_to,
            'salary_currency': self.salary_currency,
            'key_skills': self.key_skills,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'url': self.url
        }