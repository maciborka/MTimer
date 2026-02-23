#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления ставок для существующих проектов
"""

from database import Database

def main():
    db = Database()
    projects = db.get_all_projects()
    
    print("Существующие проекты:")
    for i, p in enumerate(projects, 1):
        try:
            rate = p['hourly_rate'] if p['hourly_rate'] else 0
        except (KeyError, IndexError):
            rate = 0
        print(f"{i}. {p['name']} - текущая ставка: ${rate:.2f}/ч")
    
    print("\n" + "="*50)
    print("Примеры ставок для обновления:")
    print("Разработка сайта -> $50/ч")
    print("Мобильное приложение -> $60/ч")
    print("Дизайн -> $45/ч")
    print("="*50 + "\n")
    
    # Автоматические обновления для типичных проектов
    rates_map = {
        'Разработка сайта': 50,
        'Мобильное приложение': 60,
        'Дизайн интерфейса': 45,
        'Консультация': 80,
        'Поддержка': 40,
        'Тестирование': 35,
        'Документация': 30,
        'Обучение': 55
    }
    
    updated = 0
    for p in projects:
        if p['name'] in rates_map:
            new_rate = rates_map[p['name']]
            db.update_project_rate(p['id'], new_rate)
            print(f"✓ Обновлен проект '{p['name']}': ${new_rate}/ч")
            updated += 1
    
    if updated > 0:
        print(f"\n✓ Обновлено проектов: {updated}")
    else:
        print("\nℹ Автоматически обновляемых проектов не найдено.")
        print("Вы можете добавить ставки вручную через интерфейс приложения.")
    
    db.close()

if __name__ == '__main__':
    main()
