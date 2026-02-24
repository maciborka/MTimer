with open('mac_app.py', 'r') as f:
    text = f.read()

# Remove dummyTimeField dummyAddBtn
dummy_code_to_remove = """            # Dummy element (to mimic the 02:30:00 input box in your design without actually adding functionality)
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
                self.dummyAddBtn.setFrame_(NSMakeRect(width - 60, filterY + 2, 40, 24))"""

text = text.replace(dummy_code_to_remove, "")
text = text.replace("self.continueBtn.setFrame_(NSMakeRect(width - 290, filterY + 2, 125, 24))", "self.continueBtn.setFrame_(NSMakeRect(width - 150, filterY + 2, 125, 24))")

with open('mac_app.py', 'w') as f:
    f.write(text)
