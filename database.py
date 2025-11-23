import sqlite3
from datetime import datetime
import os
from localization import t

class Database:
    def __init__(self, db_name='timetracker.db'):
        # По умолчанию база рядом с модулем (удобно в dev-режиме)
        base_dir = os.path.dirname(__file__)
        # Если папка недоступна для записи (например, внутри .app в /Applications),
        # переносим БД в ~/Library/Application Support/MacikTimer
        try:
            os.makedirs(base_dir, exist_ok=True)
            test_path = os.path.join(base_dir, '.write_test')
            with open(test_path, 'w') as f:
                f.write('ok')
            os.remove(test_path)
        except Exception:
            app_support = os.path.expanduser('~/Library/Application Support/MacikTimer')
            os.makedirs(app_support, exist_ok=True)
            base_dir = app_support
        self.db_path = os.path.join(base_dir, db_name)
        self.connection = None
        self.init_database()
    
    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица проектов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#0000FF',
                hourly_rate REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем колонку hourly_rate если её нет (миграция)
        try:
            cursor.execute('ALTER TABLE projects ADD COLUMN hourly_rate REAL DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            # Колонка уже существует
            pass
        
        # Таблица временных сессий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        conn.commit()
    
    def create_project(self, name, color='#0000FF', hourly_rate=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO projects (name, color, hourly_rate) VALUES (?, ?, ?)', (name, color, hourly_rate))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def update_project_rate(self, project_id, hourly_rate):
        """Обновить стоимость часа для проекта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE projects SET hourly_rate = ? WHERE id = ?', (hourly_rate, project_id))
        conn.commit()
    
    def update_project(self, project_id, name, hourly_rate):
        """Обновить имя и стоимость проекта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE projects SET name = ?, hourly_rate = ? WHERE id = ?', (name, hourly_rate, project_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_projects(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects ORDER BY name')
        return cursor.fetchall()
    
    def get_project_by_id(self, project_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        return cursor.fetchone()
    
    def start_session(self, project_id, description=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        start_time = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO time_sessions (project_id, description, start_time)
            VALUES (?, ?, ?)
        ''', (project_id, description, start_time))
        conn.commit()
        return cursor.lastrowid
    
    def stop_session(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        end_time = datetime.now().isoformat()
        
        # Получаем время начала
        cursor.execute('SELECT start_time FROM time_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row['start_time'])
            end_time_dt = datetime.fromisoformat(end_time)
            duration = int((end_time_dt - start_time).total_seconds())
            
            cursor.execute('''
                UPDATE time_sessions 
                SET end_time = ?, duration = ?
                WHERE id = ?
            ''', (end_time, duration, session_id))
            conn.commit()
            return duration
        return 0
    
    def delete_session(self, session_id):
        """Удаляет сессию по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM time_sessions WHERE id = ?', (session_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def get_active_session(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, p.name as project_name, p.color as project_color
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE s.end_time IS NULL
            ORDER BY s.start_time DESC
            LIMIT 1
        ''')
        return cursor.fetchone()
    
    def get_last_description_for_project(self, project_id):
        """Получить последнее описание для проекта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT description
            FROM time_sessions
            WHERE project_id = ? AND description IS NOT NULL AND description != ''
            ORDER BY start_time DESC
            LIMIT 1
        ''', (project_id,))
        row = cursor.fetchone()
        if row and row['description']:
            return row['description']
        return t('default_description')  # По умолчанию для новых проектов
    
    def get_sessions_by_date_range(self, start_date, end_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, p.name as project_name, p.color as project_color
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE date(s.start_time) BETWEEN date(?) AND date(?)
            ORDER BY s.start_time DESC
        ''', (start_date, end_date))
        return cursor.fetchall()
    
    def get_today_sessions(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT s.*, p.name as project_name, p.color as project_color
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE date(s.start_time) = date(?)
            ORDER BY s.start_time DESC
        ''', (today,))
        return cursor.fetchall()
    
    def get_week_sessions(self):
        """Получить все сессии за последние 7 дней"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, p.name as project_name, p.color as project_color
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE date(s.start_time) >= date('now', '-6 days')
            ORDER BY s.start_time DESC
        ''')
        return cursor.fetchall()
    
    def get_month_sessions(self):
        """Получить все сессии за последние 30 дней"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, p.name as project_name, p.color as project_color
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE date(s.start_time) >= date('now', '-29 days')
            ORDER BY s.start_time DESC
        ''')
        return cursor.fetchall()
    
    def get_week_total(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(duration) as total
            FROM time_sessions
            WHERE date(start_time) >= date('now', '-6 days')
        ''')
        row = cursor.fetchone()
        return row['total'] if row['total'] else 0
    
    def get_month_total(self):
        """Получить общее время за месяц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(duration) as total
            FROM time_sessions
            WHERE date(start_time) >= date('now', '-29 days')
        ''')
        row = cursor.fetchone()
        return row['total'] if row['total'] else 0
    
    def get_sessions_by_project(self, project_id, period='week'):
        """Получить сессии для конкретного проекта за период"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if period == 'today':
            date_filter = "date(s.start_time) = date('now')"
        elif period == 'week':
            date_filter = "date(s.start_time) >= date('now', '-6 days')"
        else:  # month
            date_filter = "date(s.start_time) >= date('now', '-29 days')"
        
        cursor.execute(f'''
            SELECT s.*, p.name as project_name, p.color as project_color, p.hourly_rate
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE s.project_id = ? AND {date_filter}
            ORDER BY s.start_time DESC
        ''', (project_id,))
        return cursor.fetchall()
    
    def get_project_total(self, project_id, period='week'):
        """Получить общее время по проекту за период"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if period == 'today':
            date_filter = "date(start_time) = date('now')"
        elif period == 'week':
            date_filter = "date(start_time) >= date('now', '-6 days')"
        else:  # month
            date_filter = "date(start_time) >= date('now', '-29 days')"
        
        cursor.execute(f'''
            SELECT SUM(duration) as total
            FROM time_sessions
            WHERE project_id = ? AND {date_filter}
        ''', (project_id,))
        row = cursor.fetchone()
        return row['total'] if row['total'] else 0
    
    def get_sessions_in_range(self, start_date, end_date):
        """Получить все сессии в указанном диапазоне дат для статистики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                s.*,
                p.name as project_name,
                p.color as project_color,
                p.hourly_rate,
                CASE 
                    WHEN p.hourly_rate > 0 THEN (s.duration / 3600.0) * p.hourly_rate
                    ELSE 0
                END as cost
            FROM time_sessions s
            LEFT JOIN projects p ON s.project_id = p.id
            WHERE s.start_time >= ? AND s.start_time <= ?
            ORDER BY s.start_time ASC
        ''', (start_date, end_date))
        return cursor.fetchall()
    
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
