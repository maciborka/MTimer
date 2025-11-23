# -*- coding: utf-8 -*-
# Нативное macOS приложение на PyObjC (AppKit)
# Использует существующую SQLite БД из database.py

from Cocoa import (
    NSApplication, NSApp, NSObject, NSWindow, NSButton, NSTextField,
    NSPopUpButton, NSTableView, NSScrollView, NSTableColumn, NSFont,
    NSMakeRect, NSTitledWindowMask, NSClosableWindowMask, NSResizableWindowMask,
    NSScreen, NSTimer, NSDate, NSTextAlignmentCenter, NSBezelStyleRounded,
    NSAlert, NSAlertStyleWarning, NSView, NSColor, NSMenu, NSMenuItem, NSImage,
    NSNotificationCenter, NSStatusBar, NSVariableStatusItemLength
)
from Foundation import NSLog, NSDateFormatter, NSDateComponentsFormatter, NSBundle, NSUserNotification, NSUserNotificationCenter, NSThread
import os
from PyObjCTools import AppHelper
from datetime import datetime
import objc

from database import Database
from localization import t, get_localization



# Имя приложения для меню и заголовков
APP_NAME = t('app_name')


class DeletableTableView(NSTableView):
    """Таблица, перехватывающая клавишу Delete для удаления строки."""
    def keyDown_(self, event):
        try:
            keyCode = event.keyCode()
        except Exception:
            keyCode = None
        # Delete (Backspace) = 51, Forward Delete = 117
        if keyCode in (51, 117):
            owner = getattr(self, 'owner', None)
            if owner is not None:
                try:
                    owner.deleteSession_(None)
                    return
                except Exception as e:
                    NSLog(f"Ошибка при удалении по клавише Delete: {e}")
        # Передаём обработку дальше по стандартной цепочке
        objc.super(DeletableTableView, self).keyDown_(event)


