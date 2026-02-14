# -*- coding: utf-8 -*-
# Нативное macOS приложение на PyObjC (AppKit)
# Использует существующую SQLite БД из database.py

from Cocoa import (
    NSApplication, NSApp, NSObject, NSWindow, NSButton, NSTextField,
    NSPopUpButton, NSTableView, NSScrollView, NSTableColumn, NSFont,
    NSMakeRect, NSTitledWindowMask, NSClosableWindowMask, NSResizableWindowMask,
    NSScreen, NSTimer, NSDate, NSTextAlignmentCenter, NSBezelStyleRounded,
    NSAlert, NSAlertStyleWarning, NSAlertStyleInformational, NSView, NSColor, 
    NSMenu, NSMenuItem, NSImage, NSNotificationCenter, NSStatusBar, 
    NSVariableStatusItemLength, NSSavePanel, NSModalResponseOK, NSTabView,
    NSTabViewItem, NSStackView, NSBox, NSDatePicker
)
from Foundation import NSLog, NSDateFormatter, NSDateComponentsFormatter, NSBundle, NSUserNotification, NSUserNotificationCenter, NSThread, NSString, NSUserDefaults
import os
import sys
from PyObjCTools import AppHelper
from datetime import datetime
import objc

from database import Database
from localization import t, get_localization

# DEV mode: упрощённый запуск из исходников (без статус-бара и уведомлений)
# Автоматически включается при запуске через python напрямую (не из .app бандла)
def _is_running_from_bundle():
    """Проверяет, запущено ли приложение из .app бандла"""
    return '.app/Contents/' in sys.executable or getattr(sys, 'frozen', False)

DEV_MODE = not _is_running_from_bundle()

# Flipped контейнер для корректной вертикальной разметки сверху вниз
class FlippedView(NSView):
    def isFlipped(self):
        return True


# Кнопка удаления с hover эффектом
class HoverDeleteButton(NSButton):
    def initWithFrame_(self, frame):
        self = objc.super(HoverDeleteButton, self).initWithFrame_(frame)
        if self is None:
            return None
        
        # Создаём tracking area для отслеживания мыши
        trackingArea = objc.lookUpClass('NSTrackingArea').alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            0x01 | 0x80 | 0x100,  # NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect
            self,
            None
        )
        self.addTrackingArea_(trackingArea)
        
        return self
    
    def mouseEntered_(self, event):
        """При наведении - красный цвет"""
        self.setContentTintColor_(NSColor.colorWithRed_green_blue_alpha_(0.95, 0.26, 0.21, 1.0))
        self.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.95, 0.26, 0.21, 0.15).CGColor())
    
    def mouseExited_(self, event):
        """При уходе мыши - серый цвет"""
        self.setContentTintColor_(NSColor.colorWithRed_green_blue_alpha_(0.6, 0.6, 0.6, 0.8))
        self.layer().setBackgroundColor_(NSColor.colorWithWhite_alpha_(0.95, 0.7).CGColor())


