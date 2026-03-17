import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import DatabaseManager

# Настройка страницы
st.set_page_config(
    page_title="DataViz Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("🔍 DataViz Detective - Аналитик рынка вакансий")
st.markdown("*Анализ вакансий для Data-специалистов с hh.ru*")


# Инициализация базы данных
@st.cache_resource
def init_db():
    return DatabaseManager("data/vacancies.db")


db = init_db()


# Загрузка данных
@st.cache_data(ttl=600)  # Кэш на 10 минут
def load_data():
    """Загрузка данных из SQLite в pandas DataFrame"""
    import sqlite3

    conn = sqlite3.connect('data/vacancies.db')

    query = """
    SELECT 
        vacancy_id,
        title,
        company,
        city,
        salary_from,
        salary_to,
        salary_currency,
        key_skills,
        published_at,
        url
    FROM vacancies
    ORDER BY published_at DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return df

    # Преобразование даты
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['published_date'] = df['published_at'].dt.date
    df['published_month'] = df['published_at'].dt.to_period('M').astype(str)
    df['published_weekday'] = df['published_at'].dt.day_name()

    # Расчет средней зарплаты
    def calculate_mid_salary(row):
        if pd.notna(row['salary_from']) and pd.notna(row['salary_to']):
            return (row['salary_from'] + row['salary_to']) / 2
        elif pd.notna(row['salary_from']):
            return row['salary_from']
        elif pd.notna(row['salary_to']):
            return row['salary_to']
        return None

    df['salary_mid'] = df.apply(calculate_mid_salary, axis=1)

    # Конвертация в рубли (игнорируем другую валюту для простоты)
    df['salary_rub'] = df.apply(
        lambda row: row['salary_mid'] if row['salary_currency'] == 'RUR' else None,
        axis=1
    )

    # Парсинг навыков
    def parse_skills(skills_json):
        try:
            if skills_json and skills_json != 'null':
                return json.loads(skills_json)
            return []
        except:
            return []

    df['skills_list'] = df['key_skills'].apply(parse_skills)

    # Извлечение уровня из названия
    def extract_level(title):
        title_lower = str(title).lower()
        if any(word in title_lower for word in ['junior', 'начинающий', 'стажер']):
            return 'Junior'
        elif any(word in title_lower for word in ['senior', 'ведущий', 'главный']):
            return 'Senior'
        elif any(word in title_lower for word in ['middle', 'мидл']):
            return 'Middle'
        else:
            return 'Не указан'

    df['level'] = df['title'].apply(extract_level)

    # Категоризация по направлению
    def categorize_direction(title):
        title_lower = str(title).lower()

        if 'data analyst' in title_lower or 'дата аналитик' in title_lower:
            return 'Data Analyst'
        elif 'data scientist' in title_lower:
            return 'Data Scientist'
        elif 'data engineer' in title_lower or 'инженер данных' in title_lower:
            return 'Data Engineer'
        elif 'bi analyst' in title_lower or 'business intelligence' in title_lower:
            return 'BI Analyst'
        elif 'бизнес-аналитик' in title_lower or 'business analyst' in title_lower:
            return 'Бизнес-аналитик'
        elif 'продуктовый аналитик' in title_lower or 'product analyst' in title_lower:
            return 'Продуктовый аналитик'
        elif 'системный аналитик' in title_lower or 'system analyst' in title_lower:
            return 'Системный аналитик'
        elif 'ml инженер' in title_lower or 'ml engineer' in title_lower:
            return 'ML инженер'
        elif 'аналитик' in title_lower and len(title_lower.split()) < 3:  # Просто "Аналитик" без уточнений
            return 'Аналитик'
        else:
            return 'Другое'

    df['direction'] = df['title'].apply(categorize_direction)

    return df


# Загрузка данных
with st.spinner('Загрузка данных...'):
    df = load_data()

if df.empty:
    st.warning("📭 В базе данных нет вакансий. Сначала запустите парсер и загрузите данные.")
    st.stop()

# Боковая панель с фильтрами
with st.sidebar:
    st.header("🔧 Фильтры")

    # Фильтр по направлению
    directions = ['Все'] + sorted(df['direction'].unique().tolist())
    selected_direction = st.selectbox("Направление", directions)

    # Фильтр по уровню
    levels = ['Все'] + sorted(df['level'].unique().tolist())
    selected_level = st.selectbox("Уровень", levels)

    # Фильтр по дате
    min_date = df['published_date'].min()
    max_date = df['published_date'].max()

    # Фильтр по городу
    cities = ['Все'] + sorted(df['city'].dropna().unique().tolist())
    selected_city = st.selectbox("Город", cities)

    date_range = st.date_input(
        "Период",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Фильтр по зарплате
    if not df['salary_rub'].isna().all():
        salary_min = int(df['salary_rub'].min())
        salary_max = int(df['salary_rub'].max())

        salary_range = st.slider(
            "Зарплата (тыс. ₽)",
            min_value=salary_min // 1000,
            max_value=salary_max // 1000,
            value=(salary_min // 1000, salary_max // 1000),
            step=10
        )

    st.markdown("---")

    # Статистика
    stats = db.get_stats()
    st.metric("📊 Всего вакансий", f"{stats['total']:,}")
    st.metric("🏢 Компаний", f"{stats['companies']:,}")
    st.metric("🌍 Городов", f"{stats['cities']:,}")

    # Кнопка обновления
    if st.button("🔄 Обновить данные"):
        st.cache_data.clear()
        st.rerun()

# Применение фильтров
filtered_df = df.copy()

if selected_direction != 'Все':
    filtered_df = filtered_df[filtered_df['direction'] == selected_direction]

if selected_level != 'Все':
    filtered_df = filtered_df[filtered_df['level'] == selected_level]

if selected_city != 'Все':
    filtered_df = filtered_df[filtered_df['city'] == selected_city]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['published_date'] >= start_date) &
        (filtered_df['published_date'] <= end_date)
        ]

if not df['salary_rub'].isna().all():
    filtered_df = filtered_df[
        (filtered_df['salary_rub'] >= salary_range[0] * 1000) &
        (filtered_df['salary_rub'] <= salary_range[1] * 1000)
        ]

# Основные метрики
st.subheader("📊 Ключевые показатели")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "📊 Вакансий",
        f"{len(filtered_df):,}",
        delta=f"{len(filtered_df) - len(df):+}" if len(filtered_df) != len(df) else None
    )

with col2:
    avg_salary = filtered_df['salary_rub'].mean()
    st.metric(
        "💰 Средняя зарплата",
        f"{int(avg_salary):,} ₽" if pd.notna(avg_salary) else "Н/Д"
    )

with col3:
    unique_companies = filtered_df['company'].nunique()
    st.metric("🏢 Компаний", f"{unique_companies:,}")

with col4:
    # Показываем выбранный город или "Все города"
    if selected_city != 'Все':
        st.metric("🌍 Город", selected_city)
    else:
        st.metric("🌍 Городов", filtered_df['city'].nunique())

with col5:
    skills_total = filtered_df['skills_list'].str.len().sum()
    st.metric("🔧 Упоминаний навыков", f"{skills_total:,}")

st.markdown("---")

# Графики
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏢 Топ-20 компаний")
    company_counts = filtered_df['company'].value_counts().head(20).sort_values(ascending=True)
    if not company_counts.empty:
        fig_companies = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            labels={'x': 'Количество вакансий', 'y': ''},
            color=company_counts.values,
            color_continuous_scale='Blues'
        )
        fig_companies.update_layout(height=600)
        st.plotly_chart(fig_companies, use_container_width=True)

with col_right:
    st.subheader("🌍 Распределение по городам")
    city_counts = filtered_df['city'].value_counts().head(10)
    if not city_counts.empty:
        fig_cities = px.pie(
            values=city_counts.values,
            names=city_counts.index,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3,
            title=f"Топ-10 городов: {city_counts.sum()} вакансий"
        )
        # Проценты внутри, легенда сбоку
        fig_cities.update_traces(
            textposition='inside',
            textinfo='percent',
            textfont_size=10,
            insidetextorientation='radial'  # Текст по радиусу, не вылезает
        )
        fig_cities.update_layout(
            height=600,
            legend=dict(
                orientation='v',
                yanchor='middle',
                y=0.5,
                xanchor='left',
                x=1.05,
                font=dict(size=10)
            ),
            margin=dict(t=30, b=30, l=30, r=150)
        )
        st.plotly_chart(fig_cities, use_container_width=True)
    else:
        st.info("Нет данных по городам")

# Анализ зарплат
st.markdown("---")
st.subheader("💰 Анализ зарплат")

col_left, col_right = st.columns(2)

with col_left:
    # Распределение зарплат
    salary_data = filtered_df[filtered_df['salary_rub'].notna()]
    if not salary_data.empty:
        fig_salary = px.histogram(
            salary_data,
            x='salary_rub',
            nbins=40,
            title='Распределение зарплат',
            labels={'salary_rub': 'Зарплата (₽)', 'count': 'Количество вакансий'},
            color_discrete_sequence=['#2E86AB']
        )
        fig_salary.update_layout(height=400)
        st.plotly_chart(fig_salary, use_container_width=True)

with col_right:
    # Зарплаты по уровням
    salary_by_level = salary_data.groupby('level')['salary_rub'].agg(['mean', 'count', 'median']).reset_index()
    salary_by_level = salary_by_level[salary_by_level['count'] > 2]

    if not salary_by_level.empty:
        fig_salary_level = px.bar(
            salary_by_level,
            x='level',
            y='mean',
            title='Средняя зарплата по уровням',
            labels={'level': 'Уровень', 'mean': 'Средняя зарплата (₽)'},
            color='count',
            text_auto='.0f',
            color_continuous_scale='Viridis'
        )
        fig_salary_level.update_layout(height=400)
        st.plotly_chart(fig_salary_level, use_container_width=True)

# Анализ навыков
st.markdown("---")
st.subheader("🔧 Ключевые навыки")

# Собираем все навыки
all_skills = []
for skills in filtered_df['skills_list']:
    all_skills.extend(skills)

if all_skills:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        skills_df = pd.Series(all_skills).value_counts().head(20).sort_values(ascending=True).reset_index()
        skills_df.columns = ['skill', 'count']

        fig_skills = px.bar(
            skills_df,
            x='count',
            y='skill',
            orientation='h',
            title='Топ-20 требуемых навыков',
            labels={'count': 'Количество упоминаний', 'skill': ''},
            color='count',
            color_continuous_scale='Viridis'
        )
        fig_skills.update_layout(height=600)
        st.plotly_chart(fig_skills, use_container_width=True)

    with col_right:
        st.subheader("📊 Статистика навыков")
        st.metric("Уникальных навыков", len(skills_df))
        st.metric("Всего упоминаний", len(all_skills))

        st.subheader("🏆 Топ-5 навыков")
        top_5 = skills_df.sort_values('count', ascending=False).head(5)
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            st.markdown(f"**{i}. {row['skill']}** — {row['count']} 🏆")

# Динамика по времени
st.markdown("---")
st.subheader("📈 Динамика вакансий")

time_data = filtered_df.groupby('published_month').agg({
    'vacancy_id': 'count',
    'salary_rub': 'mean'
}).reset_index()

if not time_data.empty and len(time_data) > 1:
    fig_trends = go.Figure()

    fig_trends.add_trace(go.Scatter(
        x=time_data['published_month'],
        y=time_data['vacancy_id'],
        name='Количество вакансий',
        yaxis='y',
        line=dict(color='#2E86AB', width=3),
        mode='lines+markers'
    ))

    if not time_data['salary_rub'].isna().all():
        fig_trends.add_trace(go.Scatter(
            x=time_data['published_month'],
            y=time_data['salary_rub'],
            name='Средняя зарплата',
            yaxis='y2',
            line=dict(color='#A23B72', width=3),
            mode='lines+markers'
        ))

    fig_trends.update_layout(
        title='Динамика количества вакансий и зарплат',
        xaxis=dict(title='Месяц'),
        yaxis=dict(title='Количество вакансий', color='#2E86AB'),
        yaxis2=dict(
            title='Средняя зарплата (₽)',
            overlaying='y',
            side='right',
            color='#A23B72'
        ),
        height=500,
        hovermode='x unified',
        showlegend=True
    )

    st.plotly_chart(fig_trends, use_container_width=True)

# Таблица с последними вакансиями
st.markdown("---")
st.subheader("📋 Последние вакансии")

display_cols = ['title', 'company', 'city', 'salary_rub', 'published_date', 'url']
display_df = filtered_df[display_cols].head(20).copy()

# Форматирование для отображения
display_df['salary_rub'] = display_df['salary_rub'].apply(
    lambda x: f"{int(x):,} ₽" if pd.notna(x) else "Не указана"
)
display_df['published_date'] = pd.to_datetime(display_df['published_date'])
display_df['published_date'] = display_df['published_date'].dt.strftime('%d.%m.%Y')
display_df['url'] = display_df['url'].apply(
    lambda x: f'<a href="{x}" target="_blank">🔗 Ссылка</a>' if pd.notna(x) else ''
)

display_df.columns = ['Должность', 'Компания', 'Город', 'Зарплата', 'Дата', 'Ссылка']

st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<center>📊 DataViz Detective | Данные с hh.ru | Обновлено: {}</center>".format(
        datetime.now().strftime('%d.%m.%Y %H:%M')
    ),
    unsafe_allow_html=True
)