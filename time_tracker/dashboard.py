import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database.engine import get_session, close_session
from database.models import TimeEntry
from datetime import datetime, timedelta
import numpy as np

# Настройка страницы
st.set_page_config(
    page_title="Трекер времени",
    page_icon="⏰",
    layout="wide"
)

# Автоматическое обновление каждые 30 секунд
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Проверяем, нужно ли обновить данные
if (datetime.now() - st.session_state.last_refresh).seconds > 30:
    st.cache_data.clear()
    st.session_state.last_refresh = datetime.now()

@st.cache_data(ttl=30)  # Кэш на 30 секунд для автоматического обновления
def load_data():
    """Загружает данные из базы данных и кэширует их"""
    session = get_session()
    try:
        entries = session.query(TimeEntry).all()
        data = []
        for entry in entries:
            data.append({
                'id': entry.id,
                'user_id': entry.user_id,
                'activity_name': entry.activity_name,
                'category': entry.category.value,
                'duration_minutes': entry.duration_minutes,
                'entry_date': entry.entry_date
            })
        df = pd.DataFrame(data)
        if not df.empty and 'entry_date' in df.columns:
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            # Добавляем дополнительные колонки для анализа
            df['date'] = df['entry_date'].dt.date
            df['hour'] = df['entry_date'].dt.hour
            df['day_of_week'] = df['entry_date'].dt.day_name()
            df['week'] = df['entry_date'].dt.isocalendar().week
            df['month'] = df['entry_date'].dt.month
            df['year'] = df['entry_date'].dt.year
        return df
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()
    finally:
        close_session(session)