# Функция для получения базового пути (работает и в .app и в исходниках)
def _get_base_dir():
    """Возвращает базовую директорию приложения"""
    import sys
    import os
    if getattr(sys, 'frozen', False):
        # Запущены из .app bundle
        return os.environ.get('RESOURCEPATH', os.path.dirname(os.path.abspath(sys.executable)))
    else:
        # Запущены из исходников
        return os.path.dirname(os.path.abspath(__file__ if '__file__' in globals() else sys.argv[0]))



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
        self.hourly_reminder_ref = None  # Таймер для часовых напоминаний
        self.projects_cache = []
        self.today_sessions = []  # Инициализируем пустой список для сессий
        self.current_filter = "week"  # По умолчанию показываем неделю
        self.selected_project_id = None  # Фильтр по проекту (None = все проекты)
        self.selected_session_id = None  # Выделенная сессия для удаления/подсветки
        # НЕ ВЫЗЫВАЕМ setupUI здесь - его вызовет AppDelegate после запуска приложения
        return self

    def setupUI(self):
        NSLog("=== setupUI: Starting ===")
        # Создаем окно
        NSLog("=== setupUI: Getting main screen ===")
        screen = NSScreen.mainScreen().frame()
        NSLog(f"=== setupUI: Screen size: {screen.size.width} x {screen.size.height} ===")
        width, height = 900, 640
        x = (screen.size.width - width) / 2
        y = (screen.size.height - height) / 2
        NSLog(f"=== setupUI: Window position: {x}, {y} ===")
        style = NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask
        NSLog("=== setupUI: Creating window ===")
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height), style, 2, False
        )
        NSLog("=== setupUI: Window created ===")
        self.window.setTitle_(APP_NAME)
        
        # Устанавливаем иконку окна - ВРЕМЕННО ОТКЛЮЧЕНО из-за bus error
        # NSLog("=== setupUI: Setting window icon ===")
        # try:
        #     self._setWindowIcon(self.window)
        #     NSLog("=== setupUI: Window icon set successfully ===")
        # except Exception as e:
        #     NSLog(f"=== setupUI: Window icon error: {e} ===")
        
        # Устанавливаем минимальный размер окна
        self.window.setMinSize_((900, 640))
        
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
        self.addProjectBtn.setButtonType_(1)  # NSMomentaryLightButton
        self.addProjectBtn.setTarget_(self)
        try:
            # Спробуємо створити селектор
            selector = objc.selector(self.createProject_, signature=b"v@:")
            NSLog(f"=== Selector created: {selector} ===")
            self.addProjectBtn.setAction_(selector)
            NSLog("=== Action set successfully ===")
        except Exception as e:
            NSLog(f"=== ERROR setting action: {e} ===")
            import traceback
            traceback.print_exc()
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
        
        # Кнопка "Свой период" - ПЕРВАЯ
        self.customFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX, filterY, 110, 24))
        self.customFilterBtn.setTitle_(t('custom_period'))
        self.customFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.customFilterBtn.setButtonType_(6)  # NSPushOnPushOffButton
        self.customFilterBtn.setTarget_(self)
        self.customFilterBtn.setAction_(objc.selector(self.setFilterCustom_, signature=b"v@:"))
        content.addSubview_(self.customFilterBtn)
        
        self.todayFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX + 115, filterY, 80, 24))
        self.todayFilterBtn.setTitle_(t('today'))
        self.todayFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.todayFilterBtn.setButtonType_(6)  # NSPushOnPushOffButton - toggle button поведение
        self.todayFilterBtn.setTarget_(self)
        self.todayFilterBtn.setAction_(objc.selector(self.setFilterToday_, signature=b"v@:"))
        content.addSubview_(self.todayFilterBtn)
        
        self.weekFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX + 200, filterY, 80, 24))
        self.weekFilterBtn.setTitle_(t('week'))
        self.weekFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.weekFilterBtn.setButtonType_(6)  # NSPushOnPushOffButton
        self.weekFilterBtn.setTarget_(self)
        self.weekFilterBtn.setAction_(objc.selector(self.setFilterWeek_, signature=b"v@:"))
        content.addSubview_(self.weekFilterBtn)
        
        self.monthFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX + 285, filterY, 80, 24))
        self.monthFilterBtn.setTitle_(t('month'))
        self.monthFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.monthFilterBtn.setButtonType_(6)  # NSPushOnPushOffButton
        self.monthFilterBtn.setTarget_(self)
        self.monthFilterBtn.setAction_(objc.selector(self.setFilterMonth_, signature=b"v@:"))
        content.addSubview_(self.monthFilterBtn)
        
        # Поля выбора дат (по умолчанию скрыты) - размещаются НИЖЕ кнопки
        customDateY = filterY - 60
        
        # Метка "С:"
        self.fromDateLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(filterX, customDateY, 25, 20))
        self.fromDateLabel.setStringValue_(t('from_date'))
        self.fromDateLabel.setBezeled_(False)
        self.fromDateLabel.setDrawsBackground_(False)
        self.fromDateLabel.setEditable_(False)
        self.fromDateLabel.setHidden_(True)
        content.addSubview_(self.fromDateLabel)
        
        # NSDatePicker для выбора даты "от"
        from datetime import datetime, timedelta
        self.fromDatePicker = NSDatePicker.alloc().initWithFrame_(NSMakeRect(filterX + 30, customDateY - 2, 140, 24))
        self.fromDatePicker.setDatePickerStyle_(0)  # NSDatePickerStyleTextFieldAndStepper
        self.fromDatePicker.setDatePickerElements_(224)  # 0x00e0 = NSYearMonthDayDatePickerElementFlag
        default_from_date = datetime.now() - timedelta(days=30)
        self.fromDatePicker.setDateValue_(default_from_date)
        self.fromDatePicker.setHidden_(True)
        content.addSubview_(self.fromDatePicker)
        
        # Метка "По:"
        self.toDateLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(filterX + 180, customDateY, 25, 20))
        self.toDateLabel.setStringValue_(t('to_date'))
        self.toDateLabel.setBezeled_(False)
        self.toDateLabel.setDrawsBackground_(False)
        self.toDateLabel.setEditable_(False)
        self.toDateLabel.setHidden_(True)
        content.addSubview_(self.toDateLabel)
        
        # NSDatePicker для выбора даты "до"
        self.toDatePicker = NSDatePicker.alloc().initWithFrame_(NSMakeRect(filterX + 210, customDateY - 2, 140, 24))
        self.toDatePicker.setDatePickerStyle_(0)  # NSDatePickerStyleTextFieldAndStepper
        self.toDatePicker.setDatePickerElements_(224)  # 0x00e0 = NSYearMonthDayDatePickerElementFlag
        self.toDatePicker.setDateValue_(datetime.now())
        self.toDatePicker.setHidden_(True)
        content.addSubview_(self.toDatePicker)
        
        # Кнопка "Применить"
        self.applyCustomFilterBtn = NSButton.alloc().initWithFrame_(NSMakeRect(filterX + 360, customDateY - 2, 80, 24))
        self.applyCustomFilterBtn.setTitle_(t('apply'))
        self.applyCustomFilterBtn.setBezelStyle_(NSBezelStyleRounded)
        self.applyCustomFilterBtn.setTarget_(self)
        self.applyCustomFilterBtn.setAction_(objc.selector(self.applyCustomFilter_, signature=b"v@:"))
        self.applyCustomFilterBtn.setHidden_(True)
        content.addSubview_(self.applyCustomFilterBtn)
        
        # Поле общего времени
        self.weekTotalField = NSTextField.alloc().initWithFrame_(NSMakeRect(390, filterY + 0, 300, 20))
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
        self.continueBtn.setButtonType_(1)  # NSMomentaryLightButton - стандартная интерактивная кнопка
        self.continueBtn.setTarget_(self)
        self.continueBtn.setAction_(objc.selector(self.continueSelected_, signature=b"v@:"))
        content.addSubview_(self.continueBtn)

        # Замість таблиці - ScrollView з StackView для списку сесій
        tableTopMargin = 80
        tableY = 20
        tableHeight = cardY - 40 - tableTopMargin
        if tableHeight < 100:
            tableHeight = 100
        
        self.sessionsScroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, tableY, width-40, tableHeight))
        self.sessionsScroll.setHasVerticalScroller_(True)
        self.sessionsScroll.setAutohidesScrollers_(True)
        self.sessionsScroll.setDrawsBackground_(True)
        self.sessionsScroll.setBackgroundColor_(NSColor.controlBackgroundColor())
        
        # Контейнер для списка сессий (FlippedView: начало координат сверху)
        self.sessionsStack = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, width-40, 100))
        # self.sessionsStack.setOrientation_(1)  # 1 = vertical
        # self.sessionsStack.setAlignment_(3)  # 3 = leading/left
        # self.sessionsStack.setSpacing_(8)
        
        self.sessionsScroll.setDocumentView_(self.sessionsStack)
        content.addSubview_(self.sessionsScroll)

        
        # Устанавливаем делегат ПОСЛЕ создания всех элементов
        self.window.setDelegate_(self)

        # Первичная загрузка
        self.reloadProjects()
        self.reloadSessions()
        
        # ТЕСТ: Перевіримо чи існує метод createProject_
        NSLog(f"=== Testing createProject_ method exists: {hasattr(self, 'createProject_')} ===")
        if hasattr(self, 'createProject_'):
            NSLog("=== createProject_ method found ===")
        else:
            NSLog("=== ERROR: createProject_ method NOT FOUND ===")
        
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
        # Проверяем что все элементы уже созданы
        if not hasattr(self, 'sessionsScroll'):
            return
            
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
            filterX = 20
            
            # Кнопки фильтра периода
            self.customFilterBtn.setFrame_(NSMakeRect(filterX, filterY, 110, 24))
            self.todayFilterBtn.setFrame_(NSMakeRect(filterX + 115, filterY, 80, 24))
            self.weekFilterBtn.setFrame_(NSMakeRect(filterX + 200, filterY, 80, 24))
            self.monthFilterBtn.setFrame_(NSMakeRect(filterX + 285, filterY, 80, 24))
            
            # Элементы DatePicker для кастомного периода
            customDateY = filterY - 60
            self.fromDateLabel.setFrame_(NSMakeRect(filterX, customDateY, 25, 20))
            self.fromDatePicker.setFrame_(NSMakeRect(filterX + 30, customDateY - 2, 140, 24))
            self.toDateLabel.setFrame_(NSMakeRect(filterX + 180, customDateY, 25, 20))
            self.toDatePicker.setFrame_(NSMakeRect(filterX + 210, customDateY - 2, 140, 24))
            self.applyCustomFilterBtn.setFrame_(NSMakeRect(filterX + 360, customDateY - 2, 80, 24))
            
            # Поля с общим временем и кнопки
            self.weekTotalField.setFrame_(NSMakeRect(390, filterY, 300, 20))
            self.todayTotalField.setFrame_(NSMakeRect(width-200, filterY + 2, 160, 20))
            self.continueBtn.setFrame_(NSMakeRect(width-360, filterY, 140, 24))
            self.statisticsBtn.setFrame_(NSMakeRect(20, filterY - 30, 120, 24))
            
            # ScrollView с сессиями - растягивается по высоте и ширине
            tableTopMargin = 80  # Увеличили отступ для кнопки статистики
            tableY = 20
            tableHeight = cardY - 40 - tableTopMargin
            if tableHeight < 100:
                tableHeight = 100
            self.sessionsScroll.setFrame_(NSMakeRect(20, tableY, width-40, tableHeight))
            
            # Таблицы больше нет, используем StackView
            # col1 = self.tableView.tableColumnWithIdentifier_("desc")
            # col2 = self.tableView.tableColumnWithIdentifier_("time")
            # col3 = self.tableView.tableColumnWithIdentifier_("duration")
            # if col1:
            #     col1.setWidth_(width*0.45)
            # if col2:
            #     col2.setWidth_(width*0.25)
            # if col3:
            #     col3.setWidth_(width*0.15)
            
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
            
            # Обновляем фон ScrollView
            self.sessionsScroll.setBackgroundColor_(NSColor.controlBackgroundColor())
            self.sessionsScroll.setDrawsBackground_(True)
            
            # Принудительная перерисовка всех view
            self.timerCard.display()
            self.updateSessionsList()  # Перерисовываем список сессий
            self.sessionsScroll.display()
            
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
            if self.current_filter == "custom":
                # Custom период - используем диапазон дат
                from_date = getattr(self, 'custom_from_date', None)
                to_date = getattr(self, 'custom_to_date', None)
                if from_date and to_date:
                    self.today_sessions = [dict(row) for row in self.db.get_sessions_in_range(from_date, to_date + ' 23:59:59')]
                    self.today_sessions = [s for s in self.today_sessions if s['project_id'] == self.selected_project_id]
                    period_total = sum([(s['duration'] or 0) for s in self.today_sessions])
                    period_label = f"{from_date} - {to_date}"
                else:
                    self.today_sessions = []
                    period_total = 0
                    period_label = t('custom_period')
            else:
                self.today_sessions = [dict(row) for row in self.db.get_sessions_by_project(self.selected_project_id, self.current_filter)]
                period_total = self.db.get_project_total(self.selected_project_id, self.current_filter)
                
                if self.current_filter == "today":
                    period_label = t('today_label')
                elif self.current_filter == "week":
                    period_label = t('week_label')
                else:
                    period_label = t('month_label')
            
            # Находим проект для отображения ставки
            project = next((p for p in self.projects_cache if p['id'] == self.selected_project_id), None)
            
            # Добавляем стоимость если есть ставка
            if project and project['hourly_rate'] > 0:
                hours = period_total / 3600.0
                cost = hours * project['hourly_rate']
                period_label += f" (${cost:.2f})"
        else:
            # Все проекты
            if self.current_filter == "custom":
                # Custom период
                from_date = getattr(self, 'custom_from_date', None)
                to_date = getattr(self, 'custom_to_date', None)
                if from_date and to_date:
                    self.today_sessions = [dict(row) for row in self.db.get_sessions_in_range(from_date, to_date + ' 23:59:59')]
                    period_total = sum([(s['duration'] or 0) for s in self.today_sessions])
                    period_label = f"{from_date} - {to_date}"
                else:
                    self.today_sessions = []
                    period_total = 0
                    period_label = t('custom_period')
            elif self.current_filter == "today":
                self.today_sessions = [dict(row) for row in self.db.get_today_sessions()]
                period_total = sum([(s['duration'] or 0) for s in self.today_sessions])
                period_label = t('today_label')
            elif self.current_filter == "week":
                self.today_sessions = [dict(row) for row in self.db.get_week_sessions()]
                period_total = self.db.get_week_total()
                period_label = t('week_label')
            else:  # month
                self.today_sessions = [dict(row) for row in self.db.get_month_sessions()]
                period_total = self.db.get_month_total()
                period_label = t('month_label')
        
        NSLog(f"reloadSessions: загружено {len(self.today_sessions)} сессий ({self.current_filter})")
        
        # Обновляем метки
        today_total = sum([(s['duration'] or 0) for s in self.today_sessions if 
                          datetime.fromisoformat(s['start_time']).date() == datetime.now().date()])
        self.todayTotalField.setStringValue_(self.formatDuration(today_total))
        self.weekTotalField.setStringValue_(f"{t('total')}: {self.formatDuration(period_total)}")
        
        # Оновлюємо StackView з сесіями
        self.updateSessionsList()
        self.updateFilterButtons()
    
    @objc.python_method
    def updateSessionsList(self):
        """Оновлює список сесій в контейнері"""
        try:
            NSLog(f"=== updateSessionsList: {len(self.today_sessions)} sessions ===")
            
            # ПОЛНОСТЬЮ пересоздаём контейнер - это избежит проблем с кешированием
            # Удаляем старый контейнер из scroll view
            if hasattr(self, 'sessionsStack') and self.sessionsStack is not None:
                self.sessionsScroll.setDocumentView_(None)
            
            # Создаём новый контейнер
            scroll_width = self.sessionsScroll.frame().size.width
            new_height = max(100, len(self.today_sessions) * 45 + 10)
            self.sessionsStack = FlippedView.alloc().initWithFrame_(NSMakeRect(0, 0, scroll_width, new_height))
            
            NSLog(f"=== Container created, size: {scroll_width} x {new_height} ===")
            
            # Додаємо нові сесії
            y_offset = 0
            for i, session in enumerate(self.today_sessions):
                NSLog(f"=== Creating view {i+1}/{len(self.today_sessions)} for session: {session.get('description', 'no desc')} ===")
                sessionView = self.createSessionView(session)
                # Позиционируем от верхнего края
                sessionView.setFrame_(NSMakeRect(10, y_offset, scroll_width - 20, 40))
                self.sessionsStack.addSubview_(sessionView)
                y_offset += 45
            
            # Устанавливаем новый контейнер в scroll view
            self.sessionsScroll.setDocumentView_(self.sessionsStack)
            
            # Явно обновляем scroll view
            self.sessionsScroll.setNeedsDisplay_(True)
            NSLog(f"=== Container updated with {len(self.today_sessions)} items, height: {new_height} ===")
        except Exception as e:
            NSLog(f"=== ERROR updating sessions list: {e} ===")
            import traceback
            traceback.print_exc()
    
    @objc.python_method
    def createSessionView(self, session):
        """Створює візуальний елемент для однієї сесії"""
        try:
            NSLog(f"=== createSessionView START ===")
            width = self.sessionsScroll.frame().size.width - 20
            NSLog(f"=== width: {width} ===")
            
            # Контейнер для сесії
            container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, 40))
            container.setWantsLayer_(True)
            # Подсветка выбранной сессии
            session_id = session.get('id', -1)
            if self.selected_session_id == session_id:
                try:
                    container.layer().setBackgroundColor_(NSColor.selectedTextBackgroundColor().colorWithAlphaComponent_(0.12).CGColor())
                except Exception:
                    container.layer().setBackgroundColor_(NSColor.controlHighlightColor().CGColor())
            NSLog(f"=== Container created ===")

            # Опис
            description = session.get('description', '') or t('no_description')
            NSLog(f"=== Creating label ===")
            descLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 20, width*0.5, 18))
            descLabel.setStringValue_(str(description))
            descLabel.setBezeled_(False)
            descLabel.setDrawsBackground_(False)
            descLabel.setEditable_(False)
            descLabel.setSelectable_(False)
            descLabel.setFont_(NSFont.systemFontOfSize_(13))
            descLabel.setTextColor_(NSColor.labelColor())
            container.addSubview_(descLabel)
            NSLog(f"=== Description label added ===")
            
            # Час
            start_time = session.get('start_time', '')
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(str(start_time))
                    end_time = session.get('end_time', '')
                    if end_time:
                        end_dt = datetime.fromisoformat(str(end_time))
                        time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                    else:
                        time_str = f"{start_dt.strftime('%H:%M')} - {t('running')}"
                except:
                    time_str = ""
            else:
                time_str = ""
            
            NSLog(f"=== Creating time label ===")
            timeLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(width*0.5 + 10, 20, width*0.25, 18))
            timeLabel.setStringValue_(time_str)
            timeLabel.setBezeled_(False)
            timeLabel.setDrawsBackground_(False)
            timeLabel.setEditable_(False)
            timeLabel.setSelectable_(False)
            timeLabel.setFont_(NSFont.systemFontOfSize_(12))
            timeLabel.setTextColor_(NSColor.secondaryLabelColor())
            container.addSubview_(timeLabel)
            NSLog(f"=== Time label added ===")
            
            # Тривалість
            duration = session.get('duration', 0) or 0
            duration_str = self.formatDuration(int(duration))
            
            NSLog(f"=== Creating duration label ===")
            durationLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(width*0.75 + 10, 20, width*0.2, 18))
            durationLabel.setStringValue_(duration_str)
            durationLabel.setBezeled_(False)
            durationLabel.setDrawsBackground_(False)
            durationLabel.setEditable_(False)
            durationLabel.setSelectable_(False)
            durationLabel.setFont_(NSFont.systemFontOfSize_(12))
            durationLabel.setTextColor_(NSColor.secondaryLabelColor())
            container.addSubview_(durationLabel)
            NSLog(f"=== Duration label added ===")

            # Кнопка "Оплачено" (зеленая галочка)
            paidBtn = HoverDeleteButton.alloc().initWithFrame_(NSMakeRect(width - 52, 12, 18, 18))
            paidBtn.setTitle_("✓")
            paidBtn.setBordered_(False)
            paidBtn.setBezelStyle_(0)
            paidBtn.setFont_(NSFont.systemFontOfSize_weight_(14, 0.2))
            paidBtn.setTarget_(self)
            paidBtn.setAction_(objc.selector(self.markSessionAsPaid_, signature=b"v@:"))
            paidBtn.setTag_(session_id)
            # Зеленый цвет для кнопки оплаты
            paidBtn.setContentTintColor_(NSColor.colorWithRed_green_blue_alpha_(0.2, 0.7, 0.3, 0.9))
            paidBtn.setWantsLayer_(True)
            paidBtn.layer().setCornerRadius_(9)
            paidBtn.layer().setBackgroundColor_(NSColor.colorWithWhite_alpha_(0.95, 0.7).CGColor())
            container.addSubview_(paidBtn)
            NSLog(f"=== Paid button added ===")

            # Кнопка удаления в стиле macOS с hover эффектом
            deleteBtn = HoverDeleteButton.alloc().initWithFrame_(NSMakeRect(width - 28, 12, 18, 18))
            deleteBtn.setTitle_("✕")
            deleteBtn.setBordered_(False)
            deleteBtn.setBezelStyle_(0)  # NSBezelStyleRounded
            deleteBtn.setFont_(NSFont.systemFontOfSize_weight_(11, -0.4))  # Тонкий шрифт
            deleteBtn.setTarget_(self)
            deleteBtn.setAction_(objc.selector(self.deleteSessionButton_, signature=b"v@:"))
            deleteBtn.setTag_(session_id)
            # Серый цвет по умолчанию
            deleteBtn.setContentTintColor_(NSColor.colorWithRed_green_blue_alpha_(0.6, 0.6, 0.6, 0.8))
            deleteBtn.setWantsLayer_(True)
            deleteBtn.layer().setCornerRadius_(9)  # Круглая кнопка
            deleteBtn.layer().setBackgroundColor_(NSColor.colorWithWhite_alpha_(0.95, 0.7).CGColor())
            container.addSubview_(deleteBtn)
            NSLog(f"=== Delete button added ===")
            
            # Кнопка выбора (прозрачная, на весь ряд кроме области удаления)
            # Добавляем последней, чтобы она была поверх всех текстовых полей
            selectBtn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, width - 55, 40))
            selectBtn.setBordered_(False)
            selectBtn.setTitle_("")
            selectBtn.setTarget_(self)
            selectBtn.setAction_(objc.selector(self.selectSession_, signature=b"v@:"))
            selectBtn.setTag_(session_id)
            container.addSubview_(selectBtn)
            NSLog(f"=== Select button added ===")
            
            NSLog(f"=== createSessionView END - returning container ===")
            return container
        except Exception as e:
            NSLog(f"=== ERROR in createSessionView: {e} ===")
            import traceback
            traceback.print_exc()
            # Возвращаем пустой контейнер если ошибка
            return NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 40))
    
    def updateFilterButtons(self):
        """Подсвечивает активный фильтр"""
        # Сбрасываем все кнопки
        try:
            from Cocoa import NSControlStateValueOn, NSControlStateValueOff
        except ImportError:
            from Cocoa import NSOnState as NSControlStateValueOn, NSOffState as NSControlStateValueOff
        
        self.customFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "custom" else NSControlStateValueOff)
        self.todayFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "today" else NSControlStateValueOff)
        self.weekFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "week" else NSControlStateValueOff)
        self.monthFilterBtn.setState_(NSControlStateValueOn if self.current_filter == "month" else NSControlStateValueOff)
    
    def setFilterToday_(self, _):
        NSLog(f"=== setFilterToday called, current_filter was: {self.current_filter} ===")
        self.current_filter = "today"
        NSLog(f"=== setFilterToday new filter: {self.current_filter} ===")
        # Скрываем поля custom периода
        self.fromDateLabel.setHidden_(True)
        self.fromDatePicker.setHidden_(True)
        self.toDateLabel.setHidden_(True)
        self.toDatePicker.setHidden_(True)
        self.applyCustomFilterBtn.setHidden_(True)
        self.reloadSessions()

    def selectSession_(self, sender):
        try:
            session_id = sender.tag()
            self.selected_session_id = session_id
            self.updateSessionsList()
        except Exception as e:
            NSLog(f"selectSession_ error: {e}")

    def deleteSessionButton_(self, sender):
        try:
            session_id = sender.tag()
            if session_id is None or session_id < 0:
                return
            # Подтверждение удаления
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('delete_confirm_title'))
            alert.setInformativeText_(t('delete_confirm_message'))
            alert.addButtonWithTitle_(t('delete'))
            alert.addButtonWithTitle_(t('cancel'))
            alert.setAlertStyle_(NSAlertStyleWarning)
            response = alert.runModal()
            # NSAlertFirstButtonReturn == 1000
            if response == 1000:
                # Удаляем запись
                self.db.delete_session(session_id)
                if self.selected_session_id == session_id:
                    self.selected_session_id = None
                self.reloadSessions()
        except Exception as e:
            NSLog(f"deleteSessionButton_ error: {e}")
    
    def markSessionAsPaid_(self, sender):
        """Отметить сессию как оплаченную"""
        try:
            session_id = sender.tag()
            if session_id is None or session_id < 0:
                return
            
            # Подтверждение
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('mark_as_paid_title'))
            alert.setInformativeText_(t('mark_as_paid_message'))
            alert.addButtonWithTitle_(t('yes'))
            alert.addButtonWithTitle_(t('cancel'))
            alert.setAlertStyle_(NSAlertStyleInformational)
            response = alert.runModal()
            
            # NSAlertFirstButtonReturn == 1000
            if response == 1000:
                # Отмечаем как оплаченную
                self.db.mark_session_as_paid(session_id)
                
                # Обновляем UI
                self.reloadSessions()
        except Exception as e:
            NSLog(f"markSessionAsPaid_ error: {e}")
    
    def setFilterWeek_(self, _):
        NSLog(f"=== setFilterWeek called, current_filter was: {self.current_filter} ===")
        self.current_filter = "week"
        NSLog(f"=== setFilterWeek new filter: {self.current_filter} ===")
        # Скрываем поля custom периода
        self.fromDateLabel.setHidden_(True)
        self.fromDatePicker.setHidden_(True)
        self.toDateLabel.setHidden_(True)
        self.toDatePicker.setHidden_(True)
        self.applyCustomFilterBtn.setHidden_(True)
        self.reloadSessions()
    
    def setFilterMonth_(self, _):
        NSLog(f"=== setFilterMonth called, current_filter was: {self.current_filter} ===")
        self.current_filter = "month"
        NSLog(f"=== setFilterMonth new filter: {self.current_filter} ===")
        # Скрываем поля custom периода
        self.fromDateLabel.setHidden_(True)
        self.fromDatePicker.setHidden_(True)
        self.toDateLabel.setHidden_(True)
        self.toDatePicker.setHidden_(True)
        self.applyCustomFilterBtn.setHidden_(True)
        self.reloadSessions()
    
    def setFilterCustom_(self, _):
        NSLog(f"=== setFilterCustom called, current_filter was: {self.current_filter} ===")
        # Показываем/скрываем поля выбора дат
        is_hidden = self.fromDatePicker.isHidden()
        self.fromDateLabel.setHidden_(not is_hidden)
        self.fromDatePicker.setHidden_(not is_hidden)
        self.toDateLabel.setHidden_(not is_hidden)
        self.toDatePicker.setHidden_(not is_hidden)
        self.applyCustomFilterBtn.setHidden_(not is_hidden)
        
        # Если показываем - применяем фильтр
        if not is_hidden:
            self.applyCustomFilter_(None)
    
    def applyCustomFilter_(self, _):
        """Применить фильтр с выбранными датами"""
        try:
            from datetime import datetime
            
            # Получаем даты из NSDatePicker
            from_date_obj = self.fromDatePicker.dateValue()
            to_date_obj = self.toDatePicker.dateValue()
            
            # Конвертируем NSDate в строку формата YYYY-MM-DD
            from_date = from_date_obj.descriptionWithCalendarFormat_timeZone_locale_('%Y-%m-%d', None, None)
            to_date = to_date_obj.descriptionWithCalendarFormat_timeZone_locale_('%Y-%m-%d', None, None)
            
            # Валидация - проверяем что from_date <= to_date
            if from_date_obj.compare_(to_date_obj) == 1:  # NSOrderedDescending
                NSLog("From date is after to date")
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_("Начальная дата должна быть раньше конечной")
                alert.setAlertStyle_(NSAlertStyleWarning)
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
            
            # Устанавливаем custom фильтр
            self.current_filter = "custom"
            self.custom_from_date = from_date
            self.custom_to_date = to_date
            NSLog(f"=== setFilterCustom: from {from_date} to {to_date} ===")
            self.reloadSessions()
            
        except Exception as e:
            NSLog(f"applyCustomFilter_ error: {e}")
    
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
        # TODO: Реализовать выбор сессии для удаления (пока таблицы нет)
        return
        
        # row = self.tableView.selectedRow()
        # if row < 0 or row >= len(getattr(self, 'today_sessions', [])):
        #     return
        
        # session = self.today_sessions[row]
        # session_id = session['id']
        
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
        NSLog("=== createProject_ CALLED ===")
        print("[DEBUG] createProject_ function called")
        # Alert с тремя полями: название, компания и ставка
        alert = NSAlert.alloc().init()
        NSLog("=== NSAlert created ===")
        alert.setMessageText_(t('new_project'))
        alert.setInformativeText_(f"{t('project_name')}\n{t('company')}\n{t('hourly_rate')}")
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
        
        # Контейнер для полей (увеличиваем высоту для третьего поля)
        accessoryView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 240, 90))
        
        nameLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 66, 80, 20))
        nameLabel.setStringValue_(t('project_name'))
        nameLabel.setBezeled_(False)
        nameLabel.setDrawsBackground_(False)
        nameLabel.setEditable_(False)
        accessoryView.addSubview_(nameLabel)
        
        nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(85, 66, 155, 24))
        accessoryView.addSubview_(nameField)
        
        # Получаем список компаний
        companies = self.db.get_all_companies()
        
        companyLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 36, 80, 20))
        companyLabel.setStringValue_(t('company'))
        companyLabel.setBezeled_(False)
        companyLabel.setDrawsBackground_(False)
        companyLabel.setEditable_(False)
        accessoryView.addSubview_(companyLabel)
        
        # Создаем NSPopUpButton для выбора компании
        companyPopup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(85, 34, 155, 26))
        companyPopup.setPullsDown_(False)
        companyPopup.addItemWithTitle_(t('no_company'))
        for company in companies:
            companyPopup.addItemWithTitle_(f"{company['name']} ({company['code']})")
        accessoryView.addSubview_(companyPopup)
        
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
        # self.tableView.setNeedsDisplay_(True)  # таблицы больше нет
        
        if resp == 1000:  # First button
            name = nameField.stringValue().strip()
            rate_str = rateField.stringValue().strip()
            hourly_rate = 0
            try:
                if rate_str:
                    hourly_rate = float(rate_str)
            except ValueError:
                hourly_rate = 0
            
            # Определяем выбранную компанию
            company_id = None
            selected_idx = companyPopup.indexOfSelectedItem()
            if selected_idx > 0:  # 0 = "Без компании"
                company_id = companies[selected_idx - 1]['id']
            
            if name:
                try:
                    NSLog(f"Attempting to create project: {name}, rate: {hourly_rate}, company_id: {company_id}")
                    NSLog(f"Database path: {self.db.db_path}")
                    res = self.db.create_project(name, hourly_rate=hourly_rate, company_id=company_id)
                    NSLog(f"Project creation result: {res}")
                    if res:
                        self.reloadProjects()
                        # Выбираем созданный проект (с учетом новой метки со ставкой)
                        rate_display = f" (${hourly_rate:.0f}/ч)" if hourly_rate > 0 else ""
                        self.projectPopup.selectItemWithTitle_(f"{name}{rate_display}")
                        NSLog(f"Project '{name}' created successfully with ID: {res}")
                    else:
                        NSLog(f"Failed to create project '{name}' - project with this name may already exist")
                        error_alert = NSAlert.alloc().init()
                        error_alert.setMessageText_(t('error'))
                        error_alert.setInformativeText_(t('project_exists') if hasattr(t, '__call__') else f"Проект з назвою '{name}' вже існує")
                        error_alert.addButtonWithTitle_("OK")
                        error_alert.runModal()
                except Exception as e:
                    NSLog(f"Error creating project: {e}")
                    import traceback
                    NSLog(f"Traceback: {traceback.format_exc()}")
                    error_alert = NSAlert.alloc().init()
                    error_alert.setMessageText_(t('error'))
                    error_alert.setInformativeText_(f"Помилка при створенні проекту: {str(e)}")
                    error_alert.addButtonWithTitle_("OK")
                    error_alert.runModal()
            else:
                NSLog("Project name is empty")

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
            
            NSLog("")
            NSLog("*** ЗАПУСКАЕТСЯ ТАЙМЕР РАБОТЫ ***")
            NSLog(f"DEBUG: Проект: {project_name if 'project_name' in locals() else 'N/A'}")
            NSLog(f"DEBUG: Начало работы: {self.start_time}")
            NSLog("*** ЗАПУСКАЕМ ТАЙМЕР НАПОМИНАНИЙ ***")
            
            # Запускаем таймер для часовых напоминаний (каждый час)
            self._startHourlyReminder()
            
            try:
                NSApp.delegate().updateStatusItem()
            except Exception:
                pass
        else:
            # стоп
            NSLog("=== НАЧАЛО ОСТАНОВКИ ТАЙМЕРА ===")
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
                NSLog(f"Информация о задаче собрана: {project_name}")
            except Exception as e:
                NSLog(f"Error preparing stop notification: {e}")
                import traceback
                traceback.print_exc()
                project_name = "Без названия"
                task_description = ""
                elapsed_time = ""
            
            # Останавливаем таймер напоминаний ПЕРВЫМ делом
            try:
                NSLog("Останавливаем таймер напоминаний...")
                self._stopHourlyReminder()
                NSLog("Таймер напоминаний остановлен")
            except Exception as e:
                NSLog(f"Ошибка остановки таймера напоминаний: {e}")
                import traceback
                traceback.print_exc()
            
            try:
                NSLog(f"Останавливаем сессию {self.current_session_id}...")
                if self.current_session_id:
                    self.db.stop_session(self.current_session_id)
                NSLog("Сессия остановлена")
            except Exception as e:
                NSLog(f"Ошибка остановки сессии: {e}")
                import traceback
                traceback.print_exc()
            
            self.timer_running = False
            self.start_time = None
            self.startStopBtn.setTitle_("▶")
            
            try:
                self._updateStartStopAppearance()
            except Exception as e:
                NSLog(f"Ошибка обновления внешнего вида кнопки: {e}")
            
            self.descriptionField.setStringValue_("")
            
            try:
                NSLog("Перезагружаем сессии...")
                self.reloadSessions()
                NSLog("Сессии перезагружены")
            except Exception as e:
                NSLog(f"Ошибка перезагрузки сессий: {e}")
                import traceback
                traceback.print_exc()
            
            try:
                NSApp.delegate().updateStatusItem()
            except Exception as e:
                NSLog(f"Ошибка обновления статус-бара: {e}")
            
            # Отправляем уведомление об остановке
            try:
                NSApp.delegate()._sendStopNotification(project_name, task_description, elapsed_time)
            except Exception as e:
                NSLog(f"Error sending stop notification: {e}")
            
            NSLog("=== ОСТАНОВКА ТАЙМЕРА ЗАВЕРШЕНА ===")

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
            
            # Запускаем таймер напоминаний при восстановлении сессии
            self._startHourlyReminder()
            
            try:
                NSApp.delegate().updateStatusItem()
            except Exception:
                pass
    
    @objc.python_method
    def _startHourlyReminder(self):
        """Запускает таймер для напоминаний каждый час"""
        # Останавливаем предыдущий таймер, если он был
        self._stopHourlyReminder()
        
        # Получаем интервал из настроек (в минутах), по умолчанию 60 минут
        defaults = NSUserDefaults.standardUserDefaults()
        interval_minutes = defaults.integerForKey_("reminderInterval")
        NSLog(f"DEBUG: Значение из NSUserDefaults reminderInterval = {interval_minutes}")
        NSLog(f"DEBUG: DEV_MODE = {DEV_MODE}")
        
        if interval_minutes <= 0:
            # В DEV режиме - 1 минута для тестирования, в продакшене - 60 минут
            interval_minutes = 1 if DEV_MODE else 60
            NSLog(f"DEBUG: interval_minutes был <= 0, установлено значение по умолчанию: {interval_minutes}")
        
        interval_seconds = interval_minutes * 60.0
        
        # Запускаем новый таймер
        NSLog(f"=== ЗАПУСК ТАЙМЕРА НАПОМИНАНИЙ (интервал: {interval_minutes} мин = {interval_seconds} сек) ===")
        self.hourly_reminder_ref = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            interval_seconds,
            self,
            objc.selector(self.showHourlyReminder_, signature=b"v@:@"),
            None,
            True  # Повторять
        )
        NSLog(f"Таймер создан: {self.hourly_reminder_ref}, валиден: {self.hourly_reminder_ref.isValid() if self.hourly_reminder_ref else 'None'}")
    
    @objc.python_method
    def _stopHourlyReminder(self):
        """Останавливает таймер напоминаний"""
        if self.hourly_reminder_ref is not None:
            NSLog("Остановка таймера напоминаний")
            self.hourly_reminder_ref.invalidate()
            self.hourly_reminder_ref = None
    
    def showHourlyReminder_(self, timer):
        """Показывает напоминание о текущей активности"""
        NSLog("")
        NSLog("########################################")
        NSLog("### ВЫЗВАН showHourlyReminder_ !!! ###")
        NSLog("########################################")
        
        try:
            NSLog(f"DEBUG: Timer running: {self.timer_running}")
            NSLog(f"DEBUG: Current time: {datetime.now()}")
            
            if not self.timer_running:
                # Если таймер уже остановлен, не показываем напоминание
                NSLog("ВНИМАНИЕ: Таймер не запущен, пропускаем напоминание")
                return
            
            NSLog("DEBUG: Прошли проверку timer_running")
            NSLog("ПОКАЗЫВАЕМ НАПОМИНАНИЕ ПОЛЬЗОВАТЕЛЮ!!!")
            
            # СНАЧАЛА ОСТАНАВЛИВАЕМ ТАЙМЕР перед показом сообщения
            NSLog("Останавливаем таймер перед показом сообщения...")
            paused_session_id = self.current_session_id
            paused_start_time = self.start_time
            
            NSLog(f"DEBUG: paused_session_id = {paused_session_id}")
            NSLog(f"DEBUG: paused_start_time = {paused_start_time}")
            
            # Временно останавливаем только визуальный таймер, но не сессию
            if self.update_timer_ref is not None:
                NSLog("DEBUG: Останавливаем update_timer_ref")
                self.update_timer_ref.invalidate()
                self.update_timer_ref = None
            
            NSLog("DEBUG: Получаем информацию о текущей задаче...")
            
            # Получаем информацию о текущей задаче
            idx = self.projectPopup.indexOfSelectedItem()
            project_name = "Без названия"
            if idx > 0 and idx-1 < len(self.projects_cache):
                project_name = self.projects_cache[idx-1]['name']
            task_description = self.descriptionField.stringValue().strip()
            
            NSLog(f"DEBUG: Проект: {project_name}, Описание: {task_description}")
            
            # Вычисляем время работы
            elapsed_seconds = 0
            if paused_start_time:
                elapsed_seconds = int((datetime.now() - paused_start_time).total_seconds())
            elapsed_str = self.formatDuration(elapsed_seconds)
            
            NSLog(f"DEBUG: Время работы: {elapsed_str}")
            
            # Формируем текст сообщения
            message = f"Проект: {project_name}"
            if task_description:
                message += f"\nЗадача: {task_description}"
            message += f"\n\nВремя работы: {elapsed_str}"
            message += f"\n\nТаймер остановлен. Продолжить работу?"
            
            NSLog("DEBUG: Создаем NSAlert...")
            
            # Создаем alert
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('still_working_question'))
            alert.setInformativeText_(message)
            alert.addButtonWithTitle_(t('yes'))  # Продолжить
            alert.addButtonWithTitle_(t('no'))   # Завершить
            alert.setAlertStyle_(1)  # NSInformationalAlertStyle
            
            # Показываем alert и обрабатываем ответ
            NSLog("DEBUG: Показываем alert...")
            response = alert.runModal()
            NSLog(f"DEBUG: Получен ответ: {response}")
            
            # NSAlertFirstButtonReturn = 1000 (Да - продолжить)
            # NSAlertSecondButtonReturn = 1001 (Нет - завершить)
            if response == 1001:  # Нажата кнопка "Нет" - ЗАВЕРШИТЬ ЗАДАЧУ
                NSLog("DEBUG: ПОЛЬЗОВАТЕЛЬ НАЖАЛ 'НЕТ' - ЗАВЕРШАЕМ ЗАДАЧУ")
                
                # Полностью останавливаем таймер и закрываем сессию
                if paused_session_id and self.timer_running:
                    NSLog(f"DEBUG: Завершаем сессию {paused_session_id}")
                    self.timer_running = False
                    self.db.stop_session(paused_session_id)
                    self.current_session_id = None
                    self.start_time = None
                    self.timerLabel.setStringValue_("00:00:00")
                    self.toggleBtn.setTitle_(t('start'))
                    
                    # Останавливаем таймер напоминаний
                    self._stopHourlyReminder()
                    
                    # Обновляем UI
                    self.reloadSessions()
                    
                    # Обновляем статус-бар
                    try:
                        NSApp.delegate().updateStatusItem()
                    except Exception:
                        pass
                    
                    NSLog("DEBUG: Задача успешно завершена!")
            else:  # Нажата кнопка "Да" - ПРОДОЛЖИТЬ РАБОТУ
                NSLog("DEBUG: Пользователь ответил 'Да', продолжаем работу")
                
                # Возобновляем таймер
                NSLog("DEBUG: Возобновляем таймер...")
                if self.timer_running and paused_session_id:
                    # Перезапускаем визуальный таймер
                    self.update_timer_ref = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                        1.0,
                        self,
                        objc.selector(self.tick_, signature=b"v@:@"),
                        None,
                        True
                    )
                    NSLog("DEBUG: Таймер успешно возобновлен!")
                    
        except Exception as e:
            NSLog(f"КРИТИЧЕСКАЯ ОШИБКА в showHourlyReminder_: {e}")
            import traceback
            traceback.print_exc()
    
    def _stopTimerFromReminder_(self, sender):
        """Безопасная остановка таймера из напоминания"""
        NSLog("=== _stopTimerFromReminder_ ВЫЗВАН ===")
        try:
            if not self.timer_running:
                NSLog("Таймер уже остановлен, выходим")
                return
            
            NSLog("Выполняем остановку таймера из напоминания...")
            self.toggleTimer_(None)
            NSLog("Таймер успешно остановлен из напоминания")
        except Exception as e:
            NSLog(f"КРИТИЧЕСКАЯ ОШИБКА при остановке таймера из напоминания: {e}")
            import traceback
            traceback.print_exc()
            # Пытаемся принудительно остановить
            try:
                self.timer_running = False
                self._stopHourlyReminder()
            except:
                pass

    def continueSelected_(self, _):
        # TODO: Реализовать выбор последней сессии для продолжения
        if not self.today_sessions:
            return
        # Берем последнюю сессию
        s = self.today_sessions[0]
        if self.timer_running:
            self.showWarning_(t('stop_current_timer'))
            return
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
        
        # Сбрасываем highlight кнопки через задержку
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.15, self, objc.selector(self.resetContinueButton_, signature=b"v@:"), None, False
        )
    
    def resetContinueButton_(self, _):
        """Сбрасывает highlight кнопки Продолжить"""
        try:
            self.continueBtn.highlight_(False)
        except Exception:
            pass
    
    def openStatistics_(self, _):
        """Відкриває вікно статистики"""
        try:
            # Викликаємо метод з AppDelegate
            NSApp.delegate().openStatistics_(None)
            
            # Сбрасываем highlight кнопки статистики через небольшую задержку
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.15, self, objc.selector(self.resetStatisticsButton_, signature=b"v@:"), None, False
            )
        except Exception as e:
            NSLog(f"Error opening statistics: {e}")
    
    def resetStatisticsButton_(self, _):
        """Сбрасывает highlight кнопки статистики"""
        try:
            self.statisticsBtn.highlight_(False)
        except Exception:
            pass

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
    
    @objc.python_method
    def _setWindowIcon(self, window):
        """Устанавливает иконку для окна"""
        try:
            base = _get_base_dir()
            candidates = [
                os.path.join(base, "assets", "app_icon.icns"),
                os.path.join(base, "assets", "app_icon.png"),
            ]
            for p in candidates:
                if os.path.exists(p):
                    img = NSImage.alloc().initWithContentsOfFile_(p)
                    if img:
                        # Устанавливаем иконку для окна
                        try:
                            window.setRepresentedURL_(None)
                            button = window.standardWindowButton_(0)
                            if button:
                                button.setImage_(img)
                        except:
                            pass
                        break
        except Exception as e:
            NSLog(f"Set window icon error: {e}")


