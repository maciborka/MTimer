from mac_app import TimeTrackerWindowController, FlippedView
import AppKit

ctrl = TimeTrackerWindowController.alloc().init()
session = {"id": 1, "description": "Test", "project_id": 7, "duration": 3600}
ctrl.projects_cache = [{"id": 7, "name": "AI_CHAT", "hourly_rate": 20.0, "company_id": 1}]
class MockDB:
    def get_all_companies(self):
        return [{"id": 1, "name": "Test Company"}]
ctrl.db = MockDB()
ctrl.sessionsScroll = AppKit.NSScrollView.alloc().init()
ctrl.sessionsScroll.setFrame_(AppKit.NSMakeRect(0,0,800,600))

v = ctrl.createSessionView(session)
print(v)
print("Subviews:", v.subviews())
for sub in v.subviews():
    if isinstance(sub, AppKit.NSTextField):
        print("TextField:", sub.stringValue(), sub.frame())
