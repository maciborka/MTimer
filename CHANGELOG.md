# Changelog

All notable changes to MTimer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Експорт даних у CSV/JSON
- Статистика та графіки
- Теги для сесій
- iCloud синхронізація

## [1.0.0] - 2025-11-17

### Added
- Нативний macOS додаток з AppKit UI
- Відстеження часу з автоматичним розділенням сесій в опівночі
- Управління проєктами з почасовими ставками
- Фільтри періодів: Сьогодні/Тиждень/Місяць
- Багатомовна підтримка (UK/EN/RU) з автоматичним визначенням
- Інтеграція в menu bar з живим таймером
- Швидке перемикання між останніми 3 завданнями
- Нативні сповіщення при старті/зупинці
- Підтримка світлої та темної теми
- Settings вікно для редагування проєктів
- Видалення сесій з підтвердженням
- Keyboard shortcuts (⌘, для Settings, Delete для видалення)
- Збереження стану додатку між запусками
- Universal binary (Intel + Apple Silicon)
- SQLite база даних для локального зберігання

### Technical
- PyObjC 10.2 для нативної інтеграції з macOS
- py2app packaging з ad-hoc підписом
- MVC архітектура з чистим розділенням логіки
- Observer pattern для реактивного оновлення UI
- Singleton database з connection pooling

[Unreleased]: https://github.com/maciborka/MTimer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/maciborka/MTimer/releases/tag/v1.0.0
