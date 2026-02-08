# MTimer — Нативний тайм-трекер для macOS

[🇬🇧 English](#english) | [Русский](#russian) | [🇭🇺 Magyar](#hungarian)

> **⚠️ Версія 2.0+**: Підтримує лише процесори Apple Silicon (ARM). Процесори Intel більше не підтримуються.

Інтуїтивний нативний macOS додаток для відстеження часу, витраченого на проєкти. Побудований на PyObjC (AppKit) та SQLite. Підтримує старт/стоп/продовження відстеження, управління проєктами з погодинною ставкою, фільтри періодів, статистику та візуалізацію, мультимовність (українська/англійська/російська/угорська) та автоматичну темну тему.

## Можливості

- ⏱ **Відстеження часу**: Старт/стоп таймера з автоматичним розділенням сесій опівночі
- 📁 **Управління проєктами**: Створення та керування проєктами з погодинними ставками
- 🏢 **Компанії та види робіт**: Організація проєктів за компаніями та категоріями робіт
- 💰 **Розрахунок вартості**: Автоматичний підрахунок вартості на основі погодинної ставки
- 💵 **Статус оплати**: Відстеження оплачених та неоплачених завдань
- 🔍 **Фільтри періодів**: Перегляд сесій за Сьогодні/Тиждень/Місяць/Кастомний період або весь час
- 📊 **Статистика та графіки**: Візуалізація даних з детальними графіками (денна динаміка, розподіл по проєктах, погодинний розподіл)
- 🌐 **Мультимовність**: Автоматичне визначення мови системи (українська/англійська/російська/угорська)
- 🌓 **Темна тема**: Підтримка темної теми з миттєвим перемиканням
- 📋 **Історія сесій**: Детальний список сесій з тривалістю та вартістю
- ⚡ **Меню-бар**: Живий таймер у меню-барі з швидким доступом до останніх завдань
- 🔔 **Сповіщення**: Отримуйте повідомлення при старті та зупинці відстеження
- ✏️ **Керування сесіями**: Редагування деталей проєкту, видалення сесій з підтвердженням
- 💾 **Збереження даних**: Автоматичне відновлення сесій після перезапуску
- 🔄 **Резервне копіювання**: Функції резервного копіювання та відновлення бази даних
- 🪟 **Нативний macOS UI**: Адаптивний інтерфейс на базі AppKit

## Вимоги

- macOS 12+ (Monterey або новіша)
- Python 3.11–3.12 (рекомендовано 3.12)
- **Версія 2.0+**: Процесор Apple Silicon (ARM64). IntelProcessor не підтримується.

## Швидкий старт

### Запуск з вихідного коду

1. Встановіть залежності:
```bash
pip3 install -r requirements.txt
```

2. Запустіть додаток:
```bash
python3 mac_app.py
```

### Збірка автономного додатка

Створення повністю автономного `.app` пакету:

```bash
python3 setup.py py2app
```

Додаток буде створено в `dist/MTimer.app`.

**Примітки:**
- Іконка автоматично включається з `assets/app_icon.icns`
- Бінарні файли автоматично підписуються ad-hoc під час збірки
- Для розповсюдження за межами вашої машини розгляньте підпис Developer ID та нотаризацію
- При першому запуску з Finder може знадобитися підтвердження Gatekeeper (клік правою кнопкою → Відкрити)

## Зберігання даних

- **Автономний додаток**: `~/Library/Application Support/MTimer/timetracker.db`
- **Режим вихідного коду**: `timetracker.db` в кореневій директорії проєкту

## Структура проєкту

```
MTimer/
├── mac_app.py              # Головний macOS UI (AppKit)
├── database.py             # Операції з базою даних SQLite
├── localization.py         # Підтримка мультимовності
├── statistics.py           # Модуль статистики та візуалізації
├── show_stats.py           # Утиліта перегляду статистики
├── setup.py                # Конфігурація збірки py2app
├── requirements.txt        # Python залежності
├── assets/                 # Іконки та ресурси
│   └── app_icon.icns      # Іконка додатка
├── generate_icns.py        # Утиліта генерації іконок
└── update_project_rates.py # Утиліта масового оновлення ставок
```

## Використання

1. **Створіть проєкт**: Натисніть кнопку "+" біля списку проєктів
2. **Встановіть погодинну ставку**: Налаштуйте ставку в налаштуваннях проєкту (⌘,)
3. **Почніть відстеження**: Введіть опис (необов'язково) та натисніть "Старт"
4. **Зупинка/Продовження**: Використовуйте головну кнопку для керування відстеженням
5. **Перегляд історії**: Перемикайте фільтри періодів для перегляду різних проміжків часу
6. **Редагування сесій**: Клік правою кнопкою для видалення сесій або використовуйте Налаштування для редагування проєктів
7. **Меню-бар**: Доступ до швидкого перемикання між останніми завданнями з іконки в меню-барі
8. **Статистика**: Натисніть кнопку "Статистика" для перегляду детальних графіків та аналізу

## Розробка

### Генерація іконки

Якщо потрібно перегенерувати іконку додатка з PNG:

```bash
python3 generate_icns.py  # Створює assets/app_icon.icns
```

### Оновлення ставок проєктів

Масове оновлення погодинних ставок для існуючих проєктів:

```bash
python3 update_project_rates.py
```

### Перегляд статистики

Відображення детальної статистики:

```bash
python3 show_stats.py
```

## Технічні деталі

- **Архітектура**: ARM64 (Apple Silicon) - Версія 2.0+
- **Мінімальна macOS**: 12.0 (Monterey)
- **Версія Python**: 3.11–3.12
- **UI Framework**: PyObjC (AppKit)
- **База даних**: SQLite 3
- **Візуалізація**: Matplotlib з нативним macOS backend
- **Локалізація**: Автоматичне визначення мови системи (UK/EN/RU/HU)

## Скріншоти

*(Додайте скріншоти тут після публікації)*

## Ліцензія

Ліцензія MIT - дивіться файл [LICENSE](LICENSE) для деталей.

## Автор

**Maciborka Vitalik**  
🌐 [it-world.com.ua](https://it-world.com.ua)  
📧 maciborka@gmail.com

## Внесок у проєкт

Внески вітаються! Не соромтеся відкривати issue або надсилати pull request.

## Подяки

Створено за допомогою [PyObjC](https://pyobjc.readthedocs.io/) — Python bindings для macOS frameworks.

---

<a name="english"></a>
# MTimer — Native macOS Time Tracker

[🇺🇦 Українська](#) | [Русский](#russian) | [🇭🇺 Magyar](#hungarian)

> **⚠️ Version 2.0+**: Supports only Apple Silicon (ARM) processors. Intel processors are no longer supported.

Intuitive native macOS application for tracking time spent on projects, built with PyObjC (AppKit) and SQLite. Features start/stop/resume tracking, project management with hourly rates, period filters, statistics and visualization, multi-language support (English/Russian/Ukrainian/Hungarian), and automatic dark mode.

## Features

- ⏱ **Time Tracking**: Start/stop timer with automatic session splitting at midnight
- 📁 **Project Management**: Create and manage multiple projects with hourly rates
- 🏢 **Companies & Work Types**: Organize projects by companies and work categories
- 💰 **Cost Calculation**: Automatic cost tracking based on project hourly rates
- 💵 **Payment Status**: Track paid and unpaid tasks
- 🔍 **Period Filters**: View sessions for Today/Week/Month/Custom Period or all time
- 📊 **Statistics & Charts**: Data visualization with detailed charts (daily trends, project distribution, hourly breakdown)
- 🌐 **Multi-Language**: Automatic language detection (English/Russian/Ukrainian/Hungarian)
- 🌓 **Dark Mode**: Native dark mode support with instant theme switching
- 📋 **Session History**: View detailed session list with duration and cost breakdown
- ⚡ **Menu Bar**: Live timer in menu bar with quick access to recent tasks
- 🔔 **Notifications**: Get notified when starting or stopping tracking
- ✏️ **Session Management**: Edit project details, delete sessions with confirmation
- 💾 **Data Persistence**: Sessions automatically restored on app restart
- 🔄 **Backup & Restore**: Database backup and restore functionality
- 🪟 **Native macOS UI**: Adaptive interface built with AppKit

## Requirements

- macOS 12+ (Monterey or later)
- Python 3.11–3.12 (3.12 recommended)
- **Version 2.0+**: Apple Silicon (ARM64) processor. Intel processors are not supported.

## Quick Start

### Running from Source

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Run the application:
```bash
python3 mac_app.py
```

### Building Standalone App

Build a fully standalone `.app` bundle:

```bash
python3 setup.py py2app
```

The app will be created in `dist/MTimer.app`.

**Notes:**
- The icon is automatically included from `assets/app_icon.icns`
- Binaries are automatically ad-hoc signed during build
- For distribution outside your machine, consider Developer ID signing and notarization
- First launch from Finder may require Gatekeeper confirmation (right-click → Open)

## Data Storage

- **Standalone App**: `~/Library/Application Support/MTimer/timetracker.db`
- **Source Mode**: `timetracker.db` in project root directory

## Project Structure

```
MTimer/
├── mac_app.py              # Main macOS UI (AppKit)
├── database.py             # SQLite database operations
├── localization.py         # Multi-language support
├── statistics.py           # Statistics and visualization module
├── show_stats.py           # Statistics viewer utility
├── setup.py                # py2app build configuration
├── requirements.txt        # Python dependencies
├── assets/                 # Icons and resources
│   └── app_icon.icns      # Application icon
├── generate_icns.py        # Icon generator utility
└── update_project_rates.py # Bulk rate update utility
```

## Usage

1. **Create a Project**: Click the "+" button next to the project list
2. **Set Hourly Rate**: Configure the rate in project settings (⌘,)
3. **Start Tracking**: Enter a description (optional) and click "Start"
4. **Stop/Resume**: Use the main button to control tracking
5. **View History**: Switch between period filters to see different time ranges
6. **Edit Sessions**: Right-click sessions to delete or use Settings to edit projects
7. **Menu Bar**: Access quick-switch menu for recent tasks from the menu bar icon
8. **Statistics**: Click the "Statistics" button to view detailed charts and analysis

## Development

### Generate Icon

If you need to regenerate the app icon from a PNG:

```bash
python3 generate_icns.py  # Creates assets/app_icon.icns
```

### Update Project Rates

Bulk update hourly rates for existing projects:

```bash
python3 update_project_rates.py
```

### View Statistics

Display detailed statistics:

```bash
python3 show_stats.py
```

## Technical Details

- **Architecture**: ARM64 (Apple Silicon) - Version 2.0+
- **Minimum macOS**: 12.0 (Monterey)
- **Python Version**: 3.11–3.12
- **UI Framework**: PyObjC (AppKit)
- **Database**: SQLite 3
- **Visualization**: Matplotlib with native macOS backend
- **Localization**: Automatic system language detection (UK/EN/RU/HU)

## Screenshots

*(Add screenshots here after publishing)*

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Maciborka Vitalik**  
🌐 [it-world.com.ua](https://it-world.com.ua)  
📧 maciborka@gmail.com

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Acknowledgments

Built with [PyObjC](https://pyobjc.readthedocs.io/) — Python bindings for macOS frameworks.

---

<a name="russian"></a>
# MTimer — Нативный тайм-трекер для macOS

[🇺🇦 Українська](#) | [🇬🇧 English](#english) | [🇭🇺 Magyar](#hungarian)

> **⚠️ Версия 2.0+**: Поддерживает только процессоры Apple Silicon (ARM). Процессоры Intel больше не поддерживаются.

Интуитивное нативное macOS приложение для отслеживания времени, потраченного на проекты. Построено на PyObjC (AppKit) и SQLite. Поддерживает старт/стоп/продолжение отслеживания, управление проектами с почасовой ставкой, фильтры периодов, статистику и визуализацию, мультиязычность (украинский/английский/русский/венгерский) и автоматическую темную тему.

## Возможности

- ⏱ **Отслеживание времени**: Старт/стоп таймера с автоматическим разделением сессий в полночь
- 📁 **Управление проектами**: Создание и управление проектами с почасовыми ставками
- 🏢 **Компании и виды работ**: Организация проектов по компаниям и категориям работ
- 💰 **Расчет стоимости**: Автоматический подсчет стоимости на основе почасовой ставки
- 💵 **Статус оплаты**: Отслеживание оплаченных и неоплаченных задач
- 🔍 **Фильтры периодов**: Просмотр сессий за Сегодня/Неделю/Месяц/Кастомный период или все время
- 📊 **Статистика и графики**: Визуализация данных с детальными графиками (дневная динамика, распределение по проектам, почасовое распределение)
- 🌐 **Мультиязычность**: Автоматическое определение языка системы (украинский/английский/русский/венгерский)
- 🌓 **Темная тема**: Поддержка темной темы с мгновенным переключением
- 📋 **История сессий**: Детальный список сессий с длительностью и стоимостью
- ⚡ **Меню-бар**: Живой таймер в меню-баре с быстрым доступом к последним задачам
- 🔔 **Уведомления**: Получайте уведомления при старте и остановке отслеживания
- ✏️ **Управление сессиями**: Редактирование деталей проекта, удаление сессий с подтверждением
- 💾 **Сохранение данных**: Автоматическое восстановление сессий после перезапуска
- 🔄 **Резервное копирование**: Функции резервного копирования и восстановления базы данных
- 🪟 **Нативный macOS UI**: Адаптивный интерфейс на базе AppKit

## Требования

- macOS 12+ (Monterey или новее)
- Python 3.11–3.12 (рекомендуется 3.12)
- **Версия 2.0+**: Процессор Apple Silicon (ARM64). Процессоры Intel не поддерживаются.

## Быстрый старт

### Запуск из исходного кода

1. Установите зависимости:
```bash
pip3 install -r requirements.txt
```

2. Запустите приложение:
```bash
python3 mac_app.py
```

### Сборка автономного приложения

Создание полностью автономного `.app` пакета:

```bash
python3 setup.py py2app
```

Приложение будет создано в `dist/MTimer.app`.

**Примечания:**
- Иконка автоматически включается из `assets/app_icon.icns`
- Бинарные файлы автоматически подписываются ad-hoc во время сборки
- Для распространения за пределами вашей машины рассмотрите подпись Developer ID и нотаризацию
- При первом запуске из Finder может потребоваться подтверждение Gatekeeper (клик правой кнопкой → Открыть)

## Хранение данных

- **Автономное приложение**: `~/Library/Application Support/MTimer/timetracker.db`
- **Режим исходного кода**: `timetracker.db` в корневой директории проекта

## Структура проекта

```
MTimer/
├── mac_app.py              # Главный macOS UI (AppKit)
├── database.py             # Операции с базой данных SQLite
├── localization.py         # Поддержка мультиязычности
├── statistics.py           # Модуль статистики и визуализации
├── show_stats.py           # Утилита просмотра статистики
├── setup.py                # Конфигурация сборки py2app
├── requirements.txt        # Python зависимости
├── assets/                 # Иконки и ресурсы
│   └── app_icon.icns      # Иконка приложения
├── generate_icns.py        # Утилита генерации иконок
└── update_project_rates.py # Утилита массового обновления ставок
```

## Использование

1. **Создайте проект**: Нажмите кнопку "+" рядом со списком проектов
2. **Установите почасовую ставку**: Настройте ставку в настройках проекта (⌘,)
3. **Начните отслеживание**: Введите описание (необязательно) и нажмите "Старт"
4. **Остановка/Продолжение**: Используйте главную кнопку для управления отслеживанием
5. **Просмотр истории**: Переключайте фильтры периодов для просмотра разных промежутков времени
6. **Редактирование сессий**: Клик правой кнопкой для удаления сессий или используйте Настройки для редактирования проектов
7. **Меню-бар**: Доступ к быстрому переключению между последними задачами из иконки в меню-баре8. **Статистика**: Нажмите кнопку "Статистика" для просмотра детальных графиков и анализа
## Разработка

### Генерация иконки

Если нужно перегенерировать иконку приложения из PNG:

```bash
python3 generate_icns.py  # Создает assets/app_icon.icns
```

### Обновление ставок проектов

Массовое обновление почасовых ставок для существующих проектов:

```bash
python3 update_project_rates.py
```

### Просмотр статистики

Отображение детальной статистики:

```bash
python3 show_stats.py
```

## Технические детали

- **Архитектура**: ARM64 (Apple Silicon) - Версия 2.0+
- **Минимальная macOS**: 12.0 (Monterey)
- **Версия Python**: 3.11–3.12
- **UI Framework**: PyObjC (AppKit)
- **База данных**: SQLite 3
- **Визуализация**: Matplotlib с нативным macOS backend
- **Локализация**: Автоматическое определение языка системы (UK/EN/RU/HU)

## Скриншоты

*(Добавьте скриншоты здесь после публикации)*

## Лицензия

Лицензия MIT - смотрите файл [LICENSE](LICENSE) для деталей.

## Автор

**Maciborka Vitalik**  
🌐 [it-world.com.ua](https://it-world.com.ua)  
📧 maciborka@gmail.com

## Вклад в проект

Вклады приветствуются! Не стесняйтесь открывать issue или отправлять pull request.

## Благодарности

Создано с помощью [PyObjC](https://pyobjc.readthedocs.io/) — Python bindings для macOS frameworks.

---

<a name="hungarian"></a>
# MTimer — Natív macOS időkövető

[🇺🇦 Українська](#) | [🇬🇧 English](#english) | [Русский](#russian)

> **⚠️ 2.0+ verzió**: Csak az Apple Silicon (ARM) processzorokat támogatja. Az Intel processzorok már nem támogatottak.

Intuitív natív macOS alkalmazás a projektekre fordított idő nyomon követésére, PyObjC (AppKit) és SQLite technológiákkal. Tartalmazza az indítás/leállítás/folytatás funkciókat, projekt menedzsmentet óradíjakkal, időszűrőket, statisztikákat és vizualizációt, többnyelvű támogatást (angol/orosz/ukrán/magyar) és automatikus sötét módot.

## Funkciók

- ⏱ **Időkövetés**: Időzítő indítása/leállítása automatikus munkamenet-felosztással éjfélkor
- 📁 **Projekt menedzsment**: Több projekt létrehozása és kezelése óradíjakkal
- 🏢 **Cégek és munkatípusok**: Projektek rendszerezése cégek és munkakategóriák szerint
- 💰 **Költségszámítás**: Automatikus költségkövetés projekt óradíjak alapján
- 💵 **Fizetési státusz**: Kifizetett és kifizetetlen feladatok nyomon követése
- 🔍 **Időszűrők**: Munkamenetek megtekintése Ma/Hét/Hónap/Egyéni időszak vagy az összes időre
- 📊 **Statisztikák és diagramok**: Adatvizualizáció részletes diagramokkal (napi trendek, projekt eloszlás, óránkénti bontás)
- 🌐 **Többnyelvűség**: Automatikus nyelvfelismerés (angol/orosz/ukrán/magyar)
- 🌓 **Sötét mód**: Natív sötét mód támogatás azonnali témaváltással
- 📋 **Munkamenet előzmények**: Részletes munkamenet lista időtartammal és költség bontással
- ⚡ **Menüsor**: Élő időzítő a menüsorban gyors hozzáféréssel a legutóbbi feladatokhoz
- 🔔 **Értesítések**: Értesítések az időkövetés indításakor vagy leállításakor
- ✏️ **Munkamenet kezelés**: Projekt részletek szerkesztése, munkamenetek törlése megerősítéssel
- 💾 **Adatmegőrzés**: Munkamenetek automatikus visszaállítása az alkalmazás újraindításakor
- 🔄 **Biztonsági mentés és visszaállítás**: Adatbázis biztonsági mentés és visszaállítás funkciók
- 🪟 **Natív macOS UI**: Adaptív felület AppKit alapokon

## Követelmények

- macOS 12+ (Monterey vagy újabb)
- Python 3.11–3.12 (3.12 ajánlott)
- **2.0+ verzió**: Apple Silicon (ARM64) processzor. Intel processzorok nem támogatottak.

## Gyors kezdés

### Futtatás forráskódból

1. Függőségek telepítése:
```bash
pip3 install -r requirements.txt
```

2. Alkalmazás futtatása:
```bash
python3 mac_app.py
```

### Önálló alkalmazás készítése

Teljesen önálló `.app` csomag létrehozása:

```bash
python3 setup.py py2app
```

Az alkalmazás a `dist/MTimer.app` mappában lesz létrehozva.

**Megjegyzések:**
- Az ikon automatikusan bekerül az `assets/app_icon.icns` fájlból
- A binárisok automatikusan ad-hoc aláírást kapnak a build során
- A gépen kívüli terjesztéshez fontolja meg a Developer ID aláírást és a notarizációt
- Az első Finder-ből történő indításkor Gatekeeper megerősítés szükséges lehet (jobb klikk → Megnyitás)

## Adattárolás

- **Önálló alkalmazás**: `~/Library/Application Support/MTimer/timetracker.db`
- **Forráskód mód**: `timetracker.db` a projekt gyökérkönyvtárában

## Projekt struktúra

```
MTimer/
├── mac_app.py              # Fő macOS UI (AppKit)
├── database.py             # SQLite adatbázis műveletek
├── localization.py         # Többnyelvű támogatás
├── statistics.py           # Statisztika és vizualizáció modul
├── setup.py                # py2app build konfiguráció
├── requirements.txt        # Python függőségek
├── assets/                 # Ikonok és erőforrások
│   └── app_icon.icns      # Alkalmazás ikon
├── generate_icns.py        # Ikon generáló segédprogram
└── update_project_rates.py # Tömeges díjfrissítő segédprogram
```

## Használat

1. **Projekt létrehozása**: Kattintson a "+" gombra a projekt lista mellett
2. **Óradíj beállítása**: Állítsa be a díjat a projekt beállításokban (⌘,)
3. **Követés indítása**: Írjon be egy leírást (opcionális) és kattintson a "Start" gombra
4. **Leállítás/Folytatás**: Használja a fő gombot a követés vezérléséhez
5. **Előzmények megtekintése**: Váltson az időszűrők között különböző időtartományok megtekintéséhez
6. **Munkamenetek szerkesztése**: Jobb klikk a munkamenetekre a törléshez vagy használja a Beállításokat a projektek szerkesztéséhez
7. **Menüsor**: Hozzáférés a gyors váltó menühöz a legutóbbi feladatokhoz a menüsor ikonból
8. **Statisztikák**: Kattintson a "Statisztikák" gombra a részletes diagramok és elemzések megtekintéséhez

## Fejlesztés

### Ikon generálása

Ha újra kell generálni az alkalmazás ikont egy PNG-ből:

```bash
python3 generate_icns.py  # Létrehozza az assets/app_icon.icns fájlt
```

### Projekt díjak frissítése

Tömeges óradíj frissítés meglévő projektekhez:

```bash
python3 update_project_rates.py
```

### Statisztikák megtekintése

Részletes statisztikák megjelenítése:

```bash
python3 show_stats.py
```

## Technikai részletek

- **Architektúra**: ARM64 (Apple Silicon) - 2.0+ verzió
- **Minimum macOS**: 12.0 (Monterey)
- **Python verzió**: 3.11–3.12
- **UI Framework**: PyObjC (AppKit)
- **Adatbázis**: SQLite 3
- **Vizualizáció**: Matplotlib natív macOS backend-del
- **Lokalizáció**: Automatikus rendszernyelv-felismerés (UK/EN/RU/HU)

## Képernyőképek

*(Adjon hozzá képernyőképeket a közzététel után)*

## Licensz

MIT Licensz - lásd a [LICENSE](LICENSE) fájlt a részletekért.

## Szerző

**Maciborka Vitalik**  
🌐 [it-world.com.ua](https://it-world.com.ua)  
📧 maciborka@gmail.com

## Közreműködés

A hozzájárulásokat szívesen fogadjuk! Nyugodtan nyisson issue-kat vagy küldjön pull request-eket.

## Köszönetnyilvánítás

Készült a [PyObjC](https://pyobjc.readthedocs.io/) segítségével — Python bindings a macOS keretrendszerekhez.