class TimeTrackerWindowController(NSObject):
    def init(self):
        self = objc.super(TimeTrackerWindowController, self).init()
        if self is None:
            return None
        self.db = Database()
        self.timer_running = False
        self.current_session_id = None
        self.start_time = None
        self.elapsed_seconds = 0
        self.update_timer_ref = None
        self.auto_refresh_ref = None
        self.projects_cache = []
        self.today_sessions = []  # Инициализируем пустой список для сессий
        self.current_filter = "week"  # По умолчанию показываем неделю
        self.selected_project_id = None  # Фильтр по проекту (None = все проекты)
        self.setupUI()
        return self

    def setupUI(self):
        # Создаем окно
        screen = NSScreen.mainScreen().frame()
        width, height = 900, 640
        x = (screen.size.width - width) / 2
        y = (screen.size.height - height) / 2
        style = NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height), style, 2, False
        )
        self.window.setTitle_(APP_NAME)
        
        # Устанавливаем минимальный размер окна
        self.window.setMinSize_((900, 640))
        
        # Устанавливаем делегат для обработки изменения размера и закрытия
        self.window.setDelegate_(self)
        
        # Предотвращаем освобождение окна при скрытии
        self.window.setReleasedWhenClosed_(False)
        
        # ВАЖНО: Устанавливаем appearance в nil для автоматической адаптации к системной теме
        try:
            self.window.setAppearance_(None)
        except Exception:
            pass

        content = self.window.contentView()
        content.setWantsLayer_(True)
        
        # Сохраняем константы для пересчета
        self.topBarHeight = 56
        self.cardHeight = 88
        
        # Верхняя синяя плашка (хедер)
        self.topBar = NSView.alloc().initWithFrame_(NSMakeRect(0, height - self.topBarHeight, width, self.topBarHeight))
        self.topBar.setWantsLayer_(True)
        self.topBar.layer().setBackgroundColor_(NSColor.colorWithSRGBRed_green_blue_alpha_(0.20, 0.52, 0.96, 1.0).CGColor())
        content.addSubview_(self.topBar)

        self.headerTitle = NSTextField.alloc().initWithFrame_(NSMakeRect(20, height - self.topBarHeight + (self.topBarHeight-22)/2, 300, 22))
        self.headerTitle.setStringValue_(APP_NAME)
        self.headerTitle.setBezeled_(False)
        self.headerTitle.setDrawsBackground_(False)
        self.headerTitle.setEditable_(False)
        self.headerTitle.setSelectable_(False)
        self.headerTitle.setFont_(NSFont.boldSystemFontOfSize_(16))
        self.headerTitle.setTextColor_(NSColor.whiteColor())
        content.addSubview_(self.headerTitle)

        # «Карточка» таймера с округленными углами - используем Box для автоматической адаптации
        cardY = height - self.topBarHeight - 20 - self.cardHeight
        
        try:
            from Cocoa import NSBox, NSBoxCustom
            self.timerCard = NSBox.alloc().initWithFrame_(NSMakeRect(20, cardY, width-40, self.cardHeight))
            self.timerCard.setBoxType_(NSBoxCustom)
            self.timerCard.setBorderType_(0)  # NoBorder
            self.timerCard.setTitlePosition_(0)  # NoTitle
            self.timerCard.setFillColor_(NSColor.controlBackgroundColor())
            self.timerCard.setCornerRadius_(12.0)
            self.timerCard.setContentViewMargins_((0, 0))
        except Exception as e:
            NSLog(f"Не удалось создать NSBox, используем NSView: {e}")
            self.timerCard = NSView.alloc().initWithFrame_(NSMakeRect(20, cardY, width-40, self.cardHeight))
            self.timerCard.setWantsLayer_(True)
            self.timerCard.layer().setCornerRadius_(12.0)
        
        content.addSubview_(self.timerCard)

        # Элементы внутри карточки
        rowY = (self.cardHeight - 28) / 2
        self.descriptionField = NSTextField.alloc().initWithFrame_(NSMakeRect(16, rowY, 360, 28))
        self.descriptionField.setPlaceholderString_(t('enter_description'))
        # Поле должно использовать системный цвет фона и текста
        try:
            self.descriptionField.setDrawsBackground_(True)
            self.descriptionField.setBackgroundColor_(NSColor.textBackgroundColor())
            self.descriptionField.setTextColor_(NSColor.textColor())
        except Exception:
            pass
        self.timerCard.addSubview_(self.descriptionField)

        self.projectPopup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(384, rowY, 200, 28), False)
        self.projectPopup.setTarget_(self)
        self.projectPopup.setAction_(objc.selector(self.projectSelected_, signature=b"v@:"))
        self.timerCard.addSubview_(self.projectPopup)

        self.addProjectBtn = NSButton.alloc().initWithFrame_(NSMakeRect(590, rowY, 35, 28))
        self.addProjectBtn.setTitle_("+")
        self.addProjectBtn.setBezelStyle_(NSBezelStyleRounded)
        self.addProjectBtn.setTarget_(self)
        self.addProjectBtn.setAction_(objc.selector(self.createProject_, signature=b"v@:"))
        self.timerCard.addSubview_(self.addProjectBtn)

        self.timerLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(self.timerCard.frame().size.width - 180 - 56, rowY, 120, 28))
        self.timerLabel.setStringValue_("00:00:00")
        self.timerLabel.setBezeled_(False)
        self.timerLabel.setDrawsBackground_(False)
        self.timerLabel.setEditable_(False)
        self.timerLabel.setSelectable_(False)
        self.timerLabel.setAlignment_(NSTextAlignmentCenter)
        self.timerLabel.setFont_(NSFont.boldSystemFontOfSize_(18))
        self.timerLabel.setTextColor_(NSColor.labelColor())  # Адаптивный цвет для таймера
        self.timerCard.addSubview_(self.timerLabel)

        # Круглая розовая кнопка Старт/Стоп
        btnSize = 44
        self.startStopBtn = NSButton.alloc().initWithFrame_(NSMakeRect(self.timerCard.frame().size.width - btnSize - 16, (self.cardHeight - btnSize)/2, btnSize, btnSize))
        self.startStopBtn.setBezelStyle_(0)  # borderless
        self.startStopBtn.setBordered_(False)
        self.startStopBtn.setWantsLayer_(True)
        self.startStopBtn.layer().setCornerRadius_(btnSize/2)
        self.startStopBtn.layer().setBackgroundColor_(NSColor.colorWithSRGBRed_green_blue_alpha_(1.0, 0.33, 0.55, 1.0).CGColor())
        try:
            self.startStopBtn.setContentTintColor_(NSColor.whiteColor())
        except Exception:
            pass
        self.startStopBtn.setFont_(NSFont.boldSystemFontOfSize_(16))
        self.startStopBtn.setTitle_("▶")
        self.startStopBtn.setTarget_(self)
        self.startStopBtn.setAction_(objc.selector(self.toggleTimer_, signature=b"v@:"))
        self.timerCard.addSubview_(self.startStopBtn)

        # Метки статистики и фильтры
        filterY = cardY - 30
        
        # Кнопки фильтра периода
        filterX = 20
        self.todayFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX, filterY, 80, 24))
        self.todayFilterBtn.setTitle_(t('today'))
        self.todayFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.todayFilterBtn.setTarget_(self)
        self.todayFilterBtn.setAction_(objc.selector(self.setFilterToday_, signature=b"v@:"))
        content.addSubview_(self.todayFilterBtn)
        
        self.weekFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX + 85, filterY, 80, 24))
        self.weekFilterBtn.setTitle_(t('week'))
        self.weekFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.weekFilterBtn.setTarget_(self)
        self.weekFilterBtn.setAction_(objc.selector(self.setFilterWeek_, signature=b"v@:"))
        content.addSubview_(self.weekFilterBtn)
        
        self.monthFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX + 170, filterY, 80, 24))
        self.monthFilterBtn.setTitle_(t('month'))
        self.monthFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.monthFilterBtn.setTarget_(self)
        self.monthFilterBtn.setAction_(objc.selector(self.setFilterMonth_, signature=b"v@:"))
        content.addSubview_(self.monthFilterBtn)
        
        # Поле общего времени
        self.weekTotalField = NSTextField.alloc().initWithFrame_(NSMakeRect(270, filterY + 0, 300, 20))
        self.weekTotalField.setStringValue_("ВСЕГО: 00:00:00")
        self.weekTotalField.setBezeled_(False)
        self.weekTotalField.setDrawsBackground_(False)
        self.weekTotalField.setEditable_(False)
        self.weekTotalField.setFont_(NSFont.boldSystemFontOfSize_(11))
        self.weekTotalField.setTextColor_(NSColor.labelColor())  # Адаптивный цвет текста
        content.addSubview_(self.weekTotalField)

        self.todayTotalField = NSTextField.alloc().initWithFrame_(NSMakeRect(width-200, filterY + 2, 160, 20))
        self.todayTotalField.setStringValue_("00:00:00")
        self.todayTotalField.setBezeled_(False)
        self.todayTotalField.setDrawsBackground_(False)
        self.todayTotalField.setEditable_(False)
        self.todayTotalField.setFont_(NSFont.boldSystemFontOfSize_(11))
        self.todayTotalField.setTextColor_(NSColor.secondaryLabelColor())  # Чуть светлее для secondary info
        content.addSubview_(self.todayTotalField)

        # Кнопка Продолжить (перемещаем выше таблицы, рядом с today total)
        continueButtonY = filterY
        self.continueBtn = NSButton.alloc().initWithFrame_(NSMakeRect(width-360, continueButtonY, 140, 24))
        self.continueBtn.setTitle_(t('continue'))
        self.continueBtn.setBezelStyle_(NSBezelStyleRounded)
        self.continueBtn.setTarget_(self)
        self.continueBtn.setAction_(objc.selector(self.continueSelected_, signature=b"v@:"))
        content.addSubview_(self.continueBtn)

        # Таблица с сессиями (увеличиваем отступ сверху для кнопки)
        tableTopMargin = 50  # отступ сверху под кнопку "Продолжить"
        tableY = 20
        tableHeight = cardY - 40 - tableTopMargin
        if tableHeight < 100:
            tableHeight = 100
        self.tableScroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, tableY, width-40, tableHeight))
        self.tableView = DeletableTableView.alloc().initWithFrame_(self.tableScroll.bounds())
        # Ссылка на контроллер для обработки Delete
        try:
            self.tableView.owner = self
        except Exception:
            pass

        col1 = NSTableColumn.alloc().initWithIdentifier_("desc")
        col1.setWidth_(width*0.45)
        col1.headerCell().setStringValue_(t('description_project'))
        self.tableView.addTableColumn_(col1)

        col2 = NSTableColumn.alloc().initWithIdentifier_("time")
        col2.setWidth_(width*0.25)
        col2.headerCell().setStringValue_(t('time'))
        self.tableView.addTableColumn_(col2)

        col3 = NSTableColumn.alloc().initWithIdentifier_("duration")
        col3.setWidth_(width*0.15)
        col3.headerCell().setStringValue_(t('duration'))
        self.tableView.addTableColumn_(col3)

        self.tableView.setDelegate_(self)
        self.tableView.setDataSource_(self)
        
        # Контекстное меню для удаления
        contextMenu = NSMenu.alloc().init()
        deleteItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            t('delete_session'), 
            objc.selector(self.deleteSession_, signature=b"v@:@"),
            ""
        )
        deleteItem.setTarget_(self)
        contextMenu.addItem_(deleteItem)
        self.tableView.setMenu_(contextMenu)
        
        # Настройка цветов таблицы для тёмного режима
        try:
            self.tableView.setBackgroundColor_(NSColor.controlBackgroundColor())
            # Цвет gridlines адаптивный
            self.tableView.setGridColor_(NSColor.separatorColor())
        except Exception:
            pass
        
        self.tableScroll.setDocumentView_(self.tableView)
        self.tableScroll.setHasVerticalScroller_(True)
        self.tableScroll.setDrawsBackground_(True)
        try:
            self.tableScroll.setBackgroundColor_(NSColor.controlBackgroundColor())
        except Exception:
            pass
        content.addSubview_(self.tableScroll)

        # Первичная загрузка
        self.reloadProjects()
        self.reloadSessions()
        
        # Проверяем незавершенные сессии и восстанавливаем таймер
        self._restoreActiveSession()

        # Таймеры
        self.update_timer_ref = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, objc.selector(self.tick_, signature=b"v@:"), None, True
        )
        self.auto_refresh_ref = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            5.0, self, objc.selector(self.autoRefresh_, signature=b"v@:"), None, True
        )

        self.window.makeKeyAndOrderFront_(None)

        # Начальное оформление кнопки Start/Stop
        self._updateStartStopAppearance()
        
        # Подписка на изменение темы оформления
        try:
            from Cocoa import NSNotificationCenter
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self, 
                objc.selector(self.themeChanged_, signature=b"v@:@"),
                "NSSystemColorsDidChangeNotification",
                None
            )
        except Exception as e:
            NSLog(f"Не удалось подписаться на изменение темы: {e}")
    
    def windowShouldClose_(self, sender):
        """Перехватываем закрытие окна - скрываем вместо закрытия"""
        self.window.orderOut_(None)
        return False
    
    def windowDidResize_(self, notification):
        """Обработчик изменения размера окна"""
        # Используем размер contentView, а не frame окна
        contentFrame = self.window.contentView().frame()
        width = contentFrame.size.width
        height = contentFrame.size.height
        
        try:
            # Обновляем topBar
            self.topBar.setFrame_(NSMakeRect(0, height - self.topBarHeight, width, self.topBarHeight))
            self.headerTitle.setFrame_(NSMakeRect(20, height - self.topBarHeight + (self.topBarHeight-22)/2, 300, 22))
            
            # Обновляем timerCard
            cardY = height - self.topBarHeight - 20 - self.cardHeight
            self.timerCard.setFrame_(NSMakeRect(20, cardY, width-40, self.cardHeight))
            
            # Обновляем элементы внутри карточки (адаптивная ширина)
            rowY = (self.cardHeight - 28) / 2
            self.descriptionField.setFrame_(NSMakeRect(16, rowY, 360, 28))
            self.projectPopup.setFrame_(NSMakeRect(384, rowY, 200, 28))
            self.addProjectBtn.setFrame_(NSMakeRect(590, rowY, 35, 28))
            
            # Таймер и кнопка старт/стоп справа
            cardWidth = width - 40
            self.timerLabel.setFrame_(NSMakeRect(cardWidth - 180 - 56, rowY, 120, 28))
            btnSize = 44
            self.startStopBtn.setFrame_(NSMakeRect(cardWidth - btnSize - 16, (self.cardHeight - btnSize)/2, btnSize, btnSize))
            
            # Фильтры и метки
            filterY = cardY - 30
            self.todayFilterBtn.setFrame_(NSMakeRect(20, filterY, 80, 24))
            self.weekFilterBtn.setFrame_(NSMakeRect(105, filterY, 80, 24))
            self.monthFilterBtn.setFrame_(NSMakeRect(190, filterY, 80, 24))
            self.weekTotalField.setFrame_(NSMakeRect(270, filterY, 300, 20))
            self.todayTotalField.setFrame_(NSMakeRect(width-200, filterY + 2, 160, 20))
            self.continueBtn.setFrame_(NSMakeRect(width-360, filterY, 140, 24))
            
            # Таблица - растягивается по высоте и ширине
            tableTopMargin = 50
            tableY = 20
            tableHeight = cardY - 40 - tableTopMargin
            if tableHeight < 100:
                tableHeight = 100
            self.tableScroll.setFrame_(NSMakeRect(20, tableY, width-40, tableHeight))
            
            # Обновляем ширину колонок таблицы пропорционально
            col1 = self.tableView.tableColumnWithIdentifier_("desc")
            col2 = self.tableView.tableColumnWithIdentifier_("time")
            col3 = self.tableView.tableColumnWithIdentifier_("duration")
            if col1:
                col1.setWidth_(width*0.45)
            if col2:
                col2.setWidth_(width*0.25)
            if col3:
                col3.setWidth_(width*0.15)
            
        except Exception as e:
            NSLog(f"Ошибка при изменении размера окна: {e}")
    
    def themeChanged_(self, notification):
        """Обработчик изменения системной темы"""
        NSLog("Обнаружено изменение темы, обновляем цвета...")
        try:
            # Обновляем цвет карточки - если это NSBox, используем setFillColor
            try:
                self.timerCard.setFillColor_(NSColor.controlBackgroundColor())
            except Exception:
                # Если это NSView с layer
                try:
                    self.timerCard.layer().setBackgroundColor_(NSColor.controlBackgroundColor().CGColor())
                except Exception:
                    pass
            
            # Обновляем поля ввода - используем более агрессивный подход
            try:
                # Сохраняем текущие значения
                descText = self.descriptionField.stringValue()
                selectedIdx = self.projectPopup.indexOfSelectedItem()
                
                # Пересоздаем цвета для поля ввода
                self.descriptionField.setBackgroundColor_(NSColor.textBackgroundColor())
                self.descriptionField.setTextColor_(NSColor.textColor())
                self.descriptionField.setStringValue_(descText)  # Восстанавливаем текст
                
                # Перерисовываем
                self.descriptionField.display()
                self.projectPopup.display()
                
                # Восстанавливаем выбор проекта
                if selectedIdx >= 0:
                    self.projectPopup.selectItemAtIndex_(selectedIdx)
            except Exception as e:
                NSLog(f"Ошибка обновления полей ввода: {e}")
            
            # Обновляем цвета текстовых меток
            self.timerLabel.setTextColor_(NSColor.labelColor())
            self.timerLabel.display()
            
            self.weekTotalField.setTextColor_(NSColor.labelColor())
            self.weekTotalField.display()
            
            self.todayTotalField.setTextColor_(NSColor.secondaryLabelColor())
            self.todayTotalField.display()
            
            # Обновляем фон и цвета таблицы
            self.tableView.setBackgroundColor_(NSColor.controlBackgroundColor())
            self.tableView.setGridColor_(NSColor.separatorColor())
            self.tableScroll.setBackgroundColor_(NSColor.controlBackgroundColor())
            self.tableScroll.setDrawsBackground_(True)
            
            # Принудительная перерисовка всех view
            self.timerCard.display()
            self.tableView.reloadData()
            self.tableView.display()
            self.tableScroll.display()
            
            # Обновляем кнопки
            for btn in [self.todayFilterBtn, self.weekFilterBtn, self.monthFilterBtn, self.continueBtn, self.addProjectBtn]:
                try:
                    btn.display()
                except Exception as e:
                    NSLog(f"Ошибка обновления кнопки: {e}")
            
            # Обновляем стоп/старт кнопку
            try:
                self.startStopBtn.display()
            except Exception:
                pass
            
            # Полная перерисовка окна
            self.window.contentView().setNeedsDisplay_(True)
            self.window.display()
            
            NSLog("Тема успешно обновлена")
        except Exception as e:
            NSLog(f"Ошибка при обновлении темы: {e}")

    # Табличные данные
    def numberOfRowsInTableView_(self, table):
        count = len(getattr(self, 'today_sessions', []))
        NSLog(f"numberOfRowsInTableView: возвращаем {count} строк")
        return count

    def tableView_objectValueForTableColumn_row_(self, table, col, row):
        if row >= len(self.today_sessions):
            NSLog(f"ОШИБКА: запрос строки {row}, но всего {len(self.today_sessions)} сессий")
            return ""
        session = self.today_sessions[row]
        ident = col.identifier()
        if ident == 'desc':
            desc = session['description'] or (session['project_name'] or t('no_name'))
            if session['project_name']:
                return f"{desc}\n• {session['project_name']}"
            return desc
        elif ident == 'time':
            start_dt = datetime.fromisoformat(session['start_time'])
            if session['end_time']:
                end_dt = datetime.fromisoformat(session['end_time'])
                return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
            else:
                return f"{start_dt.strftime('%H:%M')} - {t('running')}"
        elif ident == 'duration':
            d = session['duration'] or 0
            return self.formatDuration(d)
        return ''

    # Данные и действия
    def reloadProjects(self):
        """Перезагружает список проектов и сохраняет выбор по ID (а не по названию)."""
        self.projects_cache = self.db.get_all_projects()
        prev_selected_id = getattr(self, 'selected_project_id', None)
        self.projectPopup.removeAllItems()
        self.projectPopup.addItemWithTitle_(t('all_projects'))
        for p in self.projects_cache:
            rate_str = f" (${p['hourly_rate']:.0f}/ч)" if p['hourly_rate'] > 0 else ""
            self.projectPopup.addItemWithTitle_(f"{p['name']}{rate_str}")

        # Восстанавливаем выбор по ID
        if prev_selected_id is None:
            self.projectPopup.selectItemAtIndex_(0)
        else:
            # Индекс в popup = индекс в projects_cache + 1 (т.к. 0 — "Все проекты")
            idx_to_select = 0
            for i, p in enumerate(self.projects_cache, start=1):
                if p['id'] == prev_selected_id:
                    idx_to_select = i
                    break
            self.projectPopup.selectItemAtIndex_(idx_to_select)

    def reloadSessions(self):
        # Загружаем сессии в зависимости от выбранного фильтра и проекта
        if self.selected_project_id is not None:
            # Фильтр по проекту
            self.today_sessions = list(self.db.get_sessions_by_project(self.selected_project_id, self.current_filter))
            period_total = self.db.get_project_total(self.selected_project_id, self.current_filter)
            
            # Находим проект для отображения ставки
            project = next((p for p in self.projects_cache if p['id'] == self.selected_project_id), None)
            if self.current_filter == "today":
                period_label = t('today_label')
            elif self.current_filter == "week":
                period_label = t('week_label')
            else:
                period_label = t('month_label')
            
            # Добавляем стоимость если есть ставка
            if project and project['hourly_rate'] > 0:
                hours = period_total / 3600.0
                cost = hours * project['hourly_rate']
                period_label += f" (${cost:.2f})"
        else:
            # Все проекты
            if self.current_filter == "today":
                self.today_sessions = list(self.db.get_today_sessions())
                period_total = sum([(s['duration'] or 0) for s in self.today_sessions])
                period_label = t('today_label')
            elif self.current_filter == "week":
                self.today_sessions = list(self.db.get_week_sessions())
                period_total = self.db.get_week_total()
                period_label = t('week_label')
            else:  # month
                self.today_sessions = list(self.db.get_month_sessions())
                period_total = self.db.get_month_total()
                period_label = t('month_label')
        
        NSLog(f"reloadSessions: загружено {len(self.today_sessions)} сессий ({self.current_filter})")
        
        # Обновляем метки
        today_total = sum([(s['duration'] or 0) for s in self.today_sessions if 
                          datetime.fromisoformat(s['start_time']).date() == datetime.now().date()])
        self.todayTotalField.setStringValue_(self.formatDuration(today_total))
        self.weekTotalField.setStringValue_(f"{t('total')}: {self.formatDuration(period_total)}")
        
        self.tableView.reloadData()
        self._updateFilterButtons()
    
    def _updateFilterButtons(self):
        """Подсвечивает активный фильтр"""
        # Сбрасываем все кнопки
        try:
            from Cocoa import NSControlStateValueOn, NSControlStateValueOff
        except ImportError:
            from Cocoa import NSOnState as NSControlStateValueOn, NSOffState as NSControlStateValueOff
        
        self.todayFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "today" else NSControlStateValueOff)
        self.weekFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "week" else NSControlStateValueOff)
        self.monthFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "month" else NSControlStateValueOff)
    
    def setFilterToday_(self, _):
        self.current_filter = "today"
        self.reloadSessions()
    
    def setFilterWeek_(self, _):
        self.current_filter = "week"
        self.reloadSessions()
    
    def setFilterMonth_(self, _):
        self.current_filter = "month"
        self.reloadSessions()
    
    def projectSelected_(self, sender):
        """Обработчик выбора проекта в dropdown"""
        idx = self.projectPopup.indexOfSelectedItem()
        if idx == 0:
            # "Все проекты"
            self.selected_project_id = None
        elif idx > 0 and idx - 1 < len(self.projects_cache):
            self.selected_project_id = self.projects_cache[idx - 1]['id']
        else:
            self.selected_project_id = None
        
        NSLog(f"Выбран проект: {self.selected_project_id}")
        self.reloadSessions()
    
    def deleteSession_(self, sender):
        """Удаление выбранной сессии"""
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(getattr(self, 'today_sessions', [])):
            return
        
        session = self.today_sessions[row]
        session_id = session['id']
        
        # Показываем диалог подтверждения
        alert = NSAlert.alloc().init()
        alert.setMessageText_(t('delete_confirm_title'))
        alert.setInformativeText_(t('delete_confirm_message'))
        alert.addButtonWithTitle_(t('delete'))
        alert.addButtonWithTitle_(t('cancel'))
        alert.setAlertStyle_(NSAlertStyleWarning)
        
        response = alert.runModal()
        
        # NSAlertFirstButtonReturn = 1000 (Delete), NSAlertSecondButtonReturn = 1001 (Cancel)
        if response == 1000:  # Delete button
            if self.db.delete_session(session_id):
                NSLog(f"Сессия {session_id} удалена")
                # Если удалили активную сессию — сбросим состояние таймера
                try:
                    if getattr(self, 'current_session_id', None) == session_id:
                        self.timer_running = False
                        self.current_session_id = None
                        self.start_time = None
                        self._updateStartStopAppearance()
                        try:
                            NSApp.delegate().updateStatusItem()
                        except Exception:
                            pass
                except Exception:
                    pass
                self.reloadSessions()
            else:
                NSLog(f"Не удалось удалить сессию {session_id}")
    
    @objc.python_method
    def formatDuration(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def tick_(self, _):
        if self.timer_running and self.start_time is not None:
            now = datetime.now()
            elapsed = (now - self.start_time).total_seconds()
            self.timerLabel.setStringValue_(self.formatDuration(int(elapsed)))

            # Обновляем заголовок в статус-баре
            try:
                NSApp.delegate().updateStatusItem()
            except Exception:
                pass
            
            # Проверяем переход через полночь
            if self.start_time.date() != now.date():
                NSLog("Обнаружен переход через полночь! Автоматически останавливаем таймер.")
                # Останавливаем текущую сессию в 23:59:59 предыдущего дня
                if self.current_session_id:
                    end_of_day = self.start_time.replace(hour=23, minute=59, second=59)
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    duration = int((end_of_day - self.start_time).total_seconds())
                    cursor.execute('''
                        UPDATE time_sessions 
                        SET end_time = ?, duration = ?
                        WHERE id = ?
                    ''', (end_of_day.isoformat(), duration, self.current_session_id))
                    conn.commit()
                    
                    # Автоматически создаём новую сессию с началом в 00:00:00 нового дня
                    idx = self.projectPopup.indexOfSelectedItem()
                    project_id = None
                    if idx > 0 and idx-1 < len(self.projects_cache):
                        project_id = self.projects_cache[idx-1]['id']
                    
                    if project_id:
                        desc = self.descriptionField.stringValue().strip()
                        # Если описание пустое, берем последнее для проекта
                        if not desc:
                            desc = self.db.get_last_description_for_project(project_id)
                            self.descriptionField.setStringValue_(desc)
                        
                        start_of_new_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        cursor.execute('''
                            INSERT INTO time_sessions (project_id, description, start_time)
                            VALUES (?, ?, ?)
                        ''', (project_id, desc, start_of_new_day.isoformat()))
                        conn.commit()
                        self.current_session_id = cursor.lastrowid
                        self.start_time = start_of_new_day
                        NSLog(f"Создана новая сессия {self.current_session_id} с началом в {start_of_new_day}")
                        self.reloadSessions()

    def autoRefresh_(self, _):
        self.reloadSessions()

    def createProject_(self, _):
        # Alert с двумя полями: название и ставка
        alert = NSAlert.alloc().init()
        alert.setMessageText_(t('new_project'))
        alert.setInformativeText_(f"{t('project_name')}\n{t('hourly_rate')}")
        alert.addButtonWithTitle_(t('create'))
        alert.addButtonWithTitle_(t('cancel'))
        alert.setAlertStyle_(NSAlertStyleWarning)
        
        # Устанавливаем иконку приложения вместо Python
        try:
            appIcon = NSApp.applicationIconImage()
            if appIcon:
                alert.setIcon_(appIcon)
        except Exception:
            pass
        
        # Контейнер для полей
        accessoryView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 240, 60))
        
        nameLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 36, 80, 20))
        nameLabel.setStringValue_(t('project_name'))
        nameLabel.setBezeled_(False)
        nameLabel.setDrawsBackground_(False)
        nameLabel.setEditable_(False)
        accessoryView.addSubview_(nameLabel)
        
        nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(85, 36, 155, 24))
        accessoryView.addSubview_(nameField)
        
        rateLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 6, 80, 20))
        rateLabel.setStringValue_(t('hourly_rate'))
        rateLabel.setBezeled_(False)
        rateLabel.setDrawsBackground_(False)
        rateLabel.setEditable_(False)
        accessoryView.addSubview_(rateLabel)
        
        rateField = NSTextField.alloc().initWithFrame_(NSMakeRect(85, 6, 155, 24))
        rateField.setPlaceholderString_("0")
        accessoryView.addSubview_(rateField)
        
        alert.setAccessoryView_(accessoryView)
        resp = alert.runModal()
        
        # Возвращаем фокус окну и обновляем отображение
        self.window.makeKeyAndOrderFront_(None)
        self.tableView.setNeedsDisplay_(True)
        
        if resp == 1000:  # First button
            name = nameField.stringValue().strip()
            rate_str = rateField.stringValue().strip()
            hourly_rate = 0
            try:
                if rate_str:
                    hourly_rate = float(rate_str)
            except ValueError:
                hourly_rate = 0
            
            if name:
                res = self.db.create_project(name, hourly_rate=hourly_rate)
                if res:
                    self.reloadProjects()
                    # Выбираем созданный проект (с учетом новой метки со ставкой)
                    rate_display = f" (${hourly_rate:.0f}/ч)" if hourly_rate > 0 else ""
                    self.projectPopup.selectItemWithTitle_(f"{name}{rate_display}")

    def toggleTimer_(self, _):
        if not self.timer_running:
            # старт
            # Если выбрана строка в таблице — подставим проект и описание из неё
            try:
                row = self.tableView.selectedRow()
            except Exception:
                row = -1
            if row is not None and row >= 0 and row < len(getattr(self, 'today_sessions', [])):
                s = self.today_sessions[row]
                # Выберем проект в popup по идентификатору проекта (надёжнее, чем по названию)
                try:
                    sel_proj_id = s['project_id']
                except Exception:
                    sel_proj_id = None
                if sel_proj_id is not None:
                    # индекс 0 в popup — "Все проекты", поэтому +1
                    for idx_popup, p in enumerate(self.projects_cache, start=1):
                        if p['id'] == sel_proj_id:
                            self.projectPopup.selectItemAtIndex_(idx_popup)
                            break
                # Подставим описание, если есть
                try:
                    sel_desc = s['description']
                except Exception:
                    sel_desc = None
                if sel_desc:
                    self.descriptionField.setStringValue_(sel_desc)

            # Проверяем, был ли ранее выбран фильтр "Все проекты" (для автоприменения фильтра)
            was_all_projects = (self.selected_project_id is None)

            idx = self.projectPopup.indexOfSelectedItem()
            project_id = None
            if idx > 0 and idx-1 < len(self.projects_cache):
                project_id = self.projects_cache[idx-1]['id']
            if project_id is None:
                self.showWarning_(t('please_select_project'))
                return
            
            # Автоматически включаем фильтр по выбранному проекту ТОЛЬКО если ранее было выбрано "Все проекты"
            if was_all_projects:
                self.selected_project_id = project_id
                try:
                    self.reloadSessions()
                except Exception:
                    pass

            # Получаем описание
            desc = self.descriptionField.stringValue().strip()
            
            # Если описание пустое, берем последнее для этого проекта или "Программирование"
            if not desc:
                desc = self.db.get_last_description_for_project(project_id)
                self.descriptionField.setStringValue_(desc)
                NSLog(f"Автоматически подставлено описание: {desc}")
            
            self.current_session_id = self.db.start_session(project_id, desc)
            self.start_time = datetime.now()
            self.timer_running = True
            self.startStopBtn.setTitle_("■")
            self._updateStartStopAppearance()
            try:
                NSApp.delegate().updateStatusItem()
            except Exception:
                pass
        else:
            # стоп
            # Сохраняем информацию о задаче перед остановкой для уведомления
            try:
                idx = self.projectPopup.indexOfSelectedItem()
                project_name = "Без названия"
                if idx > 0 and idx-1 < len(self.projects_cache):
                    project_name = self.projects_cache[idx-1]['name']
                task_description = self.descriptionField.stringValue().strip()
                
                # Вычисляем время работы
                elapsed_time = ""
                if self.start_time:
                    elapsed_seconds = int((datetime.now() - self.start_time).total_seconds())
                    elapsed_time = self.formatDuration(elapsed_seconds)
            except Exception as e:
                NSLog(f"Error preparing stop notification: {e}")
                project_name = "Без названия"
                task_description = ""
                elapsed_time = ""
            
            if self.current_session_id:
                self.db.stop_session(self.current_session_id)
            self.timer_running = False
            self.start_time = None
            self.startStopBtn.setTitle_("▶")
            self._updateStartStopAppearance()
            self.descriptionField.setStringValue_("")
            self.reloadSessions()
            try:
                NSApp.delegate().updateStatusItem()
            except Exception:
                pass
            
            # Отправляем уведомление об остановке
            try:
                NSApp.delegate()._sendStopNotification(project_name, task_description, elapsed_time)
            except Exception as e:
                NSLog(f"Error sending stop notification: {e}")

    @objc.python_method
    def _updateStartStopAppearance(self):
        # Обновить цвет и иконку кнопки в зависимости от состояния
        if self.timer_running:
            # Стоп: насыщенно-розовый
            self.startStopBtn.layer().setBackgroundColor_(NSColor.colorWithSRGBRed_green_blue_alpha_(1.0, 0.25, 0.42, 1.0).CGColor())
        else:
            # Старт: более светлый розовый
            self.startStopBtn.layer().setBackgroundColor_(NSColor.colorWithSRGBRed_green_blue_alpha_(1.0, 0.33, 0.55, 1.0).CGColor())
    
    @objc.python_method
    def _restoreActiveSession(self):
        """Восстанавливает активную сессию при запуске приложения"""
        active = self.db.get_active_session()
        if active:
            NSLog(f"Найдена незавершенная сессия {active['id']}, восстанавливаем таймер")
            self.current_session_id = active['id']
            self.start_time = datetime.fromisoformat(active['start_time'])
            self.timer_running = True
            
            # Восстанавливаем описание и проект в UI
            if active['description']:
                self.descriptionField.setStringValue_(active['description'])
            
            if active['project_name']:
                # Ищем проект в списке (название может содержать ставку)
                for i in range(self.projectPopup.numberOfItems()):
                    title = self.projectPopup.itemAtIndex_(i).title()
                    if title.startswith(active['project_name']):
                        self.projectPopup.selectItemAtIndex_(i)
                        break
            
            # Обновляем кнопку
            self.startStopBtn.setTitle_("■")
            self._updateStartStopAppearance()
            
            NSLog(f"Таймер восстановлен, прошло времени: {(datetime.now() - self.start_time).total_seconds():.0f} секунд")
            try:
                NSApp.delegate().updateStatusItem()
            except Exception:
                pass

    def continueSelected_(self, _):
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(self.today_sessions):
            return
        if self.timer_running:
            self.showWarning_(t('stop_current_timer'))
            return
        s = self.today_sessions[row]
        # Выбираем проект по id, а не по названию
        try:
            proj_id = s['project_id']
        except Exception:
            proj_id = None
        if proj_id is not None:
            for idx_popup, p in enumerate(self.projects_cache, start=1):
                if p['id'] == proj_id:
                    self.projectPopup.selectItemAtIndex_(idx_popup)
                    break
        if s['description']:
            self.descriptionField.setStringValue_(s['description'])
        self.toggleTimer_(None)

    def showWarning_(self, text):
        alert = NSAlert.alloc().init()
        alert.setMessageText_(text)
        alert.addButtonWithTitle_(t('ok'))
        
        # Устанавливаем иконку приложения
        try:
            appIcon = NSApp.applicationIconImage()
            if appIcon:
                alert.setIcon_(appIcon)
        except Exception:
            pass
        
        alert.runModal()