class ProjectSettingsWindowController(NSObject):
    """Окно настроек проектов для редактирования имени и ставки"""
    def init(self):
        self = objc.super(ProjectSettingsWindowController, self).init()
        if self is None:
            return None
        self.db = Database()
        self.projects = []
        self.companies = []
        self.window = None
        self.tableView = None
        self.nameField = None
        self.companyPopup = None
        self.rateField = None
        self.saveBtn = None
        self.deleteBtn = None
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
        width = 550
        height = 550
        x = (screen_frame.size.width - width) / 2
        y = (screen_frame.size.height - height) / 2
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSTitledWindowMask | NSClosableWindowMask,
            2,
            False
        )
        self.window.setTitle_(t('settings'))
        self.window.setReleasedWhenClosed_(False)
        
        content = self.window.contentView()
        
        # Создаем TabView
        tabView = NSTabView.alloc().initWithFrame_(NSMakeRect(10, 10, width-20, height-20))
        
        # Вкладка 1: Данные (Проекты)
        dataTab = NSTabViewItem.alloc().initWithIdentifier_("data")
        dataTab.setLabel_(t('data'))
        dataView = NSView.alloc().initWithFrame_(tabView.contentRect())
        
        # Таблица проектов
        tabHeight = height - 70
        tableY = 140
        tableHeight = tabHeight - tableY - 20
        scrollView = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, tableY, width-60, tableHeight))
        self.tableView = NSTableView.alloc().initWithFrame_(scrollView.bounds())
        
        col1 = NSTableColumn.alloc().initWithIdentifier_("name")
        col1.setWidth_((width-60) * 0.6)
        col1.headerCell().setStringValue_(t('project'))
        self.tableView.addTableColumn_(col1)
        
        col2 = NSTableColumn.alloc().initWithIdentifier_("rate")
        col2.setWidth_((width-60) * 0.3)
        col2.headerCell().setStringValue_(t('rate'))
        self.tableView.addTableColumn_(col2)
        
        self.tableView.setDelegate_(self)
        self.tableView.setDataSource_(self)
        
        scrollView.setDocumentView_(self.tableView)
        scrollView.setHasVerticalScroller_(True)
        dataView.addSubview_(scrollView)
        
        # Поля редактирования и создание нового проекта
        labelY = 80
        label1 = NSTextField.alloc().initWithFrame_(NSMakeRect(20, labelY, 100, 20))
        label1.setStringValue_(t('project_name') + ":")
        label1.setBezeled_(False)
        label1.setDrawsBackground_(False)
        label1.setEditable_(False)
        dataView.addSubview_(label1)
        
        self.nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(130, labelY, width-280, 28))
        self.nameField.setPlaceholderString_(t('project_name'))
        dataView.addSubview_(self.nameField)
        
        # Поле компании
        label2 = NSTextField.alloc().initWithFrame_(NSMakeRect(20, labelY - 35, 100, 20))
        label2.setStringValue_(t('company') + ":")
        label2.setBezeled_(False)
        label2.setDrawsBackground_(False)
        label2.setEditable_(False)
        dataView.addSubview_(label2)
        
        self.companyPopup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(130, labelY - 40, 200, 28))
        self.companyPopup.setPullsDown_(False)
        dataView.addSubview_(self.companyPopup)
        
        label3 = NSTextField.alloc().initWithFrame_(NSMakeRect(20, labelY - 70, 100, 20))
        label3.setStringValue_(t('hourly_rate') + ":")
        label3.setBezeled_(False)
        label3.setDrawsBackground_(False)
        label3.setEditable_(False)
        dataView.addSubview_(label3)
        
        self.rateField = NSTextField.alloc().initWithFrame_(NSMakeRect(130, labelY - 70, 100, 28))
        self.rateField.setPlaceholderString_("0")
        dataView.addSubview_(self.rateField)
        
        # Кнопка Видалити проект  
        self.deleteBtn = NSButton.alloc().initWithFrame_(NSMakeRect(240, labelY - 70, 130, 28))
        self.deleteBtn.setTitle_(t('delete_project'))
        self.deleteBtn.setBezelStyle_(NSBezelStyleRounded)
        self.deleteBtn.setTarget_(self)
        self.deleteBtn.setAction_(objc.selector(self.deleteProject_, signature=b"v@:@"))
        dataView.addSubview_(self.deleteBtn)
        
        # Кнопка Зберегти (создает новый проект или обновляет существующий)
        self.saveBtn = NSButton.alloc().initWithFrame_(NSMakeRect(370, labelY - 70, 135, 28))
        self.saveBtn.setTitle_(t('save'))
        self.saveBtn.setBezelStyle_(NSBezelStyleRounded)
        self.saveBtn.setTarget_(self)
        self.saveBtn.setAction_(objc.selector(self.saveProject_, signature=b"v@:"))
        dataView.addSubview_(self.saveBtn)
        
        dataTab.setView_(dataView)
        tabView.addTabViewItem_(dataTab)
        
        # Вкладка 2: Системные
        utilsTab = NSTabViewItem.alloc().initWithIdentifier_("utils")
        utilsTab.setLabel_(t('system_settings'))
        utilsView = NSView.alloc().initWithFrame_(tabView.contentRect())
        
        # Кнопка Бекап базы данных
        backupBtn = NSButton.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 60, 180, 32))
        backupBtn.setTitle_(t('backup_db'))
        backupBtn.setBezelStyle_(NSBezelStyleRounded)
        backupBtn.setTarget_(self)
        backupBtn.setAction_(objc.selector(self.createBackup_, signature=b"v@:@"))
        utilsView.addSubview_(backupBtn)
        
        # Описание для бекапа
        backupLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 90, width-60, 20))
        backupLabel.setStringValue_(t('backup_description'))
        backupLabel.setBezeled_(False)
        backupLabel.setDrawsBackground_(False)
        backupLabel.setEditable_(False)
        backupLabel.setTextColor_(NSColor.secondaryLabelColor())
        utilsView.addSubview_(backupLabel)
        
        # Кнопка Восстановление из бекапа
        restoreBtn = NSButton.alloc().initWithFrame_(NSMakeRect(220, tabHeight - 60, 200, 32))
        restoreBtn.setTitle_(t('restore_from_backup'))
        restoreBtn.setBezelStyle_(NSBezelStyleRounded)
        restoreBtn.setTarget_(self)
        restoreBtn.setAction_(objc.selector(self.restoreBackup_, signature=b"v@:@"))
        utilsView.addSubview_(restoreBtn)
        
        # Описание для восстановления
        restoreLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(220, tabHeight - 90, width-240, 20))
        restoreLabel.setStringValue_(t('restore_description'))
        restoreLabel.setBezeled_(False)
        restoreLabel.setDrawsBackground_(False)
        restoreLabel.setEditable_(False)
        restoreLabel.setTextColor_(NSColor.secondaryLabelColor())
        utilsView.addSubview_(restoreLabel)
        
        # Разделитель
        separator = NSBox.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 120, width-60, 1))
        separator.setBoxType_(2)  # Separator
        utilsView.addSubview_(separator)
        
        # Настройка времени напоминания
        reminderLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 160, 180, 20))
        reminderLabel.setStringValue_(t('reminder_interval'))
        reminderLabel.setBezeled_(False)
        reminderLabel.setDrawsBackground_(False)
        reminderLabel.setEditable_(False)
        utilsView.addSubview_(reminderLabel)
        
        # Поле для ввода времени напоминания
        self.reminderIntervalField = NSTextField.alloc().initWithFrame_(NSMakeRect(210, tabHeight - 165, 80, 28))
        self.reminderIntervalField.setPlaceholderString_("60")
        # Загружаем сохраненное значение или используем 60 минут по умолчанию
        defaults = NSUserDefaults.standardUserDefaults()
        savedInterval = defaults.integerForKey_("reminderInterval")
        if savedInterval == 0:
            savedInterval = 60  # По умолчанию 60 минут (1 час)
        self.reminderIntervalField.setStringValue_(str(savedInterval))
        utilsView.addSubview_(self.reminderIntervalField)
        
        # Метка "минут" рядом с полем
        minutesLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(295, tabHeight - 160, 60, 20))
        minutesLabel.setStringValue_(t('minutes'))
        minutesLabel.setBezeled_(False)
        minutesLabel.setDrawsBackground_(False)
        minutesLabel.setEditable_(False)
        utilsView.addSubview_(minutesLabel)
        
        # Описание для напоминания
        reminderDescLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 190, width-60, 20))
        reminderDescLabel.setStringValue_(t('reminder_description'))
        reminderDescLabel.setBezeled_(False)
        reminderDescLabel.setDrawsBackground_(False)
        reminderDescLabel.setEditable_(False)
        reminderDescLabel.setTextColor_(NSColor.secondaryLabelColor())
        utilsView.addSubview_(reminderDescLabel)
        
        # Разделитель перед настройками языка
        separator2 = NSBox.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 220, width-60, 1))
        separator2.setBoxType_(2)  # Separator
        utilsView.addSubview_(separator2)
        
        # Настройка языка интерфейса
        languageLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 260, 180, 20))
        languageLabel.setStringValue_(t('interface_language'))
        languageLabel.setBezeled_(False)
        languageLabel.setDrawsBackground_(False)
        languageLabel.setEditable_(False)
        utilsView.addSubview_(languageLabel)
        
        # Popup для выбора языка
        self.languagePopup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(210, tabHeight - 265, 200, 28), False)
        self.languagePopup.addItemWithTitle_(t('language_english'))
        self.languagePopup.addItemWithTitle_(t('language_russian'))
        self.languagePopup.addItemWithTitle_(t('language_ukrainian'))
        self.languagePopup.addItemWithTitle_(t('language_hungarian'))
        
        # Устанавливаем текущий выбранный язык
        from localization import get_localization
        current_lang = get_localization().get_current_language()
        if current_lang == 'en':
            self.languagePopup.selectItemAtIndex_(0)
        elif current_lang == 'ru':
            self.languagePopup.selectItemAtIndex_(1)
        elif current_lang == 'uk':
            self.languagePopup.selectItemAtIndex_(2)
        elif current_lang == 'hu':
            self.languagePopup.selectItemAtIndex_(3)
        
        utilsView.addSubview_(self.languagePopup)
        
        # Описание для выбора языка
        languageDescLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 290, width-60, 20))
        languageDescLabel.setStringValue_(t('language_description'))
        languageDescLabel.setBezeled_(False)
        languageDescLabel.setDrawsBackground_(False)
        languageDescLabel.setEditable_(False)
        languageDescLabel.setTextColor_(NSColor.secondaryLabelColor())
        utilsView.addSubview_(languageDescLabel)
        
        # Разделитель перед общей кнопкой сохранения
        separator3 = NSBox.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 320, width-60, 1))
        separator3.setBoxType_(2)  # Separator
        utilsView.addSubview_(separator3)
        
        # Общая кнопка сохранения всех настроек
        saveAllBtn = NSButton.alloc().initWithFrame_(NSMakeRect((width - 180) / 2, tabHeight - 360, 180, 32))
        saveAllBtn.setTitle_(t('save'))
        saveAllBtn.setBezelStyle_(NSBezelStyleRounded)
        saveAllBtn.setTarget_(self)
        saveAllBtn.setAction_(objc.selector(self.saveAllSettings_, signature=b"v@:@"))
        utilsView.addSubview_(saveAllBtn)
        
        utilsTab.setView_(utilsView)
        tabView.addTabViewItem_(utilsTab)
        
        # Вкладка 3: Интеграции
        integrationsTab = NSTabViewItem.alloc().initWithIdentifier_("integrations")
        integrationsTab.setLabel_(t('integrations'))
        integrationsView = NSView.alloc().initWithFrame_(tabView.contentRect())
        
        # Заглушка для будущих интеграций
        placeholderLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, tabHeight - 60, width-60, 40))
        placeholderLabel.setStringValue_(t('integrations_placeholder'))
        placeholderLabel.setBezeled_(False)
        placeholderLabel.setDrawsBackground_(False)
        placeholderLabel.setEditable_(False)
        placeholderLabel.setTextColor_(NSColor.secondaryLabelColor())
        integrationsView.addSubview_(placeholderLabel)
        
        integrationsTab.setView_(integrationsView)
        tabView.addTabViewItem_(integrationsTab)
        
        content.addSubview_(tabView)
    
    def reloadProjects(self):
        self.projects = self.db.get_all_projects()
        self.companies = self.db.get_all_companies()
        
        # Обновляем popup с компаниями
        if self.companyPopup:
            self.companyPopup.removeAllItems()
            self.companyPopup.addItemWithTitle_(t('no_company'))
            for company in self.companies:
                self.companyPopup.addItemWithTitle_(f"{company['name']} ({company['code']})")
        
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
            
            # Устанавливаем выбранную компанию
            if self.companyPopup:
                company_id = project.get('company_id')
                if company_id:
                    # Ищем индекс компании в списке
                    for i, company in enumerate(self.companies):
                        if company['id'] == company_id:
                            self.companyPopup.selectItemAtIndex_(i + 1)  # +1 для "Без компании"
                            break
                else:
                    self.companyPopup.selectItemAtIndex_(0)  # "Без компании"
    
    def createBackup_(self, sender):
        """Создание бекапа базы данных"""
        try:
            import shutil
            from datetime import datetime
            
            # Используем ту же логику поиска БД, что и в database.py
            base_dir = _get_base_dir()
            db_path = os.path.join(base_dir, 'timetracker.db')
            
            # Если БД нет в рабочей папке, ищем в Application Support
            if not os.path.exists(db_path):
                app_support = os.path.expanduser('~/Library/Application Support/MacikTimer')
                db_path = os.path.join(app_support, 'timetracker.db')
            
            # Проверяем, существует ли файл базы данных
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"База данных не найдена: {db_path}")
            
            NSLog(f"Database path: {db_path}")
            
            # Создаем диалог выбора места сохранения
            panel = NSSavePanel.savePanel()
            panel.setTitle_(t('save_backup_title'))
            
            # Имя файла по умолчанию с датой и временем
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            panel.setNameFieldStringValue_(f"MTimer_backup_{timestamp}.db")
            panel.setAllowedFileTypes_(["db"])
            
            # Показываем диалог
            if panel.runModal() == NSModalResponseOK:
                backup_path = panel.URL().path()
                
                # Копируем файл базы данных
                shutil.copy2(db_path, backup_path)
                
                # Показываем сообщение об успехе
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('backup_created'))
                alert.setInformativeText_(t('database_saved_to') + f"\n{backup_path}")
                alert.setAlertStyle_(NSAlertStyleInformational)
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                
                NSLog(f"Backup created: {backup_path}")
        
        except Exception as e:
            NSLog(f"Backup error: {e}")
            import traceback
            traceback.print_exc()
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('backup_error'))
            alert.setInformativeText_(str(e))
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
    
    def restoreBackup_(self, sender):
        """Восстановление базы данных из бекапа"""
        try:
            import shutil
            from Cocoa import NSOpenPanel
            
            # Находим путь к текущей базе данных
            base_dir = _get_base_dir()
            db_path = os.path.join(base_dir, 'timetracker.db')
            
            # Если БД нет в рабочей папке, используем Application Support
            if not os.path.exists(db_path):
                app_support = os.path.expanduser('~/Library/Application Support/MacikTimer')
                os.makedirs(app_support, exist_ok=True)
                db_path = os.path.join(app_support, 'timetracker.db')
            
            NSLog(f"Target database path: {db_path}")
            
            # Предупреждение о замене текущей базы
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('restore_title'))
            alert.setInformativeText_(t('restore_warning'))
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_(t('restore_continue'))
            alert.addButtonWithTitle_(t('cancel'))
            
            # Первая кнопка возвращает 1000, вторая - 1001
            response = alert.runModal()
            NSLog(f"Alert response: {response}")
            if response != 1000:  # 1000 = первая кнопка "Продолжить"
                return
            
            # Создаем диалог выбора файла
            panel = NSOpenPanel.openPanel()
            panel.setTitle_(t('select_backup_file'))
            panel.setAllowedFileTypes_(["db"])
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowsMultipleSelection_(False)
            
            # Показываем диалог
            if panel.runModal() == NSModalResponseOK:
                backup_path = panel.URL().path()
                
                # Проверяем, что файл существует
                if not os.path.exists(backup_path):
                    raise FileNotFoundError(f"Файл бекапа не найден: {backup_path}")
                
                # Создаем временный бекап текущей БД на случай ошибки
                temp_backup = None
                if os.path.exists(db_path):
                    temp_backup = db_path + '.temp_backup'
                    shutil.copy2(db_path, temp_backup)
                
                try:
                    # Закрываем текущее соединение с БД
                    if hasattr(self, 'db') and self.db and self.db.connection:
                        self.db.connection.close()
                        self.db.connection = None
                    
                    # Копируем файл бекапа
                    shutil.copy2(backup_path, db_path)
                    
                    # Переинициализируем базу данных
                    if hasattr(self, 'db'):
                        self.db = Database()
                    
                    # Удаляем временный бекап
                    if temp_backup and os.path.exists(temp_backup):
                        os.remove(temp_backup)
                    
                    # Показываем сообщение об успехе
                    alert = NSAlert.alloc().init()
                    alert.setMessageText_(t('database_restored'))
                    alert.setInformativeText_(t('database_restore_success'))
                    alert.setAlertStyle_(NSAlertStyleInformational)
                    alert.addButtonWithTitle_("OK")
                    alert.runModal()
                    
                    NSLog(f"Database restored from: {backup_path}")
                    
                except Exception as restore_error:
                    # Восстанавливаем из временного бекапа при ошибке
                    if temp_backup and os.path.exists(temp_backup):
                        shutil.copy2(temp_backup, db_path)
                        os.remove(temp_backup)
                    raise restore_error
        
        except Exception as e:
            NSLog(f"Restore error: {e}")
            import traceback
            traceback.print_exc()
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('restore_error'))
            alert.setInformativeText_(str(e))
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
    
    def saveAllSettings_(self, sender):
        """Сохранение всех настроек и перезапуск приложения"""
        try:
            # 1. Валидация интервала напоминаний
            interval_str = self.reminderIntervalField.stringValue().strip()
            
            try:
                interval = int(interval_str)
            except ValueError:
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_("Пожалуйста, введите корректное число для интервала напоминаний")
                alert.setAlertStyle_(NSAlertStyleWarning)
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
            
            # Проверяем диапазон (1-1440 минут = 24 часа)
            if interval < 1 or interval > 1440:
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_("Интервал должен быть от 1 до 1440 минут")
                alert.setAlertStyle_(NSAlertStyleWarning)
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
            
            # 2. Получаем выбранный язык
            selected_index = self.languagePopup.indexOfSelectedItem()
            lang_codes = ['en', 'ru', 'uk', 'hu']
            lang_code = lang_codes[selected_index]
            
            # 3. Сохраняем все настройки в NSUserDefaults
            defaults = NSUserDefaults.standardUserDefaults()
            defaults.setInteger_forKey_(interval, "reminderInterval")
            defaults.setObject_forKey_(lang_code, "interfaceLanguage")
            defaults.synchronize()
            
            NSLog(f"Сохранены настройки: интервал={interval} мин, язык={lang_code}")
            
            # 4. Показываем сообщение о сохранении и перезапуске
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('setting_saved'))
            alert.setInformativeText_("Настройки сохранены. Приложение будет перезапущено.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            
            # 5. Перезапускаем приложение
            self.restartApplication()
            
        except Exception as e:
            NSLog(f"Ошибка сохранения настроек: {e}")
            import traceback
            traceback.print_exc()
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_(str(e))
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
    
    def restartApplication(self):
        """Перезапуск приложения"""
        try:
            import subprocess
            import sys
            import os
            
            # Получаем путь к исполняемому файлу
            executable = sys.executable
            
            NSLog(f"Перезапуск приложения: {executable}")
            
            # Закрываем окно настроек
            if hasattr(self, 'window') and self.window:
                self.window.close()
            
            # Запускаем новый процесс
            # Передаем текущее окружение, чтобы сохранить переменные типа MTIMER_DEV
            env = os.environ.copy()
            subprocess.Popen([executable] + sys.argv, env=env)
            
            # Завершаем текущий процесс
            NSApplication.sharedApplication().terminate_(None)
            
        except Exception as e:
            NSLog(f"Ошибка перезапуска приложения: {e}")
            import traceback
            traceback.print_exc()
    
    def saveLanguage_(self, sender):
        """Сохраняет выбранный язык интерфейса"""
        try:
            # Получаем индекс выбранного языка
            idx = self.languagePopup.indexOfSelectedItem()
            
            # Определяем код языка
            lang_code = None
            lang_name = None
            if idx == 0:
                lang_code = 'en'
                lang_name = t('language_english')
            elif idx == 1:
                lang_code = 'ru'
                lang_name = t('language_russian')
            elif idx == 2:
                lang_code = 'uk'
                lang_name = t('language_ukrainian')
            
            if not lang_code:
                return
            
            # Сохраняем в NSUserDefaults
            from Foundation import NSUserDefaults
            defaults = NSUserDefaults.standardUserDefaults()
            defaults.setObject_forKey_(lang_code, "interfaceLanguage")
            defaults.synchronize()
            
            NSLog(f"Сохранен язык интерфейса: {lang_code}")
            
            # Показываем сообщение об успехе
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('setting_saved'))
            alert.setInformativeText_(t('language_saved').format(lang_name))
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            
        except Exception as e:
            NSLog(f"Ошибка сохранения языка: {e}")
            import traceback
            traceback.print_exc()
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_(str(e))
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
    
    def saveReminderInterval_(self, sender):
        """Сохраняет интервал напоминаний в настройки"""
        try:
            # Получаем значение из текстового поля
            interval_str = self.reminderIntervalField.stringValue().strip()
            
            # Проверяем, что введено число
            try:
                interval = int(interval_str)
            except ValueError:
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_(t('enter_integer'))
                alert.setAlertStyle_(NSAlertStyleWarning)
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
            
            # Проверяем диапазон (от 1 до 1440 минут = 24 часа)
            if interval < 1 or interval > 1440:
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_(t('interval_range'))
                alert.setAlertStyle_(NSAlertStyleWarning)
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
            
            # Сохраняем в NSUserDefaults
            defaults = NSUserDefaults.standardUserDefaults()
            defaults.setInteger_forKey_(interval, "reminderInterval")
            defaults.synchronize()
            
            NSLog(f"Сохранен интервал напоминаний: {interval} минут")
            
            # Показываем сообщение об успехе
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('setting_saved'))
            alert.setInformativeText_(t('interval_saved').format(interval))
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            
        except Exception as e:
            NSLog(f"Ошибка сохранения интервала напоминаний: {e}")
            import traceback
            traceback.print_exc()
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_(str(e))
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_("OK")
            alert.runModal()
    
    def saveProject_(self, sender):
        """Сохраняем изменения выбранного проекта или создаем новый"""
        row = self.tableView.selectedRow()
        new_name = self.nameField.stringValue().strip()
        try:
            new_rate = float(self.rateField.stringValue())
        except ValueError:
            new_rate = 0
        
        # Определяем выбранную компанию
        company_id = None
        if self.companyPopup:
            selected_idx = self.companyPopup.indexOfSelectedItem()
            if selected_idx > 0:  # 0 = "Без компании"
                company_id = self.companies[selected_idx - 1]['id']
        
        if not new_name:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_("Введіть назву проекту")
            alert.addButtonWithTitle_(t('ok'))
            alert.runModal()
            return
        
        # Если проект не выбран - создаем новый
        if row < 0 or row >= len(self.projects):
            NSLog(f"Creating new project: {new_name}, rate: {new_rate}, company_id: {company_id}")
            try:
                project_id = self.db.create_project(new_name, hourly_rate=new_rate, company_id=company_id)
                if project_id:
                    NSLog(f"Project '{new_name}' created successfully with ID: {project_id}")
                    
                    # Оновлюємо таблицю
                    self.reloadProjects()
                    self.tableView.reloadData()
                    
                    # Очищаємо поля
                    self.nameField.setStringValue_("")
                    self.rateField.setStringValue_("0")
                    if self.companyPopup:
                        self.companyPopup.selectItemAtIndex_(0)
                    
                    # Оновлюємо основне вікно
                    try:
                        app = NSApp.delegate()
                        if app and hasattr(app, 'controller') and app.controller is not None:
                            app.controller.reloadProjects()
                            try:
                                app.updateStatusItem()
                            except Exception:
                                pass
                    except Exception as e:
                        NSLog(f"Error updating main window: {e}")
                else:
                    alert = NSAlert.alloc().init()
                    alert.setMessageText_(t('error'))
                    alert.setInformativeText_(f"Проект з назвою '{new_name}' вже існує")
                    alert.addButtonWithTitle_(t('ok'))
                    alert.runModal()
            except Exception as e:
                NSLog(f"Error creating project: {e}")
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_(f"Помилка при створенні проекту: {str(e)}")
                alert.addButtonWithTitle_(t('ok'))
                alert.runModal()
            return
        
        # Если проект выбран - обновляем существующий
        project = self.projects[row]
        NSLog(f"Updating project {project['id']}: {new_name}, ${new_rate}/ч, company_id={company_id}")
        
        # Обновляем в БД
        if self.db.update_project(project['id'], new_name, new_rate, company_id):
            NSLog(f"Проект {project['id']} обновлён")
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
            alert.setMessageText_(t('error'))
            alert.setInformativeText_("Не удалось обновить проект")
            alert.addButtonWithTitle_(t('ok'))
            alert.runModal()
    
    def createNewProject_(self, sender):
        """Створення нового проекту"""
        NSLog("=== createNewProject_ CALLED in ProjectSettings ===")
        print("[DEBUG] createNewProject_ function called in ProjectSettings")
        
        # Очищаємо поля
        self.nameField.setStringValue_("")
        self.rateField.setStringValue_("0")
        if self.companyPopup:
            self.companyPopup.selectItemAtIndex_(0)  # "Без компанії"
        
        # Знімаємо виділення в таблиці
        self.tableView.deselectAll_(None)
        
        # Фокусуємось на полі імені
        self.window.makeFirstResponder_(self.nameField)
        
        # Змінюємо текст кнопки "Зберегти" на "Створити"
        self.saveBtn.setTitle_(t('create'))
        self.saveBtn.setAction_(objc.selector(self.createProjectAction_, signature=b"v@:"))
    
    def createProjectAction_(self, sender):
        """Виконання створення нового проекту"""
        NSLog("=== createProjectAction_ CALLED ===")
        new_name = self.nameField.stringValue().strip()
        try:
            new_rate = float(self.rateField.stringValue())
        except ValueError:
            new_rate = 0
        
        # Определяем выбранную компанию
        company_id = None
        if self.companyPopup:
            selected_idx = self.companyPopup.indexOfSelectedItem()
            if selected_idx > 0:  # 0 = "Без компании"
                company_id = self.companies[selected_idx - 1]['id']
        
        if not new_name:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_("Введіть назву проекту")
            alert.addButtonWithTitle_(t('ok'))
            alert.runModal()
            return
        
        # Створюємо проект в БД
        NSLog(f"Attempting to create project: {new_name}, rate: {new_rate}, company_id: {company_id}")
        NSLog(f"Database path: {self.db.db_path}")
        
        try:
            project_id = self.db.create_project(new_name, hourly_rate=new_rate, company_id=company_id)
            NSLog(f"Project creation result: {project_id}")
            
            if project_id:
                NSLog(f"Project '{new_name}' created successfully with ID: {project_id}")
                
                # Оновлюємо таблицю
                self.reloadProjects()
                self.tableView.reloadData()
                
                # Очищаємо поля
                self.nameField.setStringValue_("")
                self.rateField.setStringValue_("0")
                if self.companyPopup:
                    self.companyPopup.selectItemAtIndex_(0)  # "Без компанії"
                
                # Повертаємо кнопку до режиму "Зберегти"
                self.saveBtn.setTitle_(t('save'))
                self.saveBtn.setAction_(objc.selector(self.saveProject_, signature=b"v@:"))
                
                # Оновлюємо основне вікно
                try:
                    app = NSApp.delegate()
                    if app and hasattr(app, 'controller') and app.controller is not None:
                        app.controller.reloadProjects()
                except Exception as e:
                    NSLog(f"Error updating main window: {e}")
            else:
                NSLog(f"Failed to create project '{new_name}' - project with this name may already exist")
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_(f"Проект з назвою '{new_name}' вже існує")
                alert.addButtonWithTitle_(t('ok'))
                alert.runModal()
        except Exception as e:
            NSLog(f"Error creating project: {e}")
            import traceback
            NSLog(f"Traceback: {traceback.format_exc()}")
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('error'))
            alert.setInformativeText_(f"Помилка при створенні проекту: {str(e)}")
            alert.addButtonWithTitle_(t('ok'))
            alert.runModal()
    
    def deleteProject_(self, sender):
        """Удаление выбранного проекта"""
        try:
            row = self.tableView.selectedRow()
            NSLog(f"deleteProject_ called, selected row: {row}")
            if row < 0 or row >= len(self.projects):
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_("Выберите проект для удаления")
                alert.addButtonWithTitle_(t('ok'))
                alert.runModal()
                return
            
            project = self.projects[row]
            NSLog(f"Attempting to delete project: {project['id']} - {project['name']}")
            
            # Проверяем, есть ли сессии у проекта
            has_sessions = self.db.has_sessions_for_project(project['id'])
            
            # Показываем подтверждение с учетом наличия сессий
            alert = NSAlert.alloc().init()
            alert.setMessageText_(t('delete_project'))
            if has_sessions:
                alert.setInformativeText_(f"{t('confirm_delete_project')}\n\n⚠️ У цього проекту є записи часу. Вони також будуть видалені!")
            else:
                alert.setInformativeText_(t('confirm_delete_project'))
            alert.addButtonWithTitle_(t('delete'))
            alert.addButtonWithTitle_(t('cancel'))
            alert.setAlertStyle_(NSAlertStyleWarning)
            
            response = alert.runModal()
            NSLog(f"User response: {response}")
            if response != 1000:  # 1000 = первая кнопка (Delete/Удалить)
                NSLog("User cancelled deletion")
                return
            
            # Удаляем проект (с сессиями если они есть)
            NSLog(f"Calling db.delete_project({project['id']}, force={has_sessions})")
            result = self.db.delete_project(project['id'], force=has_sessions)
            NSLog(f"delete_project returned: {result}")
            
            if result:
                NSLog(f"Проект {project['id']} удалён")
                self.reloadProjects()
                self.tableView.reloadData()
                
                # Очищаем поля
                self.nameField.setStringValue_("")
                self.rateField.setStringValue_("0")
                if self.companyPopup:
                    self.companyPopup.selectItemAtIndex_(0)
                
                # Обновляем основное окно
                try:
                    app = NSApp.delegate()
                    if app and hasattr(app, 'controller') and app.controller is not None:
                        # Если удалили текущий выбранный проект — переключимся на "Все проекты"
                        try:
                            if getattr(app.controller, 'selected_project_id', None) == project['id']:
                                app.controller.selected_project_id = -1
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
                # Не удалось удалить
                alert = NSAlert.alloc().init()
                alert.setMessageText_(t('error'))
                alert.setInformativeText_(t('cannot_delete_project'))
                alert.addButtonWithTitle_(t('ok'))
                alert.setAlertStyle_(NSAlertStyleCritical)
                alert.runModal()
        except Exception as e:
            NSLog(f"ERROR in deleteProject_: {e}")
            import traceback
            NSLog(f"Traceback: {traceback.format_exc()}")
            print(f"ERROR in deleteProject_: {e}")
            traceback.print_exc()


