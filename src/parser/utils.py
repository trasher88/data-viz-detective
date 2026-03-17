import json
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


def load_raw_vacancies(date_str: str = None) -> List[Dict]:
    """
    Загрузка сырых вакансий из JSON файлов за указанную дату

    Args:
        date_str: Дата в формате YYYYMMDD (если None - сегодня)
    """
    import glob

    if date_str is None:
        date_str = datetime.now().strftime('%Y%m%d')

    pattern = f"data/raw/{date_str}_*.json"
    files = glob.glob(pattern)

    vacancies = []
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                vacancies.append(data)
        except Exception as e:
            logger.error(f"Ошибка загрузки {filepath}: {e}")

    logger.info(f"Загружено {len(vacancies)} вакансий из {len(files)} файлов")
    return vacancies


def clean_old_files(days: int = 7):
    """
    Удаление старых JSON файлов (чтобы не забивали диск)

    Args:
        days: Удалять файлы старше N дней
    """
    import os
    import time

    now = time.time()
    cutoff = now - (days * 86400)  # 86400 секунд в дне

    for filename in os.listdir('data/raw'):
        filepath = os.path.join('data/raw', filename)
        if os.path.isfile(filepath):
            file_modified = os.path.getmtime(filepath)
            if file_modified < cutoff:
                os.remove(filepath)
                logger.info(f"Удален старый файл: {filename}")