class ProjectSettingsWindowController(NSObject):
    """Окно настроек проектов для редактирования имени и ставки"""
    def init(self):
        self = objc.super(ProjectSettingsWindowController, self).init()
        if self is None:
            return None
        self.db = Database()
        self.projects = []
        self.window = None
        self.tableView = None
        self.nameField = None
        self.rateField = None
        self.saveBtn = None
        return self
    
    def showWindow(self):
        if self.window is None:
            self.setupUI()
        self.reloadProjects()
        self.window.makeKeyAndOrderFront_(None)
    
    def setupUI(self):
        # Создаём окно
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        width = 500
        height = 400
        x = (screen_frame.size.width - width) / 2
        y = (screen_frame.size.height - height) / 2
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask,
            2,
            False
        )
        self.window.setTitle_(t('project_settings'))
        self.window.setReleasedWhenClosed_(False)
        
        content = self.window.contentView()
        
        # Таблица проектов (верхняя часть)
        tableY = 120
        tableHeight = height - tableY - 20
        scrollView = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, tableY, width-40, tableHeight))
        self.tableView = NSTableView.alloc().initWithFrame_(scrollView.bounds())
        
        col1 = NSTableColumn.alloc().initWithIdentifier_("name")
        col1.setWidth_((width-40) * 0.6)
        col1.headerCell().setStringValue_(t('project'))
        self.tableView.addTableColumn_(col1)
        
        col2 = NSTableColumn.alloc().initWithIdentifier_("rate")
        col2.setWidth_((width-40) * 0.3)
        col2.headerCell().setStringValue_(t('rate'))
        self.tableView.addTableColumn_(col2)
        
        self.tableView.setDelegate_(self)
        self.tableView.setDataSource_(self)
        
        scrollView.setDocumentView_(self.tableView)
        scrollView.setHasVerticalScroller_(True)
        content.addSubview_(scrollView)
        
        # Поля редактирования (нижняя часть)
        labelY = 80
        NSTextField.labelWithString_(t('project_name') + ":").setFrame_(NSMakeRect(20, labelY, 100, 20))
        
        label1 = NSTextField.alloc().initWithFrame_(NSMakeRect(20, labelY, 100, 20))
        label1.setStringValue_(t('project_name') + ":")
        label1.setBezeled_(False)
        label1.setDrawsBackground_(False)
        label1.setEditable_(False)
        content.addSubview_(label1)
        
        self.nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(130, labelY, width-260, 28))
        self.nameField.setPlaceholderString_(t('project_name'))
        content.addSubview_(self.nameField)
        
        label2 = NSTextField.alloc().initWithFrame_(NSMakeRect(20, labelY - 40, 100, 20))
        label2.setStringValue_(t('hourly_rate') + ":")
        label2.setBezeled_(False)
        label2.setDrawsBackground_(False)
        label2.setEditable_(False)
        content.addSubview_(label2)
        
        self.rateField = NSTextField.alloc().initWithFrame_(NSMakeRect(130, labelY - 40, 100, 28))
        self.rateField.setPlaceholderString_("0")
        content.addSubview_(self.rateField)
        
        # Кнопка Сохранить
        self.saveBtn = NSButton.alloc().initWithFrame_(NSMakeRect(width-130, labelY - 40, 100, 28))
        self.saveBtn.setTitle_(t('save'))
        self.saveBtn.setBezelStyle_(NSBezelStyleRounded)
        self.saveBtn.setTarget_(self)
        self.saveBtn.setAction_(objc.selector(self.saveProject_, signature=b"v@:"))
        content.addSubview_(self.saveBtn)
    
    def reloadProjects(self):
        self.projects = self.db.get_all_projects()
        if self.tableView:
            self.tableView.reloadData()
    
    # Методы делегата таблицы
    def numberOfRowsInTableView_(self, table):
        return len(self.projects)
    
    def tableView_objectValueForTableColumn_row_(self, table, col, row):
        if row >= len(self.projects):
            return ""
        project = self.projects[row]
        ident = col.identifier()
        if ident == 'name':
            return project['name']
        elif ident == 'rate':
            return f"${project['hourly_rate']:.0f}"
        return ''
    
    def tableViewSelectionDidChange_(self, notification):
        """Когда выбираем проект в таблице, загружаем его в поля редактирования"""
        row = self.tableView.selectedRow()
        if row >= 0 and row < len(self.projects):
            project = self.projects[row]
            self.nameField.setStringValue_(project['name'])
            self.rateField.setStringValue_(str(project['hourly_rate']))
    
    def saveProject_(self, sender):
        """Сохраняем изменения выбранного проекта"""
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(self.projects):
            return
        
        project = self.projects[row]
        new_name = self.nameField.stringValue().strip()
        try:
            new_rate = float(self.rateField.stringValue())
        except ValueError:
            new_rate = 0
        
        if not new_name:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('please_select_project'))
            alert.addButtonWithTitle_(t('ok'))
            alert.runModal()
            return
        
        # Обновляем в БД
        if self.db.update_project(project['id'], new_name, new_rate):
            NSLog(f"Проект {project['id']} обновлён: {new_name}, ${new_rate}/ч")
            self.reloadProjects()
            self.tableView.reloadData()
            # Обновим основное окно и статус-бар
            try:
                app = NSApp.delegate()
                if app and hasattr(app, 'controller') and app.controller is not None:
                    # Если редактировали текущий выбранный проект — сессии тоже обновим
                    try:
                        if getattr(app.controller, 'selected_project_id', None) == project['id']:
                            app.controller.reloadProjects()
                            app.controller.reloadSessions()
                        else:
                            app.controller.reloadProjects()
                    except Exception:
                        pass
                    try:
                        app.updateStatusItem()
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('create'))
            alert.setInformativeText_("Не удалось обновить проект")
            alert.addButtonWithTitle_(t('ok'))
            alert.runModal()


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self.controller = TimeTrackerWindowController.alloc().init()
        # ВАЖНО: Сохраняем сильную ссылку на окно, чтобы оно не освобождалось при закрытии
        self.mainWindow = self.controller.window
        # Окно настроек проектов
        self.settingsController = None
        # Меню приложения с Cmd+Q
        self.buildMenu()
        # Устанавливаем иконку дока, если доступна
        self._setDockIcon()
        # Создаем статус-иконку в меню-баре
        self._createStatusItem()
        # Инициализируем её отображение
        self.updateStatusItem()

    def applicationWillTerminate_(self, notification):
        try:
            self.controller.db.close()
        except Exception:
            pass

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        # Закрытие окна не завершает приложение - оно остаётся в статус-баре
        # Выход только через меню "Выйти" или Cmd+Q
        return False
    
    def applicationShouldHandleReopen_hasVisibleWindows_(self, app, flag):
        # Обработчик клика на иконку дока - показываем окно
        if hasattr(self, 'mainWindow') and self.mainWindow is not None:
            self.mainWindow.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
        return True

    @objc.python_method
    def buildMenu(self):
        try:
            # Переименуем приложение в меню (если возможно без бандла)
            try:
                bundle = NSBundle.mainBundle()
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info is not None:
                    info["CFBundleName"] = APP_NAME
                    info["CFBundleDisplayName"] = APP_NAME
                    info["NSApplicationName"] = APP_NAME
            except Exception as e:
                NSLog(f"Bundle rename error: {e}")

            # Модификаторы
            try:
                from Cocoa import NSEventModifierFlagCommand as COMMAND_MASK
            except Exception:
                from Cocoa import NSCommandKeyMask as COMMAND_MASK
            try:
                from Cocoa import NSEventModifierFlagOption as OPTION_MASK
            except Exception:
                from Cocoa import NSAlternateKeyMask as OPTION_MASK
            try:
                from Cocoa import NSEventModifierFlagShift as SHIFT_MASK
            except Exception:
                from Cocoa import NSShiftKeyMask as SHIFT_MASK

            mainMenu = NSMenu.alloc().init()

            # App menu
            appMenuItem = NSMenuItem.alloc().init()
            mainMenu.addItem_(appMenuItem)

            appMenu = NSMenu.alloc().init()
            aboutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{t('about')} {APP_NAME}", "orderFrontStandardAboutPanel:", ""
            )
            appMenu.addItem_(aboutItem)
            appMenu.addItem_(NSMenuItem.separatorItem())

            settingsItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('settings'), objc.selector(self.openSettings_, signature=b"v@:@"), ","
            )
            settingsItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            settingsItem.setTarget_(self)
            appMenu.addItem_(settingsItem)
            
            # Пункт меню Статистика
            statisticsItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('statistics'), objc.selector(self.openStatistics_, signature=b"v@:@"), "s"
            )
            statisticsItem.setKeyEquivalentModifierMask_(COMMAND_MASK | SHIFT_MASK)
            statisticsItem.setTarget_(self)
            appMenu.addItem_(statisticsItem)
            
            prefsItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('preferences'), "preferences:", ""
            )
            appMenu.addItem_(prefsItem)
            appMenu.addItem_(NSMenuItem.separatorItem())

            servicesMenu = NSMenu.alloc().initWithTitle_(t('services'))
            servicesItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('services'), None, "")
            appMenu.addItem_(servicesItem)
            appMenu.setSubmenu_forItem_(servicesMenu, servicesItem)
            NSApp.setServicesMenu_(servicesMenu)

            appMenu.addItem_(NSMenuItem.separatorItem())

            hideItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{t('hide')} {APP_NAME}", "hide:", "h"
            )
            hideItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            appMenu.addItem_((hideItem))

            hideOthers = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('hide_others'), "hideOtherApplications:", "h"
            )
            hideOthers.setKeyEquivalentModifierMask_(COMMAND_MASK | OPTION_MASK)
            appMenu.addItem_(hideOthers)

            showAll = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('show_all'), "unhideAllApplications:", ""
            )
            appMenu.addItem_(showAll)

            appMenu.addItem_(NSMenuItem.separatorItem())

            quitItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{t('quit')} {APP_NAME}", "terminate:", "q"
            )
            quitItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            appMenu.addItem_(quitItem)
            appMenuItem.setSubmenu_(appMenu)

            # Edit menu
            editMenuItem = NSMenuItem.alloc().init()
            mainMenu.addItem_(editMenuItem)
            editMenu = NSMenu.alloc().initWithTitle_(t('edit'))
            undoItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('undo'), "undo:", "z")
            undoItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            redoItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('redo'), "redo:", "Z")
            redoItem.setKeyEquivalentModifierMask_(COMMAND_MASK | SHIFT_MASK)
            cutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('cut'), "cut:", "x")
            cutItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            copyItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('copy'), "copy:", "c")
            copyItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            pasteItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('paste'), "paste:", "v")
            pasteItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            selectAllItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('select_all'), "selectAll:", "a")
            selectAllItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            for i in (undoItem, redoItem, NSMenuItem.separatorItem(), cutItem, copyItem, pasteItem, NSMenuItem.separatorItem(), selectAllItem):
                editMenu.addItem_(i)
            editMenuItem.setSubmenu_(editMenu)

            # Window menu
            windowMenuItem = NSMenuItem.alloc().init()
            mainMenu.addItem_(windowMenuItem)
            windowMenu = NSMenu.alloc().initWithTitle_(t('window'))
            minimizeItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('minimize'), "performMiniaturize:", "m")
            minimizeItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            zoomItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('zoom'), "performZoom:", "")
            closeItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('close'), "performClose:", "w")
            closeItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            for i in (minimizeItem, zoomItem, closeItem, NSMenuItem.separatorItem()):
                windowMenu.addItem_(i)
            bringAll = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(t('bring_all_to_front'), "arrangeInFront:", "")
            windowMenu.addItem_(bringAll)
            windowMenuItem.setSubmenu_(windowMenu)
            try:
                NSApp.setWindowsMenu_(windowMenu)
            except Exception:
                pass

            NSApp.setMainMenu_((mainMenu))
        except Exception as e:
            NSLog(f"Menu build error: {e}")

    def openSettings_(self, sender):
        """Открывает окно настроек проектов"""
        if self.settingsController is None:
            self.settingsController = ProjectSettingsWindowController.alloc().init()
        self.settingsController.showWindow()
        # После закрытия окна настроек обновляем основное окно
        try:
            self.controller.reloadProjects()
        except Exception:
            pass
    
    def openStatistics_(self, sender):
        """Відкриває вікно статистики"""
        try:
            import subprocess
            import sys
            import os
            
            # Запускаємо статистику в окремому процесі
            # Це дозволяє вікну працювати незалежно від основного застосунку
            script_dir = os.path.dirname(os.path.abspath(__file__))
            python_exec = sys.executable
            
            # Створюємо скрипт для запуску статистики
            stats_script = os.path.join(script_dir, 'show_stats.py')
            
            # Запускаємо в фоні
            subprocess.Popen([python_exec, stats_script], 
                           cwd=script_dir,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            
            NSLog("Statistics window launched in separate process")
                
        except Exception as e:
            NSLog(f"Statistics error: {e}")
            import traceback
            traceback.print_exc()
            from AppKit import NSAlert, NSAlertStyleWarning
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_(f"Помилка відображення статистики:\n{str(e)}")
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.runModal()
    
    @objc.python_method
    def _setDockIcon(self):
        try:
            base = os.path.dirname(__file__)
            candidates = [
                os.path.join(base, "assets", "app_icon.icns"),
                os.path.join(base, "assets", "app_icon.png"),
            ]
            for p in candidates:
                if os.path.exists(p):
                    img = NSImage.alloc().initWithContentsOfFile_(p)
                    if img:
                        NSApp.setApplicationIconImage_(img)
                        break
        except Exception as e:
            NSLog(f"Set dock icon error: {e}")

    # ===== Статус-бар (меню-бар) =====
    @objc.python_method
    def _createStatusItem(self):
        try:
            self.statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            button = self.statusItem.button()
            if button:
                button.setTitle_("⏱")

            # Меню статус-бара
            self.statusMenu = NSMenu.alloc().initWithTitle_(APP_NAME)

            showItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{t('show')} {APP_NAME}", objc.selector(self.showMainWindow_, signature=b"v@:"), ""
            )
            self.statusMenu.addItem_(showItem)

            self.statusMenu.addItem_(NSMenuItem.separatorItem())

            # Динамический пункт Старт/Стоп
            self.toggleItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('start'), objc.selector(self.toggleFromStatusBar_, signature=b"v@:"), ""
            )
            self.statusMenu.addItem_(self.toggleItem)

            self.statusMenu.addItem_(NSMenuItem.separatorItem())

            # Секция быстрого переключения между последними 3 задачами
            recentLabel = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('recent_tasks'), None, ""
            )
            recentLabel.setEnabled_(False)
            self.statusMenu.addItem_(recentLabel)
            
            # Создаем 3 пункта меню для последних задач (будут обновляться динамически)
            self.recentTaskItems = []
            for i in range(3):
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"Задача {i+1}", objc.selector(self.switchToTask_, signature=b"v@:@"), ""
                )
                item.setTag_(i)
                self.statusMenu.addItem_(item)
                self.recentTaskItems.append(item)
            
            self.statusMenu.addItem_(NSMenuItem.separatorItem())

            quitItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('quit'), "terminate:", "q"
            )
            self.statusMenu.addItem_(quitItem)

            self.statusItem.setMenu_(self.statusMenu)
            
            # Инициализируем список последних задач
            self._updateRecentTasksMenu()
            
        except Exception as e:
            NSLog(f"Create status item error: {e}")

    def showMainWindow_(self, _):
        try:
            # Показываем окно из сохранённой ссылки
            if hasattr(self, 'mainWindow') and self.mainWindow is not None:
                self.mainWindow.makeKeyAndOrderFront_(None)
                # Активируем приложение
                NSApp.activateIgnoringOtherApps_(True)
        except Exception as e:
            NSLog(f"Error showing main window: {e}")

    def toggleFromStatusBar_(self, _):
        try:
            # Если таймер остановлен, пытаемся запустить последнюю задачу
            if not getattr(self.controller, 'timer_running', False):
                self._startLastTask()
            else:
                # Останавливаем текущий таймер
                self.controller.toggleTimer_(None)
        except Exception as e:
            NSLog(f"Toggle from status bar error: {e}")
    
    @objc.python_method
    def _startLastTask(self):
        """Запускает таймер для последнего задания с уведомлением"""
        try:
            # Получаем последнюю сессию из БД
            sessions = list(self.controller.db.get_week_sessions())
            if not sessions:
                NSLog("Нет предыдущих задач для продолжения")
                return
            
            last_session = sessions[0]
            project_id = last_session['project_id']
            description = last_session['description'] or ''
            project_name = last_session['project_name'] or 'Без названия'
            
            # Выбираем проект в UI
            for idx_popup, p in enumerate(self.controller.projects_cache, start=1):
                if p['id'] == project_id:
                    self.controller.projectPopup.selectItemAtIndex_(idx_popup)
                    break
            
            # Подставляем описание
            if description:
                self.controller.descriptionField.setStringValue_(description)
            
            # Запускаем таймер
            self.controller.toggleTimer_(None)
            
            # Отправляем системное уведомление
            self._sendNotification(project_name, description)
            
        except Exception as e:
            NSLog(f"Error starting last task: {e}")
    
    @objc.python_method
    def _sendNotification(self, project_name, task_description):
        """Отправляет системное уведомление о запуске таймера"""
        try:
            notification = NSUserNotification.alloc().init()
            notification.setTitle_(f"⏱ {APP_NAME} - {t('timer_started')}")
            notification.setSubtitle_(project_name)
            notification.setInformativeText_(task_description or t('no_description'))
            
            # Устанавливаем иконку приложения
            try:
                appIcon = NSApp.applicationIconImage()
                if appIcon:
                    notification.setContentImage_(appIcon)
            except Exception as e:
                NSLog(f"Could not set notification icon: {e}")
            
            # Отправляем уведомление
            center = NSUserNotificationCenter.defaultUserNotificationCenter()
            center.deliverNotification_(notification)
            
        except Exception as e:
            NSLog(f"Error sending notification: {e}")
    
    @objc.python_method
    def _sendStopNotification(self, project_name, task_description, elapsed_time):
        """Отправляет системное уведомление об остановке таймера"""
        try:
            notification = NSUserNotification.alloc().init()
            notification.setTitle_(f"✓ {APP_NAME} - {t('timer_stopped')}")
            notification.setSubtitle_(f"{project_name} • {elapsed_time}")
            notification.setInformativeText_(task_description or t('no_description'))
            
            # Устанавливаем иконку приложения
            try:
                appIcon = NSApp.applicationIconImage()
                if appIcon:
                    notification.setContentImage_(appIcon)
            except Exception as e:
                NSLog(f"Could not set notification icon: {e}")
            
            # Отправляем уведомление
            center = NSUserNotificationCenter.defaultUserNotificationCenter()
            center.deliverNotification_(notification)
            
        except Exception as e:
            NSLog(f"Error sending stop notification: {e}")

    def switchToTask_(self, sender):
        """Переключает таймер на выбранную задачу из последних 3"""
        try:
            task_index = sender.tag()
            sessions = list(self.controller.db.get_week_sessions())
            
            if task_index >= len(sessions):
                NSLog(f"Task index {task_index} out of range")
                return
            
            selected_session = sessions[task_index]
            project_id = selected_session['project_id']
            description = selected_session['description'] or ''
            project_name = selected_session['project_name'] or 'Без названия'
            
            # Если таймер запущен - останавливаем текущую сессию
            was_running = getattr(self.controller, 'timer_running', False)
            if was_running:
                if self.controller.current_session_id:
                    self.controller.db.stop_session(self.controller.current_session_id)
                self.controller.timer_running = False
                self.controller.start_time = None
            
            # Выбираем проект в UI
            for idx_popup, p in enumerate(self.controller.projects_cache, start=1):
                if p['id'] == project_id:
                    self.controller.projectPopup.selectItemAtIndex_(idx_popup)
                    break
            
            # Подставляем описание
            if description:
                self.controller.descriptionField.setStringValue_(description)
            
            # Запускаем новый таймер (только если был запущен ранее или явно кликнули)
            if was_running or True:  # Всегда запускаем
                self.controller.toggleTimer_(None)
                
                # Отправляем уведомление о переключении
                self._sendNotification(project_name, description)
            
            NSLog(f"Switched to task: {project_name} - {description}")
            
        except Exception as e:
            NSLog(f"Error switching task: {e}")
    
    @objc.python_method
    def _updateRecentTasksMenu(self):
        """Обновляет список последних 3 задач в меню"""
        try:
            sessions = list(self.controller.db.get_week_sessions())
            
            for i, item in enumerate(self.recentTaskItems):
                if i < len(sessions):
                    session = sessions[i]
                    project_name = session['project_name'] or t('no_name')
                    description = session['description'] or t('no_description')
                    
                    # Обрезаем длинные названия
                    if len(description) > 30:
                        description = description[:27] + "..."
                    
                    item.setTitle_(f"▸ {project_name}: {description}")
                    item.setEnabled_(True)
                else:
                    item.setTitle_(f"—")
                    item.setEnabled_(False)
                    
        except Exception as e:
            NSLog(f"Error updating recent tasks menu: {e}")

    @objc.python_method
    def updateStatusItem(self):
        try:
            button = self.statusItem.button() if hasattr(self, 'statusItem') else None
            if not button:
                return
            if getattr(self.controller, 'timer_running', False) and getattr(self.controller, 'start_time', None) is not None:
                secs = int((datetime.now() - self.controller.start_time).total_seconds())
                title = self.controller.formatDuration(secs)
                button.setTitle_(title)
                if hasattr(self, 'toggleItem') and self.toggleItem is not None:
                    self.toggleItem.setTitle_(t('stop'))
            else:
                button.setTitle_("⏱")
                if hasattr(self, 'toggleItem') and self.toggleItem is not None:
                    self.toggleItem.setTitle_(t('start'))
            
            # Обновляем список последних задач при каждом обновлении статус-бара
            try:
                self._updateRecentTasksMenu()
            except Exception:
                pass
                
        except Exception as e:
            NSLog(f"Update status item error: {e}")


def main():
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()