class CompaniesWindowController(NSObject):
    """Окно управления компаниями"""
    def init(self):
        self = objc.super(CompaniesWindowController, self).init()
        if self is None:
            return None
        self.db = Database()
        self.companies = []
        self.setupUI()
        self.reloadData()
        return self
    
    def setupUI(self):
        # Создаем окно
        screen = NSScreen.mainScreen().frame()
        width, height = 600, 400
        x = (screen.size.width - width) / 2
        y = (screen.size.height - height) / 2
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask,
            2,
            False
        )
        self.window.setTitle_(t('manage_companies'))
        self.window.setReleasedWhenClosed_(False)
        
        content = self.window.contentView()
        
        # Таблица компаний
        scrollView = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 60, width-40, height-100))
        scrollView.setHasVerticalScroller_(True)
        
        self.tableView = NSTableView.alloc().init()
        self.tableView.setDelegate_(self)
        self.tableView.setDataSource_(self)
        
        col1 = NSTableColumn.alloc().initWithIdentifier_("code")
        col1.setTitle_(t('code'))
        col1.setWidth_(100)
        self.tableView.addTableColumn_(col1)
        
        col2 = NSTableColumn.alloc().initWithIdentifier_("name")
        col2.setTitle_(t('company_name'))
        col2.setWidth_(400)
        self.tableView.addTableColumn_(col2)
        
        scrollView.setDocumentView_(self.tableView)
        content.addSubview_(scrollView)
        
        # Кнопки
        addBtn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 20, 100, 32))
        addBtn.setTitle_(t('add'))
        addBtn.setBezelStyle_(NSBezelStyleRounded)
        addBtn.setTarget_(self)
        addBtn.setAction_(objc.selector(self.addCompany_, signature=b"v@:@"))
        content.addSubview_(addBtn)
        
        editBtn = NSButton.alloc().initWithFrame_(NSMakeRect(130, 20, 120, 32))
        editBtn.setTitle_(t('edit'))
        editBtn.setBezelStyle_(NSBezelStyleRounded)
        editBtn.setTarget_(self)
        editBtn.setAction_(objc.selector(self.editCompany_, signature=b"v@:@"))
        content.addSubview_(editBtn)
        
        delBtn = NSButton.alloc().initWithFrame_(NSMakeRect(260, 20, 100, 32))
        delBtn.setTitle_(t('delete'))
        delBtn.setBezelStyle_(NSBezelStyleRounded)
        delBtn.setTarget_(self)
        delBtn.setAction_(objc.selector(self.deleteCompany_, signature=b"v@:@"))
        content.addSubview_(delBtn)
    
    def reloadData(self):
        self.companies = self.db.get_all_companies()
        if self.tableView:
            self.tableView.reloadData()
    
    def numberOfRowsInTableView_(self, tableView):
        return len(self.companies)
    
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        if row >= len(self.companies):
            return ""
        company = self.companies[row]
        identifier = tableColumn.identifier()
        if identifier == "code":
            return company['code']
        elif identifier == "name":
            return company['name']
        return ""
    
    def addCompany_(self, sender):
        # Создаем диалог с полями ввода
        alert = NSAlert.alloc().init()
        alert.setMessageText_(t('add_company'))
        alert.setInformativeText_(t('enter_code_and_name'))
        alert.addButtonWithTitle_(t('create'))
        alert.addButtonWithTitle_(t('cancel'))
        
        # Создаем view с полями ввода
        accessoryView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 110))
        
        # Поле "Код"
        codeLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 85, 100, 20))
        codeLabel.setStringValue_(t('code') + ":")
        codeLabel.setBezeled_(False)
        codeLabel.setDrawsBackground_(False)
        codeLabel.setEditable_(False)
        codeLabel.setSelectable_(False)
        accessoryView.addSubview_(codeLabel)
        
        codeField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 60, 300, 25))
        codeField.setPlaceholderString_("Например: 12345678")
        accessoryView.addSubview_(codeField)
        
        # Поле "Название"
        nameLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 35, 100, 20))
        nameLabel.setStringValue_(t('name') + ":")
        nameLabel.setBezeled_(False)
        nameLabel.setDrawsBackground_(False)
        nameLabel.setEditable_(False)
        nameLabel.setSelectable_(False)
        accessoryView.addSubview_(nameLabel)
        
        nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 10, 300, 25))
        nameField.setPlaceholderString_(t('full_company_name'))
        accessoryView.addSubview_(nameField)
        
        alert.setAccessoryView_(accessoryView)
        alert.window().setInitialFirstResponder_(codeField)
        
        if alert.runModal() == 1000:
            code = codeField.stringValue().strip()
            name = nameField.stringValue().strip()
            
            if not code or not name:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Код и название обязательны для заполнения")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
                return
            
            if self.db.create_company(code, name):
                self.reloadData()
            else:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Компания с таким кодом уже существует")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
    
    def editCompany_(self, sender):
        # Проверяем, выбрана ли строка
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(self.companies):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Ошибка")
            alert.setInformativeText_("Выберите компанию для редактирования")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        
        company = self.companies[row]
        
        # Создаем диалог с полями ввода
        alert = NSAlert.alloc().init()
        alert.setMessageText_(t('edit_company'))
        alert.setInformativeText_(t('change_code_and_name'))
        alert.addButtonWithTitle_(t('save'))
        alert.addButtonWithTitle_(t('cancel'))
        
        # Создаем view с полями ввода
        accessoryView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 110))
        
        # Поле "Идентификационный код"
        codeLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 85, 200, 20))
        codeLabel.setStringValue_(t('identification_code'))
        codeLabel.setBezeled_(False)
        codeLabel.setDrawsBackground_(False)
        codeLabel.setEditable_(False)
        codeLabel.setSelectable_(False)
        accessoryView.addSubview_(codeLabel)
        
        codeField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 60, 300, 25))
        codeField.setStringValue_(company['code'])
        codeField.setPlaceholderString_("Например: 12345678")
        accessoryView.addSubview_(codeField)
        
        # Поле "Название"
        nameLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 35, 100, 20))
        nameLabel.setStringValue_(t('name') + ":")
        nameLabel.setBezeled_(False)
        nameLabel.setDrawsBackground_(False)
        nameLabel.setEditable_(False)
        nameLabel.setSelectable_(False)
        accessoryView.addSubview_(nameLabel)
        
        nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 10, 300, 25))
        nameField.setStringValue_(company['name'])
        nameField.setPlaceholderString_(t('full_company_name'))
        accessoryView.addSubview_(nameField)
        
        alert.setAccessoryView_(accessoryView)
        alert.window().setInitialFirstResponder_(codeField)
        
        if alert.runModal() == 1000:
            code = codeField.stringValue().strip()
            name = nameField.stringValue().strip()
            
            if not code or not name:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Код и название обязательны для заполнения")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
                return
            
            if self.db.update_company(company['id'], code, name):
                self.reloadData()
            else:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Компания с таким кодом уже существует")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
    
    def deleteCompany_(self, sender):
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(self.companies):
            return
        
        company = self.companies[row]
        if not self.db.delete_company(company['id']):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Ошибка")
            alert.setInformativeText_("Невозможно удалить компанию, так как с ней связаны проекты")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        
        self.reloadData()


