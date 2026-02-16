import sqlite3
from datetime import datetime, timedelta
import os
import shutil
from localization import t

# Константы версий схемы базы данных
SCHEMA_VERSION_CURRENT = 3  # Текущая версия с таблицей window_positions
SCHEMA_VERSION_V2 = 2  # Версия с таблицей task_names
SCHEMA_VERSION_LEGACY = 1  # Старая версия с description напрямую в time_sessions


class Database:
    def __init__(self, db_name="timetracker.db"):
        # По умолчанию база рядом с модулем (удобно в dev-режиме)
        import sys

        # Единый путь БД для DEV и .app, чтобы данные совпадали
        use_app_support = (
            getattr(sys, "frozen", False)
            or os.environ.get("MTIMER_USE_APP_SUPPORT") == "1"
            or os.environ.get("MTIMER_DEV") == "1"
        )
        if use_app_support:
            base_dir = os.path.expanduser("~/Library/Application Support/MacikTimer")
        else:
            # Запуск из исходников без DEV: база рядом с модулем
            base_dir = os.path.dirname(os.path.abspath(__file__))
        # Создаём директорию если её нет
        # Проверка прав записи убрана для ускорения инициализации
        # SQLite сам выдаст ошибку при попытке создания БД в недоступном месте
        try:
            os.makedirs(base_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"[DB] Cannot create directory {base_dir}: {e}")
            # Fallback на App Support если основная директория недоступна
            app_support = os.path.expanduser("~/Library/Application Support/MacikTimer")
            os.makedirs(app_support, exist_ok=True)
            base_dir = app_support
        self.db_path = os.path.join(base_dir, db_name)
        print(f"[DB] Initializing database at: {self.db_path}")
        print(
            f"[DB] frozen={getattr(sys, 'frozen', False)}, use_app_support={use_app_support}"
        )
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

        # Таблица компаний
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица видов работ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица названий задач (task names)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица проектов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#0000FF',
                hourly_rate REAL DEFAULT 0,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)

        # Добавляем колонку hourly_rate если её нет (миграция)
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN hourly_rate REAL DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Добавляем колонку company_id если её нет (миграция)
        try:
            cursor.execute(
                "ALTER TABLE projects ADD COLUMN company_id INTEGER REFERENCES companies(id)"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Таблица временных сессий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                description TEXT,
                work_type_id INTEGER,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (work_type_id) REFERENCES work_types (id)
            )
        """)

        # Добавляем колонку work_type_id если её нет (миграция)
        try:
            cursor.execute(
                "ALTER TABLE time_sessions ADD COLUMN work_type_id INTEGER REFERENCES work_types(id)"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Добавляем колонку paid (оплачено) если её нет (миграция)
        try:
            cursor.execute(
                "ALTER TABLE time_sessions ADD COLUMN paid INTEGER DEFAULT 0"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Добавляем колонку task_name_id если её нет (миграция для v2)
        try:
            cursor.execute(
                "ALTER TABLE time_sessions ADD COLUMN task_name_id INTEGER REFERENCES task_names(id)"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        conn.commit()

        # ============================================
        # Проверка версии схемы и автоматическая миграция
        # ============================================
        current_version = self.get_schema_version()

        if current_version < SCHEMA_VERSION_CURRENT:
            print(
                f"[DB] Database schema is outdated (v{current_version}), migration needed to v{SCHEMA_VERSION_CURRENT}"
            )
            print("[DB] Creating automatic backup before migration...")

            # Создаём автоматический бэкап
            backup_path = self.create_automatic_backup()

            if backup_path:
                print(f"[DB] Backup created: {backup_path}")
                print("[DB] Starting migration...")

                # Запускаем миграции последовательно
                if current_version < SCHEMA_VERSION_V2:
                    if self.migrate_to_v2():
                        print("[DB] Migration to v2 completed successfully!")
                        current_version = SCHEMA_VERSION_V2
                    else:
                        print(
                            "[DB] ERROR: Migration to v2 failed! Database remains in old format."
                        )
                        print(f"[DB] You can restore from backup: {backup_path}")
                        return

                if current_version < SCHEMA_VERSION_CURRENT:
                    if self.migrate_to_v3():
                        print("[DB] Migration to v3 completed successfully!")
                    else:
                        print("[DB] ERROR: Migration to v3 failed!")
                        print(f"[DB] You can restore from backup: {backup_path}")
            else:
                print("[DB] ERROR: Could not create backup, migration aborted!")
                print("[DB] Database will continue to work in legacy mode.")
        else:
            print(f"[DB] Database schema is up to date (v{current_version})")

    def create_window_positions_table(self):
        """
        Create table for storing window positions.
        Called during migration to v3.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS window_positions (
                window_name TEXT PRIMARY KEY,
                x REAL NOT NULL,
                y REAL NOT NULL,
                width REAL NOT NULL,
                height REAL NOT NULL,
                screen_index INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("[DB] window_positions table created")

    def create_project(self, name, color="#0000FF", hourly_rate=0, company_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            print(
                f"[DB] Creating project: name={name}, color={color}, hourly_rate={hourly_rate}, company_id={company_id}"
            )
            print(f"[DB] Database path: {self.db_path}")
            cursor.execute(
                "INSERT INTO projects (name, color, hourly_rate, company_id) VALUES (?, ?, ?, ?)",
                (name, color, hourly_rate, company_id),
            )
            conn.commit()
            project_id = cursor.lastrowid
            print(f"[DB] Project created successfully with ID: {project_id}")
            return project_id
        except sqlite3.IntegrityError as e:
            print(f"[DB] Failed to create project - IntegrityError: {e}")
            return None
        except Exception as e:
            print(f"[DB] Unexpected error creating project: {e}")
            import traceback

            traceback.print_exc()
            return None

    # ============================================
    # CRUD операции для таблицы task_names
    # ============================================

    def get_or_create_task_name(self, task_name):
        """
        Получить ID названия задачи или создать новое, если не существует.
        Возвращает ID записи в task_names.
        """
        if not task_name or task_name.strip() == "":
            return None

        task_name = task_name.strip()
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Пытаемся найти существующее название
            cursor.execute("SELECT id FROM task_names WHERE name = ?", (task_name,))
            result = cursor.fetchone()

            if result:
                return result["id"]

            # Если не нашли - создаём новое
            cursor.execute("INSERT INTO task_names (name) VALUES (?)", (task_name,))
            conn.commit()
            new_id = cursor.lastrowid
            print(f"[DB] Created new task name: '{task_name}' (ID: {new_id})")
            return new_id

        except sqlite3.IntegrityError:
            # Название уже существует (race condition)
            cursor.execute("SELECT id FROM task_names WHERE name = ?", (task_name,))
            result = cursor.fetchone()
            return result["id"] if result else None

    def update_task_name(self, task_name_id, new_name):
        """
        Переименовать задачу.
        Обновляет название в таблице task_names и description во всех связанных сессиях.
        """
        if not new_name or new_name.strip() == "":
            return False

        new_name = new_name.strip()
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Обновляем название в task_names
            cursor.execute(
                "UPDATE task_names SET name = ? WHERE id = ?", (new_name, task_name_id)
            )

            if cursor.rowcount > 0:
                # Также обновляем description во всех сессиях с этим task_name_id
                cursor.execute(
                    "UPDATE time_sessions SET description = ? WHERE task_name_id = ?",
                    (new_name, task_name_id),
                )
                sessions_updated = cursor.rowcount
                conn.commit()

                print(f"[DB] Updated task name ID {task_name_id} to '{new_name}'")
                print(f"[DB] Updated {sessions_updated} sessions with new description")
                return True
            else:
                print(f"[DB] Task name ID {task_name_id} not found")
                return False

        except sqlite3.IntegrityError:
            # Название уже существует
            print(f"[DB] Task name '{new_name}' already exists")
            return False

    def get_all_task_names(self):
        """
        Получить все названия задач с количеством использований.
        Возвращает список словарей с полями: id, name, session_count, total_duration
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                tn.id,
                tn.name,
                COUNT(ts.id) as session_count,
                COALESCE(SUM(ts.duration), 0) as total_duration
            FROM task_names tn
            LEFT JOIN time_sessions ts ON ts.task_name_id = tn.id
            GROUP BY tn.id, tn.name
            ORDER BY session_count DESC, tn.name
        """)

        return cursor.fetchall()

    def delete_task_name(self, task_name_id):
        """
        Удалить название задачи, если оно не используется в сессиях.
        Возвращает True в случае успеха, False если название используется или не найдено.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем используется ли название
        cursor.execute(
            "SELECT COUNT(*) as count FROM time_sessions WHERE task_name_id = ?",
            (task_name_id,),
        )
        result = cursor.fetchone()

        if result and result["count"] > 0:
            print(
                f"[DB] Cannot delete task name ID {task_name_id}: used in {result['count']} sessions"
            )
            return False

        # Удаляем название
        cursor.execute("DELETE FROM task_names WHERE id = ?", (task_name_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"[DB] Deleted task name ID {task_name_id}")
            return True
        else:
            print(f"[DB] Task name ID {task_name_id} not found")
            return False

    # ============================================
    # CRUD операции для time_sessions
    # ============================================

    def start_session(self, project_id, description):
        """
        Начать новую сессию работы.
        Создаёт запись в time_sessions и связывает её с task_name.
        Возвращает ID созданной сессии.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем или создаём task_name_id для данного описания
        task_name_id = None
        if description and description.strip():
            task_name_id = self.get_or_create_task_name(description.strip())

        # Создаём сессию
        start_time = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO time_sessions (project_id, description, start_time, task_name_id)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, description, start_time, task_name_id),
        )
        conn.commit()
        session_id = cursor.lastrowid
        print(
            f"[DB] Started session {session_id} for project {project_id}, task_name_id={task_name_id}"
        )
        return session_id

    def stop_session(self, session_id):
        """
        Остановить сессию работы.
        Устанавливает end_time и вычисляет duration.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем информацию о сессии
        cursor.execute(
            "SELECT start_time FROM time_sessions WHERE id = ?", (session_id,)
        )
        result = cursor.fetchone()

        if not result:
            print(f"[DB] Session {session_id} not found")
            return False

        start_time = datetime.fromisoformat(result["start_time"])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # Обновляем сессию
        cursor.execute(
            """
            UPDATE time_sessions
            SET end_time = ?, duration = ?
            WHERE id = ?
            """,
            (end_time.isoformat(), duration, session_id),
        )
        conn.commit()
        print(f"[DB] Stopped session {session_id}, duration={duration}s")
        return True

    def get_active_session(self):
        """
        Получить активную (незавершённую) сессию.
        Возвращает запись сессии или None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM time_sessions
            WHERE end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
            """
        )
        return cursor.fetchone()

    def get_today_sessions(self, project_id=None):
        """
        Получить все сессии за сегодня.
        Если указан project_id, фильтрует по проекту.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()

        if project_id:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ? AND ts.project_id = ?
                ORDER BY ts.start_time DESC
                """,
                (start_of_day, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ?
                ORDER BY ts.start_time DESC
                """,
                (start_of_day,),
            )

        return cursor.fetchall()

    def get_week_sessions(self, project_id=None):
        """
        Получить все сессии за текущую неделю (с понедельника).
        Если указан project_id, фильтрует по проекту.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Начало недели (понедельник)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week_iso = datetime.combine(
            start_of_week, datetime.min.time()
        ).isoformat()

        if project_id:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ? AND ts.project_id = ?
                ORDER BY ts.start_time DESC
                """,
                (start_of_week_iso, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ?
                ORDER BY ts.start_time DESC
                """,
                (start_of_week_iso,),
            )

        return cursor.fetchall()

    def get_today_total(self, project_id=None):
        """
        Получить общее время работы за сегодня (в секундах).
        Если указан project_id, фильтрует по проекту.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()

        if project_id:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE start_time >= ? AND project_id = ?
                """,
                (start_of_day, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE start_time >= ?
                """,
                (start_of_day,),
            )

        result = cursor.fetchone()
        return result["total"] if result else 0

    def get_week_total(self, project_id=None):
        """
        Получить общее время работы за текущую неделю (в секундах).
        Если указан project_id, фильтрует по проекту.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Начало недели (понедельник)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week_iso = datetime.combine(
            start_of_week, datetime.min.time()
        ).isoformat()

        if project_id:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE start_time >= ? AND project_id = ?
                """,
                (start_of_week_iso, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE start_time >= ?
                """,
                (start_of_week_iso,),
            )

        result = cursor.fetchone()
        return result["total"] if result else 0

    def update_session_details(self, session_id, new_description, new_project_id):
        """
        Обновить описание и проект сессии.
        При изменении описания обновляет название задачи для ВСЕХ сессий с тем же task_name_id.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем текущий task_name_id сессии
        cursor.execute(
            "SELECT task_name_id, description FROM time_sessions WHERE id = ?",
            (session_id,),
        )
        session_data = cursor.fetchone()

        if not session_data:
            print(f"[DB] Session {session_id} not found")
            return False

        current_task_name_id = session_data["task_name_id"]
        old_description = session_data["description"]

        # Обновляем проект сессии
        cursor.execute(
            "UPDATE time_sessions SET project_id = ? WHERE id = ?",
            (new_project_id, session_id),
        )

        # Если описание изменилось, обновляем название задачи
        if (
            new_description
            and new_description.strip()
            and new_description.strip() != old_description
        ):
            new_name = new_description.strip()

            if current_task_name_id:
                # Обновляем существующее название задачи (это обновит ВСЕ сессии с этим task_name_id)
                if self.update_task_name(current_task_name_id, new_name):
                    print(
                        f"[DB] Updated task name {current_task_name_id} from '{old_description}' to '{new_name}'"
                    )
                else:
                    print(f"[DB] Failed to update task name {current_task_name_id}")
            else:
                # Если task_name_id не был установлен, создаём новый или используем существующий
                task_name_id = self.get_or_create_task_name(new_name)
                cursor.execute(
                    "UPDATE time_sessions SET description = ?, task_name_id = ? WHERE id = ?",
                    (new_name, task_name_id, session_id),
                )
                print(f"[DB] Set task_name_id={task_name_id} for session {session_id}")

        conn.commit()
        print(
            f"[DB] Updated session {session_id}: description='{new_description}', project_id={new_project_id}"
        )
        return True

    def get_last_description_for_project(self, project_id):
        """
        Получить последнее описание задачи для проекта.
        Возвращает строку или "Программирование" по умолчанию.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT description
            FROM time_sessions
            WHERE project_id = ? AND description IS NOT NULL AND description != ''
            ORDER BY start_time DESC
            LIMIT 1
            """,
            (project_id,),
        )
        result = cursor.fetchone()

        if result and result["description"]:
            return result["description"]
        return "Программирование"

    def get_all_projects(self):
        """Получить все проекты"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY name")
        return cursor.fetchall()

    def get_all_companies(self):
        """Получить все компании"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies ORDER BY name")
        return cursor.fetchall()

    def get_all_sessions(self):
        """Получить все сессии"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ts.*, tn.name as task_name
            FROM time_sessions ts
            LEFT JOIN task_names tn ON ts.task_name_id = tn.id
            ORDER BY ts.start_time DESC
        """)
        return cursor.fetchall()

    def get_all_sessions_by_project(self, project_id):
        """Получить все сессии для конкретного проекта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ts.*, tn.name as task_name
            FROM time_sessions ts
            LEFT JOIN task_names tn ON ts.task_name_id = tn.id
            WHERE ts.project_id = ?
            ORDER BY ts.start_time DESC
        """,
            (project_id,),
        )
        return cursor.fetchall()

    def get_sessions_by_project(self, project_id, start_date=None, end_date=None):
        """Получить сессии для проекта в указанном диапазоне дат"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.project_id = ? 
                  AND ts.start_time >= ? 
                  AND ts.start_time <= ?
                ORDER BY ts.start_time DESC
            """,
                (project_id, start_date, end_date),
            )
        else:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.project_id = ?
                ORDER BY ts.start_time DESC
            """,
                (project_id,),
            )

        return cursor.fetchall()

    def get_sessions_in_range(self, start_date, end_date, project_id=None):
        """Получить сессии в указанном диапазоне дат"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if project_id:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ? 
                  AND ts.start_time <= ?
                  AND ts.project_id = ?
                ORDER BY ts.start_time DESC
            """,
                (start_date, end_date, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ? 
                  AND ts.start_time <= ?
                ORDER BY ts.start_time DESC
            """,
                (start_date, end_date),
            )

        return cursor.fetchall()

    def get_sessions_by_filter(self, filter_type, project_id=None):
        """Получить сессии по типу фильтра (today, week, month)"""
        if filter_type == "today":
            return self.get_today_sessions(project_id)
        elif filter_type == "week":
            return self.get_week_sessions(project_id)
        elif filter_type == "month":
            return self.get_month_sessions(project_id)
        else:
            return []

    def get_month_sessions(self, project_id=None):
        """Получить все сессии за текущий месяц"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Начало месяца
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        start_of_month_iso = datetime.combine(
            start_of_month, datetime.min.time()
        ).isoformat()

        if project_id:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ? AND ts.project_id = ?
                ORDER BY ts.start_time DESC
            """,
                (start_of_month_iso, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT ts.*, tn.name as task_name
                FROM time_sessions ts
                LEFT JOIN task_names tn ON ts.task_name_id = tn.id
                WHERE ts.start_time >= ?
                ORDER BY ts.start_time DESC
            """,
                (start_of_month_iso,),
            )

        return cursor.fetchall()

    def get_month_total(self, project_id=None):
        """
        Получить общее время работы за текущий месяц (в секундах).
        Если указан project_id, фильтрует по проекту.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Начало месяца
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        start_of_month_iso = datetime.combine(
            start_of_month, datetime.min.time()
        ).isoformat()

        if project_id:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE start_time >= ? AND project_id = ?
                """,
                (start_of_month_iso, project_id),
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE start_time >= ?
                """,
                (start_of_month_iso,),
            )

        result = cursor.fetchone()
        return result["total"] if result else 0

    def get_project_total(self, project_id, start_date=None, end_date=None):
        """Получить общее время работы по проекту (в секундах)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE project_id = ? 
                  AND start_time >= ? 
                  AND start_time <= ?
            """,
                (project_id, start_date, end_date),
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) as total
                FROM time_sessions
                WHERE project_id = ?
            """,
                (project_id,),
            )

        result = cursor.fetchone()
        return result["total"] if result else 0

    def get_unique_descriptions(self):
        """
        DEPRECATED: Use get_all_task_names() instead.
        Получить уникальные описания с количеством использований (старый метод).
        Оставлен для обратной совместимости.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                description,
                COUNT(*) as count,
                SUM(duration) as total_duration
            FROM time_sessions
            WHERE description IS NOT NULL AND description != ''
            GROUP BY description
            ORDER BY count DESC, description
        """)

        return cursor.fetchall()

    # ============================================
    # CRUD операции для work_types
    # ============================================

    def get_all_work_types(self):
        """Получить все виды работ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM work_types ORDER BY name")
        return cursor.fetchall()

    def get_work_type(self, work_type_id):
        """Получить вид работы по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM work_types WHERE id = ?", (work_type_id,))
        return cursor.fetchone()

    def update_work_type(self, work_type_id, name, description=""):
        """Обновить вид работы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE work_types SET name = ?, description = ? WHERE id = ?",
                (name, description, work_type_id),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_work_type(self, work_type_id):
        """Удалить вид работы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Проверяем, есть ли сессии с этим видом работы
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM time_sessions WHERE work_type_id = ?",
            (work_type_id,),
        )
        if cursor.fetchone()["cnt"] > 0:
            return False  # Нельзя удалить, есть связанные сессии
        cursor.execute("DELETE FROM work_types WHERE id = ?", (work_type_id,))
        conn.commit()
        return True

    def rename_all_sessions_with_description(self, old_description, new_description):
        """Переименовать все сессии с определенным описанием"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE time_sessions SET description = ? WHERE description = ?",
            (new_description, old_description),
        )
        conn.commit()
        return cursor.rowcount > 0

    # ============================================
    # Методы для работы с версионированием схемы БД
    # ============================================

    def get_schema_version(self):
        """
        Получить текущую версию схемы базы данных.
        Возвращает 1 если таблица schema_version не существует (старая БД).
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Проверяем существование таблицы schema_version
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)

            if cursor.fetchone() is None:
                # Таблицы нет - это старая версия БД (v1)
                print("[DB] schema_version table not found - legacy database (v1)")
                return SCHEMA_VERSION_LEGACY

            # Таблица есть - читаем версию
            cursor.execute("SELECT MAX(version) as version FROM schema_version")
            result = cursor.fetchone()

            if result and result["version"]:
                version = result["version"]
                print(f"[DB] Current schema version: {version}")
                return version
            else:
                # Таблица есть, но пустая - возвращаем v1
                print("[DB] schema_version table is empty - assuming v1")
                return SCHEMA_VERSION_LEGACY

        except sqlite3.Error as e:
            print(f"[DB] Error checking schema version: {e}")
            # В случае ошибки считаем что это старая БД
            return SCHEMA_VERSION_LEGACY

    # ============================================
    # Window Positions Management
    # ============================================

    def save_window_position(self, window_name, x, y, width, height, screen_index=0):
        """
        Save window position to database.
        Called when window is closed (windowWillClose_).

        Args:
            window_name: Unique identifier for the window (e.g., 'main_window', 'settings_window')
            x, y: Window position coordinates
            width, height: Window dimensions
            screen_index: Index of the screen (0 = primary)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO window_positions 
                (window_name, x, y, width, height, screen_index, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    window_name,
                    x,
                    y,
                    width,
                    height,
                    screen_index,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            print(
                f"[DB] Saved position for {window_name}: x={x:.0f}, y={y:.0f}, size={width:.0f}x{height:.0f}, screen={screen_index}"
            )
            return True
        except Exception as e:
            print(f"[DB] Error saving window position for {window_name}: {e}")
            return False

    def get_window_position(self, window_name):
        """
        Get saved window position from database.

        Args:
            window_name: Unique identifier for the window

        Returns:
            Dictionary with keys: x, y, width, height, screen_index
            or None if no saved position exists
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT x, y, width, height, screen_index 
                FROM window_positions 
                WHERE window_name = ?
            """,
                (window_name,),
            )

            result = cursor.fetchone()

            if result:
                pos = {
                    "x": result["x"],
                    "y": result["y"],
                    "width": result["width"],
                    "height": result["height"],
                    "screen_index": result["screen_index"],
                }
                print(
                    f"[DB] Loaded position for {window_name}: x={pos['x']:.0f}, y={pos['y']:.0f}, size={pos['width']:.0f}x{pos['height']:.0f}, screen={pos['screen_index']}"
                )
                return pos
            else:
                print(f"[DB] No saved position found for {window_name}")
                return None

        except Exception as e:
            print(f"[DB] Error loading window position for {window_name}: {e}")
            return None

    # ============================================
    # Database Migration Methods
    # ============================================

    def set_schema_version(self, version):
        """
        Установить версию схемы базы данных.
        Создаёт таблицу schema_version если её нет.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Создаём таблицу если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Добавляем запись о новой версии
        cursor.execute(
            "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
            (version, datetime.now().isoformat()),
        )
        conn.commit()
        print(f"[DB] Schema version set to: {version}")

    def create_automatic_backup(self):
        """
        Создаёт автоматический бэкап базы данных перед миграцией.
        Возвращает путь к созданному бэкапу или None в случае ошибки.
        """
        try:
            # Создаём директорию для бэкапов
            backup_dir = os.path.expanduser(
                "~/Library/Application Support/MTimer/backups"
            )
            os.makedirs(backup_dir, exist_ok=True)

            # Генерируем имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"auto_backup_before_migration_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)

            # Копируем файл БД
            print(f"[DB] Creating automatic backup: {backup_path}")
            shutil.copy2(self.db_path, backup_path)

            # Проверяем что файл создан
            if os.path.exists(backup_path):
                file_size = os.path.getsize(backup_path)
                print(
                    f"[DB] Backup created successfully: {backup_path} ({file_size} bytes)"
                )
                return backup_path
            else:
                print(f"[DB] ERROR: Backup file not found after creation")
                return None

        except Exception as e:
            print(f"[DB] ERROR creating automatic backup: {e}")
            import traceback

            traceback.print_exc()
            return None

    def migrate_to_v2(self):
        """
        Миграция базы данных с версии 1 на версию 2.

        Изменения в v2:
        - Создаётся таблица task_names для хранения уникальных названий задач
        - В time_sessions добавляется столбец task_name_id (FK на task_names)
        - Все существующие описания мигрируются в task_names
        - Все сессии обновляются ссылками на соответствующие task_names

        Возвращает True если миграция прошла успешно, False в случае ошибки.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            print("[DB] Starting migration to v2...")

            # Начинаем транзакцию
            cursor.execute("BEGIN TRANSACTION")

            # 1. Создаём таблицу task_names если её нет
            print("[DB] Step 1/5: Creating task_names table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_names (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Добавляем столбец task_name_id в time_sessions если его нет
            print("[DB] Step 2/5: Adding task_name_id column to time_sessions...")
            try:
                cursor.execute("""
                    ALTER TABLE time_sessions 
                    ADD COLUMN task_name_id INTEGER REFERENCES task_names(id)
                """)
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("[DB] Column task_name_id already exists, skipping...")
                else:
                    raise

            # 3. Извлекаем все уникальные описания и вставляем в task_names
            print("[DB] Step 3/5: Migrating unique descriptions to task_names...")
            cursor.execute("""
                SELECT DISTINCT description 
                FROM time_sessions 
                WHERE description IS NOT NULL AND description != ''
                ORDER BY description
            """)

            unique_descriptions = cursor.fetchall()
            print(f"[DB] Found {len(unique_descriptions)} unique task descriptions")

            for row in unique_descriptions:
                description = row["description"]
                try:
                    cursor.execute(
                        "INSERT INTO task_names (name) VALUES (?)", (description,)
                    )
                except sqlite3.IntegrityError:
                    # Название уже существует (на случай повторного запуска миграции)
                    print(f"[DB] Task name '{description}' already exists, skipping...")

            # 4. Обновляем все сессии, устанавливая task_name_id
            print("[DB] Step 4/5: Linking sessions to task_names...")
            cursor.execute("""
                UPDATE time_sessions
                SET task_name_id = (
                    SELECT id FROM task_names 
                    WHERE task_names.name = time_sessions.description
                )
                WHERE description IS NOT NULL AND description != ''
            """)

            updated_count = cursor.rowcount
            print(f"[DB] Updated {updated_count} sessions with task_name_id")

            # 5. Устанавливаем версию схемы в 2
            print("[DB] Step 5/5: Setting schema version to 2...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION_V2, datetime.now().isoformat()),
            )

            # Коммитим транзакцию
            conn.commit()
            print("[DB] Migration to v2 completed successfully!")
            print(f"[DB] Migrated {len(unique_descriptions)} unique task names")
            print(f"[DB] Updated {updated_count} time sessions")

            return True

        except Exception as e:
            # Откатываем все изменения
            conn.rollback()
            print(f"[DB] ERROR during migration: {e}")
            import traceback

            traceback.print_exc()
            return False

    def migrate_to_v3(self):
        """
        Migrate database from version 2 to version 3.

        Changes in v3:
        - Creates window_positions table for storing window positions

        Returns True if migration successful, False on error.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            print("[DB] Starting migration to v3...")

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")

            # 1. Create window_positions table
            print("[DB] Step 1/2: Creating window_positions table...")
            self.create_window_positions_table()

            # 2. Set schema version to 3
            print("[DB] Step 2/2: Setting schema version to 3...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION_CURRENT, datetime.now().isoformat()),
            )

            # Commit transaction
            conn.commit()
            print("[DB] Migration to v3 completed successfully!")

            return True

        except Exception as e:
            # Rollback all changes
            conn.rollback()
            print(f"[DB] ERROR during migration to v3: {e}")
            import traceback

            traceback.print_exc()
            return False
