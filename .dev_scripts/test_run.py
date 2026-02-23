#!/usr/bin/env python3
"""Тестовый запуск приложения для отладки"""

import sys
import traceback

print("=" * 50)
print("Starting MTimer test run...")
print("=" * 50)

try:
    print("\n1. Importing modules...")
    from mac_app import TimeTrackerWindowController, main

    print("✓ Import successful")

    print("\n2. Starting application...")
    sys.exit(main())

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)
