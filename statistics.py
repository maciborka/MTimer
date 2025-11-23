"""
Модуль статистики для MTimer
Візуалізація даних про відстеження часу з красивими графіками
"""

import matplotlib
matplotlib.use('MacOSX')  # Використовуємо нативний macOS backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

class StatisticsGenerator:
    """Генератор статистики та графіків для відстеження часу"""
    
    def __init__(self, database):
        self.db = database
    
    def _parse_datetime(self, datetime_str):
        """Парсинг datetime з підтримкою мікросекунд"""
        # Спробувати з мікросекундами
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            # Якщо не вийшло - без мікросекунд
            return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
        
    def get_daily_stats(self, days=30, project_id=None):
        """Отримати статистику по днях"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sessions = self.db.get_sessions_in_range(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d 23:59:59')
        )
        
        # Фільтруємо по проєкту якщо вказано
        if project_id is not None:
            sessions = [s for s in sessions if s['project_id'] == project_id]
        
        daily_data = defaultdict(lambda: {'duration': 0, 'cost': 0, 'sessions': 0})
        
        for session in sessions:
            date = self._parse_datetime(session['start_time']).date()
            daily_data[date]['duration'] += session['duration']
            daily_data[date]['cost'] += (session['cost'] if session['cost'] else 0)
            daily_data[date]['sessions'] += 1
            
        return daily_data
    
    def get_project_distribution(self, days=30, project_id=None):
        """Розподіл часу по проєктах"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sessions = self.db.get_sessions_in_range(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d 23:59:59')
        )
        
        # Фільтруємо по проєкту якщо вказано
        if project_id is not None:
            sessions = [s for s in sessions if s['project_id'] == project_id]
        
        project_data = defaultdict(lambda: {'duration': 0, 'cost': 0})
        
        for session in sessions:
            project = session['project_name'] if session['project_name'] else 'Без проєкту'
            project_data[project]['duration'] += session['duration']
            project_data[project]['cost'] += (session['cost'] if session['cost'] else 0)
            
        return project_data
    
    def get_hourly_distribution(self, days=30, project_id=None):
        """Розподіл активності по годинах дня"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sessions = self.db.get_sessions_in_range(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d 23:59:59')
        )
        
        # Фільтруємо по проєкту якщо вказано
        if project_id is not None:
            sessions = [s for s in sessions if s['project_id'] == project_id]
        
        hourly_data = defaultdict(float)
        
        for session in sessions:
            start = self._parse_datetime(session['start_time'])
            hour = start.hour
            hourly_data[hour] += session['duration'] / 3600  # В годинах
            
        return hourly_data
    
    def get_weekly_comparison(self, project_id=None):
        """Порівняння поточного та минулого тижня"""
        today = datetime.now()
        
        # Поточний тиждень
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        current_week = self.db.get_sessions_in_range(
            week_start.strftime('%Y-%m-%d'),
            week_end.strftime('%Y-%m-%d 23:59:59')
        )
        
        # Минулий тиждень
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(days=1)
        
        previous_week = self.db.get_sessions_in_range(
            prev_week_start.strftime('%Y-%m-%d'),
            prev_week_end.strftime('%Y-%m-%d 23:59:59')
        )
        
        # Фільтруємо по проєкту якщо вказано
        if project_id is not None:
            current_week = [s for s in current_week if s['project_id'] == project_id]
            previous_week = [s for s in previous_week if s['project_id'] == project_id]
        
        current_data = defaultdict(float)
        previous_data = defaultdict(float)
        
        for session in current_week:
            day = self._parse_datetime(session['start_time']).weekday()
            current_data[day] += session['duration'] / 3600
            
        for session in previous_week:
            day = self._parse_datetime(session['start_time']).weekday()
            previous_data[day] += session['duration'] / 3600
            
        return current_data, previous_data
    
    def format_duration(self, seconds):
        """Форматування тривалості"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}г {minutes}хв"
    
    def create_dashboard(self, period_days=30, project_id=None):
        """Створити дашборд з усіма графіками"""
        # Налаштування стилю
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Отримуємо назву проєкту для заголовка
        project_name = None
        if project_id is not None:
            projects = self.db.get_all_projects()
            for p in projects:
                if p['id'] == project_id:
                    project_name = p['name']
                    break
        
        # Створюємо фігуру з підграфіками
        fig = plt.figure(figsize=(16, 10))
        title = f'Статистика відстеження часу (останні {period_days} днів)'
        if project_name:
            title += f' - {project_name}'
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.995)
        
        # Підключаємо українські шрифти
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        
        # 1. Графік по днях (лінійний)
        ax1 = plt.subplot(2, 3, 1)
        self._plot_daily_trend(ax1, period_days, project_id)
        
        # 2. Розподіл по проєктах (кругова діаграма)
        ax2 = plt.subplot(2, 3, 2)
        self._plot_project_pie(ax2, period_days, project_id)
        
        # 3. Розподіл по годинах (стовпчикова)
        ax3 = plt.subplot(2, 3, 3)
        self._plot_hourly_distribution(ax3, period_days, project_id)
        
        # 4. Порівняння тижнів (групова стовпчикова)
        ax4 = plt.subplot(2, 3, 4)
        self._plot_weekly_comparison(ax4, project_id)
        
        # 5. Кумулятивна статистика (площа)
        ax5 = plt.subplot(2, 3, 5)
        self._plot_cumulative(ax5, period_days, project_id)
        
        # 6. Топ проєкти по вартості (горизонтальна стовпчикова)
        ax6 = plt.subplot(2, 3, 6)
        self._plot_top_projects(ax6, period_days, project_id)
        
        plt.tight_layout()
        return fig
    
    def _plot_daily_trend(self, ax, days, project_id=None):
        """Графік тренду по днях"""
        daily_stats = self.get_daily_stats(days, project_id)
        
        if not daily_stats:
            ax.text(0.5, 0.5, 'Немає даних', ha='center', va='center')
            ax.set_title('Щоденна активність')
            return
        
        dates = sorted(daily_stats.keys())
        hours = [daily_stats[d]['duration'] / 3600 for d in dates]
        
        ax.plot(dates, hours, marker='o', linewidth=2, markersize=4, color='#2E86AB')
        ax.fill_between(dates, hours, alpha=0.3, color='#2E86AB')
        
        ax.set_title('Щоденна активність', fontweight='bold')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Години')
        ax.grid(True, alpha=0.3)
        
        # Форматування дат
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_project_pie(self, ax, days, project_id=None):
        """Кругова діаграма розподілу по проєктах"""
        project_data = self.get_project_distribution(days, project_id)
        
        if not project_data:
            ax.text(0.5, 0.5, 'Немає даних', ha='center', va='center')
            ax.set_title('Розподіл по проєктах')
            return
        
        # Топ-5 проєктів + інші
        sorted_projects = sorted(project_data.items(), 
                                key=lambda x: x[1]['duration'], 
                                reverse=True)
        
        if len(sorted_projects) > 5:
            top_5 = sorted_projects[:5]
            others_duration = sum(p[1]['duration'] for p in sorted_projects[5:])
            top_5.append(('Інші', {'duration': others_duration}))
            data = top_5
        else:
            data = sorted_projects
        
        labels = [p[0] for p in data]
        sizes = [p[1]['duration'] / 3600 for p in data]
        
        colors = ['#A23B72', '#F18F01', '#C73E1D', '#2E86AB', '#6A994E', '#BC4B51']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        
        # Покращення читабельності
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        ax.set_title('Розподіл часу по проєктах', fontweight='bold')
    
    def _plot_hourly_distribution(self, ax, days, project_id=None):
        """Розподіл активності по годинах"""
        hourly_stats = self.get_hourly_distribution(days, project_id)
        
        if not hourly_stats:
            ax.text(0.5, 0.5, 'Немає даних', ha='center', va='center')
            ax.set_title('Активність по годинах')
            return
        
        hours = range(24)
        values = [hourly_stats.get(h, 0) for h in hours]
        
        colors = ['#2E86AB' if 9 <= h < 18 else '#A23B72' for h in hours]
        ax.bar(hours, values, color=colors, alpha=0.7)
        
        ax.set_title('Активність по годинах дня', fontweight='bold')
        ax.set_xlabel('Година дня')
        ax.set_ylabel('Години роботи')
        ax.set_xticks(range(0, 24, 3))
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_weekly_comparison(self, ax, project_id=None):
        """Порівняння поточного та минулого тижня"""
        current, previous = self.get_weekly_comparison(project_id)
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
        x = np.arange(len(days))
        width = 0.35
        
        current_values = [current.get(i, 0) for i in range(7)]
        previous_values = [previous.get(i, 0) for i in range(7)]
        
        ax.bar(x - width/2, previous_values, width, label='Минулий тиждень', 
               color='#A23B72', alpha=0.7)
        ax.bar(x + width/2, current_values, width, label='Поточний тиждень', 
               color='#2E86AB', alpha=0.7)
        
        ax.set_title('Порівняння тижнів', fontweight='bold')
        ax.set_ylabel('Години')
        ax.set_xticks(x)
        ax.set_xticklabels(days)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_cumulative(self, ax, days, project_id=None):
        """Кумулятивний графік"""
        daily_stats = self.get_daily_stats(days, project_id)
        
        if not daily_stats:
            ax.text(0.5, 0.5, 'Немає даних', ha='center', va='center')
            ax.set_title('Накопичувальна статистика')
            return
        
        dates = sorted(daily_stats.keys())
        hours = [daily_stats[d]['duration'] / 3600 for d in dates]
        cumulative = np.cumsum(hours)
        
        ax.fill_between(dates, cumulative, alpha=0.4, color='#6A994E')
        ax.plot(dates, cumulative, linewidth=2, color='#6A994E', marker='o', markersize=3)
        
        ax.set_title('Накопичувальний час роботи', fontweight='bold')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Всього годин')
        ax.grid(True, alpha=0.3)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_top_projects(self, ax, days, project_id=None):
        """Топ проєктів по вартості"""
        project_data = self.get_project_distribution(days, project_id)
        
        if not project_data:
            ax.text(0.5, 0.5, 'Немає даних', ha='center', va='center')
            ax.set_title('Топ проєкти по прибутку')
            return
        
        # Топ-10 по вартості
        sorted_projects = sorted(
            [(name, data['cost']) for name, data in project_data.items() if data['cost'] > 0],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        if not sorted_projects:
            ax.text(0.5, 0.5, 'Немає даних про вартість', ha='center', va='center')
            ax.set_title('Топ проєкти по прибутку')
            return
        
        names = [p[0] for p in sorted_projects]
        costs = [p[1] for p in sorted_projects]
        
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(names)))
        ax.barh(names, costs, color=colors)
        
        ax.set_title('Топ проєктів по прибутку', fontweight='bold')
        ax.set_xlabel('Вартість (₴)')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Додаємо значення на стовпчиках
        for i, cost in enumerate(costs):
            ax.text(cost, i, f' ₴{cost:.0f}', va='center', fontsize=9)
    
    def show_statistics(self, period_days=30, project_id=None):
        """Показати вікно статистики"""
        fig = self.create_dashboard(period_days, project_id)
        
        # Встановлюємо заголовок вікна
        manager = plt.get_current_fig_manager()
        manager.set_window_title('MTimer — Статистика')
        
        # Використовуємо неблокуючий режим
        plt.ion()  # Інтерактивний режим
        plt.show(block=False)  # Не блокуємо виконання
    
    def export_statistics(self, filename, period_days=30, project_id=None):
        """Експортувати статистику в файл"""
        fig = self.create_dashboard(period_days, project_id)
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return filename