def format_duration(minutes):
    """Форматирует время в читаемый вид"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}ч {mins}мин"
    else:
        return f"{mins}мин"

def show_general_statistics(df):
    """Показывает общую статистику"""
    st.header("📊 Общая статистика")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_time = df['duration_minutes'].sum()
        time_str = format_duration(total_time)
        st.metric("Общее время", time_str)
    
    with col2:
        st.metric("Всего записей", len(df))
    
    with col3:
        st.metric("Уникальных задач", df['activity_name'].nunique())
    
    with col4:
        avg_time = df['duration_minutes'].mean()
        st.metric("Среднее время", f"{avg_time:.1f} мин")
    
    # Дополнительные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        max_time = df['duration_minutes'].max()
        st.metric("Максимальная сессия", format_duration(max_time))
    
    with col2:
        min_time = df['duration_minutes'].min()
        st.metric("Минимальная сессия", format_duration(min_time))
    
    with col3:
        total_days = df['date'].nunique()
        st.metric("Дней активности", total_days)
    
    with col4:
        if total_days > 0:
            avg_daily = total_time / total_days
            st.metric("Среднее в день", format_duration(int(avg_daily)))
        else:
            st.metric("Среднее в день", "0мин")

def show_category_analysis(df):
    """Показывает анализ по категориям"""
    st.header("📂 Анализ по категориям")
    
    # Группировка по категориям
    category_summary = df.groupby('category').agg({
        'duration_minutes': ['sum', 'count', 'mean', 'max', 'min'],
        'date': 'nunique'
    }).round(1)
    
    category_summary.columns = ['Общее время (мин)', 'Количество записей', 'Среднее время (мин)', 'Макс время (мин)', 'Мин время (мин)', 'Дней активности']
    category_summary = category_summary.sort_values('Общее время (мин)', ascending=False)
    
    # Форматируем время
    category_summary['Общее время'] = category_summary['Общее время (мин)'].apply(format_duration)
    category_summary['Среднее время'] = category_summary['Среднее время (мин)'].apply(lambda x: format_duration(int(x)))
    category_summary['Макс время'] = category_summary['Макс время (мин)'].apply(format_duration)
    category_summary['Мин время'] = category_summary['Мин время (мин)'].apply(format_duration)
    
    # Добавляем эмодзи к названиям категорий
    category_emoji = {
        'work': '💼',
        'study': '📚',
        'rest': '😴'
    }
    
    category_summary['Категория'] = category_summary.index.map(lambda x: f"{category_emoji.get(x, '📊')} {x.upper()}")
    
    # Отображаем таблицу
    st.subheader("📋 Детальная статистика по категориям")
    display_cols = ['Категория', 'Общее время', 'Количество записей', 'Среднее время', 'Макс время', 'Мин время', 'Дней активности']
    st.dataframe(category_summary[display_cols], use_container_width=True)
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📂 Распределение времени по категориям")
        if not category_summary.empty:
            fig_pie = px.pie(
                category_summary.reset_index(),
                values='Общее время (мин)',
                names='category',
                title="Распределение времени по категориям",
                color_discrete_map={
                    'work': '#FF6B6B',
                    'study': '#4ECDC4', 
                    'rest': '#45B7D1'
                }
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Нет данных для отображения круговой диаграммы")
    
    with col2:
        st.subheader("📊 Количество записей по категориям")
        if not category_summary.empty:
            fig_bar = px.bar(
                category_summary.reset_index(),
                x='category',
                y='Количество записей',
                title="Количество записей по категориям",
                color='category',
                color_discrete_map={
                    'work': '#FF6B6B',
                    'study': '#4ECDC4',
                    'rest': '#45B7D1'
                }
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Нет данных для отображения столбчатой диаграммы")
    
    # Анализ баланса
    st.subheader("⚖️ Анализ баланса времени")
    
    if not category_summary.empty:
        total_time = category_summary['Общее время (мин)'].sum()
        
        col1, col2, col3 = st.columns(3)
        
        for i, (category, row) in enumerate(category_summary.iterrows()):
            with [col1, col2, col3][i]:
                percentage = (row['Общее время (мин)'] / total_time) * 100
                emoji = category_emoji.get(category, '📊')
                
                st.metric(
                    f"{emoji} {category.upper()}",
                    row['Общее время'],
                    f"{percentage:.1f}% от общего времени"
                )

def show_activity_analysis(df):
    """Показывает анализ по задачам"""
    st.header("🍰 Анализ по задачам")
    
    # Группировка по задачам
    activity_summary = df.groupby('activity_name').agg({
        'duration_minutes': ['sum', 'count', 'mean', 'max', 'min'],
        'date': 'nunique'
    }).round(1)
    
    activity_summary.columns = ['Общее время (мин)', 'Количество записей', 'Среднее время (мин)', 'Макс время (мин)', 'Мин время (мин)', 'Дней активности']
    activity_summary = activity_summary.sort_values('Общее время (мин)', ascending=False)
    
    # Форматируем время
    activity_summary['Общее время'] = activity_summary['Общее время (мин)'].apply(format_duration)
    activity_summary['Среднее время'] = activity_summary['Среднее время (мин)'].apply(lambda x: format_duration(int(x)))
    activity_summary['Макс время'] = activity_summary['Макс время (мин)'].apply(format_duration)
    activity_summary['Мин время'] = activity_summary['Мин время (мин)'].apply(format_duration)
    
    # Отображаем таблицу
    st.subheader("📋 Детальная статистика по задачам")
    display_cols = ['Общее время', 'Количество записей', 'Среднее время', 'Макс время', 'Мин время', 'Дней активности']
    st.dataframe(activity_summary[display_cols], use_container_width=True)
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🍰 Распределение времени")
        if not activity_summary.empty:
            fig_pie = px.pie(
                activity_summary.reset_index(),
                values='Общее время (мин)',
                names='activity_name',
                title="Распределение времени по задачам"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Нет данных для отображения круговой диаграммы")
    
    with col2:
        st.subheader("📊 Количество записей по задачам")
        if not activity_summary.empty:
            fig_bar = px.bar(
                activity_summary.reset_index(),
                x='activity_name',
                y='Количество записей',
                title="Количество записей по задачам"
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Нет данных для отображения столбчатой диаграммы")

def show_time_analysis(df):
    """Показывает анализ по времени"""
    st.header("⏰ Анализ по времени")
    
    # Анализ по дням недели
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Активность по дням недели")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_names_ru = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        
        daily_summary = df.groupby('day_of_week')['duration_minutes'].sum().reset_index()
        if not daily_summary.empty:
            daily_summary['day_of_week'] = pd.Categorical(daily_summary['day_of_week'], categories=day_order, ordered=True)
            daily_summary = daily_summary.sort_values('day_of_week')
            
            # Заменяем английские названия на русские
            day_mapping = dict(zip(day_order, day_names_ru))
            daily_summary['День недели'] = daily_summary['day_of_week'].map(day_mapping)
            
            fig_day = px.bar(
                daily_summary,
                x='День недели',
                y='duration_minutes',
                title="Время по дням недели",
                labels={'duration_minutes': 'Время (минуты)'}
            )
            st.plotly_chart(fig_day, use_container_width=True)
        else:
            st.info("Нет данных для отображения графика по дням недели")
    
    with col2:
        st.subheader("🕐 Активность по часам")
        hourly_summary = df.groupby('hour')['duration_minutes'].sum().reset_index()
        
        if not hourly_summary.empty:
            fig_hour = px.bar(
                hourly_summary,
                x='hour',
                y='duration_minutes',
                title="Время по часам дня",
                labels={'hour': 'Час', 'duration_minutes': 'Время (минуты)'}
            )
            fig_hour.update_xaxes(tickmode='linear', tick0=0, dtick=1)
            st.plotly_chart(fig_hour, use_container_width=True)
        else:
            st.info("Нет данных для отображения графика по часам")
    
    # Анализ по дням
    st.subheader("📈 Продуктивность по дням")
    
    daily_time = df.groupby('date')['duration_minutes'].sum().reset_index()
    daily_time['date'] = pd.to_datetime(daily_time['date'])
    daily_time = daily_time.sort_values('date')
    
    if not daily_time.empty:
        fig_daily = px.line(
            daily_time,
            x='date',
            y='duration_minutes',
            title="Тренд продуктивности по дням",
            labels={'duration_minutes': 'Время (минуты)', 'date': 'Дата'}
        )
        fig_daily.update_layout(xaxis_tickformat='%d.%m.%Y')
        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("Нет данных для отображения тренда по дням")
    
    # Тепловая карта активности
    st.subheader("🔥 Тепловая карта активности")
    
    # Создаем сводную таблицу: дни недели vs часы
    df_pivot = df.groupby(['day_of_week', 'hour'])['duration_minutes'].sum().reset_index()
    
    if not df_pivot.empty:
        df_pivot['day_of_week'] = pd.Categorical(df_pivot['day_of_week'], categories=day_order, ordered=True)
        df_pivot = df_pivot.sort_values(['day_of_week', 'hour'])
        
        # Создаем матрицу для тепловой карты
        heatmap_data = df_pivot.pivot(index='day_of_week', columns='hour', values='duration_minutes').fillna(0)
        heatmap_data.index = [day_mapping[day] for day in heatmap_data.index]
        
        fig_heatmap = px.imshow(
            heatmap_data,
            title="Тепловая карта: Дни недели × Часы дня",
            labels=dict(x="Час дня", y="День недели", color="Время (минуты)"),
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Нет данных для отображения тепловой карты")

def show_detailed_data(df):
    """Показывает детализированные данные"""
    st.header("📋 Детализированные данные")
    
    # Фильтры для таблицы
    col1, col2 = st.columns(2)
    
    with col1:
        sort_by = st.selectbox(
            "Сортировка по:",
            ['Дата (новые)', 'Дата (старые)', 'Время (больше)', 'Время (меньше)', 'Задача']
        )
    
    with col2:
        show_count = st.slider("Количество записей:", 10, 100, 50)
    
    # Сортируем данные
    display_df = df.copy()
    if sort_by == 'Дата (новые)':
        display_df = display_df.sort_values('entry_date', ascending=False)
    elif sort_by == 'Дата (старые)':
        display_df = display_df.sort_values('entry_date', ascending=True)
    elif sort_by == 'Время (больше)':
        display_df = display_df.sort_values('duration_minutes', ascending=False)
    elif sort_by == 'Время (меньше)':
        display_df = display_df.sort_values('duration_minutes', ascending=True)
    elif sort_by == 'Задача':
        display_df = display_df.sort_values('activity_name')
    
    # Форматируем данные
    display_df['entry_date'] = display_df['entry_date'].dt.strftime('%d.%m.%Y %H:%M')
    display_df['duration_formatted'] = display_df['duration_minutes'].apply(format_duration)
    display_df['day_of_week'] = display_df['day_of_week'].map({
        'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср', 'Thursday': 'Чт',
        'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
    })
    
    # Переименовываем колонки
    display_df = display_df.rename(columns={
        'id': 'ID',
        'activity_name': 'Задача',
        'category': 'Категория',
        'duration_minutes': 'Время (мин)',
        'duration_formatted': 'Время',
        'entry_date': 'Дата и время',
        'day_of_week': 'День недели',
        'hour': 'Час'
    })
    
    # Отображаем таблицу
    columns_to_show = ['ID', 'Задача', 'Категория', 'Время', 'Дата и время', 'День недели', 'Час']
    st.dataframe(display_df[columns_to_show].head(show_count), use_container_width=True)
    
    # Экспорт данных
    st.subheader("💾 Экспорт данных")
    csv = display_df[columns_to_show].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Скачать CSV",
        data=csv,
        file_name=f"time_tracker_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def show_time_by_categories(df):
    """Показывает анализ времени по категориям"""
    st.header("🕐 Анализ времени по категориям")
    
    if df.empty:
        st.info("Нет данных для анализа времени по категориям")
        return
    
    # Группировка по категориям и времени дня
    df['hour_group'] = pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], labels=['Ночь (0-6)', 'Утро (6-12)', 'День (12-18)', 'Вечер (18-24)'])
    
    # Анализ по времени дня для каждой категории
    st.subheader("⏰ Распределение времени по категориям и времени дня")
    
    category_time_analysis = df.groupby(['category', 'hour_group'], observed=True).agg({
        'duration_minutes': ['sum', 'count', 'mean']
    }).round(1)
    
    category_time_analysis.columns = ['Общее время (мин)', 'Количество записей', 'Среднее время (мин)']
    category_time_analysis = category_time_analysis.reset_index()
    
    # Создаем тепловую карту
    pivot_data = category_time_analysis.pivot(index='category', columns='hour_group', values='Общее время (мин)').fillna(0)
    
    fig_heatmap = px.imshow(
        pivot_data,
        title="Тепловая карта активности по категориям и времени дня",
        color_continuous_scale='Viridis',
        aspect='auto'
    )
    fig_heatmap.update_layout(
        xaxis_title="Время дня",
        yaxis_title="Категория"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Детальная таблица
    st.subheader("📋 Детальная статистика по времени дня")
    
    # Добавляем эмодзи к категориям
    category_emoji = {
        'work': '💼',
        'study': '📚',
        'rest': '😴'
    }
    
    category_time_analysis['Категория'] = category_time_analysis['category'].map(
        lambda x: f"{category_emoji.get(x, '📊')} {x.upper()}"
    )
    
    # Форматируем время
    category_time_analysis['Общее время'] = category_time_analysis['Общее время (мин)'].apply(format_duration)
    category_time_analysis['Среднее время'] = category_time_analysis['Среднее время (мин)'].apply(
        lambda x: format_duration(int(x)) if pd.notna(x) else "0мин"
    )
    
    display_cols = ['Категория', 'hour_group', 'Общее время', 'Количество записей', 'Среднее время']
    st.dataframe(category_time_analysis[display_cols], use_container_width=True)
    
    # Анализ по дням недели для каждой категории
    st.subheader("📅 Активность по дням недели")
    
    weekday_analysis = df.groupby(['category', 'day_of_week']).agg({
        'duration_minutes': ['sum', 'count']
    }).round(1)
    
    weekday_analysis.columns = ['Общее время (мин)', 'Количество записей']
    weekday_analysis = weekday_analysis.reset_index()
    
    # Создаем график
    fig_weekday = px.bar(
        weekday_analysis,
        x='day_of_week',
        y='Общее время (мин)',
        color='category',
        title="Активность по дням недели",
        barmode='group',
        color_discrete_map={
            'work': '#FF6B6B',
            'study': '#4ECDC4',
            'rest': '#45B7D1'
        }
    )
    fig_weekday.update_layout(
        xaxis_title="День недели",
        yaxis_title="Время (минуты)"
    )
    st.plotly_chart(fig_weekday, use_container_width=True)
    
    # Анализ по часам для каждой категории
    st.subheader("🕐 Распределение по часам дня")
    
    hourly_analysis = df.groupby(['category', 'hour']).agg({
        'duration_minutes': ['sum', 'count']
    }).round(1)
    
    hourly_analysis.columns = ['Общее время (мин)', 'Количество записей']
    hourly_analysis = hourly_analysis.reset_index()
    
    # Создаем график
    fig_hourly = px.line(
        hourly_analysis,
        x='hour',
        y='Общее время (мин)',
        color='category',
        title="Распределение активности по часам дня",
        markers=True,
        color_discrete_map={
            'work': '#FF6B6B',
            'study': '#4ECDC4',
            'rest': '#45B7D1'
        }
    )
    fig_hourly.update_layout(
        xaxis_title="Час дня",
        yaxis_title="Время (минуты)",
        xaxis=dict(tickmode='linear', tick0=0, dtick=1)
    )
    st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Статистика по категориям
    st.subheader("📊 Сводная статистика по категориям")
    
    col1, col2, col3 = st.columns(3)
    
    for i, category in enumerate(['work', 'study', 'rest']):
        with [col1, col2, col3][i]:
            category_data = df[df['category'] == category]
            if not category_data.empty:
                total_time = category_data['duration_minutes'].sum()
                avg_time = category_data['duration_minutes'].mean()
                peak_hour = category_data.groupby('hour')['duration_minutes'].sum().idxmax()
                
                emoji = category_emoji.get(category, '📊')
                st.metric(
                    f"{emoji} {category.upper()}",
                    format_duration(total_time),
                    f"Пик: {peak_hour}:00"
                )
            else:
                emoji = category_emoji.get(category, '📊')
                st.metric(f"{emoji} {category.upper()}", "0мин", "Нет данных")

def show_trends_analysis(df):
    """Показывает анализ трендов"""
    st.header("📈 Анализ трендов")
    
    if df.empty:
        st.info("Нет данных для анализа трендов")
        return
    
    # Группировка по дням
    daily_stats = df.groupby('date').agg({
        'duration_minutes': ['sum', 'count', 'mean']
    }).round(1)
    
    daily_stats.columns = ['Общее время (мин)', 'Количество записей', 'Среднее время (мин)']
    daily_stats = daily_stats.reset_index()
    
    # График общего времени по дням
    st.subheader("📊 Общее время по дням")
    fig_time = px.line(
        daily_stats,
        x='date',
        y='Общее время (мин)',
        title="Динамика общего времени по дням",
        markers=True
    )
    fig_time.update_layout(xaxis_title="Дата", yaxis_title="Время (минуты)")
    st.plotly_chart(fig_time, use_container_width=True)
    
    # График количества записей по дням
    st.subheader("📝 Количество записей по дням")
    fig_count = px.bar(
        daily_stats,
        x='date',
        y='Количество записей',
        title="Количество записей по дням"
    )
    fig_count.update_layout(xaxis_title="Дата", yaxis_title="Количество записей")
    st.plotly_chart(fig_count, use_container_width=True)
    
    # Анализ трендов
    st.subheader("📈 Анализ трендов")
    
    if len(daily_stats) > 1:
        # Вычисляем тренды
        time_trend = np.polyfit(range(len(daily_stats)), daily_stats['Общее время (мин)'], 1)
        count_trend = np.polyfit(range(len(daily_stats)), daily_stats['Количество записей'], 1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            trend_direction = "📈 Растет" if time_trend[0] > 0 else "📉 Падает" if time_trend[0] < 0 else "➡️ Стабильно"
            st.metric(
                "Тренд времени",
                trend_direction,
                f"{time_trend[0]:.1f} мин/день"
            )
        
        with col2:
            trend_direction = "📈 Растет" if count_trend[0] > 0 else "📉 Падает" if count_trend[0] < 0 else "➡️ Стабильно"
            st.metric(
                "Тренд записей",
                trend_direction,
                f"{count_trend[0]:.1f} записей/день"
            )
    else:
        st.info("Недостаточно данных для анализа трендов (нужно минимум 2 дня)")
    
    # Тренды по категориям
    st.subheader("📊 Тренды по категориям")
    
    # Группировка по дням и категориям
    daily_category_stats = df.groupby(['date', 'category'])['duration_minutes'].sum().reset_index()
    
    if not daily_category_stats.empty:
        # График трендов по категориям
        fig_category_trends = px.line(
            daily_category_stats,
            x='date',
            y='duration_minutes',
            color='category',
            title="Тренды по категориям",
            markers=True,
            color_discrete_map={
                'work': '#FF6B6B',
                'study': '#4ECDC4',
                'rest': '#45B7D1'
            }
        )
        fig_category_trends.update_layout(
            xaxis_title="Дата",
            yaxis_title="Время (минуты)"
        )
        st.plotly_chart(fig_category_trends, use_container_width=True)
        
        # Анализ трендов для каждой категории
        col1, col2, col3 = st.columns(3)
        
        for i, category in enumerate(['work', 'study', 'rest']):
            with [col1, col2, col3][i]:
                category_data = daily_category_stats[daily_category_stats['category'] == category]
                if len(category_data) > 1:
                    trend = np.polyfit(range(len(category_data)), category_data['duration_minutes'], 1)
                    trend_direction = "📈" if trend[0] > 0 else "📉" if trend[0] < 0 else "➡️"
                    
                    category_emoji = {'work': '💼', 'study': '📚', 'rest': '😴'}
                    emoji = category_emoji.get(category, '📊')
                    
                    st.metric(
                        f"{emoji} {category.upper()}",
                        trend_direction,
                        f"{trend[0]:.1f} мин/день"
                    )
                else:
                    category_emoji = {'work': '💼', 'study': '📚', 'rest': '😴'}
                    emoji = category_emoji.get(category, '📊')
                    st.metric(f"{emoji} {category.upper()}", "➡️", "Недостаточно данных")
    
    # Анализ по неделям
    st.subheader("📅 Анализ по неделям")
    
    # Добавляем недели к данным
    df_with_weeks = df.copy()
    df_with_weeks['week'] = df_with_weeks['entry_date'].dt.isocalendar().week
    df_with_weeks['year'] = df_with_weeks['entry_date'].dt.year
    
    weekly_stats = df_with_weeks.groupby(['year', 'week', 'category'])['duration_minutes'].sum().reset_index()
    
    if not weekly_stats.empty:
        weekly_stats['week_label'] = weekly_stats['year'].astype(str) + '-W' + weekly_stats['week'].astype(str)
        
        fig_weekly = px.line(
            weekly_stats,
            x='week_label',
            y='duration_minutes',
            color='category',
            title="Тренды по неделям",
            markers=True,
            color_discrete_map={
                'work': '#FF6B6B',
                'study': '#4ECDC4',
                'rest': '#45B7D1'
            }
        )
        fig_weekly.update_layout(
            xaxis_title="Неделя",
            yaxis_title="Время (минуты)"
        )
        fig_weekly.update_xaxes(tickangle=45)
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    # Анализ по месяцам
    st.subheader("📊 Анализ по месяцам")
    
    monthly_stats = df.groupby(['year', 'month', 'category'])['duration_minutes'].sum().reset_index()
    
    if not monthly_stats.empty:
        monthly_stats['month_label'] = monthly_stats['year'].astype(str) + '-' + monthly_stats['month'].astype(str).str.zfill(2)
        
        fig_monthly = px.bar(
            monthly_stats,
            x='month_label',
            y='duration_minutes',
            color='category',
            title="Время по месяцам",
            barmode='group',
            color_discrete_map={
                'work': '#FF6B6B',
                'study': '#4ECDC4',
                'rest': '#45B7D1'
            }
        )
        fig_monthly.update_layout(
            xaxis_title="Месяц",
            yaxis_title="Время (минуты)"
        )
        fig_monthly.update_xaxes(tickangle=45)
        st.plotly_chart(fig_monthly, use_container_width=True)

def main():
    """Основная функция дашборда"""
    st.title("📊 Дашборд учета времени")
    
    # Кнопка обновления данных
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Обновить данные", type="primary"):
            st.cache_data.clear()
            st.session_state.last_entry_count = 0  # Сбрасываем счетчик
            st.rerun()
    
    # Показываем статус автообновления
    with col3:
        st.markdown(f"🔄 Автообновление: каждые 30 сек")
    
    st.markdown("---")
    
    # Показываем время последнего обновления и статус базы
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"🕐 Последнее обновление: {datetime.now().strftime('%H:%M:%S')}")
    
    # Проверяем статус базы данных
    try:
        session = get_session()
        entry_count = session.query(TimeEntry).count()
        st.sidebar.markdown(f"💾 Записей в базе: {entry_count}")
        close_session(session)
    except Exception as e:
        st.sidebar.error(f"❌ Ошибка базы данных: {e}")
    
    df = load_data()
    
    # Проверяем новые записи
    if 'last_entry_count' not in st.session_state:
        st.session_state.last_entry_count = len(df)
    elif len(df) > st.session_state.last_entry_count:
        new_entries = len(df) - st.session_state.last_entry_count
        st.success(f"🎉 Добавлено {new_entries} новых записей!")
        st.session_state.last_entry_count = len(df)
    
    if df.empty:
        st.warning("📝 Данных пока нет. Добавьте записи через Telegram-бота.")
        st.info("💡 Используйте команду /add в боте для добавления первой записи.")
        return
    
    # Фильтры по времени
    st.sidebar.header("🔍 Фильтры")
    
    # Фильтр по дате
    min_date = df['entry_date'].min().date()
    max_date = df['entry_date'].max().date()
    
    date_range = st.sidebar.date_input(
        "📅 Период",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Фильтр по категориям
    all_categories = sorted(df['category'].unique())
    selected_categories = st.sidebar.multiselect(
        "📂 Категории",
        options=all_categories,
        default=all_categories,
        help="Выберите категории для анализа"
    )
    
    # Фильтр по задачам
    all_activities = sorted(df['activity_name'].unique())
    selected_activities = st.sidebar.multiselect(
        "📝 Задачи",
        options=all_activities,
        default=all_activities,
        help="Выберите задачи для анализа"
    )
    
    # Фильтр по времени дня
    time_period = st.sidebar.selectbox(
        "🕐 Время дня",
        ["Все время", "Утро (6-12)", "День (12-18)", "Вечер (18-24)", "Ночь (0-6)"]
    )
    
    # Применяем фильтры
    if len(date_range) == 2:
        start_date, end_date = date_range
        if start_date and end_date:
            df_filtered = df[
                (df['entry_date'].dt.date >= start_date) &
                (df['entry_date'].dt.date <= end_date) &
                (df['category'].isin(selected_categories)) &
                (df['activity_name'].isin(selected_activities))
            ]
        else:
            df_filtered = df[
                (df['category'].isin(selected_categories)) &
                (df['activity_name'].isin(selected_activities))
            ]
    else:
        df_filtered = df[
            (df['category'].isin(selected_categories)) &
            (df['activity_name'].isin(selected_activities))
        ]
    
    # Фильтр по времени дня
    if time_period == "Утро (6-12)":
        df_filtered = df_filtered[df_filtered['hour'].between(6, 11)]
    elif time_period == "День (12-18)":
        df_filtered = df_filtered[df_filtered['hour'].between(12, 17)]
    elif time_period == "Вечер (18-24)":
        df_filtered = df_filtered[df_filtered['hour'].between(18, 23)]
    elif time_period == "Ночь (0-6)":
        df_filtered = df_filtered[df_filtered['hour'].between(0, 5)]
    
    # Показываем статистику по отфильтрованным данным
    if df_filtered.empty:
        st.warning("📝 Нет данных для выбранных фильтров.")
        return
    
    # Вкладки для разных видов анализа
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Общая статистика", 
        "📂 По категориям",
        "🍰 По задачам", 
        "⏰ По времени", 
        "📋 Детализация",
        "📈 Тренды",
        "🕐 Время по категориям"
    ])
    
    with tab1:
        show_general_statistics(df_filtered)
    
    with tab2:
        show_category_analysis(df_filtered)
    
    with tab3:
        show_activity_analysis(df_filtered)
    
    with tab4:
        show_time_analysis(df_filtered)
    
    with tab5:
        show_detailed_data(df_filtered)
    
    with tab6:
        show_trends_analysis(df_filtered)
    
    with tab7:
        show_time_by_categories(df_filtered)

if __name__ == "__main__":
    main() 