class WorkTypesWindowController(NSObject):
    """Окно управления видами работ"""
    def init(self):
        self = objc.super(WorkTypesWindowController, self).init()
        if self is None:
            return None
        self.db = Database()
        self.work_types = []
        self.setupUI()
        self.reloadData()
        return self
    
    def setupUI(self):
        # Создаем окно
        screen = NSScreen.mainScreen().frame()
        width, height = 600, 400
        x = (screen.size.width - width) / 2
        y = (screen.size.height - height) / 2
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask,
            2,
            False
        )
        self.window.setTitle_(t('manage_work_types'))
        self.window.setReleasedWhenClosed_(False)
        
        content = self.window.contentView()
        
        # Таблица видов работ
        scrollView = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 60, width-40, height-100))
        scrollView.setHasVerticalScroller_(True)
        
        self.tableView = NSTableView.alloc().init()
        self.tableView.setDelegate_(self)
        self.tableView.setDataSource_(self)
        
        col1 = NSTableColumn.alloc().initWithIdentifier_("name")
        col1.setTitle_(t('name'))
        col1.setWidth_(200)
        self.tableView.addTableColumn_(col1)
        
        col2 = NSTableColumn.alloc().initWithIdentifier_("description")
        col2.setTitle_(t('description'))
        col2.setWidth_(350)
        self.tableView.addTableColumn_(col2)
        
        scrollView.setDocumentView_(self.tableView)
        content.addSubview_(scrollView)
        
        # Кнопки
        addBtn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 20, 100, 32))
        addBtn.setTitle_(t('add'))
        addBtn.setBezelStyle_(NSBezelStyleRounded)
        addBtn.setTarget_(self)
        addBtn.setAction_(objc.selector(self.addWorkType_, signature=b"v@:@"))
        content.addSubview_(addBtn)
        
        editBtn = NSButton.alloc().initWithFrame_(NSMakeRect(130, 20, 120, 32))
        editBtn.setTitle_(t('edit'))
        editBtn.setBezelStyle_(NSBezelStyleRounded)
        editBtn.setTarget_(self)
        editBtn.setAction_(objc.selector(self.editWorkType_, signature=b"v@:@"))
        content.addSubview_(editBtn)
        
        delBtn = NSButton.alloc().initWithFrame_(NSMakeRect(260, 20, 100, 32))
        delBtn.setTitle_(t('delete'))
        delBtn.setBezelStyle_(NSBezelStyleRounded)
        delBtn.setTarget_(self)
        delBtn.setAction_(objc.selector(self.deleteWorkType_, signature=b"v@:@"))
        content.addSubview_(delBtn)
    
    def reloadData(self):
        self.work_types = self.db.get_all_work_types()
        if self.tableView:
            self.tableView.reloadData()
    
    def numberOfRowsInTableView_(self, tableView):
        return len(self.work_types)
    
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        if row >= len(self.work_types):
            return ""
        work_type = self.work_types[row]
        identifier = tableColumn.identifier()
        if identifier == "name":
            return work_type['name']
        elif identifier == "description":
            return work_type['description'] or ""
        return ""
    
    def addWorkType_(self, sender):
        # Создаем диалог с полями ввода
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Новый вид работы")
        alert.setInformativeText_("Введите название и описание вида работы")
        alert.addButtonWithTitle_("Создать")
        alert.addButtonWithTitle_("Отмена")
        
        # Создаем view с полями ввода
        accessoryView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 110))
        
        # Поле "Название"
        nameLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 85, 100, 20))
        nameLabel.setStringValue_("Название:")
        nameLabel.setBezeled_(False)
        nameLabel.setDrawsBackground_(False)
        nameLabel.setEditable_(False)
        nameLabel.setSelectable_(False)
        accessoryView.addSubview_(nameLabel)
        
        nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 60, 300, 25))
        nameField.setPlaceholderString_("Например: Разработка")
        accessoryView.addSubview_(nameField)
        
        # Поле "Описание"
        descLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 35, 100, 20))
        descLabel.setStringValue_("Описание:")
        descLabel.setBezeled_(False)
        descLabel.setDrawsBackground_(False)
        descLabel.setEditable_(False)
        descLabel.setSelectable_(False)
        accessoryView.addSubview_(descLabel)
        
        descField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 10, 300, 25))
        descField.setPlaceholderString_("Краткое описание вида работы")
        accessoryView.addSubview_(descField)
        
        alert.setAccessoryView_(accessoryView)
        alert.window().setInitialFirstResponder_(nameField)
        
        if alert.runModal() == 1000:
            name = nameField.stringValue().strip()
            description = descField.stringValue().strip()
            
            if not name:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Название обязательно для заполнения")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
                return
            
            if self.db.create_work_type(name, description):
                self.reloadData()
            else:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Вид работы с таким названием уже существует")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
    
    def editWorkType_(self, sender):
        # Проверяем, выбрана ли строка
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(self.work_types):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Ошибка")
            alert.setInformativeText_("Выберите вид работы для редактирования")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        
        work_type = self.work_types[row]
        
        # Создаем диалог с полями ввода
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Редактирование вида работы")
        alert.setInformativeText_("Измените название и описание вида работы")
        alert.addButtonWithTitle_("Сохранить")
        alert.addButtonWithTitle_("Отмена")
        
        # Создаем view с полями ввода
        accessoryView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 110))
        
        # Поле "Название"
        nameLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 85, 100, 20))
        nameLabel.setStringValue_("Название:")
        nameLabel.setBezeled_(False)
        nameLabel.setDrawsBackground_(False)
        nameLabel.setEditable_(False)
        nameLabel.setSelectable_(False)
        accessoryView.addSubview_(nameLabel)
        
        nameField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 60, 300, 25))
        nameField.setStringValue_(work_type['name'])
        nameField.setPlaceholderString_("Например: Разработка")
        accessoryView.addSubview_(nameField)
        
        # Поле "Описание"
        descLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 35, 100, 20))
        descLabel.setStringValue_("Описание:")
        descLabel.setBezeled_(False)
        descLabel.setDrawsBackground_(False)
        descLabel.setEditable_(False)
        descLabel.setSelectable_(False)
        accessoryView.addSubview_(descLabel)
        
        descField = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 10, 300, 25))
        descField.setStringValue_(work_type['description'] or "")
        descField.setPlaceholderString_("Краткое описание вида работы")
        accessoryView.addSubview_(descField)
        
        alert.setAccessoryView_(accessoryView)
        alert.window().setInitialFirstResponder_(nameField)
        
        if alert.runModal() == 1000:
            name = nameField.stringValue().strip()
            description = descField.stringValue().strip()
            
            if not name:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Название обязательно для заполнения")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
                return
            
            if self.db.update_work_type(work_type['id'], name, description):
                self.reloadData()
            else:
                errorAlert = NSAlert.alloc().init()
                errorAlert.setMessageText_("Ошибка")
                errorAlert.setInformativeText_("Вид работы с таким названием уже существует")
                errorAlert.addButtonWithTitle_("OK")
                errorAlert.runModal()
    
    def deleteWorkType_(self, sender):
        row = self.tableView.selectedRow()
        if row < 0 or row >= len(self.work_types):
            return
        
        work_type = self.work_types[row]
        if not self.db.delete_work_type(work_type['id']):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Ошибка")
            alert.setInformativeText_("Невозможно удалить вид работы, так как с ним связаны сессии")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        
        self.reloadData()


