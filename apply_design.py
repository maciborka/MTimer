import re
import sys

with open("mac_app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update Heights in setupUI
code = code.replace("self.topBarHeight = 56", "self.topBarHeight = 84")
code = code.replace("self.cardHeight = 88", "self.cardHeight = 60")
code = code.replace("self.headerTitle.setFont_(NSFont.boldSystemFontOfSize_(16))", "self.headerTitle.setFont_(NSFont.systemFontOfSize_weight_(22, NSFontWeightRegular))")

# 2. Card Background: Make the timerCard invisible (no border, no bg color, no radius)
code = code.replace("self.timerCard.setFillColor_(NSColor.controlBackgroundColor())", "self.timerCard.setFillColor_(NSColor.clearColor())")
code = code.replace("self.timerCard.setCornerRadius_(12.0)", "self.timerCard.setCornerRadius_(0.0)")
code = code.replace("self.timerCard.layer().setBackgroundColor_(\n                        NSColor.controlBackgroundColor().CGColor()\n                    )", "")

# 3. Update windowDidResize_ to position elements nicely
# Instead of Regex, we'll replace the block in windowDidResize_ exactly.
old_resize = """            self.timerCard.setFrame_(NSMakeRect(5, cardY, width - 10, self.cardHeight))

            # Обновляем элементы внутри карточки (адаптивная ширина)
            rowY = (self.cardHeight - 28) / 2
            self.descriptionField.setFrame_(NSMakeRect(16, rowY, 360, 28))
            self.projectPopup.setFrame_(NSMakeRect(384, rowY, 200, 28))
            self.addProjectBtn.setFrame_(NSMakeRect(590, rowY, 35, 28))

            # Таймер сверху
            # timerLabel теперь находится на верхней полосе, выровнен по высоте
            self.timerLabel.setFrame_(NSMakeRect(width - 240, height - self.topBarHeight - 5, 220, 56))
            
            cardWidth = width - 10
            btnSize = 44
            self.startStopBtn.setFrame_(
                NSMakeRect(
                    cardWidth - btnSize - 16,
                    (self.cardHeight - btnSize) / 2,
                    btnSize,
                    btnSize,
                )
            )"""

new_resize = """            # TimerCard is now edge-to-edge
            self.timerCard.setFrame_(NSMakeRect(0, cardY, width, self.cardHeight))

            cardWidth = width
            btnSize = 44
            self.startStopBtn.setFrame_(
                NSMakeRect(
                    cardWidth - btnSize - 20,
                    (self.cardHeight - btnSize) / 2,
                    btnSize,
                    btnSize,
                )
            )

            # Таймер сверху
            self.timerLabel.setFrame_(NSMakeRect(width - 240, height - self.topBarHeight + (self.topBarHeight - 56) / 2 + 5, 220, 56))

            # Элементы внутри карточки
            rowY = (self.cardHeight - 32) / 2
            
            # Plus button
            self.addProjectBtn.setFrame_(NSMakeRect(cardWidth - btnSize - 20 - 35 - 10, rowY, 35, 32))
            
            # Project popup
            self.projectPopup.setFrame_(NSMakeRect(cardWidth - btnSize - 20 - 35 - 10 - 200 - 10, rowY, 200, 32))

            # Description stretches
            descWidth = cardWidth - btnSize - 20 - 200 - 10 - 35 - 10 - 20 - 10
            self.descriptionField.setFrame_(NSMakeRect(20, rowY, descWidth, 32))"""

code = code.replace(old_resize, new_resize)

# 4. Filters styling and continue button position
old_filter_resize = """            # Кнопки фильтра периода
            self.customFilterBtn.setFrame_(NSMakeRect(filterX, filterY, 110, 24))
            self.todayFilterBtn.setFrame_(NSMakeRect(filterX + 115, filterY, 80, 24))
            self.weekFilterBtn.setFrame_(NSMakeRect(filterX + 200, filterY, 80, 24))
            self.monthFilterBtn.setFrame_(NSMakeRect(filterX + 285, filterY, 80, 24))

            # Элементы для кастомного периода
            customDateY = filterY - 30  # 30 пикселей ниже кнопок
            self.fromDateLabel.setFrame_(NSMakeRect(filterX, customDateY - 5, 25, 20))
            self.fromDatePicker.setFrame_(
                NSMakeRect(filterX + 30, customDateY - 5, 180, 24)
            )
            self.toDateLabel.setFrame_(
                NSMakeRect(filterX + 220, customDateY - 5, 25, 20)
            )
            self.toDatePicker.setFrame_(
                NSMakeRect(filterX + 250, customDateY - 5, 180, 24)
            )
            self.applyCustomFilterBtn.setFrame_(
                NSMakeRect(filterX + 440, customDateY - 5, 80, 24)
            )

            # Кнопка экспорта в PDF - справа
            self.exportPdfBtn.setFrame_(NSMakeRect(width - 50, customDateY - 5, 40, 24))

            # Поля с общим временем и кнопки
            self.weekTotalField.setFrame_(NSMakeRect(390, filterY, 300, 20))
            self.todayTotalField.setFrame_(
                NSMakeRect(width - 200, filterY + 2, 160, 20)
            )
            self.continueBtn.setFrame_(NSMakeRect(width - 360, filterY, 140, 24))
            if hasattr(self, "statisticsBtn"):
                self.statisticsBtn.setFrame_(NSMakeRect(20, filterY - 30, 120, 24))

            # ScrollView с сессиями - растягивается по высоте и ширине
            tableTopMargin = 80  # Увеличили отступ для кнопки статистики
            tableY = 5
            tableHeight = cardY - 20 - tableTopMargin
            if tableHeight < 100:
                tableHeight = 100
            self.sessionsScroll.setFrame_(
                NSMakeRect(5, tableY, width - 10, tableHeight)
            )"""

new_filter_resize = """            # Кнопки фильтра периода (без рамок)
            self.customFilterBtn.setFrame_(NSMakeRect(filterX, filterY, 100, 28))
            self.todayFilterBtn.setFrame_(NSMakeRect(filterX + 110, filterY, 80, 28))
            self.weekFilterBtn.setFrame_(NSMakeRect(filterX + 200, filterY, 80, 28))
            self.monthFilterBtn.setFrame_(NSMakeRect(filterX + 290, filterY, 80, 28))

            # Элементы для кастомного периода
            customDateY = filterY - 30 
            self.fromDateLabel.setFrame_(NSMakeRect(filterX, customDateY - 5, 25, 20))
            self.fromDatePicker.setFrame_(NSMakeRect(filterX + 30, customDateY - 5, 180, 24))
            self.toDateLabel.setFrame_(NSMakeRect(filterX + 220, customDateY - 5, 25, 20))
            self.toDatePicker.setFrame_(NSMakeRect(filterX + 250, customDateY - 5, 180, 24))
            self.applyCustomFilterBtn.setFrame_(NSMakeRect(filterX + 440, customDateY - 5, 80, 24))

            self.exportPdfBtn.setFrame_(NSMakeRect(width - 50, customDateY - 5, 40, 24))

            # Поля с общим временем и кнопки
            # ВСЬОГО: 
            self.weekTotalField.setFrame_(NSMakeRect(width - 450, filterY + 4, 150, 20))
            self.todayTotalField.setHidden_(True)
            
            # Кнопка Продовжити
            self.continueBtn.setFrame_(NSMakeRect(width - 290, filterY + 2, 125, 24))
            
            # Dummy element (to mimic the 02:30:00 input box in your design without actually adding functionality)
            if not hasattr(self, "dummyTimeField"):
                self.dummyTimeField = NSTextField.alloc().initWithFrame_(NSMakeRect(width - 150, filterY + 2, 80, 24))
                self.dummyTimeField.setPlaceholderString_("00:00:00")
                self.dummyTimeField.setAlignment_(2) # Center
                self.window.contentView().addSubview_(self.dummyTimeField)
                
                self.dummyAddBtn = NSButton.alloc().initWithFrame_(NSMakeRect(width - 60, filterY + 2, 40, 24))
                self.dummyAddBtn.setTitle_("+")
                self.dummyAddBtn.setBezelStyle_(NSBezelStyleRounded)
                self.window.contentView().addSubview_(self.dummyAddBtn)
            else:
                self.dummyTimeField.setFrame_(NSMakeRect(width - 150, filterY + 2, 80, 24))
                self.dummyAddBtn.setFrame_(NSMakeRect(width - 60, filterY + 2, 40, 24))

            if hasattr(self, "statisticsBtn"):
                self.statisticsBtn.setFrame_(NSMakeRect(20, filterY - 30, 120, 24))

            # ScrollView с сессиями - растягивается по высоте и ширине
            tableTopMargin = 80
            tableY = 5
            tableHeight = cardY - 20 - tableTopMargin
            if tableHeight < 100:
                tableHeight = 100
            self.sessionsScroll.setFrame_(
                NSMakeRect(5, tableY, width - 10, tableHeight)
            )"""

code = code.replace(old_filter_resize, new_filter_resize)

# Fix filter button style
code = code.replace("self.customFilterBtn.setBezelStyle_(NSBezelStyleRounded)", "self.customFilterBtn.setBezelStyle_(NSBezelStyleRoundRect)\n        self.customFilterBtn.setBordered_(False)")
code = code.replace("self.todayFilterBtn.setBezelStyle_(NSBezelStyleRounded)", "self.todayFilterBtn.setBezelStyle_(NSBezelStyleRoundRect)\n        self.todayFilterBtn.setBordered_(False)")
code = code.replace("self.weekFilterBtn.setBezelStyle_(NSBezelStyleRounded)", "self.weekFilterBtn.setBezelStyle_(NSBezelStyleRoundRect)\n        self.weekFilterBtn.setBordered_(False)")
code = code.replace("self.monthFilterBtn.setBezelStyle_(NSBezelStyleRounded)", "self.monthFilterBtn.setBezelStyle_(NSBezelStyleRoundRect)\n        self.monthFilterBtn.setBordered_(False)")

# 5. Modify UpdateSessionsList row height and styling
# Find where it says: "rowHeight = 45" inside updateSessionsList
code = code.replace("rowHeight = 45", "rowHeight = 65")
code = code.replace("new_height = max(100, len(self.today_sessions) * 45 + 10)", "new_height = max(100, len(self.today_sessions) * 65 + 10)")

# Inside updateSessionsList row view construction:
old_render = """                descField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(10, 22, col1_width, 20)
                )
                descField.setStringValue_(str(s.get("description") or t("no_description")))
                descField.setBezeled_(False)
                descField.setDrawsBackground_(False)
                descField.setEditable_(False)
                descField.setFont_(NSFont.boldSystemFontOfSize_(13))
                rowView.addSubview_(descField)

                # Project name
                projField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(10, 2, col1_width, 20)
                )
                projField.setStringValue_(
                    f"{s.get('project_name', '')} {s.get('work_type_name', '')}"
                )
                projField.setBezeled_(False)
                projField.setDrawsBackground_(False)
                projField.setEditable_(False)
                projField.setFont_(NSFont.systemFontOfSize_(11))
                projField.setTextColor_(NSColor.secondaryLabelColor())
                rowView.addSubview_(projField)

                # Time span (12:00 - 13:00)
                timeField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(10 + col1_width, 12, col2_width, 20)
                )"""

new_render = """                # Checkmark icon on the right
                actionsX = row_width - 120
                checkIcon = NSTextField.alloc().initWithFrame_(NSMakeRect(actionsX, 22, 20, 20))
                checkIcon.setStringValue_("✓")
                checkIcon.setBezeled_(False)
                checkIcon.setDrawsBackground_(False)
                checkIcon.setEditable_(False)
                checkIcon.setTextColor_(NSColor.systemGreenColor())
                checkIcon.setFont_(NSFont.systemFontOfSize_(16))
                rowView.addSubview_(checkIcon)

                editIcon = NSTextField.alloc().initWithFrame_(NSMakeRect(actionsX + 30, 22, 20, 20))
                editIcon.setStringValue_("✎")
                editIcon.setBezeled_(False)
                editIcon.setDrawsBackground_(False)
                editIcon.setEditable_(False)
                editIcon.setTextColor_(NSColor.systemBlueColor())
                editIcon.setFont_(NSFont.systemFontOfSize_(16))
                rowView.addSubview_(editIcon)
                
                deleteIcon = NSTextField.alloc().initWithFrame_(NSMakeRect(actionsX + 60, 22, 20, 20))
                deleteIcon.setStringValue_("✕")
                deleteIcon.setBezeled_(False)
                deleteIcon.setDrawsBackground_(False)
                deleteIcon.setEditable_(False)
                deleteIcon.setTextColor_(NSColor.secondaryLabelColor())
                deleteIcon.setFont_(NSFont.systemFontOfSize_(16))
                rowView.addSubview_(deleteIcon)

                # Time span (12:00 - 13:00)
                timeField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(actionsX - col2_width - 100, 22, col2_width + 40, 20)
                )
                
                # Project name and cost (Orange)
                costField = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 5, col1_width, 20))
                project_name = s.get('project_name', '')
                
                rate_str = ""
                # Calculate cost if rate > 0
                for p in self.projects_cache:
                    if p["id"] == s.get("project_id") and p["hourly_rate"] > 0:
                        cost = (s.get("duration", 0) / 3600.0) * p["hourly_rate"]
                        rate_str = f"${cost:.2f}"
                        break
                        
                # Create attributed string for folder + project + orange cost
                attrString = NSMutableAttributedString.alloc().initWithString_attributes_(
                    f"📁 {project_name}  ", {NSFontAttributeName: NSFont.systemFontOfSize_(13), NSForegroundColorAttributeName: NSColor.secondaryLabelColor()}
                )
                if rate_str:
                    costString = NSAttributedString.alloc().initWithString_attributes_(
                        rate_str, {NSFontAttributeName: NSFont.systemFontOfSize_(13), NSForegroundColorAttributeName: NSColor.orangeColor()}
                    )
                    attrString.appendAttributedString_(costString)
                    
                costField.setAttributedStringValue_(attrString)
                costField.setBezeled_(False)
                costField.setDrawsBackground_(False)
                costField.setEditable_(False)
                rowView.addSubview_(costField)

                # Task description
                descField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(10, 30, col1_width, 20)
                )
                descField.setStringValue_(str(s.get("description") or t("no_description")))
                descField.setBezeled_(False)
                descField.setDrawsBackground_(False)
                descField.setEditable_(False)
                descField.setFont_(NSFont.boldSystemFontOfSize_(14))
                rowView.addSubview_(descField)"""

code = code.replace(old_render, new_render)

old_duration_render = """                # Duration (01:00:00)
                durationField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(10 + col1_width + col2_width, 12, col3_width, 20)
                )"""

new_duration_render = """                # Duration (00:03:26)
                durationField = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(actionsX - 80, 22, 80, 20)
                )"""

code = code.replace(old_duration_render, new_duration_render)


with open("mac_app.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Redesign applied successfully!")
