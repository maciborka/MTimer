import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
from database import Database

class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clockify - Time Tracker")
        self.root.geometry("800x600")
        self.root.configure(bg='#f5f5f5')
        
        self.db = Database()
        self.timer_running = False
        self.current_session_id = None
        self.start_time = None
        self.elapsed_seconds = 0
        self.auto_refresh_id = None
        self.first_run = True
        
        # Проверяем активную сессию при запуске
        self.check_active_session()
        
        self.create_widgets()
        self.load_projects()
        self.refresh_sessions()
        
        if self.timer_running:
            self.update_timer()
        
        # Запускаем автообновление
        self.auto_refresh_data()
    
    def check_active_session(self):
        """Проверяет есть ли активная сессия при запуске"""
        active = self.db.get_active_session()
        if active:
            self.timer_running = True
            self.current_session_id = active['id']
            start_time_str = active['start_time']
            self.start_time = datetime.fromisoformat(start_time_str)
            elapsed = datetime.now() - self.start_time
            self.elapsed_seconds = int(elapsed.total_seconds())
    
    def create_widgets(self):
        # Верхняя панель с таймером
        top_frame = tk.Frame(self.root, bg='#0088cc', height=140)
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        top_frame.pack_propagate(False)
        
        # Заголовок
        title_label = tk.Label(top_frame, text="⏱ clockify", font=('Arial', 18, 'bold'), 
                              bg='#0088cc', fg='white')
        title_label.pack(pady=10)
        
        # Контейнер для описания и таймера
        timer_container = tk.Frame(top_frame, bg='white', relief=tk.FLAT, bd=0, 
                                  highlightthickness=1, highlightbackground='#ddd')
        timer_container.pack(pady=5, padx=20, fill=tk.X)
        
        # Первая строка: описание и выбор проекта
        top_row = tk.Frame(timer_container, bg='white')
        top_row.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Описание
        self.description_entry = tk.Entry(top_row, font=('Arial', 12), 
                                         relief=tk.FLAT, bd=0, 
                                         bg='white', fg='#333')
        self.description_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.description_entry.insert(0, "Введите описание...")
        self.description_entry.config(fg='#999')
        self.description_entry.bind('<FocusIn>', self.on_description_focus_in)
        self.description_entry.bind('<FocusOut>', self.on_description_focus_out)
        
        # Вторая строка: проект, таймер и кнопка
        bottom_row = tk.Frame(timer_container, bg='white')
        bottom_row.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Метка проекта
        tk.Label(bottom_row, text="● Проект:", font=('Arial', 10), 
                bg='white', fg='#666').pack(side=tk.LEFT, padx=(0, 5))
        
        # Выбор проекта
        self.project_var = tk.StringVar()
        style = ttk.Style()
        # Используем тему 'clam', чтобы корректно настраивать цвета ttk-виджетов на macOS
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        # Стили для выпадающего списка проектов
        style.configure('Project.TCombobox', fieldbackground='white', 
                       background='white', borderwidth=1)
        # Единые стили кнопок
        style.configure('Primary.TButton', background='#ff0066', foreground='white',
                        font=('Arial', 12, 'bold'), padding=(14, 6), borderwidth=0)
        style.map('Primary.TButton',
                  background=[('active', '#cc0052'), ('disabled', '#ff99c2')],
                  foreground=[('disabled', '#f0f0f0')])
        style.configure('Action.TButton', background='#0088cc', foreground='white',
                        font=('Arial', 9, 'bold'), padding=(10, 4), borderwidth=0)
        style.map('Action.TButton', background=[('active', '#0066aa')])
        style.configure('ActionLarge.TButton', background='#0088cc', foreground='white',
                        font=('Arial', 11, 'bold'), padding=(14, 6), borderwidth=0)
        style.map('ActionLarge.TButton', background=[('active', '#0066aa')])
        self.project_combo = ttk.Combobox(bottom_row, textvariable=self.project_var, 
                                         state='readonly', width=25, 
                                         style='Project.TCombobox',
                                         font=('Arial', 11))
        self.project_combo.pack(side=tk.LEFT, padx=5)
        # Кнопка добавления проекта рядом со списком
        self.add_project_btn = ttk.Button(bottom_row, text='＋', width=3,
                                          style='Action.TButton',
                                          command=self.create_new_project)
        self.add_project_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        # Таймер
        self.timer_label = tk.Label(bottom_row, text="00:00:00", 
                                    font=('Arial', 18, 'bold'), bg='white', fg='#333')
        self.timer_label.pack(side=tk.LEFT, padx=20)
        
        # Кнопка старт/стоп (ttk c единым стилем)
        self.start_stop_btn = ttk.Button(bottom_row, text="START",
                                         style='Primary.TButton',
                                         command=self.toggle_timer)
        self.start_stop_btn.pack(side=tk.LEFT, padx=10, pady=2)
        
        if self.timer_running:
            self.start_stop_btn.config(text="STOP")
        
        # Средняя панель - статистика недели
        stats_frame = tk.Frame(self.root, bg='#f5f5f5', height=60)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        stats_frame.pack_propagate(False)
        
        week_label = tk.Label(stats_frame, text="THIS WEEK TOTAL", 
                             font=('Arial', 10, 'bold'), bg='#f5f5f5', fg='#666')
        week_label.pack(anchor=tk.W)
        
        self.week_total_label = tk.Label(stats_frame, text="00:00:00", 
                                        font=('Arial', 20, 'bold'), bg='#f5f5f5', fg='#333')
        self.week_total_label.pack(anchor=tk.W)
        
        # Сегодняшняя статистика
        today_frame = tk.Frame(self.root, bg='white', relief=tk.FLAT, 
                             highlightthickness=1, highlightbackground='#ddd')
        today_frame.pack(fill=tk.X, padx=20, pady=5)
        
        today_header = tk.Frame(today_frame, bg='white')
        today_header.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(today_header, text="📅 TODAY", font=('Arial', 10, 'bold'),
                bg='white', fg='#666').pack(side=tk.LEFT)
        
        self.today_total_label = tk.Label(today_header, text="00:00:00", 
                                         font=('Arial', 10, 'bold'), bg='white', fg='#333')
        self.today_total_label.pack(side=tk.RIGHT)
        
        # Список сессий
        sessions_container = tk.Frame(self.root, bg='white')
        sessions_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        # Скроллбар
        scrollbar = tk.Scrollbar(sessions_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.sessions_canvas = tk.Canvas(sessions_container, bg='white', 
                                        yscrollcommand=scrollbar.set, highlightthickness=0)
        self.sessions_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sessions_canvas.yview)
        
        self.sessions_frame = tk.Frame(self.sessions_canvas, bg='white')
        self.canvas_frame = self.sessions_canvas.create_window((0, 0), 
                                                               window=self.sessions_frame, 
                                                               anchor='nw')
        
        self.sessions_frame.bind('<Configure>', 
                                lambda e: self.sessions_canvas.configure(
                                    scrollregion=self.sessions_canvas.bbox('all')))
        
        # Нижняя панель - управление проектами
        bottom_frame = tk.Frame(self.root, bg='#f5f5f5', height=40)
        bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        new_project_btn = ttk.Button(bottom_frame, text="+ Новый проект", 
                                     style='ActionLarge.TButton',
                                     command=self.create_new_project)
        new_project_btn.pack(side=tk.LEFT, padx=5)
    
    def on_description_focus_in(self, event):
        """Очистка placeholder при фокусе"""
        if self.description_entry.get() == "Введите описание...":
            self.description_entry.delete(0, tk.END)
            self.description_entry.config(fg='#333')
    
    def on_description_focus_out(self, event):
        """Возврат placeholder при потере фокуса"""
        if not self.description_entry.get():
            self.description_entry.insert(0, "Введите описание...")
            self.description_entry.config(fg='#999')
    
    def load_projects(self):
        """Загружает список проектов"""
        projects = self.db.get_all_projects()
        project_names = ["Без проекта"] + [p['name'] for p in projects]
        self.project_combo['values'] = project_names
        if project_names:
            self.project_combo.current(0)
        # Если это первый запуск и нет ни одного проекта — предложить создать
        if hasattr(self, 'first_run') and self.first_run:
            if len(project_names) <= 1:
                # Открываем диалог после инициализации UI
                self.root.after(200, self.create_new_project)
            self.first_run = False
    
    def toggle_timer(self):
        """Запуск/остановка таймера"""
        if not self.timer_running:
            # Старт
            project_name = self.project_var.get()
            if not project_name or project_name == "Без проекта":
                messagebox.showwarning("Внимание", "Пожалуйста, выберите проект!")
                return
            
            projects = self.db.get_all_projects()
            project = next((p for p in projects if p['name'] == project_name), None)
            project_id = project['id'] if project else None
            
            description = self.description_entry.get()
            if description == "Введите описание...":
                description = ""
            
            self.current_session_id = self.db.start_session(project_id, description)
            self.start_time = datetime.now()
            self.elapsed_seconds = 0
            self.timer_running = True
            self.start_stop_btn.config(text="STOP")
            self.update_timer()
        else:
            # Стоп
            if self.current_session_id:
                self.db.stop_session(self.current_session_id)
                self.timer_running = False
                self.start_stop_btn.config(text="START")
                # Очищаем описание
                self.description_entry.delete(0, tk.END)
                self.description_entry.insert(0, "Введите описание...")
                self.description_entry.config(fg='#999')
                self.refresh_sessions()
                self.current_session_id = None
    
    def update_timer(self):
        """Обновляет отображение таймера"""
        if self.timer_running:
            elapsed = datetime.now() - self.start_time
            self.elapsed_seconds = int(elapsed.total_seconds())
            
            hours = self.elapsed_seconds // 3600
            minutes = (self.elapsed_seconds % 3600) // 60
            seconds = self.elapsed_seconds % 60
            
            self.timer_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)
    
    def format_duration(self, seconds):
        """Форматирует длительность в ЧЧ:ММ:СС"""
        if seconds is None:
            seconds = 0
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def continue_session(self, session):
        """Продолжает выбранную сессию"""
        if self.timer_running:
            messagebox.showwarning("Внимание", "Сначала остановите текущий таймер!")
            return
        
        # Устанавливаем проект
        if session['project_name']:
            self.project_var.set(session['project_name'])
        
        # Устанавливаем описание
        if session['description']:
            self.description_entry.delete(0, tk.END)
            self.description_entry.insert(0, session['description'])
            self.description_entry.config(fg='#333')
        
        # Запускаем таймер
        self.toggle_timer()
    
    def refresh_sessions(self):
        """Обновляет список сессий"""
        # Очищаем текущий список
        for widget in self.sessions_frame.winfo_children():
            widget.destroy()
        
        # Получаем сегодняшние сессии
        sessions = self.db.get_today_sessions()
        
        total_today = 0
        for session in sessions:
            duration = session['duration'] if session['duration'] else 0
            total_today += duration
            
            session_frame = tk.Frame(self.sessions_frame, bg='white', 
                                    relief=tk.FLAT, bd=0,
                                    highlightthickness=1, highlightbackground='#e0e0e0')
            session_frame.pack(fill=tk.X, pady=3, padx=5)
            
            # Описание или название проекта
            desc_text = session['description'] if session['description'] else session['project_name'] if session['project_name'] else 'Без названия'
            
            left_frame = tk.Frame(session_frame, bg='white')
            left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)
            
            tk.Label(left_frame, text=desc_text, font=('Arial', 11, 'bold'),
                    bg='white', fg='#333', anchor='w').pack(anchor='w')
            
            if session['project_name']:
                project_label = tk.Label(left_frame, 
                                        text=f"● {session['project_name']}", 
                                        font=('Arial', 9), bg='white', 
                                        fg=session['project_color'] if session['project_color'] else '#0088cc',
                                        anchor='w')
                project_label.pack(anchor='w')
            
            # Время и кнопка продолжить
            right_frame = tk.Frame(session_frame, bg='white')
            right_frame.pack(side=tk.RIGHT, padx=10, pady=8)
            
            start_dt = datetime.fromisoformat(session['start_time'])
            if session['end_time']:
                end_dt = datetime.fromisoformat(session['end_time'])
                time_text = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                
                # Кнопка продолжить (только для завершенных сессий)
                continue_btn = ttk.Button(right_frame, text="▶ Продолжить",
                                         style='Action.TButton',
                                         command=lambda s=session: self.continue_session(s))
                continue_btn.pack(side=tk.RIGHT, padx=(10, 0))
            else:
                time_text = f"{start_dt.strftime('%H:%M')} - Идет..."
            
            time_frame = tk.Frame(right_frame, bg='white')
            time_frame.pack(side=tk.RIGHT)
            
            tk.Label(time_frame, text=time_text, font=('Arial', 9),
                    bg='white', fg='#666').pack()
            tk.Label(time_frame, text=self.format_duration(duration), 
                    font=('Arial', 11, 'bold'), bg='white', fg='#333').pack()
        
        self.today_total_label.config(text=self.format_duration(total_today))
        
        # Обновляем недельную статистику
        week_total = self.db.get_week_total()
        self.week_total_label.config(text=self.format_duration(week_total))
    
    def create_new_project(self):
        """Создает новый проект"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый проект")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#f5f5f5')
        
        tk.Label(dialog, text="Название проекта:", font=('Arial', 11, 'bold'),
                bg='#f5f5f5', fg='#333').pack(pady=15)
        
        name_entry = tk.Entry(dialog, font=('Arial', 12), width=30, 
                             relief=tk.FLAT, bd=1, highlightthickness=1,
                             highlightbackground='#ddd')
        name_entry.pack(pady=5, padx=20)
        name_entry.focus()
        
        def save_project():
            name = name_entry.get().strip()
            if name:
                result = self.db.create_project(name)
                if result:
                    self.load_projects()
                    # Автоматически выбираем новый проект
                    self.project_var.set(name)
                    dialog.destroy()
                    messagebox.showinfo("Успех", f"Проект '{name}' создан!")
                else:
                    messagebox.showerror("Ошибка", "Проект с таким именем уже существует")
            else:
                messagebox.showwarning("Внимание", "Введите название проекта")
        
        btn_frame = tk.Frame(dialog, bg='#f5f5f5')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="Создать", command=save_project, 
                 bg='#0088cc', fg='#ffffff', font=('Arial', 11, 'bold'),
                 relief=tk.RAISED, bd=2, cursor='hand2', padx=20, pady=8,
                 activebackground='#0066aa', activeforeground='#ffffff').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                 bg='#999', fg='#ffffff', font=('Arial', 11, 'bold'),
                 relief=tk.RAISED, bd=2, cursor='hand2', padx=20, pady=8,
                 activebackground='#777', activeforeground='#ffffff').pack(side=tk.LEFT, padx=5)
        
        name_entry.bind('<Return>', lambda e: save_project())
    
    def refresh_all(self):
        """Обновляет все данные"""
        self.load_projects()
        self.refresh_sessions()
    
    def auto_refresh_data(self):
        """Автоматическое обновление данных каждые 5 секунд"""
        self.refresh_sessions()
        # Планируем следующее обновление через 5 секунд
        self.auto_refresh_id = self.root.after(5000, self.auto_refresh_data)
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        # Отменяем автообновление
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
        self.db.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
