#!/usr/bin/env python3
"""
Скрипт для відображення статистики в окремому процесі
"""

if __name__ == '__main__':
    import sys
    from statistics import StatisticsGenerator
    from database import Database
    
    try:
        # Отримуємо параметри з аргументів командного рядка
        period_filter = sys.argv[1] if len(sys.argv) > 1 else 'month'
        project_id = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != 'None' else None
        
        # Конвертуємо фільтр в кількість днів
        period_days_map = {
            'today': 1,
            'week': 7,
            'month': 30
        }
        period_days = period_days_map.get(period_filter, 30)
        
        db = Database()
        stats = StatisticsGenerator(db)
        stats.show_statistics(period_days=period_days, project_id=project_id)
        
        # Тримаємо вікно відкритим
        import matplotlib.pyplot as plt
        plt.show(block=True)  # Блокуємо тільки цей процес, не основний застосунок
        
    except Exception as e:
        print(f"Error showing statistics: {e}")
        import traceback
        traceback.print_exc()
