import streamlit as st
import pandas as pd
import plotly.express as px
from database.engine import get_session, close_session
from database.models import TimeEntry
from datetime import datetime

# Настройка страницы
st.set_page_config(
    page_title="Трекер времени",
    page_icon="⏰",
    layout="wide"
)

@st.cache_data
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
                'duration_minutes': entry.duration_minutes,
                'entry_date': entry.entry_date
            })
        df = pd.DataFrame(data)
        if not df.empty and 'entry_date' in df.columns:
            df['entry_date'] = pd.to_datetime(df['entry_date'])
        return df
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()
    finally:
        close_session(session)

def main():
    """Основная функция дашборда"""
    # Заголовок
    st.title("📊 Дашборд учета времени")
    st.markdown("---")
    
    # Загружаем данные
    df = load_data()
    
    # Проверяем, есть ли данные
    if df.empty:
        st.warning("📝 Данных пока нет. Добавьте записи через Telegram-бота.")
        st.info("💡 Используйте команду /add в боте для добавления первой записи.")
        return
    
    # Отображаем общую статистику
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_time = df['duration_minutes'].sum()
        st.metric("Общее время", f"{total_time} мин")
    
    with col2:
        total_entries = len(df)
        st.metric("Всего записей", total_entries)
    
    with col3:
        unique_activities = df['activity_name'].nunique()
        st.metric("Уникальных задач", unique_activities)
    
    with col4:
        avg_time = df['duration_minutes'].mean()
        st.metric("Среднее время", f"{avg_time:.1f} мин")
    
    st.markdown("---")
    
    # Круговая диаграмма - распределение времени по задачам
    st.header("🍰 Распределение времени по задачам")
    
    # Группируем данные по названию активности
    activity_summary = df.groupby('activity_name')['duration_minutes'].sum().reset_index()
    activity_summary = activity_summary.sort_values('duration_minutes', ascending=False)
    
    # Создаем круговую диаграмму
    fig_pie = px.pie(
        activity_summary,
        values='duration_minutes',
        names='activity_name',
        title="Распределение времени по задачам",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Столбчатая диаграмма - продуктивность по дням
    st.header("📈 Продуктивность по дням")
    
    # Создаем колонку с датой (без времени)
    df['date'] = df['entry_date'].dt.date
    
    # Группируем по дате
    daily_summary = df.groupby('date')['duration_minutes'].sum().reset_index()
    daily_summary['date'] = pd.to_datetime(daily_summary['date'])
    daily_summary = daily_summary.sort_values('date')
    
    # Создаем столбчатую диаграмму
    fig_bar = px.bar(
        daily_summary,
        x='date',
        y='duration_minutes',
        title="Суммарное время по дням",
        labels={'duration_minutes': 'Время (минуты)', 'date': 'Дата'},
        color='duration_minutes',
        color_continuous_scale='viridis'
    )
    fig_bar.update_layout(xaxis_tickformat='%d.%m.%Y')
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Таблица со всеми записями
    st.header("📋 Все записи")
    
    # Форматируем данные для отображения
    display_df = df.copy()
    display_df['entry_date'] = display_df['entry_date'].dt.strftime('%d.%m.%Y %H:%M')
    display_df['duration_formatted'] = display_df['duration_minutes'].apply(
        lambda x: f"{x//60}ч {x%60}мин" if x >= 60 else f"{x}мин"
    )
    
    # Переименовываем колонки для лучшего отображения
    display_df = display_df.rename(columns={
        'id': 'ID',
        'activity_name': 'Задача',
        'duration_minutes': 'Время (мин)',
        'duration_formatted': 'Время',
        'entry_date': 'Дата и время'
    })
    
    # Отображаем только нужные колонки
    columns_to_show = ['ID', 'Задача', 'Время', 'Дата и время']
    st.dataframe(display_df[columns_to_show], use_container_width=True)
    
    # Дополнительная статистика
    st.markdown("---")
    st.header("📊 Дополнительная статистика")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Топ-5 самых долгих задач")
        top_activities = activity_summary.head(5)
        for idx, row in top_activities.iterrows():
            hours = row['duration_minutes'] // 60
            minutes = row['duration_minutes'] % 60
            time_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
            st.write(f"• **{row['activity_name']}**: {time_str}")
    
    with col2:
        st.subheader("Последние 5 записей")
        recent_entries = df.sort_values('entry_date', ascending=False).head(5)
        for idx, row in recent_entries.iterrows():
            hours = row['duration_minutes'] // 60
            minutes = row['duration_minutes'] % 60
            time_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
            date_str = row['entry_date'].strftime('%d.%m.%Y %H:%M')
            st.write(f"• **{row['activity_name']}** ({time_str}) - {date_str}")

if __name__ == "__main__":
    main() 