class AllTasksWindowController(NSObject):
    """Вікно для перегляду всіх виконаних задач"""
    def init(self):
        self = objc.super(AllTasksWindowController, self).init()
        if self is None:
            return None
        self.db = Database()
        self.all_sessions = []
        self.window = None
        self.tableView = None
        self.filterPopup = None
        self.projectPopup = None
        self.projects_cache = []
        self.selected_project_id = None
        self.current_filter = 'all'  # За замовчуванням - всі задачі
        return self
    
    def showWindow(self):
        if self.window is None:
            self.setupUI()
        self.reloadData()
        self.window.makeKeyAndOrderFront_(None)
    
    def setupUI(self):
        # Створюємо вікно
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        width = 900
        height = 600
        x = (screen_frame.size.width - width) / 2
        y = (screen_frame.size.height - height) / 2
        
        # Імпортуємо додаткові константи для масштабування
        try:
            from Cocoa import NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskResizable, NSWindowStyleMaskMiniaturizable
            style_mask = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable | NSWindowStyleMaskMiniaturizable
        except ImportError:
            style_mask = NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask | 4  # 4 = NSMiniaturizableWindowMask
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            style_mask,
            2,
            False
        )
        self.window.setTitle_(t('all_tasks'))
        self.window.setReleasedWhenClosed_(False)
        
        # Встановлюємо мінімальний і максимальний розмір вікна
        from Cocoa import NSMakeSize
        self.window.setMinSize_(NSMakeSize(600, 400))
        self.window.setMaxSize_(NSMakeSize(1600, 1200))
        
        content = self.window.contentView()
        
        # Імпортуємо константи для autoresizing
        try:
            from Cocoa import NSViewWidthSizable, NSViewHeightSizable, NSViewMinXMargin
        except ImportError:
            NSViewWidthSizable = 2
            NSViewHeightSizable = 16
            NSViewMinXMargin = 4
        
        # Фільтри зверху
        filterY = height - 60
        
        # Label "Фільтр:"
        filterLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, filterY, 60, 20))
        filterLabel.setStringValue_(t('period'))
        filterLabel.setBezeled_(False)
        filterLabel.setDrawsBackground_(False)
        filterLabel.setEditable_(False)
        content.addSubview_(filterLabel)
        
        # Popup для вибору періоду
        self.filterPopup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(90, filterY, 150, 28), False)
        self.filterPopup.addItemWithTitle_(t('all'))
        self.filterPopup.addItemWithTitle_(t('today'))
        self.filterPopup.addItemWithTitle_(t('week'))
        self.filterPopup.addItemWithTitle_(t('month'))
        self.filterPopup.setTarget_(self)
        self.filterPopup.setAction_(objc.selector(self.filterChanged_, signature=b"v@:"))
        content.addSubview_(self.filterPopup)
        
        # Label "Проект:"
        projectLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(270, filterY, 60, 20))
        projectLabel.setStringValue_(t('project') + ':')
        projectLabel.setBezeled_(False)
        projectLabel.setDrawsBackground_(False)
        projectLabel.setEditable_(False)
        content.addSubview_(projectLabel)
        
        # Popup для вибору проекту
        self.projectPopup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(340, filterY, 250, 28), False)
        self.projectPopup.setTarget_(self)
        self.projectPopup.setAction_(objc.selector(self.projectChanged_, signature=b"v@:"))
        content.addSubview_(self.projectPopup)
        
        # Label з загальною статистикою
        self.statsLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(600, filterY, 280, 20))
        self.statsLabel.setStringValue_("Всього: 0 задач, 00:00:00, $0.00")
        self.statsLabel.setBezeled_(False)
        self.statsLabel.setDrawsBackground_(False)
        self.statsLabel.setEditable_(False)
        self.statsLabel.setAlignment_(2)  # Right align
        self.statsLabel.setAutoresizingMask_(NSViewMinXMargin)  # Прилипає до правого краю
        content.addSubview_(self.statsLabel)
        
        # Таблиця задач
        tableY = 20
        tableHeight = height - 100
        scrollView = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, tableY, width-40, tableHeight))
        scrollView.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)  # Розтягується по ширині та висоті
        self.tableView = NSTableView.alloc().initWithFrame_(scrollView.bounds())
        
        # Колонки таблиці
        col1 = NSTableColumn.alloc().initWithIdentifier_("description")
        col1.setWidth_((width-40) * 0.30)
        col1.headerCell().setStringValue_("Опис")
        self.tableView.addTableColumn_(col1)
        
        col2 = NSTableColumn.alloc().initWithIdentifier_("project")
        col2.setWidth_((width-40) * 0.18)
        col2.headerCell().setStringValue_("Проект")
        self.tableView.addTableColumn_(col2)
        
        col3 = NSTableColumn.alloc().initWithIdentifier_("date")
        col3.setWidth_((width-40) * 0.12)
        col3.headerCell().setStringValue_("Дата")
        self.tableView.addTableColumn_(col3)
        
        col4 = NSTableColumn.alloc().initWithIdentifier_("time")
        col4.setWidth_((width-40) * 0.15)
        col4.headerCell().setStringValue_("Час")
        self.tableView.addTableColumn_(col4)
        
        col5 = NSTableColumn.alloc().initWithIdentifier_("duration")
        col5.setWidth_((width-40) * 0.12)
        col5.headerCell().setStringValue_("Тривалість")
        self.tableView.addTableColumn_(col5)
        
        col6 = NSTableColumn.alloc().initWithIdentifier_("cost")
        col6.setWidth_((width-40) * 0.13)
        col6.headerCell().setStringValue_("Вартість")
        self.tableView.addTableColumn_(col6)
        
        self.tableView.setDelegate_(self)
        self.tableView.setDataSource_(self)
        
        scrollView.setDocumentView_(self.tableView)
        scrollView.setHasVerticalScroller_(True)
        content.addSubview_(scrollView)
        
        # Зберігаємо scrollView для подальшого використання
        self.scrollView = scrollView
        
        # Встановлюємо делегат вікна для відстеження зміни розміру
        self.window.setDelegate_(self)
        
        # Завантажуємо список проектів
        self.loadProjects()
    
    def loadProjects(self):
        """Завантажити список проектів"""
        self.projects_cache = self.db.get_all_projects()
        self.projectPopup.removeAllItems()
        self.projectPopup.addItemWithTitle_(t('all_projects'))
        for p in self.projects_cache:
            self.projectPopup.addItemWithTitle_(p['name'])
    
    def filterChanged_(self, sender):
        """Обробка зміни фільтра періоду"""
        idx = self.filterPopup.indexOfSelectedItem()
        if idx == 0:
            self.current_filter = 'all'
        elif idx == 1:
            self.current_filter = 'today'
        elif idx == 2:
            self.current_filter = 'week'
        elif idx == 3:
            self.current_filter = 'month'
        self.reloadData()
    
    def projectChanged_(self, sender):
        """Обробка зміни проекту"""
        idx = self.projectPopup.indexOfSelectedItem()
        if idx == 0:
            self.selected_project_id = None
        else:
            project = self.projects_cache[idx - 1]
            self.selected_project_id = project['id']
        self.reloadData()
    
    def reloadData(self):
        """Перезавантажити дані задач"""
        if self.current_filter == 'all':
            # Отримуємо всі задачі
            if self.selected_project_id is not None:
                self.all_sessions = [dict(row) for row in self.db.get_all_sessions_by_project(self.selected_project_id)]
            else:
                self.all_sessions = [dict(row) for row in self.db.get_all_sessions()]
        else:
            # Отримуємо задачі за фільтром
            if self.selected_project_id is not None:
                self.all_sessions = [dict(row) for row in self.db.get_sessions_by_project(self.selected_project_id, self.current_filter)]
            else:
                self.all_sessions = [dict(row) for row in self.db.get_sessions_by_filter(self.current_filter)]
        
        # Оновлюємо статистику
        total_duration = sum(s['duration'] for s in self.all_sessions)
        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60
        seconds = total_duration % 60
        
        # Рахуємо загальну вартість
        total_cost = 0
        for s in self.all_sessions:
            duration_hours = s['duration'] / 3600.0
            hourly_rate = s.get('hourly_rate', 0) or 0
            total_cost += duration_hours * hourly_rate
        
        self.statsLabel.setStringValue_(f"Всього: {len(self.all_sessions)} задач, {hours:02d}:{minutes:02d}:{seconds:02d}, ${total_cost:.2f}")
        
        self.tableView.reloadData()
    
    # NSTableView DataSource методи
    def numberOfRowsInTableView_(self, tableView):
        return len(self.all_sessions)
    
    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        if row >= len(self.all_sessions):
            return ""
        
        session = self.all_sessions[row]
        identifier = tableColumn.identifier()
        
        if identifier == "description":
            return session.get('description', '')
        elif identifier == "project":
            project_id = session.get('project_id')
            if project_id:
                project = next((p for p in self.projects_cache if p['id'] == project_id), None)
                return project['name'] if project else ''
            return ''
        elif identifier == "date":
            start_time = session.get('start_time', '')
            if start_time:
                try:
                    dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%d.%m.%Y')
                except:
                    return start_time.split()[0] if ' ' in start_time else start_time
            return ''
        elif identifier == "time":
            start_time = session.get('start_time', '')
            end_time = session.get('end_time', '')
            if start_time and end_time:
                try:
                    dt_start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                    dt_end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                    return f"{dt_start.strftime('%H:%M')} - {dt_end.strftime('%H:%M')}"
                except:
                    return f"{start_time.split()[1] if ' ' in start_time else start_time}"
            return ''
        elif identifier == "duration":
            duration = session.get('duration', 0)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif identifier == "cost":
            duration = session.get('duration', 0)
            hourly_rate = session.get('hourly_rate', 0) or 0
            if hourly_rate > 0:
                duration_hours = duration / 3600.0
                cost = duration_hours * hourly_rate
                return f"${cost:.2f}"
            return "$0.00"
        
        return ""
    
    def tableView_willDisplayCell_forTableColumn_row_(self, tableView, cell, tableColumn, row):
        """Устанавливаем цвет фона для оплаченных задач"""
        if row >= len(self.all_sessions):
            return
        
        session = self.all_sessions[row]
        is_paid = session.get('paid', 0) == 1
        
        if is_paid:
            # Салатовый фон для оплаченных задач (светло-зеленый)
            # RGB: (217, 242, 217) -> (0.85, 0.95, 0.85)
            paid_color = NSColor.colorWithRed_green_blue_alpha_(0.85, 0.95, 0.85, 1.0)
            cell.setBackgroundColor_(paid_color)
            cell.setDrawsBackground_(True)
        else:
            # Обычный белый фон для неоплаченных
            try:
                # Пытаемся использовать системный цвет фона
                cell.setBackgroundColor_(NSColor.controlBackgroundColor())
            except:
                cell.setBackgroundColor_(NSColor.whiteColor())
            cell.setDrawsBackground_(True)
    
    def windowDidResize_(self, notification):
        """Обробка зміни розміру вікна - оновлюємо ширину колонок"""
        if hasattr(self, 'tableView') and hasattr(self, 'scrollView'):
            # Отримуємо нову ширину scrollView
            frame = self.scrollView.frame()
            new_width = frame.size.width
            
            # Оновлюємо ширину колонок пропорційно
            columns = self.tableView.tableColumns()
            if len(columns) >= 6:
                columns[0].setWidth_(new_width * 0.30)  # Опис
                columns[1].setWidth_(new_width * 0.18)  # Проект
                columns[2].setWidth_(new_width * 0.12)  # Дата
                columns[3].setWidth_(new_width * 0.15)  # Час
                columns[4].setWidth_(new_width * 0.12)  # Тривалість
                columns[5].setWidth_(new_width * 0.13)  # Вартість


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        NSLog("=== AppDelegate: applicationDidFinishLaunching started ===")
        try:
            NSLog("=== Creating TimeTrackerWindowController ===")
            self.controller = TimeTrackerWindowController.alloc().init()
            NSLog("=== Controller created, calling setupUI ===")
            # ВЫЗЫВАЕМ setupUI только после полного запуска приложения
            self.controller.setupUI()
            NSLog("=== setupUI completed ===")
            # ВАЖНО: Сохраняем сильную ссылку на окно, чтобы оно не освобождалось при закрытии
            self.mainWindow = self.controller.window
            NSLog("=== Window reference saved ===")
            # Окно настроек проектов
            self.settingsController = None
            # Меню приложения с Cmd+Q
            NSLog("=== Building menu ===")
            self.buildMenu()
            NSLog("=== Menu built ===")
            # Устанавливаем иконку дока, если доступна
            if not DEV_MODE:
                self._setDockIcon()
                NSLog("=== Dock icon set ===")
            else:
                NSLog("=== DEV_MODE active: dock icon skip ===")
            if not DEV_MODE:
                # Создаем статус-иконку в меню-баре (в dev-режиме не используем, чтобы избежать крашей)
                self._createStatusItem()
                NSLog("=== Status item created ===")
                # Инициализируем её отображение
                self.updateStatusItem()
                NSLog("=== Status item updated ===")
            else:
                NSLog("=== DEV_MODE active: status bar disabled ===")
            NSLog("=== AppDelegate: applicationDidFinishLaunching completed ===")
        except Exception as e:
            NSLog(f"=== ERROR in applicationDidFinishLaunching: {e} ===")
            import traceback
            traceback.print_exc()

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
                t('settings'), objc.selector(self.openSettings_, signature=b"v@:"), ","
            )
            settingsItem.setKeyEquivalentModifierMask_(COMMAND_MASK)
            settingsItem.setTarget_(self)
            appMenu.addItem_(settingsItem)
            
            # Пункт меню Статистика
            statisticsItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('statistics'), objc.selector(self.openStatistics_, signature=b"v@:"), "s"
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

            # Data menu (Данные)
            dataMenuItem = NSMenuItem.alloc().init()
            mainMenu.addItem_(dataMenuItem)
            dataMenu = NSMenu.alloc().initWithTitle_(t('data_menu'))
            
            companiesItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('companies_menu'), objc.selector(self.openCompanies_, signature=b"v@:@"), ""
            )
            companiesItem.setTarget_(self)
            dataMenu.addItem_(companiesItem)
            
            projectsItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('projects_menu'), objc.selector(self.openSettings_, signature=b"v@:@"), ""
            )
            projectsItem.setTarget_(self)
            dataMenu.addItem_(projectsItem)
            
            workTypesItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('work_types_menu'), objc.selector(self.openWorkTypes_, signature=b"v@:@"), ""
            )
            workTypesItem.setTarget_(self)
            dataMenu.addItem_(workTypesItem)
            
            dataMenu.addItem_(NSMenuItem.separatorItem())
            
            # Пункт меню "Статистика (Все задачи)"
            allTasksItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                t('all_tasks'), objc.selector(self.openAllTasks_, signature=b"v@:@"), "a"
            )
            allTasksItem.setKeyEquivalentModifierMask_(COMMAND_MASK | SHIFT_MASK)
            allTasksItem.setTarget_(self)
            dataMenu.addItem_(allTasksItem)
            
            dataMenuItem.setSubmenu_(dataMenu)

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
            
            # Отримуємо поточний фільтр та проєкт з контроллера
            current_filter = getattr(self.controller, 'current_filter', None)
            # Если фильтр не выбран - используем 'month' по умолчанию
            if current_filter is None:
                current_filter = 'month'
            selected_project_id = getattr(self.controller, 'selected_project_id', None)
            
            # Запускаємо статистику в окремому процесі
            # Це дозволяє вікну працювати незалежно від основного застосунку
            
            # Определяем, запущены ли мы из .app bundle
            if getattr(sys, 'frozen', False):
                # Запущены из .app
                bundle_dir = os.environ.get('RESOURCEPATH', os.path.dirname(os.path.abspath(sys.executable)))
                script_dir = bundle_dir
                stats_script = os.path.join(bundle_dir, 'show_stats.py')
                python_exec = sys.executable
            else:
                # Запущены из исходников
                script_dir = _get_base_dir()
                stats_script = os.path.join(script_dir, 'show_stats.py')
                python_exec = sys.executable
            
            # Передаємо параметри як аргументи
            args = [python_exec, stats_script, current_filter, str(selected_project_id)]
            
            NSLog(f"Launching statistics: script={stats_script}, python={python_exec}, cwd={script_dir}")
            
            # Запускаємо в фоні (с выводом для отладки при запуске из .app)
            if getattr(sys, 'frozen', False):
                # В .app показываем вывод для отладки
                subprocess.Popen(args, cwd=script_dir)
            else:
                # Из исходников - скрываем вывод
                subprocess.Popen(args, 
                               cwd=script_dir,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            
            NSLog(f"Statistics window launched: filter={current_filter}, project={selected_project_id}")
                
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
    
    def openCompanies_(self, sender):
        """Открыть окно управления компаниями"""
        if not hasattr(self, 'companiesController') or self.companiesController is None:
            self.companiesController = CompaniesWindowController.alloc().init()
        self.companiesController.window.makeKeyAndOrderFront_(None)
    
    def openWorkTypes_(self, sender):
        """Открыть окно управления видами работ"""
        if not hasattr(self, 'workTypesController') or self.workTypesController is None:
            self.workTypesController = WorkTypesWindowController.alloc().init()
        self.workTypesController.window.makeKeyAndOrderFront_(None)
    
    def openAllTasks_(self, sender):
        """Відкрити вікно зі всіма задачами"""
        if not hasattr(self, 'allTasksController') or self.allTasksController is None:
            self.allTasksController = AllTasksWindowController.alloc().init()
        self.allTasksController.showWindow()
    
    @objc.python_method
    def _setDockIcon(self):
        try:
            base = _get_base_dir()
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
    
    @objc.python_method
    def _setWindowIcon(self, window):
        """Устанавливает иконку для окна"""
        try:
            base = _get_base_dir()
            candidates = [
                os.path.join(base, "assets", "app_icon.icns"),
                os.path.join(base, "assets", "app_icon.png"),
            ]
            for p in candidates:
                if os.path.exists(p):
                    img = NSImage.alloc().initWithContentsOfFile_(p)
                    if img:
                        # Устанавливаем иконку для окна через представленное окно
                        window.setRepresentedURL_(None)
                        window.standardWindowButton_(0).setImage_(img)  # 0 = Close button's document icon
                        break
        except Exception as e:
            NSLog(f"Set window icon error: {e}")

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
                    f"Задача {i+1}", objc.selector(self.switchToTask_, signature=b"v@:"), ""
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
            work_type_name = last_session['work_type_name'] if last_session['work_type_name'] else ''
            project_name = last_session['project_name'] or 'Без названия'
            
            # Выбираем проект в UI
            for idx_popup, p in enumerate(self.controller.projects_cache, start=1):
                if p['id'] == project_id:
                    self.controller.projectPopup.selectItemAtIndex_(idx_popup)
                    break
            
            # Подставляем вид работы (сейчас пока в description field, потом сделаем dropdown)
            if work_type_name:
                self.controller.descriptionField.setStringValue_(work_type_name)
            
            # Запускаем таймер
            self.controller.toggleTimer_(None)
            
            # Отправляем системное уведомление
            self._sendNotification(project_name, work_type_name)
            
        except Exception as e:
            NSLog(f"Error starting last task: {e}")
    
    @objc.python_method
    def _sendNotification(self, project_name, task_description):
        """Отправляет системное уведомление о запуске таймера"""
        try:
            if DEV_MODE:
                NSLog("DEV_MODE: skip notification")
                return
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
            work_type_name = selected_session['work_type_name'] if selected_session['work_type_name'] else ''
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
            
            # Подставляем вид работы
            if work_type_name:
                self.controller.descriptionField.setStringValue_(work_type_name)
            
            # Запускаем новый таймер (только если был запущен ранее или явно кликнули)
            if was_running or True:  # Всегда запускаем
                self.controller.toggleTimer_(None)
                
                # Отправляем уведомление о переключении
                self._sendNotification(project_name, work_type_name)
            
            NSLog(f"Switched to task: {project_name} - {work_type_name}")
            
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
                    work_type_name = session['work_type_name'] if session['work_type_name'] else t('no_description')
                    
                    # Обрезаем длинные названия
                    if len(work_type_name) > 30:
                        work_type_name = work_type_name[:27] + "..."
                    
                    item.setTitle_(f"▸ {project_name}: {work_type_name}")
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
