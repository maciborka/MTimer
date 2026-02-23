#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт миграции: переносит текстовые описания (description) из time_sessions
в справочник work_types и создает связи через work_type_id
"""

from database import Database

def migrate_descriptions():
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Получаем все уникальные описания из сессий, где нет work_type_id
    cursor.execute('''
        SELECT DISTINCT description 
        FROM time_sessions 
        WHERE description IS NOT NULL 
          AND description != '' 
          AND work_type_id IS NULL
        ORDER BY description
    ''')
    
    descriptions = [row['description'] for row in cursor.fetchall()]
    
    if not descriptions:
        print("✅ Нет данных для миграции. Все сессии уже связаны с видами работ или не имеют описаний.")
        return
    
    print(f"Найдено {len(descriptions)} уникальных описаний для миграции:\n")
    
    migrated_count = 0
    
    for desc in descriptions:
        # Проверяем, существует ли уже такой вид работы
        cursor.execute('SELECT id FROM work_types WHERE name = ?', (desc,))
        row = cursor.fetchone()
        
        if row:
            work_type_id = row['id']
            print(f"  ↻ '{desc}' уже существует (id={work_type_id})")
        else:
            # Создаем новый вид работы
            cursor.execute('''
                INSERT INTO work_types (name, description) 
                VALUES (?, ?)
            ''', (desc, f'Автоматически создано из описаний сессий'))
            work_type_id = cursor.lastrowid
            conn.commit()
            print(f"  ✓ Создан вид работы '{desc}' (id={work_type_id})")
        
        # Обновляем все сессии с этим описанием
        cursor.execute('''
            UPDATE time_sessions 
            SET work_type_id = ? 
            WHERE description = ? AND work_type_id IS NULL
        ''', (work_type_id, desc))
        
        updated = cursor.rowcount
        conn.commit()
        
        print(f"    → Обновлено сессий: {updated}")
        migrated_count += updated
    
    print(f"\n✅ Миграция завершена! Обновлено {migrated_count} сессий.")
    print(f"Создано/использовано {len(descriptions)} видов работ.")
    
    # Показываем статистику
    cursor.execute('SELECT COUNT(*) as cnt FROM time_sessions WHERE work_type_id IS NULL')
    remaining = cursor.fetchone()['cnt']
    
    if remaining > 0:
        print(f"\n⚠️  Осталось {remaining} сессий без вида работы (пустое описание).")
    
    db.close()

if __name__ == '__main__':
    print("=== Миграция описаний в виды работ ===\n")
    migrate_descriptions()
