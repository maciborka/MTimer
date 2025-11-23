#!/usr/bin/env python3
"""
Скрипт для відображення статистики в окремому процесі
"""

if __name__ == '__main__':
    from statistics import StatisticsGenerator
    from database import Database
    
    try:
        db = Database()
        stats = StatisticsGenerator(db)
        stats.show_statistics(period_days=30)
        
        # Тримаємо вікно відкритим
        import matplotlib.pyplot as plt
        plt.show(block=True)  # Блокуємо тільки цей процес, не основний застосунок
        
    except Exception as e:
        print(f"Error showing statistics: {e}")
        import traceback
        traceback.print_exc()
