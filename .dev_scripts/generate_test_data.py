# -*- coding: utf-8 -*-
"""
Генератор тестовых данных для MacikTimer
Создаёт проекты и сессии за сегодня и текущую неделю
"""

from database import Database
from datetime import datetime, timedelta
import random

def generate_test_data():
    db = Database()
    
    # Названия проектов
    project_names = [
        "Разработка сайта",
        "Мобильное приложение",
        "Документация",
        "Встречи с клиентами",
        "Code Review",
        "Рефакторинг",
        "Тестирование",
        "DevOps задачи"
    ]
    
    # Описания для задач
    descriptions = [
        "Исправление бага в авторизации",
        "Добавление новой функции",
        "Оптимизация запросов к БД",
        "Создание unit-тестов",
        "Обновление документации API",
        "Настройка CI/CD pipeline",
        "Код-ревью PR #123",
        "Встреча с командой",
        "Планирование спринта",
        "Исследование новой библиотеки",
        "Багфиксинг",
        "Разработка UI компонентов",
        "Интеграция с внешним API",
        "Рефакторинг legacy кода",
        "Написание технической спецификации"
    ]
    
    print("Создаю проекты...")
    # Создаём проекты
    project_ids = []
    for name in project_names:
        pid = db.create_project(name)
        if pid:
            project_ids.append(pid)
            print(f"  ✓ {name}")
    
    if not project_ids:
        print("Не удалось создать проекты. Используем существующие.")
        existing = db.get_all_projects()
        project_ids = [p['id'] for p in existing]
    
    if not project_ids:
        print("Нет проектов для генерации данных!")
        db.close()
        return
    
    print(f"\nГенерирую сессии...")
    today = datetime.now()
    
    # Генерируем сессии за сегодня (15-25 записей)
    num_today_sessions = random.randint(15, 25)
    print(f"Создаю {num_today_sessions} сессий за сегодня...")
    
    for i in range(num_today_sessions):
        project_id = random.choice(project_ids)
        description = random.choice(descriptions)
        
        # Случайное время начала в течение дня
        hour = random.randint(8, 19)
        minute = random.randint(0, 59)
        start_time = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Длительность от 2 до 45 минут
        duration_minutes = random.randint(2, 45)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Вставляем напрямую в БД
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO time_sessions (project_id, description, start_time, end_time, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            project_id,
            description,
            start_time.isoformat(),
            end_time.isoformat(),
            duration_minutes * 60
        ))
    
    conn.commit()
    print(f"  ✓ Создано {num_today_sessions} сессий за сегодня")
    
    # Генерируем сессии за прошлые дни недели (понедельник-вчера)
    days_back = (today.weekday() + 1) % 7  # дни с понедельника
    if days_back == 0:
        days_back = 7
    
    print(f"\nСоздаю сессии за последние {days_back} дней...")
    for day_offset in range(1, days_back + 1):
        day = today - timedelta(days=day_offset)
        num_sessions = random.randint(8, 15)
        
        for i in range(num_sessions):
            project_id = random.choice(project_ids)
            description = random.choice(descriptions)
            
            hour = random.randint(8, 19)
            minute = random.randint(0, 59)
            start_time = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            duration_minutes = random.randint(5, 60)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO time_sessions (project_id, description, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                project_id,
                description,
                start_time.isoformat(),
                end_time.isoformat(),
                duration_minutes * 60
            ))
        
        conn.commit()
        day_name = day.strftime('%d.%m (%A)')
        print(f"  ✓ {day_name}: {num_sessions} сессий")
    
    # Статистика
    total_today = len(list(db.get_today_sessions()))
    week_total = db.get_week_total()
    
    print(f"\n{'='*50}")
    print(f"Готово!")
    print(f"{'='*50}")
    print(f"Сессий сегодня: {total_today}")
    print(f"Общее время за неделю: {week_total // 3600}ч {(week_total % 3600) // 60}м")
    print(f"\nТеперь запустите приложение:")
    print(f"  python mac_app.py")
    
    db.close()

if __name__ == '__main__':
    generate_test_data()
